"""Courtyard43 interior14 -> interior15 curtain refinement.

Run apply_curtains15() explicitly from the official Blender Lab MCP. Importing
this module is side-effect free. The function edits only the two curtain
panels and their assigned materials in memory; it does not save or export.
The current shell already has real normal-offset thickness, so this stage
targets the high-frequency glint and adds restrained sewn edge rolls and broad
fabric irregularity without moving its supported outline, header, or overlap.
"""
import bpy
import json
import math
import numpy as np
import struct, zlib
from pathlib import Path


def _smooth(t):
    t = max(0.0, min(1.0, float(t)))
    return t * t * (3.0 - 2.0 * t)


def apply_curtains15():
    scene = bpy.context.scene
    assert scene.get('room_id') == 'Courtyard43'
    assert scene.get('web_revision') == 'courtyard43-interior14', scene.get('web_revision')
    assert not scene.get('curtains15_applied'), 'interior15 has already been applied'

    reports = []
    ncols, nrows = 121, 65
    surface_count = ncols * nrows

    # UV0 uses metres on both axes. Use a square tile, with subdued encoded
    # sRGB variation. The old image's ~0.106 Blender sample is LINEAR (~92/255
    # sRGB), not 27/255 encoded. Preserve the grey brightness and avoid a
    # double gamma conversion. Texture is material information, not a photo.
    tex_w = tex_h = 512
    uu = np.arange(tex_w, dtype=np.float32)[None, :] / tex_w
    vv = np.arange(tex_h, dtype=np.float32)[:, None] / tex_h
    weave = .8*np.cos(2*math.pi*128*uu)+.5*np.cos(2*math.pi*128*vv)
    rgb = np.clip(92.0+weave,0,255).astype(np.uint8)
    rgb = np.repeat(rgb[:,:,None],3,axis=2)
    def chunk(k,data):
        return struct.pack('>I',len(data))+k+data+struct.pack('>I',zlib.crc32(k+data)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',tex_w,tex_h,8,2,0,0,0))
    data+=chunk(b'sRGB',b'\0')+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in rgb)))+chunk(b'IEND',b'')
    path=Path(__file__).resolve().parents[1]/'assets/architecture/textures/curtain-quiet-weave15.png'
    path.write_bytes(data)
    weave_image=bpy.data.images.load(str(path),check_existing=False)
    weave_image.colorspace_settings.name='sRGB'

    for side in ('Left', 'Right'):
        obj = bpy.data.objects['C43_Curtain_' + side]
        assert obj.type == 'MESH' and obj.data.shape_keys, obj.name
        obj.data = obj.data.copy()
        keys = obj.data.shape_keys.key_blocks
        assert 'Basis' in keys and 'Open' in keys
        assert len(keys['Basis'].data) == surface_count * 2, (obj.name, len(keys['Basis'].data))

        # Form small turned hems around the lower and outside edges. The two
        # cloth faces stay symmetric about their existing centre surface; the
        # hemline, jamb returns, and supported centreline remain fixed.
        # A lighter roll at the meeting edge preserves its 20 mm depth overlap.
        for key_name in ('Basis', 'Open'):
            block = keys[key_name]
            for i in range(surface_count):
                row, col = divmod(i, ncols)
                a, v = col / (ncols - 1), row / (nrows - 1)
                front = block.data[i].co.copy()
                back = block.data[i + surface_count].co.copy()
                centre = (front + back) * 0.5
                half = (front - back) * 0.5

                outside = (1.0 - a) if side == 'Left' else a
                meeting = a if side == 'Left' else (1.0 - a)
                lower_hem = _smooth((v - 0.965) / 0.035)
                outer_binding = _smooth((outside - 0.985) / 0.015)
                meeting_binding = _smooth((meeting - 0.975) / 0.025)
                # 3.4 mm body thickness grows to roughly 6-7 mm at sewn edges.
                # Keep the middle overlap conservative to avoid panel contact.
                roll = max(lower_hem, outer_binding) * 0.82 + meeting_binding * 0.14
                half *= 1.0 + roll
                block.data[i].co = centre + half
                block.data[i + surface_count].co = centre - half

                # Add a low-amplitude, drifting cloth trough to soften the
                # evenly repeated folds. Zero at top, hem and both side edges.
                # The same field is used in each shape so opening remains a
                # smooth morph instead of changing the fabric's identity.
                body = _smooth(v / 0.12) * _smooth((1.0 - v) / 0.12)
                body *= _smooth(a / 0.07) * _smooth((1.0 - a) / 0.07)
                amp = 0.0048 if key_name == 'Basis' else 0.0028
                phase = 2.0 * math.pi * (5.65 * a + 0.075 * math.sin(v * 4.4 + 0.3))
                drift = 0.0017 * math.sin(2.0 * math.pi * (2.35 * a - 0.22 * v) + 0.7)
                centre = (block.data[i].co + block.data[i + surface_count].co) * 0.5
                centre.y += body * (amp * math.sin(phase) + drift)
                offset = (block.data[i].co - block.data[i + surface_count].co) * 0.5
                block.data[i].co = centre + offset
                block.data[i + surface_count].co = centre - offset

        # Basis vertices are the evaluated starting state used by the exporter.
        for vertex, basis in zip(obj.data.vertices, keys['Basis'].data):
            vertex.co = basis.co
        obj.data.update()
        obj['curtains15'] = 'Sewn rolled hems and broad irregular drape; supported outline and overlap retained'

        # Remove the fine normal-map sparkle that reads as a metallic grid at
        # room distance. Keep its weave map at a low level, with a fully matte,
        # non-metallic response; keep the base fabric texture and color intact.
        mat = obj.data.materials[0].copy()
        mat.name = 'C43_Dry_Blackout15_' + side
        obj.data.materials[0] = mat
        bsdf = next(node for node in mat.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Metallic'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 1.0
        bsdf.inputs['Specular IOR Level'].default_value = 0.006
        bsdf.inputs['Sheen Weight'].default_value = 0.0
        bsdf.inputs['Emission Strength'].default_value = 0.0
        base_source = bsdf.inputs['Base Color'].links[0].from_node
        assert base_source.type == 'TEX_IMAGE' and base_source.image
        base_source.image = weave_image
        normal = next((node for node in mat.node_tree.nodes if node.type == 'NORMAL_MAP'), None)
        if normal:
            normal.inputs['Strength'].default_value = 0.009
        props = json.loads(mat.get('web_props', '{}'))
        props.update(roughness=1.0, metalness=0.0, sheen=0.0,
                     specularIntensity=0.006, envMapIntensity=0.025,
                     emissiveIntensity=0.0)
        mat['web_props'] = json.dumps(props)
        meta = json.loads(mat.get('web_userData', '{}'))
        meta.update(surfaceFinish='heavy matte blackout woven cloth with sewn hems',
                    blackoutCurtain=True, curtainSide=side.lower())
        mat['web_userData'] = json.dumps(meta)
        reports.append({'object': obj.name, 'material': mat.name,
                        'vertices': len(obj.data.vertices),
                        'roughness': 1.0, 'metalness': 0.0,
                        'normalStrength': 0.009})

    bpy.context.view_layer.update()
    scene['parent_web_revision'] = 'courtyard43-interior14'
    scene['web_revision'] = 'courtyard43-interior15'
    scene['curtains15_applied'] = True
    targets = ['C43_Curtain_Left', 'C43_Curtain_Right']
    return {'revision': scene['web_revision'], 'curtains': reports,
            'changedObjects': targets, 'targets': targets}
