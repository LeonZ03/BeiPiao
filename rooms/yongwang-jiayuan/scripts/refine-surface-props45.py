"""props44a -> props45. Surface-bound print, slimmer frames, shared switch, toothbrush.

Run through official Blender Lab MCP. Keeps every approved object anchor.
"""
from pathlib import Path
import bpy, bmesh, math, copy, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props44a'

def commit_mesh(nid,me,name=None):
    o=obs[nid];o.data=me
    if name:o.name=name;data['nodes'][nid]['name']=name
    bpy.context.view_layer.update()
    data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C)
    export(o);return o

# Preserve the inner hoop and string endpoints; reduce the excessive frontal
# frame width from 21.6 to 14.8 mm. The manufacturer's beam depth is a different
# dimension and is deliberately not confused with the front-facing width.
for wilson,ids in [(True,{'grey':2009,'red':2010,'black':2011}),(False,{'orange':2020,'black':2021})]:
    rx=.132 if wilson else .129;ry=.176;cy=.497;rows={k:[] for k in ids}
    for i in range(160):
        a=math.tau*(i+.5)/160
        key=('red' if .70<a<2.42 or 3.86<a<5.58 else 'grey' if a<.70 or a>5.58 else 'black') if wilson else ('orange' if a<2.02 or a>4.26 else 'black')
        rows[key].append(i)
    for key,nid in ids.items():
        me=obs[nid].data.copy();cursor=0
        for segment in rows[key]:
            for a in [math.tau*segment/160,math.tau*(segment+1)/160]:
                n=Vector((math.sin(a)/rx,math.cos(a)/ry,0)).normalized()
                for j in range(12):
                    offset=.0108*math.copysign(abs(math.cos(math.tau*j/12))**.65,math.cos(math.tau*j/12))
                    p=me.vertices[cursor].co;q=Vector((p.x,p.z,-p.y))
                    q+=n*(-.0034+offset*(.0074/.0108-1))
                    me.vertices[cursor].co=bp(q);cursor+=1
        commit_mesh(nid,me)
    # Head bumper follows the slimmer outside edge. Grommets terminate inside
    # the new frame rather than protruding past the paint.
    nid=2012 if wilson else 2022;me=obs[nid].data.copy()
    for i,v in enumerate(me.vertices):
        p=Vector((v.co.x,v.co.z,-v.co.y))
        if i<101*8:
            a=-1.5+(i//8)*3/100;p.x-=.0068*math.sin(a);p.y-=.0068*math.cos(a)
        else:
            # Each two-ring eyelet has 14 vertices; its outer ring is shortened.
            if (i-101*8)%14>=7:
                n=Vector((p.x/(rx*rx),(p.y-cy)/(ry*ry),0)).normalized();p-=n*.0060
        v.co=bp(p)
    commit_mesh(nid,me)

def body_bvh(ids):
    verts=[];faces=[]
    for nid in ids:
        me=obs[nid].data;start=len(verts)
        verts.extend([(v.co.x,v.co.z,-v.co.y) for v in me.vertices])
        faces.extend([tuple(start+i for i in p.vertices) for p in me.polygons])
    return BVHTree.FromPolygons(verts,faces)

surfaces={824:body_bvh([2009,2010,2011]),811:body_bvh([2020,2021])}
print_report=[]
def adhere(nid,points,faces,uvs):
    parent=data['nodes'][nid]['parent'];tree=surfaces[parent];verts=[]
    for x,y in points:
        hit,normal,_,distance=tree.ray_cast(Vector((x,y,.06)),Vector((0,0,-1)),.13)
        assert hit is not None,('Print outside painted frame',nid,x,y)
        verts.append((x,y,hit.z+.00004))
    o=commit_mesh(nid,mesh(obs[nid].name,verts,faces,uvs,True))
    mid=material('Surface45 '+o.name,data['nodes'][nid]['material'],rough=.48,
                 polygonOffset=True,polygonOffsetFactor=-1,polygonOffsetUnits=-1,
                 depthWrite=True,transparent=False,alphaTest=.3,side=0,
                 metadata={'revision':'props45','surfacePrint':True})
    set_material(nid,mid);data['nodes'][nid]['castShadow']=False
    o['surface_clearance_m']=.00004
    print_report.append({'id':nid,'vertices':len(verts),'surfaceClearanceM':.00004})

def branch(t):
    p=[Vector(q) for q in [(.008,.165),(.020,.220),(.034,.279),(.091,.369)]]
    q=(1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
    d=(3*(1-t)**2*(p[1]-p[0])+6*(1-t)*t*(p[2]-p[1])+3*t*t*(p[3]-p[2])).normalized()
    return q,Vector((-d.y,d.x))

# Wilson artwork is a subdivided curved transfer, with the original UV artwork.
points=[];uv=[];faces=[];nu,nv=72,8
for i in range(nu+1):
    u=i/nu;q,n=branch(.17+.65*u)
    for j in range(nv+1):
        v=j/nv;points.append(tuple(q+n*((v-.5)*.013)));uv.append((u,v))
for i in range(nu):
    for j in range(nv):
        a=i*(nv+1)+j;faces.append((a,a+nv+1,a+nv+2,a+1))
adhere(2018,points,faces,uv)

def font_print(nid,angle,map_point):
    me=obs[nid].data.copy();bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    # Small triangles follow the curved surface instead of bridging a letter
    # across a hollow throat or leaving long straight glyphs in mid-air.
    for _ in range(2):
        edges=[e for e in bm.edges if e.calc_length()>.0025]
        if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
    bm.to_mesh(me);bm.free()
    ca,sa=math.cos(angle),math.sin(angle);coords=[]
    for v in me.vertices:
        x,y=v.co.x,v.co.z;coords.append((ca*x+sa*y,-sa*x+ca*y))
    lo=[min(p[k] for p in coords) for k in range(2)];hi=[max(p[k] for p in coords) for k in range(2)]
    pts=[map_point((u-lo[0])/(hi[0]-lo[0]),(v-lo[1])/(hi[1]-lo[1])-.5) for u,v in coords]
    adhere(nid,pts,[tuple(p.vertices) for p in me.polygons],[(0,0)]*len(pts))

def on_branch(u,v):
    q,n=branch(.14+.72*u);return tuple(q+n*v*.011)
font_print(2029,math.atan2(.143,.060),on_branch)

def hoop(rx,a0,a1,width):
    def mapped(u,v):
        a=a0+(a1-a0)*u;n=Vector((math.sin(a)/rx,math.cos(a)/.176)).normalized()
        q=Vector((rx*math.sin(a),.497+.176*math.cos(a)))+n*(-.0034+v*width)
        return tuple(q)
    return mapped
font_print(2019,math.pi/2,hoop(.132,-1.94,-1.51,.008))
font_print(2031,math.pi/2,hoop(.129,-1.81,-1.27,.007))
font_print(2030,-.7,hoop(.129,-2.60,-2.25,.006))
# Remove the old floating cyan strips and replace them with projected paint.
me=obs[2034].data;pts=[]
for v in me.vertices:
    x,y=v.co.x,v.co.z
    if y>.36:
        a=math.atan2(x/.129,(y-.497)/.176);q,n=Vector((.129*math.sin(a),.497+.176*math.cos(a))),Vector((math.sin(a)/.129,math.cos(a)/.176)).normalized()
        radial=(Vector((x,y))-q).dot(n);p=q+n*(-.0034+radial*.55);pts.append(tuple(p))
    else:
        t=(y-.202)/.12;q,n=branch(.18+.58*t);pts.append((-q.x+(x-(-.019-.041*t))*.5,q.y))
adhere(2034,pts,[tuple(p.vertices) for p in me.polygons],[(0,0)]*len(pts))

# Append the actual C43 final switch meshes and materials, not a second build.
source=ROOT/'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend'
names=['C43_Switch_Backplate','C43_Switch_Rocker','C43_Switch28_reveal']
with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=names
loaded=dict(zip(names,b.objects));copied_mats={}
for src,nid,pos in [(loaded[names[0]],1482,(1.392,1.120,.860)),(loaded[names[1]],1483,(1.387,1.120,.860)),(loaded[names[2]],2033,(1.3895,1.120,.860))]:
    sm=src.data.materials[0]
    if sm.name not in copied_mats:
        mid=len(data['materials']);cm=sm.copy();cm.name='Shared45 '+sm.name;cm['web_material_id']=mid
        bs=next(n for n in cm.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        desc={'id':mid,'name':cm.name,'type':'MeshPhysicalMaterial','props':{'roughness':float(bs.inputs['Roughness'].default_value),'metalness':0,'ior':1.5,'side':2,'depthWrite':True},'colors':{'color':list(bs.inputs['Base Color'].default_value)[:3]},'textures':{},'vectors':{},'userData':{'sourceRoom':'Courtyard43','sourceRevision':'courtyard43-switch28','sourceMaterial':sm.name}}
        mats[mid]=cm;data['materials'].append(desc);copied_mats[sm.name]=mid
    me=src.data.copy();o=attach(me,data['nodes'][nid]['name'],copied_mats[sm.name],1481,nid)
    o.matrix_local=Matrix.Translation(Vector(bp(pos)));bpy.context.view_layer.update()
    data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);export(o)
    o['source_asset']='Courtyard43 switch28 / ce9e183';assert len(me.vertices)==len(src.data.vertices)
    assert all((x.co-y.co).length<1e-9 for x,y in zip(me.vertices,src.data.vertices))
for o in loaded.values():bpy.data.objects.remove(o,do_unlink=True)

# Toothbrush: a centred connected neck and oval head, with each tuft rooted
# inside the curved head face. Retain the original desk anchor and total height.
def lathe(nid,name,profile,mid,segments=48):
    v=[];f=[]
    for z,rx,ry,cx in profile:
        for i in range(segments):
            a=math.tau*i/segments;v.append((cx+rx*math.cos(a),z,ry*math.sin(a)))
    for j in range(len(profile)-1):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments;f.append((a,b,b+segments,a+segments))
    f.extend([tuple(reversed(range(segments))),tuple((len(profile)-1)*segments+i for i in range(segments))])
    o=attach(mesh(name,v,f,smooth=True),name,mid,1069,nid);o.matrix_local=Matrix.Identity(4)
    bpy.context.view_layer.update();data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);export(o);return o
lathe(1070,'toothbrush-charging-dock',[(0,.025,.025,0),(.002,.030,.030,0),(.015,.030,.030,0),(.020,.027,.027,0),(.023,.020,.020,0)],91)
lathe(1071,'toothbrush-rounded-white-handle',[(.022,.010,.010,0),(.025,.0135,.0135,0),(.030,.0145,.0145,0),(.125,.0130,.0124,0),(.145,.0115,.0107,0),(.152,.009,.0085,0),(.154,.007,.0065,0)],91)
lathe(1072,'toothbrush-head-connection-collar',[(.151,.0073,.0068,0),(.155,.0075,.007,0),(.159,.006,.0058,0)],93,32)
lathe(1073,'toothbrush-continuous-neck',[(.157,.0058,.0056,0),(.172,.0045,.0045,0),(.191,.0034,.004,-.001),(.204,.0038,.005,-.0015)],91,32)
# Original switch button stays on the front of the new handle, slightly inset.
button=obs[1074];button.location.x=-.0133;bpy.context.view_layer.update();data['nodes'][1074]['matrix']=flat(C.inverted()@button.matrix_local@C);changed.add(1074)
lathe(1075,'toothbrush-oval-brush-head',[(.198,.002,.002,-.0015),(.201,.0037,.0048,-.0015),(.207,.0041,.0065,-.0015),(.219,.0041,.0065,-.0015),(.224,.0034,.0048,-.0015),(.227,.001,.001,-.0015)],91,40)
tufts={100:([],[]),101:([],[])};roots=[]
for row in range(6):
    z=.204+row*.0035
    for col in range(4):
        y=(col-1.5)*.0031;mid=100 if col in [0,3] else 101;v,f=tufts[mid]
        # Five fine fibres per tuft; roots extend into the head, not its air gap.
        for dz,dy in [(0,0),(.00033,0),(-.00033,0),(0,.00033),(0,-.00033)]:
            start=len(v);root=-.0038;tip=-.0108+.00025*math.sin(row+col)
            for x in [root,tip]:
                for j in range(5):
                    a=math.tau*j/5;v.append((x,z+dz+.00031*math.cos(a),y+dy+.00031*math.sin(a)))
            for j in range(5):f.append((start+j,start+(j+1)%5,start+5+(j+1)%5,start+5+j))
            f.append(tuple(start+5+j for j in range(5)))
        roots.append([root,z,y])
for nid,mid in [(1076,100),(1077,101)]:
    v,f=tufts[mid];o=attach(mesh('toothbrush-rooted-bristles',v,f,smooth=True),f'toothbrush-rooted-bristles-{mid}',mid,1069,nid);o.matrix_local=Matrix.Identity(4)
    bpy.context.view_layer.update();data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);export(o)
for nid in range(1078,1096):
    obs[nid].hide_render=True;obs[nid].hide_set(True);data['nodes'][nid]['visible']=False;changed.add(nid)

result=save('props45',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'props45':{'parent':'props44a','frameFrontWidthM':.0148,'surfacePrint':print_report,'switchSource':'Courtyard43 switch28 / ce9e183','toothbrushTuftRoots':roots}})
