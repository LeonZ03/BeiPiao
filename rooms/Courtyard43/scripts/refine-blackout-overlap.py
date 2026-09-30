"""Official MCP: fit blackout overlap to cap and separate moving centre hems.
Input: saved interior11 after refine-blackout-shell.py. Idempotence guarded.
"""
from pathlib import Path
import bpy,json,hashlib
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior11' and s.get('blackout_shell_checked')
assert not s.get('blackout_overlap_checked')
bpy.context.preferences.filepaths.save_version=0
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def depth(a,side):
 return (-.008 if side=='Left' else .008)*smooth(((a if side=='Left' else 1-a)-.80)/.12)
for side in ['Left','Right']:
 o=bpy.data.objects['C43_Curtain_'+side];n=121*65
 for key in o.data.shape_keys.key_blocks:
  for i,v in enumerate(key.data):
   a=(i%n)%121/120
   if key.name=='Basis':v.co.x+=(-.025*a if side=='Left' else .021*(1-a))
   v.co.y+=depth(a,side)
 for v,k in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data):v.co=k.co
 o['blackout11']='Opaque thick matte cloth; 30mm jamb coverage, 20mm central overlap with separated hems'
 rings=bpy.data.objects[o.name+'_Rings']
 for key in rings.data.shape_keys.key_blocks:
  for r in range(11):
   a=.016+r*.0968
   for v in list(key.data)[r*160:(r+1)*160]:
    if key.name=='Basis':v.co.x+=(-.025*a if side=='Left' else .021*(1-a))
    v.co.y+=depth(a,side)
 for v,k in zip(rings.data.vertices,rings.data.shape_keys.key_blocks[0].data):v.co=k.co
bpy.context.view_layer.update()
objects={bpy.data.objects['C43_Curtain_'+side+suffix] for side in ['Left','Right'] for suffix in ['', '_Rings','_Pivot']}
p=ROOM/'assets/blackout-curtains/Courtyard43-blackout-curtains.blend';bpy.data.libraries.write(str(p),objects,path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(s['components'])
for c in components:
 if c['component']=='blackout-curtains':c['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
s['components']=json.dumps(components);s['blackout_overlap_checked']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';d={'__file__':str(p),'__name__':'blackout_export'};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),d)
result={'export':d['export_interior'](),'clearance':'20 mm centre overlap with separated hems'}
