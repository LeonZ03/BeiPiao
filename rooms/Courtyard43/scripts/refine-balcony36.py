"""balcony35 -> balcony36: taller end cabinets and ceiling scissor drying rack.

Official Blender Lab MCP only. User correction supersedes the wall-mounted
rail inference. V01 11.3s shows the folding links; small dimensions are estimates.
No animation or per-frame simulation is needed for the fixed resting position.
"""
from pathlib import Path
import ast, bpy, bmesh, hashlib, json, math
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-balcony35'
bpy.context.preferences.filepaths.save_version=0

# Reuse definitions, never execute the previous stage against a newer source.
def load_functions(path,names):
    tree=ast.parse(path.read_text('utf8'))
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(body)==len(names)
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),globals())
load_functions(ROOM/'scripts/refine-furnishings.py',{'digest'})
load_functions(ROOM/'scripts/refine-balcony35.py',{'tag','finish','mesh','box','tube','cabinet'})
prefixes=('C43_B35_LeftCabinet','C43_B35_RightCabinet','C43_B35_DryingRail','C43_B35_WireHanger')
targets={o.name for o in s.objects if o.name.startswith(prefixes)}
before={o.name:digest(o) for o in s.objects if o.name not in targets}
bp=lambda p:Vector((p[0],-p[2],p[1]))
collection=bpy.data.collections['C43_Balcony35'];created=[]
paint=bpy.data.materials['C43_B35_OldIvoryLaminate']
edge=bpy.data.materials['C43_B35_FadedEdgeBand']
wood=bpy.data.materials['C43_B35_ExposedParticleBoard']
steel=bpy.data.materials['C43_B35_OldDryingRail']
wire=bpy.data.materials['C43_B35_HangerWire']
left,right=-2.025,2.225
for name in targets:
    if 'WireHanger' not in name:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)

# Raise the casework by 18 cm; retain board thickness, bevels and floor contact.
# Rebuilding the carcasses avoids stretching the old bevels and pulls.
cabinet('LeftCabinet',left+.19,.36,.78,1.02,1)
# The existing return-window sill projects 90 mm beyond the former cabinet
# back. Fit the case just inboard of that real ledge rather than cutting through it.
cabinet('RightCabinet',right-.28,.36,.57,1.06,-1)

def link(name,p,q,xshift):
    p=Vector(p);q=Vector(q);p.x+=xshift;q.x+=xshift
    d=(q-p).normalized();u=Vector((1,0,0));v=d.cross(u).normalized()
    vs=[a+u*(sx*.002)+v*(sv*.009) for a in [p,q] for sx,sv in [(-1,-1),(-1,1),(1,-1),(1,1)]]
    return mesh(name,vs,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],steel,.00065)

rack=[]
for side,x in enumerate([-1.48,1.68]):
    rack.append(box('RackCeilingPlate%d'%side,(x,2.742,-.63),(.08,.016,.37),steel,.002))
    # Two stacked X stages, with separated metal layers and physical pivot pins.
    for tier,(top,bottom) in enumerate([(2.718,2.478),(2.478,2.238)]):
        for cross,(za,zb) in enumerate([(-.76,-.50),(-.50,-.76)]):
            rack.append(link('RackScissor%d_%d_%d'%(side,tier,cross),(x,top,za),(x,bottom,zb),(-.003 if cross==0 else .003)))
        yy=(top+bottom)/2
        rack.append(tube('RackCentrePivot%d_%d'%(side,tier),[(x-.008,yy,-.63),(x+.008,yy,-.63)],.0045,wire,12))
    for j,y in enumerate([2.718,2.478,2.238]):
        for k,z in enumerate([-.76,-.50]):
            rack.append(tube('RackEndPivot%d_%d_%d'%(side,j,k),[(x-.008,y,z),(x+.008,y,z)],.0045,wire,12))
    for k,z in enumerate([-.76,-.50]):
        rack.append(box('RackTopClevis%d_%d'%(side,k),(x,2.725,z),(.026,.025,.025),steel,.001))
        rack.append(box('RackLowerCollar%d_%d'%(side,k),(x,2.235,z),(.027,.026,.027),steel,.001))

for j,z in enumerate([-.76,-.50]):
    rack.append(tube('DryingRail' if j==0 else 'RackParallelRail',[(-1.62,2.235,z),(1.82,2.235,z)],.010,steel,20))
for j,x in enumerate([-1.62,1.82]):
    rack.append(tube('RackEndCrossbar%d'%j,[(x,2.235,-.77),(x,2.235,-.49)],.010,steel,16))
for o in rack:
    o['web_tags']=json.dumps({'ceilings':True})
    o['evidence']='V01 11.3s and user ceiling-mounted scissor correction; dimensions estimated'
for o in s.objects:
    if o.name.startswith('C43_B35_WireHanger'):o['web_tags']=json.dumps({'ceilings':True})

bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items()),'Unrelated object changed'
s['parent_web_revision']='courtyard43-balcony35';s['web_revision']='courtyard43-balcony36'
s['balcony36']=json.dumps({'parent':'courtyard43-balcony35','unchangedObjects':len(before),'cabinetHeightDeltaM':.18,'cabinetHeightsM':[1.02,1.06],'rightCabinetInsetM':.09,'rack':'ceiling plates, two two-stage scissor supports, two rails; static pose','dimensions':'photo estimates'})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')}
exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns)
result={**ns['export_interior'](),'unchangedObjects':len(before),'newObjects':len(set(created))}
