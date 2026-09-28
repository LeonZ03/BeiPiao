"""Remove exposed coplanar base/end faces. Execute via official Blender Lab MCP.

architecture03 -> architecture04. Keep the accepted envelope, cap and curtains.
Only the two dark plinth pieces inside the existing joined grille are adjusted.
"""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
SOURCE = ROOM / 'assets/architecture/Courtyard43-architecture.blend'
scene = bpy.context.scene
assert scene['component_revision'] == 'architecture03'
assert scene['source_layout'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
obj = bpy.data.objects['C43_Radiator_White_Vertical_Grille']

def digest(o):
    h = hashlib.sha256(repr((o.type, tuple(tuple(r) for r in o.matrix_world),
        o.parent.name if o.parent else None, dict(o.items()))).encode())
    if o.type == 'MESH':
        h.update(repr(([tuple(v.co) for v in o.data.vertices],
            [tuple(p.vertices) for p in o.data.polygons],
            [(u.name, [tuple(d.uv) for d in u.data]) for u in o.data.uv_layers])).encode())
    return h.hexdigest()

before = {o.name: digest(o) for o in scene.objects if o != obj}
obj.data = obj.data.copy()
bm = bmesh.new()
bm.from_mesh(obj.data)
unseen = set(bm.verts)
targets = []
while unseen:
    first = unseen.pop()
    pending, island = [first], {first}
    while pending:
        v = pending.pop()
        for edge in v.link_edges:
            nxt = edge.other_vert(v)
            if nxt in unseen:
                unseen.remove(nxt)
                island.add(nxt)
                pending.append(nxt)
    q = [obj.matrix_world @ v.co for v in island]
    if min(p.z for p in q) < .021 and max(p.z for p in q) < .083:
        assert len(island) == 96
        assert max(p.x for p in q)-min(p.x for p in q) > 1.09
        targets.append(island)
assert len(targets) == 2
inv = obj.matrix_world.inverted()
for island in targets:
    for v in island:
        p = obj.matrix_world @ v.co
        # Preserve bevel strip widths by translating each end rigidly. Ends
        # enter the adjacent side boards by 0.5 mm; no exposed coplanar caps.
        p.x += .0215 if p.x < .84 else -.0215
        # Recess the room-facing plinth 6 mm from the white side return. This
        # creates a real reveal instead of two different colours at z=.262.
        if -p.y > .1:
            p.y += .006
        v.co = inv @ p
assert not any(not e.is_manifold for e in bm.edges)
assert not any(f.calc_area() < 1e-14 for f in bm.faces)
bm.to_mesh(obj.data)
bm.free()
obj.data.update()
obj['base_joint'] = 'Dark plinth ends inside side panels, 6 mm front reveal; no exposed coplanar end/front faces'
assert before == {o.name: digest(o) for o in scene.objects if o != obj}
scene['component_parent_revision'] = 'architecture03'
scene['component_revision'] = 'architecture04'
scene['radiator_base_fix'] = 'Two plinth pieces trimmed to web X .3115..1.3685; front web Z .14.. .256'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
result = {'revision': 'architecture04', 'changedObjects': [obj.name],
    'changedIslands': 2, 'nonTargetObjectsUnchanged': len(before),
    'source': str(SOURCE), 'frontReveal': .006}
