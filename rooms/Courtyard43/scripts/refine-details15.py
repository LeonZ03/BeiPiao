"""Official Blender Lab MCP only: user-confirmed cloth/furniture/prop corrections.

Parent interior14. Geometry not visible in the photographs and dimensions other
than the mouse mat are estimates. Never replay old complete-room generators.
"""
from pathlib import Path
import ast, bpy, bmesh, json, math, hashlib, os
import numpy as np
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[3]; ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior14'
assert not scene.get('details15')
bpy.context.preferences.filepaths.save_version=0
bp=lambda p:Vector((p[0],-p[2],p[1]))
web=lambda p:Vector((p[0],p[2],-p[1]))
targets=set()
helper=ROOM/'scripts/refine-furnishings.py'
tree=ast.parse(helper.read_text(encoding='utf8'))
names={'digest','shader','material','assign','replace','solid','tube','lathe'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(helper),'exec'))
bpy.context.view_layer.update()
before={o.name:digest(o) for o in scene.objects}

def mat(name,color,rough=.7,metal=0,alpha=1):
    m=material(name,color,rough,metal,0,alpha)
    m.name='C43_'+name+'_15'
    shader(m).inputs['Specular IOR Level'].default_value=.25
    m['web_props']=json.dumps({'roughness':rough,'metalness':metal,'specularIntensity':.4,'clearcoat':0,'sheen':0,'opacity':alpha,'transparent':alpha<1,'depthWrite':alpha>=1,'side':0})
    return m

def hide(o):
    targets.add(o.name);o.hide_render=True;o.hide_set(True)

def cube(name,center,size,m,bevel=.002):
    c=Vector(center);s=Vector(size)*.5
    vv=[tuple(c+Vector((x*s.x,y*s.y,z*s.z))) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=replace(name,vv,[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)],[m],smooth=False)
    if bevel:
        mod=o.modifiers.new('Small physical edge radius','BEVEL');mod.width=bevel;mod.segments=3
        mod=o.modifiers.new('Stable hard-surface normals','WEIGHTED_NORMAL');mod.keep_sharp=True
    return o

def deform(o,fn):
    targets.add(o.name);o.data=o.data.copy();inv=o.matrix_world.inverted()
    for v in o.data.vertices:v.co=inv@bp(fn(web(o.matrix_world@v.co)))
    o.data.update()

def bezier(name,points,radius,m):
    old=bpy.data.objects.get(name)
    cr=bpy.data.curves.new(name+'_path15','CURVE');cr.dimensions='3D';cr.resolution_u=12;cr.bevel_depth=radius;cr.bevel_resolution=3;cr.use_fill_caps=True
    sp=cr.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
    for p,co in zip(sp.bezier_points,points):p.co=bp(co);p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    ob=bpy.data.objects.new(name+'_tmp',cr);scene.collection.objects.link(ob);cr.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    if old:
        ob.data.transform(old.matrix_world.inverted());old.modifiers.clear();old.data=ob.data;bpy.data.objects.remove(ob,do_unlink=True);ob=old
    else:ob.name=name
    if not ob.data.uv_layers:
        uv=ob.data.uv_layers.new(name='UVMap')
        for p in ob.data.polygons:
            for li in p.loop_indices:
                v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.z)
    targets.add(ob.name);ob['web_tags']=json.dumps({'noCollision':True})
    return ob

def textmesh(name,text,size,center,m,curved=None):
    cu=bpy.data.curves.new(name,'FONT');cu.body=text;cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.resolution_u=4;cu.extrude=.00006
    if any(ord(c)>127 for c in text):
        font=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyhbd.ttc'
        cu.font=bpy.data.fonts.load(str(font))
    ob=bpy.data.objects.new(name,cu);scene.collection.objects.link(ob);cu.materials.append(m)
    ob.location=bp(center);ob.rotation_euler.x=math.pi/2
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH');bpy.context.view_layer.update()
    if curved:
        cx,cz,r=curved;inv=ob.matrix_world.inverted()
        for v in ob.data.vertices:
            p=web(ob.matrix_world@v.co);a=(p.x-cx)/r;p.x=cx+r*math.sin(a);p.z=cz+r*math.cos(a)+.0002+(p.z-center[2]);v.co=inv@bp(p)
    uv=ob.data.uv_layers.new(name='UVMap')
    for p in ob.data.polygons:
        for li in p.loop_indices:
            v=ob.data.vertices[ob.data.loops[li].vertex_index].co;uv.data[li].uv=(v.x,v.y)
    targets.add(name);ob['web_tags']=json.dumps({'noCollision':True});return ob

# Shorten the lower sheet skirt, then keep the floral quilt entirely on the
# mattress. The same deformation applies to each sewn edge and both shells.
for name in ['C43_DrapedWhiteSheet','C43_DrapedWhiteSheetSewnHem']:
    deform(bpy.data.objects[name],lambda p:(p.x,.5575-(.5575-p.y)*.27 if p.y<.5575 else p.y,p.z))
def quilt(p):
    x=-1.39+(p.x+1.3925)*(1.79/1.8947)
    z=1.32+(p.z-1.2254)*(1.405/1.5822)
    y=.572+.020*math.log1p(math.exp((p.y-.572)/.020))
    return x,y,z
for name in ['C43_FloralDuvet','C43_FloralDuvetSewnHem']:
    deform(bpy.data.objects[name],quilt)
bpy.data.objects['C43_FloralDuvet']['details15']='Quilt gathered on mattress; no hanging quilt below bed frame'

# Left actual hat: append all dependencies from the approved Yongwang full
# scene, including its LA embroidery. Never save or modify the source file.
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
caproot=bpy.data.objects['C43_Cap2_Black_LA_Baseball_Cap.001']
destination=caproot.matrix_world.copy()
for o in list(scene.objects):
    if o.type=='MESH' and o.name.startswith('C43_Cap2_'):hide(o)
source_names=['Black LA Baseball Cap','attached-padded-curved-bill','continuous-six-panel-crown','crown-sewn-hem','top-covered-button']
source_names += ['bill-top-stitch'+('' if i==0 else f'.{i:03}') for i in range(6)]
source_names += ['crown-panel-seam'+('' if i==0 else f'.{i:03}') for i in range(6)]
source_names += ['curved-interlocking-LA-embroidery','curved-interlocking-LA-embroidery.001']+[f'Mesh {i:04}' for i in range(856,862)]
with bpy.data.libraries.load(str(source),link=False) as (src,dst):
    assert all(n in src.objects for n in source_names)
    dst.objects=source_names
loaded=list(dst.objects)
root=next(o for o in loaded if o.type=='EMPTY')
oldworld=root.matrix_world.copy()
for o in loaded:
    scene.collection.objects.link(o)
    o.name='C43_Baseball15_'+o.name
    for key in ['web_node_id','web_name','web_user_data']:
        if key in o:del o[key]
    if o.type=='MESH':
        o.data=o.data.copy()
        if not o.data.uv_layers:
            uv=o.data.uv_layers.new(name='UVMap')
            for poly in o.data.polygons:
                for li in poly.loop_indices:
                    v=o.data.vertices[o.data.loops[li].vertex_index].co
                    uv.data[li].uv=(v.x,v.y)
        o['web_tags']=json.dumps({'noCollision':True})
        for i,m in enumerate(o.data.materials):
            if m:
                m=m.copy();m.name='C43_Baseball15_'+m.name;o.data.materials[i]=m
                if m.node_tree:
                    for n in m.node_tree.nodes:
                        if n.type=='TEX_IMAGE' and n.image:
                            n.image=n.image.copy()
    targets.add(o.name)
root.matrix_world=destination
root['reuse']=json.dumps({'source':str(source.relative_to(ROOT)).replace('\\','/'),'sourceRevision':'handles39','sha256':source_hash,'mode':'append independent mesh/material/image data; complete approved cap including embroidery'})
bpy.context.view_layer.update()

# Right hat is a soft bucket hat: closed shallow crown, sloping band, broad
# drooping all-around brim, parallel stitching and a real underside.
for o in list(scene.objects):
    if o.type=='MESH' and o.name.startswith('C43_Cap3_'):hide(o)
black=mat('Bucket_black_cotton',(.018,.019,.020),.94)
thread=mat('Bucket_dark_stitch',(.038,.039,.038),.96)
# Local hat axis points out from wall, its brim hangs vertically.
cx,cy,cz=-1.12,1.51,.097
profile=[(0,.097),(.025,.097),(.070,.096),(.077,.089),(.083,.074),(.089,.025),(.092,.002),(.111,-.015),(.137,-.025),(.147,-.023),(.149,-.025),(.143,-.029),(.132,-.030),(.109,-.020),(.090,-.004),(.086,.022),(.080,.071),(.073,.086),(.02,.09),(0,.09)]
hat=lathe('C43_BucketHat15',(0,0,0),profile,black,96)
def hatmap(p):
    a=math.atan2(p.z,p.x);r=math.hypot(p.x,p.z);w=max(0,min(1,(r-.086)/.064))
    return cx+p.x,cy+p.z*.92-.007*w*math.sin(a*3+.4),cz+p.y+w*(.009*math.sin(a*3+.2)+.004*math.sin(a*7))
deform(hat,hatmap)
hat['details15']='User-confirmed bucket hat; fabric band and all-around stitched brim; estimated proportions'
for j,r in enumerate([.105,.115,.125,.137]):
    pts=[hatmap(Vector((r*math.cos(a),-.013-(r-.105)*.42,r*math.sin(a)))) for a in np.linspace(0,math.tau,97)]
    tube('C43_BucketHat15_stitch_'+str(j),pts,.00045,thread)
tube('C43_Cap_hook_2',[(-1.12,1.66,.002),(-1.12,1.66,.036),(-1.12,1.631,.095)],.0024,bpy.data.materials['C43_Small_satin_nickel_07'])

# Hanging package: thin heat-sealed printed plastic, with an actual roll
# emerging through the side opening rather than a flat decorative blue lid.
navy=mat('Bag15_indigo_print',(.039,.043,.065),.71)
ivory=mat('Bag15_ivory_print',(.66,.66,.60),.75)
blue=mat('Bag15_blue_polyethylene',(.07,.31,.49),.68)
darkblue=mat('Bag15_roll_layers',(.024,.14,.24),.81)
vv=[];ff=[];uv=[];N=80;R=41
for j in range(R):
    t=j/(R-1);w=float(np.interp(t,[0,.06,.20,.57,.80,1],[.085,.123,.144,.119,.080,.007]));d=float(np.interp(t,[0,.12,.6,.86,1],[.018,.040,.035,.012,.003]))
    for i in range(N):
        a=math.tau*i/N;s=math.sin(a);c=math.cos(a);fold=(.006*math.sin(a*5+t*13)+.003*math.sin(a*11-t*19))*math.sin(math.pi*t)
        vv.append((1.973-.018*t**3+w*math.copysign(abs(c)**.60,c),1.225+.378*t+.009*math.sin(a*3+.2)*math.sin(math.pi*t),1.449-.037*t**3+(d+fold)*math.copysign(abs(s)**.60,s)))
        uv.append((i/N,t))
for j in range(R-1):
    for i in range(N):ff.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
ff.extend([tuple(reversed(range(N))),tuple((R-1)*N+i for i in range(N))])
bag=replace('C43_Hanging_bag',vv,ff,[ivory,navy],uv)
for p in bag.data.polygons:p.material_index=1 if N*15<=p.index<N*39 else 0
bag['details15']='User-confirmed garbage-bag retail package, thin sealed plastic with visible blue bag roll; unreadable product microcopy omitted'
for k in range(2):hide(bpy.data.objects['C43_Bag_strap_'+str(k)])
hide(bpy.data.objects['C43_Bag_round_rim'])
roll=lathe('C43_Bag_visible_blue_round_item',(0,0,0),[(.005,0),(.030,0),(.033,.003),(.033,.084),(.031,.089),(.005,.089),(.005,0)],blue,80)
# Roll projects obliquely from inside the upper-left side of the bag.
def rollmap(p):return 1.868+p.x-.31*p.y,1.451+p.z+.28*p.y,1.464+p.y*.90
deform(roll,rollmap)
paths=[]
for j,r in enumerate([.007,.011,.016,.021,.026,.030]):
    pts=[rollmap(Vector((r*math.cos(a),.0894,r*math.sin(a)))) for a in np.linspace(0,math.tau,81)]
    tube('C43_Bag15_roll_layer_'+str(j),pts,.00028,darkblue)
# The reference does not resolve any retail lettering; retain the package colours only.

# Large red-capped Nongfu bottle, retaining its counter anchor. The water level
# is calculated from the modeled inner volume, not 75% of overall cap height.
cx,base,cz=.56,1.0125,.215
pet=mat('Nongfu15_clear_PET',(.81,.86,.85),.16,alpha=.18)
water=mat('Nongfu15_water',(.68,.80,.81),.10,alpha=.25)
shader(water).inputs['IOR'].default_value=1.333
red=mat('Nongfu15_red_cap',(.53,.012,.006),.42)
labelred=mat('Nongfu15_label_red',(.61,.019,.009),.67)
labelwhite=mat('Nongfu15_label_white',(.89,.88,.82),.76)
profile=[(0,0),(.035,0),(.049,.004),(.054,.010),(.054,.019)]
for h in np.linspace(.022,.212,83):
    rib=.0018*(.5+.5*math.cos(h*math.tau/.020))
    profile.append((.0535-rib,float(h)))
profile += [(.052,.221),(.050,.234),(.044,.250),(.035,.263),(.023,.276),(.020,.287),(.020,.299)]
inner=[(max(0,r-.0009),h+.0008 if h<.010 else h) for r,h in profile[1:]]
shell=profile+list(reversed(inner))+[(0,.0012)]
lathe('C43_Ribbed_water_bottle',(cx,base,cz),shell,pet,112)
hs=np.linspace(.002,.297,700)
radii=np.interp(hs,[p[1] for p in profile[1:]],[max(0,p[0]-.0014) for p in profile[1:]])
vol=np.cumsum(math.pi*radii*radii*(hs[1]-hs[0]));level=float(np.interp(.75*vol[-1],vol,hs));wr=float(np.interp(level,hs,radii))
wp=[(0,.002)]+[(float(r),float(h)) for r,h in zip(radii,hs) if h<level]+[(wr,level-.001),(wr-.001,level),(0,level)]
wat=lathe('C43_Bottle_water',(cx,base,cz),wp,water,80);wat['fillFraction']=.75;wat['fillHeightM']=level
lathe('C43_Bottle_cap',(cx,base+.294,cz),[(0,0),(.021,0),(.022,.002),(.022,.027),(.019,.030),(0,.030)],red,96)
lathe('C43_Nongfu15_tamper_ring',(cx,base+.286,cz),[(.020,0),(.022,0),(.022,.006),(.020,.006),(.020,0)],red,96)
for j in range(40):
    a=j*math.tau/40;tube('C43_Nongfu15_cap_rib_'+str(j),[(cx+.022*math.cos(a),base+.297,cz+.022*math.sin(a)),(cx+.022*math.cos(a),base+.319,cz+.022*math.sin(a))],.00055,red)
label=lathe('C43_Bottle_label',(cx,base,cz),[(.054,.096),(.054,.147),(.054,.165),(.0535,.165),(.0535,.096),(.054,.096)],labelred,112)
label.data.materials.append(labelwhite)
for p in label.data.polygons:
    h=sum(web(label.matrix_world@label.data.vertices[i].co).y for i in p.vertices)/len(p.vertices)-base
    if h>.147:p.material_index=1
textmesh('C43_Nongfu15_brand','农夫山泉',.019,(cx,base+.126,cz+.055),labelwhite,(cx,cz,.055))
textmesh('C43_Nongfu15_water_title','饮用天然水',.0075,(cx,base+.155,cz+.055),labelred,(cx,cz,.055))

# Reconstruct the visible horizontal outlet strip. Hole pairs have the real
# side-by-side two-pin / angled three-pin arrangement, not four vertical dashes.
white=mat('Power15_warm_ABS',(.76,.75,.69),.65)
socketdark=mat('Power15_recess',(.016,.017,.016),.94)
rubber=mat('Power15_black_rubber',(.010,.011,.011),.89)
for o in list(scene.objects):
    if o.name.startswith('C43_Desk_Outlet_Slot'):hide(o)
cube('C43_Desk_Outlet_Backplate',(-2.016,.780,.900),(.019,.080,.180),white,.0035)
for j,z in enumerate([.845,.900,.955]):
    cube('C43_Power15_socket_face_'+str(j),(-2.004,.780,z),(.009,.068,.055),white,.003)
    for k,zz in enumerate([z-.009,z+.009]):
        cube(f'C43_Power15_pair_{j}_{k}',(-1.9985,.796,zz),(.002,.012,.0036),socketdark,.0007)
    cube('C43_Power15_earth_'+str(j),(-1.9985,.778,z),(.002,.008,.0036),socketdark,.0005)
    for k,sign in enumerate([-1,1]):
        # Angled rectangular apertures modeled as closed recess surfaces.
        ob=cube(f'C43_Power15_angle_{j}_{k}',(-1.9985,.766,z+sign*.009),(.002,.010,.0036),socketdark,.0004)
        # Rotate local web YZ about its own center, not about the world origin.
        c=bp((-1.9985,.766,z+sign*.009));rot=Matrix.Rotation(sign*.5,4,'X')
        inv=ob.matrix_world.inverted()
        for v in ob.data.vertices:v.co=inv@(c+rot.to_3x3()@(ob.matrix_world@v.co-c))
cube('C43_Desk_power_plug',(-1.977,.782,.845),(.043,.038,.037),white,.005)
cube('C43_Desk_small_dark_device',(-1.82,.753,.43),(.084,.026,.050),rubber,.006)
# AC input routes around the left desk edge and enters the adapter's left end.
ac=[(-1.957,.776,.845),(-1.935,.746,.842),(-1.911,.579,.806),(-1.88,.509,.710),(-1.903,.553,.609),(-2.006,.693,.502),(-2.008,.763,.459),(-1.920,.769,.433),(-1.861,.754,.430)]
bezier('C43_Desk_power_cable',ac,.0025,rubber)
bezier('C43_Power15_adapter_output',[(-1.781,.754,.430),(-1.766,.758,.425),(-1.754,.757,.391),(-1.776,.756,.340),(-1.782,.749,.297),(-1.751,.7475,.297)],.0018,rubber)
cube('C43_Power15_laptop_connector',(-1.751,.7475,.297),(.020,.0045,.010),rubber,.001)
for name,p0,p1,r in [('ac_strain',ac[0],(-1.950,.760,.844),.004),('adapter_ac',ac[-1],(-1.870,.755,.430),.0035),('adapter_dc',(-1.781,.754,.430),(-1.771,.756,.428),.0029)]:
    bezier('C43_Power15_'+name,[p0,p1],r,rubber)

# The separately authored, scope-limited helpers are executed in this same
# official process. They do not open or save a different complete scene.
for filename,fn in [('refine-chair15.py','apply_chair15'),('refine-curtains15.py','apply_curtains15')]:
    path=ROOM/'scripts'/filename;scope={'__file__':str(path),'__name__':'detail_helper'}
    exec(compile(path.read_text(encoding='utf8'),str(path),'exec'),scope)
    returned=scope[fn]();targets.update(returned['targets'])
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets),'Unrelated object changed'
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash,'Yongwang source changed'
scene['parent_web_revision']='courtyard43-interior14';scene['web_revision']='courtyard43-interior15'
scene['details15']=json.dumps({'targets':sorted(targets),'sourceReference':'P03/P04 + user type corrections','bottleFillFraction':.75,'sourceCapRevision':'handles39','sourceCapSHA256':source_hash})
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:
        im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath,library=im.library),start=str(ROOM/'assets/full-room'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'revision':scene['web_revision'],'targets':len(targets),'untouched':len(set(before)-targets),'waterHeight':level}
