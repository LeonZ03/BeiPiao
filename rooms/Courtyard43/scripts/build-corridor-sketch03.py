"""User sketch revision 03 only: run through official Blender Lab MCP, never integrate.

Connections follow the user sketch; all rendering dimensions remain estimates. This fresh study cannot overwrite the accepted interior source.
"""
from pathlib import Path
import os
import math
import json
import bpy
from mathutils import Vector

ROOM = Path(__file__).resolve().parents[1]
OUT = ROOM / 'docs/reviews/corridor-sketch03'
SOURCE = ROOM / 'assets/layout-studies/corridor-sketch03.blend'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene['revision'] = 'corridor-sketch03-unapproved'
scene['warning'] = 'Topology follows user sketch; dimensions and door swing angles are illustrative. No cardinal orientation assigned.'
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

def opening(name,center,width,angle=0,closed=False,swing=58):
    # Orange base strips intentionally distinguish hypothesized locations.
    c=Vector(center);along=Vector((math.cos(angle),math.sin(angle),0))
    for side in [-1,1]:
        p=c+along*(width/2)*side
        box(name+' jamb',p+Vector((0,0,.70)),(.07,.07,1.4),orange,.008)
    sill=box(name+' threshold',c+Vector((0,0,.025)),(width,.09,.05),orange,.006);sill.rotation_euler.z=angle
    if closed:
        leaf=box(name+' leaf',c+Vector((0,0,.65)),(width-.08,.055,1.3),white);leaf.rotation_euler.z=angle
        leaf['interactive']=False
        leaf['explorable']=False
    else:
        leafangle=angle+math.radians(swing)
        hinge=c-along*width/2
        leaf=box(name+' open schematic leaf',hinge+Vector((math.cos(leafangle),math.sin(leafangle),0))*(width-.08)/2+Vector((0,0,.40)),(width-.08,.045,.8),glass,.012)
        leaf.rotation_euler.z=leafangle

font_path=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc'
font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def text_obj(name,body,location,size,mat):
    d=bpy.data.curves.new(name,'FONT');d.body=body;d.size=size;d.align_x='CENTER';d.align_y='CENTER';d.extrude=0
    if font:d.font=font
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=location;o.data.materials.append(mat);return o

# Same orientation as the user's paper: bedroom below, horizontal corridor,
# bathroom upper-left, kitchen upper-right. No geographic compass is implied.
floor('Main bedroom context',0,6.2,0,2.5,bedroom)
floor('Horizontal corridor',0,6.2,2.5,4.0,wood)
floor('Bathroom upper left',0,2.45,4.0,6.8,tile)
floor('Kitchen upper right',2.45,6.2,4.0,6.8,pink)
for name,a,b in [
    ('Bedroom lower',(0,0),(6.2,0)),('Bedroom left',(0,0),(0,2.5)),('Bedroom right',(6.2,0),(6.2,2.5)),
    ('Bedroom doorway left',(0,2.5),(.12,2.5)),('Bedroom doorway right',(1.12,2.5),(6.2,2.5)),
    ('Corridor left lower',(0,2.5),(0,2.76)),('Corridor left upper',(0,3.74),(0,4)),
    ('Corridor right lower',(6.2,2.5),(6.2,2.76)),('Corridor right upper',(6.2,3.74),(6.2,4)),
    ('Bathroom continuous corridor wall',(0,4),(2.45,4)),
    ('Bathroom left',(0,4),(0,6.8)),('Upper outer',(0,6.8),(6.2,6.8)),
    ('Bathroom kitchen divider above doorway',(2.45,4.95),(2.45,6.8)),('Kitchen right',(6.2,4),(6.2,6.8))]:wall(name,a,b)

opening('Main bedroom door LEFT HINGE',(.62,2.5,0),1,0,swing=-58)
opening('Bathroom door RIGHT SIDE', (2.45,4.475,0),.95,math.pi/2)
opening('Secondary bedroom LEFT CLOSED',(0,3.25,0),.98,math.pi/2,closed=True)
opening('Secondary bedroom RIGHT CLOSED',(6.2,3.25,0),.98,math.pi/2,closed=True)
# No floors, shells or furnishings behind either secondary-bedroom door.
for x in [0,6.2]:
    # Handles indicate a complete closed door, not a passage or placeholder gap.
    box('Closed door visible handle',(x+(.045 if x==0 else -.045),3.52,.65),(.08,.13,.04),dark,.012)

# Facilities observed in V02. Placements within rooms are schematic.
box('Toilet tank',(.64,6.43,.61),(.43,.23,.6),white,.06)
box('Toilet pedestal',(.64,6.09,.24),(.35,.5,.48),white,.1)
box('Toilet seat',(.64,6.04,.49),(.45,.62,.10),white,.14)
box('Basin pedestal',(1.78,6.18,.4),(.23,.23,.8),white,.08)
box('Basin rim',(1.78,6.18,.84),(.65,.50,.14),white,.1)
box('Basin recess',(1.78,6.16,.916),(.42,.3,.02),glass,.09)
box('Kitchen back counter',(4.27,6.43,.45),(3.4,.60,.90),white)
box('Kitchen right return',(5.86,5.54,.45),(.59,1.19,.90),white)
for x in [3.0,3.57]:box('Double sink schematic',(x,6.43,.91),(.49,.40,.035),dark,.04)
box('Stovetop schematic',(5.86,5.52,.918),(.43,.79,.035),dark)
box('Washing machine seen in video',(2.86,5.45,.44),(.62,.60,.88),white,.04)
box('Washing machine lid',(2.86,5.45,.90),(.54,.52,.035),glass,.03)
# User correction: the corridor is empty. No table, chair or clutter.

labels=[]
for name,p,size in [('卧室',(3.0,1.10,.13),.40),('走廊 · 无陈设',(3.3,3.18,.13),.30),('厕所',(1.12,4.95,.13),.34),('厨房',(4.38,5.36,.13),.34),('半开放连接',(4.38,4.08,.10),.21),('次卧 1\n关闭 · 不可进入',(-1.07,3.25,.80),.23),('次卧 2\n关闭 · 不可进入',(7.25,3.25,.80),.23)]:
    labels.append(text_obj(name,name,p,size,ink))

bpy.ops.object.light_add(type='AREA',location=(2,-3,11));bpy.context.object.data.energy=1900;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='SketchReviewCamera';camera.data.type='ORTHO';camera.data.ortho_scale=13.2;scene.camera=camera
target=Vector((3.1,3.4,0))
views=[('01-top',(3.1,3.4,20),'01  正俯视 · 与手绘朝向一致'),('02-oblique',(10,-10,17),'02  斜俯视 · 门洞及通道关系')]
for name,body,y,size in [('Title','门外布局 · 半开放修正版 03',5.25,.30),('Scope','移除走廊桌椅；厨房侧开敞；卧室门与厕所门按标线纠正',4.83,.19),('Restriction','走廊两端各一间次卧：仅保留关闭的门，不建室内、不开放探索',-4.95,.20),('Footer','局部结构审阅 · 未接入正式房间 · 隐去顶棚并降低墙高',-5.30,.18)]:
    ob=text_obj(name,body,(0,0,0),size,ink);ob.parent=camera;ob.location=(0,y,-1)
caption=text_obj('View caption','',(0,0,0),.20,ink);caption.parent=camera;caption.location=(0,4.48,-1)
for name,pos,view_caption in views:
    camera.location=pos;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for o in labels:o.rotation_euler=camera.rotation_euler
    caption.data.body=view_caption
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
scene['review_note']='User correction 03: empty corridor; inferred open kitchen connection; bedroom left hinge; bathroom door in lower right partition. Closed secondary bedrooms unchanged. Sizes estimated.'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
(OUT/'review.json').write_text(json.dumps({'revision':scene['revision'],'topologySource':'user hand-drawn plan and annotated correction03, 2026-09-30','corridorEmpty':True,'kitchenConnection':'open, no dividing wall or door','bathroomDoor':'lower end of right partition','bedroomDoorHinge':'drawing-left','metricApproved':False,'source':str(SOURCE.relative_to(ROOM)),'views':[v[0]+'.png' for v in views],'secondaryBedrooms':{'count':2,'closed':True,'interactive':False,'interiorsModeled':False}},ensure_ascii=False,indent=2),encoding='utf-8')
result={'source':str(SOURCE),'renders':str(OUT),'revision':scene['revision']}

