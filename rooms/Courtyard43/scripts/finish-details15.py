"""Official MCP: preserve label relief depth when wrapping typography."""
import bpy,ast,math,os,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene;scene=s
assert s.get('web_revision')=='courtyard43-interior15' and s.get('details15_fitted') and not s.get('details15_finished')
bp=lambda p:Vector((p[0],-p[2],p[1]));web=lambda p:Vector((p[0],p[2],-p[1]));targets=set()
p=ROOM/'scripts/refine-details15.py';t=ast.parse(p.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='textmesh'],type_ignores=[]),str(p),'exec'))
for name,text,size,h,material in [('C43_Nongfu15_brand','农夫山泉',.019,1.1385,'C43_Nongfu15_label_white_15'),('C43_Nongfu15_water_title','饮用天然水',.0075,1.1675,'C43_Nongfu15_label_red_15')]:
    bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    textmesh(name,text,size,(.56,h,.270),bpy.data.materials[material],(.56,.215,.055))
s['details15_finished']=True
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'finished':True}
