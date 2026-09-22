"""Append audited components, save full editable source, export via official MCP.

Never rebuild the accepted whitebox or another room. The three component sources
are independent rebuild points; this stage only assembles their collections.
"""
import hashlib
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
P = json.loads((ROOM / 'history/inputs/approved-layout.json').read_text(encoding='utf-8'))
assert P['structureApproved'] and P['parentRevision'] == 'courtyard43-whitebox06'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene['room_id'] = 'Courtyard43'
scene['stage'] = 'interior'
scene['web_revision'] = 'courtyard43-interior01'
scene['structure_approved'] = True
scene['source_layout'] = P['parentRevision']
scene['review_parameters'] = json.dumps(P, ensure_ascii=False)
components = []
for component in ['architecture', 'furniture', 'props']:
    source = ROOM / f'assets/{component}/Courtyard43-{component}.blend'
    assert source.is_file(), f'Component not ready: {source}'
    before = set(bpy.data.images)
    with bpy.data.libraries.load(str(source), link=False) as (src, dst):
        collection = 'C43_' + component.title()
        assert collection in src.collections
        dst.collections = [collection]
    scene.collection.children.link(dst.collections[0])
    for image in set(bpy.data.images) - before:
        if image.source == 'FILE' and image.filepath:
            # Append normally resolves // against the library. Handle versions
            # retaining // explicitly, before saving the main source elsewhere.
            path = Path(bpy.path.abspath(image.filepath, library=image.library)).resolve()
            if not path.is_file() and image.filepath.startswith('//'):
                path = (source.parent / image.filepath[2:]).resolve()
            assert path.is_file(), f'Missing component texture {image.name}: {path}'
            image.filepath = str(path)
    components.append(dict(component=component, source=str(source.relative_to(ROOT)).replace('\\','/'),
                           sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
scene['components'] = json.dumps(components)
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
assert not any(block.library for group in [bpy.data.objects,bpy.data.meshes,bpy.data.materials,bpy.data.images,bpy.data.node_groups] for block in group), 'Unexpected mutable cross-room link'
bpy.context.view_layer.update()
for obj in scene.objects:
    if obj.type == 'MESH' and not obj.data.uv_layers:
        # Some accepted plain-metal fasteners did not need UVs in the old pack.
        # Create a stable object-space projection here; preserve existing UVs.
        uv = obj.data.uv_layers.new(name='UVMap')
        for face in obj.data.polygons:
            axis = max(range(3), key=lambda a:abs(face.normal[a]))
            axes = [a for a in range(3) if a != axis]
            for li, vi in zip(face.loop_indices,face.vertices):
                vertex = obj.data.vertices[vi].co
                uv.data[li].uv = (vertex[axes[0]],vertex[axes[1]])
scene.world = bpy.data.worlds.new('C43_Neutral_authoring_world')
scene.world.color = (.18,.18,.18)
blend = ROOM / 'assets/full-room/Courtyard43-interior.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for image in bpy.data.images:
    if image.source == 'FILE' and image.filepath:
        image.filepath = bpy.path.relpath(bpy.path.abspath(image.filepath))
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
script = ROOM / 'scripts/export-interior.py'
scope = {'__file__':str(script),'__name__':'courtyard43_export'}
exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),scope)
result = scope['export_interior']()
result['components'] = components
