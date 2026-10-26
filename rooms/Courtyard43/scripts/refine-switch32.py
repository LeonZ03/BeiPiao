"""switch31 -> switch32: thicker housing/button, two opposed stable tilts.

Official Blender Lab MCP only. Thickness/tilt are generic photo estimates.
Reuse the same sealed construction helpers, without rerunning the older stage.
"""
from pathlib import Path
import bpy,bmesh,json,ast,hashlib
from mathutils import Vector
import math
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-switch31'
for file,names in [('refine-furnishings.py',{'digest'}),('refine-switch31.py',{'finish_mesh','rounded_loop'})]:
    tree=ast.parse((ROOM/'scripts'/file).read_text('utf8'))
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),file,'exec'))
targets={'C43_Switch_Backplate','C43_Switch_Rocker','C43_Switch_Pivot'}
before={o.name:digest(o) for o in s.objects if o.name not in targets}
n=32;loops=[rounded_loop(.00425,.086,.086,.002),rounded_loop(-.00725,.086,.086,.002),rounded_loop(-.00725,.068,.067,.001),rounded_loop(.00355,.068,.067,.001)]
faces=[]
for a,b in [(0,1),(1,2),(2,3)]:
    for i in range(n):j=(i+1)%n;faces.append((a*n+i,a*n+j,b*n+j,b*n+i))
faces.extend([tuple(range(n-1,-1,-1)),tuple(3*n+i for i in range(n))])
housing,volume=finish_mesh('Switch32 11.5mm sealed housing',sum(loops,[]),faces,.00022)
bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
for v in bm.verts:v.co=Vector((v.co.x*.010,v.co.y*.065,v.co.z*.064))
bm.verts.ensure_lookup_table();bm.verts.index_update()
button,button_volume=finish_mesh('Switch32 10mm closed rocker',[tuple(v.co) for v in bm.verts],[tuple(v.index for v in f.verts) for f in bm.faces],.0008);bm.free()
for name,me in [('C43_Switch_Backplate',housing),('C43_Switch_Rocker',button)]:
    o=bpy.data.objects[name];mat=o.material_slots[0].material;o.data=me;me.materials.append(mat)
pivot=bpy.data.objects['C43_Switch_Pivot'];pivot.location.x=2.225-.008
# Web Z is Blender -Y. Save the off endpoint in the authored source itself.
pivot.rotation_euler.y=.045
desc=json.loads(pivot['c43_interaction']);desc.update(angle=.09,offAngle=-.045,onAngle=.045);pivot['c43_interaction']=json.dumps(desc)
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[name])==h for name,h in before.items())
details={'parent':'courtyard43-switch31','wallX':2.225,'wellFloorX':2.2248,'rockerCenterX':2.217,'housingThicknessM':.0115,'rockerThicknessM':.010,'angle':.09,'offAngle':-.045,'onAngle':.045,'housingVolumeM3':volume,'rockerVolumeM3':button_volume,'unchangedObjects':len(before)}
s['parent_web_revision']='courtyard43-switch31';s['web_revision']='courtyard43-switch32';s['switch32']=json.dumps(details)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':s['web_revision'],**details}
