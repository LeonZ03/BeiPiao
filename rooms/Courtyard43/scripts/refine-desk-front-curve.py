"""Correct the desktop's concave working edge through official Blender MCP.

Run only against furniture03, opened by execute_blender_code_for_cli. The
user's marked real-object photograph identifies the broad inward curve at
the seated working position. The former 12 mm convex front misunderstood
that silhouette. Curve depth is a photo estimate, not a measured dimension.
Only desktop vertex positions and its construction metadata are changed;
topology, UV0/UV1, materials, transforms, frame and every other object remain.
"""
from pathlib import Path
import hashlib
import json
import math

import bpy
import bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
SOURCE = ROOM / 'assets/furniture/Courtyard43-furniture.blend'
REPORT = ROOT / 'analysis/Courtyard43/furniture'
REPORT.mkdir(parents=True, exist_ok=True)
PARENT_HASH = '39d6255b483e763e5fd36f908cec28e741e54d067a515ed0305a22dc9e856264'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == PARENT_HASH
scene = bpy.context.scene
assert scene['component'] == 'furniture'
assert scene['component_revision'] == 'courtyard43-furniture03'
assert scene['parent_revision'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
coll = bpy.data.collections['C43_Furniture']
desk = bpy.data.objects['C43_DeskTop']
assert desk.data.users == 1
assert [uv.name for uv in desk.data.uv_layers] == ['UVMap', 'UV1']


def evaluated(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(depsgraph)
    mesh = evaluated_obj.to_mesh()
    mesh.calc_loop_triangles()
    vertices = [obj.matrix_world @ v.co for v in mesh.vertices]
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    evaluated_obj.to_mesh_clear()
    return vertices, triangles


def bounds(obj):
    vertices, _ = evaluated(obj)
    web = [(v.x, v.z, -v.y) for v in vertices]
    return [[min(v[i] for v in web) for i in range(3)],
            [max(v[i] for v in web) for i in range(3)]]


def digest(obj):
    payload = [obj.type, obj.parent.name if obj.parent else None,
               tuple(tuple(row) for row in obj.matrix_world), dict(obj.items())]
    if obj.type == 'MESH':
        vertices, triangles = evaluated(obj)
        payload += [[tuple(v) for v in vertices], triangles,
                    [(uv.name, [tuple(item.uv) for item in uv.data]) for uv in obj.data.uv_layers],
                    [m.name for m in obj.data.materials]]
    return hashlib.sha256(repr(payload).encode()).hexdigest()


def uv_signature(mesh):
    return [(uv.name, [tuple(item.uv) for item in uv.data]) for uv in mesh.uv_layers]


bpy.context.view_layer.update()
before = {o.name: digest(o) for o in coll.all_objects if o != desk}
old_bounds = bounds(desk)
old_uv = uv_signature(desk.data)
old_topology = [tuple(p.vertices) for p in desk.data.polygons]
old_materials = [m.name for m in desk.data.materials]
old_matrix = desk.matrix_world.copy()
x0, y0, z0 = old_bounds[0]
x1, y1, z1 = old_bounds[1]
front_radius = .035
old_convex_depth = .012
inward_depth = .080
left_shoulder, right_shoulder = x0 + front_radius, x1 - front_radius
old_front_corner_back = z1 - old_convex_depth - front_radius
inv = desk.matrix_world.inverted()
changed_vertices = 0

# furniture03 already has 48 evenly sampled front segments and real rounded
# corners. Deform only this contour, retaining both UV layers byte for byte.
# The sin-squared bowl has zero slope at both shoulder/corner joins. Its
# center is recessed into the desk; both side working areas retain the full
# approved depth. No geometry outside the original envelope is introduced.
for vertex in desk.data.vertices:
    world = desk.matrix_world @ vertex.co
    wx, wy, wz = world.x, world.z, -world.y
    if wz < old_front_corner_back - 1e-6:
        continue
    t = min(1.0, max(0.0, (wx - left_shoulder) / (right_shoulder - left_shoulder)))
    bowl = math.sin(math.pi * t) ** 2
    new_z = wz + old_convex_depth - (old_convex_depth + inward_depth) * bowl
    vertex.co = inv @ Vector((wx, -new_z, wy))
    changed_vertices += 1
desk.data.update()
desk.data.name = 'C43_Desk_ConcaveWorkingEdgeMesh'
desk['construction'] = ('Solid 30 mm desktop; photo-estimated broad concave working edge, '
                        '80 mm center recess; approved envelope and original UV mapping retained')
bpy.context.view_layer.update()
new_bounds = bounds(desk)
assert all(abs(a - b) < 2e-6 for aa, bb in zip(old_bounds, new_bounds) for a, b in zip(aa, bb)), (old_bounds, new_bounds)
assert old_uv == uv_signature(desk.data)
assert old_topology == [tuple(p.vertices) for p in desk.data.polygons]
assert old_materials == [m.name for m in desk.data.materials]
assert old_matrix == desk.matrix_world
assert before == {o.name: digest(o) for o in coll.all_objects if o != desk}

check = bmesh.new()
check.from_mesh(desk.data)
topology = {'nonManifoldEdges': sum(not edge.is_manifold for edge in check.edges),
            'zeroAreaFaces': sum(face.calc_area() < 1e-14 for face in check.faces),
            'signedVolume': check.calc_volume(signed=True)}
assert topology['nonManifoldEdges'] == topology['zeroAreaFaces'] == 0
assert topology['signedVolume'] > 0
assert all(math.isfinite(c) for vertex in check.verts for c in vertex.co)
check.free()
ev = desk.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = ev.to_mesh()
mesh.calc_loop_triangles()
assert all(math.isfinite(c) for vertex in mesh.vertices for c in (*vertex.co, *vertex.normal))
assert all(triangle.area > 1e-14 for triangle in mesh.loop_triangles)
evaluated_counts = {'vertices': len(mesh.vertices), 'triangles': len(mesh.loop_triangles)}
ev.to_mesh_clear()

# Take top-face curve samples directly from the preserved front contour.
samples = []
for vertex in desk.data.vertices:
    world = desk.matrix_world @ vertex.co
    if abs(world.z - y1) < 1e-6 and left_shoulder - 1e-6 <= world.x <= right_shoulder + 1e-6 and -world.y > .45:
        samples.append([world.x, -world.y])
samples.sort()
assert samples and abs(min(p[1] for p in samples) - (z1 - inward_depth)) < 2e-6
scene['component_parent_revision'] = 'courtyard43-furniture03'
scene['component_revision'] = 'courtyard43-furniture04'
metadata = {'reference': 'User-marked real-object desktop photo, 2026-09-28',
            'dimensionSource': 'Photo-estimated front-edge curvature; approved size retained',
            'curveDirection': 'concave toward rear at seated center',
            'estimatedCenterRecessMeters': inward_depth,
            'cornerRadiiMeters': [.025, front_radius], 'approvedWebBounds': new_bounds}
scene['desk_outline_correction'] = json.dumps(metadata)
report = {'parentRevision': 'courtyard43-furniture03', 'revision': scene['component_revision'],
          'sourceParentSha256': PARENT_HASH, 'target': desk.name,
          'oldDeskWebBounds': old_bounds, 'deskWebBounds': new_bounds,
          'changedBaseVertices': changed_vertices, 'uvLayersUnchanged': True,
          'baseTopologyUnchanged': True, 'desktopMaterialUnchanged': old_materials,
          'nonTargetObjectDigestsUnchanged': len(before), 'nonTargetDigests': before,
          'estimatedCenterRecessMeters': inward_depth, 'frontEdgeTopSamplesXZ': samples,
          'topology': topology, 'evaluatedCounts': evaluated_counts}
(REPORT / 'desk-front-curve-check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
result = {key: report[key] for key in report if key not in ['nonTargetDigests', 'frontEdgeTopSamplesXZ']}
