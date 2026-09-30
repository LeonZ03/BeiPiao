"""Hypothesis A only: run through official Blender Lab MCP, never integrate.

All plan coordinates below are illustrative video estimates, not approved
dimensions. This fresh study cannot overwrite the accepted interior source.
"""
from pathlib import Path
import os
import math
import json
import bpy
from mathutils import Vector

ROOM = Path(__file__).resolve().parents[1]
OUT = ROOM / 'docs/reviews/corridor-hypothesis01'
SOURCE = ROOM / 'assets/layout-studies/corridor-hypothesis01.blend'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene['revision'] = 'corridor-hypothesis01-unapproved'
scene['warning'] = 'Illustrative connectivity hypothesis, NOT measured or approved. No cardinal orientation assigned.'
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.render.resolution_x = 1400
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new('StudyWorld')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.72,.76,.8,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value = .65
nodes=scene.world.node_tree.nodes
links=scene.world.node_tree.links
camera_background=nodes.new('ShaderNodeBackground')
camera_background.inputs[0].default_value=(.86,.90,.93,1)
camera_background.inputs[1].default_value=1
ray=nodes.new('ShaderNodeLightPath');mix=nodes.new('ShaderNodeMixShader')
links.new(ray.outputs['Is Camera Ray'],mix.inputs[0])
links.new(nodes['Background'].outputs[0],mix.inputs[1])
links.new(camera_background.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],nodes['World Output'].inputs[0])
scene.view_settings.view_transform = 'AgX'
bpy.context.preferences.filepaths.save_version = 0

def material(name, color, emission=False):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=.7
    if emission:
        n.inputs['Emission Color'].default_value=(*color,1);n.inputs['Emission Strength'].default_value=1
    return m

white=material('White cutaway walls',(.78,.8,.8))
dark=material('Dark fittings',(.08,.105,.12))
wood=material('Observed dark wood category',(.24,.085,.055))
pink=material('Observed pink brown tile category',(.51,.32,.25))
tile=material('Observed pale bathroom tile',(.7,.71,.64))
bedroom=material('Bedroom context only',(.32,.45,.52))
orange=material('UNCONFIRMED openings',(.95,.39,.075))
blue=material('Route hypothesis',(.045,.36,.58))
red=material('Visible red decoration, no invented text',(.65,.055,.03))
glass=material('Glazing schematic',(.28,.48,.51))
ink=material('Label ink',(.025,.045,.07),True)
paper=material('Label light',(.95,.97,.99),True)

def box(name, pos, size, mat, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        b=o.modifiers.new('Soft edges','BEVEL');b.width=bevel;b.segments=2
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o

def floor(name,x0,x1,y0,y1,mat):
    return box(name,((x0+x1)/2,(y0+y1)/2,-.08),(x1-x0,y1-y0,.16),mat)

def wall(name,a,b,height=.65):
    x0,y0=a;x1,y1=b
    return box(name,((x0+x1)/2,(y0+y1)/2,height/2),
               (max(abs(x1-x0),.12),max(abs(y1-y0),.12),height),white)

floor('A bedroom doorway context only',0,3,-1.7,0,bedroom)
floor('Short passage',0,1.2,0,2.6,wood)
floor('C table area',1.2,3.8,1,3.9,pink)
floor('D bathroom visible part',3.8,6,1,3.9,tile)
floor('E kitchen visible part',1.2,3.8,3.9,6.2,pink)
# Cutaway walls: room-sized rectangles beyond visible evidence are placeholders.
for name,a,b in [
    ('Bedroom back cut',(0,-1.7),(3,-1.7)),('Bedroom left',(0,-1.7),(0,0)),
    ('Bedroom right',(3,-1.7),(3,0)),('Bedroom door left',(0,0),(.15,0)),('Bedroom door right',(1.05,0),(3,0)),
    ('Passage left',(0,0),(0,2.6)),('Passage right low',(1.2,0),(1.2,1.15)),
    ('Passage right upper',(1.2,2.15),(1.2,2.6)),('Red door left',(0,2.6),(.15,2.6)),('Red door right',(1.05,2.6),(1.2,2.6)),
    ('Hall bottom',(1.2,1),(3.8,1)),('Hall left beyond passage',(1.2,2.6),(1.2,3.9)),
    ('Bath door bottom',(3.8,1),(3.8,1.35)),('Bath door top',(3.8,2.25),(3.8,3.9)),
    ('Bath far wall',(6,1),(6,3.9)),('Bath bottom',(3.8,1),(6,1)),('Bath top',(3.8,3.9),(6,3.9)),
    ('Kitchen door left',(1.2,3.9),(2.4,3.9)),('Kitchen door right',(3.4,3.9),(3.8,3.9)),
    ('Kitchen left',(1.2,3.9),(1.2,6.2)),('Kitchen right',(3.8,3.9),(3.8,6.2)),('Kitchen back',(1.2,6.2),(3.8,6.2))]:wall(name,a,b)

def opening(name,center,width,angle=0,closed=False):
    # Orange base strips intentionally distinguish hypothesized locations.
    c=Vector(center);along=Vector((math.cos(angle),math.sin(angle),0))
    for side in [-1,1]:
        p=c+along*(width/2)*side
        box(name+' jamb',p+Vector((0,0,.70)),(.07,.07,1.4),orange,.008)
    sill=box(name+' threshold',c+Vector((0,0,.025)),(width,.09,.05),orange,.006);sill.rotation_euler.z=angle
    if closed:
        leaf=box(name+' leaf',c+Vector((0,0,.65)),(width-.08,.055,1.3),white);leaf.rotation_euler.z=angle
        for dx in [-.2,.05,.25]:box('Red visible patch',c+Vector((dx,-.034,1.0)),(.07,.01,.20),red,.002)
    else:
        leafangle=angle+math.radians(58)
        hinge=c-along*width/2
        leaf=box(name+' open schematic leaf',hinge+Vector((math.cos(leafangle),math.sin(leafangle),0))*(width-.08)/2+Vector((0,0,.40)),(width-.08,.045,.8),glass,.012)
        leaf.rotation_euler.z=leafangle

opening('A bedroom door',(.60,0,0),.9)
opening('B red decorated door',(.60,2.60,0),.9,closed=True)
opening('C possible side connection',(1.20,1.65,0),1,math.pi/2)
opening('D bathroom door',(3.8,1.8,0),.9,math.pi/2)
opening('E kitchen door',(2.9,3.9,0),1)

# Only recognizable furniture masses; no unseen detailed room fittings.
box('C visible white table',(1.78,3.25,.73),(1.0,.58,.08),white)
for x in [1.37,2.18]:
    for y in [3.03,3.47]:box('Table leg',(x,y,.36),(.04,.04,.72),white,.008)
box('C chair seat',(2.0,2.59,.43),(.4,.4,.06),white)
box('C chair back',(2,2.4,.68),(.4,.045,.43),white)
for x in [1.84,2.16]:
    for y in [2.43,2.75]:box('Chair leg',(x,y,.21),(.025,.025,.42),dark,.004)
box('D toilet tank',(4.35,3.59,.60),(.42,.22,.58),white,.06)
box('D toilet base',(4.35,3.24,.23),(.34,.50,.46),white,.1)
box('D toilet seat simplified',(4.35,3.19,.46),(.44,.59,.11),white,.15)
box('D pedestal basin stem',(5.34,3.35,.4),(.22,.22,.8),white,.08)
box('D basin silhouette',(5.34,3.35,.83),(.67,.5,.14),white,.12)
box('D basin dark recess',(5.34,3.33,.907),(.42,.3,.015),glass,.10)
box('E sink counter',(2.45,5.84,.45),(2.36,.6,.9),white)
box('E side counter',(3.47,4.95,.45),(.52,1.2,.9),white)
for x in [1.94,2.52]:box('E double sink',(x,5.84,.91),(.49,.40,.04),dark,.05)
box('E cooker block',(3.47,4.92,.92),(.43,.75,.035),dark)

def cylinder(name,loc,radius,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=loc)
    o=bpy.context.object;o.name=name;o.data.materials.append(mat);return o

def arrow(a,b):
    a=Vector((*a,.035));b=Vector((*b,.035));v=b-a
    shaft=box('Hypothesized walking direction',(a+b)/2,(v.length-.12,.045,.025),blue,.005)
    shaft.rotation_euler.z=math.atan2(v.y,v.x)
    direction=v.normalized();side=Vector((-direction.y,direction.x,0))
    mesh=bpy.data.meshes.new('Route arrow mesh');mesh.from_pydata([b,b-direction*.23+side*.13,b-direction*.23-side*.13],[],[(0,1,2)])
    ob=bpy.data.objects.new('Route arrow',mesh);scene.collection.objects.link(ob);ob.data.materials.append(blue)

for a,b in [((.6,.35),(.6,1.55)),((.65,1.65),(2.45,1.65)),((2.7,2.1),(2.7,3.45))]:arrow(a,b)

font_path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc'
font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def text_obj(name,body,location,size,mat):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.align_y='CENTER';d.extrude=0
    if font:d.font=font
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=location;o.data.materials.append(mat);return o

labels=[]
for letter,p in [('A',(1.5,-.95,.12)),('B',(.6,2.6,1.62)),('C',(2.65,2.75,.2)),('D',(4.95,2.1,.2)),('E',(2.30,4.85,.2))]:
    labels.append(text_obj('Area '+letter,letter,p,.43,ink))

bpy.ops.object.light_add(type='AREA',location=(1,-3,10));bpy.context.object.data.energy=1800;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='StudyCamera';camera.data.type='ORTHO';camera.data.ortho_scale=13.2;scene.camera=camera
target=Vector((2.6,2.2,0))
views=[('01-front-oblique',(11,-10,15),'01  从卧室一侧俯看'),('02-left-oblique',(-9,-7,14),'02  从另一侧俯看'),('03-reverse-oblique',(10,13,16),'03  从厨房一侧回看'),('04-top',(2.6,2.2,20),'04  正上方：重点核对门洞关系')]
hud=[]
for name,body,y,size,mat in [('title','门外布局 · 理解稿 A（待确认）',5.25,.29,ink),('warning','橙色 = 推定门洞位置；尺寸、转向与开门方向均未确认',4.83,.19,ink),('legend','A 卧室门口    B 贴红饰的门    C 桌边区域    D 卫生间    E 厨房',-4.95,.19,ink),('note','仅供纠正空间关系 · 非完整户型 · 已隐藏顶棚并降低墙高',-5.30,.18,ink)]:
    ob=text_obj(name,body,(0,0,0),size,mat);ob.parent=camera;ob.location=(0,y,-1);ob.rotation_euler=(0,0,0);hud.append(ob)
view_label=text_obj('View caption','',(0,0,0),.20,ink);view_label.parent=camera;view_label.location=(0,4.48,-1)
for name,pos,caption in views:
    camera.location=pos
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for o in labels:o.rotation_euler=camera.rotation_euler
    view_label.data.body=caption
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
scene['review_note']='B is an unidentified decorated door, not asserted to be the apartment entrance. C side connection, D/E locations are hypotheses.'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
(OUT/'review.json').write_text(json.dumps({'revision':scene['revision'],'approved':False,'source':str(SOURCE.relative_to(ROOM)),'views':[v[0]+'.png' for v in views],'hypothesis':'A bedroom -> short passage with B ahead; guessed right branch C -> D bathroom / E kitchen. No metric or cardinal claims.'},ensure_ascii=False,indent=2),encoding='utf-8')
result={'source':str(SOURCE),'renders':str(OUT),'revision':scene['revision']}
