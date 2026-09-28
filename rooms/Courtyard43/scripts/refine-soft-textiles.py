"""Second textile pass; official Blender Lab MCP only.

Run on furniture04, architecture06, then interior05. No room anchors change.
Photos P03/P04 establish shapes, not measured seams, folds or transmission.
All generated maps are neutral material information, without baked lighting.
"""
import bpy
import bmesh
import numpy as np
import math
import json
import hashlib
import struct
import zlib
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
kind=scene.get('component')
full=scene.get('stage')=='interior' and kind not in ('architecture','furniture')
if full: assert scene.get('web_revision')=='courtyard43-interior05'
elif kind=='architecture': assert scene.get('component_revision')=='architecture06'
elif kind=='furniture': assert scene.get('component_revision')=='courtyard43-furniture04'
else: raise AssertionError(dict(scene.items()))
if kind=='furniture':
    approved=json.loads((ROOM/'history/inputs/approved-layout.json').read_text(encoding='utf-8'))
    assert scene['approved_layout_commit']==approved['approval']['baselineCommit']
else:
    assert scene['source_layout']=='courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version=0
BED=['C43_DrapedWhiteSheet','C43_DrapedWhiteSheetSewnHem','C43_FloralDuvet',
     'C43_FloralDuvetSewnHem','C43_CottonPillow','C43_PillowPipedSeam']
CURTAINS=['C43_Curtain_'+side+suffix for side in ('Left','Right') for suffix in ('','_Rings')]
targets=set((BED if full or kind=='furniture' else [])+(CURTAINS if full or kind=='architecture' else []))

def digest(o):
    h=hashlib.sha256(repr((o.name,tuple(tuple(r) for r in o.matrix_world),
        o.parent.name if o.parent else None,dict(o.items()))).encode())
    if o.type=='MESH':
        h.update(repr(([tuple(v.co) for v in o.data.vertices],
            [(tuple(p.vertices),p.material_index) for p in o.data.polygons],
            [(u.name,[tuple(d.uv) for d in u.data]) for u in o.data.uv_layers],
            [m.name for m in o.data.materials])).encode())
    return h.hexdigest()

before={o.name:digest(o) for o in scene.objects if o.name not in targets}

def web(v): return (v[0],-v[1],v[2])
def bp(p): return (p[0],-p[2],p[1])
def smooth(x):
    x=np.clip(x,0,1)
    return x*x*(3-2*x)

def image_png(path,rgb):
    # Explicit PNG byte encoding avoids generated Image.save color ambiguity.
    rgb=np.rint(np.clip(rgb,0,1)*255).astype(np.uint8)
    h,w=rgb.shape[:2]
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))
    data+=chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in rgb),6))+chunk(b'IEND',b'')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)
    im=bpy.data.images.load(str(path),check_existing=False)
    im.name='C43_'+path.stem
    im.colorspace_settings.name='sRGB'
    return im

def independent_material(name,source):
    m=bpy.data.materials[source].copy();m.name=name
    return m,next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')

def replace_mesh(name,verts,faces,mat,uvs=None,uv1s=None,opened=None):
    o=bpy.data.objects[name]
    inv=o.matrix_world.inverted()
    local=[inv@Vector(bp(v)) for v in verts]
    m=bpy.data.meshes.new(name+'_Textile06')
    m.from_pydata(local,[],faces);m.materials.append(mat);m.update()
    bm=bmesh.new();bm.from_mesh(m)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:
        bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(m);bm.free()
    for layer_name,values in [('UVMap',uvs),('UV1',uv1s)]:
        layer=m.uv_layers.new(name=layer_name)
        for p in m.polygons:
            p.use_smooth=True
            for li in p.loop_indices:
                vi=m.loops[li].vertex_index
                layer.data[li].uv=values[vi] if values is not None else (verts[vi][0],verts[vi][2])
    o.data=m
    if opened is not None:
        o.shape_key_add(name='Basis')
        key=o.shape_key_add(name='Open')
        for v,p in zip(key.data,opened):v.co=inv@Vector(bp(p))
        key.value=0
    return o

def tube_arrays(paths,radius=.00065,sides=6):
    vertices=[];faces=[]
    for path in paths:
        start=len(vertices);pts=[Vector(p) for p in path];n=len(pts)
        for i,p in enumerate(pts):
            tangent=(pts[(i+1)%n]-pts[(i-1)%n]).normalized()
            axis=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
            a=tangent.cross(axis).normalized();b=tangent.cross(a).normalized()
            vertices.extend(tuple(p+radius*(math.cos(j*math.tau/sides)*a+math.sin(j*math.tau/sides)*b)) for j in range(sides))
        for i in range(n):
            for j in range(sides):faces.append(tuple(start+k for k in [i*sides+j,i*sides+(j+1)%sides,((i+1)%n)*sides+(j+1)%sides,((i+1)%n)*sides+j]))
    return vertices,faces

def bend(value,lo,hi,radius):
    if lo<=value<=hi:return value,0
    side=-1 if value<lo else 1;edge=lo if side<0 else hi
    excess=abs(value-edge);arc=min(excess/radius,math.pi/2)
    rest=max(0,excess-radius*math.pi/2)
    return edge+side*(radius*math.sin(arc)+rest*.045),radius*(1-math.cos(arc))+rest

def bed_surface(kind,u,v):
    if kind=='sheet':
        sx=-1.918+u*2.620;sz=1.04+v*1.745
        x,dx=bend(sx,-1.94,.425,.028);z,dz=bend(sz,1.292,2.768,.023)
        drop=math.hypot(dx,dz);hang=float(smooth(drop/.08))
        # Geometry supplies hanging folds; no photographed crease in albedo.
        phase=sx*13+.7*math.sin(sx*4.1)
        z-=hang*(.007*math.sin(phase)+.003*math.sin(phase*1.8+.4))*(dz>0)
        x+=hang*(.007*math.sin(sz*15+.3)+.003*math.sin(sz*27))*(dx>0)
        y=.5575-drop+hang*(.009*math.sin(sx*8+sz*3)+.004*math.sin(sx*17-sz*2))
        return (x,y,z)
    sx=-1.47+u*2.06+.11*math.exp(-u/.027)+.018*math.sin(v*7+.6)*(1-u)**6
    sz=1.15+v*1.65+.012*math.sin(u*8)*math.sin(math.pi*v)
    x,dx=bend(sx,-1.93,.436,.038);z,dz=bend(sz,1.277,2.783,.032)
    drop=math.hypot(dx,dz);release=math.exp(-drop*7)
    q1=sx+.84-.46*(sz-2.03)-.05*math.sin(sz*5)
    q2=sx+.05+.68*(sz-2.03)+.06*math.sin(sz*3.5)
    q3=sz-1.58+.18*sx+.025*math.sin(sx*7)
    folds=.086*math.exp(-(q1/.075)**2)*(.45+.55*math.exp(-((sz-1.97)/.55)**2))
    folds+=.073*math.exp(-(q2/.085)**2)*(.35+.65*math.exp(-((sz-2.26)/.38)**2))
    folds+=.036*math.exp(-(q3/.07)**2)*math.exp(-((sx+.52)/.65)**2)
    folds+=.023*math.exp(-((sx+1.10)/.22)**2-((sz-2.31)/.22)**2)
    # Short secondary creases terminate into the broad folds, rather than
    # repeating a regular corrugation across the entire bed.
    for q,along,center,span,amplitude in [
        (sx+1.12+.35*(sz-1.7),sz,1.65,.34,.022),
        (sx+.54-.42*(sz-2.05),sz,2.20,.42,.024),
        (sz-2.33+.26*(sx+.2),sx,-.25,.50,.021),
        (sx-.19+.5*(sz-1.55),sz,1.5,.27,.027)]:
        folds+=amplitude*math.exp(-(q/.033)**2-((along-center)/span)**2)
    broad=.003*(1+math.sin(sx*3+sz*2))+.002*(1+math.sin(sz*5-sx))
    turnover=.058*math.exp(-((u-.025)/.037)**2)*(.85+.15*math.sin(v*9))
    lift=float(smooth(drop/.06))*(.023*math.exp(-((sx+.57)/.24)**2)+.013*math.exp(-((sz-2.19)/.25)**2))
    y=.574+release*(folds+broad+turnover)-drop+lift
    hang=float(smooth(drop/.055))
    z-=hang*.008*math.sin(sx*8+.4)*(dz>0)
    # Keep the outer quilt outside the independently rippled sheet at the foot.
    x+=hang*.006*math.sin(sz*9+.8)*(dx>0)+.018*float(smooth(dx/.025))
    return (x,y,z)

def bed_shell(name,kind,nx,ny,thickness,mat,seam_mat):
    surface=np.array([[bed_surface(kind,i/nx,j/ny) for i in range(nx+1)] for j in range(ny+1)])
    tv,tu=np.gradient(surface,axis=(0,1));normal=np.cross(tv,tu)
    normal/=np.maximum(np.linalg.norm(normal,axis=2,keepdims=True),1e-12)
    upper=surface.reshape(-1,3);lower=(surface-normal*thickness).reshape(-1,3)
    verts=np.concatenate([upper,lower]).tolist();n=len(upper);faces=[]
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i
            faces.extend([(k,k+nx+1,k+nx+2,k+1),(k+n,k+1+n,k+nx+2+n,k+nx+1+n)])
    edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    for i,k in enumerate(edge):
        q=edge[(i+1)%len(edge)];faces.append((k,q,q+n,k+n))
    repeat=1/.78 if kind=='duvet' else 1
    uv=[(i/nx*(1.58 if kind=='duvet' else 2.2)*repeat,j/ny*(1.22 if kind=='duvet' else 1.5)*repeat) for j in range(ny+1) for i in range(nx+1)]
    thread=[(q[0]*24/repeat,q[1]*24/repeat) for q in uv]
    obj=replace_mesh(name,verts,faces,mat,uv+uv,thread+thread)
    obj['cloth_thickness_m']=thickness
    obj['construction']='Closed cotton shell; curved local accumulation, edge turnover and gravity-released drape'
    # Two close-set fine stitch lines follow the SAME surface, not detached cords.
    paths=[]
    for inset in ([.006,.012] if kind=='duvet' else [.005]):
        pad=inset/2;path=[]
        for k in edge:
            j,i=divmod(k,nx+1);u=pad+(1-2*pad)*i/nx;v=pad+(1-2*pad)*j/ny
            p=np.array(bed_surface(kind,u,v))
            p+=normal[j,i]*.00025
            path.append(p)
        paths.append(path)
    sv,sf=tube_arrays(paths,.00055 if kind=='sheet' else .0007)
    replace_mesh(name+'SewnHem',sv,sf,seam_mat)
    return obj

def refine_bed():
    mat,p=independent_material('C43_Textile_PlainCotton','C43_PlainCotton')
    v,u=np.mgrid[0:256,0:256]
    rng=np.random.default_rng(4306)
    grain=.0015*np.sin(u*math.pi)+.0014*np.sin(v*math.pi)+rng.normal(0,.0009,(256,256))
    rgb=np.array([.913,.905,.881])[None,None,:]+grain[:,:,None]
    im=image_png(ROOM/'assets/furniture/textures/plain-cotton-textile06.png',rgb)
    color=p.inputs['Base Color'].links[0].from_node;color.image=im
    p.inputs['Roughness'].default_value=.91
    p.inputs['Sheen Weight'].default_value=.25;p.inputs['Sheen Tint'].default_value=(.75,.73,.68,1)
    floral,fp=independent_material('C43_Textile_FloralCotton','C43_FloralCotton')
    fp.inputs['Roughness'].default_value=.88
    fp.inputs['Sheen Weight'].default_value=.25;fp.inputs['Sheen Tint'].default_value=(.75,.73,.68,1)
    seam,sp=independent_material('C43_Textile_SewnThread','C43_CottonSeam')
    sp.inputs['Base Color'].default_value=(.74,.715,.66,1)
    bed_shell('C43_DrapedWhiteSheet','sheet',94,68,.0018,mat,seam)
    bed_shell('C43_FloralDuvet','duvet',132,104,.009,floral,seam)
    # Preserve the accepted pillow mesh; soften asymmetrically using one field
    # on pillow and piping, ensuring their connection remains exact.
    for name in ('C43_CottonPillow','C43_PillowPipedSeam'):
        obj=bpy.data.objects[name];obj.data=obj.data.copy();inv=obj.matrix_world.inverted()
        for v in obj.data.vertices:
            p=obj.matrix_world@v.co;x,y,z=p.x,p.z,-p.y
            height=y-.5618
            compression=.004*math.exp(-((x+1.70)/.10)**2-((z-2.06)/.16)**2)*float(smooth(height/.08))
            y=.5578+height*.94-compression
            x+=.005*math.sin((z-1.7)*8)*float(smooth(height/.12))
            v.co=inv@Vector((x,-z,y))
        obj.data.materials[0]=mat if name.endswith('CottonPillow') else seam
        obj['textile06']='Shared gentle compression of pillow and existing piped edge; independent cotton material'

def curtain_surface(a,v,side,opened):
    width=.165 if opened else (.872 if side=='Left' else 1.196)
    start=-.63 if side=='Left' else 1.43-width
    x=start+a*width
    x+=.004*math.sin(math.pi*a)**2*math.sin(math.pi*v)*math.sin(a*13+v*2)*(0.15 if opened else 1)
    pin=(a-.016)/.0968
    top=2.399-.0065*math.sin(math.pi*pin)**2
    # Small hem variations, all above their actual support surfaces.
    bottom=(.0505 if side=='Left' else 1.018)+.0035*math.sin(a*11+.5)+.0015*math.sin(a*23)
    y=top+(bottom-top)*v
    phase=a*math.tau*(5.5 if side=='Left' else 6)+.16*math.sin(a*17)+.24*v*math.sin(a*11+.4)
    if opened:
        depth=.066+.034*math.cos(a*math.tau*5)+.003*math.sin(a*19+v*4)*v
    else:
        depth=.064+.029*math.cos(phase)+.008*math.cos(2*phase+.55)
        depth+=.005*math.sin(a*8+v*3)*math.sin(math.pi*v)
        # Overlapping meeting edges occupy different depths, preventing a seam slit.
        if side=='Left':depth=depth*(1-float(smooth((a-.94)/.06)))+.102*float(smooth((a-.94)/.06))
        else:depth=depth*float(smooth(a/.06))+.081*(1-float(smooth(a/.06)))
    header=.072+.009*math.sin(math.tau*pin)
    release=float(smooth(v/.065))
    z=header*(1-release)+depth*release
    return (x,y,z)

def refine_curtain(side):
    name='C43_Curtain_'+side;old=bpy.data.objects[name]
    mat,p=independent_material('C43_Textile_Grey_'+side,old.data.materials[0].name)
    p.inputs['Roughness'].default_value=.79
    p.inputs['Sheen Weight'].default_value=.38;p.inputs['Sheen Roughness'].default_value=.72
    p.inputs['Sheen Tint'].default_value=(.40,.41,.42,1)
    normal=next(n for n in mat.node_tree.nodes if n.type=='NORMAL_MAP')
    normal.inputs['Strength'].default_value=.19
    p.inputs['Emission Strength'].default_value=.045
    meta=json.loads(mat.get('web_userData','{}'));meta['curtainDiffuseTransmission']=True
    mat['web_userData']=json.dumps(meta)
    # Normalized seam/thickness mask uses UV1 and contains no room illumination.
    v,u=np.mgrid[0:256,0:256]/255
    width=.872 if side=='Left' else 1.196;height=2.399-(.0505 if side=='Left' else 1.018)
    edge=np.minimum(u,1-u)*width
    weight=(.18+.82*smooth(edge/.023))*(.2+.8*smooth(v*height/.07))*(.23+.77*smooth((1-v)*height/.045))
    im=image_png(ROOM/('assets/architecture/textures/cloth-sewn-transmission-'+side.lower()+'-06.png'),np.repeat(weight[:,:,None],3,axis=2))
    tex=next(n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.get('web_map')=='emissiveMap')
    tex.image=im
    for link in list(tex.inputs['Vector'].links):mat.node_tree.links.remove(link)
    uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UV1'
    mat.node_tree.links.new(uvnode.outputs['UV'],tex.inputs['Vector'])
    nx,ny=120,64;n=(nx+1)*(ny+1)
    verts=[];opened=[];uv=[];uv1=[];faces=[]
    for sign in (1,-1):
        for j in range(ny+1):
            for i in range(nx+1):
                a,v=i/nx,j/ny
                hem=1+.8*(1-float(smooth(min(a,1-a)*width/.018)))
                hem+=1.3*(1-float(smooth(min(v*height/.045,(1-v)*height/.03))))
                for points,state in ((verts,False),(opened,True)):
                    x,y,z=curtain_surface(a,v,side,state);points.append((x,y,z+sign*.00085*hem))
                uv.append((a*width,v*height));uv1.append((a,v))
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i
            faces.extend([(k,k+1,k+nx+2,k+nx+1),(n+k,n+k+nx+1,n+k+nx+2,n+k+1)])
    edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    for i,k in enumerate(edge):
        q=edge[(i+1)%len(edge)];faces.append((k,k+n,q+n,q))
    obj=replace_mesh(name,verts,faces,mat,uv,uv1,opened)
    obj['construction']='Unequal gravity pleats, sewn header/side/bottom thickness, overlapping central edge and support-following hem'
    obj['cloth_thickness_m']=.0017
    user=json.loads(obj['web_userData']);user['fixedTop']=2.399
    obj['web_userData']=json.dumps(user)
    # Rings retain round sections in both states; lower ring tangents meet header.
    ringverts=[];ringopen=[];ringfaces=[]
    for a in np.linspace(.016,.984,11):
        base=len(ringverts)
        for j in range(20):
            angle=j/20*math.tau
            for k in range(8):
                phi=k/8*math.tau;r=.025+.0023*math.cos(phi)
                for arr,state in ((ringverts,False),(ringopen,True)):
                    x,_,_=curtain_surface(float(a),0,side,state)
                    arr.append((x+.0023*math.sin(phi),2.425+r*math.cos(angle),.072+r*math.sin(angle)))
        for j in range(20):
            for k in range(8):ringfaces.append(tuple(base+jj*8+kk for jj,kk in [(j,k),((j+1)%20,k),((j+1)%20,(k+1)%8),(j,(k+1)%8)]))
    ringmat=bpy.data.objects[name+'_Rings'].data.materials[0]
    replace_mesh(name+'_Rings',ringverts,ringfaces,ringmat,opened=ringopen)

if full or kind=='furniture':refine_bed()
if full or kind=='architecture':
    for side in ('Left','Right'):refine_curtain(side)
bpy.context.view_layer.update()
assert before=={o.name:digest(o) for o in scene.objects if o.name in before}
checks=[]
for name in sorted(targets):
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
    assert not any(not e.is_manifold for e in bm.edges),name
    assert not any(f.calc_area()<1e-14 for f in bm.faces),name
    volume=bm.calc_volume(signed=True);assert volume>0,(name,volume)
    checks.append({'name':name,'volume':volume,'vertices':len(o.data.vertices)})
    bm.free()
if full:
    scene['parent_web_revision']='courtyard43-interior05';scene['web_revision']='courtyard43-interior06'
    records=json.loads(scene['components'])
    for r in records:
        if r['component'] in ('architecture','furniture'):r['sha256']=hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest()
    scene['components']=json.dumps(records)
    output=ROOM/'assets/full-room/Courtyard43-interior.blend'
else:
    scene['component_parent_revision']=scene['component_revision']
    scene['component_revision']='architecture07' if kind=='architecture' else 'courtyard43-furniture05'
    output=ROOM/f'assets/{kind}/Courtyard43-{kind}.blend'
scene['textile06']='P03/P04 cloth refinement; manufactured details and transmission remain photo estimates'
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:
        absolute=bpy.path.abspath(im.filepath,library=im.library)
        im.filepath=bpy.path.relpath(absolute,start=str(output.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(output))
result={'saved':str(output),'unchangedObjects':len(before),'checks':checks}
if full:
    p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'export'}
    exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope)
    result['export']=scope['export_interior']()
