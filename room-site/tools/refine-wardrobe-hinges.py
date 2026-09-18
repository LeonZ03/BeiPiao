"""Finish wardrobe29: concealed articulated hinges and a hidden top rebate.
Execute through Blender Lab MCP. Preserve the approved exterior and pivots.
"""
import copy,gzip,json,math,os
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(os.environ.get('BEIPIAO_ROOT',Path(__file__).resolve().parents[2]));OUT=ROOT/'room-site/dist/assets/full-room'
data=json.loads((OUT/'scene.json').read_text(encoding='utf-8'));assert data['revision']=='wardrobe29'
before=copy.deepcopy(data);raw=bytearray((OUT/'geometry.bin').read_bytes());changed=set();exports=[]
obs={int(o['web_node_id']):o for o in bpy.data.objects if 'web_node_id' in o}
mats={int(m['web_material_id']):m for m in bpy.data.materials if 'web_material_id' in m}
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)));I=Matrix.Identity(4)
collection=obs[772].users_collection[0]
def bp(p):return Vector((p[0],-p[2],p[1]))
def flat(m):return [m[r][c] for c in range(4) for r in range(4)]
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def update_desc(o):
    nid=o['web_node_id'];d=data['nodes'][nid];d['name']=o.name;d['matrix']=flat(C.inverted()@o.matrix_local@C);o['web_name']=o.name;changed.add(nid)
def add(name,mesh=None,mid=None,parent=772,extra=None):
    nid=len(data['nodes']);o=bpy.data.objects.new(name,mesh);collection.objects.link(o);o.parent=obs[parent];o.matrix_local=I.copy();obs[nid]=o
    d=copy.deepcopy(before['nodes'][772]);d.update(id=nid,parent=parent,name=name,matrix=flat(I),userData={'authoring':'Blender','blenderNode':nid,'revision':'wardrobe29b',**(extra or {})})
    if mesh:
        d.update(type='Mesh',material=mid,castShadow=True,receiveShadow=True);mesh.materials.clear();mesh.materials.append(mats[mid]);exports.append(o)
    o['web_node_id']=nid;o['web_name']=name;o['web_user_data']=json.dumps(d['userData']);data['nodes'].append(d);changed.add(nid);return o
def retire(o):
    nid=o['web_node_id'];p=o.parent;local=o.matrix_local.copy();name=o.name
    bpy.data.objects.remove(o,do_unlink=True);e=bpy.data.objects.new(name+'-merged',None);collection.objects.link(e);e.parent=p;e.matrix_local=local;obs[nid]=e
    d=data['nodes'][nid];d.update(type='Group',name=e.name,castShadow=False,receiveShadow=False)
    for k in ['material','geometry']:d.pop(k,None)
    e['web_node_id']=nid;e['web_name']=e.name;e['web_user_data']=json.dumps(d['userData']);changed.add(nid)
def primitive_box(name,size):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o=bpy.context.object;o.name=name;o.scale=(size[0],size[2],size[1]);activate(o);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bevel=o.modifiers.new('Small nickel edge','BEVEL');bevel.width=.0006;bevel.segments=2;bpy.ops.object.modifier_apply(modifier=bevel.name)
    me=o.data;bpy.data.objects.remove(o,do_unlink=True);return me
def place_web(o,W):o.matrix_local=C@W@C.inverted();bpy.context.view_layer.update();update_desc(o)

# Rebate only the invisible underside of the original top cap. The original
# helmet contact plane at 2.1225 m, silhouette and outer veneer remain intact.
cap=obs[774];activate(cap)
bpy.ops.mesh.primitive_cube_add(size=1,location=obs[772].matrix_world@bp((.310,2.058,0)))
cutter=bpy.context.object;cutter.dimensions=(.068,1.30,.045);activate(cutter);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
activate(cap);mod=cap.modifiers.new('Hidden clearance behind overlay doors','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
cap.name='wardrobe-top-cap-with-concealed-rebate';exports.append(cap);update_desc(cap)

nickel=next(m['id'] for m in data['materials'] if m['userData'].get('surfaceFinish')=='Wardrobe · brushed nickel hardware')
hinges=[];door_ids=data['refs']['wardrobeDoors']
for pid in door_ids:
    door=obs[pid];d=data['nodes'][pid];z=d['matrix'][14];side=-1 if d['userData']['interactive']=='wardrobeLeft' else 1
    cups=[o for o in obs.values() if o.type=='MESH' and o.parent==door and o.name.endswith('hinge-cup')]
    # Blender auto-appends numeric suffixes; names from the manifest are stable.
    cups=[obs[n['id']] for n in data['nodes'] if n['parent']==pid and n['name'].split('.')[0].endswith('hinge-cup')]
    for cup in cups:
        for v in cup.data.vertices:v.co.x+=.0005
        exports.append(cup)
    for n in list(data['nodes']):
        if n['parent']==pid and n['name'].split('.')[0].endswith('hinge-link'):retire(obs[n['id']])
    for h in [.235,1.045,1.900]:
        A=Vector((.235,h,z+side*.011));B=Vector((.2795,h,z+side*.028));L=.055
        mech=add('wardrobe-concealed-hinge-mechanism',extra={'dynamic':True,'noCollision':True,'doorNodeId':pid,'fixedAnchor':list(A),'movingAnchor':[-.0285,h,side*.028],'armLength':L,'elbowSign':side})
        mid=mech['web_node_id'];arm1=add('wardrobe-hinge-upper-link',primitive_box('hinge-upper',(.009,1,.006)),nickel,mid)
        arm2=add('wardrobe-hinge-lower-link',primitive_box('hinge-lower',(.009,1,.006)),nickel,mid)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.005)
        temp=bpy.context.object;mesh=temp.data;bpy.data.objects.remove(temp,do_unlink=True);joint=add('wardrobe-hinge-articulation-pin',mesh,nickel,mid)
        D=B-A;E=(A+B)/2+Vector((-D.z,0,D.x)).normalized()*math.sqrt(L*L-D.length_squared/4)*side
        for o,a,b in [(arm1,A,E),(arm2,E,B)]:
            q=Vector((0,1,0)).rotation_difference(b-a)
            W=Matrix.Translation((a+b)/2)@q.to_matrix().to_4x4()@Matrix.Diagonal((1,L,1,1));place_web(o,W)
        place_web(joint,Matrix.Translation(E))
        md=data['nodes'][mid]['userData'];md.update(upperArmNodeId=arm1['web_node_id'],lowerArmNodeId=arm2['web_node_id'],jointNodeId=joint['web_node_id']);mech['web_user_data']=json.dumps(md);hinges.append(mid)
        for i in range(25):
            angle=d['userData']['openAngle']*i/24
            M=Matrix.Translation(Vector((.308,0,z)))@Matrix.Rotation(angle,4,'Y')
            distance=(M@Vector(md['movingAnchor'])-A).length
            assert distance<2*L-.0005,('Hinge overextended',pid,i,distance)

# Move the existing tiny vertical pins behind the door, into their fixed plates.
for n in data['nodes']:
    if n['type']=='Mesh' and n['name'].split('.')[0]=='wardrobe-hinge-axis':
        o=obs[n['id']]
        for v in o.data.vertices:v.co.x-=.073
        exports.append(o)
data['refs']['wardrobeHingeMechanisms']=hinges

# Consolidate repeated fixed screws/sockets and door cups by material and parent.
# Preserve IDs as empty nodes so diagnostics and historic references stay valid.
groups={}
for n in list(data['nodes']):
    if n['type']!='Mesh':continue
    name=n['name']
    if not (name.startswith('wardrobe-hinge-') or name.startswith('wardrobe-rail-') or name.startswith('wardrobe-shelf-support-') or '-hinge-fixed-' in name or '-hinge-cup' in name):continue
    if n['parent'] in hinges:continue
    groups.setdefault((n['parent'],n['material']),[]).append(obs[n['id']])
for (parent,mat),parts in groups.items():
    if len(parts)<2:continue
    verts=[];faces=[];uvs=[];normals=[]
    for o in parts:
        M=o.matrix_local;N=M.to_3x3().inverted().transposed();offset=len(verts);me=o.data
        verts.extend(M@v.co for v in me.vertices)
        for f in me.polygons:
            faces.append(tuple(offset+i for i in f.vertices))
            for li in f.loop_indices:
                uvs.append(tuple(me.uv_layers.active.data[li].uv) if me.uv_layers.active else (0,0));normals.append(tuple((N@me.corner_normals[li].vector).normalized()))
    mesh=bpy.data.meshes.new('wardrobe-consolidated-hardware');mesh.from_pydata(verts,[],faces);mesh.update();uv=mesh.uv_layers.new(name='UVMap')
    for i,v in enumerate(uvs):uv.data[i].uv=v
    mesh.normals_split_custom_set(normals)
    add('wardrobe-consolidated-hardware-'+str(parent)+'-'+str(mat),mesh,mat,parent)
    for o in parts:
        if o in exports:exports.remove(o)
        retire(o)

bpy.context.view_layer.update()
def bvh(o):
    return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],all_triangles=False)
fixed=[o for o in obs.values() if o.type=='MESH' and (o.name.startswith('wardrobe-fixed-') or o.name.startswith('wardrobe-back-') or o.name.startswith('wardrobe-wide-') or o.name.startswith('wardrobe-narrow-') or o.name.startswith('wardrobe-bottom-') or o.name.startswith('wardrobe-top-'))]
fixed_trees=[(o.name,bvh(o)) for o in fixed];collisions=[]
for pid in door_ids:
    pivot=obs[pid];closed=pivot.matrix_local.copy();leaf=obs[data['nodes'][pid]['userData']['leafNodeId']]
    for step in range(25):
        R=Matrix.Rotation(data['nodes'][pid]['userData']['openAngle']*step/24,4,'Y');pivot.matrix_local=closed@C@R@C.inverted();bpy.context.view_layer.update();tree=bvh(leaf)
        for name,other in fixed_trees:
            if tree.overlap(other):collisions.append({'door':pid,'step':step,'fixed':name})
    pivot.matrix_local=closed;bpy.context.view_layer.update()
assert not collisions,collisions

def pack(values,size=None):
    a=np.asarray(values);integer=a.dtype.kind in 'iu';a=a.astype('<u4' if integer else '<f4').ravel();assert np.isfinite(a).all()
    while len(raw)%4:raw.append(0)
    d={'offset':len(raw),'length':len(a),'type':'Uint32Array' if integer else 'Float32Array'}
    if size:d['itemSize']=size
    raw.extend(a.tobytes());return d
for o in exports:
    me=o.data;me.calc_loop_triangles();p=[];n=[];uv=[]
    for l in me.loops:
        v=me.vertices[l.vertex_index].co;normal=me.corner_normals[l.index].vector;p.append((v.x,v.z,-v.y));n.append((normal.x,normal.z,-normal.y));uv.append(tuple(me.uv_layers.active.data[l.index].uv) if me.uv_layers.active else (0,0))
    gid=len(data['geometries']);data['geometries'].append({'id':gid,'attributes':{'position':pack(p,3),'normal':pack(n,3),'uv':pack(uv,2)},'index':pack([i for t in me.loop_triangles for i in t.loops]),'groups':[],'userData':{'authoring':'Blender','sourceType':'ArticulatedWardrobeHardware','revision':'wardrobe29b'}})
    data['nodes'][o['web_node_id']]['geometry']=gid;changed.add(o['web_node_id'])
for i,n in enumerate(before['nodes']):
    if i not in changed:assert data['nodes'][i]==n,('Unrelated node changed',i)
data['revision']='wardrobe29b';data['statistics']['wardrobeRefinement'].update(articulatedHinges=9,doorSweepSamples=25,doorCarcassIntersections=0,topCapRebate=True)
data['statistics']['meshes']=len(data['geometries']);data['statistics']['triangles']=sum(g['index']['length']//3 for g in data['geometries'])
bpy.context.scene['web_revision']='wardrobe29b';bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'generated-assets/full-room/永旺家园-完整场景.blend'))
(OUT/'geometry.bin').write_bytes(raw);(OUT/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0));(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'wardrobe29b','hinges':hinges,'linkLength':.055,'closedDoorPositionsUnchanged':True,'doorCarcassSamples':75,'doorCarcassIntersections':collisions,'hardwareGroups':len(groups),'sourceSaved':True}
