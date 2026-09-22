"""Courtyard43 architecture, run ONLY through Blender Lab official MCP.

Independent component built from approved whitebox06. Photos P03/P04 define
occupancy; P01/P02 and V01 define retained structure. Dimensions are estimates.
Cloth uses the proven Yongwang direct closed-volume + morph method, adapted
without executing the historic generator or modifying its source.
"""
import json
import math
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
OUT = ROOM / 'assets/architecture'
TEX = OUT / 'textures'
REPORT = ROOT / 'analysis/Courtyard43/architecture'
for directory in (OUT, TEX, REPORT):
    directory.mkdir(parents=True, exist_ok=True)
P = json.loads((ROOM / 'history/inputs/approved-layout.json').read_text(encoding='utf-8'))
assert P['structureApproved'] and P['parentRevision'] == 'courtyard43-whitebox06'
assert P['room']['width'] == 4.25 and P['room']['centerX'] == .1
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene['room_id'] = 'Courtyard43'
scene['component'] = 'architecture'
scene['web_revision'] = 'courtyard43-interior01'
scene['component_revision'] = 'architecture01'
scene['source_layout'] = 'courtyard43-whitebox06'
scene['dimension_source'] = 'Photo estimates; user approved spatial arrangement, not measured dimensions'
coll = bpy.data.collections.new('C43_Architecture')
scene.collection.children.link(coll)


def bp(p):
    return (p[0], -p[2], p[1])


def own(o, name, tags=None):
    o.name = 'C43_' + name
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    o['web_tags'] = json.dumps(tags or {})
    return o


def image(name, rgb, color=True):
    rgb = np.asarray(rgb, dtype=np.float32)
    if rgb.ndim == 2:
        rgb = np.repeat(rgb[:, :, None], 3, axis=2)
    h, w = rgb.shape[:2]
    im = bpy.data.images.new('C43_' + name, width=w, height=h, alpha=False)
    im.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    # Blender's generated Image.save writes assigned PNG samples verbatim in
    # this MCP/runtime build. Encode albedo explicitly, so after reopening an
    # sRGB image decodes back to the intended scene-linear reflectance. Never
    # apply this transfer to normal/data maps.
    rgb = np.clip(rgb, 0, 1)
    if color:
        rgb = np.where(rgb <= .0031308, rgb*12.92, 1.055*np.power(rgb, 1/2.4)-.055)
    rgba = np.concatenate((rgb, np.ones((h, w, 1))), axis=2)
    im.pixels.foreach_set(rgba.astype(np.float32).ravel())
    im.filepath_raw = str(TEX / (name + '.png'))
    im.file_format = 'PNG'
    im.save()
    return im


def material(name, color, rough=.6, metal=0, base=None, normal=None, alpha=1, props=None):
    m = bpy.data.materials.new('C43_' + name)
    m.use_nodes = True
    m.diffuse_color = (*color, alpha)
    m.roughness = rough
    m.metallic = metal
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Alpha'].default_value = alpha
    if base:
        tx = m.node_tree.nodes.new('ShaderNodeTexImage')
        tx.image = base
        m.node_tree.links.new(tx.outputs['Color'], bs.inputs['Base Color'])
    if normal:
        tx = m.node_tree.nodes.new('ShaderNodeTexImage')
        tx.image = normal
        nm = m.node_tree.nodes.new('ShaderNodeNormalMap')
        nm.inputs['Strength'].default_value = .35
        m.node_tree.links.new(tx.outputs['Color'], nm.inputs['Color'])
        m.node_tree.links.new(nm.outputs[0], bs.inputs['Normal'])
    if props:
        m['web_props'] = json.dumps(props)
    return m


# Compact photo-guided, non-photographic PBR maps generated in Blender via MCP.
# They contain albedo/normal only: no room shadows, perspective or highlights.
rng = np.random.default_rng(4306)
N = 1024
yy, xx = np.mgrid[0:N, 0:N] / N
warp = xx + .010*np.sin(yy*15) + .004*np.sin(yy*37+xx*9)
grain = .018*np.sin(warp*690 + 1.7*np.sin(yy*7)) + .011*np.sin(warp*1470 + yy*19)
grain += .009*np.sin(warp*163 + yy*2) + rng.normal(0, .003, (N, N))
woodrgb = np.stack([.245+grain, .083+grain*.47, .035+grain*.24], axis=-1)
# Final P03/P04 browser calibration: darker red-brown reflectance, preserving
# the grain's relative chromatic variation, UVs, normal relief and satin finish.
woodrgb *= np.array([.14/.245, .048/.083, .026/.035])
woodtex = image('red-brown-wood-albedo', woodrgb)
gy, gx = np.gradient(grain)
woodnormal = np.stack([.5-gx*4, .5-gy*4, np.full_like(xx, .999)], axis=-1)
woodnorm = image('red-brown-wood-normal', woodnormal, False)
N = 512
yy, xx = np.mgrid[0:N, 0:N] / N
fibres = .008*np.sin(xx*math.tau*181) + .006*np.sin(yy*math.tau*163)
fibres += rng.normal(0, .0015, (N, N))
clothtex = image('grey-woven-cloth-albedo', np.stack([.175+fibres, .174+fibres, .169+fibres], axis=-1))
clothnorm = image('grey-woven-cloth-normal', np.stack([.5+.05*np.sin(xx*math.tau*181), .5+.04*np.sin(yy*math.tau*163), np.ones_like(xx)*.996], axis=-1), False)
plastertex = image('warm-white-plaster-albedo', np.repeat((.72 + rng.normal(0,.003,(N,N)))[:, :, None], 3, axis=2))
# Six staggered rows; red, salmon and light buff rectangular brick-pattern tile.
rows = np.floor(yy*6).astype(int)
columns = np.floor(xx*4 + (rows%2)*.5).astype(int)
palette = np.array([[.43,.19,.115],[.52,.27,.17],[.34,.135,.075],[.62,.38,.24],[.46,.205,.13],[.57,.32,.205]])
palette_id = (rows*7+columns*3+rows*columns) % len(palette)
brickrgb = palette[palette_id] + rng.normal(0,.007,(N,N,1))
fx = (xx*4+(rows%2)*.5)%1
fy = (yy*6)%1
joints = (fx<.012)|(fx>.988)|(fy<.021)|(fy>.979)
brickrgb[joints] = (.53,.40,.29)
bricktex = image('balcony-brick-pattern-albedo', brickrgb)
# Irregular small porcelain mosaic, based on the stone-like P01 floor pattern.
points = rng.uniform(-.1, 1.1, (180, 2))
best = np.full((N,N), 10.0)
second = best.copy()
ids = np.zeros((N,N), dtype=int)
for i, pnt in enumerate(points):
    dist = (xx-pnt[0])**2 + (yy-pnt[1])**2
    hit = dist<best
    second = np.where(hit,best,np.minimum(second,dist))
    best = np.where(hit,dist,best)
    ids = np.where(hit,i,ids)
stonecols = rng.uniform(.32,.57,(180,1))*np.array([[1,.72,.53]])
stonergb = stonecols[ids] + rng.normal(0,.005,(N,N,1))
stonergb[np.sqrt(second)-np.sqrt(best)<.006] = (.69,.62,.51)
stonetex = image('balcony-small-mosaic-albedo',stonergb)
# A restrained reed/leaf silhouette: legible plant motif, no invented text.
floral = np.ones((N,N,3))*np.array([.47,.61,.60])
mask = np.zeros((N,N), dtype=bool)
for k in range(7):
    stem_x = .50 + (k-3)*.020 + np.maximum(0,yy-.12)**1.7*(k-3)*.080
    mask |= (np.abs(xx-stem_x)<.003)&(yy>.07)&(yy<.80-abs(k-3)*.04)
    for v in [.30,.48,.63]:
        center_x = .50+(k-3)*.020+(v-.12)**1.7*(k-3)*.080
        dx = xx-center_x-(yy-v)*(.9 if k%2 else -.9)
        mask |= (dx*dx/.009**2+(yy-v)**2/.057**2<1)
floral[mask] = (.17,.28,.265)
floraltex = image('frosted-reed-pattern-albedo', floral)

wall = material('Warm_white_plaster', (.72,.71,.68), .88, base=plastertex)
paint = material('Aged_ivory_painted_trim', (.69,.67,.59), .43)
white = material('White_satin_painted_metal', (.79,.78,.73), .32, .05)
wood = material('Red_brown_floorboards', (.14,.048,.026), .32, base=woodtex, normal=woodnorm)
wood['web_userData'] = json.dumps({'surfaceFinish':'red-brown satin timber, scene-independent grain'})
skirt = material('Dark_red_brown_skirt',(.10,.038,.022),.43)
joint = material('Dark_wood_joint',(.035,.021,.014),.82)
stone = material('Balcony_mosaic_tile',(.42,.32,.23),.63,base=stonetex)
brick = material('Balcony_brick_pattern_tile',(.43,.19,.11),.73,base=bricktex)
blue = material('Muted_teal_radiator_stripes',(.025,.25,.31),.4,.06)
dark = material('Dark_metal_and_gaskets',(.018,.022,.025),.48,.2)
steel = material('Brushed_silver_hardware',(.51,.55,.58),.24,.88)
glass = material('Clear_window_glass',(.74,.84,.84),.085,alpha=.16,props={'transparent':True,'opacity':.16,'depthWrite':False,'side':2})
frosted = material('Reed_pattern_frosted_glass',(.47,.61,.6),.84,base=floraltex,alpha=.88,props={'transparent':True,'opacity':.88,'depthWrite':False,'side':2})
cloth = material('Grey_woven_curtain',(.175,.174,.169),.92,base=clothtex,normal=clothnorm,props={'side':2})
cloth['web_userData'] = json.dumps({'surfaceFinish':'grey woven opaque cloth','curtainBacklight':True})
bs = next(n for n in cloth.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Sheen Weight'].default_value = .24
bs.inputs['Sheen Roughness'].default_value = .82
lamp = material('Downlight_diffuser',(.86,.83,.72),.35)
bs = next(n for n in lamp.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Emission Color'].default_value = (1,.86,.63,1)
bs.inputs['Emission Strength'].default_value = .22
lamp['web_props'] = json.dumps({'emissive': '#fff0d3', 'emissiveIntensity': .22})


def box(name, pos, size, mat, bevel=.003, tags=None, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=bp(pos))
    o = own(bpy.context.object, name, tags)
    o.dimensions = (size[0],size[2],size[1])
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        md=o.modifiers.new('Small manufactured edge radius','BEVEL')
        md.width=min(bevel,min(size)*.22)
        md.segments=3
        bpy.ops.object.modifier_apply(modifier=md.name)
        for poly in o.data.polygons:
            poly.use_smooth = poly.area < min(size)**2
        weighted=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
        weighted.keep_sharp=True
        bpy.ops.object.modifier_apply(modifier=weighted.name)
    if parent:
        world=o.matrix_world.copy()
        o.parent=parent
        o.matrix_world=world
    return o


def uv_project(o, axis='auto', scale=1, shift=(0,0)):
    mesh=o.data
    uv=mesh.uv_layers.active or mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        a=axis
        if a=='auto':
            a=('yz','xz','xy')[max(range(3),key=lambda i:abs(poly.normal[i]))]
        for li in poly.loop_indices:
            v=o.matrix_world @ mesh.vertices[mesh.loops[li].vertex_index].co
            pairs={'xy':(v.x,-v.y),'xz':(v.x,v.z),'yz':(-v.y,v.z)}
            uv.data[li].uv=(pairs[a][0]*scale+shift[0],pairs[a][1]*scale+shift[1])


def tube(name, a, b, radius, mat, vertices=16, tags=None, parent=None):
    aa,bb=Vector(bp(a)),Vector(bp(b))
    delta=bb-aa
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=delta.length,location=(aa+bb)/2)
    o=own(bpy.context.object,name,tags)
    o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    o.data.materials.append(mat)
    for poly in o.data.polygons:
        poly.use_smooth=len(poly.vertices)==4
    if parent:
        world=o.matrix_world.copy();o.parent=parent;o.matrix_world=world
    return o


def empty(name, pos=(0,0,0), interaction=None):
    o=bpy.data.objects.new('C43_'+name,None)
    coll.objects.link(o);o.location=bp(pos)
    bpy.context.view_layer.update()
    if interaction:o['c43_interaction']=json.dumps(interaction)
    return o


def combine(name, objects, tags=None):
    if not objects:return
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join()
    o=objects[0];o.name='C43_'+name;o['web_tags']=json.dumps(tags or {})
    return o


r,b=P['room'],P['balcony']
w,d,h,t=r['width'],r['depth'],r['height'],r['wall']
cx=r['centerX'];left=cx-w/2;right=cx+w/2
ol,orr=b['openingLeft'],b['openingRight']
entry=P['entry'];dl=entry['centerX']-entry['width']/2;dr=entry['centerX']+entry['width']/2

# Surfaces stay at the approved whitebox positions. The wood surface is y=0.
box('Floor_Substrate',(cx,-.074,d/2),(w,.112,d),joint,0)
boards=[]
count=33
board_width=w/count
for i in range(count):
    xx=left+(i+.5)*board_width
    start=-((i*7)%9)*.103
    j=0
    while start<d:
        end=min(d,start+.91)
        z0=max(0,start)
        if end-z0>.005:
            ob=box('Floor_Board_%02d_%02d'%(i,j),(xx,-.009,(z0+end)/2),(board_width-.0014,.018,end-z0-.0012),wood,.0009)
            uv_project(ob,'xy',1.0,(i*.137,j*.29))
            boards.append(ob)
        start+=.91;j+=1
combine('Floor_RedBrown_Boards',boards)
o=box('Floor_Balcony_Tile',(cx,-.025,-b['depth']/2),(w,.08,b['depth']),stone,.002)
uv_project(o,'xy',1.8)
box('Wall_Left',(left-t/2,h/2,d/2),(t,h,d),wall,.003)
box('Wall_Right',(right+t/2,h/2,d/2),(t,h,d),wall,.003,{'cutaway':True})
for name,a,c in [('Left',left,dl),('Right',dr,right)]:
    box('Wall_Entry_'+name,((a+c)/2,h/2,d+t/2),(c-a,h,t),wall,.003,{'cutaway':True})
box('Wall_Entry_Header',(entry['centerX'],(h+entry['height'])/2,d+t/2),(entry['width'],h-entry['height'],t),wall,.003,{'cutaway':True})
box('Ceiling_Main',(cx,h+.065,d/2),(w+.24,.13,d+.24),wall,.004,{'ceilings':True})
border=[]
for x in [left+.14,right-.14]:border.append(box('Ceiling_SideBorder',(x,h-.1,d/2),(.28,.2,d),wall,.004))
for z in [.14,d-.14]:border.append(box('Ceiling_CrossBorder',(cx,h-.1,z),(w-.56,.2,.28),wall,.004))
combine('Ceiling_Dropped_Perimeter',border,{'ceilings':True})
# Fine upper reveal inside the shallow tray, dark gap is real recessed geometry.
reveal=[]
for x in [left+.28,right-.28]:reveal.append(box('Ceiling_Reveal',(x,h-.028,d/2),(.012,.018,d-.56),wall,.001))
for z in [.28,d-.28]:reveal.append(box('Ceiling_Reveal',(cx,h-.028,z),(w-.56,.018,.012),wall,.001))
combine('Ceiling_Tray_Reveal',reveal,{'ceilings':True})
for name,a,c in [('Left',left,ol),('Right',orr,right)]:
    box('Wall_Balcony_Pier_'+name,((a+c)/2,h/2,-.065),(c-a,h,.13),wall,.002)
box('Wall_Balcony_Lintel',((ol+orr)/2,2.575,-.065),(orr-ol,.35,.13),wall,.003,{'ceilings':True})
box('Threshold_Dark_Stone',((ol+orr)/2,.022,0),(orr-ol,.044,.15),dark,.003)
box('Wall_Balcony_Left',(left-t/2,h/2,-b['depth']/2),(t,h,b['depth']),wall,.003)
box('Ceiling_Balcony',(cx,h+.05,-b['depth']/2),(w+.24,.1,b['depth']),wall,.003,{'ceilings':True})
frontpar=box('Wall_Balcony_Brick_Parapet',(cx,b['sill']/2,-b['depth']-.06),(w,b['sill'],.12),brick,.002)
uv_project(frontpar,'xz',1.3)
returnpar=box('Wall_Balcony_Brick_Return',(right+.06,b['sill']/2,-b['depth']/2),(.12,b['sill'],b['depth']),brick,.002,{'cutaway':True})
uv_project(returnpar,'yz',1.3)
box('Wall_Balcony_Window_Header',(cx,(h+b['windowTop'])/2,-b['depth']-.06),(w,h-b['windowTop'],.12),wall,.003,{'ceilings':True})
box('Window_Stone_Sill',(cx,b['sill']+.008,-b['depth']+.01),(w+.035,.028,.16),paint,.007)
box('Window_Return_Stone_Sill',(right-.01,b['sill']+.008,-b['depth']/2),(.16,.028,b['depth']),paint,.007)

skirting=[]
for x in [left+.009,right-.009]:skirting.append(box('Skirting',(x,.045,d/2),(.018,.09,d),skirt,.002))
for a,c in [(left,dl),(dr,right)]:skirting.append(box('Skirting',((a+c)/2,.045,d-.009),(c-a,.09,.018),skirt,.002))
for a,c in [(left,ol),(orr,right)]:skirting.append(box('Skirting',((a+c)/2,.045,.009),(c-a,.09,.018),skirt,.002))
combine('Skirting_Dark_Timber',skirting)

# Window PVC frame, internal gaskets and individual clear panes.
frames=[];gaskets=[];glassobjects=[]
xs=[left,left+w/3,left+2*w/3,right]
ys=[b['sill'],1.98,b['windowTop']]
for x in xs:frames.append(box('Window_Mullion',(x,(ys[0]+ys[-1])/2,-b['depth']),(.045,ys[-1]-ys[0],.075),white,.003))
for y in ys:frames.append(box('Window_Rail',(cx,y,-b['depth']),(w,.045,.075),white,.003))
for i in range(3):
    for j in range(2):
        x0,x1=xs[i]+.024,xs[i+1]-.024;y0,y1=ys[j]+.024,ys[j+1]-.024
        for x in (x0,x1):gaskets.append(box('Window_Gasket',(x,(y0+y1)/2,-b['depth']-.019),(.006,y1-y0,.009),dark,.001))
        for y in (y0,y1):gaskets.append(box('Window_Gasket',((x0+x1)/2,y,-b['depth']-.019),(x1-x0,.006,.009),dark,.001))
        glassobjects.append(box('Window_Glass_%d_%d'%(i,j),((x0+x1)/2,(y0+y1)/2,-b['depth']-.023),(x1-x0-.003,y1-y0-.003,.006),glass,0,{'glass':True}))
        if j==0:
            frames.append(box('Window_Sash_Rail',((x0+x1)/2,y0+.014,-b['depth']+.012),(x1-x0,.024,.055),white,.002))
            box('Window_Latch_%d'%i,(x1-.023,1.45,-b['depth']+.047),(.018,.085,.02),paint,.005,{'noCollision':True})
for z in [-b['depth'],-.05]:frames.append(box('Window_Return_Post',(right,(ys[0]+ys[-1])/2,z),(.075,ys[-1]-ys[0],.045),white,.003))
for y in ys:frames.append(box('Window_Return_Rail',(right,y,-b['depth']/2),(.075,.045,b['depth']),white,.003))
for j in range(2):
    glassobjects.append(box('Window_Return_Glass_%d'%j,(right+.018,(ys[j]+ys[j+1])/2,-b['depth']/2),(.006,ys[j+1]-ys[j]-.049,b['depth']-.055),glass,0,{'glass':True}))
combine('Window_White_Frames',frames)
combine('Window_Dark_Gaskets',gaskets,{'noCollision':True})
# Exterior safety bars visible in V01; no landscape or architectural invention.
bars=[]
for x in np.arange(left+.10,right,.17):bars.append(tube('Window_SafetyBar',(x,.91,-b['depth']-.10),(x,2.42,-b['depth']-.10),.005,steel,10))
for y in [1.12,1.55,1.98,2.36]:bars.append(tube('Window_SafetyRail',(left,y,-b['depth']-.10),(right,y,-b['depth']-.10),.006,steel,12))
combine('Window_Exterior_SafetyBars',bars)
tube('Clothes_Rail',(left+.07,2.27,-.85),(right-.07,2.27,-.85),.0125,steel,24)

# Open-backed radiator enclosure: narrow slats are real rectangular sections.
# Rear/top service opening gives the grey curtain continuous free travel.
rad=[]
for x in [.301,1.379]:rad.append(box('Radiator_Side',(x,.49,.204),(.022,.94,.116),paint,.002))
rad.append(box('Radiator_Base_Front',(.84,.051,.204),(1.1,.062,.116),skirt,.003))
rad.append(box('Radiator_Base_Rear',(.84,.051,-.0875),(1.1,.062,.065),skirt,.003))
for y in [.103,.932]:rad.append(box('Radiator_Frame',(.84,y,.254),(1.10,.031,.025),paint,.002))
for x in np.linspace(.329,1.351,67):rad.append(box('Radiator_VerticalSlat',(float(x),.513,.259),(.0085,.802,.018),paint,.0015))
combine('Radiator_White_Vertical_Grille',rad)
for i,y in enumerate([.29,.69]):box('Radiator_Teal_Crossbar_%d'%i,(.84,y,.271),(1.1,.12,.025),blue,.002)
# The cap keeps the approved front edge and outer width; a rear cloth slot is
# a hidden, explicitly inferred construction, avoiding impossible penetration.
box('Radiator_Cap_Front',(.84,.99,.215),(1.17,.045,.13),paint,.007)
box('Radiator_Cap_RearSupport',(.84,.99,-.0875),(1.17,.045,.065),paint,.004)
box('Radiator_Inner_Shadow',(.84,.505,.204),(1.044,.81,.015),dark,.001)
parts=[]
for x in [.31,.62,1.07,1.38]:parts.append(box('Partition_Upright',(x,1.70,-.075),(.055,1.42,.065),paint,.003))
for x in [.465,1.225]:
    for y in [1.085,2.315]:parts.append(box('Partition_Panel_Rail',(x,y,-.075),(.255,.027,.065),paint,.002))
    o=box('Partition_Frosted_Plant_Panel_'+str(x),(x,1.70,-.075),(.255,1.20,.012),frosted,.001,{'glass':True})
    # One upright motif over each panel; mirrored back faces stay readable.
    uv=o.data.uv_layers.active
    for po in o.data.polygons:
        for li in po.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=(v.x/.255+.5,v.z/1.20+.5)
for y in np.linspace(1.13,2.39,17):parts.append(box('Partition_Teal_Horizontal',(.845,float(y),-.075),(.40,.024,.044),blue,.0018))
combine('Partition_Painted_Frame',parts)

# Entry, a white panel door and brushed lock hardware. The hinge starts in the
# approved open position, with closed-space dimensions retained for animation.
for x in [dl-.019,dr+.019]:box('Door_Jamb',(x,1.06,d+.015),(.038,2.12,.15),paint,.004,{'cutaway':True})
box('Door_Jamb_Header',(entry['centerX'],2.116,d+.015),(entry['width']+.076,.032,.15),paint,.004,{'cutaway':True})
doorpivot=empty('Door_Hinge',(dr-.02,0,d-.005),{'id':'entry-door','kind':'hinge','axis':'y','openAngle':-math.pi/2,'audio':'wardrobe','defaultOpen':True})
doorpivot['web_tags']=json.dumps({'cutaway':True})
doorparts=[]
doorparts.append(box('Door_Leaf',(entry['centerX']-.02,1.05,d-.005),(entry['width']-.008,2.10,.04),white,.004,{'cutaway':True},doorpivot))
for y in [.26,1.05,1.87]:
    tube('Door_Hinge_Knuckle',(dr-.02,y-.035,d+.022),(dr-.02,y+.035,d+.022),.009,steel,16,parent=doorpivot)
handleX=dl+.115
box('Door_Lock_Backplate',(handleX,1.005,d-.031),(.046,.255,.01),steel,.008,{'noCollision':True},doorpivot)
tube('Door_Handle_Spindle',(handleX,1.025,d-.034),(handleX,1.025,d-.081),.011,steel,20,parent=doorpivot)
tube('Door_Handle_Lever',(handleX,1.025,d-.077),(handleX+.112,1.025,d-.077),.012,steel,20,parent=doorpivot)
lock=empty('Door_Lock_Pivot',(handleX,.942,d-.045),{'id':'entry-lock','kind':'lock','axis':'z','audio':'lock'})
world=lock.matrix_world.copy();lock.parent=doorpivot;lock.matrix_world=world
box('Door_Thumbturn',(handleX,.942,d-.046),(.034,.012,.013),steel,.004,{'noCollision':True},lock)
doorpivot.rotation_euler.z=-math.pi/2
doorpivot['c43_base_closed_rotation']=json.dumps([0,0,0])

# Small actual switch meshes, no invisible click plane. Placement is inferred
# on the right entry wall because P01/V02 only establish the door hardware.
switchpos=(right-.006,1.26,2.40)
box('Switch_Backplate',switchpos,(.012,.085,.085),white,.005,{'cutaway':True})
switch=empty('Switch_Pivot',(right-.015,1.26,2.40),{'id':'ceiling-switch','kind':'switch','axis':'z','audio':'switch'})
switch['web_tags']=json.dumps({'cutaway':True})
box('Switch_Rocker',(right-.019,1.26,2.40),(.014,.062,.064),paint,.004,{'switches':True},switch)
# A double outlet beside desk seen in P03; details are deliberately unlabelled.
box('Desk_Outlet_Backplate',(left+.009,.78,.90),(.018,.066,.12),white,.004)
for z in [.866,.932]:
    for y in [.772,.798]:box('Desk_Outlet_Slot',(left+.019,y,z),(.002,.012,.004),dark,.0005,{'noCollision':True})

# Recessed perimeter downlights. Mesh fixtures only; main agent owns lighting.
fixtures=[];diffusers=[]
for x,z in [(left+.14,.60),(left+.14,1.45),(left+.14,2.30),(right-.14,.62),(right-.14,1.47),(right-.14,2.32),(-.75,.14),(.45,.14),(-.75,d-.14),(.45,d-.14)]:
    tube('Downlight_Bezel',(x,h-.201,z),(x,h-.185,z),.033,steel,32,tags={'ceilings':True,'lightFixture':True})
    tube('Downlight_Diffuser',(x,h-.203,z),(x,h-.201,z),.025,lamp,32,tags={'ceilings':True,'lightFixture':True})

# Two continuous 2 mm closed-volume cloth meshes, with independently modeled
# sewn edge reinforcement. Gaussian broad folds release naturally below hooks.
curtain=empty('Curtain_Pivot',interaction={'id':'curtain','kind':'curtain','axis':'x','audio':'curtain'})
THICK=.002
TOP=2.400
BOTTOM=.066
cloth_panels=[]


def surface(a,v,side,opened=False,offset=0):
    width=.165 if opened else 1.03
    start=-.63 if side=='Left' else 1.43-width
    x=start+a*width
    x+=.0025*math.sin(a*19+v*3)*(math.sin(math.pi*a)**2)*v
    y=TOP-(TOP-BOTTOM)*v-.004*(math.sin(a*math.tau*5)**2)*(1-v)**10
    y+=.009*math.sin(a*13+.4)*v**6+.003*math.sin(a*31)*v**8
    if opened:
        z=.073+.028*math.cos(a*math.tau*5)+.002*math.sin(a*19+v*4)*v
    else:
        spread=1-math.exp(-v*12)
        z=.085+.004*math.sin(a*9+v*3)*math.sin(math.pi*v)
        for k,c in enumerate([.08,.26,.45,.66,.85]):
            center=c+.015*math.sin(k*1.9+v*2.2)*v
            dep=[.036,.026,.040,.028,.034][k]
            z-=dep*math.exp(-((a-center)/(.034+.019*v))**2)*spread
        z+=.014*math.sin(a*math.tau*5)*(1-spread)
    # Keep cloth away from sill and radiator rear/front supports in every state.
    return (x,y,z+offset)


def cloth_mesh(side):
    nx,ny=120,54
    verts=[];opened=[];uvs=[];faces=[]
    n=(nx+1)*(ny+1)
    for sign in [1,-1]:
        for j in range(ny+1):
            for i in range(nx+1):
                a,v=i/nx,j/ny
                hem=1+.65*(math.exp(-((v-.977)/.015)**2)+math.exp(-((a-.012)/.009)**2)+math.exp(-((a-.988)/.009)**2))
                verts.append(bp(surface(a,v,side,False,sign*THICK*.5*hem)))
                opened.append(bp(surface(a,v,side,True,sign*THICK*.5*hem)))
                uvs.append((a*1.03,v*(TOP-BOTTOM)))
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i
            faces.extend([(k,k+1,k+nx+2,k+nx+1),(n+k,n+k+nx+1,n+k+nx+2,n+k+1)])
    perimeter=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+i for i in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
    for q,k in enumerate(perimeter):
        nxt=perimeter[(q+1)%len(perimeter)]
        faces.append((k,k+n,nxt+n,nxt))
    me=bpy.data.meshes.new('C43_Curtain_'+side+'_ClosedVolume')
    me.from_pydata(verts,[],faces);me.materials.append(cloth);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        p.use_smooth=True
        for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    o=bpy.data.objects.new('C43_Curtain_'+side,me);coll.objects.link(o);o.parent=curtain
    o['web_tags']=json.dumps({'curtainPanels':True,'noCollision':True})
    o['web_userData']=json.dumps({'curtainShapeKey':True,'surface':'grey-curtain','fixedTop':2.40,'fixedSideX':-.63 if side=='Left' else 1.43,'safeWindZ':.012,'safeWindX':.004,'safeWindY':.005})
    o.shape_key_add(name='Basis');key=o.shape_key_add(name='Open')
    for i,p in enumerate(opened):key.data[i].co=p
    cloth_panels.append(o)
    # Rings carry their own shared morph mesh; rings remain on the rail.
    ringverts=[];ringopen=[];ringfaces=[]
    for a in np.linspace(.016,.984,11):
        center=surface(float(a),0,side,False);openctr=surface(float(a),0,side,True)
        base=len(ringverts)
        for j in range(20):
            angle=j/20*math.tau
            for k in range(8):
                phi=k/8*math.tau
                radius=.025+.0023*math.cos(phi)
                delta=(.0023*math.sin(phi),radius*math.cos(angle),radius*math.sin(angle))
                for arr,ctr in [(ringverts,center),(ringopen,openctr)]:
                    arr.append(bp((ctr[0]+delta[0],2.425+delta[1],.072+delta[2])))
        for j in range(20):
            for k in range(8):ringfaces.append(tuple(base+jj*8+kk for jj,kk in [(j,k),((j+1)%20,k),((j+1)%20,(k+1)%8),(j,(k+1)%8)]))
    me=bpy.data.meshes.new('C43_Curtain_'+side+'_Rings');me.from_pydata(ringverts,[],ringfaces);me.materials.append(white)
    for p in me.polygons:p.use_smooth=True
    o=bpy.data.objects.new('C43_Curtain_'+side+'_Rings',me);coll.objects.link(o);o.parent=curtain
    o['web_tags']=json.dumps({'curtainPanels':True,'noCollision':True})
    o['web_userData']=json.dumps({'curtainShapeKey':True,'curtainRings':True})
    o.shape_key_add(name='Basis');key=o.shape_key_add(name='Open')
    for i,p in enumerate(ringopen):key.data[i].co=p


cloth_mesh('Left');cloth_mesh('Right')
tube('Curtain_Rod',(-.71,2.435,.072),(1.51,2.435,.072),.012,white,24,tags={'noCollision':True})
for x in [-.68,1.48]:
    tube('Curtain_Rod_Bracket',(x,2.435,-.004),(x,2.435,.072),.009,white,16,tags={'noCollision':True})
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.021,location=bp((x+(-.03 if x<0 else .03),2.435,.072)))
    own(bpy.context.object,'Curtain_Rod_Finial',{'noCollision':True}).data.materials.append(white)

# Ensure usable UVs everywhere; box texture UVs and cloth morph UVs stay intact.
for o in coll.all_objects:
    if o.type=='MESH' and not o.data.uv_layers:
        uv_project(o)
bpy.context.view_layer.update()
for im in bpy.data.images:
    if im.source=='FILE' or im.filepath:
        im.filepath=bpy.path.relpath(im.filepath,start=str(OUT))

# All component diagnostics run inside Blender, including 41 morph samples.
def bounds(o):
    coords=[o.matrix_world@Vector(v) for v in o.bound_box]
    return {'min':[min(v[i] for v in coords) for i in range(3)],'max':[max(v[i] for v in coords) for i in range(3)]}

samples=[]
for amount in np.linspace(0,1,41):
    positions=[]
    for o in cloth_panels:
        a=o.data.shape_keys.key_blocks['Basis'];bkey=o.data.shape_keys.key_blocks['Open']
        arr=np.array([tuple(a.data[i].co.lerp(bkey.data[i].co,float(amount))) for i in range(len(a.data))])
        positions.append(arr)
    ar=np.concatenate(positions)
    # Convert Blender coordinates back to web; all gaps use physical surfaces.
    web=ar[:,[0,2,1]];web[:,2]*=-1
    y=web[:,1];z=web[:,2];x=web[:,0]
    rightmask=(x>=.29)&(x<=1.425)
    capmask=rightmask&(y>.9675)&(y<1.0125)
    partitionmask=rightmask&(y>1.00)&(y<2.41)
    samples.append({'open':float(amount),'minY':float(y.min()),'minZ':float(z.min()),'maxZ':float(z.max()),'openingEdgeGap':float(min(x.min()-ol,orr-x.max())),
                    'capFrontGap':float(.15-z[capmask].max()) if capmask.any() else None,
                    'capRearGap':float(z[capmask].min()+.055) if capmask.any() else None,
                    'partitionFrontGap':float(z[partitionmask].min()+.0425) if partitionmask.any() else None,
                    'radiatorRearInnerGap':float(.1965-z[rightmask].max())})
assert min(s['minY'] for s in samples)>.049, 'Hem must clear 44 mm threshold plus 5 mm wind allowance'
assert min(s['openingEdgeGap'] for s in samples)>.015
assert min(s['capFrontGap'] for s in samples if s['capFrontGap'] is not None)>.04
assert min(s['partitionFrontGap'] for s in samples if s['partitionFrontGap'] is not None)>.06
triangles=0;meshes=0
for o in coll.all_objects:
    if o.type=='MESH':
        meshes+=1;o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
        assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
        assert o.data.uv_layers
assert triangles<150000,(triangles,'architecture triangle budget exceeded')
report={'revision':'architecture01','layout':P['parentRevision'],'objects':len(coll.all_objects),'meshObjects':meshes,'triangles':triangles,'materials':len(bpy.data.materials),'images':len(bpy.data.images),
        'roomWebBounds':{'left':left,'right':right,'depth':d,'height':h,'balconyDepth':P['balcony']['depth']},'curtainSamples':samples,
        'sourceReuse':{'room':'yongwang-jiayuan','revision':'sunview34','mode':'method reuse, independent geometry and images','objectsInspected':['ivory-jacquard-curtain','photo-guided-curtain-assembly']},
        'inferredHiddenConstruction':['radiator open rear and top cloth service slot','door hinge direction and lock thumbturn','switch exact position','balcony left wall extent'],
        'lightObjects':len([o for o in coll.all_objects if o.type=='LIGHT'])}
(REPORT/'geometry-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Courtyard43-architecture.blend'))
result={'saved':str(OUT/'Courtyard43-architecture.blend'),'objects':len(coll.all_objects),'triangles':triangles,'images':len(bpy.data.images),
        'curtainSampleCount':len(samples),'minCapFrontGap':min(s['capFrontGap'] for s in samples if s['capFrontGap'] is not None),
        'minPartitionGap':min(s['partitionFrontGap'] for s in samples if s['partitionFrontGap'] is not None)}
