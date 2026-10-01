"""Official MCP: curved ink tessellation and unprinted white label reverse."""
import bpy,bmesh,math,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior16' and not s.get('nongfu16_finished')
web=lambda p:Vector((p[0],p[2],-p[1]));bp=lambda p:Vector((p[0],-p[2],p[1]))
for o in list(s.objects):
    if not o.name.startswith('C43_Nongfu16_logo_'):continue
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=12,use_grid_fill=True)
    inv=o.matrix_world.inverted();radius=.04412+(.00010 if o.name.endswith('_snow') else 0)
    for v in bm.verts:
        p=web(o.matrix_world@v.co);a=math.atan2(p.x-.56,p.z-.215)
        p.x=.56+radius*math.sin(a);p.z=.215+radius*math.cos(a);v.co=inv@bp(p)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
o=bpy.data.objects['C43_Bottle_label']
for p in o.data.polygons:
    mid=web(o.matrix_world@p.center);normal=o.matrix_world.to_3x3()@p.normal;n=web(normal)
    if n.x*(mid.x-.56)+n.z*(mid.z-.215)<0:p.material_index=1
pet=bpy.data.materials['C43_Nongfu16_clear_PET'];props=json.loads(pet['web_props']);props['opacity']=.18;pet['web_props']=json.dumps(props)
next(n for n in pet.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Alpha'].default_value=.18
s['nongfu16_finished']=True
def add_emboss():
    """Thickened clear PET along the three shallow arched moulding ribs."""
    m=bpy.data.materials['C43_Nongfu16_clear_PET'].copy();m.name='C43_Nongfu16_moulded_ribs'
    p=json.loads(m['web_props']);p.update(opacity=.32,roughness=.14);m['web_props']=json.dumps(p)
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Alpha'].default_value=.32;bs.inputs['Roughness'].default_value=.14
    cr=bpy.data.curves.new('C43_Nongfu16_moulded_arches','CURVE');cr.dimensions='3D';cr.bevel_depth=.00042;cr.bevel_resolution=2;cr.resolution_u=1
    for center in [.182,.193,.204]:
        sp=cr.splines.new('POLY');sp.points.add(159);sp.use_cyclic_u=True
        for i,pnt in enumerate(sp.points):
            a=math.tau*i/160;h=center+.007*(.5+.5*math.cos(4*a))
            if h<=.193:r=.0435-(h-.174)*(.0003/.019)
            else:r=.0432-(h-.193)*(.0012/.020)
            pnt.co=(*bp((.56+(r+.0012)*math.sin(a),1.0125+h,.215+(r+.0012)*math.cos(a))),1)
    o=bpy.data.objects.new('C43_Nongfu16_moulded_arches',cr);bpy.context.scene.collection.objects.link(o);cr.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    o['web_tags']=json.dumps({'noCollision':True});uv=o.data.uv_layers.new(name='UVMap')
    for poly in o.data.polygons:
        for li in poly.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.z)
add_emboss()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';ns={'__file__':str(p)};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns)
result=ns['export_interior']()
