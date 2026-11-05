"""balcony41 -> join42. Seal the counter's right junction through official MCP."""
from pathlib import Path
import ast
import hashlib
import json

import bpy
from mathutils.bvhtree import BVHTree


ROOM = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
assert scene.get('web_revision') == 'courtyard43-balcony41'
bpy.context.preferences.filepaths.save_version = 0
wall = bpy.data.objects['C43_Wall_Balcony_Pier_Right']
tree = ast.parse((ROOM / 'scripts/refine-furnishings.py').read_text('utf8'))
definition = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'digest')
exec(compile(ast.Module(body=[definition], type_ignores=[]), 'digest', 'exec'))
before = {o.name: digest(o) for o in scene.objects if o != wall}


def surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    points = [obj.matrix_world @ v.co for v in mesh.vertices]
    result = BVHTree.FromPolygons(points, [tuple(p.vertices) for p in mesh.loop_triangles],
                                 all_triangles=True)
    evaluated.to_mesh_clear()
    return result


old_wall_surface = surface(wall)
# The return meets the counter behind the travelling curtain. Its broad face
# and outside edge stay on their old planes.
# Ten millimetres of hidden overlap closes even an oblique line of sight.
inverse = wall.matrix_world.inverted()
for vertex in wall.data.vertices:
    point = wall.matrix_world @ vertex.co
    if point.x < 1.455:
        point.x -= .07
        vertex.co = inverse @ point
wall.data.update()

bpy.context.view_layer.update()

# Compare actual cloth triangles with the old wall. The fixed outer hem
# already tucks 0.5 mm into its broad face and is outside the edited junction.
wall_surface = surface(wall)
curtain = bpy.data.objects['C43_Curtain_Right']
opening = curtain.data.shape_keys.key_blocks['Open']
initial = opening.value
for step in range(21):
    opening.value = step / 20
    bpy.context.view_layer.update()
    cloth = surface(curtain)
    old_contacts = {a for a, _ in cloth.overlap(old_wall_surface)}
    new_contacts = {a for a, _ in cloth.overlap(wall_surface)}
    assert new_contacts <= old_contacts, 'Return adds a curtain intersection'
opening.value = initial
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[name]) == value for name, value in before.items())
scene['parent_web_revision'] = 'courtyard43-balcony41'
scene['web_revision'] = 'courtyard43-join42'
scene['join42'] = json.dumps(dict(unchangedObjects=len(before), curtainStates=21,
                                 targets=[wall.name], hiddenOverlap=.01))
exporter = ROOM / 'scripts/export-interior.py'
ns = {'__file__': str(exporter)}
exec(compile(exporter.read_text('utf8'), str(exporter), 'exec'), ns)
report = ns['export_interior']()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM / 'assets/full-room/Courtyard43-interior.blend'))
result = {**report, 'unchangedObjects': len(before), 'curtainStates': 21}
