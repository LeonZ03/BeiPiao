"""Integrate two audited mesh edits into interior02 through official MCP only.

Preserves full-scene AO materials, every other object, hierarchy and interaction.
This does not rebuild the room or rerun the initial component generators.
"""
from pathlib import Path
import bpy
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
scene = bpy.context.scene
assert scene['web_revision'] == 'courtyard43-interior02'
assert scene['source_layout'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
changes = {'architecture': 'C43_Radiator_White_Vertical_Grille',
           'furniture': 'C43_DeskTop'}
source_hashes = {
    'architecture': '5e5d76995dbcc87afc6e06dd1974568cda8924fdc9f1334b3fc9c36f2a3e08e7',
    'furniture': '881fa33fcd635a2a670fb5c313ab71d5c435a3427374e6d615dbd53488ae4740',
}

def digest(o):
    h = hashlib.sha256(repr((o.type, o.parent.name if o.parent else None,
        tuple(tuple(row) for row in o.matrix_world), dict(o.items()))).encode())
    if o.type == 'MESH':
        h.update(repr(([tuple(v.co) for v in o.data.vertices],
            [tuple(p.vertices) for p in o.data.polygons],
            [(u.name, [tuple(d.uv) for d in u.data]) for u in o.data.uv_layers],
            [m.name for m in o.data.materials])).encode())
    return h.hexdigest()

before = {o.name: digest(o) for o in scene.objects if o.name not in changes.values()}
records = json.loads(scene['components'])
for component, name in changes.items():
    source = ROOM / f'assets/{component}/Courtyard43-{component}.blend'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hashes[component], 'Unreviewed component revision'
    target = bpy.data.objects[name]
    old_materials = list(target.data.materials)
    old_transform = target.matrix_world.copy()
    with bpy.data.libraries.load(str(source), link=False) as (src, dst):
        assert name in src.objects
        dst.objects = [name]
    imported = dst.objects[0]
    # An unlinked library object has not been evaluated by the depsgraph yet;
    # its matrix_world is identity. Compare its authored parent chain instead.
    def authored_world(obj):
        return (authored_world(obj.parent) @ obj.matrix_parent_inverse @ obj.matrix_basis
                if obj.parent else obj.matrix_basis)
    imported_world = authored_world(imported)
    assert all(abs(imported_world[i][j]-old_transform[i][j]) < 1e-6
               for i in range(4) for j in range(4)), 'Approved transform changed'
    mesh = imported.data.copy()
    assert len(mesh.materials) == len(old_materials)
    material_indices = [p.material_index for p in mesh.polygons]
    mesh.materials.clear()
    for material in old_materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
    target.data = mesh
    for modifier in list(target.modifiers):
        target.modifiers.remove(modifier)
    for modifier in imported.modifiers:
        copy = target.modifiers.new(modifier.name, modifier.type)
        for prop in modifier.bl_rna.properties:
            if prop.is_readonly or prop.identifier in {'rna_type', 'name', 'type'}:
                continue
            try:
                setattr(copy, prop.identifier, getattr(modifier, prop.identifier))
            except (TypeError, AttributeError):
                pass
    for key in ['construction', 'base_joint']:
        if key in imported:
            target[key] = imported[key]
    bpy.data.objects.remove(imported, do_unlink=True)
    for record in records:
        if record['component'] == component:
            record['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
assert before == {o.name: digest(o) for o in scene.objects if o.name in before}
scene['components'] = json.dumps(records)
scene['parent_web_revision'] = 'courtyard43-interior02'
scene['web_revision'] = 'courtyard43-interior03'
bpy.context.view_layer.update()
blend = ROOM / 'assets/full-room/Courtyard43-interior.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
script = ROOM / 'scripts/export-interior.py'
scope = {'__file__': str(script), '__name__': 'courtyard43_export'}
exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), scope)
result = scope['export_interior']()
result['unchangedObjects'] = len(before)
result['changedObjects'] = list(changes.values())
