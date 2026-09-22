"""Build the authoritative editable room scene and its web mesh pack in Blender.

Historical base generator: execute through Blender Lab official MCP only.
Do not run over the refined current scene; see AGENTS.md and tools/README.md.
The reference capture retains approved dimensions, UVs, materials and pivots.
Blender rebuilds manufactured cylinders, refines hard edges, gives curtains
physical thickness, and owns every final visible mesh (including instances).
Lighting, water particles and screen-space effects remain real-time web effects.
"""
import bpy, bmesh, math, json, pathlib, gzip, shutil, struct, time, copy
import numpy as np
from mathutils import Matrix, Vector

SITE=(pathlib.Path(__file__).resolve().parents[3] / 'room-site')
SOURCE=SITE.parent/'rooms/yongwang-jiayuan/assets/full-room'
OUT=SITE/'dist/assets/full-room'
OUT.mkdir(parents=True,exist_ok=True)
DATA=json.loads((SOURCE/'source-scene.json').read_text())
for texture in DATA['textures']:
    texture['file']=str(SITE.parent / texture['file'])
RAW=(SOURCE/'source-geometry.bin').read_bytes()
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
CI=C.inverted()
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
scene['source']='Full Blender room; photo-proportional dimensions, not a survey'
scene['web_coordinates']='x, y-up, z toward room; Blender x,-z,y'
scene['revision']='blender18'
library=bpy.data.collections.new('00 · Editable mesh library');scene.collection.children.link(library)
assembly=bpy.data.collections.new('01 · Room and courtyard');scene.collection.children.link(assembly)
library.hide_render=True;library.hide_viewport=True

def read(a):
    types={'Float32Array':'<f4','Uint32Array':'<u4','Uint16Array':'<u2'}
    return np.frombuffer(RAW,dtype=types[a['type']],count=a['length'],offset=a['offset']).copy()
def convert(p):
    result=np.empty_like(p);result[:,0]=p[:,0];result[:,1]=-p[:,2];result[:,2]=p[:,1];return result
def inverse(p):
    result=np.empty_like(p);result[:,0]=p[:,0];result[:,1]=p[:,2];result[:,2]=-p[:,1];return result
def world_matrix(m):
    return C@Matrix(np.array(m).reshape((4,4),order='F').tolist())@CI
def mat_bsdf(m):
    m.use_nodes=True
    bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bs is None:
        bs=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
        output=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or m.node_tree.nodes.new('ShaderNodeOutputMaterial')
        output.is_active_output=True
        m.node_tree.links.new(bs.outputs[0],output.inputs[0])
    return bs

# The approved layout stays fixed. Fine-scale material response is authored here,
# shared by the Blender project and web materials, not baked as fake painted light.
def detail_texture(name,values,repeat):
    size=values.shape[0];rgba=np.ones((size,size,4),dtype=np.float32);rgba[:,:,:3]=values[:,:,None]
    image=bpy.data.images.new(name,width=size,height=size,alpha=True,float_buffer=False)
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(rgba.ravel())
    file=SOURCE/'textures'/f'{name}.png';image.filepath_raw=str(file);image.file_format='PNG';image.save()
    t=copy.deepcopy(DATA['textures'][0]);t.update(id=len(DATA['textures']),file=str(file),webPath=None,colorSpace='',repeat=repeat,offset=[0,0],channel=0,wrapS=1000,wrapT=1000)
    DATA['textures'].append(t);return t['id']
yy,xx=np.mgrid[0:256,0:256]/256
rng=np.random.default_rng(18);noise=rng.random((256,256)).astype(np.float32)
weave=.50+.19*np.sin(xx*math.tau*8)*np.cos(yy*math.tau*8)+.026*np.sin(xx*math.tau*64)+.021*np.sin(yy*math.tau*64)
fabric_height=detail_texture('cotton-thread-relief',weave,[24,24])
fine_height=detail_texture('fine-satin-surface',.48+.07*noise+.014*np.sin(xx*math.tau*13),[12,12])
fine_rough=detail_texture('subtle-surface-roughness',.85+.12*noise,[8,8])
wood_texture=next(t for t in DATA['textures'] if t['file'].endswith('wood.jpg'))
wood_bump=copy.deepcopy(wood_texture);wood_bump.update(id=len(DATA['textures']),colorSpace='');DATA['textures'].append(wood_bump)
users_by_material={}
def ancestors(n):
    parts=[]
    while n['parent']>=0:
        parts.append(n['name']);n=DATA['nodes'][n['parent']]
    return '/'.join(parts).lower()
for n in DATA['nodes']:
    if 'material' in n:
        for mid in n['material'] if isinstance(n['material'],list) else [n['material']]:users_by_material.setdefault(mid,[]).append(n)
material_refinements=0
bed_wood_id=next(n['material'] for n in DATA['nodes'] if n['parent']==DATA['refs']['bed'] and 'material' in n)
curtain_material_ids={DATA['nodes'][i]['material'] for i in DATA['refs']['curtainPanels']}
for m in DATA['materials']:
    if m['type'] not in ['MeshStandardMaterial','MeshPhysicalMaterial'] or (m['props'].get('transparent') and m['id'] not in curtain_material_ids):continue
    paths='/'.join(ancestors(n) for n in users_by_material.get(m['id'],[]))
    texmap=DATA['textures'][m['textures']['map']]['file'] if 'map' in m['textures'] else ''
    rough=m['props'].get('roughness',.7);metal=m['props'].get('metalness',0)
    cotton=('woven-cloth' in texmap or m['id'] in curtain_material_ids or any(s in paths for s in ['pillow','cotton','lumbar','upholstered','soft-woven-desk-cover','duvet','black_la_cap'])) and rough>.7
    ceramic=any(s in paths for s in ['porcelain-toilet','hollow-ceramic-mug','rounded-porcelain-mug','concave-washbasin']) and metal<.1 and rough<.4
    if cotton:
        m['type']='MeshPhysicalMaterial';m['props'].update(sheen=.22,sheenRoughness=.86)
        m['colors']['sheenColor']=[.55,.52,.47]
        if 'bumpMap' not in m['textures']:m['textures']['bumpMap']=fabric_height;m['props']['bumpScale']=.00055
        m['userData']['surfaceFinish']='woven cotton micro-relief';material_refinements+=1
    elif 'wood.jpg' in texmap or m['id']==bed_wood_id:
        m['textures']['bumpMap']=wood_bump['id'];m['props']['bumpScale']=.0006;m['textures']['roughnessMap']=fine_rough
        m['type']='MeshPhysicalMaterial';m['props'].update(clearcoat=.12,clearcoatRoughness=.4)
        m['userData']['surfaceFinish']='satin wood grain';material_refinements+=1
    elif ceramic:
        m['type']='MeshPhysicalMaterial';m['props'].update(clearcoat=.32,clearcoatRoughness=.16,roughness=.24)
        m['textures']['bumpMap']=fine_height;m['props']['bumpScale']=.000035;m['textures']['roughnessMap']=fine_rough
        m['userData']['surfaceFinish']='glazed ceramic';material_refinements+=1
    elif metal<.2 and .30<=rough<=.68 and 'map' not in m['textures']:
        m['textures']['bumpMap']=fine_height;m['textures']['roughnessMap']=fine_rough;m['props']['bumpScale']=.00010
        m['userData']['surfaceFinish']='fine satin manufactured finish';material_refinements+=1

images={};webtextures=[]
for t in DATA['textures']:
    image=bpy.data.images.load(t['file'],check_existing=True)
    desired='sRGB' if t['colorSpace']=='srgb' else 'Non-Color'
    if image.colorspace_settings.name!=desired and image.users: image=image.copy()
    image.colorspace_settings.name=desired
    image.pack();images[t['id']]=image
    item=dict(t);item.pop('file')
    if not item['webPath']:
        name='texture-'+str(t['id'])+'.png';shutil.copyfile(t['file'],OUT/name)
        item['webPath']='./assets/full-room/'+name
    webtextures.append(item)
materials=[]
for desc in DATA['materials']:
    m=bpy.data.materials.new(f"Material {desc['id']:03d}");bs=mat_bsdf(m)
    color=desc['colors'].get('color',[1,1,1]);alpha=desc['props'].get('opacity',1)
    m.diffuse_color=(*color,alpha);bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=desc['props'].get('roughness',.6)
    bs.inputs['Metallic'].default_value=desc['props'].get('metalness',0)
    bs.inputs['Alpha'].default_value=alpha
    if 'emissive' in desc['colors']:
        bs.inputs['Emission Color'].default_value=(*desc['colors']['emissive'],1)
        bs.inputs['Emission Strength'].default_value=desc['props'].get('emissiveIntensity',0)
    bs.inputs['Coat Weight'].default_value=desc['props'].get('clearcoat',0)
    bs.inputs['Coat Roughness'].default_value=desc['props'].get('clearcoatRoughness',.2)
    bs.inputs['Sheen Weight'].default_value=desc['props'].get('sheen',0)
    for key,target in [('map','Base Color'),('roughnessMap','Roughness'),('metalnessMap','Metallic')]:
        if key not in desc['textures']:continue
        t=DATA['textures'][desc['textures'][key]]
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images[t['id']]
        uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
        mapping=m.node_tree.nodes.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value=(*t['repeat'],1)
        mapping.inputs['Location'].default_value=(*t['offset'],0)
        m.node_tree.links.new(uv.outputs[0],mapping.inputs['Vector'])
        m.node_tree.links.new(mapping.outputs[0],tex.inputs['Vector'])
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs[target])
    if 'bumpMap' in desc['textures']:
        t=DATA['textures'][desc['textures']['bumpMap']];tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images[t['id']]
        uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';mapping=m.node_tree.nodes.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=(*t['repeat'],1)
        m.node_tree.links.new(uv.outputs[0],mapping.inputs[0]);m.node_tree.links.new(mapping.outputs[0],tex.inputs[0])
        bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=desc['props'].get('bumpScale',.0001)
        m.node_tree.links.new(tex.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    m['web_material_id']=desc['id'];materials.append(m)

geometry_materials={}
for n in DATA['nodes']:
    if 'geometry' in n:geometry_materials.setdefault(n['geometry'],n['material'])
geometry_nodes={}
for n in DATA['nodes']:
    if 'geometry' in n:geometry_nodes.setdefault(n['geometry'],[]).append(n)

def import_mesh(desc):
    a=desc['attributes'];p=read(a['position']).reshape(-1,3)
    indices=read(desc['index']).astype(np.int32) if desc.get('index') else np.arange(len(p),dtype=np.int32)
    me=bpy.data.meshes.new(f"Mesh {desc['id']:04d} · {desc['type']}")
    me.vertices.add(len(p));me.vertices.foreach_set('co',convert(p).ravel())
    me.loops.add(len(indices));me.loops.foreach_set('vertex_index',indices)
    me.polygons.add(len(indices)//3);me.polygons.foreach_set('loop_start',np.arange(0,len(indices),3,dtype=np.int32));me.polygons.foreach_set('loop_total',np.full(len(indices)//3,3,dtype=np.int32))
    me.update(calc_edges=True)
    for uv in ['uv','uv1','uv2']:
        if uv in a:
            layer=me.uv_layers.new(name='UVMap' if uv=='uv' else uv)
            layer.data.foreach_set('uv',read(a[uv]).reshape(-1,2)[indices].ravel())
    if 'color' in a:
        values=read(a['color']).reshape(-1,a['color']['itemSize'])
        rgba=np.ones((len(p),4),dtype=np.float32);rgba[:,:values.shape[1]]=values
        layer=me.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='POINT');layer.data.foreach_set('color',rgba.ravel())
    for group in desc['groups']:
        for i in range(group['start']//3,(group['start']+group['count'])//3):me.polygons[i].material_index=group['materialIndex']
    me.validate(verbose=False,clean_customdata=False)
    me.update(calc_edges=True)
    if 'normal' in a:
        for face in me.polygons:face.use_smooth=True
        me.normals_split_custom_set_from_vertices(convert(read(a['normal']).reshape(-1,3)).tolist())
    return me

def cylinder_mesh(desc):
    """Native manufactured surface with round shoulders; no polygonal end silhouette."""
    p=desc['parameters'];rt=p['radiusTop'];rb=p['radiusBottom'];h=p['height']
    segments=max(p.get('radialSegments',24),32 if max(rt,rb)>.03 else 24)
    bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=not p.get('openEnded',False),cap_tris=False,segments=segments,radius1=rb,radius2=rt,depth=h)
    me=bpy.data.meshes.new(f"Turned surface {desc['id']:04d}");bm.to_mesh(me);bm.free()
    for face in me.polygons:face.use_smooth=len(face.vertices)==4
    uv=me.uv_layers.new(name='UVMap')
    for face in me.polygons:
        for i in face.loop_indices:
            co=me.vertices[me.loops[i].vertex_index].co
            uv.data[i].uv=((math.atan2(co.y,co.x)/math.tau)%1,co.z/max(h,.000001)+.5) if len(face.vertices)==4 else (co.x/max(rt,rb,.000001)/2+.5,co.y/max(rt,rb,.000001)/2+.5)
    return me

blob=[];offset=0;packed=[];prototypes={};stats={'beveled':0,'rebuiltCylinders':0,'solidified':0,'meshes':0,'triangles':0}
def pack_array(array,item_size=None):
    global offset
    dtype='<f4' if array.dtype.kind=='f' else '<i2' if array.dtype==np.int16 else '<u2' if array.dtype==np.uint16 else '<u4'
    array=np.asarray(array,dtype=dtype).ravel()
    names={'<f4':'Float32Array','<i2':'Int16Array','<u2':'Uint16Array','<u4':'Uint32Array'}
    raw=array.tobytes();info={'offset':offset,'length':len(array),'type':names[dtype]}
    if item_size:info['itemSize']=item_size
    blob.append(raw);offset+=len(raw)
    pad=(4-offset%4)%4
    if pad:blob.append(bytes(pad));offset+=pad
    return info
def pack_quantized(values,item_size):
    low=values.min(axis=0);span=values.max(axis=0)-low;step=np.where(span>1e-10,span/65535,1)
    quantized=np.rint((values-low)/step).clip(0,65535).astype(np.uint16)
    desc=pack_array(quantized,item_size);desc['decodeOffset']=low.tolist();desc['decodeScale']=step.tolist();return desc
def export_geometry(me,desc):
    me.calc_loop_triangles()
    coords=np.empty(len(me.vertices)*3,dtype=np.float32);me.vertices.foreach_get('co',coords);coords=inverse(coords.reshape(-1,3))
    loopvertices=np.empty(len(me.loops),dtype=np.int32);me.loops.foreach_get('vertex_index',loopvertices)
    normals=np.empty(len(me.corner_normals)*3,dtype=np.float32);me.corner_normals.foreach_get('vector',normals);normals=inverse(normals.reshape(-1,3))
    uvs={}
    for layer in me.uv_layers:
        values=np.empty(len(me.loops)*2,dtype=np.float32);layer.data.foreach_get('uv',values)
        uvs['uv' if layer.name=='UVMap' else layer.name]=values.reshape(-1,2)
    cols=None
    if 'Color' in me.color_attributes:
        layer=me.color_attributes['Color'];values=np.empty(len(layer.data)*4,dtype=np.float32);layer.data.foreach_get('color',values);cols=values.reshape(-1,4)
        if layer.domain=='POINT':cols=cols[loopvertices]
    # Compact loop vertices while retaining UV seams and hard edge normals.
    parts=[coords[loopvertices],normals]+list(uvs.values())
    if cols is not None:parts.append(cols[:,:3])
    joined=np.hstack(parts).astype(np.float32)
    unique,inverse_indices=np.unique(joined,axis=0,return_inverse=True)
    triangles=np.empty(len(me.loop_triangles)*3,dtype=np.int32);me.loop_triangles.foreach_get('loops',triangles)
    indices=inverse_indices[triangles].astype(np.uint32)
    normal=pack_array(np.rint(np.clip(unique[:,3:6],-1,1)*32767).astype(np.int16),3);normal['normalized']=True
    at={'position':pack_quantized(unique[:,:3],3),'normal':normal};cursor=6
    for name in uvs:at[name]=pack_quantized(unique[:,cursor:cursor+2],2);cursor+=2
    if cols is not None:at['color']=pack_array(unique[:,cursor:cursor+3],3)
    groups=[]
    if len(me.materials)>1:
        previous=None
        for i,tri in enumerate(me.loop_triangles):
            value=tri.material_index
            if value!=previous:groups.append({'start':i*3,'count':0,'materialIndex':value});previous=value
            groups[-1]['count']+=3
    packed.append({'id':desc['id'],'attributes':at,'index':pack_array(indices.astype(np.uint16) if len(unique)<65536 else indices),'groups':groups,'userData':{'authoring':'Blender','sourceType':desc['type']}})
    stats['triangles']+=len(me.loop_triangles);stats['meshes']+=1

for desc in DATA['geometries']:
    id=desc['id'];users=geometry_nodes[id];p=desc['parameters'];kind=desc['type']
    material_ids=geometry_materials[id];material_ids=material_ids if isinstance(material_ids,list) else [material_ids]
    textured=any('map' in DATA['materials'][m]['textures'] for m in material_ids)
    # Curved decals, existing sculpted Blender assets and UV-bearing cloth retain
    # their approved shapes. All final meshes are evaluated and exported here.
    rebuild=kind=='CylinderGeometry' and not textured and p.get('thetaLength',math.tau)>6.28
    me=cylinder_mesh(desc) if rebuild else import_mesh(desc)
    if rebuild:stats['rebuiltCylinders']+=1
    for mid in material_ids:me.materials.append(materials[mid])
    o=bpy.data.objects.new(f"Asset {id:04d} · {next((n['name'] for n in users if n['name']),kind)}",me);library.objects.link(o)
    bevel=0
    if kind=='BoxGeometry' and max(p.get('width',1),p.get('height',1),p.get('depth',1))<2.4:
        dims=[p['width'],p['height'],p['depth']]
        if min(dims)>.012:
            bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=.000001);bmesh.ops.dissolve_limit(bm,angle_limit=.0001,verts=bm.verts,edges=bm.edges);bm.to_mesh(me);bm.free()
            bevel=min(.002,min(dims)*.07)
    elif rebuild and not p.get('openEnded',False):bevel=min(.0012,min(p['radiusTop'],p['radiusBottom'])*.065,p['height']*.06)
    if bevel>.00001:
        mod=o.modifiers.new('Manufactured edge radius','BEVEL');mod.width=bevel;mod.segments=3;mod.limit_method='ANGLE';mod.angle_limit=.52
        mod.harden_normals=True;stats['beveled']+=1
        normal=o.modifiers.new('Weighted surface normals','WEIGHTED_NORMAL');normal.keep_sharp=True
    # Full curtain cloth now has a thin closed edge, instead of an infinitely thin plane.
    if kind=='PlaneGeometry' and any(n['id'] in DATA['refs']['curtainPanels'] for n in users):
        mod=o.modifiers.new('Woven cloth thickness','SOLIDIFY');mod.thickness=.0012;mod.offset=0;stats['solidified']+=1
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();evaluated=o.evaluated_get(deps)
    final=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
    final.name=f"Blender final {id:04d}";prototypes[id]=final
    export_geometry(final,desc)
    if id%100==0:print(f'BLENDER_MODEL {id}/{len(DATA["geometries"])}',flush=True)

def make_instances(obj,node,mesh):
    matrices=read(node['instanceMatrix']).reshape(-1,16)
    positions=[];rotations=[];scales=[]
    for flat in matrices:
        position,rotation,scale=world_matrix(flat).decompose();positions.append(position);rotations.append(rotation.to_euler());scales.append(scale)
    points=bpy.data.meshes.new('Instance placements '+str(node['id']));points.from_pydata(positions,[],[])
    for name,values in [('rotation',rotations),('scale',scales)]:
        layer=points.attributes.new(name,'FLOAT_VECTOR','POINT');layer.data.foreach_set('vector',np.asarray(values,dtype=np.float32).ravel())
    obj.data=points
    proto=bpy.data.objects.new('Instance prototype '+str(node['id']),mesh);library.objects.link(proto)
    mids=node['material'] if isinstance(node['material'],list) else [node['material']]
    for j,mid in enumerate(mids):
        if j<len(proto.material_slots):proto.material_slots[j].link='OBJECT';proto.material_slots[j].material=materials[mid]
    group=bpy.data.node_groups.new('Shared instances '+str(node['id']),'GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=group.nodes;links=group.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput')
    source=nodes.new('GeometryNodeObjectInfo');source.inputs['Object'].default_value=proto
    inst=nodes.new('GeometryNodeInstanceOnPoints');links.new(inp.outputs['Geometry'],inst.inputs['Points']);links.new(source.outputs['Geometry'],inst.inputs['Instance'])
    for name in ['rotation','scale']:
        attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='FLOAT_VECTOR';attr.inputs['Name'].default_value=name;links.new(attr.outputs['Attribute'],inst.inputs[name.capitalize()])
    links.new(inst.outputs['Instances'],out.inputs['Geometry']);mod=obj.modifiers.new('GPU-friendly shared instances','NODES');mod.node_group=group

objects={};webnodes=[]
for node in DATA['nodes']:
    id=node['id'];label=node['name'] or f"{node['type']} {id:04d}"
    obj=bpy.data.objects.new(label,prototypes[node['geometry']] if 'geometry' in node else None);assembly.objects.link(obj);objects[id]=obj
    obj['web_node_id']=id;obj['web_name']=node['name'];obj['web_user_data']=json.dumps(node['userData'],ensure_ascii=False)
    if node['parent']>=0:obj.parent=objects[node['parent']]
    obj.matrix_local=world_matrix(node['matrix'])
    obj.hide_render=not node['visible']
    if 'material' in node:
        mids=node['material'] if isinstance(node['material'],list) else [node['material']]
        for j,mid in enumerate(mids):
            if j<len(obj.material_slots):obj.material_slots[j].link='OBJECT';obj.material_slots[j].material=materials[mid]
        # The browser uses separate invisible shadow proxies. Hide those in Blender
        # while retaining their geometry and metadata in the editable project.
        if all(DATA['materials'][mid]['props'].get('colorWrite',True)==False for mid in mids):obj.hide_render=True;obj.hide_set(True)
    item=dict(node);item['userData']={**node['userData'],'authoring':'Blender','blenderNode':id}
    for key in ['instanceMatrix','instanceColor']:
        if key in node:item[key]=pack_array(read(node[key]))
    if node['type']=='InstancedMesh':make_instances(obj,node,prototypes[node['geometry']])
    webnodes.append(item)

# An immediately usable material-preview scene; the web retains its verified warm
# afternoon lighting. Camera and lighting are not exported as new web geometry.
world=bpy.data.worlds.new('Warm afternoon world');scene.world=world;world.use_nodes=True
background=world.node_tree.nodes.get('Background') or world.node_tree.nodes.new('ShaderNodeBackground')
world_output=world.node_tree.nodes.get('World Output') or world.node_tree.nodes.new('ShaderNodeOutputWorld')
world.node_tree.links.new(background.outputs[0],world_output.inputs[0]);background.inputs[0].default_value=(.70,.76,.81,1);background.inputs[1].default_value=.45
light=bpy.data.lights.new('Afternoon sun','SUN');light.energy=2.5;light.color=(1,.83,.59);light.angle=.12
sun=bpy.data.objects.new('Afternoon sun',light);scene.collection.objects.link(sun);sun.rotation_euler=Vector((-2.6,9,-5.7)).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('Room preview');camera=bpy.data.objects.new('Room preview',camera_data);scene.collection.objects.link(camera)
camera.location=C@Vector((.83,1.48,1.66));target=C@Vector((-.15,1.25,-1.30));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.lens=22;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1280;scene.render.resolution_y=900;scene.render.resolution_percentage=100
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.clip_end=200
stats['refinedMaterials']=material_refinements
scene['asset_statistics']=json.dumps(stats)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'永旺家园-完整场景.blend'))
manifest={'format':'blender-room-pack-1','revision':'blender18','binary':'./assets/full-room/geometry.bin','compressedBinary':'./assets/full-room/geometry.bin.gz','nodes':webnodes,'geometries':packed,'materials':DATA['materials'],'textures':webtextures,'refs':DATA['refs'],'statistics':stats}
raw=b''.join(blob);(OUT/'geometry.bin').write_bytes(raw);(OUT/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9))
(OUT/'scene.json').write_text(json.dumps(manifest,separators=(',',':')),encoding='utf8')
(SOURCE/'build-report.json').write_text(json.dumps({**stats,'bytes':len(raw),'compressedBytes':(OUT/'geometry.bin.gz').stat().st_size},indent=2))
print('FULL_ROOM_READY '+json.dumps({**stats,'bytes':len(raw),'compressedBytes':(OUT/'geometry.bin.gz').stat().st_size}),flush=True)
