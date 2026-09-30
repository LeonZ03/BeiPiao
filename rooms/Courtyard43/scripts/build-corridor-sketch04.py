"""User sketch revision 04 only: run through official Blender Lab MCP, never integrate.

Connections follow the user sketch; all rendering dimensions remain estimates. This fresh study cannot overwrite the accepted interior source.
"""
from pathlib import Path
import os
import math
import json
import bpy
from mathutils import Vector

ROOM = Path(__file__).resolve().parents[1]
OUT = ROOM / 'docs/reviews/corridor-sketch04'
SOURCE = ROOM / 'assets/layout-studies/corridor-sketch04.blend'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene['revision'] = 'corridor-sketch04-unapproved'
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

# User correction 04: dining area is outside kitchen; vertical sliding partition,
# short corridor wall on right, and a room door at the top of the dining area.
# Footprint stretched only in this diagram to show appliances; no metric claim.
floor('Bedroom context',0,7.4,0,2.5,bedroom)
floor('EMPTY horizontal corridor',0,7.4,2.5,4,wood)
floor('Bathroom',0,2.45,4,7.4,tile)
floor('Dining area',2.45,4.7,4,7.4,pink)
floor('Kitchen',4.7,7.4,4,7.4,pink)
for name,a,b in [
    ('Bedroom lower',(0,0),(7.4,0)),('Bedroom left',(0,0),(0,2.5)),('Bedroom right',(7.4,0),(7.4,2.5)),
    ('Bedroom door left',(0,2.5),(.12,2.5)),('Bedroom door right',(1.12,2.5),(7.4,2.5)),
    ('Corridor left low',(0,2.5),(0,2.76)),('Corridor left high',(0,3.74),(0,4)),
    ('Corridor right low',(7.4,2.5),(7.4,2.76)),('Corridor right high',(7.4,3.74),(7.4,4)),
    ('Bathroom corridor wall',(0,4),(2.45,4)),('Bathroom left',(0,4),(0,7.4)),
    ('Bathroom right above door',(2.45,4.95),(2.45,7.4)),('Bathroom top',(0,7.4),(2.45,7.4)),
    ('Top room door left',(2.45,7.4),(3.15,7.4)),('Top room door right',(4.10,7.4),(4.7,7.4)),
    ('Kitchen north',(4.7,7.4),(7.4,7.4)),('Kitchen east',(7.4,4),(7.4,7.4)),
    ('USER CONFIRMED short wall at corridor right',(4.7,4),(7.4,4))]:wall(name,a,b)
opening('Bedroom left-hinged door',(.62,2.5,0),1,0,swing=-58)
opening('Bathroom right-side door',(2.45,4.475,0),.95,math.pi/2)
opening('Top ROOM DOOR',(3.625,7.4,0),.95,math.pi)
for x in [0,7.4]:
    opening('Secondary bedroom CLOSED '+str(x),(x,3.25,0),.98,math.pi/2,closed=True)
    box('Closed door handle',(x+(.045 if x==0 else -.045),3.52,.65),(.08,.13,.04),dark,.012)

def cylinder(name,pos,radius,depth,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=radius,depth=depth,location=pos)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(mat);return ob

metal=material('Stainless steel',(.34,.40,.42))
metal.node_tree.nodes['Principled BSDF'].inputs['Metallic'].default_value=.65
metal.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.32
green=material('Open half marker',(.16,.48,.38))

# Two framed frosted sliding leaves overlap in the upper half: never swing.
# Heights are lowered in this review diagram; opening width is 50% by design.
for y in [4.0,7.4]:box('Sliding partition outer jamb',(4.7,y,.74),(.08,.07,1.48),white,.009)
box('Sliding double track',(4.7,5.7,.025),(.15,3.4,.05),metal,.007)
for layer,x in enumerate([4.66,4.74]):
    lo,hi=5.7,7.4
    box('Sliding leaf frosted glass '+str(layer),(x,(lo+hi)/2,.70),(.022,hi-lo-.09,1.28),glass,.009)
    for y in [lo,hi]:box('Sliding leaf vertical stile',(x,y,.7),(.045,.055,1.40),white,.006)
    for z in [.03,.38,.74,1.10,1.40]:box('Sliding leaf cross rail',(x,(lo+hi)/2,z),(.045,hi-lo,.04),white,.006)
    box('Sliding handle',(x-.032,lo+.12,.80),(.04,.06,.21),dark,.008)
box('OPEN HALF floor strip',(4.70,4.85,.058),(.065,1.55,.015),green,.004)

# Dining table from 10.80-11.10s: against wall, white chair, loose papers,
# leaning timber board. It is wholly beyond the empty corridor boundary.
box('Dining table top',(2.83,6.02,.75),(.68,1.43,.07),white)
for x in [2.57,3.09]:
    for y in [5.38,6.65]:box('Dining metal leg',(x,y,.37),(.04,.04,.74),metal,.006)
box('Dining white chair seat',(3.42,5.95,.43),(.40,.43,.055),white,.035)
box('Dining white chair back',(3.62,5.95,.68),(.045,.43,.44),white,.04)
for x in [3.27,3.57]:
    for y in [5.78,6.12]:box('Dining chair leg',(x,y,.215),(.025,.025,.43),metal,.005)
board=box('Visible leaning timber board',(2.58,6.98,.66),(.08,.38,1.31),wood,.008);board.rotation_euler.y=-.09
for i in range(4):
    p=box('Visible table papers',(2.85+i*.008,5.88+i*.025,.795+i*.007),(.30,.39,.006),white,.002);p.rotation_euler.z=.10+i*.055

# Bathroom fixed visible pair, V02 9.67s. Exact hidden fixtures remain omitted.
box('Toilet tank',(.65,7.06,.61),(.43,.23,.60),white,.06)
box('Toilet base',(.65,6.73,.24),(.35,.51,.48),white,.10)
box('Toilet seat',(.65,6.66,.49),(.45,.62,.10),white,.14)
box('Basin pedestal',(1.78,6.82,.40),(.23,.23,.80),white,.08)
box('Basin rim',(1.78,6.82,.84),(.66,.5,.14),white,.12)
box('Basin recess',(1.78,6.80,.917),(.43,.31,.018),glass,.09)
box('Bathroom floor drain',(2.05,5.77,.014),(.14,.14,.02),metal,.005)

# Kitchen viewed through its west sliding entry: sink directly ahead on east
# wall, washing machine/window to left (north), microwave then stove to right.
box('Sink run base',(7.07,5.97,.44),(.62,2.52,.88),white)
box('Cooker return base',(6.05,4.33,.44),(2.08,.60,.88),white)
box('Sink run worktop',(7.07,5.97,.90),(.68,2.58,.065),tile,.018)
box('Cooker return worktop',(6.04,4.33,.90),(2.12,.66,.065),tile,.018)
for y in [6.10,6.68]:
    box('Stainless sink rim',(7.06,y,.943),(.51,.53,.025),metal,.045)
    box('Sink recessed dark basin',(7.06,y,.958),(.41,.43,.008),dark,.05)
# A low arched spout curve is sufficient to recognize the actual sink fitting.
cv=bpy.data.curves.new('Tap curve','CURVE');cv.dimensions='3D';cv.bevel_depth=.017;cv.bevel_resolution=3
sp=cv.splines.new('POLY');pts=[(7.32,6.38,.95),(7.32,6.38,1.20),(7.27,6.38,1.29),(7.12,6.38,1.29),(7.02,6.38,1.18)];sp.points.add(len(pts)-1)
for p,co in zip(sp.points,pts):p.co=(*co,1)
ob=bpy.data.objects.new('Sink faucet',cv);scene.collection.objects.link(ob);ob.data.materials.append(metal)
box('Microwave white body',(7.08,5.22,1.12),(.46,.55,.38),white,.022)
box('Microwave front dark window',(6.841,5.24,1.13),(.014,.38,.25),dark,.014)
cylinder('Microwave control top',(6.83,4.99,1.18),.022,.015,white).rotation_euler.y=math.pi/2
box('Twin gas hob stainless',(6.08,4.32,.955),(1.05,.46,.025),metal)
for x in [5.78,6.37]:
    cylinder('Gas burner',(x,4.33,.984),.105,.035,dark)
    box('Burner grate X',(x,4.33,1.01),(.33,.024,.035),dark,.003)
    box('Burner grate Y',(x,4.33,1.01),(.024,.33,.035),dark,.003)
box('Top loading washing machine',(5.22,7.02,.44),(.67,.64,.88),white,.035)
box('Washing machine lid',(5.22,7.02,.90),(.58,.54,.04),white,.04)
box('Washing machine lid inset',(5.22,6.98,.925),(.47,.37,.018),glass,.025)
# Window behind washing machine, visible without inventing outside view.
for x in [4.8,5.66]:box('Kitchen window side',(x,7.39,1.43),(.05,.05,1.0),white,.006)
for z in [.94,1.22,1.52,1.93]:box('Kitchen window rail',(5.23,7.39,z),(.91,.05,.045),white,.006)
box('Kitchen window opaque patterned glazing',(5.23,7.415,1.43),(.84,.02,.93),glass,.002)

# Upper objects are saved, but hidden only in plan renders to reveal worktops.
upper=[]
upper.append(box('Water heater above sink',(7.23,6.43,1.80),(.30,.49,.66),white,.022))
upper.append(box('Water heater dark panel',(7.071,6.43,1.75),(.015,.30,.16),dark,.006))
upper.append(box('East wall upper cabinet',(7.22,5.49,1.88),(.34,.9,.67),white))
upper.append(box('South wall upper cabinet',(6.86,4.18,1.87),(.6,.35,.67),white))
upper.append(box('Dark extractor hood',(6.06,4.23,1.67),(1.10,.49,.21),dark,.035))
upper.append(box('Hood duct',(6.06,4.19,2.05),(.22,.24,.57),metal,.04))
for y in [5.0,5.5,6.0,6.8]:box('Sink run cabinet seam',(6.75,y,.44),(.008,.012,.75),dark,.001)
for x in [5.4,6.1,6.8]:box('Cooker base cabinet seam',(x,4.018,.44),(.012,.008,.75),dark,.001)

labels=[]
for name,p,size in [('卧室',(3.65,1.15,.13),.36),('走廊 · 保持空置',(3.7,3.15,.13),.27),('厕所',(1.15,5.30,.13),.30),('饭桌区',(3.73,5.37,.13),.25),('厨房',(5.99,5.52,.13),.29),('房门',(3.63,7.80,.13),.24),('次卧 1\n关闭 · 不可进入',(-1.08,3.25,.80),.21),('次卧 2\n关闭 · 不可进入',(8.47,3.25,.80),.21)]:labels.append(text_obj(name,name,p,size,ink))
# Small positional captions make slider opening and short wall unambiguous.
for name,p in [('通行半幅',(4.45,4.80,.12)),('门扇重叠',(4.68,6.34,1.65)),('保留墙段',(6.16,3.88,.76))]:labels.append(text_obj(name,name,p,.17,ink))

bpy.ops.object.light_add(type='AREA',location=(2,-3,12));bpy.context.object.data.energy=2200;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=8
bpy.ops.object.camera_add();camera=bpy.context.object;camera.name='SketchReviewCamera';camera.data.type='ORTHO';camera.data.ortho_scale=14.3;scene.camera=camera
target=Vector((3.7,3.7,0))
views=[('01-top',(3.7,3.7,22),'01  正俯视 · 与标注朝向一致'),('02-oblique',(12,-11,19),'02  斜俯视 · 推拉门保持半开')]
for name,body,y,size in [('Title','门外布局 · 饭桌区与厨房分隔 04',5.7,.30),('Scope','上方房门 / 右侧墙段 / 双扇推拉门半开 / 走廊空置',5.26,.20),('Restriction','物件关系参照视频 10–18 秒；尺寸仍为估计，不改正式卧室布局',-5.37,.19),('Footer','为看清台面，图中隐藏部分吊柜、热水器和油烟机；源工程保留',-5.72,.18)]:
    ob=text_obj(name,body,(0,0,0),size,ink);ob.parent=camera;ob.location=(0,y,-1)
caption=text_obj('View caption','',(0,0,0),.20,ink);caption.parent=camera;caption.location=(0,4.9,-1)
for name,pos,title in views:
    camera.location=pos;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for o in labels:o.rotation_euler=camera.rotation_euler
    for o in upper:o.hide_render=True
    caption.data.body=title
    scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
scene['review_note']='Correction04: dining vs kitchen separated by 50%-open sliding partition; top room door; short wall on corridor right; corridor empty. All dimensions estimated.'
scene['video_item_order']='Facing kitchen through west entry: washer north/window, sink east, microwave south of sink, cooker on south return. Table in dining, outside corridor.'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE))
(OUT/'review.json').write_text(json.dumps({'revision':scene['revision'],'source':str(SOURCE.relative_to(ROOM)),'views':[v[0]+'.png' for v in views],'slidingDoorOpenFraction':.5,'corridorContents':[],'hiddenForPlanReview':[o.name for o in upper],'dimensionsMeasured':False},ensure_ascii=False,indent=2),encoding='utf-8')
result={'source':str(SOURCE),'renders':str(OUT),'revision':scene['revision']}

