"""Read-only component checks/rendering via official Blender Lab MCP.

No model source is saved. Reports and optional neutral inspection renders go to
analysis/Courtyard43/furniture. Set C43_RENDER=1 in the MCP Python environment
for images. Exported webpage appearance remains the final acceptance target.
"""
from pathlib import Path
import hashlib
import json
import math
import os

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / 'analysis/Courtyard43/furniture'
REPORT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
assert scene['component'] == 'furniture'
col = bpy.data.collections['C43_Furniture']
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def geometry(obj):
    evaluated = obj.evaluated_get(dg)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    verts = [obj.matrix_world @ v.co for v in mesh.vertices]
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return verts, triangles


def bounds(obj):
    verts, _ = geometry(obj)
    # Convert to web coordinate convention for reports.
    coords = [(v.x, v.z, -v.y) for v in verts]
    return [[min(p[a] for p in coords) for a in range(3)], [max(p[a] for p in coords) for a in range(3)]]


def tree(obj):
    verts, triangles = geometry(obj)
    return BVHTree.FromPolygons(verts, triangles, all_triangles=True, epsilon=0)


def box_tree(lo, hi):
    vertices = [(x, -z, y) for x in [lo[0], hi[0]] for y in [lo[1], hi[1]] for z in [lo[2], hi[2]]]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return BVHTree.FromPolygons(vertices, faces)


report = {'component': scene['component_revision'], 'objects': len(col.objects), 'meshes': 0, 'triangles': 0, 'vertices': 0, 'finiteErrors': [], 'topologyErrors': [], 'missingImages': [], 'bounds': {}, 'doorSamples': []}
for obj in col.objects:
    if obj.type != 'MESH':
        continue
    report['meshes'] += 1
    verts, triangles = geometry(obj)
    report['vertices'] += len(verts)
    report['triangles'] += len(triangles)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bad = sum(not e.is_manifold for e in bm.edges)
    volume = bm.calc_volume(signed=True)
    zero = sum(f.calc_area() < 1e-12 for f in bm.faces)
    if bad or volume < 0 or zero:
        report['topologyErrors'].append({'name': obj.name, 'nonmanifold': bad, 'signedVolume': volume, 'degenerateFaces': zero})
    bm.free()
    if any(not math.isfinite(c) for v in verts for c in v):
        report['finiteErrors'].append(obj.name)
    if not obj.data.uv_layers:
        report['finiteErrors'].append(obj.name + ': missing UV')
    if any(not math.isfinite(c) for item in obj.data.uv_layers.active.data for c in item.uv):
        report['finiteErrors'].append(obj.name + ': nonfinite UV')
    if obj.name in ['C43_BedPlatform', 'C43_BedHeadboard', 'C43_Mattress', 'C43_FloralDuvet', 'C43_DrapedWhiteSheet', 'C43_CottonPillow', 'C43_DeskTop', 'C43_ChairWhiteCurvedBack', 'C43_WardrobeNearSide', 'C43_WardrobeFarSide']:
        report['bounds'][obj.name] = bounds(obj)
for image in bpy.data.images:
    if image.source == 'FILE' and not Path(bpy.path.abspath(image.filepath)).is_file():
        report['missingImages'].append(image.filepath)

report['surfaceIntersections'] = {}
for a, b in [('C43_FloralDuvet', 'C43_Mattress'), ('C43_DrapedWhiteSheet', 'C43_Mattress'), ('C43_CottonPillow', 'C43_Mattress'), ('C43_FloralDuvet', 'C43_CottonPillow'), ('C43_FloralDuvet', 'C43_DrapedWhiteSheet')]:
    report['surfaceIntersections'][a + '/' + b] = len(tree(bpy.data.objects[a]).overlap(tree(bpy.data.objects[b])))

# Door sweep checks include both doors together and the locked radiator cap,
# front cover, bed volume and curtain envelope. Hinge attachment overlap with
# its own mounting hardware is intentional and excluded.
obstacles = {'radiatorCap': box_tree((.255, .9675, -.12), (1.425, 1.0125, .28)),
             'radiatorCap20mmMargin': box_tree((.235, .9475, -.14), (1.445, 1.0325, .30)),
             'radiatorCover': box_tree((.29, .02, .146), (1.39, .96, .2835)),
             'curtainEnvelope': box_tree((-.63, .034, .03), (1.43, 2.40, .104))}
carcass = [o for o in col.objects if o.type == 'MESH' and o.name.startswith('C43_Wardrobe') and any(s in o.name for s in ['Side', 'Back', 'Base', 'Top', 'Shelf', 'ToeKick'])]
for obj in carcass:
    obstacles[obj.name] = tree(obj)
pivots = [bpy.data.objects['C43_WardrobeDoorFarPivot'], bpy.data.objects['C43_WardrobeDoorNearPivot']]
for step in range(25):
    amount = step / 24
    for pivot in pivots:
        pivot.rotation_euler.z = json.loads(pivot['c43_interaction'])['openAngle'] * amount
    bpy.context.view_layer.update()
    dg.update()
    doors = [bpy.data.objects['C43_WardrobeDoorFar'], bpy.data.objects['C43_WardrobeDoorNear']]
    data = {'amount': round(amount, 5), 'intersections': {}, 'capMinimumSampledDistance': None}
    distances = []
    for door in doors:
        door_tree = tree(door)
        for name, obstacle in obstacles.items():
            hits = len(door_tree.overlap(obstacle))
            if hits:
                data['intersections'][door.name + '/' + name] = hits
        # Include points across the vertical face at cap height; endpoint-only
        # vertex distances would miss a cap passing midway up the tall panel.
        verts, _ = geometry(door)
        local_bounds = [[min(v.co[a] for v in door.data.vertices) for a in range(3)], [max(v.co[a] for v in door.data.vertices) for a in range(3)]]
        for side in [0, 1]:
            for j in range(151):
                verts.append(door.matrix_world @ Vector((local_bounds[side][0], local_bounds[0][1] + (local_bounds[1][1] - local_bounds[0][1]) * j / 150, 0)))
        for v in verts:
            v.z = 1.0
            hit = obstacles['radiatorCap'].find_nearest(v)
            if hit:
                distances.append(hit[3])
    hits = len(tree(doors[0]).overlap(tree(doors[1])))
    if hits:
        data['intersections']['door/door'] = hits
    data['capMinimumSampledDistance'] = min(distances)
    report['doorSamples'].append(data)
for pivot in pivots:
    pivot.rotation_euler.z = 0
bpy.context.view_layer.update()
report['feet'] = {obj.name: bounds(obj)[0][1] for obj in col.objects if 'Foot' in obj.name and obj.type == 'MESH'}
report['sourceUnchanged'] = hashlib.sha256((ROOT / 'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend').read_bytes()).hexdigest() == scene['source_sha256']
report['linkedLibraries'] = len(bpy.data.libraries)
assert not report['finiteErrors'] and not report['missingImages']
assert not report['topologyErrors'], report['topologyErrors']
assert report['sourceUnchanged'] and not report['linkedLibraries']
assert not any(report['surfaceIntersections'].values())
assert not any(sample['intersections'] for sample in report['doorSamples'])
(REPORT / 'geometry-check.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')

if os.environ.get('C43_RENDER') == '1':
    # Temporary neutral studio, omitted from the saved component.
    bpy.ops.mesh.primitive_plane_add(size=200)
    floor = bpy.context.object
    floor.name = 'CHECK_Floor'
    mat = bpy.data.materials.new('CHECK_FloorMat')
    mat.diffuse_color = (.22, .24, .24, 1)
    floor.data.materials.append(mat)
    world = bpy.data.worlds.new('CHECK_World')
    world.use_nodes = True
    background = next((n for n in world.node_tree.nodes if n.type == 'BACKGROUND'), None)
    if background is None:
        background = world.node_tree.nodes.new('ShaderNodeBackground')
        output = world.node_tree.nodes.new('ShaderNodeOutputWorld')
        world.node_tree.links.new(background.outputs[0], output.inputs['Surface'])
    background.inputs['Color'].default_value = (.42, .46, .51, 1)
    background.inputs['Strength'].default_value = .55
    scene.world = world
    for pos, power, size in [((-1, 5, .5), 850, 5), ((2, 3, 3), 450, 4)]:
        data = bpy.data.lights.new('CHECK_Area', 'AREA')
        data.energy = power
        data.shape = 'DISK'
        data.size = size
        obj = bpy.data.objects.new('CHECK_Area', data)
        scene.collection.objects.link(obj)
        obj.location = (pos[0], -pos[2], pos[1])
        obj.rotation_euler = (Vector((0, -1.4, .6)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('CHECK_Camera')
    camera = bpy.data.objects.new('CHECK_Camera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    views = [('overview', (-4.4, 3.9, 5.9), (.10, .85, 1.32), 43),
             ('bed', (.4, 1.55, .65), (-.87, .53, 2.04), 45),
             ('desk', (-.15, 1.15, 1.64), (-1.29, .46, .54), 52),
             ('wardrobe', (-.05, 1.5, 2.0), (1.88, 1.02, .8), 48)]
    for name, pos, target, focal in views:
        if os.environ.get('C43_VIEW', 'overview') != name:
            continue
        camera.location = (pos[0], -pos[2], pos[1])
        target_bl = Vector((target[0], -target[2], target[1]))
        camera.rotation_euler = (target_bl - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.lens = focal
        if name == 'wardrobe':
            for pivot in pivots:
                pivot.rotation_euler.z = json.loads(pivot['c43_interaction'])['openAngle']
            bpy.context.view_layer.update()
        scene.render.filepath = str(REPORT / (name + '.png'))
        bpy.ops.render.render(write_still=True)

result = {key: report[key] for key in ['component', 'objects', 'meshes', 'triangles', 'vertices', 'finiteErrors', 'topologyErrors', 'missingImages', 'surfaceIntersections', 'sourceUnchanged', 'linkedLibraries']}
result['doorIntersectionSamples'] = [sample for sample in report['doorSamples'] if sample['intersections']]
result['minCapSampledDistance'] = min(sample['capMinimumSampledDistance'] for sample in report['doorSamples'])
result['report'] = str(REPORT / 'geometry-check.json')
