"""Photo-based chair and woven racket strings. Run only via official Blender MCP.

Patch the saved complete scene and mesh pack; preserve all unrelated geometry.
Web/authoring coordinates below are metres, +Y up and +X toward the desk.
"""
import os
import bpy, bmesh, copy, gzip, json, math
import numpy as np
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[3]))
OUT = ROOT/'room-site/dist/assets/full-room'
data = json.loads((OUT/'scene.json').read_text(encoding='utf-8'))
assert data['revision'] == 'floor19'
before = copy.deepcopy(data['nodes'])
raw = bytearray((OUT/'geometry.bin').read_bytes())
objects = {o['web_node_id']:o for o in bpy.data.objects if 'web_node_id' in o}
materials = {m['web_material_id']:m for m in bpy.data.materials if 'web_material_id' in m}
collection = objects[1281].users_collection[0]
C = Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
identity = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
changed = set()

def bp(v): return (v[0], -v[2], v[1])
def srgb(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
def rgb(hex): return [srgb(int(hex[i:i+2],16)/255) for i in (0,2,4)]

def pack(a, size=None):
    a=np.asarray(a); integer=a.dtype.kind in 'iu'
    a=a.astype('<u4' if integer else '<f4').ravel()
    while len(raw)%4:raw.append(0)
    d={'offset':len(raw),'length':len(a),'type':'Uint32Array' if integer else 'Float32Array'}
    if size:d['itemSize']=size
    raw.extend(a.tobytes());return d

def export(mesh):
    mesh.calc_loop_triangles()
    p=[];n=[];uv=[]
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index].co;normal=mesh.corner_normals[loop.index].vector
        p.append((v.x,v.z,-v.y));n.append((normal.x,normal.z,-normal.y))
        uv.append(tuple(mesh.uv_layers.active.data[loop.index].uv))
    gid=len(data['geometries'])
    data['geometries'].append({'id':gid,'attributes':{'position':pack(p,3),'normal':pack(n,3),'uv':pack(uv,2)},
        'index':pack([i for t in mesh.loop_triangles for i in t.loops]),'groups':[],
        'userData':{'authoring':'Blender','sourceType':'PhotoRefinement','revision':'chair21'}})
    return gid

def attach(mesh,name,mid,parent=1280,nid=None,extra=None):
    if nid is None:
        nid=len(data['nodes']);desc=copy.deepcopy(before[1281]);desc['id']=nid;data['nodes'].append(desc)
        ob=bpy.data.objects.new(name,mesh);collection.objects.link(ob);objects[nid]=ob
    else:
        desc=data['nodes'][nid];old=objects[nid]
        if old.type=='MESH':ob=old;ob.modifiers.clear();ob.data=mesh
        else:
            ob=bpy.data.objects.new(name,mesh);collection.objects.link(ob)
            bpy.data.objects.remove(old,do_unlink=True);objects[nid]=ob
    ob.name=name;ob.parent=objects[parent];ob.matrix_local=Matrix.Identity(4)
    mesh.materials.clear();mesh.materials.append(materials[mid])
    ob.material_slots[0].link='DATA';ob.material_slots[0].material=materials[mid]
    desc.update(name=name,type='Mesh',parent=parent,geometry=export(mesh),material=mid,matrix=identity.copy(),
                visible=True,castShadow=True,receiveShadow=True)
    desc['userData']={'authoring':'Blender','blenderNode':nid,'revision':'chair21',**(extra or {})}
    ob['web_node_id']=nid;ob['web_name']=name;ob['web_user_data']=json.dumps(desc['userData'])
    changed.add(nid);return ob

def mesh_from(name,verts,faces,uvs=None,smooth=True):
    me=bpy.data.meshes.new(name);me.from_pydata([bp(p) for p in verts],[],faces)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
    layer=me.uv_layers.new(name='UVMap')
    for face in me.polygons:
        face.use_smooth=smooth
        for li in face.loop_indices:
            vi=me.loops[li].vertex_index
            layer.data[li].uv=uvs[vi] if uvs is not None else (verts[vi][0]/.06,verts[vi][1]/.06)
    return me

def upholstered(name,fun,nx=36,ny=36,uvplane='xy'):
    verts=[];uvs=[];faces=[]
    for sign in (1,-1):
        for j in range(ny+1):
            for i in range(nx+1):
                p=fun(i/nx*2-1,j/ny*2-1,sign);verts.append(p)
                uvs.append((p[2]/.06,p[1]/.06) if uvplane=='back' else (p[0]/.06,p[2]/.06) if uvplane=='seat' else (p[0]/.06,p[1]/.06))
    off=(nx+1)*(ny+1)
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i;faces.extend([(k,k+1,k+nx+2,k+nx+1),(off+k,off+k+nx+1,off+k+nx+2,off+k+1)])
    boundary=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    for i,k in enumerate(boundary):
        n=boundary[(i+1)%len(boundary)];faces.append((k,k+off,n+off,n))
    return mesh_from(name,verts,faces,uvs),[verts[i] for i in boundary]

def tubes(name,paths,radius=.0015,sides=8,radii=None):
    verts=[];faces=[];uvs=[]
    for path_id,path in enumerate(paths):
        points=[Vector(p) for p in path];offset=len(verts);distance=0
        for j,p in enumerate(points):
            tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized()
            helper=Vector((0,0,1)) if abs(tangent.z)<.95 else Vector((0,1,0))
            a=tangent.cross(helper).normalized();b=tangent.cross(a).normalized()
            r=radius if radii is None else radii[0]+(radii[1]-radii[0])*j/(len(points)-1)
            if j:distance+=(p-points[j-1]).length
            for k in range(sides):
                angle=k/sides*math.tau;v=p+r*(math.cos(angle)*a+math.sin(angle)*b)
                verts.append(tuple(v));uvs.append((k/sides,distance/.06))
            if j:
                for k in range(sides):
                    n=(k+1)%sides;faces.append((offset+(j-1)*sides+k,offset+(j-1)*sides+n,offset+j*sides+n,offset+j*sides+k))
        faces.append(tuple(offset+k for k in reversed(range(sides))))
        faces.append(tuple(offset+(len(points)-1)*sides+k for k in range(sides)))
    return mesh_from(name,verts,faces,uvs)

def texture(name,array,colorspace):
    h,w=array.shape[:2];image=bpy.data.images.new(name,width=w,height=h,alpha=False)
    image.colorspace_settings.name='sRGB' if colorspace=='srgb' else 'Non-Color'
    rgba=np.ones((h,w,4),dtype=np.float32);rgba[:,:,:3]=array
    image.pixels.foreach_set(rgba.ravel());image.filepath_raw=str(OUT/(name+'.png'));image.file_format='PNG';image.save();image.pack()
    tid=len(data['textures']);desc=copy.deepcopy(data['textures'][0])
    desc.update(id=tid,webPath='./assets/full-room/'+name+'.png',colorSpace=colorspace,repeat=[1,1],channel=0)
    data['textures'].append(desc);return tid,image

def material(name,color,roughness=.6,tex=None,bump=None,base_id=151):
    mid=len(data['materials']);d=copy.deepcopy(data['materials'][base_id]);d['id']=mid
    d['colors']['color']=rgb(color);d['textures']={};d['userData']={'surfaceFinish':name,'revision':'chair21'}
    d['props'].update(roughness=roughness,metalness=0,bumpScale=.00026,sheen=.15 if tex else 0)
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=(*rgb(color),1)
    nodes=mat.node_tree.nodes;bs=nodes.new('ShaderNodeBsdfPrincipled');output=nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bs.outputs['BSDF'],output.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*rgb(color),1);bs.inputs['Roughness'].default_value=roughness
    for key,pair in [('map',tex),('bumpMap',bump)]:
        if pair:
            tid,image=pair;d['textures'][key]=tid;t=nodes.new('ShaderNodeTexImage');t.image=image
            uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';mat.node_tree.links.new(uv.outputs[0],t.inputs[0])
            if key=='map':mat.node_tree.links.new(t.outputs['Color'],bs.inputs['Base Color'])
            else:
                b=nodes.new('ShaderNodeBump');b.inputs['Distance'].default_value=.00026
                mat.node_tree.links.new(t.outputs['Color'],b.inputs['Height']);mat.node_tree.links.new(b.outputs[0],bs.inputs['Normal'])
    mat['web_material_id']=mid;materials[mid]=mat;data['materials'].append(d);return mid

# Greige woven upholstery: a small physical repeat, not the coarse tablecloth.
rng=np.random.default_rng(21);yy,xx=np.mgrid[:512,:512]
warp=np.cos(xx*math.tau/8);weft=np.cos(yy*math.tau/8)
over=((xx//8+yy//8)%2)==0
height=.5+.21*np.where(over,warp,weft)+.035*rng.normal(size=(512,512))
melange=.045*rng.normal(size=(64,64)).repeat(8,0).repeat(8,1)
tone=np.clip(.96+.075*np.where(over,warp,weft)+melange+.015*rng.normal(size=(512,512)),.77,1.13)
fabricmap=texture('chair21-greige-weave',np.clip(tone[:,:,None]*np.array([.62,.594,.553]),0,1),'srgb')
fabricbump=texture('chair21-weave-height',np.repeat(np.clip(height,0,1)[:,:,None],3,axis=2),'')
fabric=material('Reference chair · greige woven upholstery','ffffff',.91,fabricmap,fabricbump)
piping=material('Reference chair · matching stitched piping','aaa296',.94)
woodtone=.96+.05*np.sin(xx*math.tau/32+1.1*np.sin(yy*math.tau/512))+.018*np.sin(xx*math.tau/7+yy*.019)
woodmap=texture('chair21-beech-grain',np.clip(woodtone[:,:,None]*np.array([.65,.51,.35]),0,1),'srgb')
wood=material('Reference chair · warm wood-colour tapered legs','ffffff',.49,woodmap)
rubber=material('Chair foot pads','35332f',.92)
orange=material('Upper racket · orange woven strings','db7626',.46)
black=material('Lower racket · black woven strings','202326',.49)

def seat(u,v,sign):
    env=max(0,(1-u*u)*(1-v*v))**.40
    x=.012+.230*u*math.sqrt(1-.10*v**10)
    z=.225*v*math.sqrt(1-.09*u**10)*(1+.035*u)
    wrinkle=.0008*math.sin(u*29+v*12)*(abs(v)**6+abs(u)**6)*env
    y=.457+sign*(.016+.025*env)-(.004*math.exp(-(u*u+v*v)*3) if sign>0 else 0)+wrinkle
    return x,y,z

def back(u,v,sign):
    env=max(0,(1-u*u)*(1-v*v))**.40
    y=.705+.255*v*math.sqrt(1-.09*u**8)
    z=.241*u*math.sqrt(1-.10*v**8)*(1-.028*v)
    x=-.188-(y-.47)*.20+.030*u*u+sign*(.018+.016*env)
    x+=.0007*math.sin(u*36+v*8)*abs(v)**5*env
    return x,y,z

seatmesh,seatborder=upholstered('chair-rounded-seat-cushion',seat,44,40,'seat')
attach(seatmesh,'blender-upholstered-chair-seat',fabric,nid=1281)
backmesh,backborder=upholstered('chair-reclined-curved-back',back,44,40,'back')
attach(backmesh,'blender-upholstered-chair-back',fabric,nid=1282)

def base(u,v,sign):
    env=max(0,(1-u*u)*(1-v*v))**.4
    return (.008+.235*u*math.sqrt(1-.10*v**8),.423+sign*(.015+.007*env),.243*v*math.sqrt(1-.10*u**8))
basemesh,_=upholstered('chair-upholstered-underseat',base,24,24,'seat')
attach(basemesh,'chair-upholstered-underseat',fabric)

armborders=[]
for side in [-1,1]:
    def arm(u,v,sign):
        t=(u+1)/2;q=(v+1)/2
        env=max(0,(1-u*u)*(1-v*v))**.45
        top=.492+.295*(1-t)**2.4;bottom=.421+.005*math.sin(t*math.pi)
        x=-.219+.463*t-.012*t**8*abs(v)**8+.006*(1-t)**8*abs(v)**8
        y=bottom+(top-bottom)*q
        z=side*(.218+.010*math.sin(t*math.pi)+.010*q+sign*(.012+.006*env))
        return x,y,z
    me,border=upholstered('chair-low-wraparound-arm',arm,40,28)
    attach(me,'chair-low-wraparound-arm-'+('left' if side<0 else 'right'),fabric)
    armborders.append(border)

for label,border in [('seat',seatborder),('back',backborder),('arm-left',armborders[0]),('arm-right',armborders[1])]:
    attach(tubes('chair-piping-'+label,[border+[border[0]]],.00115,6),'chair-tailored-piping-'+label,piping)

feet=[]
for nid,(x,z) in zip(range(1283,1287),[(-1,-1),(-1,1),(1,-1),(1,1)]):
    top=(x*.164,.436,z*.174);bottom=(x*.219,.019,z*.218)
    # Radius decreases toward the floor; the cap stays embedded in the seat.
    leg=tubes('chair-splayed-leg',[[top,bottom]],sides=24,radii=(.0195,.0125))
    attach(leg,'chair-tapered-wood-leg-'+str(nid-1282),wood,nid=nid)
    feet.append([(bottom[0],.0115,bottom[2]),(bottom[0],.020,bottom[2])])
attach(tubes('chair-floor-pads',feet,.0127,16),'chair-floor-pads',rubber)

# Keep the owner's black contoured cushion; recline it against the new back.
ob=objects[1287];W=Matrix.Translation(Vector((-.174,.6766589238196612,0))) @ Matrix.Rotation(math.pi/2,4,'Y') @ Matrix.Rotation(-.20,4,'X')
ob.matrix_local=C@W@C.inverted()
data['nodes'][1287]['matrix']=[W[r][c] for c in range(4) for r in range(4)];changed.add(1287)
objects[1280].name='photo-matched-upholstered-chair';data['nodes'][1280]['name']=objects[1280].name;changed.add(1280)
objects[1280]['web_name']=objects[1280].name

# True tubular mesh survives the scene exporter (the old LineSegments did not).
for nid,parent,mat,label in [(821,811,orange,'orange'),(834,824,black,'black')]:
    paths=[];rx=.131;ry=.185;cy=.470;r=.00073;px=.0146;py=.0175
    for i in range(16):
        x=(i-7.5)*px;dy=ry*math.sqrt(1-(x/rx)**2)
        paths.append([(x,cy-dy+2*dy*k/72,.001+r*(-1)**i*math.cos(math.pi*((-dy+2*dy*k/72)/py))) for k in range(73)])
    for j in range(-9,10):
        y=j*py;dx=rx*math.sqrt(1-(y/ry)**2)
        paths.append([(-dx+2*dx*k/60,cy+y,.001-r*(-1)**j*math.cos(math.pi*((-dx+2*dx*k/60)/px+7.5))) for k in range(61)])
    me=tubes('woven-racket-strings-'+label,paths,r,6)
    attach(me,'woven-racket-strings-'+label,mat,parent,nid,{'mainStrings':16,'crossStrings':19,'stringDiameterMm':1.46,'woven':True})

for i,n in enumerate(before):
    if i not in changed:assert data['nodes'][i]==n, f'Unexpected scene change {i}'
data['revision']='chair21b'
data['statistics']['meshes']=len(data['geometries'])
data['statistics']['triangles']=sum(g['index']['length']//3 for g in data['geometries'])
data['statistics']['chairRacketRefinement']={'racketsWithWovenMeshes':2,'stringsPerRacket':[16,19],'chairWraparoundArms':2,'sourcePhotos':['reference-window-new.jpg','reference-closet-new.jpg','codex-clipboard-01b5bd44-6cf2-4b1a-96f0-2e884afff16e.jpg']}
bpy.context.scene['web_revision']='chair21b'
bpy.context.scene['chair_racket_notes']='Photographic chair shell, low arms, greige weave, tapered legs and two real woven racket string meshes. Authored with official Blender Lab MCP.'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'))
(OUT/'geometry.bin').write_bytes(raw);(OUT/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9))
(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'chair21b','changedOriginalNodes':sorted(i for i in changed if i<len(before)),
        'newObjects':len(data['nodes'])-len(before),'newTextures':3,'wovenStringsPerRacket':35,'projectSaved':True,'binaryBytes':len(raw)}
