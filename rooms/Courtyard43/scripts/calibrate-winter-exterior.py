"""Pre-release interior10 calibration after four-view browser inspection.

Run through official Blender Lab MCP only; does not move approved room geometry.
"""
from pathlib import Path
import bpy, json, hashlib
ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'; scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior10'
assert not scene.get('winter_browser_calibrated')
bpy.context.preferences.filepaths.save_version=0
# Keep the centre-right sky gap visible; far tower belongs behind the right slab.
for o in bpy.data.collections['C43_ZWinter'].objects:
    if 'FarTower' in o.name:
        for v in o.data.vertices: v.co.x+=5.0
# Clear glazing should retain restrained reflection without opaque grey veiling.
m=bpy.data.materials['C43_Clear_window_glass']
bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Alpha'].default_value=.045
bs.inputs['Roughness'].default_value=.22
p=json.loads(m.get('web_props','{}'));p.update(opacity=.045,roughness=.22,specularIntensity=.12,envMapIntensity=.2)
m['web_props']=json.dumps(p)
m=bpy.data.materials['C43_ZWinter_Settled_Snow']
bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Emission Strength'].default_value=.50
bpy.context.view_layer.update()
component=ROOM/'assets/winter-exterior/Courtyard43-winter-exterior.blend'
bpy.data.libraries.write(str(component),{bpy.data.collections['C43_ZWinter']},path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(scene['components'])
for item in components:
    if item['component']=='winter-exterior':item['sha256']=hashlib.sha256(component.read_bytes()).hexdigest()
scene['components']=json.dumps(components);scene['winter_browser_calibrated']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'winter_calibration'}
exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope)
result=scope['export_interior']()
