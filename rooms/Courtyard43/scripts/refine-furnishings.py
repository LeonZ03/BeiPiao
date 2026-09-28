"""Third finish pass. Execute only through official Blender Lab MCP.

Run on architecture07, furniture05, props01, then interior06. Approved room
anchors and textile06 geometry stay unchanged. P03/P04 guide visible finishes;
small dimensions, concealed bag interior and unreadable labels remain inferred.
"""
from pathlib import Path
import bpy, bmesh, numpy as np, math, json, hashlib, struct, zlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
kind=scene.get('component')
full=scene.get('stage')=='interior' and kind not in ('architecture','furniture','props')
parents={'architecture':'architecture07','furniture':'courtyard43-furniture05','props':'courtyard43-props01'}
assert scene.get('web_revision')=='courtyard43-interior06' if full else scene.get('component_revision')==parents[kind]
bpy.context.preferences.filepaths.save_version=0
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
assert source_hash=='d1659edad574ee6d11ad27f594cdecb28001a3014c044a280274c0a0441a3a16'
bp=lambda p:Vector((p[0],-p[2],p[1]))
web=lambda p:Vector((p[0],p[2],-p[1]))
targets=set()

def digest(o):
    h=hashlib.sha256(repr((tuple(tuple(r) for r in o.matrix_world),o.parent.name if o.parent else '',dict(o.items()))).encode())
    if o.type=='MESH':
        h.update(repr(([tuple(v.co) for v in o.data.vertices],[(tuple(p.vertices),p.material_index) for p in o.data.polygons],[(u.name,[tuple(d.uv) for d in u.data]) for u in o.data.uv_layers],[m.name for m in o.data.materials])).encode())
    return h.hexdigest()
before={o.name:digest(o) for o in scene.objects}

def shader(m):
    output=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output)
    return output.inputs['Surface'].links[0].from_node

def material(name,color,rough=.6,metal=0,sheen=0,alpha=1):
    m=bpy.data.materials.new('C43_'+name+'_07');m.use_nodes=True
    b=shader(m);b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal;b.inputs['Sheen Weight'].default_value=sheen
    b.inputs['Sheen Tint'].default_value=(.42,.44,.46,1);b.inputs['Sheen Roughness'].default_value=.75
    b.inputs['Alpha'].default_value=alpha
    if alpha<1:m['web_props']=json.dumps({'transparent':True,'opacity':alpha,'depthWrite':False,'side':0})
    return m

def image(name,rgb,folder,color=True):
    rgb=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    if rgb.ndim==2:rgb=np.repeat(rgb[:,:,None],3,axis=2)
    h,w=rgb.shape[:2]
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))
    if color:data+=chunk(b'sRGB',b'\0')
    data+=chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in rgb),6))+chunk(b'IEND',b'')
    path=ROOM/f'assets/{folder}/textures/{name}-07.png';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='sRGB' if color else 'Non-Color'
    return im

def tex(m,im,socket,scale=1):
    tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
    uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
    mapping=m.node_tree.nodes.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=(scale,scale,1)
    m.node_tree.links.new(uv.outputs[0],mapping.inputs[0]);m.node_tree.links.new(mapping.outputs[0],tx.inputs['Vector'])
    m.node_tree.links.new(tx.outputs['Color'],socket)
    return tx

def bump(m,im,scale=1,strength=.00015):
    b=m.node_tree.nodes.new('ShaderNodeBump');b.inputs['Distance'].default_value=strength;b.inputs['Strength'].default_value=.45
    tex(m,im,b.inputs['Height'],scale);m.node_tree.links.new(b.outputs[0],shader(m).inputs['Normal'])

def assign(o,mats):
    targets.add(o.name);ids=[p.material_index for p in o.data.polygons];o.data=o.data.copy();o.data.materials.clear()
    for m in mats:o.data.materials.append(m)
    for p,i in zip(o.data.polygons,ids):p.material_index=min(i,len(mats)-1)

def replace(name,verts,faces,mats,uv=None,smooth=True):
    bpy.context.view_layer.update()
    o=bpy.data.objects.get(name)
    if not o:
        o=bpy.data.objects.new(name,bpy.data.meshes.new(name));bpy.data.collections['C43_Props'].objects.link(o)
        o['web_tags']=json.dumps({'noCollision':True})
    targets.add(name);inv=o.matrix_world.inverted();me=bpy.data.meshes.new(name+'_finish07')
    me.from_pydata([inv@bp(v) for v in verts],[],faces);me.update()
    for m in mats:me.materials.append(m)
    layer=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth=smooth
        for li in p.loop_indices:
            vi=me.loops[li].vertex_index;layer.data[li].uv=uv[vi] if uv else (verts[vi][0],verts[vi][1])
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    me.update();o.modifiers.clear();o.data=me
    return o

def solid(o,thickness):
    mod=o.modifiers.new('Physical thin shell','SOLIDIFY');mod.thickness=thickness;mod.offset=-1

def settle_bag(o):
    # Broad diagonals run from the gathered mouth into the loaded body. The
    # mouth and bottom remain pinned so the sewn strap connections do not move.
    for v in o.data.vertices:
        p=web(o.matrix_world@v.co);t=max(0,min(1,(p.y-1.105)/.318))
        envelope=math.sin(math.pi*t)**1.7
        crease=-.020*math.exp(-((p.x-(1.89+.14*t))/.025)**2)+.013*math.exp(-((p.x-(2.045-.10*t))/.033)**2)
        p.z+=math.copysign(1,p.z-1.446)*crease*envelope*min(1,abs(p.z-1.446)/.035)
        v.co=o.matrix_world.inverted()@bp(p)
    o.data.update()

def tube(name,points,radius,mat):
    vv=[];ff=[];n=8
    for i,p in enumerate(points):
        p=Vector(p);t=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
        axis=Vector((0,0,1)) if abs(t.z)<.9 else Vector((1,0,0));a=t.cross(axis).normalized();b=t.cross(a)
        vv.extend(tuple(p+radius*(a*math.cos(k*math.tau/n)+b*math.sin(k*math.tau/n))) for k in range(n))
    for i in range(len(points)-1):
        for k in range(n):ff.append((i*n+k,i*n+(k+1)%n,(i+1)*n+(k+1)%n,(i+1)*n+k))
    ff.extend([tuple(reversed(range(n))),tuple((len(points)-1)*n+k for k in range(n))])
    return replace(name,vv,ff,[mat])

def lathe(name,center,profile,mat,n=96):
    vv=[];ff=[];uv=[]
    for j,(r,h) in enumerate(profile):
        for i in range(n):
            a=i*math.tau/n;vv.append((center[0]+r*math.cos(a),center[1]+h,center[2]+r*math.sin(a)));uv.append((i/n,j/(len(profile)-1)))
    for j in range(len(profile)-1):
        for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    o=replace(name,vv,ff,[mat],uv)
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-9)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();return o

if full or kind=='architecture':
    o=bpy.data.objects['C43_Floor_RedBrown_Boards'];targets.add(o.name)
    m=o.data.materials[0].copy();m.name='C43_Timber_satin_07';assign(o,[m]);b=shader(m)
    rng=np.random.default_rng(4307);y,x=np.mgrid[0:2048,0:1024]/np.array([2048,1024])[:,None,None]
    warp=x+.004*np.sin(y*math.tau*2+x*6)+.0015*np.sin(y*math.tau*7+x*19)
    grain=np.zeros_like(x)
    for freq in [11,23,47,89,137,211]:
        grain+=rng.uniform(.001,.0028)*np.sin(warp*math.tau*freq+rng.uniform(0,6)+.35*np.sin(y*math.tau*3))
    broad=.010*np.sin(warp*math.tau*4+.7*np.sin(y*math.tau))+.006*np.sin(warp*math.tau*9+1.8)
    grain+=broad+rng.normal(0,.0012,x.shape)
    # Encoded albedo stays at the accepted dark red-brown average. Broad grain
    # and subdued pores replace evenly repeated high-contrast striping.
    rgb=np.stack([.410+grain,.242+grain*.64,.175+grain*.45],axis=-1)
    tx=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.outputs['Color'].is_linked and n.outputs['Color'].links[0].to_socket==b.inputs['Base Color'])
    tx.image=image('timber-grain',rgb,'architecture')
    rough=.39+.025*np.sin(warp*math.tau*11)+.008*np.sin(y*math.tau*5)
    tex(m,image('timber-satin',rough,'architecture',False),b.inputs['Roughness'])
    normal=next(n for n in m.node_tree.nodes if n.type=='NORMAL_MAP');normal.inputs['Strength'].default_value=.14
    nm=normal.inputs['Color'].links[0].from_node
    gy,gx=np.gradient(grain);nm.image=image('timber-pores',np.stack([.5-gx*.7,.5-gy*.7,np.ones_like(x)],axis=-1),'architecture',False)
    b.inputs['Coat Weight'].default_value=.08;b.inputs['Coat Roughness'].default_value=.38

if full or kind=='furniture':
    y,x=np.mgrid[0:256,0:256]/256
    rng=np.random.default_rng(4317);micro=rng.normal(0,.008,x.shape)
    rough=image('white-laminate-satin',.43+micro,'furniture',False)
    powder=image('white-powdercoat-micro',.5+rng.normal(0,.035,x.shape),'furniture',False)
    replacements={}
    for name in ['C43_WarmWhiteLaminate','C43_WhitePowderCoatedSteel']:
        old=bpy.data.materials.get(name)
        if not old:continue
        m=old.copy();m.name=name+'_07';b=shader(m);b.inputs['Metallic'].default_value=0
        if 'Laminate' in name:
            b.inputs['Coat Weight'].default_value=.10;b.inputs['Coat Roughness'].default_value=.35;tex(m,rough,b.inputs['Roughness'])
        else:
            b.inputs['Roughness'].default_value=.36;bump(m,powder,12,.000035)
        replacements[old]=m
    for o in list(scene.objects):
        if o.type=='MESH' and any(m in replacements for m in o.data.materials):assign(o,[replacements.get(m,m) for m in o.data.materials])
    # The curved chair back is moulded plastic, not the wardrobe's laminate.
    o=bpy.data.objects['C43_ChairWhiteCurvedBack'];m=material('Chair_satin_shell',(.78,.785,.755),.42)
    assign(o,[m])

if full or kind=='props':
    y,x=np.mgrid[0:512,0:512]/512
    weave=.5+.075*np.sin(x*math.tau*89+.9*np.sin(y*math.tau*89))+.045*np.sin(y*math.tau*83)
    fibre=image('accessory-fabric-weave',weave,'props',False)
    capmat=material('Cap_charcoal_twill',(.026,.027,.030),.80,sheen=.34);bump(capmat,fibre,3,.00022)
    seam=material('Cap_fine_stitch',(.052,.054,.058),.87,sheen=.18)
    metal=material('Small_satin_nickel',(.38,.40,.41),.33,.75)
    for o in list(scene.objects):
        if o.type=='MESH' and o.name.startswith(('C43_Cap1_','C43_Cap2_','C43_Cap3_')):
            assign(o,[seam if 'stitch' in o.name or 'seam' in o.name else capmat])
    # Connect the existing hat hook to the nearest authored crown hem. The
    # hats' silhouettes, tailored panels and positions remain exactly intact.
    for i in range(3):
        crown=next(o for o in scene.objects if o.name.startswith(f'C43_Cap{i+1}_crown-sewn-hem'))
        hook=bpy.data.objects[f'C43_Cap_hook_{i}'];center=web(hook.matrix_world.translation)
        points=[web(crown.matrix_world@v.co) for v in crown.data.vertices]
        end=min(points,key=lambda p:(p-Vector((center.x,center.y,.045))).length)
        tube(hook.name,[(center.x,center.y+.012,.002),(center.x,center.y+.013,.029),tuple(end+Vector((0,-.003,0))),tuple(end+Vector((0,.004,0)))],.0024,metal)

    navy=material('Bag_soft_navy',(.044,.048,.073),.80,sheen=.3);cream=material('Bag_canvas_base',(.62,.62,.56),.86,sheen=.2)
    for m in [navy,cream]:bump(m,fibre,3,.00025)
    vv=[];ff=[];uv=[];n=80;rows=37
    for j in range(rows):
        t=j/(rows-1);width=np.interp(t,[0,.12,.4,.70,1],[.075,.145,.150,.119,.075]);depth=np.interp(t,[0,.14,.5,.8,1],[.025,.05,.054,.037,.021])
        for i in range(n):
            a=math.tau*i/n;fold=(.008*math.sin(3*a+t*5)+.004*math.sin(7*a-t*8))*math.sin(math.pi*t)
            xx=1.955+.007*math.sin(t*5)+width*math.copysign(abs(math.cos(a))**.68,math.cos(a))
            yy=1.105+.318*t+.010*math.sin(a+.4)*math.sin(math.pi*t)-.012*math.sin(a)**2*t**8
            zz=1.446+(depth+fold)*math.copysign(abs(math.sin(a))**.68,math.sin(a))
            vv.append((xx,yy,zz));uv.append((i/n,t))
    for j in range(rows-1):
        for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    ff.append(tuple(reversed(range(n))))
    bag=replace('C43_Hanging_bag',vv,ff,[cream,navy],uv);solid(bag,.0015)
    for p in bag.data.polygons:p.material_index=0 if p.index<13*n or len(p.vertices)>4 else 1
    settle_bag(bag)
    # Flatten the two straps into sewn fabric ribbons, broad across the chest
    # but thin in depth; both ends enter the actual lip and meet the hook.
    for k in range(2):
        points=[]
        lip=[Vector(v) for v in vv[-n:]]
        start=min(lip,key=lambda p:(p-Vector((1.885,1.421,1.434 if k==0 else 1.458))).length)
        end=min(lip,key=lambda p:(p-Vector((2.012,1.421,1.434 if k==0 else 1.458))).length)
        for j in range(49):
            t=j/48;xx=start.x+(end.x-start.x)*t;yy=start.y+(end.y-start.y)*t+.186*math.sin(math.pi*t)**.72
            zz=(start.z+(end.z-start.z)*t)*(1-math.sin(math.pi*t)**3)+1.412*math.sin(math.pi*t)**3
            points.append((xx,yy,zz))
        verts=[];faces=[]
        for j,p in enumerate(points):
            tangent=(Vector(points[min(j+1,48)])-Vector(points[max(j-1,0)])).normalized();across=Vector((tangent.y,-tangent.x,0)).normalized()
            for side in [-1,1]:verts.append(tuple(Vector(p)+across*side*.0055))
        for j in range(48):faces.append((2*j,2*j+1,2*j+3,2*j+2))
        ob=replace(f'C43_Bag_strap_{k}',verts,faces,[navy],[(i%2,i//2/48) for i in range(len(verts))]);solid(ob,.0013)
    hookmat=material('Opaque_white_hook',(.76,.77,.72),.40)
    hook=bpy.data.objects['C43_Bag_wall_hook'];assign(hook,[hookmat])
    for v in hook.data.vertices:
        p=web(hook.matrix_world@v.co)
        if p.z<1.391:p.z-=.008;v.co=hook.matrix_world.inverted()@bp(p)
    tube('C43_Bag_hook_tip',[(1.955,1.615,1.393),(1.955,1.590,1.411),(1.955,1.603,1.414)],.003,hookmat)

    # Reuse the newest accepted softpack/tissue geometry, never its unrelated
    # heart print. Source coordinates are converted once to this smaller pack.
    names=['heart-print-soft-tissue-package','softpack-gingham-rounded-sides','raised-folded-tissue-0','raised-folded-tissue-1']
    with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=list(names)
    imported={o.name:o for o in dst.objects if o}
    bodymat=material('Tissue_soft_wrapper',(.82,.82,.77),.58)
    papermat=material('Tissue_thin_fibre',(.88,.87,.81),.94);bump(papermat,fibre,1,.00006)
    def packpoint(co,body=False):
        p=web(co);return (1.195+p.z*.18/.205,1.0125+(p.y+(.047 if body else 0))*.079/.094,.214+p.x*.108/.123)
    verts=[];faces=[];uv=[]
    for name in names[:2]:
        me=imported[name].data;offset=len(verts);verts.extend(packpoint(v.co,True) for v in me.vertices)
        faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
        uv.extend((web(v.co).z/.205+.5,web(v.co).y/.094) for v in me.vertices)
    replace('C43_Tissue_packet',verts,faces,[bodymat],uv)
    for k,name in enumerate(names[2:]):
        me=imported[name].data;verts=[packpoint(v.co) for v in me.vertices]
        verts=[(x,1.0915+(y-1.0915)*.63,z) for x,y,z in verts]
        replace(f'C43_Tissue_{k}',verts,[tuple(p.vertices) for p in me.polygons],[papermat])
    for o in imported.values():bpy.data.objects.remove(o,do_unlink=True)
    # A real raised heat-seal, without invented product text or branding.
    green=material('Tissue_muted_green_seal',(.05,.25,.19),.57)
    tube('C43_Tissue_top_seal',[(1.11,1.085,.179),(1.15,1.091,.166),(1.23,1.090,.166),(1.28,1.084,.179)],.0012,green)
    slot=material('Tissue_opening_shadow',(.12,.12,.10),.95)
    opening=lathe('C43_Tissue_opening',(1.195,1.0916,.214),[(0,0),(.008,0),(.008,.0004),(0,.0004)],slot,48)
    for v in opening.data.vertices:v.co.x=1.195+(v.co.x-1.195)*5

    plastic=material('Bottle_clear_PET',(.72,.76,.77),.13,alpha=.105)
    cupmat=material('Cup_translucent_rim',(.82,.84,.82),.22,alpha=.18)
    for name,m in [('C43_Ribbed_water_bottle',plastic),('C43_Plastic_cup',cupmat)]:assign(bpy.data.objects[name],[m])
    # Reference reads bottle -> cup -> tissue from left to right. Move only
    # these loose objects; all architecture and large furniture stay fixed.
    for name in ['C43_Ribbed_water_bottle','C43_Bottle_water','C43_Bottle_cap']:
        o=bpy.data.objects[name];targets.add(name);o.location.x-=.34
    o=bpy.data.objects['C43_Plastic_cup'];targets.add(o.name);o.location.x-=.27
    # Reinforcing rings with smooth manufactured shoulder transitions.
    profile=[(0,0),(.030,0),(.042,.003),(.045,.009),(.045,.020)]
    for h in [.027,.046,.067,.087,.108,.131,.154,.177]:profile.extend([(.045,h),(.0438,h+.002),(.0443,h+.004),(.045,h+.006)])
    profile +=[(.045,.19),(.043,.20),(.038,.211),(.029,.226),(.020,.237),(.0168,.243),(.0168,.258),(.0153,.258),(.0153,.243),(.027,.226),(.036,.211),(.042,.197),(.043,.015),(.039,.004),(0,.004)]
    lathe('C43_Ribbed_water_bottle',(.56,1.0125,.215),profile,plastic)
    red=material('Bottle_label_red',(.53,.029,.014),.52)
    white=material('Bottle_label_white',(.82,.83,.78),.59)
    label=lathe('C43_Bottle_label',(.56,1.0125,.215),[(.046,.086),(.046,.123),(.046,.137),(.0457,.137),(.0457,.123),(.0457,.086),(.046,.086)],red)
    label.data.materials.append(white)
    for p in label.data.polygons:p.material_index=int((label.matrix_world@p.center).z>1.1354)
    # Rounded rolled rim, tapered inner wall and finite bottom, no white solid.
    lathe('C43_Plastic_cup',(.89,1.0125,.215),[(0,0),(.027,0),(.032,.003),(.033,.007),(.0386,.105),(.0398,.109),(.0394,.112),(.038,.113),(.0368,.112),(.0365,.109),(.037,.106),(.0305,.008),(0,.004)],cupmat)
    cap=bpy.data.objects['C43_Bottle_cap'];assign(cap,[material('Bottle_cap_satin_red',(.44,.019,.012),.42)])
    scene['finish07_reuse']=json.dumps({'room':'yongwang-jiayuan','revision':'shelf36','commit':'cbbf843','sha256':source_hash,'objects':names,'method':'append meshes; isolated smaller unbranded softpack variant; no source writes'})

bpy.context.view_layer.update()
unchanged={name:digest(bpy.data.objects[name]) for name in before if name not in targets}
assert all(value==before[name] for name,value in unchanged.items()),'Unrelated object changed'
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash,'Source-room changed'
if full:
    scene['parent_web_revision']='courtyard43-interior06';scene['web_revision']='courtyard43-interior07'
    records=json.loads(scene['components'])
    for r in records:r['sha256']=hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest()
    scene['components']=json.dumps(records);output=ROOM/'assets/full-room/Courtyard43-interior.blend'
else:
    scene['component_parent_revision']=scene['component_revision']
    scene['component_revision']={'architecture':'architecture08','furniture':'courtyard43-furniture06','props':'courtyard43-props02'}[kind]
    output=ROOM/f'assets/{kind}/Courtyard43-{kind}.blend'
scene['finish07']='Photo-led timber, white finishes and accessory refinement; no measured dimensions or invented label text'
# Imported orphan materials do not become persistent cross-room dependencies.
for group in [bpy.data.meshes,bpy.data.materials,bpy.data.images,bpy.data.node_groups]:
    for block in group:block.use_fake_user=False
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath,library=im.library),start=str(output.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(output))
result={'saved':str(output),'targets':sorted(targets),'unchangedObjects':len(unchanged)}
if full:
    p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'export'}
    exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope);result['export']=scope['export_interior']()
