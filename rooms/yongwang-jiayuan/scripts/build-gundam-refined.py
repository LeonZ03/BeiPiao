"""Reference-led articulated Mk-II shelf miniature. Blender authored solid meshes.

All armor has volume, corrected outward normals and small molded edge radii.
The material batches retain the kit's separate armor, recessed frame and panel lines.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=(Path(__file__).resolve().parents[3] / 'room-site')
SOURCE=ROOT.parent/'rooms/yongwang-jiayuan/assets/shelf-gundam'
OUT=ROOT/'dist/assets/shelf-gundam'
SOURCE.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
PALETTE={
 'armor':((.61,.67,.66,1),.03,.33),
 'armorLight':((.76,.79,.76,1),.025,.30),
 'edgeGrey':((.21,.24,.29,1),.22,.34),
 'frame':((.052,.064,.084,1),.28,.32),
 'navy':((.019,.028,.047,1),.09,.29),
 'red':((.66,.018,.012,1),.025,.30),
 'yellow':((1,.58,.016,1),.03,.30),
 'ventShade':((.43,.24,.010,1),.05,.43),
 'green':((.025,.60,.22,1),.18,.21),
 'gunmetal':((.105,.124,.162,1),.20,.33),
 'panel':((.17,.20,.21,1),0,.51),
}
mats={}; objects=[]
for name,(rgba,metal,rough) in PALETTE.items():
 m=bpy.data.materials.new(name);m.diffuse_color=rgba;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=rgba
 bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 mats[name]=m

def finish(o,mat,bevel=.006,smooth=False):
 o.data.materials.append(mats[mat])
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 if smooth:
  for f in o.data.polygons:f.use_smooth=True
 if bevel:
  mod=o.modifiers.new('injection-molded edge radius','BEVEL');mod.width=bevel;mod.segments=3
  mod.limit_method='ANGLE';mod.harden_normals=True
  n=o.modifiers.new('weighted planar normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=40
 objects.append(o);return o

def mesh(name,verts,faces,mat='armor',bevel=.006,smooth=False):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
 ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob)
 return finish(ob,mat,bevel,smooth)

def box(name,loc,size,mat='armor',bevel=.006,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 return finish(o,mat,bevel)

def prism(name,points,depth,mat='armor',bevel=.006,y=0):
 n=len(points);v=[(x,y-depth/2,z)for x,z in points]+[(x,y+depth/2,z)for x,z in points]
 f=[tuple(range(n)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n)]
 return mesh(name,v,f,mat,bevel)

def ring(w,d,cut=.2):
 return [(-w/2+cut*w,-d/2),(w/2-cut*w,-d/2),(w/2,-d/2+cut*d),(w/2,d/2-cut*d),
         (w/2-cut*w,d/2),(-w/2+cut*w,d/2),(-w/2,d/2-cut*d),(-w/2,-d/2+cut*d)]

def loft(name,sections,mat='armor',bevel=.006):
 # (z, centerX, centerY, width, depth); octagonal cross sections.
 v=[]
 for z,x,y,w,d in sections:v.extend((x+a,y+b,z)for a,b in ring(w,d))
 n=8;f=[tuple(range(n)),tuple(range(len(v)-n,len(v)))]
 for k in range(len(sections)-1):
  for j in range(n):f.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
 return mesh(name,v,f,mat,bevel)

def cylinder(name,loc,r,depth,mat='frame',axis='Z',vertices=24):
 rot={'X':(0,math.pi/2,0),'Y':(math.pi/2,0,0),'Z':(0,0,0)}[axis]
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc,rotation=rot)
 o=bpy.context.object;o.name=name;return finish(o,mat,min(.003,r*.1),True)

def rod(name,a,b,r,mat='frame',vertices=16):
 a,b=Vector(a),Vector(b);o=cylinder(name,(a+b)/2,r,(b-a).length,mat,vertices=vertices)
 o.rotation_mode='QUATERNION';o.rotation_quaternion=Vector((0,0,1)).rotation_difference((b-a).normalized());return o

def line(name,pts,r=.0013,mat='panel'):
 # Real, very shallow seam geometry; no thick black cartoon outlines.
 for i in range(len(pts)-1):rod(name+str(i),pts[i],pts[i+1],r,mat,8)

def ball(name,loc,scale,mat='frame'):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,mat,0,True)

def transform_parts(start,matrix):
 for ob in objects[start:]:ob.matrix_world=matrix@ob.matrix_world

def oriented_parts(start,a,b):
 a,b=Vector(a),Vector(b);q=Vector((0,0,1)).rotation_difference((b-a).normalized())
 transform_parts(start,Matrix.Translation(a)@q.to_matrix().to_4x4())

def joint(name,loc,r=.075,width=.14):
 cylinder(name+' axle',loc,r,width,'frame','X')
 for s in (-1,1):
  cylinder(name+' endcap',(loc[0]+s*width/2,loc[1],loc[2]),r*.72,.009,'edgeGrey','X')
  cylinder(name+' hub',(loc[0]+s*(width/2+.005),loc[1],loc[2]),r*.32,.011,'gunmetal','X')

# Splayed legs with long, tapered lower legs; the knee frame remains visible.
for s in (-1,1):
 x=s*.45
 start=len(objects)
 # Toe outline in horizontal plane, then angled top. The heel is much higher.
 xy=[(-.137,-.35),(.137,-.35),(.185,-.25),(.173,.17),(.12,.24),(-.12,.24),(-.173,.17),(-.185,-.25)]
 verts=[(a,b,.005)for a,b in xy]+[(a,b,.092+(.062 if b>.05 else 0))for a,b in xy]
 mesh('red long foot sole',verts,[tuple(range(8)),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8)for i in range(8)],'red',.012)
 # Main toe slopes down toward the viewer and wraps a dark exposed instep.
 verts=[(-.14,-.302,.088),(.14,-.302,.088),(.147,.16,.13),(-.147,.16,.13),
        (-.12,-.295,.145),(.12,-.295,.145),(.128,.12,.277),(-.128,.12,.277)]
 mesh('sloping molded toe',verts,[(0,1,2,3),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'armor',.009)
 box('foot open instep',(0,-.055,.241),(.14,.255,.035),'edgeGrey',.009,(-.28,0,0))
 for a in (-.104,.104):box('toe trim',(a,-.156,.211),(.031,.24,.026),'armorLight',.004,(-.28,0,0))
 line('toe molded seam',[(-.125,-.257,.163),(0,-.268,.163),(.125,-.257,.163)],.0013)
 # Low cuff is a separate band, not a solid slab over the foot.
 for a in (-.122,.122):box('ankle cuff side',(a,.045,.286),(.055,.20,.072),'armor',.008)
 box('ankle cuff brow',(0,-.069,.285),(.27,.041,.066),'armorLight',.006,(-.16,0,0))
 joint('ankle hinge',(0,.03,.337),.077,.19)
 for a in (-.06,-.02,.02,.06):rod('ankle tendon',(a,.016,.30),(a,.041,.407),.011,'gunmetal',12)
 transform_parts(start,Matrix.Translation((x,0,0))@Matrix.Rotation(-s*.115,4,'Z'))
 def cx(z):return s*(.50-.117*z)
 loft('sculpted calf',[(.39,cx(.39),.035,.27,.27),(.48,cx(.48),.042,.32,.31),(.67,cx(.67),.045,.345,.335),(.87,cx(.87),.035,.295,.29),(.99,cx(.99),.025,.235,.245)],'armor',.012)
 # Front shin wrap with asymmetrical slopes and an inset mechanical ankle gap.
 xx=cx(.65)
 prism('shin wrap',[(xx-.133,.385),(xx-.16,.53),(xx-.124,.82),(xx-.07,.956),(xx+.07,.956),(xx+.124,.82),(xx+.145,.48),(xx+.126,.395)],.040,'armorLight',.007,-.128)
 prism('raised tapered shin spine',[(xx-.038,.41),(xx+.043,.41),(xx+.049,.80),(xx+.026,.887),(xx-.026,.887),(xx-.05,.80)],.025,'armor',.005,-.157)
 line('shin panel seam',[(xx-.072,-.151,.81),(xx-.091,-.151,.836),(xx-.074,-.151,.898),(xx+.058,-.151,.898),(xx+.086,-.151,.851)],.0014)
 line('shin center seam',[(xx+.033,-.173,.465),(xx+.033,-.173,.76),(xx+.012,-.173,.79)],.0011)
 # Side thruster detail sunk into the calf shell.
 box('calf side dark recess',(xx+s*.164,.028,.646),(.012,.094,.15),'ventShade',.005)
 box('calf golden insert',(xx+s*.173,.018,.644),(.012,.057,.122),'yellow',.004)
 joint('knee', (cx(1.07),.007,1.077),.094,.226)
 box('knee articulation visible',(cx(1.07),-.106,1.071),(.145,.078,.135),'frame',.012,(-.11,0,0))
 for a in (-.042,0,.042):box('knee hinge ridges',(cx(1.07)+a,-.150,1.07),(.015,.014,.09),'edgeGrey',.003,(-.15,0,0))
 loft('upper thigh armor',[(1.17,cx(1.17),.027,.231,.238),(1.45,cx(1.45),.029,.267,.266),(1.67,cx(1.67),.042,.31,.30)],'armorLight',.012)
 prism('thigh front armor panel',[(cx(1.2)-.081,1.19),(cx(1.2)+.081,1.19),(cx(1.60)+.092,1.59),(cx(1.60)-.092,1.59)],.028,'armor',.005,-.116)
 line('thigh split seam',[(cx(1.25)-.086,-.132,1.23),(cx(1.50)-.099,-.132,1.50)],.0011)
 joint('hip',(s*.258,.025,1.71),.11,.18)

# Waist and four hanging armor leaves, with photographed vent and panel layout.
loft('pelvis',[(1.55,0,.04,.39,.27),(1.79,0,.04,.51,.30)],'frame',.015)
cylinder('waist rotating ring',(0,.025,1.878),.167,.17,'edgeGrey')
box('belt',(0,-.025,1.838),(.46,.30,.10),'frame',.014)
for s in (-1,1):
 pts=[(s*.035,1.854),(s*.20,1.864),(s*.297,1.738),(s*.321,1.47),(s*.238,1.46),(s*.101,1.514)]
 prism('front skirt shaped armor',pts,.069,'armorLight',.008,-.185)
 line('skirt long seam',[(s*.19,-.224,1.819),(s*.205,-.224,1.745),(s*.235,-.224,1.70),(s*.249,-.224,1.505)],.0012)
 line('skirt engraved corner',[(s*.104,-.224,1.555),(s*.137,-.224,1.555),(s*.146,-.224,1.60),(s*.179,-.224,1.62)],.0012)
 # Narrow inset slotted louver instead of thick black decorative line.
 box('skirt vent bed',(s*.199,-.225,1.76),(.028,.003,.089),'panel',.001)
 for i in range(7):box('skirt fine louvers',(s*.199,-.23,1.723+i*.012),(.026,.003,.004),'armor',.001)
 prism('side skirt',[(s*.285,1.845),(s*.445,1.789),(s*.502,1.58),(s*.379,1.51),(s*.302,1.69)],.208,'armor',.008,.034)
 prism('rear skirt',[(s*.04,1.81),(s*.295,1.82),(s*.365,1.57),(s*.09,1.54)],.046,'armor',.006,.221)
prism('front waist middle', [(-.050,1.85),(.05,1.85),(.068,1.686),(0,1.64),(-.068,1.686)],.076,'armorLight',.006,-.223)
box('waist small slot',(0,-.264,1.78),(.009,.004,.044),'panel',.001)

# Torso has tapered sides, recessed chest and a red projecting cockpit keel.
loft('torso silhouette',[(1.925,0,.020,.485,.31),(2.06,0,.015,.605,.34),(2.27,0,.007,.70,.36),(2.37,0,.015,.58,.29)],'navy',.017)
for s in (-1,1):
 prism('dark chest flank',[(s*.083,2.32),(s*.31,2.31),(s*.364,2.22),(s*.277,1.999),(s*.082,1.947)],.068,'navy',.009,-.172)
 # Gold vent housing follows an irregular trapezoid, with dark recess and gold slats.
 pts=[(s*.121,2.281),(s*.265,2.275),(s*.301,2.236),(s*.288,2.12),(s*.131,2.11),(s*.115,2.134)]
 prism('gold chest vent rim',pts,.033,'yellow',.008,-.219)
 pts=[(s*.135,2.258),(s*.257,2.255),(s*.274,2.23),(s*.268,2.135),(s*.14,2.131)]
 prism('recess inside gold vent',pts,.004,'ventShade',.003,-.239)
 for i in range(4):box('molded vent slat',(s*.204,-.244,2.15+i*.026),(.123,.012,.009),'yellow',.003, (0,s*.018,0))
 box('chest clavicle',(s*.177,-.127,2.376),(.23,.083,.048),'armor',.005)
 box('chest sensor frame',(s*.334,-.187,2.348),(.029,.025,.065),'frame',.003)
 box('chest green sensor',(s*.334,-.203,2.35),(.013,.009,.041),'green',.002)
 line('chest molded side seam',[(s*.30,-.21,2.076),(s*.27,-.21,2.041),(s*.163,-.211,2.013)],.0013,'edgeGrey')
prism('red cockpit keel',[(-.047,2.297),(.047,2.297),(.059,2.075),(.045,1.958),(-.008,1.918),(-.054,1.967)],.10,'red',.008,-.205)
box('cockpit stepped panel',(0,-.261,2.129),(.055,.01,.181),'red',.004)
line('cockpit molded seam',[(-.029,-.27,2.245),(-.029,-.27,2.081),(.018,-.27,2.071)],.0011,'ventShade')
box('collar gold',(0,-.002,2.394),(.235,.185,.038),'yellow',.012)
cylinder('neck',(0,.009,2.435),.061,.104,'frame')

# Compact helmet: curved polygon shell, recessed eyes, angular nose/mouth/chin.
start=len(objects)
loft('helmet main shell',[(2.45,0,.026,.25,.245),(2.52,0,.029,.324,.273),(2.69,0,.033,.296,.261),(2.739,0,.025,.21,.218)],'armorLight',.012)
for s in (-1,1):
 # cheek guards surround the face opening, preserving a fine facial silhouette.
 prism('helmet side cheek',[(s*.089,2.657),(s*.144,2.678),(s*.168,2.603),(s*.152,2.48),(s*.113,2.47),(s*.075,2.546)],.106,'armor',.006,-.07)
 box('temple equipment pod',(s*.182,.015,2.588),(.064,.154,.171),'edgeGrey',.010)
 cylinder('temple pod round end',(s*.216,-.025,2.626),.037,.016,'frame','X')
 for i in range(5):box('helmet cheek louver',(s*.128,-.133,2.52+i*.02),(.038,.011,.006),'edgeGrey',.001)
 # eye forms a thin slanted trapezoid rather than a full green visor.
 prism('eye socket',[(s*.01,2.64),(s*.117,2.66),(s*.108,2.598),(s*.027,2.602)],.025,'frame',.002,-.136)
 prism('green eye',[(s*.03,2.626),(s*.10,2.641),(s*.096,2.62),(s*.032,2.613)],.005,'green',.001,-.153)
 prism('slanted eyebrow',[(s*.008,2.66),(s*.118,2.686),(s*.138,2.669),(s*.015,2.638)],.036,'armorLight',.003,-.141)
 # Thin swept V-fin, tapered to a fine point.
 prism('gold V fin',[(s*.025,2.695),(s*.075,2.727),(s*.338,2.879),(s*.128,2.663),(s*.056,2.667)],.012,'yellow',.002,-.139)
# Faceted face mask comes forward toward the nose; cheeks angle back.
v=[(-.087,-.151,2.595),(.087,-.151,2.595),(.067,-.150,2.492),(-.067,-.15,2.492),
   (-.027,-.202,2.587),(.027,-.202,2.587),(.035,-.194,2.505),(-.035,-.194,2.505)]
mesh('sculpted face mask',v,[(0,1,5,4),(0,4,7,3),(4,5,6,7),(5,1,2,6),(3,7,6,2),(0,3,2,1)],'armorLight',.003)
prism('nose bridge',[(-.023,2.611),(.023,2.611),(.028,2.55),(0,2.537),(-.028,2.55)],.026,'armor',.003,-.205)
for z in (2.524,2.537):box('two mouth vents',(0,-.2,z),(.048,.005,.004),'frame',.001)
prism('small red chin',[(-.029,2.507),(.029,2.507),(.037,2.478),(0,2.447),(-.037,2.478)],.043,'red',.005,-.168)
box('helmet crown camera frame',(0,-.044,2.742),(.064,.106,.062),'armor',.004)
box('forehead green lens',(0,-.103,2.759),(.037,.008,.032),'green',.002)
prism('red forehead crest',[(-.034,2.738),(.034,2.738),(.04,2.667),(0,2.64),(-.04,2.667)],.042,'red',.004,-.148)
box('rear helmet camera',(0,.157,2.658),(.067,.012,.058),'edgeGrey',.004)
line('helmet crown seam',[(-.08,-.06,2.741),(-.08,.085,2.731),(-.113,.131,2.677)],.0011)
transform_parts(start,Matrix.Translation((0,0,2.44))@Matrix.Rotation(-.055,4,'Z')@Matrix.Translation((0,0,-2.44)))

# Layered backpack: two saber racks and a narrow communications aerial.
box('backpack core',(0,.271,2.232),(.37,.222,.338),'frame',.014)
for s in (-1,1):
 box('backpack side',(s*.221,.225,2.358),(.117,.15,.231),'gunmetal',.01)
 start=len(objects)
 box('saber rack',(s*.264,.24,2.535),(.073,.075,.37),'edgeGrey',.006,(0,s*.17,0))
 box('saber white back',(s*.282,.245,2.647),(.065,.059,.244),'armor',.005,(0,s*.17,0))
 cylinder('backpack exhaust',(s*.12,.355,2.13),.069,.077,'gunmetal','Y')
rod('communications antenna',(.115,.271,2.4),(.115,.268,2.985),.008,'edgeGrey',12)

def arm_segment(name,a,b,w=.19,d=.18):
 start=len(objects);length=(Vector(b)-Vector(a)).length
 loft(name+' frame',[(0,0,0,w*.71,d*.75),(length,0,0,w*.68,d*.72)],'frame',.008)
 loft(name+' armor',[(.025,0,0,w*.72,d*.81),(.065,0,0,w,d),(length-.04,0,0,w*.89,d*.97),(length-.01,0,0,w*.72,d*.8)],'armorLight',.008)
 prism(name+' front plate',[(-w*.34,.085),(w*.34,.085),(w*.31,length-.05),(-w*.31,length-.05)],.020,'armor',.004,-d/2-.003)
 line(name+' seam',[(-w*.31,-d/2-.015,.09),(-w*.31,-d/2-.015,length-.067)],.0011)
 oriented_parts(start,a,b)

# Sloped pauldrons cap the upper arms; no enormous visible front pivot discs.
for s in (-1,1):
 joint('shoulder hinge',(s*.402,.011,2.265),.098,.176)
 prism('shoulder outer shell',[(s*.431,2.416),(s*.627,2.439),(s*.78,2.372),(s*.761,2.157),(s*.55,2.119),(s*.416,2.227)],.269,'armor',.009,-.001)
 prism('shoulder inset panel',[(s*.469,2.40),(s*.62,2.414),(s*.744,2.36),(s*.726,2.226),(s*.55,2.194),(s*.465,2.269)],.012,'armorLight',.005,-.141)
 line('pauldron panel detail',[(s*.497,-.15,2.38),(s*.526,-.15,2.339),(s*.655,-.15,2.332),(s*.695,-.15,2.302)],.0012)
 cylinder('shoulder small recessed fastener',(s*.535,-.152,2.362),.015,.005,'armor','Y')
 box('shoulder gold edge',(s*.767,-.005,2.306),(.009,.091,.088),'yellow',.002,(0,s*.14,0))
arm_segment('left upper arm',(-.625,.007,2.15),(-.728,-.026,1.936),.181,.19)
joint('left elbow',(-.743,-.026,1.902),.064,.155)
box('left elbow open front',(-.743,-.139,1.92),(.11,.025,.12),'edgeGrey',.005,(0,-.26,0))
arm_segment('left forearm',(-.757,-.024,1.865),(-.874,-.055,1.56),.205,.209)
arm_segment('right upper arm',(.633,.025,2.144),(.784,-.043,1.99),.18,.19)
joint('right elbow',(.801,-.045,1.967),.071,.18)
arm_segment('raised right forearm',(.833,-.081,1.986),(.864,-.138,2.252),.198,.209)

def hand(name,cx,cy,cz):
 box(name+' palm',(cx,cy,cz),(.135,.095,.115),'frame',.011)
 for i in range(4):
  xx=cx+(i-1.5)*.03
  box(name+' knuckle',(xx,cy-.056,cz+.023),(.025,.041,.043),'gunmetal',.006)
  box(name+' curled digit',(xx,cy-.060,cz-.019),(.023,.046,.044),'edgeGrey',.004,(-.33,0,0))
 box(name+' thumb',(cx+.076,cy-.036,cz-.003),(.038,.05,.079),'edgeGrey',.007,(0,-.35,0))
hand('left gripping hand',-.899,-.06,1.499)
hand('right shield hand',.878,-.148,2.318)

# Rifle, authored upright and posed as a single connected assembly through hand.
start=len(objects)
prism('rifle sculpted receiver',[(-.071,.16),(.081,.17),(.09,.60),(.06,.77),(-.026,.81),(-.075,.72),(-.09,.48)],.117,'gunmetal',.006,-.010)
prism('rifle upper receiver bevel',[(-.046,.22),(.054,.23),(.065,.64),(.033,.723),(-.049,.72)],.025,'edgeGrey',.004,-.076)
box('rifle long barrel',(0,0,-.168),(.047,.044,.655),'gunmetal',.003)
box('rifle barrel shroud',(.015,-.005,.069),(.091,.094,.282),'gunmetal',.006)
box('rifle muzzle',(0,0,-.5),(.067,.07,.066),'frame',.004)
box('muzzle open dark slot',(0,-.039,-.512),(.029,.005,.033),'navy',.001)
prism('rifle angled magazine',[(.071,.35),(.205,.376),(.21,.18),(.134,.12),(.081,.17)],.106,'gunmetal',.006,.02)
prism('rifle stock',[(-.035,.733),(.047,.733),(.146,.9),(.081,.946),(-.043,.816)],.078,'gunmetal',.006,.007)
box('rifle scope spine',(-.067,-.023,.635),(.063,.143,.31),'gunmetal',.005)
box('rifle scope lens',(-.070,-.103,.701),(.039,.008,.025),'green',.002)
box('rifle side track',(-.023,-.094,.46),(.016,.01,.368),'frame',.002)
for i in range(4):box('rifle receiver molded ribs',(.054,-.093,.42+i*.045),(.04,.014,.012),'gunmetal',.002)
box('rifle hand grip',(.112,.042,.571),(.157,.07,.058),'frame',.005)
line('rifle trigger guard',[(.081,.089,.614),(.181,.089,.614),(.177,.089,.50),(.08,.089,.5)],.008,'gunmetal')
# The handle is aligned to the hanging hand; muzzle angles down-left as in photo.
rot=Matrix.Rotation(math.radians(24),4,'Y')
grip=rot@Vector((.112,.042,.571));target=Vector((-.899,-.061,1.499))
transform_parts(start,Matrix.Translation(target-grip)@rot)

# Shield raised above right shoulder, photograph's long dark inset and lower tip.
start=len(objects)
prism('shield main thick shell',[(-.154,-.66),(.15,-.64),(.195,-.48),(.19,.64),(.125,.77),(-.144,.77),(-.20,.61),(-.19,-.48)],.066,'armor',.009)
prism('shield inset border',[(-.14,-.12),(.143,-.12),(.155,.58),(.10,.683),(-.1,.683),(-.155,.58)],.030,'armorLight',.005,-.047)
prism('shield navy solid inset',[(-.117,-.10),(.117,-.10),(.132,.567),(.087,.659),(-.089,.659),(-.132,.571)],.017,'navy',.004,-.069)
prism('shield lower armor',[(-.16,-.61),(.138,-.61),(.16,-.13),(-.157,-.15)],.020,'armorLight',.005,-.041)
prism('shield gold lower emblem',[(-.070,-.28),(.03,-.24),(.064,-.48),(-.021,-.44)],.006,'yellow',.002,-.055)
box('shield red lower crossbar',(.022,-.066,-.563),(.261,.036,.055),'red',.006)
for xx in (-.144,.141):box('shield slender prong',(xx,.008,.799),(.022,.035,.206),'armor',.004)
line('shield lower molded seam',[(-.127,-.055,-.225),(-.11,-.055,-.489),(-.063,-.055,-.52)],.0012)
box('shield arm mount',(0,.104,-.02),(.086,.19,.18),'frame',.008)
for xx in (-.08,.08):cylinder('shield rear mount pin',(xx,.07,.1),.023,.075,'gunmetal','Y')
# Lean toward the head at the top and present slight three-quarter thickness.
transform_parts(start,Matrix.Translation((.96,-.224,2.438))@Matrix.Rotation(-.15,4,'Y')@Matrix.Rotation(-.12,4,'Z'))

def export_asset():
 bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 groups={k:dict(name='gundam-'+k,material=k,position=[],normal=[],uv=[],index=[])for k in mats}
 lo=[1e9]*3;hi=[-1e9]*3;tris=0
 for ob in objects:
  ev=ob.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles();mx=ob.matrix_world;nm=mx.to_3x3().inverted().transposed();g=groups[ob.data.materials[0].name];seen={}
  for tri in me.loop_triangles:
   tris+=1
   for li in tri.loops:
    c=mx@me.vertices[me.loops[li].vertex_index].co;n=(nm@me.corner_normals[li].vector).normalized()
    p=(round(c.x,6),round(c.z,6),round(-c.y,6));nn=(round(n.x,5),round(n.z,5),round(-n.y,5));key=p+nn
    if key not in seen:
     seen[key]=len(g['position'])//3;g['position'].extend(p);g['normal'].extend(nn);g['uv'].extend((0,0))
     for i in range(3):lo[i]=min(lo[i],p[i]);hi[i]=max(hi[i],p[i])
    g['index'].append(seen[key])
  ev.to_mesh_clear()
 meshes=[v for v in groups.values()if v['index']]
 # Exact sole contact without moving only the miniature root.
 for g in meshes:
  for j in range(1,len(g['position']),3):g['position'][j]=round(g['position'][j]-lo[1],6)
 height=hi[1]-lo[1];hi[1]=height;lo[1]=0
 asset=dict(metadata=dict(name='Reference-led articulated Mk-II miniature',authoring='Blender '+bpy.app.version_string,upAxis='Y',frontAxis='+Z',floorY=0,overallHeight=height,triangleCount=tris,drawCount=len(meshes),revision=15),bounds=dict(min=lo,max=hi),palette={k:dict(color=list(v[0]),metalness=v[1],roughness=v[2])for k,v in PALETTE.items()},meshes=meshes)
 (OUT/'models.js').write_text('export default '+json.dumps(asset,separators=(',',':'))+';\n',encoding='utf-8')
 return asset

asset=export_asset()
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'shelf-gundam.blend'))
ground=bpy.data.materials.new('ground');ground.diffuse_color=(.16,.17,.18,1)
bpy.ops.mesh.primitive_plane_add(size=20);bpy.context.object.data.materials.append(ground)
for loc,power,size in [((-3,-4,6),650,4),((4,-2,4),420,3),((1,3,5),900,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size
 o.rotation_euler=(Vector((0,0,1.6))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.4,-8,3.1));cam=bpy.context.object
cam.rotation_euler=(Vector((0,-.02,1.61))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=3.7
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1100;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(SOURCE/'shelf-gundam-preview.png')
scene.world=bpy.data.worlds.new('studio');scene.world.color=(.20,.20,.20);scene.view_settings.look='AgX - Medium High Contrast'
bpy.ops.render.render(write_still=True)
print('REFINED_GUNDAM',json.dumps(asset['metadata']))
