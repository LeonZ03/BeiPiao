"""Append a limited doorway backdrop to interior08 via official Blender MCP.

No kitchen/dining/bathroom reconstruction. Keep approved room and navigation.
The unmodeled semi-open continuation is only an empty recessed visual stop,
not a claim about the rest of the flat. All corridor sizes are estimates.
"""
from pathlib import Path
import bpy, json, hashlib, math
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior08'
assert scene.get('source_layout')=='courtyard43-whitebox06'
assert not any(o.name.startswith('C43_ZCorridor') for o in scene.objects)
bpy.context.preferences.filepaths.save_version=0
before=set(o.name for o in scene.objects)
original_materials={m.name:repr([(n.name,n.type,[(i.name,tuple(i.default_value) if hasattr(i.default_value,'__iter__') and not isinstance(i.default_value,str) else i.default_value) for i in n.inputs if hasattr(i,'default_value')]) for n in m.node_tree.nodes]) for m in bpy.data.materials if m.use_nodes}
collection=bpy.data.collections.new('C43_ZCorridor');scene.collection.children.link(collection)
collection['revision']='corridor01';collection['scope']='empty doorway backdrop only; no additional rooms or interactions'
root=bpy.data.objects.new('C43_ZCorridor',None);collection.objects.link(root)
root['web_tags']=json.dumps({'cutaway':True})
root['web_userData']=json.dumps({'corridorBackdrop':True,'explorable':False})

def clone(source,name):
    m=bpy.data.materials[source].copy();m.name='C43_ZCorridor_'+name
    # Do not reuse contact occlusion baked for the old room floor.
    for n in list(m.node_tree.nodes):
        if n.type=='TEX_IMAGE' and n.image and 'contact' in n.image.name.lower():m.node_tree.nodes.remove(n)
    if 'web_props' in m:
        props=json.loads(m['web_props']);props.pop('aoMapIntensity',None);m['web_props']=json.dumps(props)
    return m
wallmat=clone('C43_Warm_white_plaster','Wall')
floor=clone('C43_Timber_satin_07','Timber')
paint=clone('C43_White_satin_painted_metal','Paint')
skirt=clone('C43_Dark_red_brown_skirt','Skirt')
steel=clone('C43_Brushed_silver_hardware','Metal')
joint=clone('C43_Dark_wood_joint','Joint')
bp=lambda p:Vector((p[0],-p[2],p[1]))
objects=[]
def own(o,name,mat):
    o.name='C43_ZCorridor_'+name
    for c in list(o.users_collection):c.objects.unlink(o)
    collection.objects.link(o);o.parent=root;o.data.materials.append(mat);objects.append(o)
    return o
def uv(o):
    layer=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
    bpy.context.view_layer.update()
    for p in o.data.polygons:
        axis=max(range(3),key=lambda a:abs(p.normal[a]))
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            layer.data[li].uv=((v.y,v.z) if axis==0 else (v.x,v.z) if axis==1 else (v.x,-v.y))
def box(name,pos,size,mat,bevel=.003):
    bpy.ops.mesh.primitive_cube_add(size=1,location=bp(pos));o=own(bpy.context.object,name,mat)
    o.dimensions=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        b=o.modifiers.new('Physical soft edge','BEVEL');b.width=min(bevel,min(size)*.2);b.segments=2;bpy.ops.object.modifier_apply(modifier=b.name)
        w=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=w.name)
    uv(o);return o
def join(name,items):
    bpy.ops.object.select_all(action='DESELECT')
    for o in items:o.select_set(True)
    bpy.context.view_layer.objects.active=items[0];bpy.ops.object.join();o=items[0];o.name='C43_ZCorridor_'+name;return o

left,right,z0,z1=-2.025,2.225,2.85,4.20
height=2.75
box('Subfloor',(.1,-.065,(z0+z1)/2),(4.25,.10,z1-z0),joint,.001)
boards=[]
for i in range(33):
    a=left+i*4.25/33;b=left+(i+1)*4.25/33
    seam=3.44+(i%3)*.13
    for start,end in [(z0,seam),(seam,z1)]:
        boards.append(box('Board',((a+b)/2,-.009,(start+end)/2),(b-a-.0013,.018,end-start-.0013),floor,.0006))
join('Floor',boards)
# Returns adjoining original doorway, with no near-coplanar floor sheets.
walls=[]
for x in [left-.06,right+.06]:
    for a,b in [(z0,3.13),(3.97,z1+.12)]:walls.append(box('SideWall',(x,height/2,(a+b)/2),(.12,height,b-a),wallmat))
    walls.append(box('SideDoorHeader',(x,2.425,3.55),(.12,.65,.84),wallmat))
# Retain a shallow empty continuation at the semi-open middle; don't add a
# dining room, kitchen, bathroom, furniture or new clickable destination.
for a,b in [(left-.12,-.52),(.56,right+.12)]:walls.append(box('OppositeWall',((a+b)/2,height/2,z1+.06),(b-a,height,.12),wallmat))
for x in [-.58,.62]:walls.append(box('UnmodeledReturn',(x,height/2,4.47),(.12,height,.42),wallmat))
walls.append(box('UnmodeledVisualStop',(.02,height/2,4.74),(1.32,height,.12),wallmat))
walls.append(box('ContinuationHeader',(.02,2.45,4.26),(1.08,.6,.12),wallmat))
join('Walls',walls)
box('ContinuationFloor',(.02,-.03,4.47),(1.08,.06,.54),floor,.001)
box('Ceiling',(.1,2.81,3.80),(4.49,.12,1.9),wallmat,.002)
skirts=[]
for a,b in [(left,-.52),(.56,right)]:skirts.append(box('Skirt',((a+b)/2,.045,z1-.009),(b-a,.09,.018),skirt,.002))
for x in [left+.009,right-.009]:
    for a,b in [(z0,3.13),(3.97,z1)]:skirts.append(box('Skirt',(x,.045,(a+b)/2),(.018,.09,b-a),skirt,.002))
join('Skirting',skirts)

for side,x,sign in [('Left',left,1),('Right',right,-1)]:
    parts=[]
    # Closed, slightly inset paneled doors seen only from the corridor.
    parts.append(box(side+'ClosedDoor',(x-sign*.020,1.045,3.55),(.045,2.09,.812),paint,.004))
    for z in [3.105,3.995]:parts.append(box(side+'Jamb',(x+sign*.012,1.065,z),(.07,2.13,.047),paint,.004))
    parts.append(box(side+'JambTop',(x+sign*.012,2.137,3.55),(.07,.048,.937),paint,.004))
    # Trim only: shallow physical relief, no layered coplanar faces.
    for y0,y1 in [(.16,.83),(.98,1.94)]:
        for z in [3.23,3.87]:parts.append(box(side+'PanelTrim',(x+sign*.010,(y0+y1)/2,z),(.018,y1-y0,.023),paint,.003))
        for y in [y0,y1]:parts.append(box(side+'PanelTrim',(x+sign*.010,y,3.55),(.018,.024,.66),paint,.003))
    door=join(side+'ClosedDoor',parts);door['web_userData']=json.dumps({'secondaryBedroom':True,'openable':False,'explorable':False})
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.034,location=bp((x+sign*.067,1.00,3.25)))
    knob=own(bpy.context.object,side+'DoorKnob',steel);uv(knob)
    for p in knob.data.polygons:p.use_smooth=True
    box(side+'KnobBase',(x+sign*.025,1.0,3.25),(.026,.06,.06),steel,.01)

bpy.context.view_layer.update()
assert before=={o.name for o in scene.objects if not o.name.startswith('C43_ZCorridor')}
for name,expected in original_materials.items():
    m=bpy.data.materials[name]
    actual=repr([(n.name,n.type,[(i.name,tuple(i.default_value) if hasattr(i.default_value,'__iter__') and not isinstance(i.default_value,str) else i.default_value) for i in n.inputs if hasattr(i,'default_value')]) for n in m.node_tree.nodes])
    assert actual==expected,name
assert not any('c43_interaction' in o for o in collection.objects)
component=ROOM/'assets/corridor/Courtyard43-corridor.blend';component.parent.mkdir(parents=True,exist_ok=True)
bpy.data.libraries.write(str(component),{collection},path_remap='RELATIVE',fake_user=True,compress=True)
records=json.loads(scene['components']);records.append({'component':'corridor','source':str(component.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(component.read_bytes()).hexdigest(),'revision':'corridor01'})
scene['components']=json.dumps(records)
scene['parent_web_revision']='courtyard43-interior08';scene['web_revision']='courtyard43-interior09'
scene['corridor09']='Doorway view only. Empty passage, two noninteractive closed secondary-bedroom doors; other rooms intentionally out of scope. Dimensions estimated.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'corridor_export'}
exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope)
result=scope['export_interior']();result['unchangedOriginalObjects']=len(before);result['corridorSource']=str(component)
(ROOT/'analysis/Courtyard43/corridor09/mcp-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
