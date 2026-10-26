"""switch28 -> mirror29. Reuse the approved Yongwang door mirror.

Execute through official Blender Lab MCP; no other room objects are altered.
Mirror size is reused asset geometry, placement on the photographed door is
estimated. Source glass is 4 mm thick, with a 0.04 mm reflection clearance.
"""
from pathlib import Path
import bpy, ast, hashlib, json, math
from mathutils import Matrix, Vector

ROOT=Path(__file__).resolve().parents[3]; ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-switch28'
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
before={o.name:digest(o) for o in scene.objects}
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
names=['wardrobe-right-inner-mirror-reflection','wardrobe-right-inner-mirror-glass-edge']
with bpy.data.libraries.load(str(source),link=False) as (a,b):
    assert all(n in a.objects for n in names)
    b.objects=names
pivot=bpy.data.objects['C43_WardrobeDoorFarPivot']
records=[]
for src,name,x in zip(b.objects,['C43_WardrobeFarMirror_Reflection','C43_WardrobeFarMirror_Edge'],[.03304,.033]):
    me=src.data.copy(); me.name=name+'_mesh'
    # Object-level material overrides in the complete source take precedence.
    material=src.material_slots[0].material.copy(); material.name=name+'_material'
    if 'web_material_id' in material:del material['web_material_id']
    material['web_userData']=json.dumps({'sourceRoom':'yongwang-jiayuan','sourceObject':src.name,'sourceBaseline':'ce9e183 / props44a (unchanged in props45)'})
    me.materials.clear();me.materials.append(material)
    o=bpy.data.objects.new(name,me);scene.collection.objects.link(o)
    o.parent=pivot;o.matrix_parent_inverse=Matrix.Identity(4)
    o.location=(x,-.2775,1.025);o.rotation_euler=(0,0,math.pi/2)
    o['web_userData']=json.dumps({'noCollision':True,'noShadow':True,'mirrorSurface':name.endswith('Reflection'),'sourceAsset':src.name})
    o['web_tags']=json.dumps({'cutaway':True})
    assert len(o.data.vertices)==len(src.data.vertices)
    assert all((v.co-s.co).length<1e-9 for v,s in zip(o.data.vertices,src.data.vertices))
    records.append({'name':name,'source':src.name,'localX':x,'sizeM':[.265,1.385],'sourceMeshUnchanged':True})
    bpy.data.objects.remove(src,do_unlink=True)
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items()),'Unrelated object changed'
scene['parent_web_revision']='courtyard43-switch28';scene['web_revision']='courtyard43-mirror29'
scene['mirror29']=json.dumps({'source':'yongwang-jiayuan / ce9e183 mirror','door':'Far near window','placement':'photo estimate','records':records,'unchangedObjects':len(before)})
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')}
exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns)
ns['export_interior']()
result={'revision':scene['web_revision'],'records':records,'unchangedObjects':len(before)}
