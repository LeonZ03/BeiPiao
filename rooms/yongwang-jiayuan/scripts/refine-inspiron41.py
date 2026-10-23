"""laptop40 -> inspiron41. Execute only through official Blender Lab MCP.

Dell Inspiron 14 5430 upfiring-speaker silver chassis is a candidate based on
2023 purchase and the closed silver laptop in the room photo, NOT confirmed SKU.
Official envelope/display/touchpad dimensions; small details photo-estimated.
Only laptop descendants and the connector needed for its smaller case change.
"""
from pathlib import Path
import bpy,bmesh,math,json,copy
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text(encoding='utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='laptop40'
bpy.context.preferences.filepaths.save_version=0

def meta(nid,extra):
    d={**data['nodes'][nid].get('userData',{}),**extra}
    obs[nid]['web_user_data']=json.dumps(d);data['nodes'][nid]['userData']=d;changed.add(nid)

# Keep the stable roots and motion interface. Old meshes remain recoverable in
# history but do not contribute geometry, picking, or shadows to this revision.
for o in list(obs[1132].children_recursive):
    if int(o['web_node_id'])==1220:continue
    nid=int(o['web_node_id']);o.hide_render=True;o.hide_set(True)
    data['nodes'][nid]['visible']=False;changed.add(nid)
meta(1132,{'laptopRoot':True,'defaultOpen':True,'modelCandidate':'Dell Inspiron 14 5430','modelConfirmed':False})
meta(1220,{'laptopLid':True,'defaultOpen':True,'openAngle':-.21,'closedAngle':math.pi/2})
lid=obs[1220];lid.location=bp((0,.00895,-.1085));lid.rotation_euler.x=-.21
bpy.context.view_layer.update();data['nodes'][1220]['matrix']=flat(C.inverted()@lid.matrix_local@C)

silver=material('Inspiron41 bead-blasted silver',118,[.76,.77,.785],.39,{},metalness=.32)
edge=material('Inspiron41 cut aluminium rim',118,[.70,.72,.735],.29,{},metalness=.68)
underside=material('Inspiron41 satin silver underside',118,[.49,.51,.535],.48,{},metalness=.32)
keymat=material('Inspiron41 graphite silver keycaps',91,[.50,.515,.53],.52,{},metalness=.05)
black=material('Inspiron41 recessed graphite',91,[.035,.039,.045],.77,{},metalness=0)
rubber=material('Inspiron41 soft bezel gasket',91,[.026,.029,.034],.92,{},metalness=0)
screen=material('Inspiron41 unlit display glass',91,[.055,.067,.079],.23,{},metalness=.08)
legend=material('Inspiron41 key legends',91,[.80,.815,.82],.65,{},metalness=0)
logo=material('Inspiron41 Dell inset graphite mark',91,[.15,.17,.19],.48,{},metalness=.35)

# Build in laptop-local web coordinates, combine by material and motion parent.
# Broad top faces remain planar, corner sidewalls use real radii and smooth normals.
buckets={}
def put(verts,faces,mid,parent=1132,smooth=None):
    key=(parent,mid);v,f,s=buckets.setdefault(key,([],[],[]));off=len(v)
    v.extend(verts);f.extend(tuple(off+i for i in face) for face in faces)
    s.extend(smooth if smooth is not None else [False]*len(faces))

def outline(w,d,r,n=10):
    return [(cx+r*math.cos(a),cz+r*math.sin(a))
        for cx,cz,a0 in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,90),(-w/2+r,-d/2+r,180),(w/2-r,-d/2+r,270)]
        for a in [math.radians(a0+k*90/n) for k in range(n+1)]]

def slab(center,w,d,r,profile,mid,parent=1132,vertical=False):
    # profile = (height, perimeter inset); optional vertical lid mapping.
    vs=[];fs=[];sm=[];N=len(outline(w,d,r))
    for h,inset in profile:
        for x,z in outline(w-2*inset,d-2*inset,max(.0002,r-inset)):
            vs.append((center[0]+x,center[1]+(z if vertical else h),center[2]+(-h if vertical else z)))
    fs.append(tuple(reversed(range(N))));sm.append(False)
    for j in range(len(profile)-1):
        for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i));sm.append(True)
    fs.append(tuple((len(profile)-1)*N+i for i in range(N)));sm.append(False)
    # outline winds around XZ; positive height is Y => reverse faces for outward.
    fs=[tuple(reversed(f)) for f in fs]
    if vertical:fs=[tuple(reversed(f)) for f in fs]  # mapping determinant -1
    put(vs,fs,mid,parent,sm)

def rod(a,b,r,mid,parent=1132,n=16):
    a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0)))
    if u.length<.1:u=axis.cross(Vector((1,0,0)))
    u.normalize();v=axis.cross(u);vs=[]
    for p in [a,b]:
        vs.extend(tuple(p+r*(u*math.cos(k*math.tau/n)+v*math.sin(k*math.tau/n))) for k in range(n))
    fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    put(vs,fs,mid,parent,[False,False]+[True]*n)

# Tapered lower tray and thin upper deck (official 314 x 226.6 mm envelope).
slab((0,0,0),.314,.2266,.006,[(-.0055,.0042),(-.0047,.002),(-.002,.0006),(.0035,0)],underside)
slab((0,0,0),.314,.2266,.006,[(.0035,0),(.0039,0),(.0053,.00065)],silver)
slab((0,.00531,-.033),.291,.103,.003,[(0,0),(.00010,.0002)],black)

# Six rows follow the photographed 5430 US layout, including variable widths,
# compact function row, isolated fingerprint power key, and half-height arrows.
rows=[
 [('esc',1),('F1',1),('F2',1),('F3',1),('F4',1),('F5',1),('F6',1),('F7',1),('F8',1),('F9',1),('F10',1),('home',1),('end',1),('insert',1),('delete',1),('',1)],
 [('~',1),('1',1),('2',1),('3',1),('4',1),('5',1),('6',1),('7',1),('8',1),('9',1),('0',1),('-',1),('=',1),('backspace',2)],
 [('tab',1.5),('Q',1),('W',1),('E',1),('R',1),('T',1),('Y',1),('U',1),('I',1),('O',1),('P',1),('[',1),(']',1),('\\',1.5)],
 [('caps lock',1.9),('A',1),('S',1),('D',1),('F',1),('G',1),('H',1),('J',1),('K',1),('L',1),(';',1),("'",1),('enter',2.1)],
 [('shift',2.5),('Z',1),('X',1),('C',1),('V',1),('B',1),('N',1),('M',1),(',',1),('.',1),('/',1),('shift',2.5)],
 [('ctrl',1.5),('fn',1),('win',1),('alt',1),('',5),('alt',1),('ctrl',1),('<',1.2),('arrows',1.1),('>',1.2)] ]

def textlabel(txt,x,z,size,parent=1132,y=.00604,cover=False,tilt=0):
    if not txt:return
    cu=bpy.data.curves.new('engraving','FONT');cu.body=txt;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.resolution_u=3
    ob=bpy.data.objects.new('temporary engraving',cu);bpy.context.scene.collection.objects.link(ob)
    me=bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    vs=[]
    for v in me.vertices:
        px=v.co.x*math.cos(tilt)-v.co.y*math.sin(tilt);py=v.co.x*math.sin(tilt)+v.co.y*math.cos(tilt)
        if cover:vs.append((x-px,z+py,y))
        else:vs.append((x+px,y,z-py))
    fs=[tuple(p.vertices) for p in me.polygons]
    put(vs,fs,logo if cover else legend,parent)
    bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(me);bpy.data.curves.remove(cu)

for row,keys in enumerate(rows):
    z=[-.076,-.060,-.042,-.024,-.006,.012][row];total=sum(w for _,w in keys);unit=.279/total;x=-.1395
    for txt,units in keys:
        w=units*unit-.0015;cx=x+units*unit/2;x+=units*unit
        dz=.011 if row==0 else .0157
        if txt=='arrows':
            for t,zz in [('^',z-.0041),('v',z+.0041)]:
                slab((cx,0,zz),w,.0074,.0015,[(.00543,0),(.0060,.0003)],keymat)
                textlabel(t,cx,zz,.0021)
        else:
            slab((cx,0,z),w,dz,.0017,[(.00543,0),(.00593,.0002),(.0060,.0004)],keymat)
            textlabel(txt,cx,z,.00205 if len(txt)>1 else .00305)
        if txt in ['F','J']:slab((cx,.00603,z+.0052),.0033,.00045,.00022,[(0,0),(.00009,0)],legend)

# Touchpad known 115 x 80 mm, centered below keyboard; inset perimeter hairline.
slab((0,0,.065),.1162,.0812,.0017,[(.00531,0),(.00543,0)],underside)
slab((0,0,.065),.115,.080,.0015,[(.00542,0),(.00551,.0001)],silver)

# Speaker perforations are small recessed dark apertures, batched as one mesh.
# Not broad black strips. The photographed grille is about 6 mm wide.
for side in [-1,1]:
    for row in range(63):
        for col in range(4):
            x=side*(.1450+col*.00105);z=-.081+row*.00156
            n=6;r=.00028
            put([(x+r*math.cos(k*math.tau/n),.00542,z+r*math.sin(k*math.tau/n)) for k in range(n)], [tuple(reversed(range(n)))],black)

# Lid outer cover and separate black polymer bezel. Actual LCD active area is
# 301.59 x 188.50 mm; the lower chin and camera bar are visibly asymmetric.
slab((0,.10915,0),.314,.2183,.0045,[(-.0022,.0006),(-.0017,0),(.0016,0),(.0022,.0006)],silver,1220,True)
slab((0,.10915,.00225),.312,.2163,.0037,[(-.00012,0),(.00012,.0001)],rubber,1220,True)
slab((0,.1150,.00252),.30159,.18850,.0012,[(-.00008,0),(.00008,0)],screen,1220,True)
# Camera, IR-size status holes, and physical privacy-slider detail at top centre.
rod((0,.2116,.00253),(0,.2116,.00285),.00115,black,1220,24)
rod((0,.2116,.00286),(0,.2116,.0029),.00058,screen,1220,20)
for x in [-.006,.006]:rod((x,.2116,.00255),(x,.2116,.0027),.0003,black,1220,8)
slab((0,.2165,.0026),.014,.001,.00035,[(-.0001,0),(.0001,0)],black,1220,True)
slab((.003,.2165,.00285),.0045,.0008,.0003,[(-.0001,0),(.0001,0)],keymat,1220,True)

# Circular recessed DELL cover emblem, authentic tilted E, viewed from exterior.
for i,ch in enumerate('DELL'):textlabel(ch,(i-1.5)*.0054,.113,.0082,1220,y=-.00228,cover=True,tilt=-.42 if ch=='E' else 0)
N=96;v=[]
for k in range(N):
    a=k*math.tau/N
    for r in [.0171,.01765]:v.append((r*math.cos(a),.113+r*math.sin(a),-.00228))
put(v,[(2*k,2*((k+1)%N),2*((k+1)%N)+1,2*k+1) for k in range(N)],logo,1220)

# Two discrete hinges, dark exhaust slit between them, underside rubber feet.
for x in [-.113,.113]:
    rod((x-.017,.0061,-.1065),(x+.017,.0061,-.1065),.0035,underside)
    slab((x,0,-.101),.035,.018,.002,[(.0033,0),(.0056,0)],silver)
slab((0,0,-.109),.176,.0027,.0007,[(.0023,0),(.0040,0)],black)
for z in [-.088,.086]:slab((0,0,z),.267,.006,.003,[(-.0065,.0003),(-.0055,0)],rubber)

# Port outlines and inset wells. Boolean apertures are cut into the silver
# sidewall below after material buckets are instantiated; faces are not painted
# flat on the chassis. Positions read from Dell's left/right product photos.
ports=[(-1,-.088,.0048,.0048,'dc'),(-1,-.061,.015,.005,'hdmi'),(-1,-.037,.0135,.0055,'usb'),(-1,-.018,.0082,.0031,'typec'),
       (1,-.089,.0035,.0035,'audio'),(1,-.065,.0135,.0055,'usb'),(1,-.031,.030,.0023,'sd')]
port_cutters=[]
for side,z,w,h,typ in ports:
    # Hole axis X. Outer opening extends through casing, well is recessed 0.8mm.
    bpy.ops.mesh.primitive_cube_add(size=1,location=bp((side*.156,0,z)))
    ob=bpy.context.object;ob.name='Temporary port cutter';ob.dimensions=(.007,w,h)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=ob.modifiers.new('Port corner radius','BEVEL');bevel.width=min(h*.20,.0007);bevel.segments=3
    bpy.ops.object.modifier_apply(modifier=bevel.name);port_cutters.append(ob)
    # Inner opening faces with rounded perimeter.
    points=outline(w,h,min(h*.35,.0011),6)
    vs=[(side*.1544,yy,z+xx) for xx,yy in points]
    fs=[tuple(range(len(vs)))]
    if side<0:fs=[tuple(reversed(fs[0]))]
    put(vs,fs,black)
    if typ=='usb':
        # A USB-A tongue with four subdued gold contacts, recessed in its well.
        put([(side*.1547,-.0002,z+q) for q in [-.0055,.0055]]+[(side*.1547,.0008,z+q) for q in [.0055,-.0055]],[(0,1,2,3)],keymat)

# Final combined objects: only 15 material/motion groups, independent of detail
# count. Recalculate normals once, then preserve smooth curved edges.
created=[]
for (parent,mid),(vs,fs,sm) in buckets.items():
    me=mesh('Inspiron41',vs,fs)
    for p,s in zip(me.polygons,sm):p.use_smooth=s
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=attach(me,'Inspiron41 '+('lid ' if parent==1220 else 'base ')+mats[mid].name,mid,parent)
    nid=int(ob['web_node_id']);data['nodes'][nid]['visible']=True;ob.hide_render=False
    if parent==1132 and mid in [silver,underside]:
        # Temporarily detach to evaluate local-space booleans correctly.
        keep=ob.parent;ob.parent=None;ob.matrix_world=Matrix.Identity(4)
        for cutter in port_cutters:
            activate(ob);md=ob.modifiers.new('Functional side aperture','BOOLEAN');md.operation='DIFFERENCE';md.solver='EXACT';md.object=cutter
            bpy.ops.object.modifier_apply(modifier=md.name)
        ob.parent=keep;ob.matrix_local=Matrix.Identity(4)
    ob.data.materials.clear();ob.data.materials.append(mats[mid]);ob.material_slots[0].link='DATA'
    for face in ob.data.polygons:face.material_index=0
    export(ob);created.append(nid)
for ob in port_cutters:bpy.data.objects.remove(ob,do_unlink=True)

# Old USB connector was placed for a 350mm case. Reconnect it to this case's
# right USB-A opening without moving the adapter or changing room furniture.
oldplug=next(o for o in obs.values() if o.get('purpose')=='Laptop USB cable plug')
pid=int(oldplug['web_node_id']);oldplug.hide_render=True;data['nodes'][pid]['visible']=False;changed.add(pid)
bpy.context.view_layer.update()
end=obs[878].matrix_world.inverted()@obs[1132].matrix_world@Vector(bp((.160,0,-.065)))
endweb=(end.x,end.z,-end.y)
curve=bpy.data.curves.new('USB connected to Inspiron41','CURVE');curve.dimensions='3D';curve.resolution_u=12;curve.bevel_depth=.0019;curve.bevel_resolution=2;curve.use_fill_caps=True
pts=[(.186,.855,.178),(.174,.853,.178),(.148,.824,.146),(.119,.816,.02),(.105,.816,-.13),(.012,.816,-.245),(endweb[0]-.020,endweb[1],endweb[2]),endweb]
sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
for p,co in zip(sp.bezier_points,pts):p.co=bp(co);p.handle_left_type=p.handle_right_type='AUTO'
ob=bpy.data.objects.new('temporary cable',curve);collection.objects.link(ob);activate(ob);bpy.ops.object.convert(target='MESH');me=ob.data.copy();bpy.data.objects.remove(ob,do_unlink=True)
uv=me.uv_layers.new(name='UVMap')
ob=attach(me,'USB cable connected to Inspiron41',91,878,1067);export(ob)
plug=box('Inspiron41 USB connector',(.162,0,-.065),(.012,.0048,.0115),black,1132,.0006)
data['nodes'][int(plug['web_node_id'])]['visible']=True

result=save('inspiron41',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'laptop41':{'candidate':'Inspiron 14 5430 silver upfiring speakers','confirmedModel':False,'dimensions_m':[.314,.2266,.01767],'displayActive_m':[.30159,.18850],'touchpad_m':[.115,.080],'newGroupedMeshes':len(created),'parent':'laptop40','unrelatedNodesUnchanged':len(before['nodes'])-len(changed)}})
