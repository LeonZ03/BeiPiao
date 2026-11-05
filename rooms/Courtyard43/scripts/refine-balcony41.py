"""cap40 -> balcony41. Close the right balcony end and clear the old right curtain.

Run through the official Blender Lab MCP on the complete cap40 source.
"""
from pathlib import Path
import ast
import hashlib
import json

import bmesh
import bpy
from mathutils import Vector


ROOM = Path(__file__).resolve().parents[1]
scene = bpy.context.scene
parent = 'courtyard43-cap40'
revision = 'courtyard43-balcony41'
assert scene.get('web_revision') == parent
bpy.context.preferences.filepaths.save_version = 0

objects = bpy.data.objects
left_wall = objects['C43_Wall_Balcony_Left']
old_wall = objects['C43_Wall_Balcony_Brick_Return']
frames = objects['C43_Window_White_Frames']
curtain = objects['C43_B35_OldCurtainRight']
removed_names = [old_wall.name, 'C43_Window_Return_Stone_Sill',
                 'C43_Window_Return_Glass_0', 'C43_Window_Return_Glass_1']
changed_names = {*removed_names, frames.name, curtain.name}
tree = ast.parse((ROOM / 'scripts/refine-furnishings.py').read_text('utf8'))
digest_definition = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'digest')
exec(compile(ast.Module(body=[digest_definition], type_ignores=[]), 'digest', 'exec'))
before = {o.name: digest(o) for o in scene.objects if o.name not in changed_names}

# Match the existing left end wall, including plaster and bevel, at the
# established right-end footprint. The old side glazing was an estimate.
right_wall = left_wall.copy()
right_wall.data = left_wall.data.copy()
right_wall.name = 'C43_Wall_Balcony_Right'
left_wall.users_collection[0].objects.link(right_wall)
right_wall.matrix_world = left_wall.matrix_world.copy()
right_wall.location.x = old_wall.location.x
right_wall['web_tags'] = old_wall['web_tags']
right_wall['evidence'] = 'User confirmed solid end wall; section and finish follow left balcony wall'

# The front and return PVC frame sections were joined without welding.
# Remove only the five right return sections; keep the front corner mullion.
mesh = bmesh.new()
mesh.from_mesh(frames.data)
unvisited = set(mesh.verts)
return_vertices = []
return_sections = 0
while unvisited:
    stack = [unvisited.pop()]
    section = []
    while stack:
        v = stack.pop()
        section.append(v)
        for e in v.link_edges:
            neighbor = e.other_vert(v)
            if neighbor in unvisited:
                unvisited.remove(neighbor)
                stack.append(neighbor)
    xs = [(frames.matrix_world @ v.co).x for v in section]
    if min(xs) > 2.18 and max(xs) > 2.25:
        return_vertices.extend(section)
        return_sections += 1
assert return_sections == 5
bmesh.ops.delete(mesh, geom=return_vertices, context='VERTS')
mesh.to_mesh(frames.data)
mesh.free()
for name in removed_names:
    objects.remove(objects[name], do_unlink=True)


def smoothstep(t):
    t = min(1, max(0, t))
    return t * t * (3 - 2 * t)


# Leave the wire and ties in place. Keep the cloth gathered at the ties,
# then drape it around the projecting sill. Both cloth surfaces and the
# bound hem travel together; the lower fold crests have room to sway.
inverse = curtain.matrix_world.inverted()
for v in curtain.data.vertices:
    p = curtain.matrix_world @ v.co
    height = p.z
    over_sill = smoothstep((1.24 - height) / .296)
    fold = .21 + .29 * smoothstep((2.365 - height) / .29) + .17 * over_sill
    depth = -1.034 + .078 * over_sill + fold * (-p.y + 1.045)
    v.co = inverse @ Vector((p.x, -depth, height))
curtain.data.update()

bpy.context.view_layer.update()
assert all(digest(objects[name]) == value for name, value in before.items())
scene['parent_web_revision'] = parent
scene['web_revision'] = revision
scene['balcony41'] = json.dumps(dict(unchangedObjects=len(before), removed=removed_names,
                                    removedReturnFrameSections=return_sections))
script = ROOM / 'scripts/export-interior.py'
ns = {'__file__': str(script)}
exec(compile(script.read_text('utf8'), str(script), 'exec'), ns)
report = ns['export_interior']()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM / 'assets/full-room/Courtyard43-interior.blend'))
result = {**report, 'unchangedObjects': len(before), 'removedReturnFrameSections': return_sections}
