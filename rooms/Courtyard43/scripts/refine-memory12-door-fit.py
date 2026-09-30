"""Official MCP only: finish the interior12 leaf/jamb rotational clearance.

Keep the approved hinge and doorway. Retain a 30 mm leaf, with its hinge edge
inside the swing clearance envelope; this is a fit correction, not a layout edit.
"""
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[3]
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior12'
o=bpy.data.objects['C43_Door_Leaf']
assert not o.get('memory12_swing_fit')
o.data=o.data.copy(); inv=o.matrix_world.inverted()
for v in o.data.vertices:
    p=o.matrix_world@v.co
    p.x=1.066+(p.x-1.066)/.828*.823
    z=-p.y
    p.y=-(2.835+(z-2.825)*.75)
    v.co=inv@p
o['memory12_swing_fit']='30 mm leaf; original hinge retained; full swing cleared'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend'))
p=ROOT/'rooms/Courtyard43/scripts/export-interior.py'
d={'__file__':str(p),'__name__':'memory_export'}
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),d)
result=d['export_interior']()
