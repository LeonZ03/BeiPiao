"""exterior32 -> sunlight33. Thin bay glazing without point-light fireflies.

Run through Blender Lab MCP. A sky sun is composited by the browser using the
unchanged directional light; it is not a nearby luminous ball in this model.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='exterior32'
assert bpy.context.scene.get('web_revision')=='exterior32'
glass=material('Bay window · restrained clear glazing',226,rough=.24,textures={},specularIntensity=.06,depthWrite=False,metadata={'thinWindowGlazing':True,'revision':'sunlight33'})
data['materials'][glass]['type']='MeshPhysicalMaterial'
# Match the runtime specular attenuation in the editable Blender material.
bs=next(n for n in mats[glass].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Specular IOR Level'].default_value=.5*.06
bs.inputs['Alpha'].default_value=data['materials'][glass]['props']['opacity']
for nid in (166,172,178):set_material(nid,glass)
assert changed=={166,172,178}
details=copy.deepcopy(before['statistics']['exteriorRefinement'])
details['bayGlazing']='restrained specular; translucent panes do not occlude distant sky depth'
result=save('sunlight33',details)
