"""Read-only, evaluated source checks; run via official Blender Lab MCP."""
from pathlib import Path
import bpy, bmesh, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
assert bpy.context.scene.get('web_revision')=='courtyard43-interior07'
ROOT=Path(__file__).resolve().parents[3]
dg=bpy.context.evaluated_depsgraph_get()

def evaluated(name):
    o=bpy.data.objects[name];e=o.evaluated_get(dg);me=e.to_mesh();me.calc_loop_triangles()
    points=[o.matrix_world@v.co for v in me.vertices]
    tree=BVHTree.FromPolygons(points,[tuple(p.vertices) for p in me.loop_triangles],all_triangles=True)
    bm=bmesh.new();bm.from_mesh(me)
    row={'name':name,'nonManifold':sum(not ed.is_manifold for ed in bm.edges),'zeroArea':sum(f.calc_area()<1e-14 for f in bm.faces),'volume':bm.calc_volume(signed=True)}
    bm.free();e.to_mesh_clear();return tree,points,row

names=['C43_Tissue_packet','C43_Tissue_0','C43_Tissue_1','C43_Ribbed_water_bottle','C43_Plastic_cup','C43_Bottle_label','C43_Hanging_bag','C43_Bag_strap_0','C43_Bag_strap_1']
rows=[evaluated(name)[2] for name in names]
contacts=[]
bag,_,_=evaluated('C43_Hanging_bag')
for name in ['C43_Bag_strap_0','C43_Bag_strap_1']:
    _,points,_=evaluated(name)
    ends=[p for p in points if p.z<1.428]
    contacts.append({'object':name,'contact':'bag mouth','minGap':min(bag.find_nearest(p)[3] for p in ends)})
hook,_,_=evaluated('C43_Bag_hook_tip')
for name in ['C43_Bag_strap_0','C43_Bag_strap_1']:
    _,points,_=evaluated(name);tops=[p for p in points if p.z>1.595]
    contacts.append({'object':name,'contact':'hook tip','minGap':min(hook.find_nearest(p)[3] for p in tops)})
for i in range(3):
    name=next(o.name for o in bpy.context.scene.objects if o.name.startswith(f'C43_Cap{i+1}_crown-sewn-hem'))
    hat,_,_=evaluated(name);_,points,_=evaluated(f'C43_Cap_hook_{i}')
    contacts.append({'object':name,'contact':'hat hook','minGap':min(hat.find_nearest(p)[3] for p in points)})
body,points,_=evaluated('C43_Bag_wall_hook')
assert max(p.y for p in points)>-1.375,'Bag hook must reach wardrobe surface'
for name in ['C43_Tissue_packet','C43_Ribbed_water_bottle','C43_Plastic_cup']:
    _,points,_=evaluated(name);assert abs(min(p.z for p in points)-1.0125)<.0005,name+' support'
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath,library=im.library)).is_file()]
result={'geometry':rows,'contacts':contacts,'missingImages':missing}
result['pass']=not missing and all(r['nonManifold']==0 and r['zeroArea']==0 and r['volume']>0 for r in rows) and all(c['minGap']<.004 for c in contacts)
out=ROOT/'analysis/Courtyard43/finish07';out.mkdir(parents=True,exist_ok=True)
(out/'source-check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert result['pass'],'Inspect finish07/source-check.json'
