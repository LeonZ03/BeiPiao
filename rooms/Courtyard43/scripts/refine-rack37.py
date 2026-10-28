"""balcony36 -> rack37: one pole, scissor planes along it, direct ceiling eyes.

Execute through official Blender Lab MCP only. User-confirmed correction:
rotate the existing scissor supports 90 degrees, remove the upper rectangles,
second pole and end crossbars. Cabinet geometry and the retained pole stay fixed.
Small mounting eyes/studs are restrained connection estimates, not measured parts.
"""
from pathlib import Path
import ast,bpy,bmesh,json,hashlib,math
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-balcony36'
bpy.context.preferences.filepaths.save_version=0
def definitions(path,names):
    tree=ast.parse(path.read_text('utf8'))
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(body)==len(names)
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),globals())
definitions(ROOM/'scripts/refine-furnishings.py',{'digest'})
definitions(ROOM/'scripts/refine-balcony35.py',{'tag','finish','mesh','tube'})
rack=[o for o in s.objects if o.name.startswith('C43_B35_Rack')]
assert len(rack)==37, 'Unexpected parent rack; inspect before editing'
targets={o.name for o in rack}
before={o.name:digest(o) for o in s.objects if o.name not in targets}
collection=bpy.data.collections['C43_Balcony35'];created=[]
bp=lambda p:Vector((p[0],-p[2],p[1]))
web=lambda p:Vector((p[0],p[2],-p[1]))
steel=bpy.data.materials['C43_B35_OldDryingRail']
wire=bpy.data.materials['C43_B35_HangerWire']
centres=[-1.48,1.68]
removed=[]
for o in rack:
    name=o.name.removeprefix('C43_B35_')
    if name.startswith(('RackCeilingPlate','RackParallelRail','RackEndCrossbar','RackTopClevis')) or name.startswith(('RackEndPivot0_0_','RackEndPivot1_0_')):
        removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
    assert name.startswith(('RackScissor','RackCentrePivot','RackEndPivot','RackLowerCollar')),name
    side=int(next(c for c in name if c.isdigit()));cx=centres[side]
    # R_y(90 degrees) around each former support centre, then align with the
    # retained pole at Z=-0.76. Rigid rotation preserves thickness and bevels.
    o.data=o.data.copy();inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        p=web(o.matrix_world@v.co)
        q=Vector((cx+p.z+.63,p.y,-.76-(p.x-cx)))
        v.co=inv@bp(q)
    o.data.update()
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()

# Four small round eyes attach straight into the ceiling. No spanning mounting
# plate remains. The eye is offset behind the link layers and joined by a pin.
for side,cx in enumerate(centres):
    for end,dx in enumerate([-.13,.13]):
        x=cx+dx;y=2.718;z=-.772;n=24
        vs=[]
        for zz,r in [(z-.0015,.0115),(z-.0015,.0055),(z+.0015,.0055),(z+.0015,.0115)]:
            vs.extend([(x+r*math.cos(j*math.tau/n),y+r*math.sin(j*math.tau/n),zz) for j in range(n)])
        fs=[(a*n+j,a*n+(j+1)%n,((a+1)%4)*n+(j+1)%n,((a+1)%4)*n+j) for a in range(4) for j in range(n)]
        mesh('RackCeilingEye%d_%d'%(side,end),vs,fs,steel,smooth=True)
        tube('RackCeilingStud%d_%d'%(side,end),[(x,2.728,z),(x,2.758,z)],.0045,steel,16)
        tube('RackEndPivot%d_0_%d'%(side,end),[(x,y,-.776),(x,y,-.744)],.0045,wire,12)
for name in created:
    o=bpy.data.objects[name]
    o['web_tags']=json.dumps({'ceilings':True})
    o['evidence']='User-confirmed single pole and 90 degree scissor orientation; mounting details estimated'

bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items()),'Non-rack object changed'
for o in s.objects:
    if o.name.startswith('C43_B35_Rack'):
        bm=bmesh.new();bm.from_mesh(o.data)
        assert all(e.is_manifold for e in bm.edges),o.name
        bm.free()
s['parent_web_revision']='courtyard43-balcony36';s['web_revision']='courtyard43-rack37'
s['rack37']=json.dumps({'parent':'courtyard43-balcony36','unchangedObjects':len(before),'removed':removed,'poleCount':1,'scissorPlane':'XY, parallel to pole','ceiling':'direct round eyes and studs, no rectangular plate','simulation':'none'})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')}
exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns)
report=ns['export_interior']()
result={**report,'unchangedObjects':len(before),'removedObjects':len(removed)}
