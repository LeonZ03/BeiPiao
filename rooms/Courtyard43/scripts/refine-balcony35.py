"""switch32 -> balcony35: evidence-led balcony contents and suspended bedhead soffit.

Run only through official Blender Lab MCP on the current complete scene.
P01/P03 show three bedhead downlights and an open-topped perimeter soffit.
P02 and V01 8.4/11.3s show the rack, old outer curtains and end cabinets.
All small dimensions, hidden cabinet interiors and wear extent are estimates.
The approved room, furniture anchors, blackout curtains and exterior stay fixed.
"""
from pathlib import Path
import ast, bpy, bmesh, hashlib, json, math
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
s = bpy.context.scene
assert s.get('web_revision') == 'courtyard43-switch32', 'Use the current complete source'
bpy.context.preferences.filepaths.save_version = 0
tree = ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'digest'], type_ignores=[]), 'digest', 'exec'))
targets = {'C43_Ceiling_Dropped_Perimeter', 'C43_Ceiling_Tray_Reveal'}
before = {o.name: digest(o) for o in s.objects if o.name not in targets}
original_materials = {m.name: hashlib.sha256(repr([(n.name, [(i.name, str(i.default_value)) for i in n.inputs if hasattr(i, 'default_value')]) for n in m.node_tree.nodes]).encode()).hexdigest() for m in bpy.data.materials if m.use_nodes}
collection = bpy.data.collections.new('C43_Balcony35')
s.collection.children.link(collection)
bp = lambda p: Vector((p[0], -p[2], p[1]))
created = []

def mat(name, rgb, rough=.7, metal=0):
    m=bpy.data.materials.new('C43_B35_'+name);m.use_nodes=True
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value=(*rgb,1)
    b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
    return m

paint=mat('OldIvoryLaminate',(.58,.55,.48),.76)
edge=mat('FadedEdgeBand',(.40,.36,.28),.80)
wood=mat('ExposedParticleBoard',(.27,.20,.12),.88)
inside=mat('RecessShadow',(.105,.095,.077),.93)
steel=mat('OldDryingRail',(.21,.23,.22),.42,.5)
wire=mat('HangerWire',(.055,.063,.06),.52,.4)
cloth=mat('OldBalconyCloth',(.24,.245,.225),.96)
hem=mat('OldCurtainHem',(.47,.455,.395),.94)
bezel=mat('DownlightBezel',(.34,.33,.30),.4,.65)
diffuser=mat('DownlightDiffuser',(.60,.57,.48),.57)
bs=next(n for n in diffuser.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Emission Color'].default_value=(1,.85,.65,1)
bs.inputs['Emission Strength'].default_value=0
diffuser['web_props']=json.dumps({'emissive':[1,.85,.65],'emissiveIntensity':0})
diffuser['web_userData']=json.dumps({'lightFixture':True})
plaster=bpy.data.materials['C43_Warm_white_plaster']

def tag(o, ceilings=False, fixture=False):
    o['web_tags']=json.dumps({'ceilings':ceilings,'lightFixture':fixture})
    o['evidence']='P01/P02/P03 and V01; dimensions estimated'
    created.append(o.name)
    return o

def finish(o, material, bevel=0, smooth=False):
    o.data.materials.append(material)
    if bevel:
        bpy.context.view_layer.objects.active=o;o.select_set(True)
        mod=o.modifiers.new('Material-scale edge','BEVEL');mod.width=bevel;mod.segments=3
        bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    uv=o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        p.use_smooth=smooth
        for li in p.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v.x+v.y,v.z+v.y)
    o.data.uv_layers.new(name='UV1',do_init=True)
    return o

def mesh(name, verts, faces, material, bevel=0, smooth=False):
    me=bpy.data.meshes.new('B35 '+name);me.from_pydata([bp(v) for v in verts],[],faces);me.update()
    o=bpy.data.objects.new('C43_B35_'+name,me);collection.objects.link(o)
    return tag(finish(o,material,bevel,smooth))

def box(name, center, size, material, bevel=.001):
    x,y,z=center;a,b,c=[v/2 for v in size]
    vs=[(x+i*a,y+j*b,z+k*c) for i,j,k in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    return mesh(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],material,bevel)

def tube(name, points, radius, material, segments=12):
    vs=[];fs=[]
    for i,p in enumerate(points):
        d=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])).normalized()
        u=d.cross(Vector((0,1,0)))
        if u.length<.01:u=d.cross(Vector((1,0,0)))
        u.normalize();v=d.cross(u).normalized()
        vs.extend([Vector(p)+radius*(math.cos(j*math.tau/segments)*u+math.sin(j*math.tau/segments)*v) for j in range(segments)])
        if i:
            for j in range(segments):fs.append(((i-1)*segments+j,(i-1)*segments+(j+1)%segments,i*segments+(j+1)%segments,i*segments+j))
    fs += [tuple(range(segments-1,-1,-1)),tuple((len(points)-1)*segments+j for j in range(segments))]
    return mesh(name,vs,fs,material,smooth=True)

# Thin suspended plate and an open cove replace the former solid ceiling blocks.
# Keep the exact old outer footprint and lower elevation (2.55 m).
left,right=-2.025,2.225
parts=[]
for x in [left+.14,right-.14]:parts.append(box('SoffitPlate',(x,2.561,1.425),(.28,.022,2.85),plaster,.002))
for z in [.14,2.71]:parts.append(box('SoffitCrossPlate',(.1,2.561,z),(3.69,.022,.28),plaster,.002))
for i,z in enumerate([.60,1.45,2.30]):
    # Actual holes through the suspended plate; the dark can is recessed above it.
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.032,depth=.08,location=bp((left+.14,2.565,z)))
    cutter=bpy.context.object
    plate=parts[0];bpy.context.view_layer.objects.active=plate
    mod=plate.modifiers.new('Recessed downlight opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
    # Blender's boolean may append the cutter's empty material slot.
    plate.data.materials.clear();plate.data.materials.append(plaster)
    for p in plate.data.polygons:p.material_index=0
    tag(tube('BedheadLight%d_Can'%i,[(left+.14,2.580,z),(left+.14,2.607,z)],.031,inside,32),True,True)
    # Annular trim, leaving its centre physically open rather than a stacked disk.
    n=48;vs=[]
    for y,r in [(2.548,.039),(2.548,.029),(2.555,.029),(2.555,.039)]:
        vs.extend([(left+.14+r*math.cos(j*math.tau/n),y,z+r*math.sin(j*math.tau/n)) for j in range(n)])
    fs=[(a*n+j,a*n+(j+1)%n,((a+1)%4)*n+(j+1)%n,((a+1)%4)*n+j) for a in range(4) for j in range(n)]
    tag(mesh('BedheadLight%d_Bezel'%i,vs,fs,bezel,smooth=True),True,True)
    tag(tube('BedheadLight%d_Diffuser'%i,[(left+.14,2.570,z),(left+.14,2.574,z)],.0285,diffuser,32),True,True)

# Inner upstand has a 70 mm open shadow gap. Two small missing paint/fascia
# areas correspond to P01/P03, without inventing widespread damage.
for a,b in [(.28,1.80),(1.98,2.31),(2.48,2.57)]:
    parts.append(box('SoffitBedheadFascia',(left+.274,2.626,(a+b)/2),(.012,.108,b-a),plaster,.001))
for a,b in [(1.80,1.98),(2.31,2.48)]:
    parts.append(box('SoffitExposedCore',(left+.279,2.597,(a+b)/2),(.011,.05,b-a),wood,.0007))
parts.append(box('SoffitOppositeFascia',(right-.274,2.626,1.425),(.012,.108,2.29),plaster))
for z in [.274,2.576]:parts.append(box('SoffitCrossFascia',(.1,2.626,z),(3.69,.108,.012),plaster))
for name in targets:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
for o in parts:o['web_tags']=json.dumps({'ceilings':True})

# Cabinets: independent estimated carcasses, empty and closed. They are not the
# already-confirmed solid radiator cover beside the bedroom opening.
def cabinet(label, x, width, depth, height, facing):
    z=-.59;floor=.015;front=x+facing*width/2;back=x-facing*(width/2-.009)
    for zz in [z-depth/2+.009,z+depth/2-.009]:box(label+'_Side',(x,floor+height/2,zz),(width,height,.018),edge if label=='RightCabinet' else paint)
    for yy in [floor+.025,floor+height-.009]:box(label+'_Board',(x,yy,z),(width,.018,depth),paint,.0015)
    box(label+'_Back',(back,floor+height/2,z),(.018,height-.036,depth-.036),wood)
    box(label+'_Shelf',(x,floor+height*.50,z),(width-.03,.016,depth-.036),paint)
    # Two simple inset fronts on the longer left cabinet, one on the right.
    count=2 if label=='LeftCabinet' else 1
    for i in range(count):
        zz=z-depth/2+(i+.5)*depth/count
        door=box(label+'_Door%d'%i,(front,floor+height/2+.007,zz),(.018,height-.056,depth/count-.004),paint,.0013)
        # Restrained exposed edge, modelled clear of the broad paint surface.
        box(label+'_WornLowerEdge%d'%i,(front+facing*.0097,floor+.033,zz),(.0015,.005,depth/count-.025),edge,.0004)
        tube(label+'_SmallPull%d'%i,[(front+facing*.012,floor+height*.57,zz-.025),(front+facing*.024,floor+height*.57,zz-.025),(front+facing*.024,floor+height*.57,zz+.025),(front+facing*.012,floor+height*.57,zz+.025)],.003,edge)
    box(label+'_RecessedPlinth',(x,floor+.012,z),(width-.035,.024,depth-.045),edge)

cabinet('LeftCabinet',left+.19,.36,.78,.84,1)
cabinet('RightCabinet',right-.19,.36,.57,.88,-1)

# One rigid wall-supported drying rail, two simple empty wire hangers visible in
# the video. No unsupported hanging laundry is introduced into the winter scene.
for x in [left+.012,right-.012]:
    box('DryingRailWallSocket',(x,2.235,-.76),(.024,.052,.052),steel,.003)
tube('DryingRail',[(left+.018,2.235,-.76),(right-.018,2.235,-.76)],.010,steel,20)
for i,x in enumerate([-.77,1.45]):
    z=-.76
    points=[(x+.025,2.249,z),(x+.015,2.275,z),(x-.014,2.273,z),(x-.026,2.253,z),(x-.018,2.229,z),(x,2.208,z),(x,2.166,z),(x-.18,2.035,z),(x-.19,2.014,z),(x+.19,2.014,z),(x+.18,2.035,z),(x,2.166,z)]
    tube('WireHanger%d'%i,points,.0022,wire,8)

# Old outer-window curtains: opaque, dull, narrow gathered panels with softened
# irregular folds, an ivory hem and a small uneven lower edge. Their exact
# pattern and deterioration cannot be recovered from the dark video.
tube('OuterCurtainSupport',[(left+.004,2.371,-1.043),(right-.004,2.371,-1.043)],.004,wire)
for x in [left+.004,right-.004]:box('OuterCurtainWallSocket',(x,2.371,-1.043),(.008,.027,.027),steel,.001)
for label,x0,x1,bottom,phase in [('Left',-1.98,-1.39,.91,.5),('Right',1.64,2.18,.65,2.1)]:
    nx,ny=48,26;vs=[];fs=[]
    for j in range(ny+1):
        t=j/ny
        for i in range(nx+1):
            u=i/nx;x=x0+(x1-x0)*u
            fold=.032*math.sin(u*math.tau*5+phase)+.009*math.sin(u*math.tau*9+.7)
            lower=bottom+.015*math.sin(u*7+phase)+(.025*max(0,1-abs(u-.81)/.045) if label=='Right' else 0)
            y=2.365+(lower-2.365)*t
            z=-1.045+fold*(.65+.35*t)+.009*math.sin(t*4+u*3)
            vs.append((x,y,z))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
    o=mesh('OldCurtain'+label,vs,fs,cloth,smooth=True);o.data.materials.append(hem)
    for p in o.data.polygons:
        if p.index//nx>=ny-1:p.material_index=1
    mod=o.modifiers.new('Real cloth edge thickness','SOLIDIFY');mod.thickness=.002;mod.offset=0
    bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
    o['web_userData']=json.dumps({'noCollision':True})
    for i in range(7):
        x=x0+(x1-x0)*(i+.25)/7
        tube('OuterCurtain'+label+'Tie%d'%i,[(x,2.371,-1.043),(x,2.36,-1.023)],.002,hem,6)

bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items()), 'Unrelated object changed'
assert all(hashlib.sha256(repr([(n.name, [(i.name, str(i.default_value)) for i in n.inputs if hasattr(i, 'default_value')]) for n in bpy.data.materials[k].node_tree.nodes]).encode()).hexdigest()==h for k,h in original_materials.items()), 'Original material changed'
s['parent_web_revision']='courtyard43-switch32';s['web_revision']='courtyard43-balcony35'
s['balcony35']=json.dumps({'parent':'courtyard43-switch32','unrelatedObjectsUnchanged':len(before),'replaced':sorted(targets),'newObjects':sorted(set(created)),'reference':'P01/P02/P03; V01 8.4s and 11.3s','dimensions':'photo estimates','bedheadDownlights':3,'openCoveHeightM':.07})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')}
exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns)
report=ns['export_interior']()
result={**report,'unchangedObjects':len(before),'newObjects':len(set(created))}
