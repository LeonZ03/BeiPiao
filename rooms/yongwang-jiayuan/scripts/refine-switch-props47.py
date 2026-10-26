"""props46 -> props47: reuse C43 switch32 final thicker meshes and off tilt.

Official Blender Lab MCP; current materials and non-switch descriptors retained.
"""
from pathlib import Path
import bpy,json,copy
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props46'
donor=json.loads((ROOT/'room-site/dist/assets/rooms/Courtyard43/interior/scene.json').read_text('utf8'))
assert donor['revision']=='courtyard43-switch32'
names=['C43_Switch_Backplate','C43_Switch_Rocker']
with bpy.data.libraries.load(str(ROOT/'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend'),link=False) as (a,b):b.objects=names
for src,nid,x,angle in [(b.objects[0],1482,1.4-.00375,0),(b.objects[1],1483,1.4-.008,-.045)]:
    assert src is not None
    me=src.data.copy();mid=data['nodes'][nid]['material'];me.materials.clear();me.materials.append(mats[mid])
    o=attach(me,data['nodes'][nid]['name'],mid,1481,nid)
    o.matrix_local=Matrix.Translation(Vector(bp((x,1.120,.860))))@Matrix.Rotation(angle,4,Vector((0,-1,0)))
    o['source_asset']='Courtyard43 / courtyard43-switch32'
    bpy.context.view_layer.update();data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);export(o)
    bpy.data.objects.remove(src,do_unlink=True)
details={**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'switch32':{'parent':'props46','source':'Courtyard43 / courtyard43-switch32','wallX':1.4,'wellFloorX':1.3998,'rockerCenterX':1.392,'housingThicknessM':.0115,'rockerThicknessM':.010,'angle':.09,'offAngle':-.045,'onAngle':.045}}
result=save('props47',details)
