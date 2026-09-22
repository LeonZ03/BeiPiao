"""PBR / hierarchy / morph exporter. Run inside official Blender Lab MCP only.

No persistent browser geometry or material is manufactured by the viewer.
Active Blender material outputs, evaluated normals and UV seams are authoritative.
"""
from array import array
import gzip
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
OUT = ROOT / 'room-site/dist/assets/rooms/Courtyard43/interior'
WEB = './assets/rooms/Courtyard43/interior'
TO_WEB = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def meta(block, key):
    value = block.get(key, '{}')
    return json.loads(value) if isinstance(value, str) else dict(value)


def export_interior():
    scene = bpy.context.scene
    assert scene.get('room_id') == 'Courtyard43' and scene.get('stage') == 'interior'
    assert scene.unit_settings.system == 'METRIC' and scene.unit_settings.scale_length == 1
    layout = json.loads((ROOM / 'history/inputs/approved-layout.json').read_text(encoding='utf-8'))
    assert layout['structureApproved']
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'textures').mkdir(exist_ok=True)
    buffer, textures, materials, geometries, bounds = bytearray(), [], [], [], []
    texture_ids, material_ids = {}, {}

    def pack(values, item_size, integer=False):
        while len(buffer) % 4:
            buffer.append(0)
        a = array('I' if integer else 'f', values)
        assert a.itemsize == 4
        if sys.byteorder != 'little':
            a.byteswap()
        desc = dict(type='Uint32Array' if integer else 'Float32Array', offset=len(buffer), length=len(a), itemSize=item_size)
        buffer.extend(a.tobytes())
        return desc

    def source_node(socket):
        return socket.links[0].from_node if socket and socket.is_linked else None

    def texture(node, color=False):
        assert node.type == 'TEX_IMAGE' and node.image, node.name
        img = node.image
        path = Path(bpy.path.abspath(img.filepath, library=img.library)).resolve()
        if not path.is_file():
            # Packed/generated images belong to the saved source, not references.
            path = OUT / 'textures' / (bpy.path.clean_name(img.name) + '.png')
            img.save(filepath=str(path))
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()[:16]
        target = OUT / 'textures' / (digest + path.suffix.lower())
        if path != target:
            shutil.copyfile(path, target)
        repeat, offset, rotation, channel = [1, 1], [0, 0], 0, 0
        vector = source_node(node.inputs.get('Vector'))
        if vector and vector.type == 'MAPPING':
            repeat = list(vector.inputs['Scale'].default_value)[:2]
            offset = list(vector.inputs['Location'].default_value)[:2]
            rotation = vector.inputs['Rotation'].default_value.z
            vector = source_node(vector.inputs.get('Vector'))
        if vector and vector.type == 'UVMAP':
            channel = 1 if vector.uv_map.lower() in ('uv1', 'lightmap', 'uvmap.001') else 0
        elif vector:
            assert vector.type == 'TEX_COORD', f'Bake unsupported texture coordinates: {node.name}'
        desc = dict(webPath=f'{WEB}/textures/{target.name}', wrapS=1000 if node.extension == 'REPEAT' else 1001,
                    wrapT=1000 if node.extension == 'REPEAT' else 1001, magFilter=1006, minFilter=1008,
                    anisotropy=8, flipY=True, colorSpace='srgb' if color else '', channel=channel,
                    rotation=rotation, repeat=repeat, offset=offset, center=[0, 0], generateMipmaps=True)
        key = json.dumps(desc, sort_keys=True)
        if key not in texture_ids:
            texture_ids[key] = len(textures)
            textures.append(dict(id=len(textures), **desc))
        return texture_ids[key]

    def material(mat):
        if mat.name in material_ids:
            return material_ids[mat.name]
        assert mat.use_nodes, mat.name
        output = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        shader = source_node(output.inputs['Surface'])
        assert shader and shader.type == 'BSDF_PRINCIPLED', f'Bake unsupported shader: {mat.name}'
        value = lambda name, default: shader.inputs[name].default_value if name in shader.inputs else default
        props = dict(roughness=float(value('Roughness', .5)), metalness=float(value('Metallic', 0)), side=2,
                     opacity=float(value('Alpha', 1)), transparent=value('Alpha', 1) < 1, depthWrite=value('Alpha', 1) >= 1)
        props.update(ior=float(value('IOR', 1.5)), sheen=float(value('Sheen Weight', 0)),
                     sheenRoughness=float(value('Sheen Roughness', .5)), clearcoat=float(value('Coat Weight', 0)),
                     clearcoatRoughness=float(value('Coat Roughness', .03)))
        colors = dict(color=list(value('Base Color', mat.diffuse_color))[:3])
        maps, vectors = {}, {}
        for socket_name, web_name, color in [('Base Color', 'map', True), ('Roughness', 'roughnessMap', False),
                                              ('Metallic', 'metalnessMap', False), ('Alpha', 'alphaMap', False)]:
            node = source_node(shader.inputs.get(socket_name))
            if node:
                assert node.type == 'TEX_IMAGE', f'Bake {mat.name}/{socket_name}/{node.type}'
                maps[web_name] = texture(node, color)
                if web_name == 'map':
                    colors['color'] = [1, 1, 1]
                if web_name == 'roughnessMap':
                    props['roughness'] = 1
                if web_name == 'metalnessMap':
                    props['metalness'] = 1
        normal = source_node(shader.inputs.get('Normal'))
        if normal:
            assert normal.type in ('BUMP', 'NORMAL_MAP'), f'Bake normal {mat.name}'
            input_name = 'Height' if normal.type == 'BUMP' else 'Color'
            image = source_node(normal.inputs[input_name])
            assert image and image.type == 'TEX_IMAGE', f'Bake normal texture {mat.name}'
            if normal.type == 'BUMP':
                maps['bumpMap'] = texture(image)
                props['bumpScale'] = float(normal.inputs['Distance'].default_value * normal.inputs['Strength'].default_value) * (-1 if normal.invert else 1)
            else:
                maps['normalMap'] = texture(image)
                strength = float(normal.inputs['Strength'].default_value)
                vectors['normalScale'] = [strength, strength]
        emission = value('Emission Color', (0, 0, 0, 1))
        strength = float(value('Emission Strength', 0))
        if max(emission[:3]) > 0 and strength:
            colors['emissive'] = list(emission)[:3]
            props['emissiveIntensity'] = strength
        props.update(meta(mat, 'web_props'))
        # Color/vector overrides belong in their own serialized sections.
        for key in ['color', 'emissive', 'attenuationColor', 'sheenColor']:
            if key in props:
                override = props.pop(key)
                if isinstance(override, str) and override.startswith('#'):
                    srgb = [int(override[i:i+2], 16)/255 for i in (1, 3, 5)]
                    colors[key] = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in srgb]
                else:
                    colors[key] = list(override)[:3]
        for key in ['normalScale', 'clearcoatNormalScale']:
            if key in props:
                vectors[key] = props.pop(key)
        mid = len(materials)
        material_ids[mat.name] = mid
        materials.append(dict(id=mid, name=mat.name, type='MeshPhysicalMaterial', props=props, colors=colors,
                              vectors=vectors, textures=maps, userData=dict(authoring='Blender', **meta(mat, 'web_userData'))))
        return mid

    matrix_array = lambda m: [v for column in m.transposed() for v in column]
    nodes = [dict(id=0, name='courtyard43-world', type='Group', parent=-1, matrix=matrix_array(Matrix.Identity(4)),
                  visible=True, castShadow=False, receiveShadow=False, renderOrder=0, frustumCulled=True, userData={})]
    objects = sorted((o for o in scene.objects if o.type in ('MESH', 'EMPTY') and not o.hide_render), key=lambda o: o.name)
    ids = {obj.name: i+1 for i, obj in enumerate(objects)}
    refs = dict(world=0, cutaway=[], ceilings=[], curtainPanels=[], switches=[], lightFixture=[], glass=[])
    interactions = []
    triangle_count = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rotation = TO_WEB.to_3x3()

    for obj in objects:
        tags = meta(obj, 'web_tags')
        parent = ids.get(obj.parent.name, 0) if obj.parent else 0
        matrix = obj.parent.matrix_world.inverted() @ obj.matrix_world if parent else obj.matrix_world
        node = dict(id=ids[obj.name], name=obj.name, type='Group' if obj.type == 'EMPTY' else 'Mesh', parent=parent,
                    matrix=matrix_array(TO_WEB @ matrix @ TO_WEB.inverted()), visible=True,
                    castShadow=not tags.get('glass', False), receiveShadow=True, renderOrder=0, frustumCulled=True,
                    userData=dict(authoring='Blender', **meta(obj, 'web_userData'), **tags))
        for key in refs:
            if key != 'world' and tags.get(key):
                refs[key].append(node['id'])
        if obj.get('c43_interaction'):
            interactions.append(dict(node=node['id'], **meta(obj, 'c43_interaction')))
        if obj.type == 'MESH':
            keys = obj.data.shape_keys
            original_values = [key.value for key in keys.key_blocks] if keys else []
            if keys:
                for key in keys.key_blocks:
                    key.value = 0
                bpy.context.view_layer.update()
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
            mesh.calc_loop_triangles()
            assert mesh.uv_layers.active, f'Missing UV: {obj.name}'
            assert obj.data.materials and all(obj.data.materials), f'Missing material {obj.name}'
            mid = [material(mat) for mat in obj.data.materials]
            node['material'] = mid[0] if len(mid) == 1 else mid
            uv = mesh.uv_layers.active
            uv1 = next((layer for layer in mesh.uv_layers if layer != uv), None)
            positions, normals, uvs, uv1s, indices, groups, loop_order = [], [], [], [], [], [], []
            unique = {}
            for tri in mesh.loop_triangles:
                if not groups or groups[-1]['materialIndex'] != tri.material_index:
                    groups.append(dict(start=len(indices), count=0, materialIndex=tri.material_index))
                for li in tri.loops:
                    vi = mesh.loops[li].vertex_index
                    pos = rotation @ mesh.vertices[vi].co
                    normal = (rotation @ mesh.corner_normals[li].vector).normalized()
                    tex = uv.data[li].uv
                    tex1 = uv1.data[li].uv if uv1 else ()
                    key = (vi if keys else -1, *[round(v, 7) for v in (*pos, *normal, *tex, *tex1)])
                    if key not in unique:
                        unique[key] = len(unique)
                        positions.extend(pos); normals.extend(normal); uvs.extend(tex); uv1s.extend(tex1)
                        loop_order.append((vi, li))
                    indices.append(unique[key]); groups[-1]['count'] += 1
            desc = dict(id=len(geometries), attributes=dict(position=pack(positions, 3), normal=pack(normals, 3), uv=pack(uvs, 2)),
                        index=pack(indices, 1, True), groups=groups if len(mid) > 1 else [], userData=dict(authoring='Blender'))
            if uv1:
                desc['attributes']['uv1'] = pack(uv1s, 2)
            points = [TO_WEB @ (obj.matrix_world @ v.co) for v in mesh.vertices]
            bounds.append(dict(name=obj.name, min=[min(p[a] for p in points) for a in range(3)], max=[max(p[a] for p in points) for a in range(3)]))
            topology = (len(mesh.vertices), len(mesh.loops))
            evaluated.to_mesh_clear()
            if keys and len(keys.key_blocks) > 1:
                morphs = dict(position=[], normal=[])
                for shape in list(keys.key_blocks)[1:]:
                    shape.value = 1
                    bpy.context.view_layer.update()
                    evaluated = obj.evaluated_get(depsgraph)
                    target = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
                    assert topology == (len(target.vertices), len(target.loops)), f'Morph topology changed: {obj.name}'
                    mp, mn = [], []
                    for vi, li in loop_order:
                        mp.extend(rotation @ target.vertices[vi].co)
                        mn.extend((rotation @ target.corner_normals[li].vector).normalized())
                    morphs['position'].append(pack(mp, 3)); morphs['normal'].append(pack(mn, 3))
                    evaluated.to_mesh_clear()
                    shape.value = 0
                for key, value in zip(keys.key_blocks, original_values):
                    key.value = value
                bpy.context.view_layer.update()
                desc['morphTargets'] = morphs
                desc['userData']['morphNames'] = [key.name for key in list(keys.key_blocks)[1:]]
            node['geometry'] = len(geometries)
            geometries.append(desc)
            triangle_count += len(indices)//3
        nodes.append(node)

    manifest = dict(format='blender-room-pack-1', roomId='Courtyard43', stage='interior', structureApproved=True,
                    revision=scene['web_revision'], parentRevision=layout['parentRevision'],
                    binary=f'{WEB}/geometry.bin', compressedBinary=f'{WEB}/geometry.bin.gz',
                    nodes=nodes, geometries=geometries, materials=materials, textures=textures, refs=refs,
                    interactions=interactions, review=layout,
                    statistics=dict(meshes=len(geometries), triangles=triangle_count,
                                    vertices=sum(g['attributes']['position']['length']//3 for g in geometries)))
    (OUT / 'geometry.bin').write_bytes(buffer)
    (OUT / 'geometry.bin.gz').write_bytes(gzip.compress(buffer, mtime=0))
    (OUT / 'scene.json').write_text(json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    used = {Path(texture['webPath']).name for texture in textures}
    for path in (OUT / 'textures').iterdir():
        if path.is_file() and re.fullmatch(r'[a-f0-9]{16}\.[a-z0-9]+', path.name) and path.name not in used:
            path.unlink()  # Only obsolete, reproducible hash-named exports.
    report = ROOT / 'analysis/Courtyard43'
    report.mkdir(parents=True, exist_ok=True)
    (report / 'interior-bounds.json').write_text(json.dumps(bounds, indent=2), encoding='utf-8')
    return dict(revision=manifest['revision'], statistics=manifest['statistics'], materials=len(materials), textures=len(textures),
                bytes=len(buffer), interactions=interactions, manifest=str(OUT / 'scene.json'))


if __name__ == '__main__':
    result = export_interior()
