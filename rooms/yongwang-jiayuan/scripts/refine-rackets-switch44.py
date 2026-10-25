"""props43a -> props44. Run with official Blender Lab MCP only.

User photographs: Clash first generation (submodel unconfirmed), HEAD Graphene
XT Radical MP. Manufacturer length/string pattern; other contours estimated.
Preserve both approved hanging anchors. New hooks cradle the top cross-string.
"""
from pathlib import Path
import bpy, math, copy
from mathutils import Vector, Matrix
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props43a'

def plain(name,color,rough=.5,metal=0):
    return material(name,0,color,rough,{},metalness=metal,vertexColors=False,transparent=False,opacity=1,side=0)
black=plain('Racket44 charcoal painted composite',[.035,.041,.045],.46)
red=plain('Racket44 Clash fluorescent red',[.92,.105,.045],.48)
grey=plain('Racket44 Clash graphite grey',[.30,.34,.37],.55)
orange=plain('Racket44 Radical orange',[1,.28,.025],.38)
blue=plain('Racket44 Radical cyan details',[.02,.56,.78],.44)
rubber=plain('Racket44 textured bumper and grommets',[.018,.022,.024],.84)
orange_string=plain('Racket44 orange polyester strings',[.96,.29,.035],.56)
dark_string=plain('Racket44 black polyester strings',[.027,.034,.036],.58)
grip_w=plain('Racket44 pale sage overgrip',[.71,.75,.66],.95)
grip_h=plain('Racket44 ivory overgrip',[.84,.84,.76],.94)
grip_seam_w=plain('Racket44 sage wrap edge',[.61,.65,.57],.96)
grip_seam_h=plain('Racket44 ivory wrap edge',[.72,.73,.66],.96)
tape=plain('Racket44 white finishing tape',[.91,.90,.84],.77)
hookmat=plain('Racket44 satin nickel hook',[.57,.58,.56],.34,.77)
switchmat=plain('Switch44 warm white PC',[.87,.86,.81],.48)
switchgap=plain('Switch44 recessed frame reveal',[.24,.24,.22],.8)

# A material bucket joins repeated strings/grommets into a few draw calls.
buckets={}
def put(mid,verts,faces,uv=None):
    v,f,u=buckets.setdefault(mid,([],[],[]));base=len(v);v.extend(verts)
    f.extend([tuple(base+i for i in face) for face in faces]);u.extend(uv or [(0,0)]*len(verts))

def sweep(points,radius,mid,sides=8,flat=None):
    pts=[Vector(p) for p in points];v=[];f=[]
    for i,p in enumerate(pts):
        tangent=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized()
        guide=Vector((0,0,1)) if abs(tangent.z)<.95 else Vector((1,0,0))
        a=tangent.cross(guide).normalized();b=tangent.cross(a).normalized()
        rr=radius[i] if isinstance(radius,list) else radius
        for j in range(sides):
            q=p+a*math.cos(j*math.tau/sides)*rr+b*math.sin(j*math.tau/sides)*(flat if flat else rr)
            v.append(tuple(q))
    for i in range(len(pts)-1):
        for j in range(sides):f.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
    f.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);put(mid,v,f)

def curve(control,steps=28):
    # Cubic Bezier, deterministic and independent of operator selection.
    p=[Vector(v) for v in control]
    return [tuple((1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]) for t in [i/steps for i in range(steps+1)]]

def finish(prefix,parent):
    made=[]
    for mid,(v,f,u) in buckets.items():
        o=attach(mesh(prefix+' '+mats[mid].name,v,f,u,True),prefix+' '+mats[mid].name,mid,parent)
        export(o);made.append(int(o['web_node_id']))
    buckets.clear();return made

def label(text,center,length,mid,parent,angle=0):
    # Visible labels only. No guessed model number, mass or tension markings.
    cr=bpy.data.curves.new('Racket44 printed '+text,'FONT');cr.body=text;cr.align_x='CENTER';cr.align_y='CENTER';cr.size=1;cr.extrude=0;cr.resolution_u=3
    o=bpy.data.objects.new('Racket44 lettering source',cr);collection.objects.link(o)
    bpy.context.view_layer.update();scale=length/max(o.dimensions.x,.001)
    dep=bpy.context.evaluated_depsgraph_get();me=bpy.data.meshes.new_from_object(o.evaluated_get(dep));bpy.data.objects.remove(o,do_unlink=True)
    ca,sa=math.cos(angle),math.sin(angle)
    ymax=max(v.co.y for v in me.vertices)-min(v.co.y for v in me.vertices)
    sy=min(scale,.015/max(ymax,.001))
    for p in me.vertices:
        x,y=p.co.x*scale,p.co.y*sy;p.co=bp((center[0]+ca*x-sa*y,center[1]+sa*x+ca*y,center[2]))
    me.uv_layers.new(name='UVMap');o=attach(me,'Racket44 '+text,mid,parent);export(o);return o

# Reuse the authentic Wilson artwork, tint its white print red on the throat.
oldlogo=data['materials'][data['nodes'][835]['material']]
wilsonlogo=material('Racket44 Wilson red printed wordmark',data['nodes'][835]['material'],[.94,.09,.035],.58,copy.deepcopy(oldlogo['textures']),metalness=0,vertexColors=False,transparent=True,alphaTest=.3,depthWrite=False,polygonOffset=True,polygonOffsetFactor=-1,polygonOffsetUnits=-1)

newnodes=[];contact=[]
for parent,is_wilson in [(824,True),(811,False)]:
    prefix='Clash44' if is_wilson else 'Radical44'
    for o in list(obs[parent].children):
        nid=o.get('web_node_id');assert nid is not None
        o.hide_render=True;o.hide_set(True);data['nodes'][nid]['visible']=False;changed.add(nid)
    oldhook=836 if is_wilson else 823
    obs[oldhook].hide_render=True;obs[oldhook].hide_set(True);data['nodes'][oldhook]['visible']=False;changed.add(oldhook)
    rx=.132 if is_wilson else .129;ry=.176;cy=.497
    # Oval, flattened 24.5 mm / variable 20–23 mm frame beam, not a round tube.
    n=160;ring=[]
    for i in range(n+1):
        a=math.tau*i/n;x=rx*math.sin(a);y=cy+ry*math.cos(a)
        normal=Vector((math.sin(a)/rx,math.cos(a)/ry,0)).normalized()
        depth=.0245 if is_wilson else (.020+.003*math.sin(a)**2)
        row=[]
        for j in range(12):
            t=math.tau*j/12
            # Rounded rectangular section: broad front faces and gentle corners.
            c=math.copysign(abs(math.cos(t))**.65,math.cos(t));s=math.copysign(abs(math.sin(t))**.65,math.sin(t))
            q=Vector((x,y,0))+normal*(.0108*c)+Vector((0,0,depth*.5*s));row.append(tuple(q))
        ring.append(row)
    for i in range(n):
        a=math.tau*(i+.5)/n
        if is_wilson:mid=red if .70<a<2.42 or 3.86<a<5.58 else (grey if a<.70 or a>5.58 else black)
        else:mid=orange if a<2.02 or a>4.26 else black
        put(mid,ring[i]+ring[i+1],[(j,(j+1)%12,12+(j+1)%12,12+j) for j in range(12)])
    # Molded Y throat with a curved bridge, continuous into the lower hoop.
    for side in [-1,1]:
        pts=curve([(side*.008,.165,0),(side*.020,.220,0),(side*.034,.279,0),(side*.091,.369,0)],32)
        sweep(pts,[.008+.0025*i/32 for i in range(33)],black,12,.0115 if is_wilson else .0105)
    sweep(curve([(-.078,.355,0),(-.047,.319,0),(.047,.319,0),(.078,.355,0)]),.0083,black,10,.011)
    # Head guard follows the outer arc with grommet eyelets at every line end.
    sweep([( (rx+.008)*math.sin(a),cy+(ry+.008)*math.cos(a),0) for a in [(-1.5+i*3/100) for i in range(101)]],.0030,rubber,8,.011)
    irx=rx-.0107;iry=ry-.0107;xs=[(i-7.5)*.0144 for i in range(16)];ys=[cy+(i-9)*.01715 for i in range(19)]
    ends=[];sm=orange_string if is_wilson else dark_string
    for ix,x in enumerate(xs):
        h=iry*math.sqrt(1-(x/irx)**2);lo,hi=cy-h,cy+h
        pts=[(x,lo+(hi-lo)*j/100,.00055*math.cos(math.pi*((lo+(hi-lo)*j/100-ys[0])/.01715+ix))) for j in range(101)]
        sweep(pts,.00062,sm,5);ends.extend([pts[0],pts[-1]])
    for iy,y in enumerate(ys):
        w=irx*math.sqrt(1-((y-cy)/iry)**2)
        pts=[(-w+2*w*j/75,y,-.00055*math.cos(math.pi*((-w+2*w*j/75-xs[0])/.0144+iy))) for j in range(76)]
        sweep(pts,.00062,sm,5);ends.extend([pts[0],pts[-1]])
    for x,y,z in ends:
        direction=Vector((x/(irx*irx),(y-cy)/(iry*iry),0)).normalized()
        sweep([(x,y,0),tuple(Vector((x,y,0))+direction*.019)],.00165,rubber,7)
    # Eight-sided handle and a helical overlap edge instead of stacked rings.
    gm,em=(grip_w,grip_seam_w) if is_wilson else (grip_h,grip_seam_h)
    sweep([(0,.008,0),(0,.018,0),(0,.163,0),(0,.177,0)],[.0185,.0170,.0163,.0155],gm,8)
    sweep([(0,.003,0),(0,.010,0)],[.0195,.0188],black,8)
    helix=[]
    for i in range(641):
        t=i/640;a=t*math.tau*10;y=.017+.151*t;r=.0175-.0012*t
        # Octagonal radius retains the grip facets under the wrap.
        r*=math.cos(math.pi/8)/math.cos((a+math.pi/8)%(math.pi/4)-math.pi/8)
        helix.append((r*math.cos(a),y,r*math.sin(a)))
    sweep(helix,.00048,em,5)
    sweep([(0,.172,0),(0,.185,0)],.0163,tape,8)
    # Photo-visible lower-bed dampener/tie; do not add unverifiable hardware.
    if is_wilson:sweep([(-.014,.361,.0015),(0,.358,.0018),(.014,.361,.0015)],.0020,tape,8)
    else:
        sweep(curve([(-.010,.360,.002),(-.029,.333,.003),(.025,.330,.004),(.014,.357,.002)],18),.0014,blue,6)
        sweep([(-.010,.360,.002),(.005,.365,.002),(.022,.350,.002)],.0014,blue,6)
    # Short hook: hidden screw plate on the cabinet, curved tip under first cross.
    top=ys[-1];hook=[(0,top+.010,-.027),(0,top+.010,-.020),(0,top-.004,-.005),(0,top-.0025,.002),(0,top+.007,.008)]
    sweep(hook,.0018,hookmat,10)
    sweep([(0,top+.010,-.027),(0,top+.010,-.024)],.0055,hookmat,12)
    contact.append({'parent':parent,'topCrossY':top,'hookSupportY':top-.0025,'clearance':.00008,'stringRows':[16,19]})
    newnodes.extend(finish(prefix,parent))
    if is_wilson:
        # Long red wordmark on the right throat arm, matching actual print.
        a=math.atan2(.139,.061);center=Vector((.038,.257,.0119));length=.105;h=length/(89.64/21.17)
        ux=Vector((math.cos(a),math.sin(a),0));uy=Vector((-math.sin(a),math.cos(a),0))
        vv=[tuple(center+ux*x+uy*y) for x,y in [(-length/2,-h/2),(length/2,-h/2),(length/2,h/2),(-length/2,h/2)]]
        o=attach(mesh('Clash44 Wilson wordmark',vv,[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)]),'Clash44 Wilson wordmark',wilsonlogo,parent);export(o)
        label('CLASH',(-.123,.47,.0126),.069,tape,parent,math.pi/2)
    else:
        label('HEAD',(.039,.257,.0117),.132,red,parent,math.atan2(.143,.060))
        label('RADICAL MP',(-.075,.371,.0117),.052,orange,parent,-.7)
        label('GRAPHENE XT',(-.122,.507,.0121),.088,tape,parent,math.pi/2)
        label('ALPHA',(0,.179,.0167),.021,grey,parent)

# Replace the base/plinth finish, retaining all cabinet transforms and UV1.
o=obs[781];o.data=o.data.copy();uv=o.data.uv_layers.active
for p in o.data.polygons:
    axis=max(range(3),key=lambda k:abs(p.normal[k]))
    for li in p.loop_indices:
        v=o.data.vertices[o.data.loops[li].vertex_index].co
        uv.data[li].uv=(v.x/.56,(v.z+.075)/2.02) if axis==1 else (v.y/1.14,(v.z+.075)/2.02) if axis==0 else (v.x/.56,v.y/1.14)
set_material(781,61);export(o);o.name='wardrobe-woodgrain-bottom-plinth';data['nodes'][781]['name']=o.name

# A conventional flush 86-style plate and broad rocker, only ~8 mm proud.
def switch_box(nid,name,size,center,mid,bevel):
    o=obs[nid];me=bpy.data.meshes.new(name);bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector(bp([size[k]*v.co[k] for k in range(3)]))
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=4,affect='EDGES');bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.uv_layers.new(name='UVMap')
    attach(me,name,mid,1481,nid);o.matrix_local=Matrix.Translation(Vector(bp(center)));data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);export(o)
switch_box(1482,'wall-switch-86-frame',(.006,.086,.086),(1.392,1.120,.860),switchmat,.0014)
switch_box(1483,'light-switch-rocker',(.005,.064,.065),(1.387,1.120,.860),switchmat,.0012)
# Narrow dark reveal is actual recessed geometry, not painted outlines.
o=box('Switch44 reveal',(1.3895,1.120,.860),(.001,.067,.068),switchgap,1481,.0003);o.name='wall-switch-recessed-gap';data['nodes'][o['web_node_id']]['name']=o.name
details={**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'props44':{'parent':'props43a','rackets':contact,'source':'2026-10-26 user photos; manufacturer catalog dimensions','switch':'unbranded ~86 mm rocker','cabinetBottom':781}}
result=save('props44',details)
