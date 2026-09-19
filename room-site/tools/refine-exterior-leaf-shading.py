"""exterior31c -> exterior31e. Diffuse foliage budget, Blender Lab MCP only.

Leaves have baked canopy occlusion and thin backlighting in the web shader.
Their broad diffuse response does not need the room's costly PMREM specular
integration on every overlapping leaf fragment. Geometry and wind stay intact.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='exterior31c'
assert bpy.context.scene.get('web_revision')=='exterior31c'
old=data['nodes'][644]['material']
mid=material('Summer poplar · diffuse leaf with thin backlight',old,rough=.88,metadata={'leafSurface':True,'diffuseFoliage':True})
data['materials'][mid]['type']='MeshLambertMaterial'
bs=next(n for n in mats[mid].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Specular IOR Level'].default_value=0
for nid in (644,649,654):
    set_material(nid,mid)
    proto=bpy.data.objects.get('Instance prototype '+str(nid))
    proto.data.materials.clear();proto.data.materials.append(mats[mid])
    proto.material_slots[0].link='OBJECT';proto.material_slots[0].material=mats[mid]
details=copy.deepcopy(before['statistics']['exteriorRefinement']);details['foliageLighting']='diffuse with bounded backlight, no per-fragment PMREM'
result=save('exterior31e',details)
