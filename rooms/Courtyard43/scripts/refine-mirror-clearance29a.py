"""mirror29 -> mirror29a. Restore the source mirror's 0.4 mm face clearance.

Official Blender Lab MCP only. The smaller 0.04 mm offset flickered against
the opaque glass edge in oblique web views with the small navigation near plane.
"""
from pathlib import Path
import bpy, json
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-mirror29'
o=bpy.data.objects['C43_WardrobeFarMirror_Reflection']
assert abs(o.location.x-.03304)<1e-6
o.location.x=.0334
s['parent_web_revision']='courtyard43-mirror29';s['web_revision']='courtyard43-mirror29a'
s['mirror29a']=json.dumps({'reflectionClearanceM':.0004,'reason':'same as Yongwang source separation; oblique depth precision'})
bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')}
exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':s['web_revision'],'clearanceM':.0004}
