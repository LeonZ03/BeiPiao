"""One-time pre-publication photo08 correction after actual browser inspection.

Reduce over-broad duvet mounds and turn the former bag's handles into a gathered
packaging neck. Run after refine-photo-fidelity on furniture07, props03, interior08.
The scene marker prevents accidental reapplication; no approved anchors move.
"""
from pathlib import Path
import ast,bpy,bmesh,numpy as np,math,json,hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene;kind=scene.get('component');full=scene.get('stage')=='interior' and kind not in ('architecture','furniture','props')
assert not scene.get('photo08_web_tuned')
assert scene.get('web_revision')=='courtyard43-interior08' if full else scene.get('component_revision') in ('courtyard43-furniture07','courtyard43-props03')
bpy.context.preferences.filepaths.save_version=0
bp=lambda p:Vector((p[0],-p[2],p[1]));web=lambda p:Vector((p[0],p[2],-p[1]));targets=set()
for file,names in [('refine-furnishings.py',{'digest','shader','material','assign','replace','solid','tube','lathe'}),('refine-photo-fidelity.py',{'deform','smooth'})]:
    p=ROOM/'scripts'/file;t=ast.parse(p.read_text(encoding='utf-8'))
    exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(p),'exec'))
bpy.context.view_layer.update();before={o.name:digest(o) for o in scene.objects}
def cloth(p):
    x,y,z=p;q=x+.62-.48*(z-2.04)-.13*math.sin(z*3.3);q2=z-2.17+.38*x+.045*math.sin(x*6)
    delta=-.047*math.exp(-(q/.12)**2-((z-2.1)/.66)**2)-.032*math.exp(-(q2/.095)**2-((x+.3)/.85)**2)
    for k,(cx,cz,slope,length) in enumerate([(-.8,1.7,.45,.5),(-.32,2.38,-.7,.42),(-1.1,2.4,.1,.36),(-.2,1.55,.8,.3),(.15,2.15,-.4,.35)]):
        a=x-cx;b=z-cz;line=b-slope*a-.016*math.sin(a*18+k)
        delta+=(.012+k%2*.003)*math.exp(-(line/(.015+k%3*.006))**2-(a/length)**4)
    return x,y+delta*smooth((y-.48)/.08),z
if full or kind=='furniture':
    for n in ['C43_FloralDuvet','C43_FloralDuvetSewnHem']:deform(bpy.data.objects[n],cloth)
def settle_duvet():
    # P04 is an unoccupied thin quilt, not a lofted comforter. Retain its
    # diagonal gathering while halving excess height above the supported top.
    for n in ['C43_FloralDuvet','C43_FloralDuvetSewnHem']:
        if n in bpy.data.objects:
            deform(bpy.data.objects[n],lambda p:(p.x,p.y-.45*max(0,p.y-.574),p.z))
if full or kind=='furniture':
    settle_duvet();scene['photo08_duvet_settled']=True
if full or kind=='props':
    def bagfield(p):
        t=max(0,min(1,(p.y-1.215)/.323));return 1.958+(p.x-1.958)*(1-.78*t**6),p.y+.064*t**4,p.z
    bag=bpy.data.objects['C43_Hanging_bag'];deform(bag,bagfield)
    navy=bag.data.materials[1]
    for k in range(2):
        pts=[(1.952+.010*math.cos(a),1.594+.012*math.sin(a),1.412+k*.004) for a in np.linspace(0,math.tau,33)]
        tube('C43_Bag_strap_'+str(k),pts,.003,navy)
    # Keep only the photograph's readable large colour blocks. Assigning a
    # diagonal printed patch by polygons creates visible stepped boundaries.
    # Wrinkled package sides; all geometry shares a support-preserving field.
    for o in scene.objects:
        if o.type=='MESH' and o.name.startswith('C43_Tissue_'):
            deform(o,lambda p:(p.x,p.y,p.z+.0018*math.sin((p.x-1.1)*167+(p.y-1.0125)*65)*smooth((p.y-1.0125)/.009)*(1-smooth((p.y-1.042)/.01))))
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==v for n,v in before.items() if n not in targets)
def orient_details():
    # The vertical-axis remapping of the new lathed details changes handedness.
    # Restore outward winding in source, not with DoubleSide in the viewer.
    for name in ['C43_Bag_visible_blue_round_item','C43_Round_hanging_item','C43_Headboard_mark_0','C43_Headboard_mark_1']:
        o=bpy.data.objects.get(name)
        if not o:continue
        bm=bmesh.new();bm.from_mesh(o.data)
        if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(o.data);bm.free();o.data.update()
orient_details()
scene['photo08_web_tuned']=True
if full:
    records=json.loads(scene['components'])
    for r in records:r['sha256']=hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest()
    scene['components']=json.dumps(records);output=ROOM/'assets/full-room/Courtyard43-interior.blend'
else:output=ROOM/f'assets/{kind}/Courtyard43-{kind}.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(output));result={'saved':str(output),'targets':sorted(targets)}
if full:
    p=ROOM/'scripts/export-interior.py';s={'__file__':str(p),'__name__':'export'}
    exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),s);result['export']=s['export_interior']()
