"""Official MCP only: extract the already saved kit into its standalone scene.
Open the complete source in a fresh process. Never save this pruned scene over it.
"""
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
assert scene.get('web_revision') in ('courtyard43-interior13','courtyard43-interior14') and scene.get('desktop13_finish')
assert scene.get('web_revision')!='courtyard43-interior14' or scene.get('desktop14_notes')
kit=bpy.data.collections['C43_DevelopmentKit_desktop13'];keep=set(kit.objects)
for obj in list(bpy.data.objects):
    if obj not in keep:bpy.data.objects.remove(obj,do_unlink=True)
for coll in list(bpy.data.collections):
    if coll!=kit:bpy.data.collections.remove(coll)
scene['component']='development-kit';scene['component_revision']=scene.get('desktop_kit_revision','desktop13')
scene.name='Courtyard43 development kit'
for obj in keep:obj.select_set(True)
bpy.context.view_layer.objects.active=next(iter(keep))
bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
bpy.context.preferences.filepaths.save_version=0
target=ROOM/'assets/development-kit/Courtyard43-development-kit.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target),check_existing=False)
result={'source':str(target),'objects':len(keep)}
