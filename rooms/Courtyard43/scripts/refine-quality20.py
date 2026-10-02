"""Official MCP: interior19 -> interior20, visible furniture construction.

Photo-based estimates. Preserve anchors, silhouette corrections and interaction
pivots. Existing detailed bottle, desktop electronics, hats and paper are kept;
their material response is handled separately in quality21.
"""
from pathlib import Path
import bpy,bmesh,math,json,hashlib,ast
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior19'
bpy.context.preferences.filepaths.save_version=0
bp=lambda p:Vector((p[0],-p[2],p[1]))
web=lambda p:Vector((p[0],p[2],-p[1]))
targets=set()
# Reuse side-effect-free helper definitions, never execute old stage bodies.
helper=ROOM/'scripts/refine-furnishings.py';tree=ast.parse(helper.read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'digest','replace','shader','tube'}],type_ignores=[]),str(helper),'exec'))
before={o.name:digest(o) for o in scene.objects}

# Sewn thin pad: compressed against the white seat ring, softly crowned face,
# gently unequal side edges, closed bottom. No hard uniform bevel box.
name='C43_Chair15_BlackSeatPad';old=bpy.data.objects[name];mat=old.data.materials[0]
nx=40;ny=40;verts=[];uv=[]
for bottom in (False,True):
    for j in range(ny+1):
        for i in range(nx+1):
            u,v=i/nx,j/ny;a=2*u-1;b=2*v-1
            # Rounded rectangular parameter boundary, exact supported footprint.
            x=-1.35+.197*a*(1-.085*abs(b)**12)
            z=.742+.197*b*(1-.085*abs(a)**12)
            t=max(0,(1-a*a)*(1-b*b))**.42
            h=.4382 if bottom else .450+.022*t-.004*math.exp(-((u-.53)/.25)**2-((v-.58)/.28)**2)*t
            if not bottom:h+=.0018*math.sin(u*9+v*5)*t
            verts.append((x,h,z));uv.append((u*.394,v*.394))
n=(nx+1)*(ny+1);faces=[]
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;faces.extend([(k,k+1,k+nx+2,k+nx+1),(k+n,k+nx+1+n,k+nx+2+n,k+1+n)])
edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
for i,k in enumerate(edge):q=edge[(i+1)%len(edge)];faces.append((k,q,q+n,k+n))
pad=replace(name,verts,faces,[mat],uv);pad['construction']='Closed sewn cushion, compressed supported underside, gently crowned top'
# Binding runs halfway down its compressed perimeter and meets the tie loops.
path=[(verts[k][0],.446,verts[k][2]) for k in edge];path.append(path[0])
seam=tube('C43_Chair20_CushionBinding',path,.0007,mat)
matrix=seam.matrix_world.copy();seam.parent=bpy.data.objects['C43_DeskChair'];seam.matrix_world=matrix

# Furniture edge radii follow each manufacturing process. Keep every original
# bounding box and hinge root; replacing the bevel does not scale the panels.
for o in list(scene.objects):
    if o.type!='MESH':continue
    radius=None
    if o.name.startswith(('C43_WardrobeDoor','C43_WardrobeNearSide','C43_WardrobeFarSide')):radius=.0013
    elif o.name=='C43_BedHeadboard':radius=.003
    elif o.name.startswith(('C43_DeskSquareLeg','C43_DeskSideBrace','C43_BedLongSteelRail','C43_BedCrossSteelRail')):radius=.001
    if radius is not None:
        for mod in o.modifiers:
            if mod.type=='BEVEL':mod.width=radius;mod.segments=3;targets.add(o.name)

# Separate wood effect face from the solid edge band by assigning EXISTING
# side faces, without adding a second near-coplanar mesh or moving the rim.
desk=bpy.data.objects['C43_DeskTop'];targets.add(desk.name);desk.data=desk.data.copy()
band=desk.data.materials[0].copy();band.name='C43_Desk20_SealedEdge'
b=shader(band)
for link in list(b.inputs['Base Color'].links):band.node_tree.links.remove(link)
b.inputs['Base Color'].default_value=(.59,.49,.34,1)
b.inputs['Roughness'].default_value=.46
props=json.loads(band.get('web_props','{}'));props.update(roughness=.46,metalness=0);band['web_props']=json.dumps(props)
desk.data.materials.append(band)
normal_matrix=desk.matrix_world.to_3x3().inverted().transposed()
for poly in desk.data.polygons:
    if abs((normal_matrix@poly.normal).normalized().z)<.5:poly.material_index=len(desk.data.materials)-1

# Match small contact transitions at the cap and grille ends. Existing solid
# cabinet body stays untouched and cannot turn into an open-backed shell.
for name,radius in [('C43_Radiator_Cap_Front',.00065),('C43_Radiator_White_Vertical_Grille',.00045)]:
    o=bpy.data.objects[name];targets.add(name)
    mod=o.modifiers.new('Fine formed edge quality20','BEVEL');mod.width=radius;mod.segments=2;mod.limit_method='ANGLE';mod.angle_limit=.6
    mod=o.modifiers.new('Preserve flat surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True

# Existing apron/leg joints already overlap by their true contact thickness.
# Keep those components, rather than inventing hidden hardware from one photo.
assert all(digest(o)==before[o.name] for o in scene.objects if o.name in before and o.name not in targets)
scene['quality20_targets']=json.dumps(sorted(targets));scene['parent_web_revision']='courtyard43-interior19';scene['web_revision']='courtyard43-interior20'
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'revision':scene['web_revision'],'targets':sorted(targets),'nonTargetsUnchanged':len(before)-len(targets.intersection(before))}
