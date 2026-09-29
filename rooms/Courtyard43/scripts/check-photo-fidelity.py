"""Read-only contact checks for interior08, run via official Blender Lab MCP.

The established exhaustive 21x21 curtain contact test is reused as code, with
an explicit new parent guard and independent report directory, never bypassed.
"""
from pathlib import Path
import bpy
assert bpy.context.scene.get('web_revision')=='courtyard43-interior08'
p=Path(__file__).with_name('check-soft-textiles.py')
code=p.read_text(encoding='utf-8').replace("=='courtyard43-interior06'","=='courtyard43-interior08'").replace("analysis/Courtyard43/textile06","analysis/Courtyard43/photo08")
exec(compile(code,str(p),'exec'))
import bmesh
result['closedDetails']=[]
for name in ['C43_Hanging_bag','C43_Bag_strap_0','C43_Bag_strap_1','C43_Bag_visible_blue_round_item','C43_Round_hanging_item','C43_Headboard_mark_0','C43_Headboard_mark_1','C43_Tissue_packet']:
    obj=bpy.data.objects[name];evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh()
    bm=bmesh.new();bm.from_mesh(mesh)
    row={'name':name,'volume':bm.calc_volume(signed=True),'nonmanifold':sum(not e.is_manifold for e in bm.edges),'zeroArea':sum(f.calc_area()<1e-14 for f in bm.faces)}
    result['closedDetails'].append(row);bm.free();evaluated.to_mesh_clear()
assert all(r['volume']>0 and not r['nonmanifold'] and not r['zeroArea'] for r in result['closedDetails'])
(OUT/'contact-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
