"""handles39 -> laptop40. Run through official Blender Lab MCP only.

Preserve the accepted laptop and desk anchors; add Dell markings and real lid
clearance. Socket/cable dimensions and concealed routing are visual estimates.
"""
from pathlib import Path
import bpy, bmesh, math, json, copy
from mathutils import Matrix, Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text(encoding='utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='handles39'
bpy.context.preferences.filepaths.save_version=0

def metadata(nid,extra):
    meta={**data['nodes'][nid].get('userData',{}),**extra}
    obs[nid]['web_user_data']=json.dumps(meta);data['nodes'][nid]['userData']=meta;changed.add(nid)

obs[1225].hide_render=True;data['nodes'][1225]['visible']=False;changed.add(1225)
metadata(1132,{'laptopRoot':True,'defaultOpen':True})
metadata(1220,{'laptopLid':True,'axis':'x','closedAngle':math.pi/2,'openAngle':-.21,'defaultOpen':True})
lid=obs[1220];lid.location.z=.019;bpy.context.view_layer.update()
data['nodes'][1220]['matrix']=flat(C.inverted()@lid.matrix_local@C)

def finish_mesh(o,name,mid,parent):
    bpy.context.view_layer.update();me=o.data.copy();me.transform(o.matrix_world)
    bpy.data.objects.remove(o,do_unlink=True)
    if not me.uv_layers:
        uv=me.uv_layers.new(name='UVMap')
        for l in me.loops:uv.data[l.index].uv=(me.vertices[l.vertex_index].co.x,me.vertices[l.vertex_index].co.z)
    ob=attach(me,name,mid,parent);export(ob);return ob

ink=material('Dell subdued silver mark',125,[.66,.68,.69],.55,{},metalness=.25,side=2)
silver=material('Hinge satin alloy',118,[.56,.58,.60],.34,{},metalness=.65)
for x in [-.12,.12]:box('Laptop connected hinge riser',(x,.012,-.112),(.036,.021,.012),silver,1132,.002)

# Outer cover lettering faces away from the display; no luminous decal.
for label,cy,cz,size,angle in [('cover',.117,-.00365,.0105,-math.pi/2),('bezel',.012,.006,.0037,math.pi/2)]:
    for i,ch in enumerate('DELL'):
        cu=bpy.data.curves.new('Dell glyph','FONT');cu.body=ch;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.extrude=.000035;cu.resolution_u=5
        ob=bpy.data.objects.new('Dell glyph',cu);bpy.context.scene.collection.objects.link(ob)
        # Text XY maps to Blender XZ, normal toward exterior +Y for cover.
        ob.location=bp(((i-1.5)*size*.66,cy,cz));ob.rotation_euler=(angle,0,0)

        if ch=='E':ob.rotation_euler.rotate_axis('Z',-.36)
        activate(ob);bpy.ops.object.convert(target='MESH');finish_mesh(ob,'DELL '+label+' '+str(i),ink,1220)
    if label=='cover':
        verts=[];faces=[]
        for i in range(97):
            a=i/96*math.tau
            for r in [.024,.0246]:verts.append((r*math.cos(a),cy+r*math.sin(a),cz-.00008))
        for i in range(96):faces.append((2*i,2*i+1,2*i+3,2*i+2))
        ob=attach(mesh('Dell circle',verts,faces), 'DELL cover circle',ink,1220);export(ob)

# Replace fake raised black bars with genuine recessed two-pin/three-pin holes.
white=material('Extension socket moulded warm ABS',91,[.86,.85,.80],.56,{})
dark=material('Socket recessed safety shutters',90,[.045,.046,.043],.95,{})
for nid in range(1052,1064):
    obs[nid].hide_render=True;data['nodes'][nid]['visible']=False;changed.add(nid)
for slot,z in enumerate([-.06,0,.06]):
    panel=box('Socket face '+str(slot),(0,.025,z),(.069,.004,.051),white,1050,.002)
    nid=int(panel['web_node_id'])
    for j,(x,dz,w,h,rot) in enumerate([(-.010,-.012,.0034,.010,0),(.010,-.012,.0034,.010,0),(0,.000,.0036,.008,0),(-.010,.012,.0036,.011,-.48),(.010,.012,.0036,.011,.48)]):
        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter=bpy.context.object;cutter.dimensions=(w,h,.014);cutter.location=bp((x,.025,z+dz));cutter.rotation_euler.z=rot
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        # Both cutter and panel evaluated in the same parent-local space.
        cutter.parent=obs[1050];bpy.context.view_layer.update()
        activate(panel);mod=panel.modifiers.new('Actual plug aperture','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    export(panel)
    box('Socket shadow well '+str(slot),(0,.0246,z),(.063,.0008,.045),dark,1050,.0001)

# Seat the charger on the last socket, with the plug blades entering its pair.
charger=obs[1064];charger.location.y=-.178;charger.location.x=.205
bpy.context.view_layer.update();data['nodes'][1064]['matrix']=flat(C.inverted()@charger.matrix_local@C);changed.add(1064)
for x in [-.010,.010]:box('USB charger inserted blade',(x,-.003,-.000),(.002,.008,.007),silver,1064,.0003)

def cable(nid,name,points,radius,mid,parent=878):
    cr=bpy.data.curves.new(name,'CURVE');cr.dimensions='3D';cr.resolution_u=14;cr.bevel_depth=radius;cr.bevel_resolution=3;cr.use_fill_caps=True
    sp=cr.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=bp(co);p.handle_left_type=p.handle_right_type='AUTO'
    temp=bpy.data.objects.new(name,cr);bpy.context.scene.collection.objects.link(temp);activate(temp);bpy.ops.object.convert(target='MESH')
    me=temp.data.copy();bpy.data.objects.remove(temp,do_unlink=True)
    uv=me.uv_layers.new(name='UVMap')
    for l in me.loops:uv.data[l.index].uv=(me.vertices[l.vertex_index].co.x,me.vertices[l.vertex_index].co.z)
    ob=attach(me,name,mid,parent,nid);export(ob);return ob

# Both visible ends enter an actual connector. Behind-desk continuation is
# concealed and is not presented as a measured wall-socket location.
cable(1067,'USB cable connected at both ends',[(.186,.855,.178),(.174,.853,.178),(.148,.824,.146),(.119,.816,.02),(.105,.816,-.13),(.012,.816,-.252),(-.022,.813,-.28),(-.030,.813,-.28)],.0019,91)
box('USB adapter cable plug',(.186,.855,.178),(.014,.008,.010),91,878,.001)
box('Laptop USB cable plug',(-.022,.813,-.28),(.015,.006,.012),91,878,.001)
cable(1068,'Continuous extension mains lead',[(.205,.814,.219),(.225,.808,.245),(.276,.805,.260),(.326,.799,.245),(.335,.72,.20),(.335,.67,-.05),(.335,.72,-.27),(.335,.85,-.31),(.335,.890,-.31)],.0031,91)
box('Extension lead strain relief',(.205,.814,.228),(.011,.010,.024),91,878,.002)

box('Extension wall plug',(.335,.910,-.31),(.026,.040,.034),91,878,.004)
box('Wall plug strain relief',(.335,.889,-.31),(.009,.014,.009),91,878,.002)
result=save('laptop40',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'desktop40':'Dell opening lid, real five-hole faces and connected cables; photo estimated'})
