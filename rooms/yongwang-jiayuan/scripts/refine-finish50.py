"""fitting49 -> finish50. Execute only through official Blender Lab MCP.

Incremental photo-guided head/cap/helmet/basin/toiletry corrections. Dimensions
are estimates; visible product fronts use user-provided reference artwork.
Never executes the historic whole-room or asset generators.
"""
from pathlib import Path
import bpy,bmesh,math,json,ast,copy
from mathutils import Vector,Matrix
from mathutils.kdtree import KDTree
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='fitting49'
bpy.context.preferences.filepaths.save_version=0
web=lambda p:Vector((p.x,p.z,-p.y))
original_material=material
def material(*args,**kwargs):
    kwargs['metadata']={'exteriorSurface':False,'revision':'finish50',**kwargs.get('metadata',{})}
    return original_material(*args,**kwargs)

def finish_mesh(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free();o.data.update()
    if not o.data.uv_layers:
        uv=o.data.uv_layers.new(name='UVMap')
        for l in o.data.loops:
            p=o.data.vertices[l.vertex_index].co;uv.data[l.index].uv=(p.x,p.z)
    export(o)
    g=data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]
    g['attributes']['uv1']=copy.deepcopy(g['attributes']['uv'])

def deform(nid,fn):
    o=obs[nid];o.data=o.data.copy()
    for v in o.data.vertices:v.co=Vector(bp(fn(web(v.co))))
    finish_mesh(o)

def cap_crown(p):
    x,y,z=p;t=max(0,min(1,y/.108));return (x*(1-.035*t),y*1.04+.003*math.sin(math.pi*t),z)
def cap_bill(p):
    x,y,z=p;a=math.asin(max(-.999,min(.999,x/.093)));base=.104*math.cos(a)
    t=max(0,min(1,(z-base)/(.09*max(.05,math.cos(a))**.5)))
    return(x,y-.009*t-.025*(x/.094)**2*t,base+(z-base)*(.070/.09))
for nid in range(838,862):deform(nid,cap_bill if nid==839 or 847<=nid<=852 else cap_crown)

# Low, close-fitting rear spoiler; supports/exhaust follow the same map.
for nid in [789,790,793,794,795]:
    deform(nid,lambda p:(p.x,p.y-.030,-.104+(p.z+.104)*.48))

# Small photo-confirmed pale irregular marks are ink on the shell, not floating
# white tubes. Project paths onto the original shell UV field in Blender.
old=data['materials'][63]
carbon=material('FF801 photo-guided charcoal carbon',63,color=(.095,.105,.11),rough=.30,textures={})
set_material(783,carbon)
for nid in [789,790,793,794,795,796,798]:
    if nid not in [790,794]:set_material(nid,carbon)
shell=obs[783];shell.data=shell.data.copy()
# Paint mask in the shell's existing angular/height UV layout. Faint woven
# carbon remains subordinate to the sparse, non-repeating pale print.
w,h=1024,512;yy,xx=np.mgrid[:h,:w];cloth=(np.sin((xx+yy)*math.pi/5)*np.sin((xx-yy)*math.pi/5))*.004
pixels=np.empty((h,w,3));pixels[:]=np.array([.095,.102,.108]);pixels+=cloth[:,:,None]
paths=[[(.63,.79),(.65,.73),(.66,.72),(.675,.675),(.691,.67),(.70,.69)],[(.605,.62),(.63,.60),(.638,.58),(.66,.57)],[(.72,.45),(.715,.41),(.723,.385),(.721,.35)],[(.33,.76),(.35,.73),(.36,.68),(.375,.67)],[(.29,.49),(.30,.46),(.31,.45),(.315,.41)]]
for path in paths:
    for a,b in zip(path,path[1:]):
        ax,ay=a[0]*w,a[1]*h;bx,by=b[0]*w,b[1]*h;dx,dy=bx-ax,by-ay
        t=np.clip(((xx-ax)*dx+(yy-ay)*dy)/max(1,dx*dx+dy*dy),0,1)
        d=np.sqrt((xx-ax-t*dx)**2+(yy-ay-t*dy)**2);mask=np.clip(1.15-d,0,1)
        pixels=pixels*(1-mask[:,:,None])+np.array([.62,.61,.57])*mask[:,:,None]
tid=texture('ff801-printed-carbon50',pixels)
printed=material('FF801 sparse pale reference print',carbon,color=(1,1,1),rough=.30,textures={'map':tid})
set_material(783,printed)

# Replace just the helmet shell inside the merged Gundam light-armour batch.
# Current independent source already includes the approved 80% head scale.
mini=ROOT/'rooms/yongwang-jiayuan/assets/shelf-gundam/shelf-gundam.blend'
with bpy.data.libraries.load(str(mini),link=False) as (src,dst):dst.objects=['helmet main shell']
part=dst.objects[0];assert part is not None
collection.objects.link(part);bpy.context.view_layer.update()
evaluated=part.evaluated_get(bpy.context.evaluated_depsgraph_get());part.data=evaluated.to_mesh().copy();evaluated.to_mesh_clear()
floor=json.loads((ROOT/'rooms/yongwang-jiayuan/history/inputs/viewer26-head-points.json').read_text())['floor']
points=[part.matrix_world@v.co-Vector((0,0,floor))for v in part.data.vertices]
tree=KDTree(len(points))
for i,p in enumerate(points):tree.insert(p,i)
tree.balance();body=obs[1253];body.data=body.data.copy();bm=bmesh.new();bm.from_mesh(body.data)
remove=[v for v in bm.verts if tree.find(v.co)[2]<4e-6];assert len(remove)>20,('Head mapping failed',len(remove))
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(body.data);bm.free()
sections=[(2.45,.125,.110),(2.49,.147,.128),(2.57,.157,.134),(2.65,.147,.122),(2.70,.125,.105),(2.732,.080,.065),(2.742,.012,.012)]
verts=[];faces=[];n=32
for z,rx,ry in sections:
    for j in range(n):
        a=math.tau*j/n;v=Vector((rx*math.cos(a),.030+ry*math.sin(a),z));verts.append(part.matrix_world@v-Vector((0,0,floor)))
for k in range(len(sections)-1):
    for j in range(n):faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
faces.extend([tuple(reversed(range(n))),tuple((len(sections)-1)*n+j for j in range(n))])
me=bpy.data.meshes.new('Gundam50 rounded cranial armour');me.from_pydata(verts,[],faces);me.update()
tmp=bpy.data.objects.new('Gundam50 head patch',me);collection.objects.link(tmp)
tmp.matrix_world=body.matrix_world.copy();me.materials.append(body.data.materials[0]);uv=me.uv_layers.new(name='UVMap')
for f in me.polygons:
    f.use_smooth=True
    for li in f.loop_indices:
        p=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(p.x,p.z)
activate(body);tmp.select_set(True);bpy.ops.object.join();finish_mesh(body)
bpy.data.objects.remove(part,do_unlink=True)

# Narrow the boxy temple pods and their round end-caps together, without
# disturbing eyes, V-fin, face mask or any body piece in the material batches.
names=['temple equipment pod','temple equipment pod.001','temple pod round end','temple pod round end.001']
with bpy.data.libraries.load(str(mini),link=False) as (src,dst):dst.objects=names
for part in dst.objects:
    assert part is not None
    collection.objects.link(part)
bpy.context.view_layer.update()
for part in dst.objects:
    evaluated=part.evaluated_get(bpy.context.evaluated_depsgraph_get());part.data=evaluated.to_mesh().copy();evaluated.to_mesh_clear()
    pts=[part.matrix_world@v.co-Vector((0,0,floor))for v in part.data.vertices]
    kd=KDTree(len(pts))
    for i,p in enumerate(pts):kd.insert(p,i)
    kd.balance();center=sum(pts,Vector())/len(pts)
    nid=1254 if part.name.startswith('temple equipment') else 1255
    o=obs[nid];o.data=o.data.copy();count=0
    for v in o.data.vertices:
        if kd.find(v.co)[2]<4e-6:
            p=v.co-center;p.x*=.86;p.y*=.92;p.z*=.90
            v.co=center+p+Vector((-.012 if center.x>0 else .012,0,0));count+=1
    assert count>10,('Temple mapping failed',part.name,count)
    finish_mesh(o);bpy.data.objects.remove(part,do_unlink=True)

# Source helper operates only on the specified chair nodes.
chair_ns={};exec(compile((HERE/'finish50-chair.py').read_text('utf8'),str(HERE/'finish50-chair.py'),'exec'),chair_ns)
chair_result=chair_ns['refine_chair50'](globals())
for nid in chair_result['nodes']:
    g=data['geometries'][data['nodes'][nid]['geometry']];g['attributes']['uv1']=copy.deepcopy(g['attributes']['uv'])

def replace(nid,name,verts,faces,mid,parent=None,smooth=True,uv=None):
    o=obs[nid];me=mesh(name,verts,faces,uv,smooth);o.data=me;o.modifiers.clear();o.name=name
    data['nodes'][nid]['name']=name;o['web_name']=name
    set_material(nid,mid);finish_mesh(o);return o

def set_world_origin(o,point):
    o.matrix_world=Matrix.Translation(Vector(bp(point)));bpy.context.view_layer.update()
    nid=int(o['web_node_id']);data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);changed.add(nid)

# Remove the long white bar; the original ceramic rear lip receives the tap.
o=obs[1503];o.data=bpy.data.meshes.new('Removed false basin rear bar');export(o);data['nodes'][1503]['visible']=False;o.hide_render=True
o=obs[1513];o.data=o.data.copy()
for v in o.data.vertices:
    if v.co.z<-.070:v.co.z-=.008
finish_mesh(o)

def bottle(nid,name,point,height,width,depth,profile,mid):
    vs=[];fs=[];n=64
    for y,r in profile:
        for j in range(n):
            a=math.tau*j/n;vs.append((width*.5*r*math.sin(a),height*y,-depth*.5*r*math.cos(a)))
    for k in range(len(profile)-1):
        for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    fs.extend([tuple(reversed(range(n))),tuple((len(profile)-1)*n+j for j in range(n))])
    o=replace(nid,name,vs,fs,mid);set_world_origin(o,point);return o

ivory=material('Toiletry50 warm white HDPE',105,color=(.88,.89,.87),rough=.46,textures={},metalness=0)
blue=material('Toiletry50 cobalt flip cap',105,color=(.035,.19,.60),rough=.29,textures={},metalness=0)
teal=material('Toiletry50 Rejoice blue bottle',105,color=(.39,.65,.72),rough=.37,textures={},metalness=0)
gold=material('Toiletry50 LUX rose gold pump',105,color=(.67,.47,.32),rough=.30,textures={},metalness=.25)
paper=material('Toiletry50 uncoated toilet tissue',105,color=(.86,.84,.77),rough=.94,textures={},metalness=0)

# The small-bottle references are a 170 g Rejoice and 200 g Safeguard; their
# proportions are taken from the provided fronts, not an invented CAD model.
rejoice=[(0,.66),(.025,.85),(.10,.94),(.70,1),(.82,.90),(.91,.56),(.94,.49),(1,.49)]
safeguard=[(0,.92),(.025,1),(.15,.93),(.40,.82),(.72,.86),(.80,.96),(.84,.94),(1,.94)]
lux=[(0,.9),(.03,1),(.76,1),(.83,.93),(.88,.65),(1,.30)]
bottle(1528,'Rejoice 170g travel bottle50',(-.32,1.6955,3.065),.166,.049,.032,rejoice,teal)
bottle(1529,'Safeguard 200g small bottle50',(-.25,1.6955,3.065),.174,.048,.030,safeguard,ivory)
bottle(1530,'LUX white pump bottle50',(-.22,2.0065,3.070),.195,.068,.040,lux,ivory)
# Former purple ring becomes the real blue cap on Safeguard, not a label band.
bottle(1531,'Safeguard blue flip cap50',(-.25,1.6955+.174*.84,3.065),.174*.16,.048,.030,[(0,.94),(.12,1),(.88,1),(1,.91)],blue)
bottle(1532,'LUX pump neck50',(-.22,2.2015,3.070),.022,.015,.015,[(0,1),(1,1)],gold)
# Pump spout built as a solid softly bevelled component with actual neck contact.
o=obs[1533];me=bpy.data.meshes.new('Lux pump spout50');bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
for v in bm.verts:v.co=Vector((v.co.x*.044,v.co.y*.015,v.co.z*.009))
bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.002,segments=3,affect='EDGES');bm.to_mesh(me);bm.free();o.data=me
if not me.uv_layers:me.uv_layers.new(name='UVMap')
set_material(1533,gold);set_world_origin(o,(-.235,2.223,3.070));finish_mesh(o)

def label(name,path,crop,nid,height,width,depth,profile,lo,hi):
    # Read only the user-provided visible label region; save the derived label
    # to source textures so no temporary/private reference path survives.
    im=bpy.data.images.load(str(path),check_existing=False);im.colorspace_settings.name='Non-Color';iw,ih=im.size
    arr=np.array(im.pixels[:]).reshape(ih,iw,4);x0,y0,x1,y1=crop
    crop_pixels=arr[ih-y1:ih-y0,x0:x1,:3];tid=texture(name,crop_pixels);bpy.data.images.remove(im)
    mid=material(name,ivory,color=(1,1,1),rough=.52,textures={'map':tid},metalness=0)
    vs=[];uv=[];fs=[];nx,ny=32,24
    for j in range(ny+1):
        y=lo+(hi-lo)*j/ny;r=np.interp(y,[a for a,b in profile],[b for a,b in profile])
        for i in range(nx+1):
            a=(i/nx*2-1)*.92;vs.append(((width*.5*r+.0007)*math.sin(a),height*y,-(depth*.5*r+.0007)*math.cos(a)));uv.append((i/nx,j/ny))
    for j in range(ny):
        for i in range(nx):k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
    o=attach(mesh(name,vs,fs,uv,True),name,mid,nid);export(o)
    data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]['attributes']['uv1']=copy.deepcopy(data['geometries'][data['nodes'][int(o['web_node_id'])]['geometry']]['attributes']['uv'])
inputs=json.loads((ROOT/'rooms/yongwang-jiayuan/history/inputs/finish50-products.json').read_text('utf8'))
for item in inputs:
    label(item['name'],ROOT/item['source'],item['crop'],item['node'],item['height'],item['width'],item['depth'],{'rejoice':rejoice,'safeguard':safeguard,'lux':lux}[item['profile']],item['lo'],item['hi'])

# Toilet roll has an actual open cardboard core and paper wall, not a cup.
vs=[];fs=[];n=64
for y,r in [(0,.038),(.102,.038),(.102,.0125),(0,.0125)]:
    for j in range(n):a=math.tau*j/n;vs.append((r*math.sin(a),y,r*math.cos(a)))
for k in range(4):
    for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,((k+1)%4)*n+(j+1)%n,((k+1)%4)*n+j))
o=replace(1534,'Toilet tissue roll with open core50',vs,fs,paper);set_world_origin(o,(.12,2.0065,3.070))

result=save('finish50',{'stage':'head, cap, close rear spoiler, continuous chair joins and photographed toiletries','parent':'fitting49','chair':chair_result,'dimensions':'photo/product-front estimates'})
