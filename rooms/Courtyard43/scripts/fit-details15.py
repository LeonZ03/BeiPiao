"""Official MCP finishing check: outward winding and bounded water tessellation."""
import bpy,bmesh,ast,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior15' and not s.get('details15_fitted')
bp=lambda p:Vector((p[0],-p[2],p[1]));targets=set()
p=ROOM/'scripts/refine-furnishings.py';tree=ast.parse(p.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'replace','lathe'}],type_ignores=[]),str(p),'exec'))
o=bpy.data.objects['C43_Bottle_water'];height=float(o['fillHeightM']);m=o.data.materials[0]
profile=[(0,.002),(.044,.002),(.051,.010)]
for h in np.linspace(.020,height,42):
    r=.0535-.0018*(.5+.5*math.cos(h*math.tau/.020))-.0016
    profile.append((r,float(h)))
profile += [(profile[-1][0]-.001,height+.0002),(0,height+.0002)]
o=lathe(o.name,(.56,1.0125,.215),profile,m,64);o['fillFraction']=.75;o['fillHeightM']=height
for name in ['C43_BucketHat15','C43_Bag_visible_blue_round_item','C43_Desk_power_cable','C43_Power15_adapter_output','C43_Power15_ac_strain','C43_Power15_adapter_ac','C43_Power15_adapter_dc']:
    o=bpy.data.objects[name];o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()
s['details15_fitted']=True
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'waterVertices':len(bpy.data.objects['C43_Bottle_water'].data.vertices),'fitted':True}
