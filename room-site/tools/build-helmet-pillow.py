"""Photo-guided adult FF801 silhouette and sewn cotton pillow, Y-up metres.
The visor, face aperture, lower chin and swept rear spoiler are modelled separately.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/assets/close-refinements';OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT.parent/'generated-assets/close-refinements';SOURCE.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
groups={'helmet':[],'pillow':[]}
mats={}
for name,color,metal,rough in [('carbon',(.032,.037,.042),.28,.22),('rubber',(.011,.013,.016),0,.75),('vent',(.035,.043,.045),.38,.3),('visor',(.75,.33,.04),.75,.14),('silver',(.47,.49,.5),.85,.2),('linen',(.8,.77,.71),0,.9),('seam',(.68,.65,.59),0,1)]:
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;mats[name]=m
for name in ['brand-logo','model-logo']:mats[name]=mats['silver'].copy();mats[name].name=name
def bp(p):return(p[0],-p[2],p[1])
def addmesh(name,pts,faces,material='carbon',group='helmet',uvs=None,solid=0,bevel=0,smooth=True):
 me=bpy.data.meshes.new(name);me.from_pydata([bp(p) for p in pts],[],faces);me.materials.append(mats[material]);me.update()
 if uvs:
  uv=me.uv_layers.new()
  for poly in me.polygons:
   for li in poly.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
 else:
  uv=me.uv_layers.new()
  for poly in me.polygons:
   for li in poly.loop_indices:
    p=pts[me.loops[li].vertex_index];uv.data[li].uv=(p[0]*2+0.5,p[1]*2+p[2])
 for p in me.polygons:p.use_smooth=smooth
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);groups[group].append(o)
 if solid:
  mod=o.modifiers.new('Real shell thickness','SOLIDIFY');mod.thickness=solid;mod.offset=-1
 if bevel:
  mod=o.modifiers.new('Soft machined edge','BEVEL');mod.width=bevel;mod.segments=3
 return o
def tube(name,points,r,mat='rubber',group='helmet',closed=False):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=r;curve.bevel_resolution=2
 sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
 for p,v in zip(sp.points,points):p.co=(*bp(v),1)
 sp.use_cyclic_u=closed;o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);o.data.materials.append(mats[mat]);groups[group].append(o);return o
def ellipsoid(name,p,s,mat='rubber'):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=bp(p));o=bpy.context.object;o.name=name;o.scale=(s[0],s[2],s[1]);o.data.materials.append(mats[mat]);groups['helmet'].append(o)
 for f in o.data.polygons:f.use_smooth=True
 return o

# Long front-to-back oval, a tapered chin, and a low swept forehead.
rings=[(.022,.104,-.135,.137),(.048,.127,-.157,.188),(.080,.142,-.171,.207),(.130,.150,-.176,.190),(.163,.152,-.179,.182),(.202,.150,-.176,.168),(.242,.139,-.164,.142),(.271,.121,-.147,.108),(.294,.093,-.121,.070),(.310,.052,-.082,.017),(.316,.001,-.032,-.030)]
def ringpoint(row,a):
 y,rx,back,front=rings[row];f=max(0,math.cos(a));z=(back+front)/2+(front-back)/2*math.cos(a)
 x=rx*math.sin(a)*(1-(.13 if row<3 else .02)*f*f)
 if row==0:y+=.050*max(0,-math.cos(a))+.022*math.sin(a)**2
 if row==1:y+=.018*max(0,-math.cos(a))+.009*math.sin(a)**2
 if row==3:y+=.020*(abs(math.sin(a))**1.6)
 if row==6:y-=.011*(abs(math.sin(a))**1.6)
 return(x,y,z)
# Use a periodic cubic interpolant between the design stations, retaining aperture edges.
def ringinterp(v,a):
 j=min(len(rings)-2,int(v));t=v-j
 p0=ringpoint(max(0,j-1),a);p1=ringpoint(j,a);p2=ringpoint(j+1,a);p3=ringpoint(min(len(rings)-1,j+2),a)
 return tuple(.5*((2*p1[k])+(-p0[k]+p2[k])*t+(2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+(-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t) for k in range(3))
def on_shell(v,a,lift=0):
 p=Vector(ringinterp(v,a));n=Vector((p.x/.15**2,(p.y-.16)/.16**2,p.z/.18**2)).normalized();return tuple(p+n*lift)
def surface_patch(name,surface,material,nx=24,ny=10,thickness=0):
 pts=[];faces=[];uv=[]
 for j in range(ny+1):
  for i in range(nx+1):pts.append(surface(i/nx,j/ny));uv.append((i/nx,j/ny))
 for j in range(ny):
  for i in range(nx):k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
 return addmesh(name,pts,faces,material,uvs=uv,solid=thickness)
N=100;R=60;pts=[];uv=[];faces=[];opening=1.194
for j in range(R+1):
 for i in range(N+1):
  a=-math.pi+math.tau*i/N;pts.append(ringinterp(j/R*10,a));uv.append((i/N,j/R))
for j in range(R):
 for i in range(N):
  a=-math.pi+math.tau*(i+.5)/N;v=(j+.5)/R*10
  if 3<v<6 and abs(a)<opening:continue
  k=j*(N+1)+i;faces.append((k,k+1,k+N+2,k+N+1))
shell=addmesh('FF801-aerodynamic-carbon-shell',pts,faces,uvs=uv,solid=.003)
# Face aperture is a continuous glazed shield. Its edge exactly follows the shell.
def visor(u,v):
 a=u*opening;b=ringpoint(3,a);t=ringpoint(6,a);c=.004*math.sin(v*math.pi)
 return(b[0]*(1-v)+t[0]*v+.003*math.sin(a),b[1]*(1-v)+t[1]*v,b[2]*(1-v)+t[2]*v+.004*math.cos(a)+c)
pts=[];uv=[];faces=[];nx=72;ny=16
for j in range(ny+1):
 for i in range(nx+1):pts.append(visor(i/nx*2-1,j/ny));uv.append((i/nx,j/ny))
for j in range(ny):
 for i in range(nx):k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
addmesh('FF801-rainbow-mirror-shield',pts,faces,'visor',uvs=uv,solid=.002)
for v in [0,1]:tube('visor-rubber-seal',[visor(i/80*2-1,v) for i in range(81)],.0023)
for s in [-1,1]:
 p=visor(s,.55);ellipsoid('flush-visor-pivot',p,(.008,.010,.006),'vent')
 # Thin cheek channels conform to the shell instead of cutting across its curvature.
 surface_patch('fitted-cheek-vent',lambda u,v,s=s:on_shell(1.95+v*.75+u*.55,s*(.50+u*.55),.0013),'vent',thickness=.002)
 # Hollow intake under the rear spoiler, framed by two structural carbon strakes.
 pts=[(s*.098,.271,-.090),(s*.080,.304,-.215),(s*.111,.235,-.101)]
 addmesh('rear-spoiler-side-strake',pts,[(0,1,2)],solid=.007,bevel=.0017,smooth=False)
 pts=[(s*.100,.262,-.106),(s*.087,.292,-.184),(s*.104,.249,-.108)]
 addmesh('rear-exhaust-vent',pts,[(0,1,2)],'rubber',solid=.0015)
# A genuine tapered rear wing, projecting behind the shell (not a torus or crown).
pts=[];uv=[];faces=[];nx=32;ny=6
for j in range(ny+1):
 for i in range(nx+1):
  u=i/nx*2-1;t=j/ny;x=u*(.108-.006*t);y=.287+.018*(1-u*u)+.006*t;z=-.104-.119*t+.015*u*u
  pts.append((x,y,z));uv.append((i/nx,t))
for j in range(ny):
 for i in range(nx):k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
addmesh('swept-racing-rear-spoiler',pts,faces,uvs=uv,solid=.005,bevel=.0013)
for s in [-1,1]:
 surface_patch('fitted-crown-air-scoop',lambda u,v,s=s:on_shell(7.9+v*.93,s*(.42+u*.24),.002+.004*math.sin(math.pi*v)),'carbon',thickness=.004)
 surface_patch('crown-intake-grille',lambda u,v,s=s:on_shell(8.03+v*.55,s*(.46+u*.16),.006),'vent',thickness=.002)
# Sculpted central chin scoop; its perimeter follows the pointed shell front.
surface_patch('fitted-central-chin-intake',lambda u,v:on_shell(1.90+.83*v,(u*2-1)*(.14+.13*v),.0014),'rubber',thickness=.0025)
for row,w in [(2.18,.18),(2.48,.22)]:tube('chin-grille-bar',[on_shell(row,(i/20*2-1)*w,.0027) for i in range(21)],.0011,'vent')
# Open neck roll and visible padding, no sphere filling the opening.
tube('lower-shell-rubber-trim',[ringpoint(0,-math.pi+i/100*math.tau) for i in range(100)],.004,closed=True)
tube('interior-neck-padding',[(.088*math.sin(a),.032+.050*max(0,-math.cos(a))+.022*math.sin(a)**2,-.012+.118*math.cos(a)) for a in [i/100*math.tau for i in range(100)]],.011,closed=True)
for s in [-1,1]:ellipsoid('inner-cheek-pad',(s*.095,.074,.070),(.019,.033,.063))
tube('fastened-chin-strap',[(-.07,.068,-.030),(-.02,.059,.010),(.05,.063,.026)],.006)
surface_patch('curved-brow-LS2-mark',lambda u,v:on_shell(6.62+.52*v,(u*2-1)*.32,.0008),'brand-logo')
for s in [-1,1]:
 surface_patch('curved-FF801-carbon-mark',lambda u,v,s=s:on_shell(1.95+.35*v,1.20+.78*u if s>0 else -1.98+.78*u,.0015),'model-logo',nx=32,ny=12)

# Slightly asymmetric cotton volume, with restrained gathered corners and a seam.
nx=48;ny=32;pts=[];uv=[];faces=[]
def pillow(u,v,sign):
 e=max(0,(1-u*u)*(1-v*v))**.42
 x=u*.328*math.sqrt(1-.10*v*v);z=v*.213*math.sqrt(1-.13*u*u)
 crease=.0030*math.sin(u*30+v*16)*(abs(u)**8+abs(v)**9)*e
 broad=.008*math.sin(2.2*u+1.1*v)*e
 dent=.009*math.exp(-((u-.15)/.5)**2-((v+.05)/.6)**2)
 y=(.006+.084*e+broad-dent+crease) if sign>0 else -(.006+.061*e)
 return(x,y,z)
for sign in [1,-1]:
 for j in range(ny+1):
  for i in range(nx+1):pts.append(pillow(i/nx*2-1,j/ny*2-1,sign));uv.append((i/nx,j/ny))
off=(nx+1)*(ny+1)
for j in range(ny):
 for i in range(nx):
  k=j*(nx+1)+i;faces.extend([(k,k+nx+1,k+nx+2,k+1),(k+off,k+1+off,k+nx+2+off,k+nx+1+off)])
edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
for i,k in enumerate(edge):n=edge[(i+1)%len(edge)];faces.append((k,n,n+off,k+off))
o=addmesh('full-cotton-pillow',pts,faces,'linen','pillow',uvs=uv)
sub=o.modifiers.new('Sewn softened corners','SUBSURF');sub.levels=1
seam=[]
for k in edge:
 p=pts[k];seam.append((p[0],0,p[2]))
tube('pillow-piped-seam',seam,.0015,'seam','pillow',True)

# Export indexed evaluated meshes and UVs; no Blender runtime needed in the browser.
result={'metadata':{'authoring':'Blender '+bpy.app.version_string,'units':'metres','reference':'User FF801 photographs and existing single pillow'},'groups':{}}
deps=bpy.context.evaluated_depsgraph_get()
for group,objects in groups.items():
 entries=[]
 for ob in objects:
  ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();mx=ob.matrix_world;nm=mx.to_3x3().inverted().transposed();d={'name':ob.name,'material':ob.data.materials[0].name,'position':[],'normal':[],'uv':[],'index':[]};seen={}
  for tri in me.loop_triangles:
   for li in tri.loops:
    v=mx@me.vertices[me.loops[li].vertex_index].co;n=(nm@me.corner_normals[li].vector).normalized();p=tuple(round(x,6) for x in (v.x,v.z,-v.y));nn=tuple(round(x,5) for x in (n.x,n.z,-n.y));uv=tuple(round(x,6) for x in (me.uv_layers.active.data[li].uv if me.uv_layers.active else (0,0)));key=p+nn+uv
    if key not in seen:seen[key]=len(d['position'])//3;d['position'].extend(p);d['normal'].extend(nn);d['uv'].extend(uv)
    d['index'].append(seen[key])
  ev.to_mesh_clear();entries.append(d)
 result['groups'][group]=entries
(OUT/'models.js').write_text('export default '+json.dumps(result,separators=(',',':'))+';\n',encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'ff801-carbon-and-cotton-pillow.blend'))
print('REFINEMENTS_EXPORTED', {k:len(v) for k,v in result['groups'].items()},flush=True)
