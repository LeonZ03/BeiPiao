"""laptop25 -> logo26. Only replace the mirrored cover emblem via official MCP."""
from pathlib import Path
import bpy, json, ast, hashlib
ROOM=Path(__file__).resolve().parents[1];ROOT=ROOM.parents[1]
assert bpy.context.scene.get('web_revision')=='courtyard43-laptop25'
name='C43_Inspiron25_Inspiron41 lid Inspiron41 Dell inset graphite mark'
target=bpy.data.objects[name];oldmatrix=target.matrix_world.copy();material=target.data.materials[0]
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
assert json.loads((ROOT/'room-site/dist/assets/full-room/scene.json').read_text('utf8'))['revision']=='laptop42'
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
before={o.name:digest(o) for o in bpy.context.scene.objects if o!=target}
with bpy.data.libraries.load(str(source),link=False) as (src,dst):
    dst.meshes=['DELL outside-facing bold emblem']
assert len(dst.meshes)==1 and dst.meshes[0]
target.data=dst.meshes[0];target.data.materials.clear();target.data.materials.append(material);target.material_slots[0].link='DATA'
bpy.context.view_layer.update();assert target.matrix_world==oldmatrix
assert all(digest(bpy.data.objects[n])==h for n,h in before.items())
bpy.context.scene['parent_web_revision']='courtyard43-laptop25';bpy.context.scene['web_revision']='courtyard43-logo26'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':'courtyard43-logo26','unchangedObjects':len(before),'target':name}
