"""balcony38 -> finish39. Official Blender Lab MCP only.

Apply the same cap shape functions as Yongwang finish50 to its independent
local mesh copies. Root, wall hook, LA embroidery and materials remain local.
"""
from pathlib import Path
import bpy,bmesh,ast,json,math,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
assert bpy.context.scene.get('web_revision')=='courtyard43-balcony38'
bpy.context.preferences.filepaths.save_version=0
def functions(path,names):
    tree=ast.parse(path.read_text('utf8'));body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
    assert len(body)==len(names);exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),globals())
functions(ROOT/'rooms/yongwang-jiayuan/scripts/refine-finish50.py',{'cap_crown','cap_bill'})
functions(ROOM/'scripts/refine-furnishings.py',{'digest'})
targets=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('C43_Baseball15_')]
assert len(targets)==24
before={o.name:digest(o) for o in bpy.context.scene.objects if o not in targets}
for o in targets:
    o.data=o.data.copy();fn=cap_bill if 'bill' in o.name else cap_crown
    for v in o.data.vertices:
        p=Vector((v.co.x,v.co.z,-v.co.y));q=fn(p);v.co=(q[0],-q[2],q[1])
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
    o['reuse_finish39']='Yongwang finish50 cap shape; independent mesh and original Courtyard materials/root'
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items())
s=bpy.context.scene;s['parent_web_revision']='courtyard43-balcony38';s['web_revision']='courtyard43-finish39'
s['finish39']=json.dumps({'capSource':'Yongwang finish50, same cap_crown/cap_bill mapping','unchangedObjects':len(before),'wind':'runtime only; no cloth shape or material changes'})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns)
result={**ns['export_interior'](),'unchangedObjects':len(before)}
