"""Courtyard43 furniture component, executed only through Blender Lab official MCP.

The approved whitebox06 layout is immutable. Rebuilds this independent component,
never the whitebox, complete interior or Yongwang source. Dimensions are photo
estimates, not measurements. P03/P04 govern the occupied-room appearance.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil
import struct
import zlib

import bpy
import bmesh
import numpy as np
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
OUT = ROOM / 'assets/furniture'
TEX = OUT / 'textures'
REPORT = ROOT / 'analysis/Courtyard43/furniture'
SOURCE = ROOT / 'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
SOURCE_HASH = '67765fb8a97bf6b86d9d272f5319ab8aa047f5330438210ccce063a06833e150'
P = json.loads((ROOM / 'history/inputs/approved-layout.json').read_text(encoding='utf-8'))
assert P['structureApproved'] and P['parentRevision'] == 'courtyard43-whitebox06'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH, 'Reinspect changed source'
for directory in [OUT, TEX, REPORT]:
    directory.mkdir(parents=True, exist_ok=True)

# Read the actual accepted full source. Snapshot evaluated mesh data; no external
# datablock remains shared. Inactive duplicate Principled nodes are ignored.
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
assert bpy.context.scene['web_revision'] == 'sunview34'
source_materials = {}
for object_name in ['full-cotton-pillow', 'duvet-top']:
    mat = bpy.data.objects[object_name].data.materials[0]
    output = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    shader = output.inputs['Surface'].links[0].from_node
    assert shader.type == 'BSDF_PRINCIPLED'
    source_materials[object_name] = {'material': mat.name, 'shader': shader.name, 'images': []}
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            path = Path(bpy.path.abspath(node.image.filepath)).resolve()
            assert path.is_file()
            shutil.copy2(path, TEX / path.name)
            source_materials[object_name]['images'].append({'source': str(path.relative_to(ROOT)).replace('\\', '/'), 'copy': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

source_meshes = []
dg = bpy.context.evaluated_depsgraph_get()
for name in ['full-cotton-pillow', 'pillow-piped-seam']:
    original = bpy.data.objects[name]
    evaluated = original.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    positions = [tuple(original.matrix_world @ vertex.co) for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    uv = [tuple(item.uv) for item in mesh.uv_layers.active.data] if mesh.uv_layers.active else None
    source_meshes.append((name, positions, faces, uv))
    evaluated.to_mesh_clear()

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0
scene['room_id'] = 'Courtyard43'
scene['component'] = 'furniture'
scene['component_revision'] = 'courtyard43-furniture02'
scene['parent_revision'] = P['parentRevision']
scene['approved_layout_commit'] = P['approval']['baselineCommit']
scene['dimensions_source'] = 'Photo estimates; whitebox06 proportions approved, not measured'
scene['source_sha256'] = SOURCE_HASH
scene['source_materials'] = json.dumps(source_materials, ensure_ascii=False)
scene['editing_workflow'] = 'Official Blender Lab MCP'
collection = bpy.data.collections.new('C43_Furniture')
scene.collection.children.link(collection)


def bp(point):
    return Vector((point[0], -point[2], point[1]))


def yp(point):
    return (point[0], point[2], -point[1])


def attach(obj, name, material=None, parent=None, **tags):
    obj.name = 'C43_' + name
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection.objects.link(obj)
    if material:
        obj.data.materials.append(material)
    if parent:
        bpy.context.view_layer.update()
        matrix = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = matrix
    obj['web_tags'] = json.dumps(tags)
    return obj


def empty(name, center=(0, 0, 0), parent=None):
    obj = bpy.data.objects.new('C43_' + name, None)
    collection.objects.link(obj)
    obj.location = bp(center)
    if parent:
        obj.parent = parent
    bpy.context.view_layer.update()
    return obj


def material(name, color, rough=.6, metal=0, category=None):
    mat = bpy.data.materials.new('C43_' + name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Roughness'].default_value = rough
    shader.inputs['Metallic'].default_value = metal
    mat.diffuse_color = (*color, 1)
    mat.roughness = rough
    mat.metallic = metal
    if category:
        mat['web_userData'] = json.dumps({'surfaceCategory': category})
    return mat


def image_node(mat, path, color=True, uv='UVMap'):
    image = bpy.data.images.load(str(path), check_existing=False)
    image.name = 'C43_' + path.stem
    image.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    image.filepath = '//textures/' + path.name
    node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    node.extension = 'REPEAT'
    uvnode = mat.node_tree.nodes.new('ShaderNodeUVMap')
    uvnode.uv_map = uv
    mat.node_tree.links.new(uvnode.outputs['UV'], node.inputs['Vector'])
    return node


def cloth_material(name, floral=False):
    mat = material(name, (.82, .80, .75), .89, category='cotton')
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Sheen Weight'].default_value = .21
    color = image_node(mat, TEX / ('quilt-flat-floral-v2.png' if floral else 'woven-cloth.jpg'))
    mat.node_tree.links.new(color.outputs['Color'], shader.inputs['Base Color'])
    relief = image_node(mat, TEX / 'cotton-thread-relief.png', color=False, uv='UV1')
    bump = mat.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .18
    bump.inputs['Distance'].default_value = .0003
    mat.node_tree.links.new(relief.outputs['Color'], bump.inputs['Height'])
    mat.node_tree.links.new(bump.outputs['Normal'], shader.inputs['Normal'])
    mat['provenance'] = 'Independent copy of sunview34 accepted cotton images; new PBR nodes'
    return mat


def generated_texture(name, values, color=True):
    # Color values here are TARGET PNG sRGB bytes, never scene-linear pixel
    # buffer values. Direct PNG encoding avoids implicit Blender save transforms.
    # Data maps are likewise untransformed scalar bytes, loaded as Non-Color.
    height, width = values.shape[:2]
    rgb = np.repeat(values[:, :, None], 3, axis=2) if values.ndim == 2 else values
    encoded = np.rint(np.clip(rgb, 0, 1) * 255).astype(np.uint8)
    rows = b''.join(b'\x00' + row.tobytes() for row in encoded)
    def chunk(kind, payload):
        return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    if color:
        png += chunk(b'sRGB', b'\x00')
    png += chunk(b'IDAT', zlib.compress(rows, 6)) + chunk(b'IEND', b'')
    path = TEX / (name + '.png')
    path.write_bytes(png)
    assert zlib.decompress(zlib.compress(rows, 6)) == rows
    return path


def srgb_to_linear(color):
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in color)


# P03 calibration: pale low-saturation maple, with a target sRGB mean #D4C7B2.
# Fine irregular fibres have only 2-3 code values of contrast. No baked light.
yy, xx = np.mgrid[0:768, 0:768].astype(np.float32) / 768
rng = np.random.default_rng(4306)
fibres = rng.normal(0, .58, 192)
fibre_x = np.mod(xx + .0028 * np.sin(yy * 8.4) + .0011 * np.sin(yy * 17.3 + .6), 1)
grain = np.interp(fibre_x, np.linspace(0, 1, len(fibres)), fibres)
grain += .14 * np.sin((xx * 37 + .11 * np.sin(yy * 6)) * math.tau) + rng.normal(0, .10, xx.shape)
grain = np.clip(grain, -1, 1)
maple_srgb = np.array([212, 199, 178], dtype=np.float32) / 255
wood_colors = maple_srgb[None, None, :] + grain[:, :, None] * np.array([.010, .009, .007])
wood_color = generated_texture('maple-laminate-color', np.clip(wood_colors, 0, 1))
wood_rough = generated_texture('maple-laminate-roughness', np.clip(.58 + grain * .012, 0, 1), False)
wood = material('MapleLaminate', srgb_to_linear(maple_srgb), .58, category='laminateWood')
shader = wood.node_tree.nodes.get('Principled BSDF')
wood.node_tree.links.new(image_node(wood, wood_color).outputs['Color'], shader.inputs['Base Color'])
wood.node_tree.links.new(image_node(wood, wood_rough, False).outputs['Color'], shader.inputs['Roughness'])
wood_edge = material('MapleEdgeBand', srgb_to_linear(np.array([208, 193, 167]) / 255), .61, category='laminateWood')
white = material('WarmWhiteLaminate', (.79, .785, .755), .49, category='laminate')
steelwhite = material('WhitePowderCoatedSteel', (.80, .81, .785), .38, .14, 'paintedSteel')
nickel = material('BrushedNickel', (.42, .43, .42), .28, .83, 'metal')
black = material('ChairBlackSeat', (.023, .025, .024), .72, category='upholstery')
rubber = material('DarkRubberFeet', (.016, .017, .015), .91, category='rubber')
cream = material('CottonSeam', (.79, .765, .70), .95, category='cotton')
floral = cloth_material('FloralCotton', True)
linen = cloth_material('PlainCotton', False)
interior = material('WardrobeInterior', (.68, .66, .58), .69, category='laminate')


def box(name, center, dimensions, mat, bevel=.003, parent=None, smooth=False):
    bpy.ops.mesh.primitive_cube_add(size=1, location=bp(center))
    obj = bpy.context.object
    obj.dimensions = (dimensions[0], dimensions[2], dimensions[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    attach(obj, name, mat, parent)
    if bevel:
        mod = obj.modifiers.new('Real softened edge', 'BEVEL')
        mod.width = min(bevel, min(dimensions) * .42)
        mod.segments = 3
        mod.harden_normals = True
        normals = obj.modifiers.new('Weighted planar normals', 'WEIGHTED_NORMAL')
        normals.keep_sharp = True
    if smooth:
        for poly in obj.data.polygons:
            poly.use_smooth = True
    return obj


def tube(name, points, radius, mat, parent=None, closed=False, sides=10):
    # Parallel-transport-like frame with stable local tangent. Solid end caps.
    pts = [bp(p) for p in points]
    vertices, faces = [], []
    for index, point in enumerate(pts):
        prev = pts[(index - 1) % len(pts)] if closed or index else point
        nxt = pts[(index + 1) % len(pts)] if closed or index < len(pts) - 1 else point
        tangent = (nxt - prev).normalized()
        axis = Vector((0, 0, 1)) if abs(tangent.z) < .92 else Vector((1, 0, 0))
        a = tangent.cross(axis).normalized()
        b = tangent.cross(a).normalized()
        for j in range(sides):
            angle = j * math.tau / sides
            vertices.append(point + radius * (a * math.cos(angle) + b * math.sin(angle)))
    segments = len(pts) if closed else len(pts) - 1
    for i in range(segments):
        k = (i + 1) % len(pts)
        for j in range(sides):
            faces.append((i * sides + j, i * sides + (j + 1) % sides, k * sides + (j + 1) % sides, k * sides + j))
    if not closed:
        faces.extend([tuple(reversed(range(sides))), tuple((len(pts) - 1) * sides + j for j in range(sides))])
    return mesh_object(name, vertices, faces, mat, parent=parent, already_blender=True)


def mesh_object(name, vertices, faces, mat, uvs=None, parent=None, already_blender=False):
    mesh = bpy.data.meshes.new('C43_' + name + 'Mesh')
    mesh.from_pydata(vertices if already_blender else [bp(v) for v in vertices], [], faces)
    mesh.update()
    mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name='UVMap')
    thread = mesh.uv_layers.new(name='UV1')
    for poly in mesh.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            co = mesh.vertices[vi].co
            val = uvs[vi] if uvs is not None else (co.x, co.y)
            uv.data[li].uv = val
            thread.data[li].uv = (val[0] * 24, val[1] * 24)
    obj = bpy.data.objects.new('C43_' + name, mesh)
    collection.objects.link(obj)
    obj['web_tags'] = '{}'
    if parent:
        bpy.context.view_layer.update()
        obj.parent = parent
        obj.matrix_world = Matrix.Identity(4)
    return obj


left = P['room']['centerX'] - P['room']['width'] / 2
right = P['room']['centerX'] + P['room']['width'] / 2
bedp = P['bed']
bx, bz = left + .06 + bedp['length'] / 2, bedp['centerZ']
x0, x1 = bx - bedp['length'] / 2, bx + bedp['length'] / 2
z0, z1 = bz - bedp['width'] / 2, bz + bedp['width'] / 2
bed = empty('Bed')
# Flat white headboard and round legs are photograph-specific, not the previous
# room's upholstered platform. The supporting platform retains exact massing.
box('BedPlatform', (bx, .3925, bz), (2.4, .045, 1.5), wood_edge, .006, bed)
for zi in [z0 + .035, z1 - .035]:
    box('BedLongSteelRail', (bx, .347, zi), (2.31, .047, .035), steelwhite, .004, bed)
for xi in [x0 + .07, x1 - .06]:
    box('BedCrossSteelRail', (xi, .347, bz), (.035, .047, 1.40), steelwhite, .004, bed)
for i, xi in enumerate([left + .13, left + bedp['length'] - .05]):
    for j, zi in enumerate([z0 + .09, z1 - .09]):
        tube('BedRoundLeg%d%d' % (i, j), [(xi, .018, zi), (xi, .372, zi)], .020, steelwhite, bed, sides=24)
        tube('BedFootCap%d%d' % (i, j), [(xi, 0, zi), (xi, .021, zi)], .0204, rubber, bed, sides=24)
box('BedHeadboard', (left + .065, .72, bz), (.06, .78, 1.54), white, .013, bed)
box('Mattress', (bx, .485, bz), (2.375, .14, 1.475), linen, .026, bed, True)
# Subtle mattress perimeter piping has genuine round section.
for height in [.428, .544]:
    points = []
    for j in range(144):
        a = j / 144 * math.tau
        points.append((bx + 1.169 * math.copysign(abs(math.cos(a)) ** .24, math.cos(a)), height,
                       bz + .720 * math.copysign(abs(math.sin(a)) ** .24, math.sin(a))))
    tube('MattressPiping', points, .0016, cream, bed, True, 6)


def bend_over(value, low, high, radius=.026):
    if low <= value <= high:
        return value, 0
    sign = -1 if value < low else 1
    edge = low if sign < 0 else high
    excess = low - value if sign < 0 else value - high
    arc = min(excess / radius, math.pi / 2)
    rest = max(0, excess - math.pi / 2 * radius)
    return edge + sign * (radius * math.sin(arc) + rest * .055), radius * (1 - math.cos(arc)) + rest


def cloth_surface(kind, u, v):
    if kind == 'sheet':
        sx = x0 + .047 + u * (2.36 + .26)
        sz = z0 - .24 + v * (1.5 + .245)
        x, dropx = bend_over(sx, x0 + .025, x1 - .010, .028)
        z, dropz = bend_over(sz, z0 + .012, z1 - .012, .023)
        drop = math.sqrt(dropx * dropx + dropz * dropz)
        y = .5615 - drop
        outside = min(1, drop / .045)
        z -= outside * .006 * math.sin(sx * 16 + .3)
        x += outside * .006 * math.sin(sz * 21 + .2)
        y += outside * .007 * math.sin(sx * 11 + sz * 5)
        return (x, y, z)
    # Broad diagonal folds and an irregular retreat at the pillow edge. Closed
    # shell thickness is 7 mm; no sharp stacked sine-wave pleats.
    sx = -1.47 + u * 2.06 + .014 * math.sin(v * 8.2) * (1 - u) ** 7
    sz = z0 - .070 + v * (1.5 + .090)
    x, dropx = bend_over(sx, x0 + .035, x1 + .001, .037)
    z, dropz = bend_over(sz, z0 - .003, z1 + .003, .030)
    drop = math.sqrt(dropx * dropx + dropz * dropz)
    edgefade = math.exp(-drop * 24)
    ridge1 = .044 * math.exp(-((sx + .82 - .52 * (sz - bz)) / .14) ** 2)
    ridge2 = .033 * math.exp(-((sx + .10 + .72 * (sz - bz)) / .16) ** 2)
    ridge3 = .021 * math.exp(-((sz - 1.70 + .16 * sx) / .095) ** 2)
    # Two localized broad accumulations make the folds end and merge naturally.
    pile = .024 * math.exp(-((sx + 1.13) / .23) ** 2 - ((sz - 2.30) / .26) ** 2)
    pile += .015 * math.exp(-((sx - .10) / .23) ** 2 - ((sz - 1.55) / .22) ** 2)
    broad = .0065 * math.sin(sx * 3.3 + sz * 2.1) + .004 * math.sin(sz * 5.1 - sx)
    headturn = .024 * math.exp(-u * 42) * (.65 + .35 * math.sin(v * 5 + 1))
    hem_lift = min(1, drop / .065) * (.025 * math.exp(-((sx + .62) / .23) ** 2) +
        .018 * math.exp(-((sz - 2.2) / .21) ** 2) * min(1, dropx / .07))
    y = .583 + (ridge1 + ridge2 + ridge3 + pile + broad + headturn) * edgefade - drop + hem_lift
    z -= .005 * math.sin(sx * 8 + .2) * min(1, dropz / .03)
    x += .008 * math.sin(sz * 7 + .8) * min(1, dropx / .04)
    return (x, y, z)


def cloth_shell(name, kind, nx, nz, thickness, mat):
    surface = np.array([[cloth_surface(kind, i / nx, j / nz) for i in range(nx + 1)] for j in range(nz + 1)])
    tangent_z, tangent_x = np.gradient(surface, axis=(0, 1))
    normal = np.cross(tangent_z, tangent_x)
    normal /= np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-12)
    upper = surface.reshape(-1, 3)
    lower = (surface - normal * thickness).reshape(-1, 3)
    vertices = np.concatenate([upper, lower]).tolist()
    layer = len(upper)
    print_repeat = 1 / .78 if kind == 'duvet' else 1
    uvs = [(i / nx * (1.58 if kind == 'duvet' else 2.2) * print_repeat, j / nz * (1.22 if kind == 'duvet' else 1.5) * print_repeat) for j in range(nz + 1) for i in range(nx + 1)]
    uvs += uvs.copy()
    faces = []
    for j in range(nz):
        for i in range(nx):
            k = j * (nx + 1) + i
            faces.extend([(k, k + nx + 1, k + nx + 2, k + 1),
                          (k + layer, k + 1 + layer, k + nx + 2 + layer, k + nx + 1 + layer)])
    edge = list(range(nx + 1)) + [j * (nx + 1) + nx for j in range(1, nz + 1)] + [nz * (nx + 1) + i for i in range(nx - 1, -1, -1)] + [j * (nx + 1) for j in range(nz - 1, 0, -1)]
    for i, k in enumerate(edge):
        nxt = edge[(i + 1) % len(edge)]
        faces.append((k, nxt, nxt + layer, k + layer))
    obj = mesh_object(name, vertices, faces, mat, uvs, bed)
    if kind == 'duvet':
        # Print changes size; physical cotton threads do not.
        for item in obj.data.uv_layers['UV1'].data:
            item.uv /= print_repeat
    obj['cloth_thickness_m'] = thickness
    obj['construction'] = 'Continuous closed sewn shell; analytic rounded mattress-edge drape'
    seam = [tuple((np.array(vertices[k]) + np.array(vertices[k + layer])) / 2) for k in edge]
    tube(name + 'SewnHem', seam, .0011 if kind == 'sheet' else .0018, cream, bed, True, 6)
    return obj


sheet = cloth_shell('DrapedWhiteSheet', 'sheet', 94, 68, .0018, linen)
duvet = cloth_shell('FloralDuvet', 'duvet', 114, 90, .007, floral)

# Uniformly preserve the final accepted pillow geometry, reorient 90 degrees in
# plan, and translate its actual minimum to the new sheet's support surface.
arr = np.array(source_meshes[0][1])
old_center = (arr.min(0) + arr.max(0)) / 2
old_center[2] = arr[:, 2].min()
for source_name, positions, faces, source_uv in source_meshes:
    transformed = []
    for point in positions:
        local = np.array(point) - old_center
        transformed.append((-local[1] - 1.704, local[0] - bz, local[2] + .5618))
    name = 'CottonPillow' if source_name == 'full-cotton-pillow' else 'PillowPipedSeam'
    obj = mesh_object(name, transformed, faces, linen if source_name == 'full-cotton-pillow' else cream, parent=bed, already_blender=True)
    if source_uv:
        for li, value in enumerate(source_uv):
            obj.data.uv_layers['UVMap'].data[li].uv = value
            obj.data.uv_layers['UV1'].data[li].uv = (value[0] * 16, value[1] * 12)
    # The accepted source contains coincident split seam endpoints. Weld only
    # this independent copy at micron tolerance, retaining shape and corner UVs.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=.000001)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj['provenance'] = json.dumps({'sourceObject': source_name, 'sourceRoom': 'yongwang-jiayuan', 'webRevision': 'sunview34', 'sourceSha256': SOURCE_HASH, 'baselineCommit': P['approval']['baselineCommit'], 'mode': 'Independent evaluated mesh copy; rigid reorientation and translation only'})

# Table long side follows X; seated user faces -Z and the back faces the bed.
deskp = P['desk']
dx, dz = left + deskp['width'] / 2 + .025, deskp['centerZ']
desk = empty('Desk')
box('DeskTop', (dx, .725, dz), (1.3, .030, .55), wood, .007, desk)
for i, xi in enumerate([dx - .605, dx + .605]):
    for j, zi in enumerate([dz - .230, dz + .230]):
        box('DeskSquareLeg%d%d' % (i, j), (xi, .365, zi), (.029, .690, .029), steelwhite, .003, desk)
        box('DeskFoot%d%d' % (i, j), (xi, .010, zi), (.030, .020, .030), rubber, .003, desk)
    tube('DeskSideBrace%d' % i, [(xi, .165, dz + .215), (xi, .33, dz + .176), (xi, .49, dz + .07), (xi, .695, dz - .09)], .008, steelwhite, desk, sides=10)
    box('DeskSideApron%d' % i, (xi, .681, dz), (.020, .056, .48), steelwhite, .003, desk)
box('DeskBackApron', (dx, .681, dz - .230), (1.20, .056, .020), steelwhite, .003, desk)

cz = P['deskChair']['centerZ']
chair = empty('DeskChair')
box('ChairSeatFrame', (dx, .427, cz), (.39, .030, .39), steelwhite, .006, chair)
box('ChairBlackCushion', (dx, .454, cz - .008), (.395, .048, .395), black, .021, chair, True)
for i, xi in enumerate([dx - .172, dx + .172]):
    tube('ChairFrontLeg%d' % i, [(xi, .014, cz - .184), (xi, .245, cz - .161), (xi, .440, cz - .152)], .011, nickel, chair, sides=16)
    tube('ChairBackFrame%d' % i, [(xi, .014, cz + .210), (xi, .425, cz + .154), (xi, .59, cz + .199), (xi, .87, cz + .222)], .011, nickel, chair, sides=16)
    for j, zi in enumerate([cz - .184, cz + .210]):
        tube('ChairRubberFoot%d%d' % (i, j), [(xi, 0, zi), (xi, .020, zi)], .0128, rubber, chair, sides=12)
    tube('ChairSideRail%d' % i, [(xi, .416, cz - .174), (xi, .416, cz + .178)], .010, nickel, chair, sides=12)
# Shallow concave shell, rounded outline and 5 mm thickness; the white back is
# a real curved panel, not a plane or a large upholstered office-chair body.
verts, uvs, faces = [], [], []
nx, ny = 32, 24
for side in [0, 1]:
    for j in range(ny + 1):
        v = j / ny
        for i in range(nx + 1):
            u = i / nx * 2 - 1
            width = .189 - .018 * (1 - v) ** 3 - .012 * abs(2 * v - 1) ** 12
            y = .617 + v * .257 - .009 * abs(u) ** 8 * abs(2 * v - 1) ** 6
            z = cz + .195 + .029 * v + .016 * (1 - u * u) + side * .005
            verts.append((dx + width * u, y, z))
            uvs.append((i / nx, v))
layer = (nx + 1) * (ny + 1)
for j in range(ny):
    for i in range(nx):
        k = j * (nx + 1) + i
        faces.extend([(k, k + 1, k + nx + 2, k + nx + 1), (k + layer, k + nx + 1 + layer, k + nx + 2 + layer, k + 1 + layer)])
edge = list(range(nx + 1)) + [j * (nx + 1) + nx for j in range(1, ny + 1)] + [ny * (nx + 1) + i for i in range(nx - 1, -1, -1)] + [j * (nx + 1) for j in range(ny - 1, 0, -1)]
for i, k in enumerate(edge):
    nxt = edge[(i + 1) % len(edge)]
    faces.append((k, nxt, nxt + layer, k + layer))
mesh_object('ChairWhiteCurvedBack', verts, [tuple(reversed(face)) for face in faces], white, uvs, chair)
for xi in [dx - .174, dx + .174]:
    for y in [.655, .831]:
        tube('ChairBackRivet', [(xi, y, cz + .236), (xi, y, cz + .244)], .005, nickel, chair, sides=12)

# Separate boards provide a credible empty interior and allow both doors to
# move. The unseen shelf/rail arrangement is explicitly a minimal inference.
wp = P['wardrobe']
wardrobe = empty('Wardrobe')
wx0, wx1 = right - wp['depth'], right
wz0, wz1 = wp['centerZ'] - wp['width'] / 2, wp['centerZ'] + wp['width'] / 2
for label, zi in [('Far', wz0 + .009), ('Near', wz1 - .009)]:
    box('Wardrobe' + label + 'Side', ((wx0 + wx1) / 2, 1.025, zi), (.55, 2.05, .018), wood, .002, wardrobe)
box('WardrobeBack', (wx1 - .008, 1.04, wp['centerZ']), (.012, 1.99, 1.114), interior, .0015, wardrobe)
for label, y in [('Base', .073), ('Top', 2.041), ('Shelf', 1.615)]:
    box('Wardrobe' + label, ((wx0 + wx1) / 2, y, wp['centerZ']), (.535, .018, 1.114), interior if label != 'Top' else wood, .002, wardrobe)
box('WardrobeToeKick', (wx0 + .058, .028, wp['centerZ']), (.022, .056, 1.114), wood_edge, .002, wardrobe)
tube('WardrobeHangingRail', [(wx0 + .286, 1.511, wz0 + .03), (wx0 + .286, 1.511, wz1 - .03)], .0125, nickel, wardrobe, sides=20)
for zi in [wz0 + .023, wz1 - .023]:
    tube('WardrobeRailSocket', [(wx0 + .286, 1.511, zi - .007), (wx0 + .286, 1.511, zi + .007)], .022, nickel, wardrobe, sides=20)
wardrobe['interior_evidence'] = 'Unseen interior: minimal inferred empty cabinet, one high shelf and a rail; no invented contents or mirror'

door_pivots = []
door_meshes = []
for label, sign in [('Far', -1), ('Near', 1)]:
    hinge_z = wz0 + .010 if sign < 0 else wz1 - .010
    center_z = wp['centerZ'] - wp['width'] / 4 if sign < 0 else wp['centerZ'] + wp['width'] / 4
    pivot = empty('WardrobeDoor' + label + 'Pivot', (wx0 - .032, 0, hinge_z), wardrobe)
    # Empty's parent's transform is identity, preserving the documented world axis.
    angle = math.radians(-72 if sign < 0 else 90)
    pivot['c43_interaction'] = json.dumps({'id': 'wardrobe' + label, 'kind': 'hinge', 'axis': 'y', 'openAngle': angle, 'audio': 'wardrobe'})
    pivot['clearance_note'] = 'Far door limited to 72 degrees to retain >20 mm clearance at approved radiator cap; near door 90 degrees'
    door = box('WardrobeDoor' + label, (wx0 - .016, 1.025, center_z), (.026, 2.025, .567), white, .004, pivot)
    handle_z = wp['centerZ'] - .055 if sign < 0 else wp['centerZ'] + .055
    hx = wx0 - .060
    tube('Wardrobe' + label + 'Handle', [(hx + .020, .876, handle_z), (hx, .886, handle_z), (hx, 1.115, handle_z), (hx + .020, 1.125, handle_z)], .0065, nickel, pivot, sides=16)
    for y in [.902, 1.099]:
        tube('Wardrobe' + label + 'HandleMount', [(wx0 - .030, y, handle_z), (hx, y, handle_z)], .006, nickel, pivot, sides=12)
    for index, y in enumerate([.235, 1.025, 1.813]):
        # Small hinge barrel on the actual pivot, a fixed plate, and a moving
        # door leaf. These do not introduce an oversized click target.
        tube('Wardrobe' + label + 'HingePin%d' % index, [(wx0 - .032, y - .029, hinge_z), (wx0 - .032, y + .029, hinge_z)], .006, nickel, wardrobe, sides=16)
        box('Wardrobe' + label + 'FixedHinge%d' % index, (wx0 + .022, y, hinge_z), (.073, .044, .003), nickel, .001, wardrobe)
        box('Wardrobe' + label + 'MovingHinge%d' % index, (wx0 - .002, y, hinge_z - sign * .025), (.006, .034, .05), nickel, .001, pivot)
    door_pivots.append(pivot)
    door_meshes.append(door)

# Wood UVs use actual face axes. Long grain follows vertical cabinetry and the
# long edge of the desk. Cubes otherwise retain Blender's valid UVs.
for obj in collection.objects:
    if obj.type != 'MESH' or not obj.data.materials or obj.data.materials[0] != wood:
        continue
    uv = obj.data.uv_layers.active
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            co = obj.data.vertices[obj.data.loops[li].vertex_index].co
            if obj.name == 'C43_DeskTop':
                uv.data[li].uv = (co.y * 1.4 + .5, co.x * .8 + .5)
            elif abs(poly.normal.y) > .5:
                uv.data[li].uv = (co.x * 1.5 + .5, co.z * .55 + .5)
            else:
                uv.data[li].uv = (co.y * 1.3 + .5, co.z * .55 + .5)

# Every image is a local independent copy. Keep a reproducible provenance file.
for obj in collection.objects:
    if obj.type != 'MESH':
        continue
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if bm.calc_volume(signed=True) < 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
provenance = {'room': 'Courtyard43', 'revision': scene['component_revision'], 'baselineCommit': P['approval']['baselineCommit'], 'sourceRoom': 'yongwang-jiayuan', 'sourceFile': str(SOURCE.relative_to(ROOT)).replace('\\', '/'), 'sourceSha256': SOURCE_HASH, 'sourceWebRevision': 'sunview34', 'sources': source_materials, 'pillowMesh': 'Copied evaluated final mesh, rigid transform only', 'duvetMesh': 'New continuous closed thin shell with wide diagonal folds; same accepted flower texture', 'newSurfaces': 'Maple color and roughness deterministically generated in Blender MCP; white laminate and metals are independent Principled PBR', 'layout': 'approved-layout.json; no approved major anchor moved', 'uncertainty': 'All dimensions remain photo estimates. Empty wardrobe shelf and rail are inferred.'}
provenance['appearanceCalibration'] = {
    'reference': 'P03 occupied-room photograph; post-browser first QA',
    'mapleColorSrgb8': [212, 199, 178],
    'edgeBandColorSrgb8': [208, 193, 167],
    'colorEncoding': 'PNG RGB bytes are explicit sRGB targets; Principled constant edge color is decoded once to linear; scalar roughness bytes load as Non-Color',
    'grainContrastSrgb8': 'About 2-3 code values; irregular fine longitudinal fibres',
    'floralPrintScaleRelativeToFurniture01': .78,
    'floralUvRepeatMultiplier': 1 / .78,
    'cottonThreadUv1Unchanged': True,
    'clothRefinement': 'Three broad directional folds, two localized shallow accumulations, selectively lifted hem; fixed support surfaces and major boundaries',
    'nonTargetEvaluatedGeometry': '88 mesh coordinate digests unchanged from furniture01',
}
scene['appearance_calibration'] = json.dumps(provenance['appearanceCalibration'])
(OUT / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
bpy.context.view_layer.update()
scene['geometry_contract'] = 'Independent component; all furniture solid, preserved parent hierarchy, web X/Y-up/Z maps Blender X/-Z/Y'
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'Courtyard43-furniture.blend'))
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_HASH
result = {'saved': str(OUT / 'Courtyard43-furniture.blend'), 'objects': len(collection.objects), 'sourceUnchanged': True, 'revision': scene['component_revision'], 'interactions': [json.loads(p['c43_interaction']) for p in door_pivots]}
