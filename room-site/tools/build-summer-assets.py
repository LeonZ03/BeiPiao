"""Blender-authored close-view bedding, summer tree, and indirect-light maps.
All exported coordinates use the existing room's Y-up metre convention.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise_vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist'/'assets'/'summer'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT.parent/'generated-assets'/'summer'
SOURCE.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

def bp(p): return (p[0],-p[2],p[1])
def yp(p): return (p[0],p[2],-p[1])
def material(name,color,rough=.8):
 m=bpy.data.materials.new(name);m.use_nodes=True
 n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough
 return m
linen=material('Cotton ivory',(.79,.75,.67))
bark=material('Summer poplar bark',(.23,.19,.135),1)
leafmat=material('Summer living leaves',(.20,.36,.065),.8)

def grid(name,nx,ny,surface,mat,up=False):
 verts=[bp(surface(i/nx*2-1,j/ny*2-1)) for j in range(ny+1) for i in range(nx+1)]
 faces=[]
 for j in range(ny):
  for i in range(nx):
   k=j*(nx+1)+i;face=(k,k+1,k+nx+2,k+nx+1);faces.append(tuple(reversed(face)) if up else face)
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(mat)
 uv=me.uv_layers.new(name='UVMap')
 for poly in me.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:
   vi=me.loops[li].vertex_index;uv.data[li].uv=(vi%(nx+1)/nx,vi//(nx+1)/ny)
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 return ob

def duvet(u,v):
 envelope=max(0,(1-u*u)*(1-v*v))**.32
 fold=(.012*math.sin(4.1*u+2.6*v+.4)+.006*math.sin(8.3*v-2.2*u)+
       .025*math.exp(-((u+.38*v-.17)/.22)**2)+
       .016*math.exp(-((u-.56*v+.45)/.28)**2))
 wrinkle=.0015*math.sin(21*u+12*v)*math.sin(15*v-7*u)
 return (u*.653*(1-.02*abs(v)**10),.563+envelope*(.045+fold+wrinkle),v*.742-.215+.01*math.sin(u*5)*abs(v)**8)

duvet_top=grid('duvet-top',52,68,duvet,linen,up=True)
sub=duvet_top.modifiers.new('Tailored cloth smoothing','SUBSURF');sub.levels=1;sub.render_levels=1
duvet_bottom=grid('duvet-underside',32,40,lambda u,v:(duvet(u,v)[0],.555,duvet(u,v)[2]),linen)
def pillow(u,v,sign):
 e=max(0,(1-u*u)*(1-v*v))**.39
 wrinkles=.0025*math.sin(u*29+v*17)*(abs(u)**7+abs(v)**7)
 return (u*.328*math.sqrt(1-.14*v*v),sign*(.004+.058*e+wrinkles),v*.205*math.sqrt(1-.14*u*u))
pillows=[grid('pillow-'+side,36,26,lambda u,v,s=sign:pillow(u,v,s),linen,up=sign>0) for side,sign in [('top',1),('bottom',-1)]]
for ob in pillows:
 sub=ob.modifiers.new('Soft cotton envelope','SUBSURF');sub.levels=1

def mesh_export(ob):
 dg=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
 pos=[];normal=[];uv=[];idx=[]
 # Loop vertices preserve UV seams and smooth split normals.
 for tri in me.loop_triangles:
  for li in tri.loops:
   v=me.vertices[me.loops[li].vertex_index]
   pos.extend(round(x,6) for x in yp(v.co));normal.extend(round(x,5) for x in yp(me.corner_normals[li].vector))
   uv.extend(round(x,6) for x in (me.uv_layers.active.data[li].uv if me.uv_layers.active else (0,0)))
   idx.append(len(idx))
 ev.to_mesh_clear();return dict(position=pos,normal=normal,uv=uv)

assets={'meshes':{o.name:mesh_export(o) for o in [duvet_top,duvet_bottom,*pillows]},'metadata':{'authoring':'Blender '+bpy.app.version_string,'units':'metres','season':'summer','light':'soft warm midafternoon'}}
def upholstered(name,nx,ny,surface):
 # A watertight pair of sculpted fabric faces joined along the perimeter.
 verts=[];faces=[];uvs=[]
 for sign in (1,-1):
  for j in range(ny+1):
   for i in range(nx+1):
    verts.append(bp(surface(i/nx*2-1,j/ny*2-1,sign)));uvs.append((i/nx,j/ny))
 offset=(nx+1)*(ny+1)
 for j in range(ny):
  for i in range(nx):
   k=j*(nx+1)+i;faces.extend([(k,k+1,k+nx+2,k+nx+1),(k+offset,k+nx+1+offset,k+nx+2+offset,k+1+offset)])
 edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
 for i,k in enumerate(edge):n=edge[(i+1)%len(edge)];faces.append((k,k+offset,n+offset,n))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[tuple(reversed(f)) for f in faces]);me.materials.append(linen);uv=me.uv_layers.new()
 for poly in me.polygons:
  poly.use_smooth=True
  for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
 ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
 mod=ob.modifiers.new('Upholstery edge smoothing','SUBSURF');mod.levels=1
 return ob
def seat(u,v,side):
 e=max(0,(1-u*u)*(1-v*v))**.36
 return (u*.226*math.sqrt(1-.14*v*v),side*(.019+.030*e)-.007*e*math.exp(-u*u*3),v*.22*math.sqrt(1-.12*u*u))
def back(u,v,side):
 e=max(0,(1-u*u)*(1-v*v))**.4
 return (side*(.012+.028*e)-.008*v*v,v*.235*math.sqrt(1-.13*u*u),u*.226*math.sqrt(1-.13*v*v)*(1-.025*v))
chair_meshes=[upholstered('chair-seat',32,28,seat),upholstered('chair-back',32,28,back)]
for ob in chair_meshes:assets['meshes'][ob.name]=mesh_export(ob);ob.hide_render=True
# Hide the locally positioned bedding while lighting the room proxy.
for ob in [duvet_top,duvet_bottom,*pillows]:ob.hide_render=True

# A tapered, bending poplar tree. Leaf clusters are exported as GPU instances,
# not thousands of independently rendered objects in the web scene.
rng=random.Random(290616)
branches=[];leaf_poses=[]
def branch(points,radii): branches.append((points,radii))
trunk=[(0,0,0),(.11,2.6,.04),(.20,5.2,-.04),(.12,8.1,.10),(.32,11.1,.16),(.22,14.3,.20)]
branch(trunk,[.19,.17,.13,.09,.045,.007])
for j in range(19):
 a=j*2.399+.45;basey=5.1+j*.40;base=(.12,basey,.05)
 reach=(2.3+1.0*math.sin(j/19*math.pi))*(.80+rng.random()*.25)
 end=(math.cos(a)*reach,basey+2.6+rng.random()*.6,math.sin(a)*reach*.72)
 mid=(end[0]*.52,basey+.85,end[2]*.49)
 branch([base,mid,end],[.068*(1-j*.027),.028,.005])
 for t in range(7):
  f=.35+t*.085;origin=tuple(base[k]+(end[k]-base[k])*f for k in range(3));aa=a+(1 if t%2 else -1)*(.65+rng.random()*.4)
  tip=(origin[0]+math.cos(aa)*(.68+rng.random()*.46),origin[1]+.5+rng.random()*.42,origin[2]+math.sin(aa)*.64)
  branch([origin,((origin[0]+tip[0])*.5,origin[1]+.22,(origin[2]+tip[2])*.5),tip],[.015,.008,.0015])
  for n in range(28):
   # Discrete leaves fill a porous ellipsoid, never a solid green sphere.
   theta=rng.uniform(0,2*math.pi);rr=rng.random()**.333;yy=rng.uniform(-1,1)
   radial=math.sqrt(1-yy*yy)
   p=(tip[0]+math.cos(theta)*radial*rr*.75,tip[1]+yy*rr*.67,tip[2]+math.sin(theta)*radial*rr*.63)
   leaf_poses.append([*[round(v,5) for v in p],round(rng.uniform(0,2*math.pi),5),round(rng.uniform(-1.15,1.15),5),round(rng.uniform(.75,1.35),4),round(rng.random(),4)])

cur=bpy.data.curves.new('Tapered organic branches','CURVE');cur.dimensions='3D';cur.resolution_u=5;cur.bevel_depth=1;cur.bevel_resolution=1;cur.resolution_u=5
for points,radii in branches:
 sp=cur.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for b,p,r in zip(sp.bezier_points,points,radii):b.co=bp(p);b.radius=r;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
tree=bpy.data.objects.new('Blender summer poplar branches',cur);bpy.context.collection.objects.link(tree);cur.materials.append(bark)
assets['meshes']['summer-branches']=mesh_export(tree)
# Leaf blade is folded slightly along a centre vein, a closed silhouette without alpha texture.
leaf=grid('summer-leaf',4,6,lambda u,v:(u*.063*math.sin((v+1)*math.pi/2)**.72,.008*(1-abs(u))+.014*v*v,v*.128),leafmat,up=True)
assets['meshes']['summer-leaf']=mesh_export(leaf);assets['leaves']=leaf_poses
tree.hide_render=True;leaf.hide_render=True
leaf_collection=bpy.data.collections.new('Summer leaf instances');bpy.context.scene.collection.children.link(leaf_collection)
for i,p in enumerate(leaf_poses):
 ob=bpy.data.objects.new('Leaf %04d'%i,leaf.data);leaf_collection.objects.link(ob);ob.location=bp(p[:3]);ob.rotation_euler=(p[4],p[3],p[3]*.13);ob.scale=(p[5],)*3;ob.hide_render=True

(OUT/'models.js').write_text('/* Exported from summer-room-source.blend; Y-up metres. */\nexport default '+json.dumps(assets,separators=(',',':'))+';\n',encoding='utf-8')
print('SUMMER_MODELS_EXPORTED',len(leaf_poses),'leaves',flush=True)

# Closed proxy of the real room for indirect diffuse baking. Only indirect light
# is exported, so window/curtain direct shadows remain controllable in Three.js.
scene=bpy.context.scene
pink=material('Pink wall',(.72,.53,.49));grey=material('Blue grey wall',(.49,.57,.61));white=material('White paint',(.83,.81,.76));floor=material('Warm ceramic',(.66,.62,.53),.28);wood=material('Honey wood',(.40,.26,.13));bedmat=material('Cotton bedding',(.75,.68,.57))
def cube(name,size,p,mat):
 bpy.ops.mesh.primitive_cube_add(size=1,location=bp(p));ob=bpy.context.object;ob.name=name;ob.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(mat);return ob
cube('Floor',(2.98,.14,5.16),(0,-.07,.69),floor)
cube('Left wall',(.14,2.65,4.98),(-1.47,1.325,.69),grey)
cube('Right wall',(.14,2.65,4.98),(1.47,1.325,.69),pink)
cube('Rear wall',(2.8,2.65,.14),(0,1.325,3.25),pink)
cube('Ceiling',(2.8,.12,4.98),(0,2.71,.69),white)
for name,size,p in [('Window left',(.65,2.65,.40),(-1.075,1.325,-2)),('Window right',(.38,2.65,.40),(1.21,1.325,-2)),('Window lower',(1.77,.64,.4),(.135,.32,-2)),('Window upper',(1.77,.35,.4),(.135,2.475,-2))]:cube(name,size,p,pink)
cube('Bath partition',(1.72,2.65,.10),(-.54,1.325,1.83),white)
cube('Wardrobe',(.57,2.10,1.17),(-1.1,1.05,-1.135),white)
cube('Wardrobe wood end',(.57,2.10,.02),(-1.1,1.05,-.54),wood)
cube('Bed', (1.45,.28,2.02),(-.60,.38,.64),bedmat)
cube('Bed head',(1.51,.69,.065),(-.60,.65,1.70),wood)
cube('Desk',(.60,.07,1.02),(1.035,.765,-.76),white)
cube('Chair seat',(.45,.085,.43),(.48,.455,-.99),bedmat)
cube('Chair back',(.075,.45,.44),(.274,.685,-.99),bedmat)

world=bpy.data.worlds.new('Summer sky');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.80,.85,.89,1);world.node_tree.nodes['Background'].inputs[1].default_value=.55
def area(name,p,target,power,size,color):
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;data.color=color
 ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=bp(p);ob.rotation_euler=(Vector(bp(target))-ob.location).to_track_quat('-Z','Y').to_euler()
area('Open window diffuse',(.1,1.65,-1.87),(-.25,1,.4),110,1.4,(1,.88,.71))
data=bpy.data.lights.new('Warm summer sun','SUN');data.energy=3.0;data.angle=.065;data.color=(1,.87,.70)
ob=bpy.data.objects.new('Warm summer sun',data);scene.collection.objects.link(ob);ob.location=bp((2.2,5.4,-8));ob.rotation_euler=(Vector(bp((.10,.10,1.0)))-ob.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.max_bounces=7;scene.cycles.diffuse_bounces=5
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception as e:print('GPU_FALLBACK',str(e),flush=True)
scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=True;scene.render.bake.use_pass_color=False;scene.render.bake.margin=3
receivers=[]
def receiver(name,corners,res):
 me=bpy.data.meshes.new('receiver-'+name);me.from_pydata([bp(p) for p in corners],[],[(0,1,2,3)]);me.update();uv=me.uv_layers.new()
 for li,coord in enumerate([(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=coord
 ob=bpy.data.objects.new('Baked indirect '+name,me);scene.collection.objects.link(ob)
 m=material('Bake white '+name,(1,1,1),1);me.materials.append(m)
 image=bpy.data.images.new('indirect-'+name,width=res[0],height=res[1],alpha=False,float_buffer=True);image.colorspace_settings.name='Non-Color'
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;m.node_tree.nodes.active=tex
 receivers.append((name,ob,image))
receiver('floor',[(-1.4,.012,3.18),(1.4,.012,3.18),(1.4,.012,-1.8),(-1.4,.012,-1.8)],(512,768))
receiver('left',[(-1.399,0,1.8),(-1.399,0,-1.8),(-1.399,2.65,-1.8),(-1.399,2.65,1.8)],(512,384))
receiver('right',[(1.399,0,-1.8),(1.399,0,3.18),(1.399,2.65,3.18),(1.399,2.65,-1.8)],(768,384))
receiver('head',[(.32,0,1.778),(-1.4,0,1.778),(-1.4,2.65,1.778),(.32,2.65,1.778)],(384,512))
receiver('ceiling',[(-1.4,2.649,-1.8),(1.4,2.649,-1.8),(1.4,2.649,3.18),(-1.4,2.649,3.18)],(512,768))
for _,r,_ in receivers:r.hide_render=True
for name,ob,image in receivers:
 ob.hide_render=False;bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 print('BAKING_INDIRECT',name,flush=True);bpy.ops.object.bake(type='DIFFUSE')
 raw=SOURCE/'raw-irradiance';raw.mkdir(exist_ok=True)
 image.filepath_raw=str(raw/('indirect-'+name+'.png'));image.file_format='PNG';image.save();ob.hide_render=True
 print('BAKED',name,flush=True)
# Preserve a reusable native source. Preview helpers and bake receivers are named.
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'summer-room-source.blend'))
print('SUMMER_ASSETS_COMPLETE',flush=True)
