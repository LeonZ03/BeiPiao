"""Independent occupied-room props, authored through official Blender Lab MCP.

Reuses accepted sunview34 laptop, mouse and cap geometry as isolated variants.
P03/P04: closed silver laptop, mouse on black pad, three dark caps, tissue,
clear cup and red-capped water bottle. Illegible labels are deliberately blank.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil
import bpy
import bmesh
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
OUT = ROOM / 'assets/props'
TEX = OUT / 'textures'
SOURCE = ROOT / 'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == '67765fb8a97bf6b86d9d272f5319ab8aa047f5330438210ccce063a06833e150'
assert json.loads((ROOM / 'history/inputs/approved-layout.json').read_text(encoding='utf-8'))['structureApproved']
TEX.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene['room_id'] = 'Courtyard43'
scene['component'] = 'props'
scene['component_revision'] = 'courtyard43-props01'
coll = bpy.data.collections.new('C43_Props')
scene.collection.children.link(coll)
bp = lambda p: Vector((p[0], -p[2], p[1]))


def own(obj, name):
    obj.name = 'C43_' + name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    obj['web_tags'] = json.dumps({'noCollision': True})
    return obj


def mat(name, color, rough=.5, metal=0, alpha=1):
    m = bpy.data.materials.new('C43_' + name)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Alpha'].default_value = alpha
    m.diffuse_color = (*color, alpha)
    if alpha < 1:
        m['web_props'] = json.dumps({'transparent': True, 'opacity': alpha, 'depthWrite': False})
    return m


def box(name, p, size, material, bevel=.002):
    bpy.ops.mesh.primitive_cube_add(size=1, location=bp(p))
    obj = own(bpy.context.object, name)
    obj.dimensions = (size[0], size[2], size[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new('Manufactured soft edge', 'BEVEL')
        mod.width = min(bevel, min(size)*.22); mod.segments = 3
        obj.modifiers.new('Weighted surface normals', 'WEIGHTED_NORMAL')
    return obj


def lathe(name, center, profile, material, segments=64):
    # Closed cross section includes inner wall and lip where physically needed.
    verts, faces, uvcoords = [], [], []
    for radius, height in profile:
        for i in range(segments):
            angle = math.tau*i/segments
            verts.append(bp((center[0]+radius*math.cos(angle), center[1]+height, center[2]+radius*math.sin(angle))))
    for j in range(len(profile)-1):
        for i in range(segments):
            k = j*segments+i; n = j*segments+(i+1)%segments
            faces.append((k+segments,n+segments,n,k))
            uvcoords.extend(((i/segments,(j+1)/(len(profile)-1)),((i+1)/segments,(j+1)/(len(profile)-1)),((i+1)/segments,j/(len(profile)-1)),(i/segments,j/(len(profile)-1))))
    mesh = bpy.data.meshes.new('C43_'+name)
    mesh.from_pydata(verts, [], faces); mesh.update()
    uv = mesh.uv_layers.new(name='UVMap')
    for item, coord in zip(uv.data, uvcoords): item.uv = coord
    for p in mesh.polygons: p.use_smooth = True
    obj = bpy.data.objects.new('C43_'+name, mesh); coll.objects.link(obj)
    obj.data.materials.append(material)
    obj['web_tags'] = json.dumps({'noCollision': True})
    return obj


# Append only necessary datablocks: meshes, materials and images are copied
# inside this target. No link to a mutable source-room datablock is retained.
needed_roots = ['detailed-laptop', 'white-gaming-mouse', 'Black LA Baseball Cap']
with bpy.data.libraries.load(str(SOURCE), link=False) as (src, dst):
    dst.objects = list(src.objects)
loaded = {o.name: o for o in dst.objects if o}
keep = set()
for name in needed_roots:
    root = loaded[name]; keep.add(root); keep.update(root.children_recursive)
for obj in list(loaded.values()):
    if obj not in keep:
        bpy.data.objects.remove(obj, do_unlink=True)
material_copies, image_copies = {}, {}
for obj in sorted(keep, key=lambda x:x.name):
    coll.objects.link(obj)
    obj['web_tags'] = json.dumps({'noCollision': True})
    if obj.data and obj.type == 'MESH':
        obj.data = obj.data.copy()
        for slot in obj.material_slots:
            source = slot.material
            if source.name not in material_copies:
                copy = source.copy(); copy.name = 'C43_Prop_'+source.name
                # Match the active surface, preserving accepted image mappings.
                for node in copy.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        original = node.image
                        if original.name not in image_copies:
                            im = original.copy()
                            path = Path(bpy.path.abspath(original.filepath, library=original.library)).resolve()
                            assert path.is_file(), path
                            target = TEX / (hashlib.sha256(path.read_bytes()).hexdigest()[:12] + path.suffix)
                            shutil.copyfile(path, target)
                            im.filepath = str(target)
                            image_copies[original.name] = im
                        node.image = image_copies[original.name]
                material_copies[source.name] = copy
            slot.material = material_copies[source.name]

silver = mat('Laptop_anodized_silver',(.48,.51,.54),.28,.78)
root = loaded['detailed-laptop']
root.parent = None; root.matrix_world = Matrix.Identity(4)
root.location = bp((-1.57, .7465, .295))
lid = loaded['laptop-open-lid']; lid.rotation_euler.x = math.pi/2
for name in ['Mesh 1133', 'Mesh 1134', 'Mesh 1221']:
    loaded[name].data.materials.clear(); loaded[name].data.materials.append(silver)
for obj in [root, *root.children_recursive]: obj.name = 'C43_Laptop_'+obj.name.replace(' ', '_')
root['reuse'] = 'sunview34 detailed-laptop; isolated; closed lid; silver outer shell from P03/P04'
mouse = loaded['white-gaming-mouse']
mouse.parent = None; mouse.matrix_world = Matrix.Identity(4)
mouse.rotation_euler.z = math.pi/2
mouse.location = bp((-1.06, .746, .325))
for obj in [mouse,*mouse.children_recursive]: obj.name = 'C43_Mouse_'+obj.name.replace(' ', '_')
mouse['reuse'] = 'sunview34 white-gaming-mouse; isolated meshes/materials/textures'
rubber = mat('Soft_black_mousepad',(.018,.021,.024),.93)
box('Mousepad',(-1.055,.7415,.345),(.245,.003,.215),rubber,.001)

cap = loaded['Black LA Baseball Cap']
cap.parent = None
for obj in list(cap.children_recursive):
    if 'embroidery' in obj.name:
        bpy.data.objects.remove(obj, do_unlink=True)
# Keep each cap's tailoring, bill thickness and approved sewn seams. Photos do
# not resolve the emblem; removing it is more honest than reusing an LA logo.
def place_cap(root, x, height, roll=0):
    matrix = root.matrix_world.copy()
    matrix.translation = Vector((0,0,0))
    root.matrix_world = Matrix.Rotation(roll,4,'Y') @ matrix
    bpy.context.view_layer.update()
    points = [o.matrix_world@v.co for o in root.children_recursive if o.type=='MESH' for v in o.data.vertices]
    root.location += Vector((x-(min(v.x for v in points)+max(v.x for v in points))/2,
                             -.045-max(v.y for v in points),
                             height-(min(v.z for v in points)+max(v.z for v in points))/2))
    root['reuse'] = 'sunview34 Black LA Baseball Cap; isolated unbranded hanging variant'

for i,(x,y,roll) in enumerate([(-1.8,1.44,-.09),(-1.46,1.52,.035),(-1.12,1.47,.11)]):
    if i == 0:
        current = cap
    else:
        remap = {}
        for obj in [cap,*cap.children_recursive]:
            clone = obj.copy()
            if obj.data: clone.data = obj.data.copy()
            coll.objects.link(clone); remap[obj] = clone
        for old, clone in remap.items():
            if old.parent in remap: clone.parent = remap[old.parent]
        current = remap[cap]
    place_cap(current,x,y,roll)
    for obj in [current,*current.children_recursive]: obj.name = f'C43_Cap{i+1}_'+obj.name.removeprefix('C43_Cap1_').replace(' ','_')
    box(f'Cap_hook_{i}',(x,y+.115,.038),(.009,.019,.022),silver,.003)

ivory = mat('Soft_offwhite_paper',(.81,.79,.72),.94)
plastic = mat('Clear_plastic',(.75,.83,.84),.16,0,.22)
water = mat('Clear_water',(.64,.79,.80),.09,0,.12)
red = mat('Bottle_red_cap',(.44,.018,.012),.47)
paper = mat('Offwhite_tissue_packet',(.74,.73,.66),.85)
box('Tissue_packet',(.61,1.052,.214),(.18,.079,.112),paper,.012)
# A few soft lifted tissues; grid is a finite solid shell, not a floating card.
for i in range(2):
    verts, faces = [], []
    for j in range(15):
        v=j/14
        for k in range(13):
            u=k/12
            verts.append(bp((.56+.102*u,1.084+.036*math.sin(v*math.pi/2)+.008*math.sin(u*math.pi*2)*v,.212+(v-.5)*.046)))
    for j in range(14):
        for k in range(12):
            a=j*13+k; faces.append((a,a+1,a+14,a+13))
    mesh=bpy.data.meshes.new('Tissue');mesh.from_pydata(verts,[],faces);mesh.update()
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        poly.use_smooth=True
        for li,vi in zip(poly.loop_indices,poly.vertices):uv.data[li].uv=(vi%13/12,vi//13/14)
    o=bpy.data.objects.new(f'C43_Tissue_{i}',mesh);coll.objects.link(o);o.data.materials.append(ivory)
    o.location.z=i*.0012
    mod=o.modifiers.new('Paper thickness','SOLIDIFY');mod.thickness=.00025
    o['web_tags']=json.dumps({'noCollision':True})
profile=[(0,0),(.037,0),(.044,.006),(.046,.015)]
for h in [.026,.043,.06,.078,.096,.115,.135,.156,.174]:
    profile.extend([(.046,h),(.0435,h+.004),(.046,h+.008)])
profile += [(.045,.19),(.033,.218),(.017,.238),(.017,.258),(.0145,.258),(.0145,.24),(.030,.217),(.043,.19),(.043,.013),(.035,.003),(0,.003)]
lathe('Ribbed_water_bottle',(.90,1.0125,.215),profile,plastic)
lathe('Bottle_water',(.90,1.016,.215),[(0,0),(.041,0),(.042,.135),(0,.135)],water)
lathe('Bottle_cap',(.90,1.263,.215),[(0,0),(.018,0),(.019,.003),(.019,.024),(.017,.026),(0,.026)],red)
lathe('Plastic_cup',(1.16,1.0125,.215),[(0,0),(.027,0),(.033,.006),(.039,.106),(.039,.11),(.0375,.111),(.0365,.106),(.0305,.006),(0,.003)],plastic)

def tube(name, points, radius, material):
    curve = bpy.data.curves.new('C43_'+name, 'CURVE')
    curve.dimensions='3D';curve.resolution_u=10;curve.bevel_depth=radius;curve.bevel_resolution=3;curve.use_fill_caps=True
    spline=curve.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
    for point, co in zip(spline.bezier_points,points):
        point.co=bp(co);point.handle_left_type='AUTO';point.handle_right_type='AUTO'
    obj=bpy.data.objects.new('C43_'+name,curve);coll.objects.link(obj);obj.data.materials.append(material)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.object.convert(target='MESH')
    obj=bpy.context.object;obj.select_set(False);obj['web_tags']=json.dumps({'noCollision':True})
    return obj

# Photo-visible power supply: endpoints enter the plug and laptop port, while
# the slack hangs down under gravity beside the left desk corner.
box('Desk_power_plug',(-1.986,.78,.87),(.041,.035,.042),ivory,.006)
tube('Desk_power_cable',[(-1.965,.78,.87),(-1.91,.62,.83),(-1.84,.56,.73),(-1.86,.60,.59),(-1.86,.722,.53),(-1.84,.751,.47),(-1.82,.754,.36),(-1.745,.748,.326)],.0025,rubber)
box('Desk_small_dark_device',(-1.82,.747,.43),(.092,.014,.056),rubber,.009)
ceramic = mat('Plain_white_container',(.79,.78,.70),.37)
blue = mat('Container_blue_band',(.025,.09,.22),.55)
lathe('Desk_lidded_container',(-1.84,.74,.145),[(0,0),(.051,0),(.061,.044),(.061,.049),(0,.049)],ceramic)
lathe('Desk_container_band',(-1.84,.74,.145),[(.056,.025),(.058,.033),(.0585,.038),(.057,.031),(.056,.025)],blue)

# Small cream wastebasket and rolled translucent liner, visible in P03. Its
# dimensions and liner creases are photo estimates, not a hidden storage claim.
cream=mat('Cream_wastebasket',(.48,.35,.16),.64)
liner=mat('Pale_bin_liner',(.68,.73,.64),.75,0,.72)
lathe('Wastebasket',(.09,0,.50),[(0,0),(.080,0),(.096,.008),(.112,.263),(.112,.274),(.108,.277),(.106,.270),(.093,.014),(0,.014)],cream)
lathe('Wastebasket_liner',(.09,.022,.50),[(.092,0),(.105,.237),(.111,.255),(.116,.258),(.118,.244),(.115,.240),(.113,.254),(.106,.254),(.100,.239),(.089,.005),(.092,0)],liner)

# Soft two-tone bag hanging from the visible wardrobe side. No unreadable
# writing or logo is invented. Both straps actually enter the top seam and hook.
navy=mat('Bag_navy_fabric',(.018,.021,.045),.91)
bagwhite=mat('Bag_offwhite_fabric',(.60,.60,.54),.93)
profile=[(0,.06,.022),(.015,.095,.035),(.050,.140,.055),(.105,.147,.056),(.17,.121,.044),(.22,.091,.028),(.255,.078,.025)]
verts,faces=[],[];N=64
for row,(height,width,depth) in enumerate(profile):
    for i in range(N):
        a=math.tau*i/N
        fold=.005*math.sin(3*a+.5)+.003*math.sin(7*a-height*8)
        verts.append(bp((1.955+width*math.cos(a),1.105+height+.006*math.sin(a)*math.sin(row/6*math.pi),1.441+(depth+fold)*math.sin(a))))
for j in range(len(profile)-1):
    for i in range(N):faces.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
faces.append(tuple(reversed(range(N))))
mesh=bpy.data.meshes.new('C43_Bag_body');mesh.from_pydata(verts,[],[tuple(reversed(f)) for f in faces]);mesh.update()
uv=mesh.uv_layers.new(name='UVMap')
for p in mesh.polygons:
    p.use_smooth=True;p.material_index=0 if p.center.z<1.225 else 1
    for li,vi in zip(p.loop_indices,p.vertices):uv.data[li].uv=(vi%N/N,vi//N/(len(profile)-1))
bag=bpy.data.objects.new('C43_Hanging_bag',mesh);coll.objects.link(bag);bag.data.materials.append(bagwhite);bag.data.materials.append(navy)
bag['web_tags']=json.dumps({'noCollision':True});solid=bag.modifiers.new('Woven bag thickness','SOLIDIFY');solid.thickness=.0018
box('Bag_wall_hook',(1.955,1.61,1.391),(.033,.04,.020),plastic,.006)
for i,z in enumerate([1.428,1.464]):
    tube(f'Bag_strap_{i}',[(1.89,1.347,z),(1.916,1.486,z+.004),(1.955,1.596,1.407),(1.99,1.487,z+.004),(2.02,1.347,z)],.0035,navy)

# Neighbouring urban facade and barred opening are supported by V01/P02.
# Exact setback and unseen details remain inferred; no unrelated trees added.
facade = mat('Distant_neutral_masonry',(.35,.32,.27),.95)
window = mat('Distant_smoky_window',(.08,.115,.14),.45)
box('Exterior_neighbor',(.4,3.2,-5.2),(8,8,.22),facade,.01)
for floor in range(3):
    for column in range(5):
        x=-3.1+column*1.55;y=.8+floor*2.25
        box(f'Exterior_window_{floor}_{column}',(x,y,-5.075),(.79,1.15,.022),window,.008)
        box(f'Exterior_sill_{floor}_{column}',(x,y-.59,-5.00),(.9,.045,.18),facade,.007)
        box(f'Exterior_mullion_{floor}_{column}',(x,y,-5.05),(.033,1.15,.025),facade,.003)
for material, suffix in [(facade, 'Masonry'), (window, 'Windows')]:
    objects = [obj for obj in scene.objects if obj.name.startswith('C43_Exterior_') and obj.type == 'MESH' and obj.active_material == material]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    obj=bpy.context.object;obj.name='C43_Exterior_'+suffix
    obj['web_tags'] = json.dumps({'noCollision': True, 'cutaway': True})

bpy.context.view_layer.update()
for obj in scene.objects:
    if obj.type != 'MESH':
        continue
    # Accepted old rounded primitives included repeated pole vertices. Clean
    # only this independent variant; retain UV loops, materials and contour.
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=1e-10)
    empty = [face for face in bm.faces if face.calc_area() < 1e-16]
    if empty: bmesh.ops.delete(bm, geom=empty, context='FACES')
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
scene['reuse_sources'] = json.dumps({'room':'yongwang-jiayuan','revision':'sunview34','file':str(SOURCE.relative_to(ROOT)).replace('\\','/'),
    'sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'objects':needed_roots,'method':'append, single-user mesh/material/image, local variants'},ensure_ascii=False)
scene['reference_notes'] = 'P03/P04 occupied period; unresolved marks left blank; exterior setback inferred from V01/P02'
# Remove unused imported datablocks, then save resolvable local image paths.
for group in [bpy.data.meshes,bpy.data.materials,bpy.data.images,bpy.data.node_groups]:
    for block in group:
        block.use_fake_user = False
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
for image in bpy.data.images:
    if image.source == 'FILE' and image.filepath:
        path = Path(bpy.path.abspath(image.filepath)).resolve()
        assert path.is_file()
        target = TEX / (hashlib.sha256(path.read_bytes()).hexdigest()[:12] + path.suffix)
        if path != target:
            shutil.copyfile(path, target)
        image.filepath = str(target)
blend = OUT / 'Courtyard43-props.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath: im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath))
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
result={'source':str(blend),'objects':len(scene.objects),'meshes':sum(o.type=='MESH' for o in scene.objects),'images':len(bpy.data.images)}
