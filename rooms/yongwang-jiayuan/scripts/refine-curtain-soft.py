"""Second photo-guided curtain: sparse soft folds and diffused bright cloth. Execute via Blender Lab MCP only.

Preserves the complete authored room. Closed and gathered cloth are authored as
Blender shape keys, exported together, and interpolated by the webpage.
"""
import os
import bpy,bmesh,copy,gzip,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector

ROOT=Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[3]));OUT=ROOT/'room-site/dist/assets/full-room'
data=json.loads((OUT/'scene.json').read_text(encoding='utf-8'))
assert data['revision']=='curtain22b'
before=copy.deepcopy(data['nodes']);raw=bytearray((OUT/'geometry.bin').read_bytes())
obs={o['web_node_id']:o for o in bpy.data.objects if 'web_node_id' in o}
mats={m['web_material_id']:m for m in bpy.data.materials if 'web_material_id' in m}
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
left=-.680;right=1.130;width=right-left;top=2.360;bottom=.500
opened_width=.345;folds=7;thickness=.0006

def linear(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def bp(p):return (p[0],-p[2],p[1])
def pack(a,size=None):
    a=np.asarray(a);a=a.astype('<u4' if a.dtype.kind in 'iu' else '<f4').ravel()
    while len(raw)%4:raw.append(0)
    d={'offset':len(raw),'length':len(a),'type':'Uint32Array' if a.dtype.kind=='u' else 'Float32Array'}
    if size:d['itemSize']=size
    raw.extend(a.tobytes());return d

def save_texture(name,pixels,color=True,repeat=(1,1)):
    h,w=pixels.shape[:2];im=bpy.data.images.new(name,width=w,height=h,alpha=False)
    im.colorspace_settings.name='sRGB' if color else 'Non-Color'
    rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=pixels
    im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save();im.pack()
    tid=len(data['textures']);d=copy.deepcopy(data['textures'][40]);d.update(id=tid,webPath='./assets/full-room/'+name+'.png',colorSpace='srgb' if color else '',wrapS=1000,wrapT=1000,repeat=list(repeat))
    data['textures'].append(d);return tid,im

# Subtle ivory-on-natural jacquard: alternate tulip plaques and rose medallions,
# with a broad gathered heading and the denser stitched lower border in the photo.
rng=np.random.default_rng(2209);h=1536;w=1024
yy,xx=np.mgrid[:h,:w];u=xx/(w-1);v=yy/(h-1)
cu=(u*6+.13)%1-.5;cv=(v*6+.04)%1-.5
cell=(np.floor(u*6+.13)+np.floor(v*6+.04)).astype(int)%2
plaque=(np.abs(cu)<.155)&(np.abs(cv)<.195)
oval=(cu/.161)**2+(cv/.216)**2<1
patch=np.where(cell==0,plaque,oval).astype(float)
def ellipse(x,y,a,b,angle=0):
    X=(cu-x)*math.cos(angle)+(cv-y)*math.sin(angle)
    Y=-(cu-x)*math.sin(angle)+(cv-y)*math.cos(angle)
    return (X/a)**2+(Y/b)**2<1
stem=(np.abs(cu)<.008)&(cv>-.145)&(cv<.088)
leaves=ellipse(-.045,-.058,.026,.069,-.64)|ellipse(.045,-.09,.026,.066,.64)
tulip=(ellipse(0,.090,.074,.079)&(cv<.15))
tulip&=~(((np.abs(cu-.025)<.010)|(np.abs(cu+.025)<.010))&(cv>.09))
rose=np.zeros((h,w),bool)
for k in range(6):
    a=k*math.tau/6;rose|=ellipse(.031*math.cos(a),.084+.038*math.sin(a),.034,.041,a)
rose|=ellipse(0,.084,.039,.037)
swirl=(np.abs(np.hypot(cu,cv-.084)-(.025+.009*np.sin(np.arctan2(cv-.084,cu)*3)))<.005)
flower=(stem|leaves|np.where(cell==0,tulip,rose&~swirl))&patch.astype(bool)
thread=.009*np.sin(xx*math.tau/3.6)+.007*np.cos(yy*math.tau/4.2)
slub=.010*rng.normal(size=(h,1))+.006*rng.normal(size=(1,w))+.004*rng.normal(size=(h,w))
base=np.zeros((h,w,3))+np.array([.90,.865,.792])
base+=patch[:,:,None]*np.array([.052,.058,.067]);base-=flower[:,:,None]*np.array([.075,.072,.064])
base+=(thread+slub)[:,:,None]
header=v>.963;hem=v<.023
base[header]=base[header]*.91+np.array([.025,.017,.0])
base[hem]=base[hem]*.89+np.array([.035,.018,.002])
stitch=(np.abs(v-.963)<.0012)|(np.abs(v-.026)<.0010)|(np.abs(v-.016)<.0010)
base[stitch]*=.93
cloth_tex,cloth_image=save_texture('curtain23-ivory-jacquard',np.clip(base,0,1))

# Light scattering is stronger in the thin weave and weaker in the denser flowers
# and seam tape. It is diffuse cloth backlighting, not clear glass refraction.
glow=(.76+.055*np.sin(u*6+v*4)+.055*np.sin(u*17-v*3))*(1-.075*patch-.055*flower)
glow*=.64+.36*np.sin(v*math.pi*.84+.16)
glow*=.82+.18*np.exp(-((u-.84)/.2)**2)
glow*=1-.70*header-.66*hem
glow*=.95+.05*np.cos(v*math.pi)
glow=np.clip(glow,.05,1)
glow_tex,glow_image=save_texture('curtain23-diffuse-translucency',np.repeat(glow[:,:,None],3,axis=2))
Y,X=np.mgrid[:512,:512];alternate=((X//8+Y//8)%2)==0
relief=np.clip(.5+.22*np.where(alternate,np.cos(X*math.tau/8),np.cos(Y*math.tau/8))+.025*rng.normal(size=(512,512)),0,1)
bump_tex,bump_image=save_texture('curtain23-fine-thread-relief',np.repeat(relief[:,:,None],3,axis=2),False,(30,30))

mid=160;d=data['materials'][mid]
d['props'].update(transparent=False,opacity=1,depthWrite=True,roughness=.93,metalness=0,sheen=.40,sheenRoughness=.86,bumpScale=.00020,emissiveIntensity=.055)
d['colors'].update(color=[1,1,1],emissive=linear(np.array([.97,.96,.90])).tolist(),sheenColor=linear(np.array([.88,.85,.78])).tolist())
d['textures']={'map':cloth_tex,'bumpMap':bump_tex,'emissiveMap':glow_tex}
d['userData']={'surfaceFinish':'photo-guided ivory jacquard, fine yarn, diffuse translucency','curtainBacklight':True,'revision':'curtain23'}
mat=mats[mid];mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();links=mat.node_tree.links
output=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled')
bs.inputs['Roughness'].default_value=.93;bs.inputs['Sheen Weight'].default_value=.40
bs.inputs['Sheen Roughness'].default_value=.86
bs.inputs['Subsurface Weight'].default_value=.08
links.new(bs.outputs['BSDF'],output.inputs['Surface'])
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
tex=nodes.new('ShaderNodeTexImage');tex.image=cloth_image;links.new(uv.outputs[0],tex.inputs[0]);links.new(tex.outputs['Color'],bs.inputs['Base Color'])
gl=nodes.new('ShaderNodeTexImage');gl.image=glow_image;links.new(uv.outputs[0],gl.inputs[0]);links.new(gl.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.055
mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=30;links.new(uv.outputs[0],mapping.inputs[0])
tx=nodes.new('ShaderNodeTexImage');tx.image=bump_image;links.new(mapping.outputs[0],tx.inputs[0])
b=nodes.new('ShaderNodeBump');b.inputs['Distance'].default_value=.00020;links.new(tx.outputs['Color'],b.inputs['Height']);links.new(b.outputs[0],bs.inputs['Normal'])

# One continuous cloth with closed edges, hems and long fine tassels.
verts=[];opens=[];uvs=[];faces=[]
def surface(a,t,is_open,offset=0):
    wd=opened_width if is_open else width;start=right-wd
    phase=math.tau*13*a
    x=start+wd*a+.003*math.sin(a*26+t*3)*(math.sin(math.pi*a)**2)*t
    # Sparse, irregular soft folds: broad almost-flat fields, with a few gentle
    # seams releasing from the heading. No corrugated sinusoidal sheet.
    y=top-(top-bottom)*t-.012*math.sin(phase*.5)**2*(1-t)**14
    y+=.007*math.sin(a*16+.5)*t**4+.003*math.sin(a*39)*t**8
    if is_open:
        z=-1.652+(.060+.006*t)*math.cos(phase)+.003*math.sin(a*19+t*5)*t
    else:
        spread=1-math.exp(-t*17)
        z=-1.606+.007*math.sin(a*13+t*2)*spread
        for k,c in enumerate([.083,.215,.367,.513,.674,.813,.955]):
            center=c+.013*math.sin(k*1.8+t*2.7)*t
            depth=[.031,.019,.038,.026,.021,.039,.023][k]
            z-=depth*math.exp(-((a-center)/(.023+.017*t))**2)*spread
        z+=.013*math.sin(phase)*(1-spread)
        z+=.009*math.sin(a*9+.4)*math.sin(t*math.pi)
    return x,y,z+offset
def add_point(p,o,uv):verts.append(p);opens.append(o);uvs.append(uv);return len(verts)-1
nx=208;ny=48;off=(nx+1)*(ny+1)
for sign in [1,-1]:
    for j in range(ny+1):
        for i in range(nx+1):
            a=i/nx;t=j/ny;add_point(surface(a,t,False,sign*thickness/2),surface(a,t,True,sign*thickness/2),(a,1-t))
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;faces.extend([(k,k+nx+1,k+nx+2,k+1),(off+k,off+k+1,off+k+nx+2,off+k+nx+1)])
boundary=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
for i,k in enumerate(boundary):n=boundary[(i+1)%len(boundary)];faces.append((k,k+off,n+off,n))
body_faces=len(faces)
# A dense row of thread bundles with small naturally uneven lengths and curls.
for f in range(325):
    a=(f+.35)/325;length=.058+.011*math.sin(f*1.913)+.003*math.cos(f*.42)
    base_c=Vector(surface(a,1,False));base_o=Vector(surface(a,1,True));idx=len(verts)
    for j in range(7):
        t=j/6;sway=.0016*math.sin(t*4+f*.74)*t
        for k in range(5):
            angle=k/5*math.tau;delta=Vector((sway+.00075*math.cos(angle),-length*t,.0013*math.sin(t*5+f)+.00075*math.sin(angle)))
            add_point(tuple(base_c+delta),tuple(base_o+delta),(a,.012))
        if j:
            for k in range(5):n=(k+1)%5;faces.append((idx+(j-1)*5+k,idx+j*5+k,idx+j*5+n,idx+(j-1)*5+n))
    faces.append(tuple(idx+k for k in reversed(range(5))));faces.append(tuple(idx+30+k for k in range(5)))

me=bpy.data.meshes.new('photo-jacquard-curtain-with-closed-and-gathered-shapes');me.from_pydata([bp(p) for p in verts],[],faces)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
layer=me.uv_layers.new(name='UVMap')
for p in me.polygons:
    p.use_smooth=True
    for li in p.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
panel=obs[1330];panel.modifiers.clear();panel.data=me;panel.matrix_local=Matrix.Identity(4)
panel.name='ivory-jacquard-curtain';panel['web_name']=panel.name;me.materials.append(mat)
panel.material_slots[0].link='DATA';panel.material_slots[0].material=mat
panel.shape_key_add(name='Closed');key=panel.shape_key_add(name='Gathered right')
for i,p in enumerate(opens):key.data[i].co=bp(p)

def arrays(mesh):
    mesh.calc_loop_triangles();p=[];n=[];uv=[]
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index].co;no=mesh.corner_normals[loop.index].vector
        p.append((v.x,v.z,-v.y));n.append((no.x,no.z,-no.y));uv.append(tuple(mesh.uv_layers.active.data[loop.index].uv))
    return p,n,uv
p,n,uv=arrays(me);morph=me.copy();morph.name='temporary-gathered-normal-evaluation'
for i,v in enumerate(morph.vertices):v.co=bp(opens[i])
morph.update();mp,mn,_=arrays(morph);bpy.data.meshes.remove(morph)
gid=len(data['geometries']);data['geometries'].append({'id':gid,'attributes':{'position':pack(p,3),'normal':pack(n,3),'uv':pack(uv,2)},
    'index':pack([i for t in me.loop_triangles for i in t.loops]),'groups':[],
    'morphTargets':{'position':[pack(mp,3)],'normal':[pack(mn,3)]},
    'userData':{'authoring':'Blender','sourceType':'PhotoCurtain','revision':'curtain23'}})
node=data['nodes'][1330];node.update(name=panel.name,matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1],geometry=gid,castShadow=False,receiveShadow=True)
node['userData'].update(curtainShapeKey=True,closedLeft=left,fixedRight=right,openWidth=opened_width,revision='curtain23')
panel['web_user_data']=json.dumps(node['userData'])
data['nodes'][1329]['name']='photo-guided-curtain-assembly';obs[1329].name='photo-guided-curtain-assembly'
# Retain old source objects hidden; the new continuous mesh includes the fringe.
for ob in list(panel.children_recursive):
    ob.hide_render=True;ob.hide_set(True)
    if 'web_node_id' in ob:data['nodes'][ob['web_node_id']]['visible']=False
# Detach archived fringe so hidden legacy bounds cannot shift the clickable area.
for ob in list(panel.children):
    if 'web_node_id' in ob:
        d=data['nodes'][ob['web_node_id']];d['parent']=-1;d['userData']['archived']=True
    ob.parent=None
for k,nid in enumerate(data['refs']['curtainRings']):
    a=k/13;ob=obs[nid];W=Matrix.Translation(Vector((left+width*a,2.389,-1.59)))
    ob.matrix_local=C@W@C.inverted();d=data['nodes'][nid]
    d['matrix']=[W[r][c] for c in range(4) for r in range(4)]
    d['userData'].update(closedX=left+width*a,slideU=a,fixedRight=right,closedWidth=width,openWidth=opened_width)

# Verify the entire cloth sweep, including the thread bundles, stays outside the
# cupboard. A non-overlapping X interval is a conservative full-motion guarantee.
wardrobe=obs[772];cabinet_points=[o.matrix_world@Vector(c) for o in [wardrobe]+list(wardrobe.children_recursive) if o.type=='MESH' for c in o.bound_box]
cabinet_right=max(p.x for p in cabinet_points)
min_clearance=min(min(p[0] for p in verts),min(p[0] for p in opens),left-.028)-cabinet_right
assert min_clearance>.04,min_clearance
data['revision']='curtain23';data['statistics']['meshes']=len(data['geometries'])
data['statistics']['triangles']=sum(g['index']['length']//3 for g in data['geometries'])
data['statistics']['curtainRefinement']={'blenderShapeKeys':2,'cupboardSweepGap':min_clearance,'clothThickness':thickness,'fringeBundles':325}
bpy.context.scene['web_revision']='curtain23';bpy.context.scene['curtain_notes']='Ivory jacquard, true cloth morph targets, fixed right edge, safe cupboard clearance throughout the slide.'
key.value=0;bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'))
(OUT/'geometry.bin').write_bytes(raw);(OUT/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9))
(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'curtain23','vertices':len(verts),'faces':len(faces),'minimumCupboardClearance':min_clearance,'shapeKeys':list(panel.data.shape_keys.key_blocks.keys()),'texturesAdded':3,'saved':True}
