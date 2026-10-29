"""rack37 -> balcony38: larger cases, lower single rail, perpendicular hangers.

Run via official Blender Lab MCP. Dimensions are proportion estimates following
the user's correction. Preserve rail section, scissor link lengths and ceiling
connections; do not stretch metal links or the casework bevels.
"""
from pathlib import Path
import ast,bpy,bmesh,json,math,hashlib
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-rack37'
bpy.context.preferences.filepaths.save_version=0

def definitions(path,names):
    tree=ast.parse(path.read_text('utf8'))
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert len(body)==len(names)
    exec(compile(ast.Module(body=body,type_ignores=[]),str(path),'exec'),globals())

definitions(ROOM/'scripts/refine-furnishings.py',{'digest'})
definitions(ROOM/'scripts/refine-balcony35.py',{'tag','finish','mesh','box','tube','cabinet'})
prefixes=('C43_B35_LeftCabinet','C43_B35_RightCabinet','C43_B35_Rack','C43_B35_DryingRail','C43_B35_WireHanger','C43_B35_OldCurtain')
targets={o.name for o in s.objects if o.name.startswith(prefixes)}
before={o.name:digest(o) for o in s.objects if o.name not in targets}
collection=bpy.data.collections['C43_Balcony35'];created=[]
bp=lambda p:Vector((p[0],-p[2],p[1]))
web=lambda p:Vector((p[0],p[2],-p[1]))
paint,edge,wood=[bpy.data.materials['C43_B35_'+n] for n in ['OldIvoryLaminate','FadedEdgeBand','ExposedParticleBoard']]
for name in targets:
    if 'Cabinet' in name:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
cabinet('LeftCabinet',-1.81,.41,.82,1.16,1)
cabinet('RightCabinet',1.92,.41,.61,1.20,-1)
for name in created:
    o=bpy.data.objects[name]
    if 'LeftCabinet' in name:o.location.y-=.035  # keep clearance behind the old cloth

def transform(o,fn):
    o.data=o.data.copy();inv=o.matrix_world.inverted()
    for v in o.data.vertices:v.co=inv@bp(fn(web(o.matrix_world@v.co)))
    o.data.update()

# Extend both X stages through rigid rotations. Link lengths stay unchanged;
# the smaller horizontal spread follows the increased vertical separation.
half=math.sqrt(.26**2+.24**2-.31**2)/2
for o in list(s.objects):
    n=o.name.removeprefix('C43_B35_')
    if not n.startswith('Rack'):continue
    side=int(next(c for c in n if c.isdigit()));cx=[-1.48,1.68][side]
    if n.startswith('RackScissor'):
        _,tier,cross=n.removeprefix('RackScissor').split('_');tier=int(tier);cross=int(cross)
        sign=1 if cross==0 else -1;z=-.757 if cross==0 else -.763
        a=Vector((cx-sign*.13,2.718-tier*.24,z));b=Vector((cx+sign*.13,2.478-tier*.24,z))
        c=Vector((cx-sign*half,2.718-tier*.31,z));d=Vector((cx+sign*half,2.408-tier*.31,z))
        rot=(b-a).rotation_difference(d-c)
        transform(o,lambda p:(c+d)/2+rot@(p-(a+b)/2))
    else:
        p=web(o.matrix_world@sum((v.co for v in o.data.vertices),Vector())/len(o.data.vertices))
        if n.startswith('RackCentrePivot'):
            tier=int(n[-1]);delta=Vector((0,2.563-tier*.31-p.y,0))
        else:
            end=int(n[-1]);sign=-1 if end==0 else 1
            delta=Vector((sign*(half-.13),0,0))
            if n.startswith('RackEndPivot'):
                tier=int(n.split('_')[-2]);delta.y=-tier*.07
            elif n.startswith('RackLowerCollar'):delta.y=-.14
        transform(o,lambda p:p+delta)

rail=bpy.data.objects['C43_B35_DryingRail'];transform(rail,lambda p:p+Vector((0,-.14,0)))
for i,x in enumerate([-.77,1.45]):
    o=bpy.data.objects['C43_B35_WireHanger%d'%i]
    old=Vector((x,2.245,-.76));pivot=old+Vector((0,-.14,0));rot=Matrix.Rotation(math.pi/2,3,'Y')
    transform(o,lambda p:pivot+rot@(p-old))
    # Authored pivot at the actual hook/rail contact. The runtime only rotates
    # this rigid Blender object; it never rebuilds hanger geometry.
    origin=bp(pivot);o.data.transform(Matrix.Translation(-origin));o.location=origin
    o['web_userData']=json.dumps({'breezeHanger':True,'breezePhase':i*1.7})
for side in ['Left','Right']:
    o=bpy.data.objects['C43_B35_OldCurtain'+side]
    o['web_userData']=json.dumps({'noCollision':True,'breezeCloth':True,'fixedTop':2.36,'breezePhase':0 if side=='Left' else 1.7})

bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items()),'Non-target changed'
for o in s.objects:
    if o.name.startswith(prefixes):
        bm=bmesh.new();bm.from_mesh(o.data)
        assert all(e.is_manifold for e in bm.edges),o.name
        assert all(f.calc_area()>1e-12 for f in bm.faces),o.name
        bm.free()
s['parent_web_revision']='courtyard43-rack37';s['web_revision']='courtyard43-balcony38'
s['balcony38']=json.dumps({'parent':'courtyard43-rack37','unchangedObjects':len(before),'caseSizesM':[[.41,.82,1.16],[.41,.61,1.20]],'railLoweredM':.14,'scissorLinkLengthPreserved':True,'hangers':'90 degree rotation; authored hook pivots','dimensions':'photo/user correction estimates'})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')}
exec(compile(Path(ns['__file__']).read_text('utf8'),ns['__file__'],'exec'),ns)
result={**ns['export_interior'](),'unchangedObjects':len(before)}
