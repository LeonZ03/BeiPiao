"""correction51c -> moto52. Replace the courtyard GSX via official Blender Lab MCP.

The prepared asset owns its baked projection maps. Existing parking transform,
room geometry, reference IDs, materials and interaction pivots are retained.
"""
from pathlib import Path
import json
import shutil

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
exec(compile((HERE / 'exterior-authoring.py').read_text('utf8'),
             str(HERE / 'exterior-authoring.py'), 'exec'))
assert data['revision'] == bpy.context.scene.get('web_revision') == 'correction51c'
ASSET = ROOT / 'rooms/yongwang-jiayuan/assets/motorcycle'
asset_path = ASSET / 'GSX250R-courtyard.blend'
metadata = json.loads((ASSET / 'gsx52-source.json').read_text('utf8'))
parking = obs[750]
old_ids = set(range(751, 771))
assert all(data['nodes'][nid]['parent'] == 750 for nid in old_ids)


def compact_attribute(values, size, normalized=False):
    """Use the existing pack decoder; keep sub-0.1 mm position precision."""
    values = np.asarray(values, dtype=float).reshape(-1, size)
    if normalized:
        quantized = np.rint(np.clip(values, -1, 1) * 32767).astype('<i2')
        extra = dict(normalized=True)
    else:
        low, high = values.min(axis=0), values.max(axis=0)
        centre = (low + high) / 2
        scale = np.maximum((high - low) / 65534, 1e-12)
        quantized = np.rint((values - centre) / scale).astype('<i2')
        assert np.max(np.abs(quantized * scale + centre - values)) < .0001
        extra = dict(decodeScale=scale.tolist(), decodeOffset=centre.tolist())
    while len(raw) % 4:
        raw.append(0)
    descriptor = dict(offset=len(raw), length=quantized.size,
                      type='Int16Array', itemSize=size, **extra)
    raw.extend(quantized.tobytes())
    return descriptor


with bpy.data.libraries.load(str(asset_path), link=False) as (source, target):
    target.objects = ['GSX52_BakedVehicle']
vehicle = target.objects[0]
collection.objects.link(vehicle)
bpy.context.view_layer.update()

# Match the old tyres' ground plane after the existing slight parking lean.
old_bottom = min((obs[nid].matrix_world @ v.co).z
                 for nid in [751, 752] for v in obs[nid].data.vertices)
new_bottom = min((parking.matrix_world @ vehicle.matrix_world @ v.co).z
                 for v in vehicle.data.vertices)
rise = (old_bottom - new_bottom) / parking.matrix_world[2][2]
for v in vehicle.data.vertices:
    v.co.z += rise

texture_ids = {}
for key, filename in [('map', 'gsx52-albedo.png'), ('metalnessMap', 'gsx52-metalness.png')]:
    shutil.copyfile(ASSET / 'textures' / filename, OUT / filename)
    tid = len(data['textures'])
    desc = copy.deepcopy(data['textures'][11])
    desc.update(id=tid, webPath='./assets/full-room/' + filename,
                colorSpace='srgb' if key == 'map' else '', repeat=[1, 1],
                offset=[0, 0], rotation=0, channel=0, wrapS=1001, wrapT=1001,
                flipY=True, anisotropy=8)
    data['textures'].append(desc)
    texture_ids[key] = tid

groups = {}
for poly in vehicle.data.polygons:
    source_material = vehicle.data.materials[poly.material_index]
    parameters = json.loads(source_material['gsx52_parameters'])
    glass = source_material.name.split('.')[0] in {
        'COL_R67_OwnerWindscreen', 'COL_R67_ScreenGlass', 'COL_R67_ClearLens'}
    key = (round(parameters['roughness'], 3), glass, round(parameters['ior'], 3))
    groups.setdefault(key, []).append(poly)

for index, ((roughness, glass, ior), polygons) in enumerate(sorted(groups.items())):
    nid = 751 + index if index < 20 else len(data['nodes'])
    mid = len(data['materials'])
    mat = vehicle.data.materials[polygons[0].material_index].copy()
    mat.name = f'GSX52 surface {index:02d}'
    mat['web_material_id'] = mid
    desc = dict(id=mid, name=mat.name, type='MeshPhysicalMaterial',
                props=dict(roughness=roughness, metalness=1, side=2,
                           transparent=glass, opacity=.28 if glass else 1,
                           depthWrite=not glass, ior=ior,
                           envMapIntensity=.65),
                colors=dict(color=[1, 1, 1]), vectors={}, textures=texture_ids.copy(),
                userData=dict(authoring='Blender', motorcycle52=True))
    data['materials'].append(desc)
    mats[mid] = mat

    source_indices = sorted({i for p in polygons for i in p.vertices})
    remap = {old: new for new, old in enumerate(source_indices)}
    me = bpy.data.meshes.new(f'GSX52 surface {index:02d}')
    me.from_pydata([vehicle.data.vertices[i].co for i in source_indices], [],
                  [[remap[i] for i in p.vertices] for p in polygons])
    me.materials.append(mat)
    uv0, uv1 = me.uv_layers.new(name='UVMap'), me.uv_layers.new(name='UV1')
    normals = []
    for original, poly in zip(polygons, me.polygons):
        poly.use_smooth = original.use_smooth
        for source_loop, new_loop in zip(original.loop_indices, poly.loop_indices):
            uv = vehicle.data.uv_layers['UVMap'].data[source_loop].uv
            uv0.data[new_loop].uv = uv
            uv1.data[new_loop].uv = uv
            normals.append(tuple(vehicle.data.corner_normals[source_loop].vector))
    me.uv_layers.active = uv0
    me.update()
    me.normals_split_custom_set(normals)
    name = f'GSX52 material batch {index:02d}'
    if index < 20:
        obj = obs[nid]
        obj.modifiers.clear()
        obj.data = me
        obj.name = name
    else:
        obj = bpy.data.objects.new(name, me)
        collection.objects.link(obj)
        obj.parent = parking
        obj['web_node_id'] = nid
        obs[nid] = obj
        data['nodes'].append(copy.deepcopy(before['nodes'][751]))
    obj.matrix_local = Matrix.Identity(4)
    obj.material_slots[0].link = 'DATA'
    obj.hide_render = False
    obj['web_name'] = name
    obj['web_user_data'] = json.dumps(dict(authoring='Blender', blenderNode=nid, motorcycle52=True))
    me.calc_loop_triangles()
    # Index by full vertex attributes, preserving UV seams and custom normals.
    vertices, normals_out, uvs, indices = [], [], [], []
    unique = {}
    for tri in me.loop_triangles:
        for li in tri.loops:
            point = me.vertices[me.loops[li].vertex_index].co
            normal = me.corner_normals[li].vector
            uv = uv0.data[li].uv
            values = (point.x, point.z, -point.y, normal.x, normal.z, -normal.y, uv.x, uv.y)
            if values not in unique:
                unique[values] = len(vertices)
                vertices.append(values[:3])
                normals_out.append(values[3:6])
                uvs.append(values[6:])
            indices.append(unique[values])
    attrs = dict(position=compact_attribute(vertices, 3),
                 normal=compact_attribute(normals_out, 3, normalized=True),
                 uv=compact_attribute(uvs, 2, normalized=True))
    attrs['uv1'] = copy.deepcopy(attrs['uv'])
    gid = len(data['geometries'])
    data['geometries'].append(dict(id=gid, attributes=attrs,
                                   index=pack(np.array(indices, dtype='uint32')),
                                   groups=[], userData=dict(authoring='Blender', revision='moto52')))
    data['nodes'][nid].update(id=nid, parent=750, name=name, type='Mesh', geometry=gid,
                             material=mid, matrix=flat(Matrix.Identity(4)), visible=True,
                             castShadow=True, receiveShadow=True, frustumCulled=True,
                             userData=dict(authoring='Blender', blenderNode=nid, motorcycle52=True))
    changed.add(nid)
    geometry_changed.add(nid)

for nid in sorted(old_ids - changed):
    obs[nid].hide_render = True
    data['nodes'][nid]['visible'] = False
    changed.add(nid)
bpy.data.objects.remove(vehicle, do_unlink=True)
# Appended asset images must resolve from this complete source as well.
for image in bpy.data.images:
    if image.name.startswith('GSX52_'):
        filename = 'gsx52-albedo.png' if 'albedo' in image.name else 'gsx52-metalness.png'
        image.filepath = str(ASSET / 'textures' / filename)
details = copy.deepcopy(before['statistics']['exteriorRefinement'])
details['motorcycle52'] = dict(**metadata, batches=len(groups), groundCorrection=rise,
                              parkingNode=750, parent='correction51c',
                              deliveryPrecision='16-bit; positions <0.1 mm rounding error')
result = save('moto52', details)
# Keep historical IDs but avoid publishing superseded, unreferenced buffers.
__file__ = str(HERE / 'compact-motorcycle52-pack.py')
exec(compile(Path(__file__).read_text('utf8'), __file__, 'exec'))
