"""Read-only blackout11 textile surface/contact checks via official Blender Lab MCP."""
import bpy
import json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior11'
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'analysis/Courtyard43/afternoon11'
OUT.mkdir(parents=True,exist_ok=True)
dg=bpy.context.evaluated_depsgraph_get()

def tree(name):
    o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh()
    m.calc_loop_triangles()
    pts=[o.matrix_world@v.co for v in m.vertices]
    t=BVHTree.FromPolygons(pts,[tuple(p.vertices) for p in m.loop_triangles],all_triangles=True)
    e.to_mesh_clear()
    return t,pts

result={'revision':scene['web_revision'],'bedding':{},'curtains':[],'missingImages':[]}
for a,b in [('FloralDuvet','Mattress'),('DrapedWhiteSheet','Mattress'),('CottonPillow','Mattress'),('CottonPillow','DrapedWhiteSheet'),('FloralDuvet','CottonPillow'),('FloralDuvet','DrapedWhiteSheet')]:
    ta,_=tree('C43_'+a);tb,_=tree('C43_'+b)
    result['bedding'][a+'/'+b]=len(ta.overlap(tb))
support={'Left':.044,'Right':1.0125}
cap,_=tree('C43_Radiator_Cap_Front')
rods,_=tree('C43_Curtain_Rod')
cache={}
for side in ('Left','Right'):
    o=bpy.data.objects['C43_Curtain_'+side];ring=bpy.data.objects[o.name+'_Rings']
    for step in range(21):
        amount=step/20
        o.data.shape_keys.key_blocks['Open'].value=amount
        ring.data.shape_keys.key_blocks['Open'].value=amount
        bpy.context.view_layer.update()
        cloth,points=tree(o.name);_,rpoints=tree(ring.name)
        # Actual lower torus points of all eleven round rings.
        distances=[cloth.find_nearest(rpoints[i*160+10*8])[3] for i in range(11)]
        row={'side':side,'amount':amount,'supportGap':min(p.z for p in points)-support[side],
             'maxRingGap':max(distances),'capIntersections':len(cloth.overlap(cap)),
             'maxRoomward':max(-p.y for p in points)}
        result['curtains'].append(row);cache[side,step]=cloth
    o.data.shape_keys.key_blocks['Open'].value=0
    ring.data.shape_keys.key_blocks['Open'].value=0
result['independentPanelIntersections']=sum(len(cache['Left',a].overlap(cache['Right',b])) for a in range(21) for b in range(21))
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath,library=im.library)).is_file():
        result['missingImages'].append(im.name)
result['pass']=not any(result['bedding'].values()) and not result['independentPanelIntersections'] and not result['missingImages'] and all(r['supportGap']>=0 and r['maxRingGap']<.004 and r['capIntersections']==0 for r in result['curtains'])
(OUT/'contact-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert result['pass'], 'Textile contact validation failed; inspect contact-report.json'
