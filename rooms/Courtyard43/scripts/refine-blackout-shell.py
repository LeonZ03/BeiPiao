"""Official MCP inspection and draft11 side-return shell correction.
The corrected authoring generator already preserves shell winding.
"""
from pathlib import Path
import bpy,json,math,hashlib,bmesh
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior11'
assert not s.get('blackout_shell_checked')
bpy.context.preferences.filepaths.save_version=0
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
rows=[]
for side in ['Left','Right']:
 o=bpy.data.objects['C43_Curtain_'+side];n=121*65;width=.872 if side=='Left' else 1.196;height=2.399-(.0505 if side=='Left' else 1.018)
 for key in o.data.shape_keys.key_blocks:
  old=[v.co.copy() for v in key.data]
  for i,v in enumerate(key.data):
   j,k=divmod(i%n,121);a=k/120;t=j/64
   hem=1+.8*(1-smooth(min(a,1-a)*width/.018))+1.3*(1-smooth(min(t*height/.045,(1-t)*height/.03)))
   half=.00085*hem*(1+.7*smooth(t/.08));mid=(old[i].y+old[(i+n)%(2*n)].y)/2
   v.co.y=mid+(-half if i<n else half)
 for v,k in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data):v.co=k.co
 bm=bmesh.new();bm.from_mesh(o.data);row={'name':o.name,'volume':bm.calc_volume(signed=True),'nonManifold':sum(not e.is_manifold for e in bm.edges)};bm.free();assert row['volume']>0 and row['nonManifold']==0;rows.append(row)
objects={bpy.data.objects['C43_Curtain_'+side+suffix] for side in ['Left','Right'] for suffix in ['', '_Rings','_Pivot']}
p=ROOM/'assets/blackout-curtains/Courtyard43-blackout-curtains.blend';bpy.data.libraries.write(str(p),objects,path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(s['components'])
for c in components:
 if c['component']=='blackout-curtains':c['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
s['components']=json.dumps(components);s['blackout_shell_checked']=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';d={'__file__':str(p),'__name__':'blackout_export'};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),d)
result={'export':d['export_interior'](),'shells':rows}
