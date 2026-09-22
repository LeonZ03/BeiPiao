"""exterior31a -> exterior31. Blender Lab MCP only; reference-based courtyard.

References: dist/assets/reference-exterior-level.jpg and exterior-down.jpg.
Facade layout is retained; recess depth/edge radii are photo estimates.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='exterior31a'
assert bpy.context.scene.get('web_revision')=='exterior31a'
def progress(stage):
    report=ROOT/'analysis/exterior-authoring-progress.txt';report.parent.mkdir(exist_ok=True);report.write_text(stage,encoding='utf8')
progress('textures')
instance_modifiers=[(m,m.show_viewport) for o in obs.values() for m in o.modifiers if m.type=='NODES']
for m,_ in instance_modifiers:m.show_viewport=False
rng=np.random.default_rng(3131);N=1024;y,x=np.mgrid[0:N,0:N]/N
grain=rng.normal(0,.010,(N,N));patch=.020*np.sin(x*math.tau*3+.8*np.sin(y*math.tau))+.012*np.cos(y*math.tau*2+x*8)
plaster=.58+patch+grain
wall_t=texture('exterior31-mineral-render',np.stack([plaster*.98,plaster,plaster*.98],axis=-1))
wall_h=texture('exterior31-render-relief',np.clip(.5+grain*7,0,1),color=False)
wall_r=texture('exterior31-render-roughness',np.clip(.84+patch+grain,0,1),color=False)
stone=.57+patch*.6+rng.normal(0,.008,(N,N))
stone_t=texture('exterior31-aged-concrete',np.stack([stone,stone*.99,stone*.95],axis=-1))
road=.35+patch*.6+rng.normal(0,.018,(N,N));chips=rng.random((N,N))>.975;road+=chips*.08
road_t=texture('exterior31-dry-asphalt',np.stack([road*.97,road,road*.98],axis=-1))
soil=.30+patch+rng.normal(0,.024,(N,N))
soil_t=texture('exterior31-tree-soil',np.stack([soil*1.10,soil,soil*.82],axis=-1))

# A shared equirectangular sky/horizon for window reflections. It has no per-frame
# scene capture and no individual window reflector. Diffuse room IBL is unchanged.
y,x=np.mgrid[0:256,0:512];v=y/255;u=x/511
sky=np.zeros((256,512,3),dtype=float)
for k,(low,high) in enumerate(zip([.72,.77,.77],[.47,.63,.74])):sky[:,:,k]=low+(high-low)*np.clip((v-.48)*1.95,0,1)
horizon=.47+.045*np.sin(u*math.tau*5)+.035*np.sin(u*math.tau*13)
mask=v<horizon;sky[mask]=np.array([.23,.29,.24])+(.5+.5*np.sin(u[mask]*57))[:,None]*.06
env_t=texture('exterior31-window-environment',sky);data['textures'][env_t]['mapping']=303
wall=material('Courtyard · mineral grey render',24,color=(1,1,1),rough=.9,textures={'map':wall_t,'bumpMap':wall_h,'roughnessMap':wall_r},bumpScale=.0014,vertexColors=True)
cream=material('Residential · faded warm mineral render',32,color=(1,.985,.89),rough=.9,textures={'map':wall_t,'bumpMap':wall_h,'roughnessMap':wall_r},bumpScale=.0012,vertexColors=True)
concrete=material('Courtyard · concrete sills and coping',21,color=(1,1,1),rough=.79,textures={'map':stone_t,'bumpMap':wall_h},bumpScale=.001,vertexColors=True)
road_mid=material('Courtyard · dry asphalt aggregate',19,color=(1,1,1),rough=.91,textures={'map':road_t,'bumpMap':wall_h},bumpScale=.0012)
paving=material('Courtyard · weathered paved strip',20,color=(1,.99,.96),rough=.91,textures={'map':stone_t,'bumpMap':wall_h},bumpScale=.001)
soil_mid=material('Courtyard · root soil',23,color=(1,1,1),rough=1,textures={'map':soil_t,'bumpMap':wall_h},bumpScale=.006)
window_mids=[material(f'Courtyard · recessed glass {i}',25,color=c,rough=.19+i*.045,textures={'envMap':env_t},metalness=.16,envMapIntensity=.65,metadata={'windowReflection':True}) for i,c in enumerate([(.25,.30,.29),(.33,.37,.35),(.21,.26,.26)])]
trim=material('Courtyard · muted aluminium frames',21,color=(.50,.53,.51),rough=.44,textures={},metalness=.40)
dark=material('Courtyard · window reveal shadow',25,color=(.105,.12,.11),rough=.92,textures={})
progress('material remap')

def physical_uv(o,scale=.36,ao=False):
    me=o.data
    uv=me.uv_layers.active or me.uv_layers.new(name='UVMap');uv.name='UVMap'
    colors=me.color_attributes.get('Color') or (me.color_attributes.new('Color','FLOAT_COLOR','CORNER') if ao else None)
    for f in me.polygons:
        axis=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=axis]
        for li in f.loop_indices:
            p=me.vertices[me.loops[li].vertex_index].co;w=o.matrix_local@p;uv.data[li].uv=(w[axes[0]]*scale,w[axes[1]]*scale)
            if colors:
                # Recess reveals carry restrained occlusion; broad walls stay clean.
                a=.88 if f.normal.z<-.5 else (.78 if abs(f.normal.y)<.45 else 1)
                colors.data[li].color=(a,a,a,1)
def bounds(o):
    a=np.array([[v.co.x,v.co.z,-v.co.y] for v in o.data.vertices]);return a.min(0),a.max(0)
def moved(nid,delta):
    o=obs[nid];M=o.matrix_local.copy();M.translation+=Vector(bp(delta));o.matrix_local=M;data['nodes'][nid]['matrix']=flat(C.inverted()@M@C);changed.add(nid)
def bevel(o,width):
    bm=bmesh.new();bm.from_mesh(o.data)
    edges=[e for e in bm.edges if e.is_manifold and e.calc_face_angle(0)>.5]
    bmesh.ops.bevel(bm,geom=edges,offset=width,segments=2,affect='EDGES');bm.to_mesh(o.data);bm.free()
def cube_mesh(name,center,size):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for q in bm.verts:q.co=Vector(bp([center[i]+size[i]*q.co[i] for i in range(3)]))
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();return me
def ring(nid,w,h,depth=.10):
    o=obs[nid];parts=[]
    for cx,cy,sx,sy in [(-w/2-.024,0,.052,h+.10),(w/2+.024,0,.052,h+.10),(0,-h/2-.024,w,.052),(0,h/2+.024,w,.052)]:
        parts.append(cube_mesh('Frame rail',(cx,cy,0),(sx,sy,depth)))
    bm=bmesh.new()
    for me in parts:bm.from_mesh(me);bpy.data.meshes.remove(me)
    me=bpy.data.meshes.new('Four-sided recessed frame');bm.to_mesh(me);bm.free();o.data=me;set_material(nid,trim);bevel(o,.004);physical_uv(o);export(o)

# Material remapping is restricted to the original outdoor branch, excluding the
# approved motorcycle and shadow proxies. Interior shared materials never change.
remap={18:paving,19:road_mid,20:paving,21:concrete,22:concrete,23:soil_mid,24:wall,32:cream}
for d in data['nodes'][193:640]:
    nid=d['id']
    if d.get('type')!='Mesh':continue
    mid=d.get('material')
    if mid in remap:
        o=obs[nid];o.data=o.data.copy();set_material(nid,remap[mid]);physical_uv(o,scale=.36,ao=mid in [21,22,24,32]);export(o)

# Detect existing windows from their authored five-part assemblies, so layout,
# opening sizes and grille placement continue to follow the original references.
windows=[]
for d in before['nodes'][250:628]:
    nid=d['id']
    if d.get('material') not in [25,27] or nid<1:continue
    prev=before['nodes'][nid-1]
    if prev.get('material')!=22 or prev['parent']!=d['parent']:continue
    lo,hi=bounds(obs[nid]);w,h=(hi-lo)[:2];x0,y0,z0=d['matrix'][12:15]
    windows.append({'glass':nid,'frame':nid-1,'x':x0,'y':y0,'z':z0,'w':float(w),'h':float(h),'parent':d['parent']})
assert len(windows)==43,('Unexpected window assemblies',len(windows))
progress('window booleans')

# Make actual masonry recesses. New cutters are temporary authoring objects;
# they never enter the website or the saved source scene.
cutters_by_wall={}
for nid in [n['id'] for n in before['nodes'][250:628] if n.get('material') in [24,30,32,33]]:
    if nid not in obs:continue
    o=obs[nid]
    if o.type!='MESH':continue
    lo,hi=bounds(o);center=np.array(data['nodes'][nid]['matrix'][12:15]);lo+=center;hi+=center
    if hi[1]-lo[1]<3 or hi[0]-lo[0]<2:continue
    candidates=[w for w in windows if w['parent']==data['nodes'][nid]['parent'] and lo[0]-.1<w['x']<hi[0]+.1 and lo[1]<w['y']<hi[1] and abs(w['z']-hi[2])<.35]
    if not candidates:continue
    # Rebuild the same cuboid bounds as welded manifold geometry for booleans.
    o.data=cube_mesh('Masonry with recessed openings', (lo+hi)/2-center,hi-lo);set_material(nid,remap.get(before['nodes'][nid]['material'],wall))
    cutter_parts=bmesh.new()
    for w in candidates:
        z=hi[2];cut=cube_mesh('Window recess cutter',(w['x']-center[0],w['y']-center[1],z-center[2]-.13),(w['w']+.042,w['h']+.042,.74))
        cutter_parts.from_mesh(cut);bpy.data.meshes.remove(cut)
        w['facade']=max(z,w.get('facade',-100))
    cut=bpy.data.meshes.new('Joined window cutters');cutter_parts.to_mesh(cut);cutter_parts.free()
    cutter=bpy.data.objects.new('Temporary apertures',cut);collection.objects.link(cutter);cutter.matrix_world=o.matrix_world.copy()
    activate(o);mod=o.modifiers.new('Window apertures','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True);bpy.data.meshes.remove(cut)
    bevel(o,.009);physical_uv(o,ao=True);export(o);cutters_by_wall[nid]=len(candidates)

progress('window assemblies')
for i,w in enumerate(windows):
    nid=w['glass'];z=w.get('facade',w['z']-.14)
    ring(w['frame'],w['w'],w['h'])
    set_material(nid,window_mids[i%3]);moved(nid,(0,0,z-.20-w['z']))
    # Mullions move together with the inset glazing, rather than float outside it.
    for child in [nid+1,nid+2]:
        set_material(child,trim);old=before['nodes'][child]['matrix'][14];moved(child,(0,0,z-.145-old))
    # Dark cavity behind the glass gives genuine parallax at oblique viewpoints.
    box('Window cavity', (w['x'],w['y'],z-.38),(w['w'],w['h'],.02),dark,w['parent'],0)
    # Subtle drip edge underneath the existing sill, restrained to reference form.
    box('Window sill drip',(w['x'],w['y']-w['h']/2-.056,z+.055),(w['w']+.15,.032,.20),concrete,w['parent'],.006)

# Soft manufactured edges and creased sheeting make the small covered scooters
# read as vehicles under fabric, rather than stacked cuboids. The GSX is untouched.
cover_mid=material('Courtyard · draped silver scooter cover',28,color=(.65,.68,.66),rough=.76,textures={'bumpMap':wall_h},bumpScale=.00045)
progress('ground and props')
for group in [727,742]:
    children=[n for n in before['nodes'] if n['parent']==group and n.get('type')=='Mesh']
    cover=children[-1];o=obs[cover['id']];o.data=o.data.copy();lo,hi=bounds(o);size=hi-lo
    verts=[];uvs=[];faces=[]
    # Closed cross sections: narrow at saddle, wider over handlebar, draped below.
    for j in range(13):
        t=j/12;z=(t-.5)*1.15;top=.20+.15*math.exp(-((t-.15)/.23)**2)-.07*t
        width=.24+.11*math.exp(-((t-.18)/.18)**2)
        for k in range(16):
            a=k/16*math.tau;xx=width*math.cos(a);yy=top-.47*(.5+.5*math.sin(a))
            xx+=.016*math.sin(t*31+k*.75)*abs(math.cos(a))**2
            verts.append((xx,yy,z));uvs.append((k/16,t))
    for j in range(12):
        for k in range(16):a=j*16+k;b=j*16+(k+1)%16;faces.append((a,b,b+16,a+16))
    faces.extend([tuple(reversed(range(16))),tuple(range(192,208))])
    o.data=mesh('Soft scooter cover',verts,faces,uvs,True);set_material(o['web_node_id'],cover_mid);export(o)

# Lower the underlay only, eliminating coplanar overlap beneath road surfacing.
moved(193,(0,-.035,0))
# Ground contact uses one shared, softly filtered mask. It remains separate from
# the approved indoor shadow maps and the existing motorcycle contact patch.
y,x=np.mgrid[-1:1:128j,-1:1:128j];a=np.exp(-(x*x+y*y)*3.5)*.26;a*=np.clip((1-np.maximum(abs(x),abs(y)))*8,0,1)
pixels=np.zeros((128,128,4));pixels[:,:,:3]=[.075,.085,.07];pixels[:,:,3]=a
contact_tex=texture('exterior31-contact',pixels)
contact=material('Courtyard · soft contact shadow',60,color=(1,1,1),textures={'map':contact_tex},opacity=1,transparent=True,depthWrite=False,polygonOffset=True,polygonOffsetFactor=-2)
for x,z,w,h in [(4,-7.7,1.1,1.8),(.2,-3.6,1.0,1.6),(1.15,-3.6,1,1.7),(.1,-7.25,1.4,1.4),(4.7,-7.25,1.4,1.4),(10.4,-7.25,1.4,1.4)]:
    y=-9.365 if z<-6 else -9.398
    me=mesh('Courtyard contact plane',[(x-w/2,y,z-h/2),(x-w/2,y,z+h/2),(x+w/2,y,z+h/2),(x+w/2,y,z-h/2)],[(0,1,2,3)],[(0,0),(0,1),(1,1),(1,0)])
    o=attach(me,'',contact);data['nodes'][o['web_node_id']].update(castShadow=False,receiveShadow=False);export(o)

# The first browser check showed the backlit canopy was still olive. Preserve
# spatial AO while shifting leaf reflectance toward a cooler living summer green.
for nid in [644,649,654]:
    d=data['nodes'][nid];colors=read(d['instanceColor']).reshape(-1,3)*np.array([.74,1.12,1.65]);d['instanceColor']=pack(colors.reshape(-1));changed.add(nid)
    obs[nid].data.attributes['InstanceTint'].data.foreach_set('color',np.column_stack([colors,np.ones(len(colors))]).astype(np.float32).ravel())
details={**before['statistics']['exteriorRefinement'],'stage':'complete','windows':len(windows),'recessDepth':.20,'recessedWalls':cutters_by_wall,'sharedWindowEnvironment':True,'dimensionsFrom':'reference photo estimates','interiorMaterialsUnchanged':True}
for n in before['nodes'][750:772]:assert data['nodes'][n['id']]==n,'Approved motorcycle changed'
progress('save source and export')
for m,visible in instance_modifiers:m.show_viewport=visible
result=save('exterior31',details)
progress('complete')
