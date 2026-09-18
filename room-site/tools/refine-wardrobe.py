"""Build the approved empty three-door wardrobe. Run via Blender Lab MCP only.

Input: viewer26. Output: wardrobe29. World placement, door fronts and all
unrelated assets stay unchanged. Metres; helper coordinates use browser Y-up.
The photograph establishes two bays (2+1 doors), not three equal cupboards.
"""
import copy, gzip, json, math, os
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(os.environ.get('BEIPIAO_ROOT',Path(__file__).resolve().parents[2]))
OUT=ROOT/'room-site/dist/assets/full-room'
data=json.loads((OUT/'scene.json').read_text(encoding='utf-8'))
assert data['revision']=='viewer26', 'Apply only to the verified viewer26 source'
before=copy.deepcopy(data); raw=bytearray((OUT/'geometry.bin').read_bytes())
obs={int(o['web_node_id']):o for o in bpy.data.objects if 'web_node_id' in o}
mats={int(m['web_material_id']):m for m in bpy.data.materials if 'web_material_id' in m}
collection=obs[772].users_collection[0]
C=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
I=Matrix.Identity(4); changed=set(); new_meshes=[]; ao_objects=[]
closed_world={n:obs[n].matrix_world.copy() for n in [775,777,779]}

def bp(p):return (p[0],-p[2],p[1])
def flat(m):return [m[r][c] for c in range(4) for r in range(4)]
def activate(o):
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
def web_matrix(o):return C.inverted()@o.matrix_local@C
def meta(o,nid,extra=None):
    o['web_node_id']=nid;o['web_name']=o.name
    d={'authoring':'Blender','blenderNode':nid,'revision':'wardrobe29',**(extra or {})}
    o['web_user_data']=json.dumps(d);return d
def group(name,position,extra):
    nid=len(data['nodes']);o=bpy.data.objects.new(name,None);collection.objects.link(o)
    o.parent=obs[772];o.matrix_local=Matrix.Translation(bp(position));obs[nid]=o
    bpy.context.view_layer.update()
    d=copy.deepcopy(before['nodes'][772]);d.update(id=nid,parent=772,name=name,matrix=flat(web_matrix(o)),userData=meta(o,nid,extra))
    data['nodes'].append(d);changed.add(nid);bpy.context.view_layer.update();return nid
def material(name,base=0,color=None,rough=.55,metal=0,wood=False,vertex_ao=False):
    mid=len(data['materials']);desc=copy.deepcopy(data['materials'][base]);desc['id']=mid
    desc['userData']={'surfaceFinish':name,'revision':'wardrobe29'}
    desc['props'].update(roughness=rough,metalness=metal,vertexColors=vertex_ao)
    if color:desc['colors']['color']=color
    if not wood:desc['textures']={}
    else:
        tid=len(data['textures']);t=copy.deepcopy(data['textures'][8]);t.update(id=tid,repeat=[1,1]);data['textures'].append(t)
        desc['textures']={'map':tid,'bumpMap':tid};desc['props'].update(bumpScale=.000055,clearcoat=.04,clearcoatRoughness=.6)
    mat=mats[base].copy();mat.name=name;mat['web_material_id']=mid
    # Retain image provenance, but give this material its own unscaled UV mapping.
    mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links
    nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');bs=nodes.new('ShaderNodeBsdfPrincipled');links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*(color or desc['colors']['color']),1)
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    if wood:
        image=bpy.data.images.load(str(ROOT/'room-site/dist/assets/wood.jpg'),check_existing=True)
        tex=nodes.new('ShaderNodeTexImage');tex.image=image;tex.extension='REPEAT'
        links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        bump=nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.000055
        links.new(tex.outputs['Color'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
        if vertex_ao:
            attr=nodes.new('ShaderNodeVertexColor');attr.layer_name='ContactAO'
            mul=nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
            links.new(tex.outputs['Color'],mul.inputs[1]);links.new(attr.outputs['Color'],mul.inputs[2]);links.new(mul.outputs[0],bs.inputs['Base Color'])
    data['materials'].append(desc);mats[mid]=mat;return mid

wood=material('Wardrobe · warm satin veneer inside',61,[1,1,1],.58,wood=True,vertex_ao=True)
nickel=material('Wardrobe · brushed nickel hardware',17,[.53,.55,.54],.30,.83)
screw_dark=material('Wardrobe · recessed screw slot',17,[.045,.048,.046],.55,.5)
mirror_edge=material('Wardrobe · polished glass bevel',17,[.68,.75,.71],.08,.94)
mirror_surface=material('Wardrobe · room reflection surface',17,[.91,.94,.92],.02,1)

def attach(mesh,name,mid,parent=772,nid=None,extra=None):
    if nid is None:
        nid=len(data['nodes']);d=copy.deepcopy(before['nodes'][775]);data['nodes'].append(d)
        o=bpy.data.objects.new(name,mesh);collection.objects.link(o);obs[nid]=o
    else:
        d=data['nodes'][nid];o=obs[nid];o.modifiers.clear();o.data=mesh
    o.name=name;o.parent=obs[parent];o.matrix_local=I.copy()
    mesh.materials.clear();mesh.materials.append(mats[mid]);o.material_slots[0].link='DATA';o.material_slots[0].material=mats[mid]
    d.update(id=nid,parent=parent,name=name,type='Mesh',material=mid,matrix=flat(I),visible=True,castShadow=True,receiveShadow=True,userData=meta(o,nid,extra))
    changed.add(nid);new_meshes.append(o);return o

def box_mesh(name,center,size,grain='vertical',dense=False):
    # Subdivision is restricted to broad planar faces for baked local contact AO.
    # The small bevel stays geometry, with exact planar top/side normals.
    verts=[];faces=[]
    for axis in range(3):
        u=(axis+1)%3;v=(axis+2)%3
        nu=max(1,math.ceil(size[u]/.042)) if dense else 1
        nv=max(1,math.ceil(size[v]/.042)) if dense else 1
        for sign in [-1,1]:
            off=len(verts)
            for j in range(nv+1):
                for i in range(nu+1):
                    p=list(center);p[axis]+=sign*size[axis]/2;p[u]+=(i/nu-.5)*size[u];p[v]+=(j/nv-.5)*size[v];verts.append(bp(p))
            for j in range(nv):
                for i in range(nu):
                    k=off+j*(nu+1)+i;f=(k,k+1,k+nu+2,k+nu+1);faces.append(f if sign>0 else tuple(reversed(f)))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces)
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0000005);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    temp=bpy.data.objects.new(name+'-bevel-eval',me);collection.objects.link(temp);activate(temp)
    bevel=temp.modifiers.new('Manufactured 0.8 mm edge','BEVEL');bevel.width=min(.0008,min(size)*.12);bevel.segments=3;bevel.limit_method='ANGLE'
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    # Weighted normals retain flat laminate and veneer, instead of inflated boards.
    for face in temp.data.polygons:face.use_smooth=True
    normal=temp.modifiers.new('Planar board normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50
    bpy.ops.object.modifier_apply(modifier=normal.name)
    me=temp.data;me.name=name;uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        n=p.normal;dominant=max(range(3),key=lambda k:abs(n[k]))
        for li in p.loop_indices:
            q=me.vertices[me.loops[li].vertex_index].co;x,y,z=q.x,q.z,-q.y
            if grain=='horizontal':u=z/.43;v=x/1.15
            elif dominant==0:u=z/.48;v=y/1.60
            else:u=x/.48;v=y/1.60
            uv.data[li].uv=(u+.17,v+.09)
    bpy.data.objects.remove(temp,do_unlink=True);return me

def board(name,center,size,nid=None,mid=wood,grain='vertical',ao=True):
    o=attach(box_mesh(name,center,size,grain,ao),name,mid,nid=nid)
    if ao:ao_objects.append(o)
    return o

# The old solid block becomes the fixed bedside panel; all other carcass panels
# are real boards, leaving both bays hollow. The visible outside veneer is kept.
board('wardrobe-fixed-racket-side',(-.005,.0+1.0475,.576),(.560,2.020,.018),773,61,ao=False)
board('wardrobe-fixed-window-side',(-.005,1.0475,-.576),(.560,2.020,.018))
board('wardrobe-back-panel',(-.279,1.0475,0),(.012,2.020,1.134))
board('wardrobe-wide-and-narrow-partition',(-.005,1.080,-.193),(.560,1.955,.018))
board('wardrobe-bottom-board',(-.005,.101,0),(.560,.022,1.134),grain='horizontal')
board('wardrobe-top-interior-liner',(-.005,2.0475,0),(.560,.020,1.134),grain='horizontal')
board('wardrobe-warm-front-plinth',(.264,.061,0),(.022,.070,1.134),grain='horizontal')

# Tops of shelves align to the photo; left bay is uninterrupted between doors.
wide=(-.184,.567);narrow=(-.567,-.202)
shelf_ids=[]
for label,span,levels in [('wide',wide,[.515,1.405]),('narrow',narrow,[.505,.945,1.405])]:
    for i,height in enumerate(levels):
        o=board(f'wardrobe-{label}-shelf-{i+1}',(-.009,height,(span[0]+span[1])/2),(.528,.018,span[1]-span[0]),grain='horizontal')
        shelf_ids.append(o['web_node_id'])

# Bake modest short-range occlusion into vertex colours using actual boards.
# No door occlusion is baked: illumination must work with every door state.
bpy.context.view_layer.update()
vertices=[];polygons=[]
for o in ao_objects+[obs[773]]:
    offset=len(vertices);vertices.extend(v.co.copy() for v in o.data.vertices)
    polygons.extend(tuple(offset+i for i in p.vertices) for p in o.data.polygons)
bvh=BVHTree.FromPolygons(vertices,polygons,all_triangles=False)
samples=[]
for i in range(20):
    r=math.sqrt((i+.5)/20);a=i*2.399963229728653
    samples.append((r*math.cos(a),r*math.sin(a),math.sqrt(1-r*r)))
for o in ao_objects:
    me=o.data;col=me.color_attributes.new(name='ContactAO',type='FLOAT_COLOR',domain='CORNER');cache={}
    for loop in me.loops:
        p=me.vertices[loop.vertex_index].co;n=me.corner_normals[loop.index].vector
        key=(loop.vertex_index,round(n.x,3),round(n.y,3),round(n.z,3))
        if key not in cache:
            helper=Vector((0,0,1)) if abs(n.z)<.95 else Vector((0,1,0));u=n.cross(helper).normalized();v=n.cross(u).normalized();blocked=0
            for a,b,c in samples:
                hit,normal,index,d=bvh.ray_cast(p+n*.0004,u*a+v*b+n*c,.115)
                if hit is not None:blocked+=(1-d/.115)**.6
            cache[key]=max(.67,1-.48*blocked/len(samples))
        value=cache[key];col.data[loop.index].color=(value,value,value,1)

def tube(name,a,b,radius,mid,parent=772):
    a=Vector(bp(a));b=Vector(bp(b));direction=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=20,radius=radius,depth=direction.length,end_fill_type='NGON',location=(0,0,0))
    o=bpy.context.object;me=o.data;rotation=Vector((0,0,1)).rotation_difference(direction)
    for v in me.vertices:v.co=rotation@v.co+(a+b)/2
    for p in me.polygons:p.use_smooth=len(p.vertices)==4
    bpy.data.objects.remove(o,do_unlink=True);return attach(me,name,mid,parent)

rail_x=-.015;rail_y=1.322
tube('wardrobe-hanging-rail',(rail_x,rail_y,wide[0]-.004),(rail_x,rail_y,wide[1]+.004),.0105,nickel)
for z,s in [(wide[0],1),(wide[1],-1)]:
    tube('wardrobe-rail-wall-socket',(rail_x,rail_y,z-s*.001),(rail_x,rail_y,z+s*.007),.016,nickel)
    # Ends seat inside the sockets, never float alongside them.
for span,levels in [(wide,[.515,1.405]),(narrow,[.505,.945,1.405])]:
    for height in levels:
        for z,sgn in [(span[0],1),(span[1],-1)]:
            for x in [-.20,.195]:tube('wardrobe-shelf-support-pin',(x,height-.012,z-sgn*.002),(x,height-.012,z+sgn*.007),.0025,nickel)

door_specs=[('Left',779,780,.579,-math.radians(85),-.13),('Middle',777,778,-.193,math.radians(85),.13),('Right',775,776,-.580,math.radians(85),.13)]
pivots=[]
for label,leaf_id,handle_id,z,angle,unused in door_specs:
    # Axis lies just outside the laminate face, so the overlay door clears the
    # carcass edge during its whole motion. Origin is saved in the .blend.
    pid=group('wardrobe-'+label.lower()+'-hinge-pivot',(.308,0,z),{'dynamic':True,'interactive':'wardrobe'+label,'closedAngle':0,'openAngle':angle,'leafNodeId':leaf_id})
    pivots.append(pid)
    for nid in [leaf_id,handle_id]:
        o=obs[nid];world=o.matrix_world.copy();o.parent=obs[pid];o.matrix_world=world
        if nid==778:
            # The middle handle belongs at the meeting edge of the LEFT pair.
            o.location.y=-.335
        bpy.context.view_layer.update();d=data['nodes'][nid];d['parent']=pid;d['matrix']=flat(web_matrix(o));d['name']='wardrobe-'+label.lower()+('-door' if nid==leaf_id else '-handle');o.name=d['name'];o['web_name']=o.name;changed.add(nid)
    # Each hinge has a fixed nickel mounting plate, pivot pin, and moving arm.
    # A cup boss on the inner face supplies the recognizable concealed-hinge form.
    inward=-1 if label=='Left' else 1
    for h in [.235,1.045,1.900]:
        attach(box_mesh('hinge-fixed-plate',(.248,h,z+inward*.010),(.042,.052,.004)),f'wardrobe-{label.lower()}-hinge-fixed-plate',nickel)
        tube('wardrobe-hinge-axis',(.308,h-.014,z),(.308,h+.014,z),.004,nickel)
        # Coordinates below are relative to the new pivot.
        attach(box_mesh('hinge-cup-back',(-.029,h,inward*.028),(.004,.035,.039)),f'wardrobe-{label.lower()}-hinge-cup',nickel,pid)
        attach(box_mesh('hinge-link-arm',(-.018,h,inward*.012),(.037,.013,.027)),f'wardrobe-{label.lower()}-hinge-link',nickel,pid)
        for y in [h-.021,h+.021]:
            tube('wardrobe-hinge-plate-screw',(.259,y,z+inward*.008),(.259,y,z+inward*.013),.0034,nickel)
            attach(box_mesh('screw-cross-slot',(.259,y,z+inward*.0132),(.004,.0008,.0003)), 'wardrobe-hinge-screw-slot',screw_dark)

# Mirror: real 4 mm backing plus a rounded reflective face. Reflector requires
# the face to be in local XY with +Z normal; do not rotate only its vertices.
right=pivots[2];mirror_w=.265;mirror_h=1.385;radius=.016
def rounded_outline(w,h,r):
    pts=[]
    for cx,cy,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for k in range(9):
            a=math.radians(start+k*90/8);pts.append((cx+r*math.cos(a),cy+r*math.sin(a)))
    return pts
outline=rounded_outline(mirror_w,mirror_h,radius)
# Local web XY plane -> Blender XZ plane. Its reflection normal is web +Z.
verts=[bp((x,y,0)) for x,y in outline];faces=[tuple(range(len(verts)))]
me=bpy.data.meshes.new('wardrobe-rounded-mirror-face');me.from_pydata(verts,[],faces);me.update()
uv=me.uv_layers.new(name='UVMap')
for l in me.loops:
    x,y=outline[l.vertex_index];uv.data[l.index].uv=(x/mirror_w+.5,y/mirror_h+.5)
mirror=attach(me,'wardrobe-right-inner-mirror-reflection',mirror_surface,right,extra={'mirrorSurface':True,'dynamic':True})
W=Matrix.Translation(Vector((-.0315,.914,.194)))@Matrix.Rotation(-math.pi/2,4,'Y')
mirror.matrix_local=C@W@C.inverted();data['nodes'][mirror['web_node_id']]['matrix']=flat(W)
data['nodes'][mirror['web_node_id']]['castShadow']=False;mirror.hide_render=False
# Thin extruded backing follows the same rounded silhouette and sits behind
# the reflection plane (towards the door), with no coplanar opaque layer.
backverts=[]
for depth in [-.004,0]:backverts.extend(bp((x,y,depth)) for x,y in outline)
N=len(outline);backfaces=[tuple(reversed(range(N))),tuple(range(N,2*N))]
backfaces.extend((i,(i+1)%N,(i+1)%N+N,i+N) for i in range(N))
me=bpy.data.meshes.new('wardrobe-rounded-mirror-glass');me.from_pydata(backverts,[],backfaces)
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();me.uv_layers.new(name='UVMap')
edge=attach(me,'wardrobe-right-inner-mirror-glass-edge',mirror_edge,right)
EW=Matrix.Translation(Vector((-.0311,.914,.194)))@Matrix.Rotation(-math.pi/2,4,'Y')
edge.matrix_local=C@EW@C.inverted();data['nodes'][edge['web_node_id']]['matrix']=flat(EW)

data['refs']['wardrobeDoors']=pivots;data['refs']['wardrobeMirror']=mirror['web_node_id']
data['refs']['wardrobeShelves']=shelf_ids
bpy.context.view_layer.update()
for n,M in closed_world.items():
    assert max(abs(obs[n].matrix_world[r][c]-M[r][c]) for r in range(4) for c in range(4))<1e-6,('Door closure changed',n)

def pack(values,size=None):
    a=np.asarray(values);integer=a.dtype.kind in 'iu';a=a.astype('<u4' if integer else '<f4').ravel();assert np.isfinite(a).all()
    while len(raw)%4:raw.append(0)
    d={'offset':len(raw),'length':len(a),'type':'Uint32Array' if integer else 'Float32Array'}
    if size:d['itemSize']=size
    raw.extend(a.tobytes());return d
def export(o):
    me=o.data;me.calc_loop_triangles();p=[];n=[];uv=[];colors=[];ao=me.color_attributes.get('ContactAO')
    for l in me.loops:
        v=me.vertices[l.vertex_index].co;normal=me.corner_normals[l.index].vector
        p.append((v.x,v.z,-v.y));n.append((normal.x,normal.z,-normal.y))
        uv.append(tuple(me.uv_layers.active.data[l.index].uv))
        if ao:colors.append(tuple(ao.data[l.index].color[:3]))
    attrs={'position':pack(p,3),'normal':pack(n,3),'uv':pack(uv,2)}
    if ao:attrs['color']=pack(colors,3)
    gid=len(data['geometries']);data['geometries'].append({'id':gid,'attributes':attrs,'index':pack([i for t in me.loop_triangles for i in t.loops]),'groups':[],'userData':{'authoring':'Blender','sourceType':'ApprovedWardrobeInterior','revision':'wardrobe29'}})
    data['nodes'][o['web_node_id']]['geometry']=gid
for o in new_meshes:export(o)

# Prevent a refinement of this asset from accidentally reverting any other work.
for i,n in enumerate(before['nodes']):
    if i not in changed:assert data['nodes'][i]==n,('Unrelated node changed',i)
assert data['geometries'][:len(before['geometries'])]==before['geometries']
assert data['materials'][:len(before['materials'])]==before['materials']
assert data['textures'][:len(before['textures'])]==before['textures']
data['revision']='wardrobe29';data['statistics']['meshes']=len(data['geometries'])
data['statistics']['triangles']=sum(g['index']['length']//3 for g in data['geometries'])
data['statistics']['wardrobeRefinement']={'doors':3,'bays':2,'empty':True,'leftBayShelves':[.515,1.405],'rightBayShelves':[.505,.945,1.405],'railHeight':1.322,'boardThickness':.018,'mirrorThickness':.004,'dimensionsFrom':'photo proportions, not measurements','shortRangeAO':True}
bpy.context.scene['web_revision']='wardrobe29';bpy.context.scene['wardrobe_notes']='Approved v2 empty wardrobe: fixed racket side, left double bay, right single bay with inside mirror. Independent door origins, nickel hinges, supported rail and shelves. Runtime coordinates are Y-up; mirror local +Z faces reflective side.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'generated-assets/full-room/永旺家园-完整场景.blend'))
(OUT/'geometry.bin').write_bytes(raw);(OUT/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
(OUT/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'wardrobe29','pivots':pivots,'mirror':mirror['web_node_id'],'shelves':shelf_ids,'newMeshes':len(new_meshes),'modifiedOriginalNodes':sorted(n for n in changed if n<len(before['nodes'])),'closedDoorMatricesPreserved':True,'unrelatedAssetsPreserved':True,'sourceSaved':True,'geometryBytes':len(raw)}
