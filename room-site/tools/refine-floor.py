"""Run through Blender Lab MCP execute_blender_code_for_cli, on the saved room.

Photo-matched rectified ceramic tiles: truly planar faces, tiny eased edges,
near-flush grout, and one continuous bedroom/corridor setting-out grid.
Only floor objects and their exported mesh records are changed.
"""
import os
import bpy
import bmesh
import copy
import gzip
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[2]))
OUT = ROOT / 'room-site/dist/assets/full-room'
MANIFEST = OUT / 'scene.json'
data = json.loads(MANIFEST.read_text(encoding='utf-8'))
assert data['revision'] == 'blender18', 'Apply to the backed-up blender18 scene only'
old_nodes = copy.deepcopy(data['nodes'])
objects = {o['web_node_id']: o for o in bpy.data.objects if 'web_node_id' in o}
materials = {m['web_material_id']: m for m in bpy.data.materials if 'web_material_id' in m}
assembly = objects[2].users_collection[0]
bed_ids = list(range(2, 38))
bath_ids = list(range(39, 69))
assert all(data['nodes'][i]['material'] == 1 for i in bed_ids)
assert all(data['nodes'][i]['material'] == 2 for i in bath_ids)
raw = bytearray((OUT / 'geometry.bin').read_bytes())
report = {'revision': 'floor19', 'bedroom': [], 'bathroom': [], 'grout': []}


def store(values, size=None):
    values = np.asarray(values)
    dtype = '<u4' if values.dtype.kind in 'iu' else '<f4'
    values = values.astype(dtype).ravel()
    while len(raw) % 4:
        raw.append(0)
    desc = {'offset': len(raw), 'length': len(values),
            'type': 'Uint32Array' if dtype == '<u4' else 'Float32Array'}
    if size:
        desc['itemSize'] = size
    raw.extend(values.tobytes())
    return desc


def export_mesh(mesh):
    mesh.calc_loop_triangles()
    positions, normals, uv, uv1 = [], [], [], []
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        n = mesh.corner_normals[loop.index].vector
        positions.append((p.x, p.z, -p.y))
        normals.append((n.x, n.z, -n.y))
        uv.append(tuple(mesh.uv_layers['UVMap'].data[loop.index].uv))
        uv1.append(tuple(mesh.uv_layers['uv1'].data[loop.index].uv))
    gid = len(data['geometries'])
    data['geometries'].append({
        'id': gid,
        'attributes': {'position': store(positions, 3), 'normal': store(normals, 3),
                       'uv': store(uv, 2), 'uv1': store(uv1, 2)},
        'index': store([i for tri in mesh.loop_triangles for i in tri.loops]),
        'groups': [], 'userData': {'authoring': 'Blender', 'sourceType': 'RectifiedCeramic',
                                 'floorRevision': 'floor19'},
    })
    return gid


def make_tile(name, width, depth, cx, cz, size):
    # The whole centre is a single flat polygon. Explicit hard normals prevent
    # box-corner interpolation from turning a flat tile into a padded square.
    edge = .00018
    corner = .0004
    verts = []
    for z, inset in [(-.011, 0), (.011 - edge, 0), (.011, edge)]:
        x, y = width / 2 - inset, depth / 2 - inset
        r = max(.0001, corner - inset)
        ring = [(-x+r, -y), (x-r, -y), (x, -y+r), (x, y-r),
                (x-r, y), (-x+r, y), (-x, y-r), (-x, -y+r)]
        verts.extend((a, b, z) for a, b in ring)
    faces = [tuple(reversed(range(8))), tuple(range(16, 24))]
    for ring in range(2):
        for i in range(8):
            j = (i+1) % 8
            faces.append((ring*8+i, ring*8+j, (ring+1)*8+j, (ring+1)*8+i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    for face in mesh.polygons:
        face.use_smooth = False
    texture = mesh.uv_layers.new(name='UVMap')
    indirect = mesh.uv_layers.new(name='uv1')
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        # Physical texture size stays consistent on the cut boundary tiles.
        texture.data[loop.index].uv = (p.x/size + .5, p.y/size + .5)
        indirect.data[loop.index].uv = ((cx+p.x+1.4)/2.8, (3.18-cz+p.y)/4.98)
    mesh.update()
    top = [p for p in mesh.polygons if p.normal.z > .999 and p.center.z > .0109]
    assert len(top) == 1
    assert all(abs(mesh.corner_normals[i].vector.z-1) < 1e-6
               for face in top for i in face.loop_indices), 'Tile top must remain planar'
    return mesh


def place(mesh, mid, name, x, y, z, node_id=None, grout=False):
    if node_id is None:
        node_id = len(data['nodes'])
        node = copy.deepcopy(old_nodes[2])
        node['id'] = node_id
        data['nodes'].append(node)
        obj = bpy.data.objects.new(name, mesh)
        assembly.objects.link(obj)
        obj.parent = objects[0]
        objects[node_id] = obj
    else:
        node = data['nodes'][node_id]
        obj = objects[node_id]
        obj.modifiers.clear()
        obj.data = mesh
    mesh.materials.clear()
    mesh.materials.append(materials[mid])
    obj.material_slots[0].link = 'DATA'
    obj.material_slots[0].material = materials[mid]
    obj.name = name
    obj.location = (x, -z, y)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    obj['web_node_id'] = node_id
    obj['web_name'] = name
    obj['floor_revision'] = 'floor19'
    node.update(name=name, material=mid, geometry=export_mesh(mesh),
                matrix=[1,0,0,0, 0,1,0,0, 0,0,1,0, x,y,z,1],
                castShadow=not grout, receiveShadow=True)
    node['userData'] = {'authoring': 'Blender', 'blenderNode': node_id,
                        'floorRevision': 'floor19', 'floorSurface': 'grout' if grout else 'ceramic'}
    obj['web_user_data'] = json.dumps(node['userData'])
    return node_id


def grid(x0, x1, z0, z1, size, origin_x, origin_z):
    cells = []
    for ix in range(math.floor((x0-origin_x)/size+1e-6), math.ceil((x1-origin_x)/size-1e-6)):
        a, b = max(x0, origin_x+ix*size), min(x1, origin_x+(ix+1)*size)
        for iz in range(math.floor((z0-origin_z)/size+1e-6), math.ceil((z1-origin_z)/size-1e-6)):
            c, d = max(z0, origin_z+iz*size), min(z1, origin_z+(iz+1)*size)
            cells.append((a, b, c, d))
    return cells


bed_cells = grid(-1.4, 1.4, -1.8, 1.8, .6, -1.4, -1.8)
bed_cells += grid(.25, 1.4, 1.8, 3.18, .6, -1.4, -1.8)
bath_cells = grid(-1.4, .25, 1.8, 3.18, .3, -1.4, 1.8)
assert len(bed_cells) == 39 and len(bath_cells) == 30
for room, cells, ids, mid, size, height, gap in [
    ('bedroom', bed_cells, bed_ids, 1, .6, 0, .0014),
    ('bathroom', bath_cells, bath_ids, 2, .3, .085, .0016),
]:
    for i, (a, b, c, d) in enumerate(cells):
        name = f'{room}-ceramic-tile-{i+1:02d}'
        cx, cz = (a+b)/2, (c+d)/2
        mesh = make_tile(name, b-a-gap, d-c-gap, cx, cz, size)
        nid = place(mesh, mid, name, cx, height, cz, ids[i] if i < len(ids) else None)
        report[room].append({'node': nid, 'bounds': [a,b,c,d], 'gap': gap,
                             'top': height+.011, 'planarTopNormals': True})


def linear(v):
    return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4


def grout_material(name, hex_color, indirect):
    mid = len(data['materials'])
    rgb = [linear(int(hex_color[i:i+2], 16)/255) for i in (0,2,4)]
    desc = copy.deepcopy(data['materials'][2])
    desc.update(id=mid, textures={'lightMap': 1} if indirect else {},
                colors={'color': rgb, 'emissive': [0,0,0]},
                userData={'surfaceFinish': 'fine nearly flush grout', 'floorRevision': 'floor19'})
    desc['props'].update(roughness=.84, bumpScale=0, lightMapIntensity=.46 if indirect else 1)
    if indirect:
        desc['userData']['bakedIndirect'] = 'floor'
    data['materials'].append(desc)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*rgb, 1)
    bs = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None:
        bs = mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
    output = next((n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    if output is None:
        output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bs.outputs['BSDF'], output.inputs['Surface'])
    bs.inputs['Base Color'].default_value = (*rgb, 1)
    bs.inputs['Roughness'].default_value = .84
    mat['web_material_id'] = mid
    materials[mid] = mat
    return mid


bed_grout = grout_material('Bedroom · warm grey fine grout', 'c1bdb3', True)
bath_grout = grout_material('Bathroom · light neutral grey fine grout', 'aeb0aa', False)
for name, a,b,c,d, top, mid in [
    ('bedroom-grout-bed', -1.4,1.4,-1.8,1.8,.01075,bed_grout),
    ('corridor-grout-bed', .25,1.4,1.8,3.18,.01075,bed_grout),
    ('bathroom-grout-bed', -1.4,.25,1.8,3.18,.09570,bath_grout),
]:
    cx, cz = (a+b)/2, (c+d)/2
    # Solid substrate under the joints, only 0.25–0.30 mm below the tile surface.
    mesh = make_tile(name, b-a, d-c, cx, cz, .6)
    nid = place(mesh, mid, name, cx, top-.011, cz, grout=True)
    report['grout'].append({'node': nid, 'top': top})

# Check that no unrelated node placement, geometry or interaction metadata changed.
for i, before in enumerate(old_nodes):
    if i not in bed_ids + bath_ids:
        assert data['nodes'][i] == before, f'Unrelated node changed: {i}'

data['revision'] = 'floor19'
data['statistics']['meshes'] = len(data['geometries'])
data['statistics']['triangles'] = sum(g['index']['length']//3 for g in data['geometries'])
data['statistics']['floorRefinement'] = {'bedroomTiles': 39, 'bathroomTiles': 30,
    'bedroomJointMm': 1.4, 'bathroomJointMm': 1.6, 'edgeEaseMm': .18,
    'groutRecessMm': [.25,.30], 'planarTopNormals': True, 'continuousBedroomGrid': True}
bpy.context.scene['web_revision'] = 'floor19'
bpy.context.scene['floor_notes'] = 'Photo-referenced narrow nearly flush grout; flat ceramic normals; 600/300mm grids. Run tools/refine-floor.py through official MCP after regenerating blender18.'
bpy.context.view_layer.update()
project = ROOT / 'generated-assets/full-room/永旺家园-完整场景.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(project))
(OUT / 'geometry.bin').write_bytes(raw)
(OUT / 'geometry.bin.gz').write_bytes(gzip.compress(raw, compresslevel=9))
MANIFEST.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
(ROOT / 'analysis/floor19-geometry-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
result = {'saved': str(project), 'revision': 'floor19', 'floorRefinement': data['statistics']['floorRefinement'],
          'untouchedOriginalNodes': len(old_nodes)-len(bed_ids)-len(bath_ids),
          'newObjects': len(data['nodes'])-len(old_nodes), 'binaryBytes': len(raw)}
