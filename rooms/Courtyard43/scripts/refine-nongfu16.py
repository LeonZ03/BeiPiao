"""Official Blender Lab MCP only. Product-confirmed Nongfu Spring 1.5 L.

Parent interior15. Outline/label derived from the official product photograph;
physical dimensions remain photo estimates, not manufacturer measurements.
"""
import bpy,bmesh,ast,json,math,os,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior15'
bpy.context.preferences.filepaths.save_version=0
targets=set();bp=lambda p:Vector((p[0],-p[2],p[1]));web=lambda p:Vector((p[0],p[2],-p[1]))
for script,names in [('refine-furnishings.py',{'digest','shader','material','replace','lathe'}),('refine-details15.py',{'mat','textmesh'})]:
    p=ROOM/'scripts'/script;t=ast.parse(p.read_text(encoding='utf8'))
    exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),str(p),'exec'))
before={o.name:digest(o) for o in scene.objects}
oldnames={o.name for o in scene.objects if o.name.startswith('C43_Nongfu15_') or o.name in {'C43_Ribbed_water_bottle','C43_Bottle_water','C43_Bottle_cap','C43_Bottle_label'}}
for name in oldnames:
    if name.startswith('C43_Nongfu15_'):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
targets.update(oldnames)
cx,base,cz=.56,1.0125,.215
def material16(name,color,rough=.5,alpha=1):
    m=mat('Nongfu16_'+name,color,rough,alpha=alpha);m.name='C43_Nongfu16_'+name
    p=json.loads(m['web_props']);p.update(specularIntensity=.65 if alpha<1 else .3,envMapIntensity=.6 if alpha<1 else .12)
    m['web_props']=json.dumps(p);return m
pet=material16('clear_PET',(.92,.95,.95),.11,.11)
water=material16('water',(.76,.86,.85),.09,.12)
red=material16('cap_red',(.72,.009,.007),.38)
labelred=material16('label_red',(.76,.008,.012),.66)
white=material16('label_white',(.93,.93,.88),.76)
green=material16('mountain_dark_green',(.008,.14,.075),.76)
lightgreen=material16('mountain_pale_green',(.08,.38,.25),.79)
# Product silhouette: height/width about 3.75; long, gently convex shoulder,
# label in the lower middle, and five scalloped PET standing feet.
profile=[(0,0),(.028,0),(.039,.004),(.043,.013),(.0435,.035),(.0435,.174),(.0432,.193),(.042,.213),(.0395,.234),(.034,.257),(.026,.279),(.0155,.298),(.0153,.308)]
def radius(h):return float(np.interp(h,[h for r,h in profile[1:]],[r for r,h in profile[1:]]))
def relief(h,a):
    val=0.
    for center in [.182,.193,.204]:
        arch=center+.007*(.5+.5*math.cos(4*a))
        val+=.00135*math.exp(-((h-arch)/.0015)**2)
    return val
def close_mesh(o):
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(o.data);bm.free();o.data.update()
def surface(name,rows,material,n=128):
    vv=[];ff=[];uv=[]
    for j,(r,h,inner) in enumerate(rows):
        for i in range(n):
            a=math.tau*i/n
            rr=r+(relief(h,a) if r>.03 and not inner else 0)
            if h<.025 and r>.02:rr-=.0027*(.5+.5*math.cos(5*a))*max(0,1-h/.025)
            yy=h+(max(0,1-h/.012)*.003*(.5+.5*math.cos(5*a)) if r>.015 and h<.012 else 0)
            vv.append((cx+rr*math.sin(a),base+yy,cz+rr*math.cos(a)));uv.append((i/n,h/.326))
    for j in range(len(rows)-1):
        for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    o=replace(name,vv,ff,[material],uv);close_mesh(o);return o
heights=np.unique(np.r_[np.linspace(.004,.308,135),[h for r,h in profile[1:]]])
outer=[(0,.003,False),(.028,0,False)]+[(radius(float(h)),float(h),False) for h in heights]
inner=[(radius(float(h))-.0006,float(h),True) for h in heights[::-1]]+[(.025,.0018,True),(0,.0042,True)]
body=surface('C43_Ribbed_water_bottle',outer+inner,pet)
# Estimate level by the modeled interior volume. Keep a physically horizontal
# meniscus; it is not a red disc or a label end-cap.
hs=np.linspace(.004,.306,1500);rs=np.array([radius(float(h))-.0008 for h in hs])
volume=np.cumsum(math.pi*rs*rs*(hs[1]-hs[0]));level=float(np.interp(.75*volume[-1],volume,hs))
wp=[(0,.004),(.029,.004)]+[(radius(float(h))-.001,float(h)) for h in np.linspace(.009,level,48)]+[(radius(level)-.0015,level+.00035),(0,level+.00035)]
wat=lathe('C43_Bottle_water',(cx,base,cz),wp,water,80)
wat['web_tags']=json.dumps({'noCollision':True,'fillFraction':.75,'nominalCapacityL':1.5,'waterLevelM':base+level})
wat['fillFraction']=.75;wat['fillHeightM']=level
# Short wide red screw cap, tightly fluted; all flutes in one mesh.
caprows=[(0,.306),(.0159,.306),(.0165,.307),(.0165,.322),(.0158,.325),(0,.325)]
vv=[];ff=[];uv=[];n=192
for j,(r,h) in enumerate(caprows):
    for i in range(n):
        a=math.tau*i/n;rr=r+(.00037*(.5+.5*math.cos(48*a)) if r>.016 else 0)
        vv.append((cx+rr*math.sin(a),base+h,cz+rr*math.cos(a)));uv.append((i/n,j/5))
for j in range(len(caprows)-1):
    for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
close_mesh(replace('C43_Bottle_cap',vv,ff,[red],uv))
lathe('C43_Nongfu16_tamper',(cx,base,cz),[(.0154,.301),(.0164,.301),(.0165,.304),(.0154,.304),(.0154,.301)],red,96)
# A genuine wrap sleeve: white mountain field over a wavy red brand field.
# Its thin annular edges must never form opaque discs inside the bottle.
vv=[];ff=[];uv=[];n=160;r=.04385
for j in range(6):
    for i in range(n):
        a=math.tau*i/n
        h=[.047,.123-.003*math.cos(a),.172,.172,.047,.047][j]
        rr=r if j<3 or j==5 else r-.00025
        vv.append((cx+rr*math.sin(a),base+h,cz+rr*math.cos(a)));uv.append((i/n,(h-.047)/.125))
for j in range(5):
    for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
label=replace('C43_Bottle_label',vv,ff,[labelred,white],uv)
for p in label.data.polygons:
    h=sum(web(label.matrix_world@label.data.vertices[i].co).y for i in p.vertices)/len(p.vertices)-base
    if h>.123-.003*math.cos(math.atan2(sum(web(label.matrix_world@label.data.vertices[i].co).x-cx for i in p.vertices),sum(web(label.matrix_world@label.data.vertices[i].co).z-cz for i in p.vertices))):p.material_index=1
close_mesh(label)
for h in [.0465,.1725]:lathe('C43_Nongfu16_green_rule_'+str(h),(cx,base,cz),[(r-.00015,h-.0008),(r+.00005,h-.0008),(r+.00005,h+.0008),(r-.00015,h+.0008),(r-.00015,h-.0008)],green,128)
# Reconstruct only readable front-label information from the official image.
for name,text,size,h,m in [('brand','农夫山泉',.022,.100,white),('english','NONGFU SPRING',.0094,.080,white),('water','饮用天然水',.0067,.069,white),('volume','净含量1.5L',.0062,.058,white)]:
    textmesh('C43_Nongfu16_'+name,text,size,(cx,base+h,cz+r+.0001),m,(cx,cz,r+.0001))
# Green mountain-and-water mark. Polygon silhouette traced from the public
# front photograph; unseen rear ingredients/barcodes deliberately omitted.
def logo(name,points,m):
    coords=[]
    for x,y in points:
        a=x/(r+.0002);coords.append((cx+(r+.0002)*math.sin(a),base+y,cz+(r+.0002)*math.cos(a)))
    o=replace('C43_Nongfu16_logo_'+name,coords,[tuple(range(len(coords)))],[m],smooth=False)
    mod=o.modifiers.new('Ink relief','SOLIDIFY');mod.thickness=.00004
    return o
logo('left',[(-.027,.141),(-.018,.158),(-.012,.152),(-.006,.140)],lightgreen)
logo('right',[(.006,.140),(.016,.162),(.029,.141)],lightgreen)
logo('main',[(-.017,.137),(-.005,.159),(-.002,.157),(.002,.166),(.022,.137)],green)
logo('snow',[(-.008,.152),(-.004,.158),(-.001,.154),(.002,.162),(.009,.151),(.003,.157),(.003,.152),(-.002,.156)],white)
for j in range(6):
    y=.135-j*.0014;w=.019*(1-j*.10)
    logo('reflection_'+str(j),[(-w,y),(w,y+.0003),(w*.93,y-.0006),(-w*.98,y-.0005)],green if j%2==0 else lightgreen)
# Keep all unrelated objects, approved positions and original lighting intact.
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==v for n,v in before.items() if n not in targets),'Unrelated object changed'
scene['web_revision']='courtyard43-interior16'
scene['nongfu16']=json.dumps({'parent':'courtyard43-interior15','reference':'https://en.nongfuspring.com/goods/detail-all.html','image':'https://file-cloud.yst.com.cn/website/2020/04/14/0168842ef2354497b74796b69c41b7e4.png','nominalCapacityL':1.5,'fillFraction':.75,'waterHeight':level,'estimatedDimensionsM':[.087,.325,.087],'targets':sorted(targets)})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';ns={'__file__':str(p)}
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns)
result=ns['export_interior']();result['waterLevel']=level;result['unchangedObjects']=len(set(before)-targets)
