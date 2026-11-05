"""join42 -> join43: continue the existing skirting and conceal the threshold end.

Execute inside the official Blender Lab MCP on the current complete source.
"""
from pathlib import Path
import ast
import hashlib
import json

import bpy

ROOM = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
assert scene.get('web_revision') == 'courtyard43-join42'
bpy.context.preferences.filepaths.save_version = 0
skirt = bpy.data.objects['C43_Skirting_Dark_Timber']
threshold = bpy.data.objects['C43_Threshold_Dark_Stone']
targets = {skirt.name, threshold.name}
tree = ast.parse((ROOM / 'scripts/refine-furnishings.py').read_text('utf8'))
definition = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'digest')
exec(compile(ast.Module(body=[definition], type_ignores=[]), 'digest', 'exec'))
before = {o.name: digest(o) for o in scene.objects if o.name not in targets}

# Move only the existing rounded end bands, retaining their closed topology,
# material, front plane and 90 mm height. The joint tucks behind the counter.
for obj in (skirt, threshold):
    assert obj.data.users == 1
    inverse = obj.matrix_world.inverted()
    moved = 0
    for vertex in obj.data.vertices:
        point = obj.matrix_world @ vertex.co
        if abs(point.x - 1.45) < .004 and (obj == threshold or point.y > -.019):
            point.x -= .07
            vertex.co = inverse @ point
            moved += 1
    assert moved > 0, obj.name
    obj.data.update()
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[name]) == value for name, value in before.items())
scene['parent_web_revision'] = 'courtyard43-join42'
scene['web_revision'] = 'courtyard43-join43'
scene['join43'] = json.dumps(dict(targets=sorted(targets), unchangedObjects=len(before),
                                 description='Continuous skirting; threshold end hidden by counter'))
exporter = ROOM / 'scripts/export-interior.py'
ns = {'__file__': str(exporter)}
exec(compile(exporter.read_text('utf8'), str(exporter), 'exec'), ns)
report = ns['export_interior']()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM / 'assets/full-room/Courtyard43-interior.blend'))
result = {**report, 'unchangedObjects': len(before), 'targets': sorted(targets)}
