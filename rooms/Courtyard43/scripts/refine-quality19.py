"""interior18 -> 19: continuous quilt loft and gravity-released curtain folds.

Run only through official Blender Lab MCP. Anchors and supported outlines are
unchanged. Fold locations/thickness are photographic estimates, not measurements.
"""
import bpy, bmesh, math, json, hashlib, time
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
_log=ROOT/'analysis/Courtyard43/quality21/progress19.txt'
_log.parent.mkdir(parents=True,exist_ok=True)
def progress(label):
    with _log.open('a',encoding='utf-8') as f:f.write(str(time.time())+' '+label+'\n')
progress('start')
assert scene.get('web_revision')=='courtyard43-interior18'
bpy.context.preferences.filepaths.save_version=0
targets={'C43_FloralDuvet','C43_FloralDuvetSewnHem','C43_CottonPillow','C43_PillowPipedSeam','C43_Curtain_Left','C43_Curtain_Right'}
def digest(o):
    h=hashlib.sha256(repr((o.name,tuple(tuple(r) for r in o.matrix_world),o.parent.name if o.parent else None,dict(o.items()))).encode())
    if o.type=='MESH':
        h.update(repr(([tuple(v.co) for v in o.data.vertices],[(tuple(p.vertices),p.material_index) for p in o.data.polygons],[m.name for m in o.data.materials])).encode())
    return h.hexdigest()
progress('digest')
before={o.name:digest(o) for o in scene.objects if o.name not in targets}
def smooth(t):
    t=np.clip(t,0,1);return t*t*(3-2*t)
def replace(name,verts,faces,uv):
    obj=bpy.data.objects[name];old=obj.data;mesh=bpy.data.meshes.new(name+'_quality19')
    mesh.from_pydata(verts,[],faces);mesh.update()
    for m in old.materials:mesh.materials.append(m)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free()
    for ln,scale in [('UVMap',1),('UV1',24)]:
        layer=mesh.uv_layers.new(name=ln)
        for p in mesh.polygons:
            p.use_smooth=True
            for li in p.loop_indices:layer.data[li].uv=Vector(uv[mesh.loops[li].vertex_index])*scale
    obj.data=mesh
    return obj

# A compressed perimeter surrounds a broad lofted body. Long paired folds are
# crests AND troughs with tapered branches, rather than isolated added bumps.
progress('quilt')
nx,ny=112,88
def quilt(u,v):
    edge=(math.sin(math.pi*u)*math.sin(math.pi*v))**.55
    x=-1.389+1.788*u+.007*math.sin(v*8)*math.sin(math.pi*u)
    z=1.323+1.397*v+.008*math.sin(u*7)*math.sin(math.pi*v)
    q=v-(.27+.34*u+.065*math.sin(u*4))
    fold=.058*math.exp(-(q/.10)**2)-.027*math.exp(-((q-.115)/.075)**2)
    q2=v-(.81-.29*u)
    fold+=(.042*math.exp(-(q2/.078)**2)-.020*math.exp(-((q2+.082)/.055)**2))*float(smooth((u-.12)/.30))
    # Two small terminal tension lines die into the principal folds.
    fine=.013*math.exp(-((v-.22+.22*u)/.034)**2-((u-.19)/.22)**2)
    fine+=.011*math.exp(-((v-.70-.19*u)/.042)**2-((u-.82)/.22)**2)
    loft=.050+.021*math.sin(math.pi*u)*math.sin(math.pi*v)+fold+fine
    top=.576+edge*loft+.011*math.exp(-((u-.04)/.035)**2)*math.sin(math.pi*v)
    bottom=.5595+edge*(.002+.22*max(0,fold))
    return x,z,top,bottom
verts=[];uv=[]
for lower in (False,True):
    for j in range(ny+1):
        for i in range(nx+1):
            u,v=i/nx,j/ny;x,z,top,bottom=quilt(u,v)
            verts.append((x,-z,bottom if lower else top))
            # Preserve the accepted flower density in physical metres.
            uv.append((u*1.58/.78,v*1.22/.78))
n=(nx+1)*(ny+1);faces=[]
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;faces.extend([(k,k+1,k+nx+2,k+nx+1),(k+n,k+nx+1+n,k+nx+2+n,k+1+n)])
edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
for i,k in enumerate(edge):q=edge[(i+1)%len(edge)];faces.append((k,q,q+n,k+n))
o=replace('C43_FloralDuvet',verts,faces,uv);o['construction']='Lofted cotton envelope, compressed perimeter and paired tapered folds; quality19'
o['cloth_thickness_m']=.0165
# Bound edge follows the exact perimeter; it is neither floating embroidery nor
# a constant-offset second blanket. Five-sided fine piping is sufficient here.
path=[]
for k in edge:
    j,i=divmod(k,nx+1);x,z,top,bottom=quilt(i/nx,j/ny);path.append(Vector((x,-z,top-.003)))
sv=[];sf=[];suv=[]
for i,p in enumerate(path):
    tangent=(path[(i+1)%len(path)]-path[i-1]).normalized();a=tangent.cross(Vector((0,0,1))).normalized();b=tangent.cross(a)
    for s in range(6):sv.append(p+.0011*(a*math.cos(s*math.tau/6)+b*math.sin(s*math.tau/6)));suv.append((i/len(path),s/6))
for i in range(len(path)):
    for s in range(6):sf.append((i*6+s,i*6+(s+1)%6,((i+1)%len(path))*6+(s+1)%6,((i+1)%len(path))*6+s))
replace('C43_FloralDuvetSewnHem',sv,sf,suv)

# Shared deformation keeps existing pillow/piping registered. Compression is
# zero at support and confined to upper fabric; corners retain visible slack.
for name in ('C43_CottonPillow','C43_PillowPipedSeam'):
    o=bpy.data.objects[name];o.data=o.data.copy();inv=o.matrix_world.inverted()
    for vertex in o.data.vertices:
        p=o.matrix_world@vertex.co;x,z,h=p.x,-p.y,p.z
        weight=float(smooth((h-.558)/.06))
        dent=.009*math.exp(-((x+1.72)/.16)**2-((z-2.04)/.24)**2)
        p.z-=weight*dent
        p.z+=weight*.0023*math.sin((z-1.7)*29)*math.exp(-((x+1.54)/.035)**2)
        vertex.co=inv@p
    o.data.update()

progress('curtain')
for side in ('Left','Right'):
    o=bpy.data.objects['C43_Curtain_'+side];o.data=o.data.copy();keys=o.data.shape_keys.key_blocks
    for keyname in ('Basis','Open'):
        block=keys[keyname];old=np.array([tuple(p.co) for p in block.data]);count=121*65
        center=((old[:count]+old[count:])*.5).reshape(65,121,3)
        new=center.copy();opened=keyname=='Open'
        for row in range(65):
            v=row/64
            for col in range(121):
                a=col/120
                # Pin header and overlap edges exactly. Fold spacing diverges
                # gently under gravity; narrow gathered crests open into wider
                # troughs with unequal amplitudes, not a corrugated extrusion.
                release=float(smooth((v-.035)/.16))
                edgefade=float(smooth(a/.08)*smooth((1-a)/.08))
                phase=math.tau*(5*a+.14*math.sin(a*6.3)+.055*v*math.sin(a*9+1))
                shape=math.cos(phase)+.23*math.cos(2*phase+.35)
                amp=(.034 if opened else .026)*(1+.18*math.sin(a*13+.5))
                depth=.063+amp*shape+.006*math.sin(a*8+v*2)*v
                blend=release*edgefade
                new[row,col,1]=center[row,col,1]*(1-blend)-depth*blend
                # Subtle lateral fall: widest toward hem, zero at supported ends.
                new[row,col,0]+=blend*.007*math.sin(a*math.tau*2.1+v)*v
        # Recompute the actual shell normal after reshaping, including hems.
        dv,du=np.gradient(new,axis=(0,1));normal=np.cross(du,dv)
        normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-10)
        for row in range(65):
            for col in range(121):
                i=row*121+col;a=col/120;v=row/64
                weight=float(smooth((v-.035)/.10)*smooth(a/.055)*smooth((1-a)/.055))
                half=(old[i]-old[i+count])*.5
                hn=normal[row,col]*.0019
                if np.dot(hn,half)<0:hn=-hn
                hn*=1+.70*float(smooth((v-.962)/.038))
                offset=half*(1-weight)+hn*weight
                block.data[i].co=new[row,col]+offset;block.data[i+count].co=new[row,col]-offset
    for vertex,basis in zip(o.data.vertices,keys['Basis'].data):vertex.co=basis.co
    o.data.update();o['quality19']='Unequal gathered folds released below unchanged header; normal-offset closed shell'

progress('verify')
assert before=={o.name:digest(o) for o in scene.objects if o.name not in targets},'Non-target object changed'
scene['parent_web_revision']='courtyard43-interior18';scene['web_revision']='courtyard43-interior19'
scene['quality19_targets']=json.dumps(sorted(targets))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text(encoding='utf-8'),ns['__file__'],'exec'),ns)
progress('save')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
progress('export')
if globals().get('EXPORT',True):ns['export_interior']()
progress('done')
result={'revision':scene['web_revision'],'targets':sorted(targets),'nonTargetsUnchanged':len(before)}
