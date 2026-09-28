"""Architecture02 -> architecture03. Execute with official Blender Lab MCP.

User 2026-09-28: north/weak daylight, one ceiling lamp, independent curtains.
P03/P04: right curtain ends on the counter, left curtain reaches the floor.
Lamp shape/dimensions and cloth clearances are conservative photo estimates.
"""
from pathlib import Path
import json
import math
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
scene = bpy.context.scene
assert scene.get('component') == 'architecture'
assert scene.get('component_revision') == 'architecture02-radiator', scene.get('component_revision')
bpy.context.preferences.filepaths.save_version = 0
coll = bpy.data.collections['C43_Architecture']
old_root = bpy.data.objects['C43_Curtain_Pivot']
assert json.loads(old_root['c43_interaction'])['id'] == 'curtain'
del old_root['c43_interaction']
old_root.name = 'C43_Curtain_Assembly'

# Independent roots; preserve all mesh coordinates and the authored morph path.
for side in ('Left', 'Right'):
    pivot = bpy.data.objects.new('C43_Curtain_' + side + '_Pivot', None)
    coll.objects.link(pivot)
    pivot.parent = old_root
    pivot['c43_interaction'] = json.dumps(dict(id='curtain-' + side.lower(), kind='curtain', axis='x', audio='curtain'))
    for suffix in ('', '_Rings'):
        obj = bpy.data.objects['C43_Curtain_' + side + suffix]
        world = obj.matrix_world.copy()
        obj.parent = pivot
        obj.matrix_world = world
        obj.data = obj.data.copy()
        keys = obj.data.shape_keys.key_blocks
        # The closed seam belongs beside the counter's left end. Gathered
        # endpoints remain on the existing rod; no ring is scaled thinner.
        for key in keys:
            if key.name == 'Basis':
                for p in key.data:
                    if side == 'Left':
                        p.co.x = -.63 + (p.co.x + .63) * (.868 / 1.03)
                    else:
                        p.co.x = 1.43 - (1.43 - p.co.x) * (1.192 / 1.03)
            if side == 'Right' and not suffix:
                for p in key.data:
                    p.co.z = 2.4 - (2.4 - p.co.z) * ((2.4 - 1.027) / (2.4 - .0543))
        for p, original in zip(obj.data.vertices, keys['Basis'].data):
            p.co = original.co
        if not suffix:
            # Keep physical texture density when changing the cloth panel sizes.
            uv = obj.data.uv_layers.active
            for loop in uv.data:
                loop.uv.x *= (.868 if side == 'Left' else 1.192) / 1.03
                if side == 'Right':
                    loop.uv.y *= (2.4 - 1.027) / (2.4 - .0543)
            mat = obj.data.materials[0].copy()
            mat.name = 'C43_Grey_woven_curtain_' + side
            obj.data.materials[0] = mat
            user = json.loads(mat.get('web_userData', '{}'))
            user.update(curtainSide=side.lower(), multiplyCurtainAlbedo=True)
            mat['web_userData'] = json.dumps(user)
            bs = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            bs.inputs['Sheen Tint'].default_value = (.42, .43, .44, 1)
            bs.inputs['Sheen Weight'].default_value = .32
            bs.inputs['Roughness'].default_value = .86
            bs.inputs['Emission Color'].default_value = (.82, .88, 1, 1)
            bs.inputs['Emission Strength'].default_value = .045
            normal = next((n for n in mat.node_tree.nodes if n.type == 'NORMAL_MAP'), None)
            if normal:
                normal.inputs['Strength'].default_value = .32
            # A seam/thickness mask only; no photographed lighting is baked in.
            size = 256
            v, u = np.mgrid[0:size, 0:size] / (size - 1)
            edge = np.minimum(np.minimum(u, 1-u)*10, np.minimum(v, 1-v)*15)
            mask = .16 + .84*np.clip(edge, 0, 1)
            pixels = np.ones((size, size, 4), dtype=np.float32)
            pixels[:, :, :3] = mask[:, :, None]
            image = bpy.data.images.new('C43_Cloth_transmission_' + side, size, size)
            image.pixels.foreach_set(pixels.ravel())
            image.colorspace_settings.name = 'sRGB'
            image.filepath_raw = str(ROOM / 'assets/architecture/textures' / ('cloth-transmission-' + side.lower() + '.png'))
            image.file_format = 'PNG'
            image.save()
            tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = image
            tex['web_map'] = 'emissiveMap'
            tex.extension = 'EXTEND'
            # UV0 is meters; normalize only the dedicated thickness mask.
            mapping = mat.node_tree.nodes.new('ShaderNodeMapping')
            coords = mat.node_tree.nodes.new('ShaderNodeUVMap')
            coords.uv_map = uv.name
            mapping.inputs['Scale'].default_value = (1/(.868 if side == 'Left' else 1.192), 1/(2.334 if side == 'Left' else 1.366), 1)
            mat.node_tree.links.new(coords.outputs['UV'], mapping.inputs['Vector'])
            mat.node_tree.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])

# Remove the assumed perimeter lights. The dropped ceiling itself is retained.
old_lights = [o for o in coll.objects if o.name.startswith('C43_Downlight_')]
assert len(old_lights) == 20
for obj in old_lights:
    bpy.data.objects.remove(obj, do_unlink=True)

def lamp_piece(name, radius, depth, height, material):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth, location=(.1, -1.425, height))
    obj = bpy.context.object
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)
    obj.data.materials.append(material)
    bevel = obj.modifiers.new('Soft diffuser rim', 'BEVEL')
    bevel.width = .008
    bevel.segments = 3
    obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    obj['web_tags'] = json.dumps(dict(ceilings=True, lightFixture=True, noCollision=True))
    # The actual light sits immediately beneath the diffuser.
    obj['web_userData'] = json.dumps(dict(noShadow=True))
    return obj

paint = bpy.data.objects['C43_Radiator_Cap_Front'].data.materials[0]
diffuser = bpy.data.materials['C43_Downlight_diffuser'].copy() if 'C43_Downlight_diffuser' in bpy.data.materials else next(m for m in bpy.data.materials if 'Downlight_diffuser' in m.name).copy()
diffuser.name = 'C43_CeilingLamp_Diffuser'
diffuser['web_userData'] = json.dumps(dict(lightFixture=True))
diffuser['web_props'] = json.dumps(dict(emissive='#fff4e6', emissiveIntensity=0))
lamp_piece('C43_CeilingLamp_Base', .205, .026, 2.735, paint)
lamp_piece('C43_CeilingLamp_Diffuser', .193, .06, 2.698, diffuser)
scene['component_revision'] = 'architecture03'
scene['web_revision'] = 'courtyard43-interior02'
scene['north_balcony_confirmed'] = True
bpy.context.view_layer.update()
for image in bpy.data.images:
    if image.source == 'FILE' and image.filepath:
        image.filepath = bpy.path.relpath(bpy.path.abspath(image.filepath))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM / 'assets/architecture/Courtyard43-architecture.blend'))
result = dict(componentRevision='architecture03', independentCurtains=True, ceilingFixtures=1)
