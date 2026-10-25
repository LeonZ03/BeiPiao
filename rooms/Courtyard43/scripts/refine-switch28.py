"""charger27a -> switch28. Conventional wall rocker; official Blender Lab MCP.

Shared visual specification with Yongwang props44; independent mesh/material.
86 mm format estimated from a generic single-gang PC rocker, no invented brand.
"""
from pathlib import Path
import bpy,bmesh,json,ast,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-charger27a'
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
before={o.name:digest(o) for o in scene.objects}
targets={'C43_Switch_Backplate','C43_Switch_Rocker','C43_Switch_Pivot'}
mat=bpy.data.materials.new('C43_Switch28_white_PC');mat.use_nodes=True
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
def lin(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
bs.inputs['Base Color'].default_value=(*[lin(v) for v in [.87,.86,.81]],1);bs.inputs['Roughness'].default_value=.48
mat['web_props']=json.dumps({'roughness':.48,'metalness':0})
dark=mat.copy();dark.name='C43_Switch28_recess';next(n for n in dark.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=(*[lin(v) for v in [.24,.24,.22]],1)
def geometry(name,size,bevel):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector([size[i]*v.co[i] for i in range(3)])
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=4,affect='EDGES');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.uv_layers.new(name='UVMap');return me
plate=bpy.data.objects['C43_Switch_Backplate'];plate.data=geometry('Switch28 plate',(.006,.086,.086),.0014);plate.data.materials.append(mat);plate.location.x=2.222
pivot=bpy.data.objects['C43_Switch_Pivot'];pivot.location.x=2.217
rocker=bpy.data.objects['C43_Switch_Rocker'];rocker.data=geometry('Switch28 rocker',(.005,.065,.064),.0012);rocker.data.materials.append(mat);rocker.location=(0,0,0)
gap=bpy.data.objects.new('C43_Switch28_reveal',geometry('Switch28 recess',(.001,.068,.067),.0003));scene.collection.objects.link(gap);gap.location=(2.2195,-2.4,1.26);gap.data.materials.append(dark);gap['web_tags']=json.dumps({'cutaway':True})
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets)
scene['parent_web_revision']='courtyard43-charger27a';scene['web_revision']='courtyard43-switch28'
scene['switch28']=json.dumps({'format':'unbranded 86 mm estimated','frontProjectionM':.0105,'unchangedObjects':len(before)-3})
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':scene['web_revision'],'unchangedObjects':len(before)-3,'rockerTravelDeg':5.73}
