"""logo26 -> charger27. Reuse the approved Yongwang black power supply.

Run only via official Blender Lab MCP. Independent meshes/materials, unchanged
desk/laptop/outlet anchors. Cable slack is fitted here, not copied across rooms.
"""
from pathlib import Path
import bpy,json,math,ast,hashlib
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-logo26'
bp=lambda p:Vector((p[0],-p[2],p[1]))
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
before={o.name:digest(o) for o in scene.objects}
targets={'C43_Desk_small_dark_device','C43_Desk_power_cable','C43_Desk_power_plug','C43_Power15_ac_strain','C43_Power15_adapter_ac','C43_Power15_adapter_dc','C43_Inspiron25_DC_lead','C43_Inspiron25_DC_barrel'}
for n in targets:
    o=bpy.data.objects[n];o.hide_render=True;o.hide_set(True)
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
sha=hashlib.sha256(source.read_bytes()).hexdigest()
assert json.loads((ROOT/'room-site/dist/assets/full-room/scene.json').read_text('utf8'))['revision']=='props43'
names=['Laptop42 black adapter lower case','Laptop42 black adapter upper case','Laptop42 adapter case seam','Laptop42 AC input strain relief','Laptop42 DC output strain relief','Laptop42 black AC plug','Laptop42 DC barrel sleeve','Laptop42 DC barrel strain relief']
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=list(names)
assert all(dst.objects)
cache={};added=[]
rot=Matrix.Rotation(-math.pi/2,4,'Z') # Blender Z == web Y
# Old adapter lower edge .800; new lower edge .740, on the same desk surface.
xf=Matrix.Translation(bp((-1.82,.753,.43)))@rot@Matrix.Translation(-bp((.195,.813,-.130)))
root=bpy.data.objects['C43_Inspiron25_detailed-laptop']
for o,n in zip(dst.objects,names):
    scene.collection.objects.link(o);o.parent=None;o.matrix_world=Matrix.Identity(4);o.data=o.data.copy()
    for slot in o.material_slots:
        old=slot.material
        if old.name not in cache:
            m=old.copy();m.name='C43_Charger27_'+old.name
            m['web_props']=json.dumps({'roughness':.91 if 'cord' in old.name else .76,'metalness':0});cache[old.name]=m
        slot.link='DATA';slot.material=cache[old.name]
    o.name='C43_Charger27_'+n.replace('Laptop42 ','');o['web_tags']=json.dumps({'noCollision':True});o['web_userData']=json.dumps({'reusedFrom':'Yongwang props43','sourceObject':n});o.hide_render=False;o.hide_set(False)
    if 'barrel' in n:
        o.matrix_world=root.matrix_world.copy()
    elif n=='Laptop42 black AC plug':
        # Rotate the socket insertion direction from downwards to the left wall.
        C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
        o.matrix_world=Matrix.Translation(bp((-1.978,.782,.845)))@C@Matrix.Rotation(-math.pi/2,4,'Z')@C.inverted()@Matrix.Translation(-bp((.205,.839,.178)))
    else:o.matrix_world=xf
    added.append(o)
rubber=next(m for name,m in cache.items() if 'cord' in name)
def cable(name,points,r):
    cr=bpy.data.curves.new(name,'CURVE');cr.dimensions='3D';cr.resolution_u=18;cr.bevel_depth=r;cr.bevel_resolution=3;cr.use_fill_caps=True
    sp=cr.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=bp(co);p.handle_left_type=p.handle_right_type='AUTO'
    bpy.ops.object.select_all(action='DESELECT');o=bpy.data.objects.new(name,cr);scene.collection.objects.link(o);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    o.data.materials.append(rubber);o.data.uv_layers.new(name='UVMap');o['web_tags']=json.dumps({'noCollision':True});added.append(o);return o
# Plug exits downwards; keep the existing free sag beside the desk.
cable('C43_Charger27_AC_lead',[(-1.978,.769,.845),(-1.950,.746,.842),(-1.911,.579,.806),(-1.88,.509,.710),(-1.903,.553,.609),(-2.006,.693,.502),(-2.008,.763,.459),(-1.920,.769,.433),(-1.877,.760,.430)],.0025)
dc=cable('C43_Charger27_DC_lead',[(-1.764,.760,.430),(-1.754,.759,.413),(-1.754,.755,.375),(-1.779,.750,.300),(-1.770,.747,.222),(-1.751,.7465,.207)],.0018)
# Exclude cable/connector intersections with the keyboard and lid footprint.
bpy.context.view_layer.update();inv=root.matrix_world.inverted()
for v in dc.data.vertices:
    p=inv@v.co;assert p.x<-.158,('DC cable enters laptop envelope',tuple(p))
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets)
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
scene['parent_web_revision']='courtyard43-logo26';scene['web_revision']='courtyard43-charger27';scene['charger27']=json.dumps({'sourceRevision':'props43','sourceSHA256':sha,'sourceObjects':names,'newObjects':[o.name for o in added],'unchanged':len(before)-len(targets)})
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':scene['web_revision'],'sourceUnchanged':True,'unchangedObjects':len(before)-len(targets),'added':len(added)}
