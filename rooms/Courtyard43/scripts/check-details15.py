"""Official MCP read-only source inspection for the seven user corrections."""
from pathlib import Path
import bpy,bmesh,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3]
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior15'
dg=bpy.context.evaluated_depsgraph_get()
def geometry(name):
    o=bpy.data.objects[name];e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles()
    points=[o.matrix_world@v.co for v in m.vertices]
    tree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in m.loop_triangles],all_triangles=True)
    bm=bmesh.new();bm.from_mesh(m)
    report={'name':name,'vertices':len(points),'zeroArea':sum(f.calc_area()<1e-14 for f in bm.faces),'boundaryEdges':sum(not ed.is_manifold for ed in bm.edges),'volume':bm.calc_volume(signed=True),'minHeight':min(p.z for p in points)}
    bm.free();e.to_mesh_clear();return tree,points,report
result={'revision':scene['web_revision'],'bedContacts':{},'curtains':[],'geometry':[],'missingImages':[]}
for a,b in [('FloralDuvet','Mattress'),('DrapedWhiteSheet','Mattress'),('FloralDuvet','DrapedWhiteSheet'),('FloralDuvet','CottonPillow')]:
    ta,_,_=geometry('C43_'+a);tb,_,_=geometry('C43_'+b);result['bedContacts'][a+'/'+b]=len(ta.overlap(tb))
for name in ['C43_FloralDuvet','C43_DrapedWhiteSheet','C43_Ribbed_water_bottle','C43_Bottle_water','C43_Bottle_cap','C43_Hanging_bag','C43_Bag_visible_blue_round_item','C43_BucketHat15','C43_Desk_power_cable']:
    result['geometry'].append(geometry(name)[2])
assert geometry('C43_FloralDuvet')[2]['minHeight']>.56,'Quilt must stay on mattress'
assert geometry('C43_DrapedWhiteSheet')[2]['minHeight']>.45,'No long bed skirt'
cap=geometry('C43_Radiator_Cap_Front')[0]
kit=[geometry(o.name)[0] for o in scene.objects if o.type=='MESH' and o.name.startswith('C43_DevKit_')]
cache={}
for side in ['Left','Right']:
    o=bpy.data.objects['C43_Curtain_'+side];rings=bpy.data.objects[o.name+'_Rings']
    saved=o.data.shape_keys.key_blocks['Open'].value
    for step in range(11):
        amount=step/10
        for obj in [o,rings]:obj.data.shape_keys.key_blocks['Open'].value=amount
        bpy.context.view_layer.update();t,pts,_=geometry(o.name)
        row={'side':side,'amount':amount,'supportGap':min(p.z for p in pts)-(0 if side=='Left' else 1.0125),'counterCrossings':len(t.overlap(cap)),'kitCrossings':sum(len(t.overlap(k)) for k in kit)}
        result['curtains'].append(row);cache[side,step]=t
    for obj in [o,rings]:obj.data.shape_keys.key_blocks['Open'].value=saved
result['panelCrossings']=sum(len(cache['Left',i].overlap(cache['Right',j])) for i in range(11) for j in range(11))
result['missingImages']=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath,library=im.library)).is_file()]
out=ROOT/'analysis/Courtyard43/details15';out.mkdir(parents=True,exist_ok=True)
result['pass']=not any(result['bedContacts'].values()) and result['panelCrossings']==0 and not result['missingImages'] and all(x['counterCrossings']==0 and x['kitCrossings']==0 and x['supportGap']>=0 for x in result['curtains']) and all(x['zeroArea']==0 and x['boundaryEdges']==0 and x['volume']>0 for x in result['geometry'])
(out/'source-check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
assert result['pass'],'Inspect source-check.json'
