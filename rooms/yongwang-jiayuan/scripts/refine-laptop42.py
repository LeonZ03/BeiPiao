"""inspiron41 -> laptop42: exterior-readable logo and connected black DC supply.

Run through official Blender Lab MCP. Laptop pose/hinge/shape are unchanged.
Adapter envelope and cable slack are estimates, not confirmed product dimensions.
"""
from pathlib import Path
import bpy, math, copy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text(encoding='utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='inspiron41'

def dell_mesh():
    # Construct the entire word in ONE outside-facing coordinate system.
    # Previously individual glyphs were mirrored, but their centres were not.
    vs=[];fs=[]
    def poly(points):
        start=len(vs);vs.extend((-u,.113+v,-.00229) for u,v in points)
        fs.append(tuple(range(start,start+len(points))))
    def glyph(points,cx,angle=0):
        ca,sa=math.cos(angle),math.sin(angle)
        poly([(cx+x*ca-y*sa,x*sa+y*ca) for x,y in points])
    # Bold D, with a real counter rather than an overlay on the silver cover.
    outer=[(-.0033,-.0044),(-.0033,.0044)]+[(.0044*math.cos(a)-.0011,.0044*math.sin(a)) for a in [math.pi/2-i*math.pi/24 for i in range(25)]]
    inner=[(-.0016,-.0027),(-.0016,.0027)]+[(.0027*math.cos(a)-.0011,.0027*math.sin(a)) for a in [math.pi/2-i*math.pi/24 for i in range(25)]]
    for k in range(len(outer)):
        j=(k+1)%len(outer);glyph([outer[k],outer[j],inner[j],inner[k]],-.0107)
    glyph([(-.00275,-.0039),(.00275,-.0039),(.00275,-.0023),(-.0011,-.0023),(-.0011,-.0008),(.0022,-.0008),(.0022,.0008),(-.0011,.0008),(-.0011,.0023),(.00275,.0023),(.00275,.0039),(-.00275,.0039)],-.0027,math.radians(40))
    for cx in [.005,.011]:
        glyph([(-.00275,-.0044),(.00275,-.0044),(.00275,-.0027),(-.00105,-.0027),(-.00105,.0044),(-.00275,.0044)],cx)
    for k in range(128):
        a=k*math.tau/128;b=(k+1)*math.tau/128
        poly([(r*math.cos(t),r*math.sin(t)) for r,t in [(.0171,a),(.01765,a),(.01765,b),(.0171,b)]])
    me=mesh('DELL outside-facing bold emblem',vs,fs)
    # All logo faces face away from the display, towards the cover observer.
    for p in me.polygons:
        if p.normal.y<0:p.flip()
    me.update();return me

logo=obs[1997];assert 'Dell inset' in logo.name
logo.data=dell_mesh();logo.data.materials.append(mats[data['nodes'][1997]['material']]);logo.material_slots[0].link='DATA';export(logo)

black=material('Laptop42 black moulded power supply',91,[.036,.039,.043],.76,{},metalness=0)
rubber=material('Laptop42 flexible black power cord',91,[.020,.023,.026],.91,{},metalness=0)
def hide(o):
    nid=int(o['web_node_id']);o.hide_render=True;o.hide_set(True);data['nodes'][nid]['visible']=False;changed.add(nid)
for nid in [1065,1066]:hide(obs[nid])
for o in list(obs.values()):
    if o.get('purpose')=='Inspiron41 USB connector':hide(o)

def cuboid(name,center,size,mid,parent=878,r=.002):
    o=box(name,center,size,mid,parent,r);nid=int(o['web_node_id'])
    o.name=name;o['web_name']=name;data['nodes'][nid]['name']=name;data['nodes'][nid]['visible']=True
    o.data.materials.clear();o.data.materials.append(mats[mid]);o.material_slots[0].link='DATA'
    return o

# Preserve the occupied AC socket. The former white USB charger was incorrect.
cuboid('Laptop42 black AC plug',(.205,.839,.178),(.028,.022,.025),black)
cuboid('Laptop42 black adapter lower case',(.195,.806,-.130),(.048,.012,.095),black,r=.003)
cuboid('Laptop42 black adapter upper case',(.195,.819,-.130),(.048,.014,.095),black,r=.003)
# A narrow mould seam; black-on-black, without invented labels or specifications.
cuboid('Laptop42 adapter case seam',(.195,.8123,-.130),(.0482,.0005,.0952),rubber,r=.002)

def cable(name,points,r,mid,nid=None):
    cr=bpy.data.curves.new(name,'CURVE');cr.dimensions='3D';cr.resolution_u=20;cr.bevel_depth=r;cr.bevel_resolution=3;cr.use_fill_caps=True
    sp=cr.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=bp(co);p.handle_left_type=p.handle_right_type='AUTO'
    ob=bpy.data.objects.new('temporary power lead',cr);collection.objects.link(ob);activate(ob);bpy.ops.object.convert(target='MESH')
    me=ob.data.copy();bpy.data.objects.remove(ob,do_unlink=True);me.uv_layers.new(name='UVMap')
    o=attach(me,name,mid,878,nid);o.data.materials.clear();o.data.materials.append(mats[mid]);o.material_slots[0].link='DATA'
    data['nodes'][int(o['web_node_id'])]['visible']=True;export(o);return o

ac=cable('Laptop42 AC input lead',[(.220,.839,.178),(.242,.838,.178),(.262,.815,.150),(.261,.809,.065),(.247,.809,-.030),(.212,.815,-.066),(.195,.820,-.0825)],.0025,rubber)
# Stay behind the hinge, then around the LEFT edge. Never cross the keyboard.
dc=cable('Laptop42 left rear DC lead',[(.195,.820,-.1775),(.189,.817,-.195),(.153,.809,-.245),(.112,.809,-.293),(.076,.809,-.307),(.062,.812,-.294),(.062,.812,-.282)],.0018,rubber,1067)
cuboid('Laptop42 AC input strain relief',(.195,.820,-.079),(.009,.008,.013),rubber,r=.001)
cuboid('Laptop42 DC output strain relief',(.195,.820,-.180),(.006,.006,.012),rubber,r=.001)

# Barrel is coaxial with the existing left rear DC socket, not a USB port.
def barrel(name,a,b,r,mid):
    a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u);n=24
    verts=[tuple(p+r*(u*math.cos(k*math.tau/n)+v*math.sin(k*math.tau/n))) for p in [a,b] for k in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    o=attach(mesh(name,verts,faces,smooth=True),name,mid,1132);data['nodes'][int(o['web_node_id'])]['visible']=True;export(o)
barrel('Laptop42 DC barrel sleeve',(-.176,0,-.088),(-.156,0,-.088),.00235,black)
barrel('Laptop42 DC barrel strain relief',(-.181,0,-.088),(-.171,0,-.088),.0020,rubber)

# Assert the authored output wire clears the full case/hinge sweep envelope.
bpy.context.view_layer.update();xf=obs[1132].matrix_world.inverted()@dc.matrix_world
for v in dc.data.vertices:
    p=xf@v.co;x,y,z=p.x,p.z,-p.y
    assert x<-.158 or z<-.120,('DC cable enters laptop footprint',x,y,z)
result=save('laptop42',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'laptop42':{'parent':'inspiron41','logo':'outside-facing DELL','power':'black AC adapter / left rear DC jack','adapterDimensions':'photo-estimated','unrelatedNodesUnchanged':len(before['nodes'])-len(changed)}})
