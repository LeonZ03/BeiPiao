"""Fill the approved radiator sill to its internal partition; official MCP only.

Parent architecture01 (post-browser colour calibration) is not regenerated.
The user's orange annotation corrects the former inferred rear curtain slot.
All dimensions remain photo estimates inside the existing approved envelope.
Curtain geometry is deliberately untouched: the integration stage must place
the right hem above this sill and the left hem outside its end panel.
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
SOURCE = ROOM / 'assets/architecture/Courtyard43-architecture.blend'
REPORT = ROOT / 'analysis/Courtyard43/architecture'
REPORT.mkdir(parents=True, exist_ok=True)
PARENT_HASH = 'eb58c480be4f106d8b2a6b3c4257e61da5edcbeca96f7cd1a2055f247082317c'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == PARENT_HASH
scene = bpy.context.scene
assert scene['component'] == 'architecture'
assert scene['component_revision'] == 'architecture01'
assert scene['source_layout'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
coll = bpy.data.collections['C43_Architecture']
targets = {'C43_Radiator_Cap_Front', 'C43_Radiator_Cap_RearSupport',
           'C43_Radiator_White_Vertical_Grille'}


def digest(o):
    h = hashlib.sha256()
    h.update(repr((o.type, o.parent.name if o.parent else None,
                   tuple(tuple(row) for row in o.matrix_world), dict(o.items()))).encode())
    if o.type == 'MESH':
        h.update(repr([tuple(v.co) for v in o.data.vertices]).encode())
        h.update(repr([tuple(p.vertices) for p in o.data.polygons]).encode())
        h.update(repr([(u.name, [tuple(i.uv) for i in u.data]) for u in o.data.uv_layers]).encode())
        h.update(repr([(k.name, [tuple(p.co) for p in k.data])
                       for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []).encode())
        h.update(repr([m.name for m in o.data.materials]).encode())
    return h.hexdigest()


def bounds(o):
    q = [o.matrix_world @ v.co for v in o.data.vertices]
    q = [(v.x, v.z, -v.y) for v in q]
    return [[min(v[i] for v in q) for i in range(3)],
            [max(v[i] for v in q) for i in range(3)]]


def uv_project(o):
    uv = o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
    for poly in o.data.polygons:
        axis = max(range(3), key=lambda i: abs(poly.normal[i]))
        for li in poly.loop_indices:
            v = o.matrix_world @ o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv = ((-v.y, v.z), (v.x, v.z), (v.x, -v.y))[axis]


bpy.context.view_layer.update()
before = {o.name: digest(o) for o in coll.all_objects if o.name not in targets}
cap = bpy.data.objects['C43_Radiator_Cap_Front']
old_cap_bounds = bounds(cap)
# Replace only the cap mesh: the stable node/material/metadata remain in place.
bpy.ops.mesh.primitive_cube_add(size=1, location=(.84, -.08, .99))
temporary = bpy.context.object
temporary.dimensions = (1.17, .40, .045)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
edge = temporary.modifiers.new('Manufactured sill edges', 'BEVEL')
edge.width = .007
edge.segments = 3
bpy.ops.object.modifier_apply(modifier=edge.name)
for poly in temporary.data.polygons:
    poly.use_smooth = poly.area < .045 ** 2
normal = temporary.modifiers.new('Weighted sill normals', 'WEIGHTED_NORMAL')
normal.keep_sharp = True
bpy.ops.object.modifier_apply(modifier=normal.name)
replacement = temporary.data
replacement.materials.append(cap.data.materials[0])
old_mesh = cap.data
cap.data = replacement
cap.matrix_world = temporary.matrix_world.copy()
bpy.data.objects.remove(temporary, do_unlink=True)
if old_mesh.users == 0:
    bpy.data.meshes.remove(old_mesh)
replacement.name = 'C43_Radiator_FullDepth_CapMesh'
uv_project(cap)
cap['construction'] = 'Continuous solid sill to internal partition; user-corrected rear slot removed'
rear = bpy.data.objects['C43_Radiator_Cap_RearSupport']
rear_mesh = rear.data
bpy.data.objects.remove(rear, do_unlink=True)
if rear_mesh.users == 0:
    bpy.data.meshes.remove(rear_mesh)

# The existing grille contains disconnected manufactured pieces. Extract its
# left shallow return, deepen that piece while preserving its edge radii, and
# keep all slats/crossmembers in their original coordinates and topology.
grille = bpy.data.objects['C43_Radiator_White_Vertical_Grille']
bm = bmesh.new()
bm.from_mesh(grille.data)
remaining = set(bm.verts)
islands = []
while remaining:
    pending = [remaining.pop()]
    island = set(pending)
    while pending:
        v = pending.pop()
        for e in v.link_edges:
            nxt = e.other_vert(v)
            if nxt in remaining:
                remaining.remove(nxt)
                island.add(nxt)
                pending.append(nxt)
    islands.append(island)
left_islands = []
for island in islands:
    q = [grille.matrix_world @ v.co for v in island]
    bb = [[min(v[i] for v in q) for i in range(3)], [max(v[i] for v in q) for i in range(3)]]
    if abs(bb[0][0] - .29) < 1e-5 and abs(bb[1][0] - .312) < 1e-5 and bb[1][2] > .959:
        left_islands.append(island)
assert len(left_islands) == 1, 'Expected the original narrow left radiator return'
island = left_islands[0]
index = {v: i for i, v in enumerate(island)}
positions = []
for v in island:
    p = grille.matrix_world @ v.co
    x, y, z = p.x, p.z, -p.y
    # Back and lower/upper bevel strips translate rigidly, preserving radii.
    if z < .20:
        z -= .266
    if y < .49:
        y -= .02
    else:
        y += .0075
    positions.append((x, -z, y))
faces = [tuple(index[v] for v in f.verts) for f in bm.faces if all(v in island for v in f.verts)]
mesh = bpy.data.meshes.new('C43_Radiator_Left_End_PanelMesh')
mesh.from_pydata(positions, [], faces)
mesh.materials.append(grille.data.materials[0])
mesh.update()
panel = bpy.data.objects.new('C43_Radiator_Left_End_Panel', mesh)
coll.objects.link(panel)
panel['web_tags'] = '{}'
panel['construction'] = 'Solid floor-to-sill left end closing full depth; photo-estimated board thickness'
for poly in mesh.polygons:
    poly.use_smooth = poly.area < .022 ** 2
uv_project(panel)
bmesh.ops.delete(bm, geom=list(island), context='VERTS')
bm.to_mesh(grille.data)
bm.free()
grille.data.update()
bpy.context.view_layer.update()

assert before == {o.name: digest(o) for o in coll.all_objects if o.name in before}
cap_bounds, panel_bounds = bounds(cap), bounds(panel)
assert all(abs(a - b) < 1e-6 for a, b in zip(cap_bounds[0], [.255, .9675, -.12]))
assert all(abs(a - b) < 1e-6 for a, b in zip(cap_bounds[1], [1.425, 1.0125, .28]))
assert abs(panel_bounds[0][1]) < 1e-6
assert abs(panel_bounds[1][1] - cap_bounds[0][1]) < 1e-6
topology = []
for o in (cap, panel, grille):
    test = bmesh.new()
    test.from_mesh(o.data)
    errors = {'object': o.name, 'nonManifoldEdges': sum(not e.is_manifold for e in test.edges),
              'zeroAreaFaces': sum(f.calc_area() < 1e-14 for f in test.faces),
              'signedVolume': test.calc_volume(signed=True)}
    assert errors['nonManifoldEdges'] == errors['zeroAreaFaces'] == 0, errors
    assert errors['signedVolume'] > 0, errors
    assert all(math.isfinite(c) for v in test.verts for c in v.co)
    test.free()
    topology.append(errors)
scene['component_parent_revision'] = 'architecture01'
scene['component_revision'] = 'architecture02-radiator'
scene['radiator_depth_correction'] = json.dumps({'reference': 'User orange annotation and P01/P03/P04',
    'capWebBounds': cap_bounds, 'leftEndWebBounds': panel_bounds,
    'dimensionsSource': 'Retained approved bounds; depth/board details estimated from photos',
    'curtainIntegrationPending': 'Right hem above cap; left hem outside left end; no rear slot'})
report = {'parentRevision': 'architecture01', 'revision': scene['component_revision'],
          'sourceParentSha256': PARENT_HASH, 'oldCapWebBounds': old_cap_bounds,
          'capWebBounds': cap_bounds, 'leftEndWebBounds': panel_bounds,
          'nonTargetObjectDigestsUnchanged': len(before), 'topology': topology,
          'removed': ['C43_Radiator_Cap_RearSupport'],
          'curtainIntegrationPending': True,
          'knownOldCurtainConflictWebBounds': [[.255, .9675, .03], [1.425, 1.0125, .104]]}
(REPORT / 'radiator-depth-check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
result = report
