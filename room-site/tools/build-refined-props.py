"""Native Blender authoring for the GSX250R silhouette, sewn cap and cupped petals.
References: user blue/white bike photos and Suzuki 2021 GSX250R catalogue.
Scene and exported mesh positions use metres. Helpers accept browser X/Y-up/Z.
"""
import bpy, math, json, pathlib, bmesh
from mathutils import Vector
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'dist/assets/refined-props'; OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT.parent/'generated-assets/refined-props'; SOURCE.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
def bp(p): return (p[0],-p[2],p[1])
def rgb(h):
    v=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in v)
materials={}; meta={}; groups={'motorcycle':[],'cap':[],'petal':[]}
def mat(name,color,rough=.45,metal=0,clear=0):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb(color),1);m.use_nodes=True
    bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bs is None:
        bs=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');output=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(bs.outputs[0],output.inputs[0])
    bs.inputs['Base Color'].default_value=m.diffuse_color
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;bs.inputs['Coat Weight'].default_value=clear
    materials[name]=m;meta[name]={'color':'#'+color,'roughness':rough,'metalness':metal,'clearcoat':clear};return m
mat('suzuki-blue','057fe2',.27,.28,.8);mat('dark-blue','075ca8',.30,.2,.65)
mat('rubber','15191b',.88);mat('frame','24282b',.51,.40);mat('seat','252529',.78)
mat('silver','bac3c7',.26,.85);mat('rotor','778286',.44,.75);mat('white','f3f5ef',.42)
mat('rim-tape','d2f219',.45,.1);mat('lamp','cedce0',.18,.35);mat('red','b21625',.3,.18)
mat('amber','db8424',.3,.1);mat('smoke','485762',.2,.2);mat('gold','cab45e',.5,.3)
mat('cap-cloth','242426',.94);mat('cap-seam','37373a',.97);mat('petal-ivory','f4f0e5',.9)
def finish(o,name,material,group='motorcycle',bevel=0,sub=0,smooth=True):
    o.name=name;o.data.materials.clear();o.data.materials.append(materials[material]);groups[group].append(o)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=bevel;mod.segments=3
    if sub:
        mod=o.modifiers.new('Continuous curved skin','SUBSURF');mod.levels=sub;mod.render_levels=sub
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    return o
def mesh(name,p,f,material,group='motorcycle',bevel=0,sub=0):
    me=bpy.data.meshes.new(name);me.from_pydata([bp(v) for v in p],[],f);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);return finish(o,name,material,group,bevel,sub)
def cube(name,p,scale,material,bevel=.005,group='motorcycle'):
    bpy.ops.mesh.primitive_cube_add(size=1,location=bp(p));o=bpy.context.object;o.scale=(scale[0],scale[2],scale[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return finish(o,name,material,group,bevel)
def ellipsoid(name,p,scale,material,group='motorcycle'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=bp(p));o=bpy.context.object;o.scale=(scale[0],scale[2],scale[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,material,group)
def rod(name,a,b,r,material,group='motorcycle',n=12,r2=None):
    av,bv=Vector(bp(a)),Vector(bp(b));bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=(bv-av).length,location=(av+bv)/2)
    o=bpy.context.object;o.rotation_euler=(bv-av).to_track_quat('Z','Y').to_euler();return finish(o,name,material,group)
def tube(name,points,r,material,group='motorcycle',cyclic=False):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=4;c.bevel_depth=r;c.bevel_resolution=2
    sp=c.splines.new('POLY');sp.points.add(len(points)-1)
    for q,p in zip(sp.points,points):q.co=(*bp(p),1)
    sp.use_cyclic_u=cyclic;o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(materials[material]);groups[group].append(o);return o
def ring(name,x,y,z,major,minor,material,axial=1):
    p=[];f=[];N=64;K=10
    for j in range(N):
        a=j/N*math.tau
        for k in range(K):
            b=k/K*math.tau;r=major+minor*math.cos(b);p.append((x+minor*math.sin(b)*axial,y+r*math.cos(a),z+r*math.sin(a)))
    for j in range(N):
        for k in range(K):a=j*K+k;b=j*K+(k+1)%K;c=((j+1)%N)*K+(k+1)%K;d=((j+1)%N)*K+k;f.append((a,b,c,d))
    return mesh(name,p,f,material)
def loft(name,sections,material,sub=2):
    # z, half-width, bottom, top; superellipse shoulders keep tank/seat silhouettes.
    p=[];f=[];N=16
    for z,w,low,high in sections:
        for j in range(N):
            a=j/N*math.tau;p.append((w*math.cos(a),(low+high)/2+(high-low)/2*math.sin(a),z))
    for i in range(len(sections)-1):
        for j in range(N):a=i*N+j;b=i*N+(j+1)%N;c=(i+1)*N+(j+1)%N;d=(i+1)*N+j;f.append((a,b,c,d))
    f+=[tuple(reversed(range(N))),tuple((len(sections)-1)*N+j for j in range(N))]
    return mesh(name,p,f,material,sub=sub)
def plate(name,coords,material,depth=.012,bevel=.008):
    # Thin closed manufactured panel, never a half-metre solid wedge.
    p=coords+[(x-math.copysign(depth,x),y,z) for x,y,z in coords];n=len(coords)
    f=[tuple(range(n)),tuple(reversed(range(n,n*2)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    return mesh(name,p,f,material,bevel=bevel)

# GSX250R: 1.430 m wheelbase, 2.085 m overall length; tyres 110/80 and 140/70-17.
for front,z,r,width in [(True,-.715,.304,.110),(False,.715,.314,.140)]:
    label='front' if front else 'rear';half=width/2
    ring(label+'-rounded-sport-tyre',0,r,z,r-.052,.052,'rubber',half/.052)
    ring(label+'-black-alloy-rim',0,r,z,.218,.019,'frame',half/.019*.7)
    for s in [-1,1]:
        ring(label+'-yellow-rim-tape-'+str(s),s*(half*.87),r,z,.234,.004,'rim-tape',.35)
    rod(label+'-axle',(-half,r,z),(half,r,z),.039,'silver',n=24)
    # Ten slender black spokes with clearly open gaps.
    for i in range(5):
        for delta in [-.07,.07]:
            a=i/5*math.tau+delta
            rod(label+'-spoke',(-.018,r+math.cos(a)*.047,z+math.sin(a)*.047),(.012,r+math.cos(a+.15)*.211,z+math.sin(a+.15)*.211),.009,'frame',n=8)
    x=-half-.008 if front else half+.008
    ring(label+'-brake-disc',x,r,z,.118 if front else .095,.014,'rotor',.17)
    for i in range(6):
        a=i/6*math.tau;rod(label+'-disc-web',(x,r+math.cos(a)*.036,z+math.sin(a)*.036),(x,r+math.cos(a+.12)*.12,z+math.sin(a+.12)*.12),.009,'rotor',n=6)
    cube(label+'-brake-caliper',(x,r+.073,z+.105),(.038,.076,.045),'frame',.012)
    # Shallow lateral tread grooves follow the tyre crown.
    for i in range(28):
        a=i/28*math.tau;pts=[]
        for j in range(7):
            xx=(j/6*2-1)*half*.76;aa=a+xx*.55;rad=r-.001-.014*(xx/half)**2;pts.append((xx,r+math.cos(aa)*rad,z+math.sin(aa)*rad))
        tube(label+'-tread-sipe',pts,.0011,'frame')

for s in [-1,1]:
    rod('lower-fork', (s*.073,.31,-.715),(s*.073,.58,-.615),.023,'rotor',n=18)
    rod('chrome-fork',(s*.073,.57,-.615),(s*.073,.90,-.47),.016,'silver',n=18)
    rod('swingarm',(s*.10,.33,.19),(s*.09,.314,.715),.030,'frame',n=8)
    rod('main-frame',(s*.16,.39,.13),(s*.095,.86,-.37),.026,'frame')
    rod('seat-subframe',(s*.12,.49,.18),(s*.105,.81,.78),.018,'frame')
    rod('rear-footrest-bracket',(s*.14,.46,.2),(s*.23,.57,.47),.013,'silver')
    rod('footrest',(s*.16,.36,.20),(s*.27,.36,.20),.013,'silver')
    rod('clip-on',(s*.085,.894,-.46),(s*.29,.92,-.40),.013,'rotor')
    rod('grip',(s*.25,.919,-.40),(s*.35,.923,-.385),.022,'rubber',n=16)
    rod('lever',(s*.235,.931,-.44),(s*.346,.936,-.44),.006,'silver')
ellipsoid('parallel-twin-crankcase',(0,.414,.025),(.18,.173,.215),'frame')
for s in [-1,1]:
    rod('engine-round-cover',(s*.17,.418,.06),(s*.195,.418,.06),.111,'rotor',n=32)
    rod('engine-cover-centre',(s*.194,.418,.06),(s*.198,.418,.06),.075,'frame',n=32)
cube('radiator',(0,.611,-.31),(.30,.28,.047),'frame',.013)
for y in [.50+i*.018 for i in range(13)]:rod('radiator-fin',(-.137,y,-.338),(.137,y,-.338),.0025,'rotor',n=6)
rod('rear-shock',(0,.39,.22),(0,.70,.4),.022,'rotor')
tube('white-shock-spring',[(.037*math.cos(i/180*math.tau*9),.405+i/180*.28,.235+i/180*.15+.032*math.sin(i/180*math.tau*9)) for i in range(181)],.006,'white')

# Tank, separately stepped seats and elevated narrow tail. Smooth volumes are closed.
loft('sculpted-fuel-tank',[(-.44,.062,.76,.89),(-.39,.14,.745,.94),(-.25,.215,.72,.965),(-.07,.207,.715,.96),(.08,.165,.72,.884),(.19,.095,.74,.80)],'suzuki-blue')
loft('rider-seat',[(.09,.083,.752,.805),(.17,.142,.739,.792),(.39,.167,.758,.807),(.48,.138,.796,.824)],'seat',2)
loft('raised-tail-fairing',[(.33,.129,.663,.797),(.53,.16,.736,.862),(.78,.126,.795,.885),(.93,.075,.825,.862),(.97,.027,.832,.850)],'suzuki-blue',2)
loft('passenger-seat',[(.48,.125,.814,.841),(.58,.13,.836,.899),(.77,.108,.854,.91),(.87,.060,.851,.879)],'seat',2)
rod('fuel-filler',(0,.968,-.16),(0,.972,-.16),.040,'silver',n=32)
rod('fuel-cap-centre',(0,.972,-.16),(0,.974,-.16),.030,'frame',n=32)

# Front cowl wraps above the front wheel; fairing halves leave chassis gaps open.
loft('front-nose-cowl',[(-.95,.053,.782,.865),(-.90,.158,.778,.915),(-.77,.234,.805,.963),(-.60,.237,.847,.996),(-.49,.177,.895,1.005)],'suzuki-blue',2)
for s in [-1,1]:
    # Joined side covers close the airbox beneath the seat and tank, while the
    # rear wheel and swingarm stay visibly separate from the bodywork.
    plate('black-airbox-side-cover-'+str(s),[(s*.170,.742,.34),(s*.165,.745,.13),(s*.180,.723,-.11),(s*.175,.540,-.04),(s*.133,.479,.19),(s*.139,.621,.36)],'frame',.016,.012)
    plate('blue-seat-side-panel-'+str(s),[(s*.137,.785,.76),(s*.165,.796,.43),(s*.166,.764,.17),(s*.155,.696,.24),(s*.147,.710,.47)],'suzuki-blue',.014,.009)
    plate('seat-panel-white-stripe-'+str(s),[(s*.168,.775,.39),(s*.168,.765,.20),(s*.160,.718,.26),(s*.160,.735,.36)],'white',.002,.001)
    plate('upper-side-fairing-'+str(s),[(s*.15,.802,-.92),(s*.244,.872,-.70),(s*.246,.807,-.40),(s*.223,.708,-.12),(s*.211,.532,-.25),(s*.198,.557,-.50)],'suzuki-blue',.014,.010)
    plate('lower-side-fairing-'+str(s),[(s*.201,.58,-.50),(s*.218,.58,-.23),(s*.195,.41,-.09),(s*.165,.263,.23),(s*.172,.211,.15),(s*.175,.206,-.29),(s*.169,.29,-.40)],'dark-blue',.014,.009)
    plate('black-fairing-vent-'+str(s),[(s*.258,.786,-.55),(s*.235,.757,-.15),(s*.212,.665,-.13),(s*.235,.710,-.38)],'frame',.009,.003)
    plate('silver-livery-swoosh-'+str(s),[(s*.256,.789,-.66),(s*.249,.779,-.42),(s*.235,.723,-.23),(s*.236,.755,-.46)],'white',.003,.001)
    plate('white-lower-graphic-'+str(s),[(s*.213,.47,-.22),(s*.189,.284,.12),(s*.179,.238,.10),(s*.194,.354,-.16)],'white',.003,.001)
    plate('lime-lower-graphic-'+str(s),[(s*.184,.285,-.27),(s*.180,.215,-.15),(s*.178,.215,-.06),(s*.190,.341,-.23)],'rim-tape',.003,.001)
    tube('mirror-stem-'+str(s),[(s*.198,.937,-.68),(s*.262,1.013,-.61),(s*.316,1.052,-.57)],.008,'frame')
    ellipsoid('mirror-shell-'+str(s),(s*.335,1.058,-.56),(.051,.031,.026),'frame')
    ellipsoid('mirror-reflector-'+str(s),(s*.335,1.062,-.54),(.043,.023,.009),'silver')
    rod('indicator-stem',(s*.21,.736,-.56),(s*.289,.723,-.56),.009,'rubber')
    ellipsoid('clear-indicator',(s*.293,.724,-.56),(.027,.017,.028),'lamp')
    ellipsoid('amber-bulb',(s*.296,.724,-.582),(.012,.009,.006),'amber')
    # Position lamp streaks on the nose.
    tube('LED-position-light',[(s*.052,.864,-.936),(s*.100,.882,-.897),(s*.144,.901,-.84)],.004,'lamp')
# Real curved windscreen with 3 mm thickness, leaning rearwards.
p=[];f=[];NX=20;NY=14
for j in range(NY+1):
    v=j/NY
    for i in range(NX+1):
        u=i/NX*2-1;p.append((u*(.188-.046*v),.941+.165*v+.014*(1-u*u),-.773+.235*v+.043*u*u))
for j in range(NY):
    for i in range(NX):k=j*(NX+1)+i;f.append((k,k+1,k+NX+2,k+NX+1))
wind=mesh('curved-windscreen',p,f,'smoke');sol=wind.modifiers.new('3 mm moulded screen','SOLIDIFY');sol.thickness=.003
cube('LCD-cluster',(0,.903,-.448),(.19,.066,.09),'frame',.024)
cube('LCD-display',(0,.936,-.442),(.141,.009,.060),'lamp',.012)
ellipsoid('central-halogen-headlight',(0,.821,-.953),(.065,.043,.014),'lamp')
# Fender arches over the wheel, with solid shell edges.
p=[];f=[]
for j in range(21):
    a=-1.0+j/20*2.5
    for i in range(9):
        u=i/8*2-1;r=.329-.016*u*u;p.append((u*.079,.304+r*math.cos(a),-.715+r*math.sin(a)))
for j in range(20):
    for i in range(8):k=j*9+i;f.append((k,k+1,k+10,k+9))
fender=mesh('blue-front-fender',p,f,'suzuki-blue');fender.modifiers.new('Fender thickness','SOLIDIFY').thickness=.005
# Long visible right-side black silencer with stamped silver heat shield.
tube('exhaust-header',[(.04,.39,-.20),(.05,.22,-.26),(.18,.19,.06),(.245,.25,.35)],.021,'rotor')
rod('exhaust-canister',(.248,.256,.34),(.264,.419,.86),.077,'frame',n=8,r2=.063)
rod('exhaust-end-cap',(.264,.419,.85),(.269,.430,.892),.063,'silver',n=8,r2=.050)
rod('exhaust-dark-outlet',(.269,.430,.893),(.271,.432,.897),.029,'rubber',n=20)
plate('silver-heat-shield',[(.320,.271,.36),(.324,.326,.40),(.329,.449,.79),(.312,.428,.83),(.307,.365,.63)],'silver',.005,.006)
cube('tail-light',(0,.826,.952),(.09,.025,.020),'red',.005)
rod('number-plate-carrier',(0,.808,.883),(0,.565,1.015),.017,'frame')
cube('yellow-rear-plate',(0,.580,1.028),(.17,.092,.008),'gold',.006)
for s in [-1,1]:ellipsoid('rear-indicator',(s*.128,.679,.931),(.03,.014,.017),'lamp')
rod('side-stand',(-.13,.303,.21),(-.294,.022,.36),.012,'rotor')
cube('stand-foot',(-.294,.010,.36),(.05,.017,.061),'frame',.004)

# Six-panel baseball crown with inner shell, turned hem, and an attached solid bill.
P=[];F=[];N=72;R=28
for j in range(R+1):
    t=.003+j/R*(math.pi/2-.003)
    for i in range(N):
        a=i/N*math.tau;dimple=1-.013*math.cos(a*6)*math.sin(t)**3
        P.append((.093*math.sin(t)*math.sin(a)*dimple,.108*math.cos(t),.104*math.sin(t)*math.cos(a)*dimple))
for j in range(R):
    for i in range(N):k=j*N+i;F.append((k,j*N+(i+1)%N,(j+1)*N+(i+1)%N,k+N))
crown=mesh('continuous-six-panel-crown',P,F,'cap-cloth','cap');crown.modifiers.new('Cotton shell thickness','SOLIDIFY').thickness=.0022
def brim(u,v):
    a=u*1.24;x=.093*math.sin(a);back=.104*math.cos(a)
    return (x*(1+.065*math.sin(v*math.pi)), -.0015-.011*(abs(u)**1.7)*v-.006*v,back+v*.09*max(.05,math.cos(a))**.50)
P=[];F=[];NX=48;NY=16
for j in range(NY+1):
    for i in range(NX+1):P.append(brim(i/NX*2-1,j/NY))
for j in range(NY):
    for i in range(NX):k=j*(NX+1)+i;F.append((k,k+1,k+NX+2,k+NX+1))
bill=mesh('attached-padded-curved-bill',P,F,'cap-cloth','cap');bill.modifiers.new('Padded brim thickness','SOLIDIFY').thickness=.0035
tube('crown-sewn-hem',[(.093*math.sin(a),0,.104*math.cos(a)) for a in [i/120*math.tau for i in range(120)]],.003,'cap-cloth','cap',True)
for i in range(6):
    a=i/6*math.tau;tube('crown-panel-seam',[(.0934*math.sin(t)*math.sin(a),.1085*math.cos(t),.1044*math.sin(t)*math.cos(a)) for t in [j/32*math.pi/2 for j in range(33)]],.00055,'cap-seam','cap')
for v in [.12,.30,.48,.66,.84,.98]:tube('bill-top-stitch',[(x,y+.001,z) for x,y,z in [brim(i/48*2-1,v) for i in range(49)]],.00035,'cap-seam','cap')
ellipsoid('top-covered-button',(0,.110,0),(.006,.0023,.006),'cap-cloth','cap')

# One sculpted, closed petal shared by all flower instances. 0.7 mm centre body,
# finer rolled margins and a turned tip; not a DoubleSide flat card.
P=[];F=[];NX=4;NY=8
for side in [1,-1]:
    for j in range(NY+1):
        v=j/NY
        for i in range(NX+1):
            u=i/NX*2-1;w=.0054*math.sin(math.pi*(.025+.95*v))**.64
            thickness=.00014+.00040*(1-u*u)*math.sin(math.pi*v)
            y=.0045*v*v+.0023*u*u*math.sin(math.pi*v)+.0023*max(0,(v-.75)/.25)**2
            P.append((u*w,y+side*thickness,v*.022))
n=(NX+1)*(NY+1)
for j in range(NY):
    for i in range(NX):
        k=j*(NX+1)+i;F.extend([(k,k+1,k+NX+2,k+NX+1),(k+n+NX+1,k+n+NX+2,k+n+1,k+n)])
border=list(range(NX+1))+[j*(NX+1)+NX for j in range(1,NY+1)]+[NY*(NX+1)+i for i in range(NX-1,-1,-1)]+[j*(NX+1) for j in range(NY-1,0,-1)]
for i,k in enumerate(border):v=border[(i+1)%len(border)];F.append((k,v,v+n,k+n))
mesh('cupped-solid-everlasting-petal',P,F,'petal-ivory','petal')

# Export evaluated smooth surfaces. Dedupe position+normal keeps sharp joins and
# makes native Blender geometry portable without a runtime loader dependency.
deps=bpy.context.evaluated_depsgraph_get();result={'metadata':{'authoring':'Blender 5.2','units':'metres','motorcycle':'GSX250R, user blue livery, catalogue proportions'},'materials':meta,'groups':{}}
for group,objects in groups.items():
    items=[]
    for ob in objects:
        ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();p=[];no=[];ix=[];seen={};matrix=ob.matrix_world;nm=matrix.to_3x3().inverted().transposed()
        for tri in me.loop_triangles:
            for li in tri.loops:
                v=matrix@me.vertices[me.loops[li].vertex_index].co;nrm=(nm@me.corner_normals[li].vector).normalized()
                vv=(round(v.x,6),round(v.z,6),round(-v.y,6));nn=(round(nrm.x,5),round(nrm.z,5),round(-nrm.y,5));key=vv+nn
                if key not in seen:seen[key]=len(p)//3;p.extend(vv);no.extend(nn)
                ix.append(seen[key])
        items.append({'name':ob.name,'material':ob.data.materials[0].name,'position':p,'normal':no,'index':ix});ev.to_mesh_clear()
    result['groups'][group]=items
(OUT/'models.js').write_text('export default '+json.dumps(result,separators=(',',':'))+';\n',encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'gsx250r-cap-flowers.blend'))
print('REFINED_PROPS_EXPORTED', {k:len(v) for k,v in result['groups'].items()},'bytes', (OUT/'models.js').stat().st_size,flush=True)
