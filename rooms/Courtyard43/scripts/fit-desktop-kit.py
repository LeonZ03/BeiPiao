"""Official MCP only: fit separate PCBs and soften photographed rotary caps."""
from pathlib import Path
import ast, json, math
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior13' and s.get('desktop13_finish')
assert not s.get('desktop13_fitted')
p=ROOM/'scripts/add-desktop-kit.py';tree=ast.parse(p.read_text(encoding='utf8'))
env={};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))],type_ignores=[]),str(p),'exec'),env)
env['collection']=bpy.data.collections['C43_DevelopmentKit_desktop13']
env['materials']={m.name.removeprefix('C43_DevKit_'):m for m in bpy.data.materials if m.name.startswith('C43_DevKit_')}
env['material']('blue_rotor',(.038,.20,.49),.48)
# Mainboard USB shell and expansion corner previously intersected. The photo
# shows two separate PCBs; move only expansion assembly 22mm along the desk.
for name in ['Expansion_board','Expansion_silkscreen_and_SMD']:
    obj=bpy.data.objects['C43_DevKit_'+name]
    for v in obj.data.vertices:v.co.x+=.022
for side,origin,tilt,yaw,centres in [
    ('Main',(-1.130,.7433,.386),29,-5,[(-.065+i*.025,.131) for i in range(4)]),
    ('Expansion',(-.942,.7433,.370),33,5,[(.037,.109),(.059,.109),(.005,.085),(.027,.085),(.061,.084),(.005,.056),(.027,.056)])]:
    transform=env['board_transform'](origin,tilt,yaw)
    m=env['Mesh'](side+'_rotor_caps',transform)
    for i,(x,y) in enumerate(centres):
        profile=[(.0055,.0099),(.0060,.0105),(.0060,.0130),(.0055,.0138)]
        vs=[];n=24
        for r,z in profile:
            vs.extend((x+r*math.cos(j*2*math.pi/n),y+r*math.sin(j*2*math.pi/n),z) for j in range(n))
        faces=[tuple(range((len(profile)-1)*n,len(profile)*n))]
        faces += [(k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j) for k in range(len(profile)-1) for j in range(n)]
        m.faces(vs,faces,'blue_rotor')
        a=math.radians([-33,24,49,-21,61,37,-40][i%7])
        m.tube([(x-.0038*math.cos(a),y-.0038*math.sin(a),.01394),(x+.0038*math.cos(a),y+.0038*math.sin(a),.01394)],.00044,'pot_slot',6)
    m.finish()
# Remove just the superseded small GXCT stamp; leave other observed legends.
o=bpy.data.objects['C43_DevKit_Main_board']
f=env['board_transform']((-1.130,.7433,.386),29,-5)
def bp(v):return Vector((v[0],-v[2],v[1]))
origin=bp(f((0,0,0)));columns=[bp(f(p))-origin for p in [(1,0,0),(0,1,0),(0,0,1)]]
inv=Matrix(columns).transposed().inverted()
bm=bmesh.new();bm.from_mesh(o.data)
index=next(i for i,m in enumerate(o.data.materials) if m.name=='C43_DevKit_silkscreen')
remove=[]
for face in bm.faces:
    local=inv@(face.calc_center_median()-origin)
    if face.material_index==index and -.079<local.x<-.067 and .020<local.y<.065 and local.z>.012:remove.append(face)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update()
def tree_for(name):
    ob=bpy.data.objects['C43_DevKit_'+name];me=ob.data
    return BVHTree.FromPolygons([ob.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons])
main,small,box=[tree_for(n) for n in ['Main_board','Expansion_board','Open_cardboard_box']]
assert not main.overlap(small), 'PCB assemblies still intersect'
assert not main.overlap(box) and not small.overlap(box), 'PCB crosses cardboard'
s['desktop13_fitted']=True
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'boardCrossings':0,'boxCrossings':0,'assemblyCount':len(env['collection'].objects)}
