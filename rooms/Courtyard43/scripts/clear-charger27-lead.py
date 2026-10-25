"""charger27 -> charger27a: route the AC lead over the desk front, clear of legs.
Official Blender Lab MCP only; unchanged plug, adapter, laptop and furnishings.
"""
from pathlib import Path
import bpy,ast,hashlib
from mathutils import Vector
ROOM=Path(__file__).resolve().parents[1];scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-charger27'
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
ob=bpy.data.objects['C43_Charger27_AC_lead'];before={o.name:digest(o) for o in scene.objects if o!=ob};mat=ob.data.materials[0]
points=[(-1.978,.769,.845),(-1.942,.729,.846),(-1.905,.578,.810),(-1.880,.515,.720),(-1.852,.603,.636),(-1.852,.748,.615),(-1.862,.764,.583),(-1.889,.750,.526),(-1.898,.751,.463),(-1.877,.760,.430)]
cr=bpy.data.curves.new('Charger27 front edge clearance','CURVE');cr.dimensions='3D';cr.resolution_u=18;cr.bevel_depth=.0025;cr.bevel_resolution=3;cr.use_fill_caps=True
sp=cr.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
for p,co in zip(sp.bezier_points,points):p.co=(co[0],-co[2],co[1]);p.handle_left_type=p.handle_right_type='AUTO'
bpy.ops.object.select_all(action='DESELECT');tmp=bpy.data.objects.new('temporary cable',cr);scene.collection.objects.link(tmp);tmp.select_set(True);bpy.context.view_layer.objects.active=tmp;bpy.ops.object.convert(target='MESH')
ob.data=tmp.data.copy();bpy.data.objects.remove(tmp,do_unlink=True);ob.data.materials.append(mat);ob.data.uv_layers.new(name='UVMap')
# Below the board, the wire stays in front of its 580 mm front edge; the
# curve rises above the surface before entering the tabletop footprint.
for v in ob.data.vertices:
    x,y,z=v.co.x,v.co.z,-v.co.y
    assert not(-2<x<-.7 and .03<z<.58 and .71<y<.74),('Board intersection',x,y,z)
    assert not(-1.972<x<-1.938 and .517<z<.553 and y<.713),('Leg intersection',x,y,z)
assert all(digest(bpy.data.objects[n])==h for n,h in before.items())
scene['parent_web_revision']='courtyard43-charger27';scene['web_revision']='courtyard43-charger27a'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':scene['web_revision'],'changedObjects':1,'deskClearance':True}
