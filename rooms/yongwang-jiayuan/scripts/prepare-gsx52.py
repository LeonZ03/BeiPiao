"""Prepare the user-supplied GSX for the courtyard. Official Blender Lab MCP only.

GSX52_INPUT names the supplied source. Output is a self-contained room asset.
Original projection shaders are baked before the bike is placed in the room.
"""
from pathlib import Path
import hashlib
import json
import os

import bpy

bpy.context.preferences.filepaths.save_version = 0
ROOT = Path(__file__).resolve().parents[3]
ASSET = ROOT / 'rooms/yongwang-jiayuan/assets/motorcycle'
INPUT = Path(os.environ['GSX52_INPUT'])
PROGRESS = ROOT / 'analysis/gsx52-progress.txt'
ASSET.mkdir(parents=True, exist_ok=True)
(ASSET / 'textures').mkdir(exist_ok=True)


def progress(message):
    PROGRESS.write_text(message, encoding='utf8')


if os.environ.get('GSX52_STAGE', 'freeze') == 'freeze':
    scene = bpy.context.scene
    bpy.context.preferences.filepaths.save_version = 0
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    progress('Loading source datablocks')
    with bpy.data.libraries.load(str(INPUT), link=False) as (source, target):
        target.objects = [name for name in source.objects]
    objects = [obj for obj in target.objects if obj.type in {'MESH', 'CURVE'}]
    visible = [obj for obj in objects if not obj.hide_render and not obj.name.startswith('Tool_')]
    for obj in objects:
        for modifier in obj.modifiers:
            # Keep source voxel sizes: coarsening a 2 mm panel can erase it.
            if modifier.type == 'SUBSURF':
                modifier.levels = min(modifier.levels, 2)
                modifier.render_levels = modifier.levels
        if obj.type == 'CURVE':
            obj.data.bevel_resolution = min(obj.data.bevel_resolution, 2)
        scene.collection.objects.link(obj)
    progress('Evaluating source surfaces and assembly modifiers')
    bpy.context.view_layer.update()
    graph = bpy.context.evaluated_depsgraph_get()
    frozen = []
    source_triangles = 0
    for index, obj in enumerate(visible):
        evaluated = obj.evaluated_get(graph)
        mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=graph)
        mesh.calc_loop_triangles()
        source_triangles += len(mesh.loop_triangles)
        copy = bpy.data.objects.new(obj.name + '_courtyard', mesh)
        copy.matrix_world = obj.matrix_world.copy()
        frozen.append(copy)
        if index % 100 == 0:
            progress(f'Freezing {index}/{len(visible)} parts')
    for obj in list(bpy.data.objects):
        if obj not in frozen:
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in frozen:
        scene.collection.objects.link(obj)
        obj.select_set(False)
    bpy.context.view_layer.update()
    
    # Dense tyre tessellation and sub-pixel mechanical surfaces dominate this
    # distant asset. Retain body silhouette and live-assembly results first.
    progress('Reducing dense tyres and mechanical tessellation')
    for obj in frozen:
        obj.data.calc_loop_triangles()
        count = len(obj.data.loop_triangles)
        target_count = 16000 if obj.name.startswith('Tire_') else 24000
        if count > target_count * 1.15:
            bpy.context.view_layer.objects.active = obj
            modifier = obj.modifiers.new('Courtyard surface budget', 'DECIMATE')
            modifier.ratio = target_count / count
            modifier.use_collapse_triangulate = True
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    
    # One atlas preserves the source's projected livery, rim stripes and markings
    # without translating its large procedural shader graph into browser code.
    progress('Packing vehicle UV atlas')
    for obj in frozen:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = frozen[0]
    bpy.ops.object.join()
    bike = bpy.context.object
    bike.name = 'GSX52_BakedVehicle'
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    scene['gsx52_input'] = json.dumps(dict(sourceSha256=hashlib.sha256(INPUT.read_bytes()).hexdigest(), sourceFile=INPUT.name, sourceParts=len(visible), evaluatedTriangles=source_triangles, sourceRemeshPreserved=True))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'analysis/gsx52-frozen.blend'))
    progress('Frozen geometry saved')
    result = json.loads(scene['gsx52_input'])
else:
    scene = bpy.context.scene
    bike = bpy.data.objects['GSX52_BakedVehicle']
    bpy.context.view_layer.objects.active = bike
    bike.select_set(True)
    # Final geometry budget before UV layout and baking.
    bike.data.calc_loop_triangles()
    if len(bike.data.loop_triangles) > 320000:
        modifier = bike.modifiers.new('Courtyard final triangle budget', 'DECIMATE')
        modifier.ratio = 320000 / len(bike.data.loop_triangles)
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=1.151917, island_margin=.0015, area_weight=.5)
    bpy.ops.object.mode_set(mode='OBJECT')
    bike.data.uv_layers.active.name = 'UVMap'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.render.bake.margin = 3
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.use_pass_color = True
    materials = {material for material in bike.data.materials if material}
    atlas = bpy.data.images.new('GSX52_albedo', width=2048, height=2048, alpha=False)
    atlas.colorspace_settings.name = 'sRGB'
    for material in materials:
        node = material.node_tree.nodes.new('ShaderNodeTexImage')
        node.name = 'GSX52_BakeTarget'
        node.image = atlas
        material.node_tree.nodes.active = node
        bsdf = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        output = next(node for node in material.node_tree.nodes if node.type == 'OUTPUT_MATERIAL' and node.is_active_output)
        emission = material.node_tree.nodes.new('ShaderNodeEmission')
        socket = bsdf.inputs['Base Color']
        if socket.is_linked:
            material.node_tree.links.new(socket.links[0].from_socket, emission.inputs['Color'])
        else:
            emission.inputs['Color'].default_value = socket.default_value
        material.node_tree.links.new(emission.outputs[0], output.inputs['Surface'])
    progress('Baking projected colours and livery')
    bpy.ops.object.bake(type='EMIT')
    atlas.filepath_raw = str(ASSET / 'textures/gsx52-albedo.png')
    atlas.file_format = 'PNG'
    atlas.save()
    
    parameters = {}
    saved_links = []
    for material in materials:
        nodes = material.node_tree.nodes
        bsdf = next(node for node in nodes if node.type == 'BSDF_PRINCIPLED')
        output = next(node for node in nodes if node.type == 'OUTPUT_MATERIAL' and node.is_active_output)
        parameters[material.name] = dict(
            roughness=float(bsdf.inputs['Roughness'].default_value),
            metalness=float(bsdf.inputs['Metallic'].default_value),
            transmission=float(bsdf.inputs['Transmission Weight'].default_value),
            ior=float(bsdf.inputs['IOR'].default_value))
        saved_links.append((material, bsdf, output))
    
    progress('Baking livery metalness masks')
    metal = bpy.data.images.new('GSX52_metalness', width=2048, height=2048, alpha=False)
    metal.colorspace_settings.name = 'Non-Color'
    for material, bsdf, output in saved_links:
        nodes, links = material.node_tree.nodes, material.node_tree.links
        emission = nodes.new('ShaderNodeEmission')
        socket = bsdf.inputs['Metallic']
        if socket.is_linked:
            links.new(socket.links[0].from_socket, emission.inputs['Color'])
        else:
            value = socket.default_value
            emission.inputs['Color'].default_value = (value, value, value, 1)
        links.new(emission.outputs[0], output.inputs['Surface'])
        nodes['GSX52_BakeTarget'].image = metal
    bpy.ops.object.bake(type='EMIT')
    metal.filepath_raw = str(ASSET / 'textures/gsx52-metalness.png')
    metal.file_format = 'PNG'
    metal.save()
    
    for material, bsdf, output in saved_links:
        nodes = material.node_tree.nodes
        for node in list(nodes):
            if node not in {bsdf, output}:
                nodes.remove(node)
        links = material.node_tree.links
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        bsdf.inputs['Base Color'].default_value = (1, 1, 1, 1)
        bsdf.inputs['Metallic'].default_value = 1
        bsdf.inputs['Emission Color'].default_value = (0, 0, 0, 1)
        bsdf.inputs['Emission Strength'].default_value = 0
        bsdf.inputs['Transmission Weight'].default_value = 0
        for name, image, socket in [('Albedo', atlas, 'Base Color'), ('Metalness', metal, 'Metallic')]:
            node = nodes.new('ShaderNodeTexImage')
            node.name = name
            node.image = image
            links.new(node.outputs['Color'], bsdf.inputs[socket])
        material['gsx52_parameters'] = json.dumps(parameters[material.name])
    
    uv0 = bike.data.uv_layers['UVMap']
    uv1 = bike.data.uv_layers.new(name='UV1')
    for source, target in zip(uv0.data, uv1.data):
        target.uv = source.uv
    bike.data.uv_layers.active = bike.data.uv_layers['UVMap']
    for image in list(bpy.data.images):
        if image not in {atlas, metal}:
            bpy.data.images.remove(image)
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    bike.data.calc_loop_triangles()
    metadata = dict(**json.loads(scene['gsx52_input']), triangles=len(bike.data.loop_triangles), materials=len(materials), atlasSize=2048, revision='gsx52')
    scene['gsx52'] = json.dumps(metadata)
    for image in [atlas, metal]:
        image.filepath = '//textures/' + Path(image.filepath_raw).name
    progress('Saving self-contained courtyard asset')
    bpy.ops.wm.save_as_mainfile(filepath=str(ASSET / 'GSX250R-courtyard.blend'))
    (ASSET / 'gsx52-source.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf8')
    progress('Prepared')
    result = metadata
