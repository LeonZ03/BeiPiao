"""interior09 -> interior10. Execute ONLY through official Blender Lab MCP.

One spatial winter exterior, inferred proportions from the user's snow photo
and V01; no measured distances or invented room interiors. Existing approved
room geometry is retained. Only two obsolete distant facade proxies are hidden.
"""
from pathlib import Path
import bpy, json, math, random, shutil, hashlib
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'; ASSET=ROOM/'assets/winter-exterior'
ASSET.mkdir(parents=True,exist_ok=True);(ASSET/'textures').mkdir(exist_ok=True)
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior09'
assert not any(o.name.startswith('C43_ZWinter') for o in scene.objects)
bpy.context.preferences.filepaths.save_version=0
rng=random.Random(43010)
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
# Read the accepted full-scene material, not an outdated isolated generator.
with bpy.data.libraries.load(str(source),link=False) as (src,dst):
    dst.materials=['Courtyard · mineral grey render']
reused=dst.materials[0]
assert reused and reused.use_nodes
images={}
for n in reused.node_tree.nodes:
    if n.type=='TEX_IMAGE' and n.image:
        original=Path(bpy.path.abspath(n.image.filepath))
        if not original.is_file():
            original=source.parent/'textures'/Path(n.image.filepath).name
        assert original.is_file(),str(original)
        target=ASSET/'textures'/original.name
        shutil.copyfile(original,target)
        im=bpy.data.images.load(str(target),check_existing=False)
        im.colorspace_settings.name=n.image.colorspace_settings.name
        images[original.stem]=im
assert 'exterior31-mineral-render' in images

def lin(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def mat(name,color,rough=.8,metal=0,textured=False,emission=0):
    m=bpy.data.materials.new('C43_ZWinter_'+name);m.use_nodes=True
    m.node_tree.nodes.clear()
    bs=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    out=m.node_tree.nodes.new('ShaderNodeOutputMaterial')
    m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface'])
    bs.inputs['Base Color'].default_value=(*[lin(c) for c in color],1)
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    # Small constant diffuse sky contribution for the unshadowed exterior;
    # prevents indoor curtain-controlled fill from turning distant facades black.
    if emission:
        bs.inputs['Emission Color'].default_value=(*[lin(c) for c in color],1);bs.inputs['Emission Strength'].default_value=emission
    m['web_userData']=json.dumps({'winterExterior':True})
    if textured:
        tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images['exterior31-mineral-render']
        m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        m['web_props']=json.dumps({'color':[lin(c)/lin(.58) for c in color]})
        if 'exterior31-render-relief' in images:
            tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=images['exterior31-render-relief']
            bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.001
            m.node_tree.links.new(tx.outputs['Color'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    return m
materials={
 'plaster':mat('BeigePink_Plaster',(.64,.59,.54),textured=True,emission=.12),
 'cream':mat('Old_Cream_Plaster',(.70,.69,.63),textured=True,emission=.12),
 'rightwall':mat('Muted_Pink_Wall',(.66,.60,.57),textured=True,emission=.12),
 'yellow':mat('Distant_Pale_Yellow',(.71,.68,.51),textured=True,emission=.12),
 'concrete':mat('Concrete',(.44,.45,.43),textured=True,emission=.1),
 'trim':mat('Ivory_Window_Frames',(.75,.77,.75),.45,.12,emission=.1),
 'rusttrim':mat('Dull_Red_Window_Trim',(.40,.27,.24),.82,emission=.1),
 'metal':mat('Weathered_Galvanized_Steel',(.31,.34,.34),.55,.45,emission=.07),
 'dark':mat('Recess_and_Rubber',(.10,.12,.12),.84,emission=.12),
 'bark':mat('Winter_Bark',(.31,.29,.26),.92,emission=.12),
 'snow':mat('Settled_Snow',(.91,.94,.95),.92,emission=.23),
 'ground':mat('Damp_Ground',(.26,.28,.28),.95,emission=.1),
 'vehicle':mat('Parked_Scooter_Paint',(.23,.26,.26),.43,.08,emission=.1),
 'seat':mat('Scooter_Seats',(.13,.12,.12),.9,emission=.1),
}
for i,c in enumerate([(.30,.36,.38),(.38,.42,.41),(.24,.28,.29),(.47,.49,.46)]):materials['glass'+str(i)]=mat('Recessed_Glass_'+str(i),c,.28,.18,emission=.12)
col=bpy.data.collections.new('C43_ZWinter');scene.collection.children.link(col)
root=bpy.data.objects.new('C43_ZWinter',None);col.objects.link(root)
root['web_tags']=json.dumps({'cutaway':True,'noCollision':True})
root['web_userData']=json.dumps({'winterExterior':True,'dimensionSource':'photo estimate'})
# Accumulate meshes by spatial region and material before export. No thousands
# of scene nodes, per-window reflectors, or per-frame instance uploads.
buckets={}
def add(group,material,verts,faces,smooth=False):
    key=(group,material);vs,fs,sm=buckets.setdefault(key,([],[],[]));start=len(vs)
    vs.extend((p[0],-p[2],p[1]) for p in verts)
    fs.extend(tuple(start+i for i in f) for f in faces);sm.extend([smooth]*len(faces))
def box(g,m,p,s):
    x,y,z=p;a,b,c=[v/2 for v in s]
    vs=[(x+dx*a,y+dy*b,z+dz*c) for dx,dy,dz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    add(g,m,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)])
def tube(g,m,a,b,r,n=7,r2=None):
    a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,1,0)) if abs(d.y)<.95 else Vector((1,0,0))).normalized();v=d.cross(u)
    verts=[tuple(p+radius*(u*math.cos(j*math.tau/n)+v*math.sin(j*math.tau/n))) for p,radius in [(a,r),(b,r if r2 is None else r2)] for j in range(n)]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    add(g,m,verts,faces,True)
def oval(g,m,p,s,segments=12,rings=6):
    vs=[(p[0],p[1]-s[1],p[2])]
    for j in range(1,rings):
        phi=-math.pi/2+math.pi*j/rings
        for i in range(segments):
            a=i*math.tau/segments;vs.append((p[0]+s[0]*math.cos(phi)*math.cos(a),p[1]+s[1]*math.sin(phi),p[2]+s[2]*math.cos(phi)*math.sin(a)))
    top=len(vs);vs.append((p[0],p[1]+s[1],p[2]))
    fs=[(0,1+i,1+(i+1)%segments) for i in range(segments)]
    for j in range(rings-2):
        for i in range(segments):
            a=1+j*segments+i;b=1+j*segments+(i+1)%segments;fs.append((a,a+segments,b+segments,b))
    fs += [(top,1+(rings-2)*segments+(i+1)%segments,1+(rings-2)*segments+i) for i in range(segments)]
    add(g,m,vs,fs,True)
def snow_sheet(g,x0,x1,z0,z1,base,thickness=.07,nx=70,nz=10,wave=0):
    vs=[]
    for top in [True,False]:
        for j in range(nz+1):
            z=z0+(z1-z0)*j/nz
            for i in range(nx+1):
                x=x0+(x1-x0)*i/nx;under=base+wave*math.cos(x*math.tau/.19)
                depth=thickness*(1+.16*math.sin(x*4.1+z*2.2)+.06*math.sin(x*13.7-z*7))
                vs.append((x,under+(depth if top else -.003),z))
    count=(nx+1)*(nz+1);fs=[]
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i;b=a+1;c=b+nx+1;d=a+nx+1
            fs.extend([(a,d,c,b),(a+count,b+count,c+count,d+count)])
    perimeter=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,nz+1)]+[nz*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(nz-1,0,-1)]
    for a,b in zip(perimeter,perimeter[1:]+perimeter[:1]):fs.append((a,b,b+count,a+count))
    add(g,'snow',vs,fs,True)

# The near safety canopy is open real mesh, not an alpha plane or solid snow.
for i in range(185):
    x=-6.8+i*.075;tube('Canopy','metal',(x,-.55,-1.28),(x,-.55,-6.35),.0038,5)
for i in range(69):
    z=-1.28-i*.075;tube('Canopy','metal',(-6.8,-.542,z),(7,-.542,z),.0038,5)
for x in [-6.8,-3.5,0,3.5,7]:
    tube('Canopy','metal',(x,-.57,-1.28),(x,-.57,-6.4),.035,9)
    tube('CanopySnow','snow',(x,-.532,-1.28),(x,-.532,-6.4),.034,10)
for z in [-1.30,-3.8,-6.4]:
    tube('Canopy','metal',(-6.8,-.57,z),(7,-.57,z),.035,9)
    tube('CanopySnow','snow',(-6.8,-.532,z),(7,-.532,z),.034,10)
for x in [-6.6,6.8]:tube('Canopy','metal',(x,-3.12,-5.9),(x,-.57,-5.9),.04,8)

# Two roofs form separate depth layers below the housing facade.
box('LowRoof','concrete',(.1,-1.80,-9.68),(22,2.55,2.8))
box('LowRoof','concrete',(.1,-.44,-9.68),(22.3,.18,3.06))
snow_sheet('LowRoofSnow',-11.05,11.25,-11.21,-8.15,-.35,.10,80,10)
for x in [-9.3,-5.7,-2.1,1.5,5.1,8.7]:
    box('LowRoof','dark',(x,-1.15,-8.26),(2.7,.73,.055))
    for xx in [x-1.35,x,x+1.35]:box('LowRoof','metal',(xx,-1.15,-8.22),(.035,.75,.05))
box('CorrugatedRoof','metal',(.1,-.51,-7.27),(21,.14,1.74))
snow_sheet('CorrugatedRoofSnow',-10.4,10.6,-8.14,-6.4,-.43,.10,220,5,.023)
for x in [-10.4,10.6]:tube('LowRoof','metal',(x,-2.8,-8.06),(x,-.51,-8.06),.045,8)
for k in range(3):
    z=-8.07-k*.035
    # Sagging utility cable pinned at both ends, not floating straight rods.
    pts=[(-10+i, -.58-.12*math.sin(math.pi*i/20),z) for i in range(21)]
    for a,b in zip(pts,pts[1:]):tube('LowRoof','dark',a,b,.008,5)
box('Ground','ground',(0,-3.22,-13),(37,.2,29))
snow_sheet('GroundSnow',-16,16,-27,-1.3,-3.117,.027,40,35)

def window(g,x,y,z,w,h,glass=0,bars=False,red=False):
    # Glass lies behind a 14 cm deep, open reveal. Wall is split around it.
    box(g,'dark',(x,y,z-.13),(w+.035,h+.035,.055))
    box(g,'glass'+str(glass),(x,y,z-.089),(w-.09,h-.09,.025))
    for xx in [x-w/2,x+w/2]:box(g,'rusttrim' if red else 'trim',(xx,y,z),(.065,h+.13,.16))
    for yy in [y-h/2,y+h/2]:box(g,'rusttrim' if red else 'trim',(x,yy,z),(w+.065,.065,.16))
    sections=max(2,round(w/.57))
    for i in range(1,sections):box(g,'trim',(x-w/2+w*i/sections,y,z-.018),(.035,h,.055))
    box(g,'trim',(x,y+h*.15,z-.018),(w,.035,.055))
    box(g,'concrete',(x,y-h/2-.065,z+.06),(w+.16,.09,.29))
    box(g,'snow',(x,y-h/2-.014,z+.073),(w+.12,.022,.25))
    if bars:
        for i in range(1,sections*3):
            xx=x-w/2+w*i/(sections*3);tube(g,'metal',(xx,y-h/2,z+.10),(xx,y+h/2,z+.10),.012,5)
        for yy in [y-h*.32,y+h*.32]:tube(g,'metal',(x-w/2,yy,z+.10),(x+w/2,yy,z+.10),.015,6)

def ac(g,x,y,z):
    box(g,'trim',(x,y,z),(.78,.49,.32))
    # Dark shallow fan grille and radial vanes; no per-unit reflective pass.
    tube(g,'dark',(x-.12,y,z+.163),(x-.12,y,z+.176),.178,14)
    for i in range(12):
        a=i*math.tau/12;tube(g,'metal',(x-.12,y,z+.184),(x-.12+math.cos(a)*.167,y+math.sin(a)*.167,z+.184),.009,5)
    for xx in [x-.3,x+.3]:box(g,'metal',(xx,y-.29,z-.05),(.025,.14,.45))
    box(g,'snow',(x,y+.26,z),(.79,.03,.33))

def facade(g,x0,x1,z,floors,base,wall='plaster',pitch=2.7,cols=6):
    cell=(x1-x0)/cols
    for row in range(floors):
        floor=base+row*pitch;bottom=floor+.73;top=floor+2.12
        for ya,yb in [(floor,bottom-.065),(top+.065,floor+pitch)]:box(g,wall,((x0+x1)/2,(ya+yb)/2,z-.18),(x1-x0,yb-ya,.36))
        for j in range(cols):
            x=x0+cell*(j+.5);w=cell-.34
            box(g,wall,(x-cell/2+.085,(bottom+top)/2,z-.18),(.17,top-bottom+.13,.36))
            box(g,wall,(x+cell/2-.085,(bottom+top)/2,z-.18),(.17,top-bottom+.13,.36))
            window(g,x,(bottom+top)/2,z,w,top-bottom,(row*5+j*3)%4,bars=(row==0 or (row+j)%5==0))
            if (row+j)%3!=1:ac(g,x+cell*.26,floor+.28,z+.16)
        box(g,'concrete',((x0+x1)/2,floor+.05,z+.04),(x1-x0,.10,.16))
    box(g,wall,((x0+x1)/2,base+floors*pitch/2,z-2.25),(x1-x0,floors*pitch,.32))
    for x in [x0-.10,x1+.10]:box(g,wall,(x,base+floors*pitch/2,z-1.15),(.2,floors*pitch,2.4))
    box(g,'concrete',((x0+x1)/2,base+floors*pitch,z-1.1),(x1-x0+.4,.17,2.65))
    snow_sheet(g+'Snow',x0-.2,x1+.2,z-2.43,z+.23,base+floors*pitch+.085,.05,30,4)

facade('MainApartment',-14.0,5.2,-20.0,6,-3.12,cols=7)
# Patches and drainage streaks are low-contrast geometry strips in recesses,
# avoiding photo-baked lighting or a repeated full building photograph.
for x in [-13.9,-7.5,-1.2,5.1]:tube('MainApartment','cream',(x,-3.0,-19.78),(x,12.85,-19.78),.037,7)

# The left low wing turns perpendicular to the main facade. Build a front
# facade locally then rotate the authored vertices around the left corner.
prior=set(buckets)
facade('LeftWing',0,15,0,2,-3.12,'cream',pitch=3.5,cols=6)
for (g,m),(vs,fs,sm) in buckets.items():
    if g.startswith('LeftWing'):
        # Stored Blender coords -> web local; local front +z becomes +x.
        for i,(x,ny,y) in enumerate(vs):
            z=-ny;wx=-8.8+z;wz=-1.4-x;vs[i]=(wx,-wz,y)
# Narrow red painted surrounds at the near wing windows are reference-specific.
for z in [-2.65,-5.15,-7.65,-10.15,-12.65,-15.15]:
    for y in [-1.7,1.8]:
        for zz in [z-.95,z+.95]:box('LeftWing','rusttrim',(-8.70,y,zz),(.06,1.65,.11))

# Right plain wall is a second perpendicular mass, leaving a genuine sky gap.
box('RightBlock','rightwall',(15.9,7.6,-18),(.2,21.5,24))
for zz in [-30,-6]:box('RightBlock','rightwall',(14,7.6,zz),(4,21.5,.2))
for row in range(8):
    yc=-1.8+row*2.65;bottom=yc-.66;top=yc+.66;lo=-3.15+row*2.65;hi=lo+2.65
    for a,b in [(lo,bottom-.03),(top+.03,hi)]:box('RightBlock','rightwall',(12.15,(a+b)/2,-18),(.3,b-a,24))
    cuts=sorted([(-8.4-j*4.5-.59,-8.4-j*4.5+.59) for j in range(5)])
    last=-30
    for a,b in cuts:
        box('RightBlock','rightwall',(12.15,yc,(last+a)/2),(.3,1.38,a-last));last=b
    box('RightBlock','rightwall',(12.15,yc,(last-6)/2),(.3,1.38,-6-last))
for row in range(8):
    for j in range(5):
        z=-8.4-j*4.5;y=-1.8+row*2.65
        # Side-facing windows assembled in a temporary bucket then rotated.
        name=f'RightWin{row}_{j}'
        window(name,0,0,0,1.12,1.32,(row+j)%4,False)
        if (row+j)%2==0:ac(name,.58,-.9,.05)
        for key in [k for k in buckets if k[0]==name]:
            vs,fs,sm=buckets.pop(key);out=buckets.setdefault(('RightDetails',key[1]),([],[],[]));start=len(out[0])
            out[0].extend((12.0+ny,-(z+x),y+yy) for x,ny,yy in vs)
            out[1].extend(tuple(start+i for i in f) for f in fs);out[2].extend(sm)
facade('FarTower',7.8,12.2,-32,10,-3.12,'rightwall',pitch=2.8,cols=2)
facade('YellowGap',4.3,9.2,-35,3,-3.12,'yellow',pitch=2.6,cols=3)

# Bare branching trees: connected tapered tubes, asymmetrical branching,
# sparse snow supported only on substantial upper-facing branches.
def tree(x,z,height,seed):
    rr=random.Random(seed);ground=-3.10
    def branch(a,d,length,r,depth):
        b=Vector(a)+Vector(d).normalized()*length;tube('Trees','bark',a,b,r,7,max(.006,r*.60))
        if depth>1 and abs(d[1])<.85 and r>.045:
            aa=Vector(a)+Vector((0,r*.85,0));bb=b+Vector((0,r*.65,0));tube('TreeSnow','snow',aa,bb,r*.35,6,r*.20)
        if depth==0:return
        for k in range(3 if depth>2 else 2):
            new=Vector(d)*.5+Vector((rr.uniform(-.85,.85),rr.uniform(.35,.85),rr.uniform(-.7,.7)))
            branch(b,new,length*rr.uniform(.55,.73),r*.59,depth-1)
    branch(Vector((x,ground,z)),Vector((.07,1,.01)),height*.39,.13,4)
for args in [(-7,-15,7.6,21),(-4.8,-17,6.7,22),(7.7,-18,8.7,23),(9.4,-22,8.1,24),(11,-12.5,7.7,25)]:tree(*args)

# Small parked two-wheelers beneath the canopy, never larger than support bay.
for i,(x,z) in enumerate([(-4.1,-3.8),(-2.6,-4.4),(-.9,-3.6),(1.7,-4.7),(3.9,-4.0),(5.4,-4.9)]):
    y=-3.085;g='ParkedBikes'
    for dz in [-.55,.55]:
        center=(x,y+.25,z+dz)
        # Closed torus in yz plane, wheels meet ground at y.
        verts=[];faces=[]
        for a in range(16):
            ang=a*math.tau/16
            for b in range(6):
                q=b*math.tau/6;rad=.205+.045*math.cos(q)
                verts.append((x+.045*math.sin(q),y+.25+rad*math.sin(ang),z+dz+rad*math.cos(ang)))
        for a in range(16):
            for b in range(6):faces.append((a*6+b,((a+1)%16)*6+b,((a+1)%16)*6+(b+1)%6,a*6+(b+1)%6))
        add(g,'dark',verts,faces,True)
        tube(g,'metal',(x-.08,y+.25,z+dz),(x+.08,y+.25,z+dz),.042,8)
    oval(g,'vehicle',(x,y+.49,z),(.21,.24,.5))
    oval(g,'seat',(x,y+.74,z-.17),(.19,.075,.32))
    tube(g,'metal',(x,y+.25,z+.55),(x,y+.99,z+.47),.023,7)
    tube(g,'dark',(x-.29,y+1.01,z+.47),(x+.29,y+1.01,z+.47),.021,7)
    tube(g,'metal',(x-.17,y+1.0,z+.47),(x-.24,y+1.21,z+.48),.009,6)
    oval(g,'metal',(x-.24,y+1.21,z+.48),(.07,.036,.025),10,4)
    oval(g,'snow',(x,y+.817,z-.17),(.18,.018,.29),12,4)

# Material batches retain UV in real world metres; no screen-space patches.
for (group,material),(verts,faces,smooth) in buckets.items():
    mesh=bpy.data.meshes.new('C43_ZWinter_'+group+'_'+material);mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(mesh.name,mesh);col.objects.link(o);o.parent=root;mesh.materials.append(materials[material])
    o['web_userData']=json.dumps({'winterExterior':True,'noCollision':True,'noShadow':True,'layer':group})
    uv=mesh.uv_layers.new(name='UVMap')
    for p,sm in zip(mesh.polygons,smooth):
        p.use_smooth=sm;axis=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            v=mesh.vertices[mesh.loops[li].vertex_index].co
            uv.data[li].uv=((v.y*.5,v.z*.5) if axis==0 else (v.x*.5,v.z*.5) if axis==1 else (v.x*.5,v.y*.5))
    assert all(p.area>1e-12 for p in mesh.polygons),o.name

for name in ['C43_Exterior_Masonry','C43_Exterior_Windows']:
    o=bpy.data.objects[name];o.hide_render=True;o.hide_set(True)
    o['superseded_by']='winter10 multi-depth exterior'
for im in images.values():im.filepath=bpy.path.relpath(im.filepath,start=str(ROOM/'assets/full-room'))
bpy.context.view_layer.update()
component=ASSET/'Courtyard43-winter-exterior.blend'
bpy.data.libraries.write(str(component),{col},path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(scene['components']);components.append({'component':'winter-exterior','source':str(component.relative_to(ROOT)).replace('\\','/'),'revision':'winter01','sha256':hashlib.sha256(component.read_bytes()).hexdigest()})
scene['components']=json.dumps(components);scene['parent_web_revision']='courtyard43-interior09';scene['web_revision']='courtyard43-interior10'
scene['winter_exterior']='User-approved four-view winter design. Photo-estimated spatial dimensions. Original room and corridor retained; exterior31 mineral texture cloned from Yongwang handles39, isolated and no source write.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'winter_export'}
exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope)
result=scope['export_interior']();result['exteriorObjects']=len(col.objects);result['sourceReuse']='Yongwang handles39 mineral plaster image maps, independent copies'
report=ROOT/'analysis/Courtyard43/winter10/model-report.json'
report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
