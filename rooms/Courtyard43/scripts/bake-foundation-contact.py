"""Bake local static occlusion into UV1 via official Blender Lab MCP.

Small, neutral accessibility maps (not albedo shadows or direct light). Moving
doors/curtains are excluded; their live shadows remain the viewer's job.
Executed only by assemble-interior.py for interior02.
"""
from pathlib import Path
import json
import bpy

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'rooms/Courtyard43/assets/full-room/textures'
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
assert scene.get('web_revision') == 'courtyard43-interior02'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.bake.margin = 8
scene.render.bake.use_selected_to_active = False
hidden = []
for obj in scene.objects:
    p = obj
    while p:
        if p.get('c43_interaction'):
            hidden.append((obj, obj.hide_render))
            obj.hide_render = True
            break
        p = p.parent

names = ['C43_Floor_RedBrown_Boards', 'C43_Wall_Left', 'C43_Wall_Right',
         'C43_Wall_Balcony_Pier_Left', 'C43_Wall_Entry_Left', 'C43_Wall_Entry_Right']
report = []
for name in names:
    obj = bpy.data.objects[name]
    assert obj.type == 'MESH' and len(obj.data.materials) == 1
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    assert len(obj.data.uv_layers) == 1, 'Do not overwrite material UV1'
    uv = obj.data.uv_layers.new(name='UV1')
    obj.data.uv_layers.active = uv
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=.015)
    bpy.ops.object.mode_set(mode='OBJECT')
    mat = obj.data.materials[0].copy()
    mat.name = name + '_contact_material'
    obj.data.materials[0] = mat
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
    original = output.inputs['Surface'].links[0].from_socket
    ao = nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = .55
    ao.samples = 32
    emit = nodes.new('ShaderNodeEmission')
    links.new(ao.outputs['Color'], emit.inputs['Color'])
    links.new(emit.outputs[0], output.inputs['Surface'])
    size = 1024 if 'Floor' in name else 512
    image = bpy.data.images.new(name + '_contact', size, size, alpha=False)
    image.colorspace_settings.name = 'Non-Color'
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = image
    tex['web_map'] = 'aoMap'
    tex.extension = 'EXTEND'
    coords = nodes.new('ShaderNodeUVMap')
    coords.uv_map = 'UV1'
    links.new(coords.outputs['UV'], tex.inputs['Vector'])
    for node in nodes:
        node.select = False
    tex.select = True
    nodes.active = tex
    bpy.ops.object.bake(type='EMIT', uv_layer='UV1')
    links.new(original, output.inputs['Surface'])
    nodes.remove(emit)
    nodes.remove(ao)
    image.filepath_raw = str(OUT / (name + '-contact.png'))
    image.file_format = 'PNG'
    image.save()
    props = json.loads(mat.get('web_props', '{}'))
    props['aoMapIntensity'] = .65
    mat['web_props'] = json.dumps(props)
    obj.data.uv_layers.active_index = 0
    obj.data.uv_layers[0].active_render = True
    report.append(dict(object=name, size=size, aoRadius=.55))
for obj, prior in hidden:
    obj.hide_render = prior
result = dict(baked=report, movingOccludersExcluded=True)
