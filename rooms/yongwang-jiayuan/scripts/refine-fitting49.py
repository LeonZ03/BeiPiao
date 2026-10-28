"""doorframe48 -> fitting49: seated entrance leaf, ceiling lamp and real sockets.

Official Blender Lab MCP only. Move the complete fixed door hierarchy, including
its hinges, lever and charm. Add physical timber stops behind the small edge gaps.
Socket apertures use the visible arrangement in Bull's GN-109K official images:
https://www.gongniu.cn/show-24-1247-1.html . This calibrates the unbranded existing
strip's openings, not a claim that the photographed strip is that exact model.
"""
from pathlib import Path
import bpy,bmesh,copy,math,json
from mathutils import Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='doorframe48'
bpy.context.preferences.filepaths.save_version=0

def moved(nid,dx=0,dy=0,dz=0):
    o=obs[nid];o.location.x+=dx;o.location.z+=dy;o.location.y-=dz
    bpy.context.view_layer.update()
    data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);changed.add(nid)

def bounds(o):
    p=[o.matrix_world@Vector(v) for v in o.bound_box]
    return [(min((v.x,v.z,-v.y)[i] for v in p),max((v.x,v.z,-v.y)[i] for v in p)) for i in range(3)]

def solid_world(name,lo,hi,mid,parent):
    inverse=obs[parent].matrix_world.inverted()
    corners=[(x,y,z) for x,y,z in [(0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)]]
    verts=[inverse@Vector(bp([lo[i]+(hi[i]-lo[i])*v[i] for i in range(3)])) for v in corners]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)])
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.0006,segments=2,affect='EDGES');bm.to_mesh(me);bm.free()
    uv=me.uv_layers.new(name='UVMap')
    for l in me.loops:
        v=me.vertices[l.vertex_index].co;uv.data[l.index].uv=(v.x*.4,v.z*.4)
    me.uv_layers.new(name='UV1',do_init=True)
    o=attach(me,name,mid,parent);export(o)
    data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]['attributes']['uv1']=copy.deepcopy(data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]['attributes']['uv'])
    return o

# Cover the bare plaster returns. Move only the inner edge bands, preserving
# the casing face, outer footprint and bevel radii instead of scaling the frame.
for nid,limit,delta in [(88,2.23,-.0045),(89,3.15,-.006)]:
    o=obs[nid];o.data=o.data.copy();inverse=o.matrix_world.inverted()
    for v in o.data.vertices:
        p=o.matrix_world@v.co;z=-p.y
        if (nid==88 and z>limit) or (nid==89 and z<limit):
            p.y-=delta;v.co=inverse@p
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    export(o)
    data['geometries'][data['nodes'][nid]['geometry']]['attributes']['uv1']=copy.deepcopy(data['geometries'][data['nodes'][nid]['geometry']]['attributes']['uv'])
# Keep a modest room-side recess and side clearance; move the whole hierarchy.
moved(1642,dx=.020,dz=-.005)
leaf_bounds=bounds(obs[1643]);stop_front=leaf_bounds[0][1]+.002
old_stop=bounds(obs[92]);moved(92,dx=stop_front-old_stop[0][0],dz=-.005)
stop_depth=old_stop[0][1]-old_stop[0][0];height=old_stop[1][0]
timber=data['nodes'][92]['material']
front_z=leaf_bounds[2][0];back_z=leaf_bounds[2][1]
solid_world('Entrance49 continuous latch-side stop',(stop_front,0,front_z-.012),(stop_front+stop_depth,height,front_z+.006),timber,88)
solid_world('Entrance49 continuous hinge-side stop',(stop_front,0,back_z-.006),(stop_front+stop_depth,height,back_z+.012),timber,89)

# Seat the existing lamp body on the actual ceiling, preserving both shapes.
ceiling_y=bounds(obs[119])[1][0]
lamp_delta=ceiling_y-bounds(obs[1479])[1][1]
assert .05<lamp_delta<.06
for nid in [1479,1480]:moved(nid,dy=lamp_delta)

# The former face and shutter stack hid the old hole layout. Rebuild only the
# three socket faces; carve the same openings into the body beneath them.
body=obs[1051];body.data=body.data.copy()
body_mid=data['nodes'][1051]['material']
white=data['nodes'][1974]['material'];dark=data['nodes'][1975]['material']
slot_specs=[(-.0065,0,.0026,.0073,0),(.0065,0,.0026,.0073,0),(0,0,.0028,.0085,0),(-.0085,.016,.0027,.0085,math.pi/6),(.0085,.016,.0027,.0085,-math.pi/6)]

def blank(nid,center,size,mid):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector(bp([center[i]+size[i]*v.co[i] for i in range(3)]))
    me=bpy.data.meshes.new('Fitting49 socket %d'%nid);bm.to_mesh(me);bm.free()
    o=obs[nid];o.data=me;o.modifiers.clear();o.matrix_local=Matrix.Identity(4)
    bpy.context.view_layer.update();data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C)
    me.materials.append(mats[mid]);set_material(nid,mid)
    return o

def finish_socket(o,mid,bevel):
    activate(o)
    if bevel:
        mod=o.modifiers.new('Soft moulded aperture lips','BEVEL');mod.width=bevel;mod.segments=2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    o.data.materials.clear();o.data.materials.append(mats[mid])
    for p in o.data.polygons:p.material_index=0
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for old in list(o.data.uv_layers):o.data.uv_layers.remove(old)
    uv=o.data.uv_layers.new(name='UVMap')
    for l in o.data.loops:
        v=o.data.vertices[l.vertex_index].co;uv.data[l.index].uv=(v.x,v.y)
    o.data.uv_layers.new(name='UV1',do_init=True)
    export(o)
    data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]['attributes']['uv1']=copy.deepcopy(data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]['attributes']['uv'])

for i,z in enumerate([-.06,0,.06]):
    face=blank(1974+i*2,(0,.025,z),(.069,.004,.051),white)
    for x,dz,w,length,angle in slot_specs:
        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter=bpy.context.object;cutter.dimensions=(w,length,.016)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        cutter.parent=obs[1050];cutter.location=bp((x,.026,z+dz));cutter.rotation_euler.z=angle
        bpy.context.view_layer.update()
        for target in [face,body]:
            activate(target);mod=target.modifiers.new('Recessed plug aperture','BOOLEAN')
            mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
            bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
    finish_socket(face,white,.00025)
    # Unused safety doors sit near the opening; the occupied unit is depressed
    # by its plug. The blind cavity remains deeper than either visible shutter.
    shutter=blank(1975+i*2,(0,.0245 if i<2 else .019,z),(.063,.002,.045),dark)
    finish_socket(shutter,dark,0)
finish_socket(body,body_mid,0)

# The existing black AC plug and both leads stay in place; its two blades now
# enter the corrected pair, which is aligned with the existing plug centre.
for x in [-.0065,.0065]:
    o=box('Fitting49 inserted AC blade',(x,.0239,.06),(.0016,.0078,.0055),118,1050,.0002)
    o.name='Fitting49 inserted AC blade %.4f'%x;o['web_name']=o.name
    data['nodes'][int(o['web_node_id'])]['name']=o.name

details=copy.deepcopy(before['statistics'].get('exteriorRefinement',{}))
details['fitting49']={'parent':'doorframe48','doorAssemblyShiftM':.020,'doorAssemblyShiftZM':-.005,'doorStopGapM':.002,'lampRaiseM':lamp_delta,'socketReference':'https://www.gongniu.cn/show-24-1247-1.html','socketPattern':'three aligned straight slots, two 30 degree angled slots; recessed wells','hiddenDimensions':'estimated'}
report=save('fitting49',details)
result={'revision':report['revision'],'changedNodes':report['changedNodes'],'geometryChanged':report['geometryChanged'],'lampRaiseM':lamp_delta,'doorStopFront':stop_front}
