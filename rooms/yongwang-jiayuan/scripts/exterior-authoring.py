"""Shared Blender-only helpers for the exterior31 refinement chain.

Execute the stage scripts through Blender Lab MCP. Existing descriptors and
binary ranges are retained; new evaluated meshes are appended, never rebuilt
from the pre-refinement whole-room generator.
"""
import copy, gzip, json, math, os
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector

ROOT=Path(os.environ.get('BEIPIAO_ROOT',Path(__file__).resolve().parents[3]))
OUT=ROOT/'room-site/dist/assets/full-room'
SOURCE=ROOT/'rooms/yongwang-jiayuan/assets/full-room'
data=json.loads((OUT/'scene.json').read_text(encoding='utf8'))
before=copy.deepcopy(data);raw=bytearray((OUT/'geometry.bin').read_bytes())
obs={int(o['web_node_id']):o for o in bpy.data.objects if 'web_node_id' in o}
mats={int(m['web_material_id']):m for m in bpy.data.materials if 'web_material_id' in m}
collection=obs[192].users_collection[0]
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
changed=set();geometry_changed=set();images={}
def bp(p):return (p[0],-p[2],p[1])
def flat(m):return [m[r][c] for c in range(4) for r in range(4)]
def read(d):
    a=np.frombuffer(raw,dtype={'Float32Array':'<f4','Uint32Array':'<u4','Uint16Array':'<u2','Int16Array':'<i2'}[d['type']],count=d['length'],offset=d['offset']).copy()
    if 'itemSize' in d:a=a.reshape(-1,d['itemSize'])
    if 'decodeScale' in d:a=a*np.array(d['decodeScale'])+np.array(d['decodeOffset'])
    if d.get('normalized'):a=np.maximum(-1,a/32767)
    return a
def pack(values,size=None):
    a=np.asarray(values);integer=a.dtype.kind in 'iu';a=a.astype('<u4' if integer else '<f4').ravel();assert np.isfinite(a).all()
    while len(raw)%4:raw.append(0)
    d={'offset':len(raw),'length':len(a),'type':'Uint32Array' if integer else 'Float32Array'}
    if size:d['itemSize']=size
    raw.extend(a.tobytes());return d
def srgb(c):
    c=np.asarray(c,dtype=float);return np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
def texture(name,pixels,repeat=(1,1),color=True):
    h,w=pixels.shape[:2];rgba=np.ones((h,w,4),dtype=np.float32)
    rgb=np.repeat(pixels[:,:,None],3,axis=2) if pixels.ndim==2 else pixels[:,:,:3]
    # Byte-backed Blender images store encoded samples. Their sRGB tag performs
    # decoding when sampled; pre-decoding here would darken the PNG a second time.
    rgba[:,:,:3]=np.clip(rgb,0,1)
    has_alpha=pixels.ndim==3 and pixels.shape[2]==4
    if has_alpha:rgba[:,:,3]=pixels[:,:,3]
    im=bpy.data.images.new(name,width=w,height=h,alpha=has_alpha)
    im.colorspace_settings.name='sRGB' if color else 'Non-Color'
    im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(SOURCE/'textures'/f'{name}.png');im.file_format='PNG';im.save()
    (OUT/f'{name}.png').write_bytes(Path(im.filepath_raw).read_bytes())
    tid=len(data['textures']);d=copy.deepcopy(data['textures'][11]);d.update(id=tid,webPath=f'./assets/full-room/{name}.png',repeat=list(repeat),colorSpace='srgb' if color else '')
    data['textures'].append(d);images[tid]=im;return tid
def material(name,base,color=None,rough=None,textures=None,**props):
    mid=len(data['materials']);d=copy.deepcopy(data['materials'][base]);d['id']=mid
    d['userData']={'exteriorSurface':True,'surfaceFinish':name,'revision':'exterior31',**props.pop('metadata',{})}
    if color is not None:d['colors']['color']=list(srgb(color))
    if rough is not None:d['props']['roughness']=rough
    d['props'].update(props)
    if 'emissive' in d['colors']:d['colors']['emissive']=[0,0,0];d['props']['emissiveIntensity']=0
    if textures is not None:d['textures']=textures
    m=mats[base].copy();m.name=name;m['web_material_id']=mid;m['web_user_data']=json.dumps(d['userData'])
    m.use_nodes=True;ns=m.node_tree.nodes;ls=m.node_tree.links;ns.clear()
    bs=ns.new('ShaderNodeBsdfPrincipled');out=ns.new('ShaderNodeOutputMaterial');ls.new(bs.outputs['BSDF'],out.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*d['colors']['color'],1);bs.inputs['Roughness'].default_value=d['props'].get('roughness',.6);bs.inputs['Metallic'].default_value=d['props'].get('metalness',0)
    albedo=None
    for key,tid in d['textures'].items():
        im=images.get(tid)
        if im is None:
            im=bpy.data.images.load(str(ROOT/'room-site/dist'/data['textures'][tid]['webPath']),check_existing=True)
        tex=ns.new('ShaderNodeTexImage');tex.image=im;tex.extension='REPEAT'
        uv=ns.new('ShaderNodeUVMap');uv.uv_map='UVMap';mp=ns.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(*data['textures'][tid]['repeat'],1)
        ls.new(uv.outputs[0],mp.inputs[0]);ls.new(mp.outputs[0],tex.inputs[0])
        if key=='map':albedo=tex.outputs['Color']
        elif key=='roughnessMap':ls.new(tex.outputs['Color'],bs.inputs['Roughness'])
        elif key=='bumpMap':
            bump=ns.new('ShaderNodeBump');bump.inputs['Distance'].default_value=d['props'].get('bumpScale',.001);ls.new(tex.outputs['Color'],bump.inputs['Height']);ls.new(bump.outputs[0],bs.inputs['Normal'])
    if albedo:
        mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*d['colors']['color'],1);ls.new(albedo,mix.inputs[1]);albedo=mix.outputs[0]
    if d['props'].get('vertexColors'):
        attr=ns.new('ShaderNodeVertexColor');attr.layer_name='Color'
        if albedo:
            mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;ls.new(albedo,mix.inputs[1]);ls.new(attr.outputs['Color'],mix.inputs[2]);albedo=mix.outputs[0]
        else:albedo=attr.outputs['Color']
    if d['userData'].get('leafSurface'):
        tint=ns.new('ShaderNodeAttribute');tint.attribute_name='InstanceTint'
        mix=ns.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
        if albedo:ls.new(albedo,mix.inputs[1])
        ls.new(tint.outputs['Color'],mix.inputs[2]);albedo=mix.outputs[0]
    if albedo:ls.new(albedo,bs.inputs['Base Color'])
    mats[mid]=m;data['materials'].append(d);return mid
def set_material(nid,mid):
    o=obs[nid];d=data['nodes'][nid];d['material']=mid;changed.add(nid)
    if o.type=='MESH':
        if not o.material_slots:o.data.materials.append(mats[mid])
        o.material_slots[0].link='OBJECT';o.material_slots[0].material=mats[mid]
def activate(o):
    old=bpy.context.view_layer.objects.active
    if old and old!=o:old.select_set(False)
    o.select_set(True);bpy.context.view_layer.objects.active=o
def attach(me,name,mid,parent=192,nid=None):
    if nid is None:
        nid=len(data['nodes']);d=copy.deepcopy(before['nodes'][250]);data['nodes'].append(d)
        o=bpy.data.objects.new(name,me);collection.objects.link(o);obs[nid]=o;o.parent=obs[parent];o.matrix_local=Matrix.Identity(4)
    else:o=obs[nid];o.modifiers.clear();o.data=me;d=data['nodes'][nid]
    o.name=name;o['web_node_id']=nid;o['web_name']=name
    meta={'authoring':'Blender','blenderNode':nid,'revision':'exterior31'};o['web_user_data']=json.dumps(meta)
    # matrix_local depends on the evaluated parent transform (not just basis).
    # Without this refresh, translated parents produce a stale inverse offset.
    bpy.context.view_layer.update()
    d.update(id=nid,parent=parent,name=name,material=mid,type='Mesh',matrix=flat(C.inverted()@o.matrix_local@C),userData=meta)
    set_material(nid,mid);return o
def mesh(name,verts,faces,uvs=None,smooth=False):
    me=bpy.data.meshes.new(name);me.from_pydata([bp(p) for p in verts],[],faces);me.update()
    for f in me.polygons:f.use_smooth=smooth
    uv=me.uv_layers.new(name='UVMap')
    for l in me.loops:
        p=verts[l.vertex_index];uv.data[l.index].uv=uvs[l.vertex_index] if uvs else (p[0],p[1])
    return me
def export_mesh(me,source):
    me.calc_loop_triangles();p=[];n=[];uv=[];colors=[];attr=me.color_attributes.get('Color')
    for l in me.loops:
        v=me.vertices[l.vertex_index].co;normal=me.corner_normals[l.index].vector
        p.append((v.x,v.z,-v.y));n.append((normal.x,normal.z,-normal.y));uv.append(tuple(me.uv_layers.active.data[l.index].uv))
        if attr:colors.append(tuple(attr.data[l.index if attr.domain=='CORNER' else l.vertex_index].color[:3]))
    attrs={'position':pack(p,3),'normal':pack(n,3),'uv':pack(uv,2)}
    if attr:attrs['color']=pack(colors,3)
    gid=len(data['geometries']);data['geometries'].append({'id':gid,'attributes':attrs,'index':pack([i for t in me.loop_triangles for i in t.loops]),'groups':[],'userData':{'authoring':'Blender','sourceType':source,'revision':'exterior31'}})
    return gid
def export(o):
    nid=int(o['web_node_id']);data['nodes'][nid]['geometry']=export_mesh(o.data,o.name);geometry_changed.add(nid);changed.add(nid)
def box(name,center,size,mid,parent=192,bevel=.008):
    bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
    for v in bm.verts:v.co=Vector(bp([center[i]+size[i]*v.co[i] for i in range(3)]))
    me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();o=attach(me,'',mid,parent)
    if bevel:
        bm=bmesh.new();bm.from_mesh(o.data)
        bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(size)*.16),segments=2,affect='EDGES')
        bm.to_mesh(o.data);bm.free()
    uv=o.data.uv_layers.new(name='UVMap')
    for f in o.data.polygons:
        axis=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=axis]
        for li in f.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]]*.4,v[axes[1]]*.4)
    o['purpose']=name;export(o);return o
def save(revision,details):
    for i,n in enumerate(before['nodes']):
        if i not in changed:assert n==data['nodes'][i],('Unrelated node',i)
    assert before['materials']==data['materials'][:len(before['materials'])]
    assert before['textures']==data['textures'][:len(before['textures'])]
    assert before['refs']==data['refs']
    assert before['geometries']==data['geometries'][:len(before['geometries'])]
    data['revision']=revision;data['statistics']['exteriorRefinement']=details
    data['statistics']['meshes']=len(data['geometries']);data['statistics']['triangles']=sum(g['index']['length']//3 for g in data['geometries'])
    def json_number(value):
        if isinstance(value,np.generic):return value.item()
        raise TypeError(f'Unsupported export value: {type(value)}')
    manifest=json.dumps(data,ensure_ascii=False,separators=(',',':'),default=json_number)
    # Stage the complete export before updating the source. This also validates
    # JSON serialization and compression before touching any authoritative file.
    compressed=gzip.compress(raw,compresslevel=6,mtime=0)
    report=ROOT/'analysis/exterior-export-staged.json';report.parent.mkdir(exist_ok=True);report.write_text(manifest,encoding='utf8')
    for im in bpy.data.images:
        if im.source=='FILE' and im.filepath:
            absolute=Path(bpy.path.abspath(im.filepath))
            if absolute.is_relative_to(ROOT):im.filepath='//'+os.path.relpath(absolute,SOURCE).replace('\\','/')
    bpy.context.scene['web_revision']=revision;bpy.context.preferences.filepaths.save_version=0;bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'永旺家园-完整场景.blend'))
    (OUT/'geometry.bin').write_bytes(raw);(OUT/'geometry.bin.gz').write_bytes(compressed)
    # Publish the prepared manifest atomically; the HTTP server may be reading
    # the previous manifest while a model refinement is being saved.
    import time
    for attempt in range(6):
        try:os.replace(report,OUT/'scene.json');break
        except OSError:
            if attempt==5:raise
            time.sleep(.15)
    return {'revision':revision,'changedNodes':len(changed),'geometryChanged':sorted(geometry_changed),'details':details,'bytes':len(raw)}
