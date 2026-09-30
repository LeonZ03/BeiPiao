"""Final browser composition correction for interior10, official MCP only."""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior10' and s.get('winter_browser_calibrated')
assert not s.get('winter_gap_final')
bpy.context.preferences.filepaths.save_version=0
col=bpy.data.collections['C43_ZWinter']
for o in col.objects:
    if o.type!='MESH':continue
    shift=3 if any(k in o.name for k in ['RightBlock','RightDetails','FarTower']) else 4.5 if 'YellowGap' in o.name else 0
    if shift:
        for v in o.data.vertices:v.co.x+=shift
bpy.context.view_layer.update()
p=ROOM/'assets/winter-exterior/Courtyard43-winter-exterior.blend'
bpy.data.libraries.write(str(p),{col},path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(s['components'])
for c in components:
    if c['component']=='winter-exterior':c['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
s['components']=json.dumps(components);s['winter_gap_final']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'winter_final'}
exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope)
result=scope['export_interior']()
