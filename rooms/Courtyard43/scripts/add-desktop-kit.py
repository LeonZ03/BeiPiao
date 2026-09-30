"""Photo-led desktop electronics, interior12 -> interior13.

Run ONLY through official Blender Lab MCP against the current full source.
All dimensions are photo estimates. Visible component layout is reproduced;
unreadable legends and concealed circuitry are deliberately left unlabelled.
The kit is independently editable and never imports/rebuilds old room sources.
"""
from pathlib import Path
from math import sin, cos, pi, radians
from collections import defaultdict
import json, random, hashlib
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
ASSET = ROOM / 'assets/development-kit'
ASSET.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
assert scene.get('web_revision') == 'courtyard43-interior12', 'Wrong parent revision'
assert not any(o.name.startswith('C43_DevKit_') for o in scene.objects)
random.seed(4313)
collection = bpy.data.collections.new('C43_DevelopmentKit_desktop13')
scene.collection.children.link(collection)
materials = {}

def material(name, rgb, rough=.6, metal=0, alpha=1):
    m = bpy.data.materials.new('C43_DevKit_' + name)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metal
    p.inputs['Alpha'].default_value = alpha
    m['web_props'] = json.dumps({'roughness':rough,'metalness':metal,'transparent':alpha<1,'opacity':alpha,'depthWrite':alpha==1})
    materials[name] = m
    return m

material('soldermask',(.022,.255,.093),.47)
material('board_edge',(.16,.22,.073),.83)
material('silkscreen',(.73,.80,.66),.84)
material('black_moulding',(.010,.016,.014),.68)
material('IC',(.015,.023,.020),.56)
material('blue_pot',(.017,.135,.40),.51)
material('pot_slot',(.005,.035,.10),.76)
material('sensor_blue',(.035,.31,.53),.75)
material('solder',(.50,.54,.50),.33,.78)
material('tin_shell',(.46,.49,.43),.29,.82)
material('screw',(.60,.61,.52),.27,.83)
material('gold',(.40,.285,.07),.36,.7)
material('LCD_rim',(.79,.80,.66),.57)
material('LCD_glass',(.008,.017,.014),.21)
material('display_face',(.025,.032,.027),.58)
material('unlit_segment',(.43,.47,.38),.73)
material('cardboard',(.34,.235,.115),.98)
material('cardboard_edge',(.235,.148,.055),1)
material('cardboard_crease',(.27,.18,.079),1)
material('cable',(.008,.016,.013),.46)
material('mousemat',(.009,.012,.014),.99)
material('mat_print',(.28,.29,.27),.96)
material('stitch',(.023,.025,.023),1)
material('bubble_film',(.74,.79,.75),.23,0,.22)

# Geometry is accumulated in local metres and transformed into Blender only at
# commit. Each component family remains editable; renderer batches by material.
class Mesh:
    def __init__(self,name,transform=None):
        self.name=name; self.transform=transform or (lambda p:p)
        self.v=[]; self.f=[]; self.mi=[]; self.keys=[]
    def faces(self, verts, faces, mat):
        if mat not in self.keys:self.keys.append(mat)
        offset=len(self.v); self.v.extend(verts)
        self.f.extend([tuple(i+offset for i in f) for f in faces])
        self.mi.extend([self.keys.index(mat)]*len(faces))
    def poly(self,outline,z0,z1,mat,edge=None):
        n=len(outline); verts=[(x,y,z) for z in (z0,z1) for x,y in outline]
        self.faces(verts,[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))],mat)
        self.faces(verts,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],edge or mat)
    def box(self,c,size,mat,r=0):
        x,y,z=c; w,h,d=size
        if r:
            pts=[]
            for cx,cy,start in [(x+w/2-r,y+h/2-r,0),(x-w/2+r,y+h/2-r,90),(x-w/2+r,y-h/2+r,180),(x+w/2-r,y-h/2+r,270)]:
                for i in range(4):
                    a=radians(start+i*30);pts.append((cx+r*cos(a),cy+r*sin(a)))
        else:pts=[(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)]
        self.poly(pts,z-d/2,z+d/2,mat)
    def cyl(self,c,r,depth,mat,n=16):
        x,y,z=c;self.poly([(x+r*cos(i*2*pi/n),y+r*sin(i*2*pi/n)) for i in range(n)],z-depth/2,z+depth/2,mat)
    def tube(self,points,r,mat,n=8):
        verts=[]; points=[Vector(p) for p in points]
        for i,p in enumerate(points):
            t=(points[min(i+1,len(points)-1)]-points[max(0,i-1)]).normalized()
            u=t.cross(Vector((0,0,1)))
            if u.length<.1:u=t.cross(Vector((0,1,0)))
            u.normalize();v=t.cross(u).normalized()
            verts.extend(tuple(p+r*(u*cos(j*2*pi/n)+v*sin(j*2*pi/n))) for j in range(n))
        faces=[tuple(range(n-1,-1,-1)),tuple(range((len(points)-1)*n,len(points)*n))]
        faces += [(i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j) for i in range(len(points)-1) for j in range(n)]
        self.faces(verts,faces,mat)
    def text(self,text,x,y,z,size,mat='silkscreen',angle=0):
        curve=bpy.data.curves.new('kit-print','FONT');curve.body=text;curve.size=size;curve.resolution_u=2
        curve.space_character=1.07
        ob=bpy.data.objects.new('kit-print',curve);collection.objects.link(ob)
        bpy.context.view_layer.update()
        temp=bpy.data.meshes.new_from_object(ob.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        a=radians(angle);verts=[(x+v.co.x*cos(a)-v.co.y*sin(a),y+v.co.x*sin(a)+v.co.y*cos(a),z) for v in temp.vertices]
        self.faces(verts,[tuple(p.vertices) for p in temp.polygons],mat)
        bpy.data.objects.remove(ob,do_unlink=True);bpy.data.curves.remove(curve);bpy.data.meshes.remove(temp)
    def finish(self):
        verts=[]
        for p in self.v:
            x,y,z=self.transform(p) # supplied in browser XYZ
            verts.append((x,-z,y))
        mesh=bpy.data.meshes.new(self.name);mesh.from_pydata(verts,[],self.f);mesh.update()
        for k in self.keys:mesh.materials.append(materials[k])
        for p,mi in zip(mesh.polygons,self.mi):p.material_index=mi
        uv=mesh.uv_layers.new(name='UVMap')
        for p in mesh.polygons:
            axes=sorted(range(3),key=lambda i:abs(p.normal[i]))[:2]
            for li in p.loop_indices:
                co=mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv=(co[axes[0]]*20,co[axes[1]]*20)
        obj=bpy.data.objects.new('C43_DevKit_'+self.name,mesh);collection.objects.link(obj)
        obj['web_tags']=json.dumps({'noCollision':True})
        obj['source']='User desktop close-up; photo-estimated dimensions; desktop13'
        return obj

# Board plane uses x=right, y=back/up, z=component height. Tilt is about the
# bottom edge; it rests on the textile, with rear bearing on the box front lip.
def board_transform(origin,angle,yaw):
    a,b=radians(angle),radians(yaw)
    def trans(p):
        x,y,z=p;xx=x;zz=-y*cos(a)+z*sin(a)
        return (origin[0]+xx*cos(b)+zz*sin(b),origin[1]+y*sin(a)+z*cos(a),origin[2]-xx*sin(b)+zz*cos(b))
    return trans

def pcb(mesh,w,h,notch=False):
    r=.002
    if notch:
        # Right board has a real lower-left cutout, not a rectangular placeholder.
        pts=[(-w/2,.029),(.005,.029),(.005,0),(w/2,0),(w/2,h),(-w/2,h)]
    else:pts=[(-w/2+r,0),(w/2-r,0),(w/2,r),(w/2,h-r),(w/2-r,h),(-w/2+r,h),(-w/2,h-r),(-w/2,r)]
    mesh.poly(pts,0,.0017,'soldermask','board_edge')

def screw(m,x,y,z=.003):
    m.cyl((x,y,z),.0041,.0011,'solder',20)
    m.cyl((x,y,z+.001),.0028,.0015,'screw',20)
    for size in [(.004,.0006,.00025),(.0006,.004,.00025)]:m.box((x,y,z+.0018),size,'black_moulding')

def pot(m,x,y):
    m.box((x,y,.0056),(.013,.012,.0078),'blue_pot',.0008)
    m.cyl((x,y,.0106),.0058,.0045,'blue_pot',20)
    m.box((x,y,.013),(.008,.0011,.00045),'pot_slot',.0003)
    for dx in [-.004,0,.004]:m.box((x+dx,y-.0064,.003),(.0006,.003,.0007),'solder')

def button(m,x,y):
    m.box((x,y,.0035),(.0078,.0078,.0036),'tin_shell',.0005)
    m.cyl((x,y,.0061),.002,.0025,'black_moulding',16)
    for dx in [-.0046,.0046]:
        for dy in [-.0023,.0023]:m.box((x+dx,y+dy,.0023),(.003,.0007,.0007),'solder')

def chip(m,x,y,w=.014,h=.009,pins=8):
    m.box((x,y,.004), (w,h,.004),'IC',.0005)
    m.cyl((x-w/2+.002,y+h/2-.002,.0061),.0006,.0002,'display_face',8)
    for side in [-1,1]:
        for i in range(pins):m.box((x-w/2+(i+.5)*w/pins,y+side*(h/2+.0013),.0025),(.0006,.0032,.0008),'solder')

def smd(m,x,y,vertical=False):
    m.box((x,y,.00235),(.0014 if vertical else .003,.003 if vertical else .0014,.0013),'black_moulding')
    for sign in [-1,1]:m.box((x+(0 if vertical else sign*.0012),y+(sign*.0012 if vertical else 0),.0026),(.0014 if vertical else .00075,.00075 if vertical else .0014,.0009),'solder')

def header(m,x,y,count,rows=2,vertical=False):
    pitch=.00254;w=count*pitch;h=rows*pitch
    m.box((x,y,.0044),(h if vertical else w,w if vertical else h,.0055),'black_moulding',.0004)
    for row in range(rows):
        for i in range(count):
            xx=(row-(rows-1)/2)*pitch if vertical else (i-(count-1)/2)*pitch
            yy=(i-(count-1)/2)*pitch if vertical else (row-(rows-1)/2)*pitch
            m.box((x+xx,y+yy,.0075),(.001,.001,.0012),'gold')

def usb(m,x,y,rot=0):
    # Hollow folded sheet-metal socket, visible insulating tongue and contacts.
    w,h=.013,.011
    m.box((x,y,.003),(w,h,.001),'tin_shell')
    m.box((x,y,.010),(w,h,.0007),'tin_shell')
    for dx in [-w/2,w/2]:m.box((x+dx,y,.0065),(.0007,h,.007),'tin_shell')
    m.box((x,y+h/2-.001,.0065),(w,.0015,.006),'black_moulding')
    m.box((x,y-.001,.006),(w*.78,h*.7,.002),'LCD_rim')
    for i in range(4):m.box((x+(i-1.5)*.002,y-.003,.0071),(.0008,.003,.0002),'gold')

# Mat and all box coordinates: local x across desktop, local y toward wall,
# local z upwards. The photographed arrangement occupies the desk's right side.
OX,OZ=-1.037,.485
def desk(p):return (OX+p[0],.740+p[2],OZ-p[1])
mat=Mesh('Mousemat',desk)
mat.box((0,.195,.00165),(.48,.39,.0033),'mousemat',.008)
# A restrained, legible reproduction of the visible print. No hidden diagram
# parts, complete weapon mechanism or unobserved model marks are invented.
ink=.00348
labels=['assembly','safety','spring','depressor plunger','depressor plunger spring','loaded bearing','plate','catch spring','catch','block pin','mechanism housing with ejector','Trigger spring 1','Trigger spring 2','Trigger bar']
for i,t in enumerate(labels):
    x=-.218+i*.029
    mat.text(t,x,.018,ink,.006,'mat_print',90)
for i in range(15):
    x=-.20+(i%5)*.086;y=.19+(i//5)*.061
    mat.text(str(i+2),x,y+.027,ink,.0045,'mat_print')
    points=[(x,y,ink),(x+.011,y+.005,ink),(x+.015,y+.024,ink),(x+.021,y+.026,ink)]
    mat.tube(points,.00024,'mat_print',4)
for x in [-.235,.235]:
    for i in range(98):mat.box((x,.003+i*.0039,.00355),(.0006,.0022,.00024),'stitch')
for y in [.005,.385]:
    for i in range(119):mat.box((-.231+i*.0039,y,.00355),(.0022,.0006,.00024),'stitch')
mat.finish()

box=Mesh('Open_cardboard_box',desk)
# Internal size 0.32 x 0.15, walls 2 mm; behind both boards. Upright lid is a
# separate bent sheet with an actual fold, small side flaps and cardboard edge.
bx,by=-.026,.28
box.box((bx,by,.005),(.32,.151,.003),'cardboard')
for x in [bx-.16,bx+.16]:box.box((x,by,.030),(.002,.154,.053),'cardboard')
box.box((bx,by-.076,.029),(.32,.002,.052),'cardboard')
box.box((bx,by+.076,.031),(.32,.002,.056),'cardboard')
lid=[(bx-.16,by+.076,.058),(bx+.16,by+.076,.058),(bx+.16,by+.092,.240),(bx-.16,by+.092,.240)]
box.faces(lid,[(0,1,2,3)],'cardboard')
box.faces([(x,y+.0018,z) for x,y,z in lid],[(3,2,1,0)],'cardboard')
for i in range(4):box.faces([lid[i],lid[(i+1)%4],(lid[(i+1)%4][0],lid[(i+1)%4][1]+.0018,lid[(i+1)%4][2]),(lid[i][0],lid[i][1]+.0018,lid[i][2])],[(0,1,2,3)],'cardboard_edge')
for z in [.060,.089]:box.tube([(bx-.157,by+.079,z),(bx+.157,by+.079,z)],.00038,'cardboard_crease',4)
for x in [bx-.16,bx+.16]:
    box.tube([(x,by-.074,.057),(x,by+.074,.057)],.0006,'cardboard_edge',6)
    box.faces([(x,by-.073,.056),(x,by+.074,.057),(x+(.022 if x>bx else -.022),by+.058,.022)],[(0,1,2)],'cardboard')
box.finish()

wrap=Mesh('Bubble_wrap',desk)
wrap.box((bx,by,.008),(.303,.137,.0005),'bubble_film',.005)
for i in range(32):
    for j in range(14):
        x=bx-.145+i*.0093+(j%2)*.002;y=by-.061+j*.0093
        # Small staggered air pockets; low segment count at physical size.
        verts=[(x,y,.0108)]
        for ring in range(1,4):
            angle=ring*pi/6
            verts.extend((x+.0038*sin(angle)*cos(k*pi/4),y+.0038*sin(angle)*sin(k*pi/4),.0083+.0025*cos(angle)) for k in range(8))
        faces=[(0,1+k,1+(k+1)%8) for k in range(8)]
        faces += [(1+(r-1)*8+k,1+(r-1)*8+(k+1)%8,1+r*8+(k+1)%8,1+r*8+k) for r in range(1,3) for k in range(8)]
        wrap.faces(verts,faces,'bubble_film')
wrap.finish()

cable=Mesh('Coiled_cable',desk)
for turn in range(3):
    pts=[]
    for i in range(100):
        a=i/99*2*pi;pts.append((bx+.099*cos(a)+turn*.003,by+.046*sin(a)-turn*.001,.015+turn*.005+.004*sin(a*2+turn)))
    cable.tube(pts,.0024,'cable',10)
cable.tube([(bx-.091,by-.013,.021),(bx-.086,by-.026,.018),(bx-.073,by-.030,.016)],.0027,'cable',10)
cable.box((bx-.068,by-.028,.018),(.027,.012,.009),'cable',.002)
cable.box((bx-.050,by-.028,.018),(.012,.011,.006),'tin_shell',.001)
for i in range(5):cable.box((bx-.080+i*.0015,by-.028,.023),(.0006,.010,.0008),'black_moulding')
cable.finish()

# Left/main board and the smaller expansion board are separate assemblies with
# independent slopes, as in the photo. Their lowest rear PCB edges touch mat.
main=Mesh('Main_board',board_transform((OX-.093,.7433,OZ-.099),29,-5))
pcb(main,.180,.148)
for x in [-.080,.080]:
    for y in [.011,.138]:screw(main,x,y)
for i in range(4):pot(main,-.065+i*.025,.131)
for i in range(5):button(main,.077,.114-i*.021)
header(main,-.083,.064,16,2,True)
header(main,-.027,.104,10,2)
header(main,.014,.104,4,2)
chip(main,.047,.105,.018,.013,12)
chip(main,-.011,.114,.008,.006,4)
usb(main,-.092,.108);usb(main,.087,.029)
for i in range(8):
    smd(main,.016+i*.006,.140,True)
    main.box((.016+i*.006,.129,.0027),(.002,.004,.0013),'LCD_rim')
for i in range(6):smd(main,-.062+i*.005,.114)
# Raised daughterboard, spacers and recessed glass; not a pasted rectangle.
main.box((-.008,.052,.007),(.137,.098,.002),'soldermask',.0015)
for x in [-.070,.051]:
    for y in [.011,.094]:screw(main,x,y,.009)
main.box((-.003,.052,.010),(.109,.086,.004),'LCD_rim',.0015)
main.box((-.003,.052,.0122),(.093,.070,.0008),'LCD_glass',.0005)
header(main,.064,.057,17,1,True)
for x,y,t in [(-.076,.024,'GXCT'),(.068,.004,'RESET'),(-.017,.094,'SWDIO'),(.023,.094,'NRST'),(.050,.014,'USB')]:main.text(t,x,y,.0135 if t=='GXCT' else .0020,.0032,angle=90 if t=='GXCT' else 0)
main.text('GXCT',-.041,.003,.0021,.007)
for i in range(6):
    main.tube([(.012+i*.008,.142,.00196),(.016+i*.008,.142,.00196),(.016+i*.008,.146,.00196)],.00015,'silkscreen',4)
main.finish()

small=Mesh('Expansion_board',board_transform((OX+.073,.7433,OZ-.115),33,5))
pcb(small,.145,.123,True)
for x,y in [(-.066,.115),(.066,.115),(.066,.061)]:screw(small,x,y)
for row in range(2):
    for i in range(4):button(small,-.045+i*.019,.113-row*.015)
for x,y in [(.037,.109),(.059,.109),(.005,.085),(.027,.085),(.061,.084),(.005,.056),(.027,.056)]:pot(small,x,y)
for i in range(3):chip(small,-.057+i*.020,.084,.014,.010,8)
for i in range(3):chip(small,.002+i*.021,.032,.009,.006,4)
for i in range(14):smd(small,-.065+i*.008,.074,True)
for i in range(3):
    x=-.054+i*.021;y=.050
    small.box((x,y,.0048),(.020,.028,.006),'display_face',.0008)
    # Unpowered seven-segment faces are grey; never luminous "888".
    for dx,dy,w,h in [(0,.010,.011,.0016),(0,0,.011,.0016),(0,-.010,.011,.0016),(-.006,.005,.0016,.008),(.006,.005,.0016,.008),(-.006,-.005,.0016,.008),(.006,-.005,.0016,.008)]:small.box((x+dx,y+dy,.0081),(w,h,.00025),'unlit_segment',.0005)
    small.cyl((x+.008,y-.011,.0081),.0007,.0003,'unlit_segment',8)
# Perforated blue sensor casing: open rectangular slots with dark recessed base.
small.box((.054,.057,.0045),(.021,.017,.005),'sensor_blue',.001)
small.box((.054,.057,.0075),(.018,.014,.001),'black_moulding')
for col in range(5):small.box((.044+col*.005,.057,.009),(.002,.017,.003),'sensor_blue')
for row in range(5):small.box((.054,.049+row*.004,.009),(.021,.0017,.003),'sensor_blue')
header(small,.030,.014,9,2)
for i in range(7):smd(small,.006+i*.009,.004)
small.cyl((.062,.023,.006),.0035,.008,'solder',16)
small.text('GXCT',.036,.050,.0020,.006,angle=90)
small.text('CT',.057,.031,.0020,.003)
small.text('GND',.002,.022,.0020,.002)
small.finish()

# Preserve the old mouse asset as an archived source object, excluded from the
# active room. The new photographic scene has no mouse sitting under the PCBs.
hidden=[]
for o in scene.objects:
    if o.name=='C43_Mousepad' or o.name.startswith('C43_Mouse_'):
        o.hide_render=True;o.hide_viewport=True;hidden.append(o.name)
objects=list(collection.objects)
scene['parent_web_revision']='courtyard43-interior12'
scene['web_revision']='courtyard43-interior13'
scene['desktop_kit_revision']='desktop13'
scene['desktop_kit_notes']='Two unpowered boards, open cardboard box, bubble wrap and coiled cable on printed textile mat. Photo estimates, not measured CAD.'
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
# Library includes independent editable geometry/materials; no foreign room data.
bpy.data.libraries.write(str(ASSET/'Courtyard43-development-kit.blend'),set(objects)|{collection},path_remap='RELATIVE',fake_user=True)
result={'revision':scene['web_revision'],'objects':len(objects),'vertices':sum(len(o.data.vertices) for o in objects),'hiddenOldMouse':len(hidden),'asset':str(ASSET/'Courtyard43-development-kit.blend')}
