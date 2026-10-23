"""props24 -> laptop25: isolated reuse of Inspiron41, official Blender MCP only.
Room anchor and default closed state preserved. SKU is still an estimate.
"""
from pathlib import Path
import bpy,bmesh,json,math,ast,hashlib
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-props24'
bp=lambda p:Vector((p[0],-p[2],p[1]))
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
before={o.name:digest(o) for o in scene.objects}
oldroot=next(o for o in scene.objects if o.name=='C43_Reuse24_detailed-laptop')
anchor=oldroot.matrix_world.copy();targets={o.name for o in [oldroot,*oldroot.children_recursive]}
for name in targets:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)

source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'room-site/dist/assets/full-room/scene.json').read_text(encoding='utf8'))
assert manifest['revision']=='inspiron41'
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=list(src.objects)
loaded={int(o['web_node_id']):o for o in dst.objects if o and 'web_node_id' in o}
keep={loaded[1132],loaded[1220]}
keep.update(o for o in loaded[1132].children_recursive if not o.hide_render and o.get('purpose')!='Inspiron41 USB connector')
for o in list(dst.objects):
    if o and o not in keep:bpy.data.objects.remove(o,do_unlink=True)
matcache={}
for o in keep:
    scene.collection.objects.link(o);nid=int(o['web_node_id']);o.name='C43_Inspiron25_'+(o.get('web_name') or str(nid))
    o.hide_render=False;o.hide_set(False);o['web_tags']=json.dumps({'noCollision':True})
    meta=json.loads(o.get('web_user_data','{}'));meta.pop('authoring',None);o['web_userData']=json.dumps(meta)
    if o.type!='MESH':continue
    o.data=o.data.copy()
    mid=manifest['nodes'][nid]['material'];d=manifest['materials'][mid]
    if mid not in matcache:
        assert not d.get('textures')
        old=next(s.material for s in o.material_slots if s.material and int(s.material.get('web_material_id',-1))==mid)
        m=old.copy();m.name='C43_Inspiron25_'+old.name;m['web_props']=json.dumps(d['props']);matcache[mid]=m
    o.data.materials.clear();o.data.materials.append(matcache[mid]);o.material_slots[0].link='DATA'
    for face in o.data.polygons:face.material_index=0
root=loaded[1132];root.parent=None;root.matrix_world=anchor
root['web_userData']=json.dumps({'laptopRoot':True,'defaultOpen':False,'modelCandidate':'Dell Inspiron 14 5430','modelConfirmed':False})
root['reuse']='Yongwang inspiron41; independent mesh/material copies; approved anchor unchanged'
lid=loaded[1220];lid.rotation_euler.x=math.pi/2
lid['web_userData']=json.dumps({'laptopLid':True,'defaultOpen':False,'openAngle':-.21,'closedAngle':math.pi/2})
lid['c43_interaction']=json.dumps({'id':'laptop','kind':'laptop','axis':'x','openAngle':-.21-math.pi/2,'defaultOpen':False})

# Reconnect existing power adapter to the left rear DC jack on the narrower case.
rubber=bpy.data.objects['C43_Power15_adapter_output'].data.materials[0]
for name in ['C43_Power15_adapter_output','C43_Power15_laptop_connector']:
    targets.add(name);bpy.data.objects[name].hide_render=True;bpy.data.objects[name].hide_set(True)
bpy.context.view_layer.update();p=root.matrix_world@bp((-.160,0,-.088));end=(p.x,p.z,-p.y)
points=[(-1.781,.754,.430),(-1.766,.758,.425),(-1.754,.757,.391),(-1.779,.752,.300),(-1.770,.747,.222),end]
cr=bpy.data.curves.new('Inspiron25 continuous DC lead','CURVE');cr.dimensions='3D';cr.resolution_u=16;cr.bevel_depth=.0018;cr.bevel_resolution=3;cr.use_fill_caps=True
sp=cr.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
for p,co in zip(sp.bezier_points,points):p.co=bp(co);p.handle_left_type=p.handle_right_type='AUTO'
ob=bpy.data.objects.new('C43_Inspiron25_DC_lead',cr);scene.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True)
bpy.ops.object.convert(target='MESH');ob.data.materials.append(rubber);ob.data.uv_layers.new(name='UVMap')
# Cylindrical barrel plug coaxial with the power jack, including strain relief.
bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.00235,depth=.011,location=bp((end[0]-.001,end[1],end[2])),rotation=(0,math.pi/2,0))
plug=bpy.context.object;plug.name='C43_Inspiron25_DC_barrel';plug.data.materials.append(rubber)
for o in [ob,plug]:o['web_tags']=json.dumps({'noCollision':True})

bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets),'Unrelated source object changed'
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
scene['parent_web_revision']='courtyard43-props24';scene['web_revision']='courtyard43-laptop25'
scene['laptop25']=json.dumps({'source':'Yongwang inspiron41','sourceSHA256':source_hash,'modelConfirmed':False,'unchangedObjects':len(before)-len(targets),'anchor':list(root.location)})
bpy.context.preferences.filepaths.save_version=0
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath,library=im.library),start=str(ROOM/'assets/full-room'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text(encoding='utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':scene['web_revision'],'unchangedObjects':len(before)-len(targets),'laptopMeshes':len(keep)-2}
