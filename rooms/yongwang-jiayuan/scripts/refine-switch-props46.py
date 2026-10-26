"""props45 -> props46: append the completed C43 switch31 sealed switch.

Official Blender Lab MCP. No independent second geometry generator; all source
meshes and materials are copied from the same finished donor version.
"""
from pathlib import Path
import bpy,json,copy
from mathutils import Matrix,Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props45'
source=ROOT/'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend'
donor=json.loads((ROOT/'room-site/dist/assets/rooms/Courtyard43/interior/scene.json').read_text('utf8'))
assert donor['revision']=='courtyard43-switch31','Inspect the new donor revision before reusing this stage'
names=['C43_Switch_Backplate','C43_Switch_Rocker']
with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=names
assert all(b.objects)
source_objects=list(b.objects);sm=source_objects[0].material_slots[0].material
assert sm.name.startswith('Switch31')
mid=len(data['materials']);cm=sm.copy();cm.name='Shared46 '+sm.name;cm['web_material_id']=mid
bs=next(n for n in cm.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
data['materials'].append({'id':mid,'name':cm.name,'type':'MeshPhysicalMaterial','props':{'roughness':.48,'metalness':0,'ior':1.5,'side':0,'depthWrite':True},'colors':{'color':list(bs.inputs['Base Color'].default_value)[:3]},'textures':{},'vectors':{},'userData':{'sourceRoom':'Courtyard43','sourceRevision':'courtyard43-switch31','closedSolid':True}});mats[mid]=cm
for src,nid,x in [(source_objects[0],1482,1.4-.00375),(source_objects[1],1483,1.4-.0065)]:
    me=src.data.copy();me.materials.clear();me.materials.append(cm)
    o=attach(me,data['nodes'][nid]['name'],mid,1481,nid)
    o.matrix_local=Matrix.Translation(Vector(bp((x,1.120,.860))))
    o['source_asset']='Courtyard43 / courtyard43-switch31';o['switch31_closed_solid']=True
    bpy.context.view_layer.update();data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);export(o)
    assert len(me.vertices)==len(src.data.vertices)
    bpy.data.objects.remove(src,do_unlink=True)
data['nodes'][2033]['visible']=False;data['nodes'][2033]['castShadow']=False;changed.add(2033)
obs[2033].hide_render=True
details={**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'switch31':{'parent':'props45','source':'Courtyard43 / courtyard43-switch31','wallX':1.4,'wellFloorX':1.3998,'rockerCenterX':1.3935,'angle':.045,'retiredGap':2033}}
result=save('props46',details)
