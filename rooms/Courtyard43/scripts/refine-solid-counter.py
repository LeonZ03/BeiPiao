"""User-corrected solid counter, via official Blender Lab MCP only.

Run on architecture04 first, then interior03. The balcony-facing side is a
closed ivory solid, not an open radiator enclosure or a dark interior proxy.
"""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
scene = bpy.context.scene
is_component = scene.get('component') == 'architecture'
assert (scene.get('component_revision') == 'architecture04' if is_component
        else scene.get('web_revision') == 'courtyard43-interior03')
assert scene['source_layout'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
targets = {'C43_Radiator_Left_End_Panel', 'C43_Radiator_Inner_Shadow',
           'C43_Radiator_White_Vertical_Grille'}

def digest(obj):
    h = hashlib.sha256(repr((obj.name, tuple(tuple(r) for r in obj.matrix_world),
        obj.parent.name if obj.parent else None, dict(obj.items()))).encode())
    if obj.type == 'MESH':
        h.update(repr(([tuple(v.co) for v in obj.data.vertices],
            [tuple(p.vertices) for p in obj.data.polygons],
            [p.material_index for p in obj.data.polygons],
            [(u.name, [tuple(d.uv) for d in u.data]) for u in obj.data.uv_layers])).encode())
    return h.hexdigest()

before = {o.name: digest(o) for o in scene.objects if o.name not in targets}
body = bpy.data.objects['C43_Radiator_Left_End_Panel']
paint = body.data.materials[0]
bpy.ops.mesh.primitive_cube_add(size=1, location=(.84, -.063, .48375))
temporary = bpy.context.object
temporary.dimensions = (1.1, .366, .9675)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
bevel = temporary.modifiers.new('Soft solid counter edges', 'BEVEL')
bevel.width = .002
bevel.segments = 3
bpy.ops.object.modifier_apply(modifier=bevel.name)
for p in temporary.data.polygons:
    p.use_smooth = p.area < .002
normal = temporary.modifiers.new('Weighted solid face normals', 'WEIGHTED_NORMAL')
normal.keep_sharp = True
bpy.ops.object.modifier_apply(modifier=normal.name)
mesh = temporary.data
mesh.transform(body.matrix_world.inverted() @ temporary.matrix_world)
mesh.materials.append(paint)
uv = mesh.uv_layers.new(name='UVMap')
for p in mesh.polygons:
    axis = max(range(3), key=lambda a: abs(p.normal[a]))
    axes = [a for a in range(3) if a != axis]
    for li in p.loop_indices:
        v = mesh.vertices[mesh.loops[li].vertex_index].co
        uv.data[li].uv = (v[axes[0]], v[axes[1]])
body.data = mesh
body.name = 'C43_Radiator_Solid_Body'
body['construction'] = 'User-confirmed solid rectangular counter, floor to sill; closed balcony face, estimated inherited envelope'
bpy.data.objects.remove(temporary, do_unlink=True)
bpy.data.objects.remove(bpy.data.objects['C43_Radiator_Inner_Shadow'], do_unlink=True)

# Remove obsolete right return and rear plinth now replaced by the solid body.
# Keep the visible room-facing trim, slats and coloured crossbars intact.
grille = bpy.data.objects['C43_Radiator_White_Vertical_Grille']
grille.data = grille.data.copy()
bm = bmesh.new()
bm.from_mesh(grille.data)
unseen = set(bm.verts)
removed = 0
trimmed = 0
inv = grille.matrix_world.inverted()
while unseen:
    first = unseen.pop()
    island, pending = {first}, [first]
    while pending:
        v = pending.pop()
        for edge in v.link_edges:
            nxt = edge.other_vert(v)
            if nxt in unseen:
                unseen.remove(nxt)
                island.add(nxt)
                pending.append(nxt)
    q = [grille.matrix_world @ v.co for v in island]
    lo = [min(p[i] for p in q) for i in range(3)]
    hi = [max(p[i] for p in q) for i in range(3)]
    right_return = lo[0] > 1.36 and hi[2] > .95
    rear_plinth = hi[2] < .083 and lo[1] > .05
    if right_return or rear_plinth:
        bmesh.ops.delete(bm, geom=list(island), context='VERTS')
        removed += 1
    elif hi[0]-lo[0] > 1.09 and lo[2] > .08:
        # The two ivory face rails enter the body; recess their end caps 2 mm
        # so the side surface cannot share the solid body's outside plane.
        for v in island:
            p = grille.matrix_world @ v.co
            p.x += .002 if p.x < .84 else -.002
            v.co = inv @ p
        trimmed += 1
assert removed == trimmed == 2
bm.to_mesh(grille.data)
bm.free()
grille['construction'] = 'Room-facing applied grille on solid counter; no open back or separate coplanar returns'
bpy.context.view_layer.update()
checks = []
for obj in [body, grille]:
    test = bmesh.new()
    test.from_mesh(obj.data)
    assert not any(not e.is_manifold for e in test.edges)
    assert not any(f.calc_area() < 1e-14 for f in test.faces)
    checks.append({'object': obj.name, 'volume': test.calc_volume(signed=True)})
    test.free()
assert checks[0]['volume'] > .38
assert before == {o.name: digest(o) for o in scene.objects if o.name in before}
if is_component:
    scene['component_parent_revision'] = 'architecture04'
    scene['component_revision'] = 'architecture05'
    output = ROOM / 'assets/architecture/Courtyard43-architecture.blend'
else:
    scene['parent_web_revision'] = 'courtyard43-interior03'
    scene['web_revision'] = 'courtyard43-interior04'
    records = json.loads(scene['components'])
    for record in records:
        if record['component'] == 'architecture':
            record['sha256'] = hashlib.sha256((ROOT / record['source']).read_bytes()).hexdigest()
    scene['components'] = json.dumps(records)
    output = ROOM / 'assets/full-room/Courtyard43-interior.blend'
scene['solid_counter_confirmed'] = 'User balcony-side annotation: entire body is a solid rectangular block, not hollow'
bpy.ops.wm.save_as_mainfile(filepath=str(output))
result = {'saved': str(output), 'unchangedObjects': len(before), 'checks': checks}
if not is_component:
    script = ROOM / 'scripts/export-interior.py'
    scope = {'__file__': str(script), '__name__': 'courtyard43_export'}
    exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), scope)
    result['export'] = scope['export_interior']()
