"""Photo-guided, solid Blender modelling of the entrance lock and lion/rabbit charm.
All authored coordinates are millimetres; export uses metres, Y-up, front = -Z.
"""
import bpy, math, json, pathlib, bmesh
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/assets/door-details';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT.parent/'generated-assets/door-details';SOURCE.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
materials={};meta={};groups={'charm':[],'lock':[],'thumbturn':[]}
def bp(p):return (p[0]*.001,-p[2]*.001,p[1]*.001)
def mat(name,h,rough=.5,metal=0):
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    rgb=[x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    if bs:
        bs.inputs['Base Color'].default_value=m.diffuse_color;bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    materials[name]=m;meta[name]={'color':'#'+h,'roughness':rough,'metalness':metal}
for a in [('ivory','fff9e8',.61,0),('plate','edf6ed',.35,0),('red','ed271e',.44,0),('red-dark','b61616',.58,0),('gold','dcc475',.25,.68),('yellow','ffcf22',.45,0),('navy','193958',.76,0),('teal','1a9caa',.44,0),('ink','111f27',.32,0),('pink','ffa5a4',.56,0),('silver','bcc4c5',.26,.64),('steel','79888d',.28,.72),('keyhole','17202a',.52,.15)]:mat(*a)
def finish(o,name,m,g='charm',bevel=0):
    o.name=name;o.data.materials.append(materials[m]);groups[g].append(o)
    if bevel:
        mod=o.modifiers.new('Rounded solid edges','BEVEL');mod.width=bevel*.001;mod.segments=3
    if o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o
def cube(name,p,scale,m,bevel=1,g='charm'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=bp(p));o=bpy.context.object;o.scale=(scale[0]*.001,scale[2]*.001,scale[1]*.001);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o=finish(o,name,m,g,bevel)
    mod=o.modifiers.new('Weighted flat-face normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    return o
def sphere(name,p,scale,m,g='charm'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=bp(p));o=bpy.context.object;o.scale=(scale[0]*.001,scale[2]*.001,scale[1]*.001);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,m,g)
def tube(name,pts,r,m,g='charm',cyclic=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=r*.001;c.bevel_resolution=2
    sp=c.splines.new('POLY');sp.points.add(len(pts)-1)
    for q,p in zip(sp.points,pts):q.co=(*bp(p),1)
    sp.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);return finish(o,name,m,g)
def ring(name,x,y,z,r,wire,m,g='charm',tilt=0):
    return tube(name,[(x+r*math.cos(a),y+r*math.sin(a),z+tilt*math.sin(a)) for a in [i/64*math.tau for i in range(64)]],wire,m,g,True)
def solid(name,p,f,m,g='charm',bevel=0):
    me=bpy.data.meshes.new(name);me.from_pydata([bp(v) for v in p],[],f);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,name,m,g,bevel)

# Off-white hook plate with three separate inset-red bars.
cube('rounded-square-hook-plate',(0,0,0),(126,139,5),'plate',7)
for y in [-41,0,41]:cube('red-horizontal-inlay',(0,y,-3.1),(86,17,1.6),'red-dark',.7)
sphere('lower-gold-hook',(0,-73,-6),(5,7,4),'gold')
ring('large-split-keyring',-6,-92,-12,19,1.7,'gold',tilt=4)
ring('second-turn-of-split-ring',-6,-92,-13.5,18.5,1.5,'gold',tilt=4)
ring('small-connector',0,-74,-10,5,1.5,'gold',tilt=3)
ring('pendant-connector',-2,-114,-17,5.5,1.3,'gold',tilt=3)

# Curved, closed red silicone loop. Two offset layers make the open end readable.
def strap(back):
    p=[];f=[];N=40
    for side in [-1,1]:
        for i in range(N+1):
            t=i/N;x=15+50*t;y=-72-172*t;z=-7-10*math.sin(t*math.pi)+back
            for u in [-1,1]:p.append((x+u*13,y,z+side*1.3))
    off=(N+1)*2
    for i in range(N):
        a=i*2;f.extend([(a,a+2,a+3,a+1),(off+a+1,off+a+3,off+a+2,off+a),(a,off+a,off+a+2,a+2),(a+1,a+3,off+a+3,off+a+1)])
    f.extend([(0,1,off+1,off),(2*N,off+2*N,off+2*N+1,2*N+1)])
    solid('silicone-wrist-loop',p,f,'red',bevel=.9)
strap(0);strap(5)
for y,x in [(-77,16),(-236,62)]:
    tube('yellow-strap-chevron',[(x-8,y+3,-14),(x,y-3,-14.7),(x+8,y+3,-14)],1.8,'yellow')

# The body is a red rabbit, held inside a sculpted white lion-dance hood.
sphere('red-lion-hood',(-6,-163,-25),(35,45,13),'red')
sphere('rabbit-body',(-5,-200,-31),(23,25,12),'red')
for x in [-26,16]:sphere('rabbit-sleeve',(x,-194,-30),(8,15,9),'red')
sphere('rabbit-face',(-5,-171,-41),(23,23,12),'red')
for x in [-16,7]:sphere('white-cheek',(x,-183,-50),(13,8,7),'ivory')
sphere('white-muzzle',(-5,-184,-52),(10,6,5),'ivory')
sphere('nose',(-5,-177,-57),(5,3,2),'pink')
tube('rabbit-smile',[(-10,-183,-57),(-6,-186,-57),(-2,-184,-57),(2,-186,-56)],.7,'red-dark')
for x in [-17,7]:
    sphere('rabbit-eye-white',(x,-167,-51),(4.9,7,2.5),'ivory')
    sphere('rabbit-eye-pupil',(x+1,-167,-53),(3.1,5,1.7),'ink')
    sphere('rabbit-eye-shine',(x,-165,-54.7),(1.3,1.8,.7),'ivory')
for x,y in [(-15,-230),(7,-222)]:
    sphere('navy-trouser-leg',(x,y,-34),(9,17,10),'navy')
    sphere('white-shoe',(x+2,y-15,-39),(10,6,11),'ivory')
    tube('shoe-sole-seam',[(x-6,y-17,-43),(x+2,y-19,-48),(x+9,y-16,-44)],.5,'plate')

# Raised lion eyes, white brows and scalloped fleece rim, all closed volumes.
for x in [-26,16]:
    sphere('lion-eye-turquoise',(x,-134,-40),(14,11,8),'teal')
    sphere('lion-eye-red-outline',(x+2,-133,-43),(10,10,6),'red-dark')
    sphere('lion-eye-pupil',(x,-134,-48),(8,9,5),'ink')
    sphere('lion-eye-sparkle',(x-3,-131,-52),(2.5,2.1,1.3),'ivory')
    for j in range(12):
        a=j/11*math.pi; sphere('fleece-eye-brow',(x+14*math.cos(a),-132+12*math.sin(a),-43),(3.8,4,4),'ivory')
    # Triangular ears, padded white piping over the red centre.
    s=-1 if x<0 else 1;tip=(x+s*10,-111,-29)
    tube('white-lion-ear',[(x-9,-125,-30),tip,(x+9,-125,-30)],2.5,'ivory',cyclic=True)
    sphere('red-ear-inner',(x+s*4,-121,-31),(5.5,7,3),'red')
for i in range(13):
    x=-40+i*5.5;y=-149+12*math.sin(i/12*math.pi)
    sphere('lion-upper-muzzle-fleece',(x,y,-47),(4.7,5,5.6),'ivory')
tube('lion-open-mouth',[(x,-153+8*math.sin((x+30)/50*math.pi),-46) for x in range(-31,23,2)],3.1,'navy')
for i in range(12):sphere('lion-small-teeth',(-30+i*4.5,-153+7*math.sin(i/11*math.pi),-48),(2.5,3.1,2.5),'ivory')
for side in [-1,1]:
    for i in range(15):
        t=i/14;x=-6+side*(32-5*t+3*math.sin(t*math.pi));y=-151-64*t
        sphere('long-fleece-hood-edge',(x,y,-37),(3.3+math.sin(i)*.5,4.3,4),'ivory')
    sphere('yellow-lion-ear-knot',(-6+side*40,-154,-31),(4,8,5),'yellow')
    tube('red-lion-ear-ribbon',[(-6+side*42,-154,-30),(-6+side*49,-155,-31),(-6+side*48,-144,-29)],2.5,'red')
tube('curled-fleece-hem',[(-31,-210,-33),(-34,-219,-34),(-24,-227,-36),(-9,-232,-34)],3,'ivory')
sphere('fleece-tail-tip',(-36,-214,-33),(5,5,5),'ivory')
sphere('lion-forehead-boss',(-6,-119,-36),(10,8,7),'yellow')
sphere('lion-forehead-blue',(-6,-118,-42),(6,4,2),'navy')
for x in [-13,0]:sphere('lion-nose-turquoise',(x,-137,-46),(4.5,4,4),'teal')
sphere('yellow-nose',(-6,-138,-50),(5,4,3),'yellow')

# Lever lock: fitted silver backplate, spindle, curved grip, cylinder and screws.
cube('silver-lock-backplate',(0,0,0),(43,180,8),'silver',4,'lock')
cube('raised-backplate-centre',(0,0,-5),(29,158,3),'steel',3,'lock')
for y in [-76,76]:
    sphere('countersunk-screw',(0,y,-6),(3.5,3.5,1),'silver','lock')
    tube('screw-slot',[(-2,y,-7),(2,y,-7)],.45,'keyhole','lock')
tube('lever-spindle',[(0,35,-5),(0,35,-27)],10,'silver','lock')
tube('rounded-lever-grip',[(0,35,-26),(-8,33,-35),(-28,32,-37),(-66,32,-37),(-79,35,-34)],7,'silver','lock')
# Interior privacy lock: round escutcheon and a separate, pivoting solid thumb grip.
sphere('thumbturn-escutcheon',(0,-34,-7),(14,14,3.5),'silver','lock')
ring('thumbturn-base-reveal',0,-34,-10.2,10,.55,'steel','lock')
sphere('turn-spindle',(0,0,0),(7,7,4),'steel','thumbturn')
cube('oval-privacy-thumb-grip',(0,0,-5),(10,25,11),'silver',4.8,'thumbturn')
# Inner-door edge latch and faceplate are separately modelled, at the free edge.
cube('door-edge-faceplate',(110,-2,43),(3,143,25),'silver',1,'lock')
cube('spring-latch-bolt',(113,33,43),(8,20,13),'steel',2,'lock')
for y in [-62,62]:sphere('edge-screw',(112,y,43),(1,3,3),'steel','lock')

# Bake transforms and merge by material to keep mobile draw calls low.
deps=bpy.context.evaluated_depsgraph_get();result={'metadata':{'authoring':'Blender','reference':'user door ornament photo','units':'metres'},'materials':meta,'groups':{}}
for group,objects in groups.items():
    batches={}
    for ob in objects:
        ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();name=ob.data.materials[0].name
        item=batches.setdefault(name,{'material':name,'position':[],'normal':[],'index':[],'parts':[]});item['parts'].append(ob.name);seen={};matrix=ob.matrix_world;nm=matrix.to_3x3().inverted().transposed()
        for tri in me.loop_triangles:
            for li in tri.loops:
                v=matrix@me.vertices[me.loops[li].vertex_index].co;n=(nm@me.corner_normals[li].vector).normalized();p=(round(v.x,6),round(v.z,6),round(-v.y,6));nn=(round(n.x,5),round(n.z,5),round(-n.y,5));key=p+nn
                if key not in seen:seen[key]=len(item['position'])//3;item['position'].extend(p);item['normal'].extend(nn)
                item['index'].append(seen[key])
        ev.to_mesh_clear()
    result['groups'][group]=list(batches.values())
(OUT/'models.js').write_text('export default '+json.dumps(result,separators=(',',':'))+';\n',encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'entrance-lock-lion-charm.blend'))
print('DOOR_DETAILS_EXPORTED', {k:len(v) for k,v in result['groups'].items()},flush=True)
