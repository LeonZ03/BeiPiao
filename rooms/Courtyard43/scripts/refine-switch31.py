"""mirror29a -> switch31: one closed rocker housing with a shallow backed well.

Official Blender Lab MCP only. 86 mm format and internal construction are
generic estimates, not a claimed brand/CAD. Yongwang appends these final meshes.
"""
from pathlib import Path
import bpy, bmesh, math, json, ast, hashlib
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-mirror29a'
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),'<digest>','exec'))
targets={'C43_Switch_Backplate','C43_Switch_Rocker','C43_Switch_Pivot','C43_Switch28_reveal'}
before={o.name:digest(o) for o in s.objects if o.name not in targets}

def finish_mesh(name,verts,faces,bevel):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    edges=[e for e in bm.edges if e.is_manifold and e.calc_face_angle()>.21]
    bmesh.ops.bevel(bm,geom=edges,offset=bevel,segments=4,affect='EDGES',clamp_overlap=True)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges),'Housing must be a sealed solid'
    assert all(f.calc_area()>1e-14 for f in bm.faces)
    volume=bm.calc_volume(signed=True);assert volume>0
    bm.to_mesh(me);bm.free();me.update()
    uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth=max(abs(v) for v in p.normal)<.9999
        axes=sorted(range(3),key=lambda i:abs(p.normal[i]))[:2]
        for li in p.loop_indices:
            co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]],co[axes[1]])
    return me,volume

def rounded_loop(x,width,height,radius):
    points=[]
    for cy,cz,start in [(width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,math.pi/2),(-width/2+radius,-height/2+radius,math.pi),(width/2-radius,-height/2+radius,3*math.pi/2)]:
        for i in range(8):
            a=start+i*math.pi/16;points.append((x,cy+radius*math.cos(a),cz+radius*math.sin(a)))
    return points

n=32
loops=[rounded_loop(.00425,.086,.086,.002),rounded_loop(-.00425,.086,.086,.002),rounded_loop(-.00425,.068,.067,.001),rounded_loop(.00355,.068,.067,.001)]
verts=sum(loops,[]);faces=[]
for a,b in [(0,1),(1,2),(2,3)]:
    for i in range(n):j=(i+1)%n;faces.append((a*n+i,a*n+j,b*n+j,b*n+i))
faces.extend([tuple(range(n-1,-1,-1)),tuple(3*n+i for i in range(n))])
housing,volume=finish_mesh('Switch31 sealed housing and recess floor',verts,faces,.00022)
bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
for v in bm.verts:v.co=Vector((v.co.x*.007,v.co.y*.065,v.co.z*.064))
bm.verts.ensure_lookup_table();bm.verts.index_update()
rocker,button_volume=finish_mesh('Switch31 closed rocker skirt',[tuple(v.co) for v in bm.verts],[tuple(v.index for v in f.verts) for f in bm.faces],.0008);bm.free()

plate=bpy.data.objects['C43_Switch_Backplate'];button=bpy.data.objects['C43_Switch_Rocker'];pivot=bpy.data.objects['C43_Switch_Pivot']
material=plate.material_slots[0].material.copy();material.name='Switch31 warm white PC'
material['web_props']=json.dumps({'roughness':.48,'metalness':0,'side':0,'depthWrite':True})
for o,me in [(plate,housing),(button,rocker)]:
    o.data=me;me.materials.append(material)
    for slot in o.material_slots:slot.link='DATA'
    o['switch31_closed_solid']=True
plate.location.x=2.225-.00375
pivot.location.x=2.225-.0065
desc=json.loads(pivot['c43_interaction']);desc['angle']=.045;pivot['c43_interaction']=json.dumps(desc)
old=bpy.data.objects['C43_Switch28_reveal'];old.hide_render=True;old.hide_set(True)
old['retired_reason']='Coplanar dark box caused flicker; backed well is part of sealed housing'
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[name])==h for name,h in before.items()),'Unrelated source object changed'
details={'parent':'courtyard43-mirror29a','wallX':2.225,'wallEmbedM':.0005,'wellFloorX':2.2248,'rockerCenterX':2.2185,'angle':.045,'housingVolumeM3':volume,'rockerVolumeM3':button_volume,'unchangedObjects':len(before),'source':'unbranded 86 mm estimated construction'}
s['parent_web_revision']='courtyard43-mirror29a';s['web_revision']='courtyard43-switch31';s['switch31']=json.dumps(details)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':s['web_revision'],**details}
