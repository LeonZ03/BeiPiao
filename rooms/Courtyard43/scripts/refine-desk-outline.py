"""Refine desk silhouette and chair fastener contacts via official MCP only.

Do not regenerate furniture02: its accepted materials/bed detail are retained.
P01/P03/P04 show rounded desk corners and a subtly curved front. The approved
width, depth, height, support frame and position stay fixed. Curve/corner detail
is estimated from photographs, not a new product specification or measurement.
"""
from pathlib import Path
import hashlib
import json
import math
import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
SOURCE = ROOM / 'assets/furniture/Courtyard43-furniture.blend'
REPORT = ROOT / 'analysis/Courtyard43/furniture'
REPORT.mkdir(parents=True, exist_ok=True)
PARENT_HASH = 'b76e9abea81afbce46c82a1e773b60daffb6c7c311a8c80f6dc98bf58de168a0'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == PARENT_HASH
scene = bpy.context.scene
assert scene['component'] == 'furniture'
assert scene['component_revision'] == 'courtyard43-furniture02'
assert scene['parent_revision'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
coll = bpy.data.collections['C43_Furniture']
desk = bpy.data.objects['C43_DeskTop']
rivets = sorted([o for o in coll.all_objects if o.name.startswith('C43_ChairBackRivet')], key=lambda o: o.name)
assert len(rivets) == 4
target_names = {desk.name, *(o.name for o in rivets)}


def bp(p):
    return Vector((p[0], -p[2], p[1]))


def evaluated(o):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj = o.evaluated_get(depsgraph)
    mesh = obj.to_mesh()
    mesh.calc_loop_triangles()
    vertices = [o.matrix_world @ v.co for v in mesh.vertices]
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    obj.to_mesh_clear()
    return vertices, triangles


def bounds(o):
    vertices, _ = evaluated(o)
    web = [(v.x, v.z, -v.y) for v in vertices]
    return [[min(v[i] for v in web) for i in range(3)],
            [max(v[i] for v in web) for i in range(3)]]


def digest(o):
    h = hashlib.sha256()
    h.update(repr((o.type, o.parent.name if o.parent else None,
                   tuple(tuple(row) for row in o.matrix_world), dict(o.items()))).encode())
    if o.type == 'MESH':
        vertices, triangles = evaluated(o)
        h.update(repr(([tuple(v) for v in vertices], triangles)).encode())
        h.update(repr([(u.name, [tuple(i.uv) for i in u.data]) for u in o.data.uv_layers]).encode())
        h.update(repr([m.name for m in o.data.materials]).encode())
    return h.hexdigest()


bpy.context.view_layer.update()
before = {o.name: digest(o) for o in coll.all_objects if o.name not in target_names}
old_bounds = bounds(desk)
x0, y0, z0 = old_bounds[0]
x1, y1, z1 = old_bounds[1]
dx = (x0 + x1) / 2
rear_radius = .025
front_radius = .035
front_curve = .012
front_end = z1 - front_curve
outline = []


def corner(cx, cz, radius, start, stop):
    for i in range(9):
        angle = start + (stop - start) * i / 8
        outline.append((cx + radius * math.cos(angle), cz + radius * math.sin(angle)))


corner(x0 + rear_radius, z0 + rear_radius, rear_radius, math.pi, 1.5 * math.pi)
corner(x1 - rear_radius, z0 + rear_radius, rear_radius, 1.5 * math.pi, 2 * math.pi)
corner(x1 - front_radius, front_end - front_radius, front_radius, 0, math.pi / 2)
for i in range(1, 49):
    x = x1 - front_radius - (x1 - x0 - 2 * front_radius) * i / 48
    z = front_end + front_curve * math.cos(math.pi * (x - dx) / (x1 - x0 - 2 * front_radius)) ** 2
    outline.append((x, z))
corner(x0 + front_radius, front_end - front_radius, front_radius, math.pi / 2, math.pi)
# Remove exact meeting points to avoid zero-length edges in the solid prism.
clean = []
for point in outline:
    if not clean or math.dist(clean[-1], point) > 1e-8:
        clean.append(point)
outline = clean
inv = desk.matrix_world.inverted()
vertices = [inv @ bp((x, y, z)) for y in (y0, y1) for x, z in outline]
n = len(outline)
faces = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
faces.extend((i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n))
mesh = bpy.data.meshes.new('C43_Desk_RoundedCurvedTopMesh')
mesh.from_pydata(vertices, [], faces)
for material in desk.data.materials:
    mesh.materials.append(material)
bm = bmesh.new()
bm.from_mesh(mesh)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh)
bm.free()
mesh.update()
# Preserve existing wood mapping scale; the furniture's UV1 is available for
# its separate fine surface detail. No material/image/texture is modified.
for name, density in [('UVMap', 1), ('UV1', 24)]:
    uv = mesh.uv_layers.new(name=name)
    for poly in mesh.polygons:
        axis = max(range(3), key=lambda i: abs(poly.normal[i]))
        for li in poly.loop_indices:
            v = mesh.vertices[mesh.loops[li].vertex_index].co
            pair = ((v.y, v.z), (v.x, v.z), (v.x, v.y))[axis]
            uv.data[li].uv = (pair[0] * density, pair[1] * density)
old_mesh = desk.data
desk.data = mesh
if old_mesh.users == 0:
    bpy.data.meshes.remove(old_mesh)
for modifier in list(desk.modifiers):
    desk.modifiers.remove(modifier)
edge = desk.modifiers.new('Rounded board edge', 'BEVEL')
edge.width = .0025
edge.segments = 3
edge.harden_normals = True
normal = desk.modifiers.new('Weighted planar normals', 'WEIGHTED_NORMAL')
normal.keep_sharp = True
desk['construction'] = 'Solid 30 mm desktop; photo-estimated rounded corners and broad shallow convex front; approved envelope retained'

# Re-seat the four existing fastener heads against the actual curved white
# chair back. Their old fixed Z was disconnected from the lower curved shell.
back = bpy.data.objects['C43_ChairWhiteCurvedBack']
bpy.context.view_layer.update()
back_vertices, back_triangles = evaluated(back)
back_tree = BVHTree.FromPolygons(back_vertices, back_triangles, all_triangles=True)
rivet_checks = []
for rivet in rivets:
    bb = bounds(rivet)
    x = (bb[0][0] + bb[1][0]) / 2
    y = (bb[0][1] + bb[1][1]) / 2
    origin = bp((x, y, 1.5))
    hit, normal_hit, _, _ = back_tree.ray_cast(origin, Vector((0, 1, 0)))
    assert hit is not None, (rivet.name, 'Rivet must be over real chair back')
    surface_z = -hit.y
    old_base = bb[0][2]
    # Embed the shaft 2 mm, leaving a 6 mm visible head; same cylinder size.
    delta = surface_z - .002 - old_base
    matrix = rivet.matrix_world.copy()
    matrix.translation.y -= delta
    rivet.matrix_world = matrix
    rivet_checks.append({'name': rivet.name, 'oldBackSurfaceGap': old_base - surface_z,
                         'newShaftEmbedDepth': .002, 'translationWebZ': delta})
bpy.context.view_layer.update()
new_bounds = bounds(desk)
assert all(abs(a - b) < 2e-6 for aa, bb in zip(old_bounds, new_bounds) for a, b in zip(aa, bb)), (old_bounds, new_bounds)
assert before == {o.name: digest(o) for o in coll.all_objects if o.name in before}
topology = []
for obj in [desk, *rivets]:
    check = bmesh.new()
    check.from_mesh(obj.data)
    item = {'object': obj.name, 'nonManifoldEdges': sum(not e.is_manifold for e in check.edges),
            'zeroAreaFaces': sum(f.calc_area() < 1e-14 for f in check.faces),
            'signedVolume': check.calc_volume(signed=True)}
    assert item['nonManifoldEdges'] == item['zeroAreaFaces'] == 0 and item['signedVolume'] > 0, item
    assert all(math.isfinite(c) for v in check.verts for c in v.co)
    check.free()
    topology.append(item)
    if obj in rivets:
        vv, tt = evaluated(obj)
        assert BVHTree.FromPolygons(vv, tt, all_triangles=True).overlap(back_tree), obj.name
scene['component_parent_revision'] = 'courtyard43-furniture02'
scene['component_revision'] = 'courtyard43-furniture03'
scene['desk_outline_correction'] = json.dumps({'reference': 'P01/P03/P04',
    'approvedWebBounds': new_bounds, 'dimensionSource': 'Photo-estimated edge detail; existing approved size retained',
    'frontCurveMeters': front_curve, 'cornerRadiiMeters': [rear_radius, front_radius]})
report = {'parentRevision': 'courtyard43-furniture02', 'revision': scene['component_revision'],
          'sourceParentSha256': PARENT_HASH, 'oldDeskWebBounds': old_bounds, 'deskWebBounds': new_bounds,
          'nonTargetObjectDigestsUnchanged': len(before), 'topology': topology,
          'rivets': rivet_checks, 'estimatedFrontCurveMeters': front_curve,
          'estimatedRearFrontCornerRadiiMeters': [rear_radius, front_radius]}
(REPORT / 'desk-outline-check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
result = report
