"""sunview34 -> shelf35. Run only through Blender Lab MCP on the complete source.

Photo-guided estimates: keep shelf/packet/cup placement; refine the softpack print,
two nested paper cups, teaspoon and the visible fragment of the wall sticker.
The supplied photo is private; only reconstructed artwork is published.
"""
from pathlib import Path
import json, math, os, gzip, copy
import bpy
from mathutils import Vector, Matrix
from mathutils.geometry import tessellate_polygon

HERE = Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text(encoding='utf8'), str(HERE/'exterior-authoring.py'), 'exec'))
assert data['revision']=='sunview34', 'Refinement requires the approved parent sunview34'
assert bpy.context.scene.get('web_revision')=='sunview34'
REV='shelf35'
ASSET=ROOT/'rooms/yongwang-jiayuan/assets/shelf-details'
collection=obs[1096].users_collection[0]

def finish(o):
    export(o)
    nid=int(o['web_node_id'])
    meta={'authoring':'Blender','blenderNode':nid,'revision':REV,'shelfDetail':True}
    data['nodes'][nid]['userData']=meta;o['web_user_data']=json.dumps(meta)
    data['geometries'][-1]['userData']['revision']=REV
    return o

def add(me,name,mid,parent,nid=None):
    o=attach(me,name,mid,parent,nid)
    return finish(o)

def mat(name,base,color=None,rough=.7,tex=None,**kw):
    mid=material(name,base,color,rough,tex if tex is not None else {},**kw)
    data['materials'][mid]['userData']={'surfaceFinish':name,'revision':REV}
    mats[mid]['web_user_data']=json.dumps(data['materials'][mid]['userData'])
    return mid

# Keep the source image as a flat, unlit albedo; no photographed wall or shelf.
im=bpy.data.images.load(str(ASSET/'tissue-front-albedo.png'),check_existing=True)
tid=len(data['textures']);td=copy.deepcopy(data['textures'][30])
td.update(id=tid,webPath='./assets/full-room/tissue-heart-print-shelf35.png',repeat=[1,1],offset=[0,0],center=[0,0],rotation=0,anisotropy=8)
data['textures'].append(td);images[tid]=im
(OUT/'tissue-heart-print-shelf35.png').write_bytes((ASSET/'tissue-front-albedo.png').read_bytes())
frontmat=mat('Softpack · reconstructed heart/bear print',102,[1,1,1],.57,{'map':tid})
# Small woven-looking noise is deliberately absent: this is plastic packaging.
grid=np.zeros((256,256,3),dtype=np.float32)
for y in range(256):
    for x in range(256):
        a=(x//32)%2;b=(y//32)%2
        grid[y,x]=([.985,.957,.858],[.972,.884,.638],[.967,.840,.522])[a+b]
gt=texture('tissue-side-gingham-shelf35',grid)
side=mat('Softpack · muted gingham sides',102,[1,1,1],.57,{'map':gt})
paper=mat('Tissue · warm white fibre',104,[.986,.978,.949],.96)

# Rounded, slightly settled softpack; six matching edge patches, no decal plane.
# Coordinates stay in the existing packet body's local frame (centre y=.047).
halves=np.array([.0615,.047,.1025]);radius=.011
front_v=[];front_f=[];front_uv=[];rest_v=[];rest_f=[];rest_uv=[]
for axis in range(3):
    for sign in [-1,1]:
        isfront=axis==0 and sign==-1
        vv,ff,uu=(front_v,front_f,front_uv) if isfront else (rest_v,rest_f,rest_uv)
        base=len(vv);N=28
        other=[i for i in range(3) if i!=axis]
        for j in range(N+1):
            for i in range(N+1):
                p=np.zeros(3);p[axis]=sign*halves[axis]
                p[other[0]]=(i/N*2-1)*halves[other[0]];p[other[1]]=(j/N*2-1)*halves[other[1]]
                q=np.clip(p,-halves+radius,halves-radius);delta=p-q;p=q+delta/np.linalg.norm(delta)*radius
                # Subtle gathered seal wrinkles, concentrated at the two ends.
                edge=abs(p[2]/halves[2])**8
                p[0]+=.0011*edge*math.sin(p[1]*210+p[2]*38)*(1-(p[1]/halves[1])**2)
                vv.append(p.tolist())
                uu.append(((p[2]+halves[2])/(2*halves[2]),(p[1]+halves[1])/(2*halves[1])) if isfront else ((p[other[1]]/halves[other[1]]+1)*.5,(p[other[0]]/halves[other[0]]+1)*.5))
        for j in range(N):
            for i in range(N):
                a=base+j*(N+1)+i;face=[a,a+1,a+N+2,a+N+1]
                p0,p1,p2=[np.array(vv[k]) for k in face[:3]]
                if np.cross(p1-p0,p2-p0)[axis]*sign<0:face.reverse()
                ff.append(face)
body=add(mesh('Softpack front',front_v,front_f,front_uv,True),'heart-print-soft-tissue-package',frontmat,1096,1097)
rest=attach(mesh('Softpack side seal',rest_v,rest_f,rest_uv,True),'softpack-gingham-rounded-sides',side,1096)
rest.matrix_local=body.matrix_local.copy();bpy.context.view_layer.update()
data['nodes'][int(rest['web_node_id'])]['matrix']=flat(C.inverted()@rest.matrix_local@C);finish(rest)

# Retain the slot's location. Two asymmetric, thin solid tissue sheets emerge
# from it; the roots fit the opening, while the tips fan gently outwards.
for k,nid in enumerate([1099,1100]):
    verts=[];faces=[];uv=[];N=26;M=24
    for j in range(M+1):
        v=j/M
        for i in range(N+1):
            u=i/N;z=(u-.5)*(.082+.042*v)
            x=(k-.5)*.002+((-1 if k==0 else 1)*(.050*v*v))+.005*math.sin(u*7+k)*v
            y=.094+v*(.057 if k==0 else .102)+.012*math.sin(u*math.pi+.5*k)*v
            if k==0:y-=.025*v**3
            verts.append([x,y,z]);uv.append([u,v])
    for j in range(M):
        for i in range(N):
            a=j*(N+1)+i;faces.append([a,a+1,a+N+2,a+N+1])
    o=attach(mesh('Folded tissue',verts,faces,uv,True),f'raised-folded-tissue-{k}',paper,1096,nid)
    activate(o);mod=o.modifiers.new('Actual paper thickness','SOLIDIFY');mod.thickness=.00018
    bpy.ops.object.modifier_apply(modifier=mod.name);finish(o)

def lathe(profile,name,parent,mid,nid=None,dy=0):
    v=[];f=[];uv=[];N=96
    for j,(r,y) in enumerate(profile):
        for i in range(N+1):
            a=i/N*2*math.pi;v.append([r*math.sin(a),y+dy,r*math.cos(a)]);uv.append([i/N,j/(len(profile)-1)])
    for j in range(len(profile)-1):
        for i in range(N):
            a=j*(N+1)+i;f.append([a,a+1,a+N+2,a+N+1])
    # Mesh normals point outwards on the rising exterior profile.
    return add(mesh(name,v,f,uv,True),name,mid,parent,nid)

# Thin tapered paper walls allow the second cup to nest without intersecting.
profile=[(.00001,.001),(.0228,.001),(.0234,.002),(.024,.006),(.031,.079)]
for i in range(13):
    a=-.1+(math.pi+.2)*i/12
    profile.append((.0308+.00115*math.cos(a),.0804+.00115*math.sin(a)))
profile +=[(.0304,.079),(.02345,.006),(.0227,.0024),(.00001,.0024)]
lathe(profile,'rolled-rim-hollow-paper-cup',1101,105,1102)
lathe(profile,'second-nested-paper-cup',1101,105,dy=.0065)

# One teaspoon, with a concave bowl, flattened oval handle and rounded end.
steel=mat('Spoon · softly brushed stainless steel',105,[.70,.72,.73],.3,metalness=.82)
def spoon_transform(p):
    x,y,z=p;a=-.32
    return [x*math.cos(a)+y*math.sin(a)+.011,-x*math.sin(a)+y*math.cos(a)+.021,z-.004]
v=[];f=[];uv=[]
# Bowl front/back joined at rim; small elliptical dished spoon, not a flat paddle.
for sideidx in range(2):
    for j in range(13):
        r=max(.001,j/12)
        for i in range(49):
            a=i/48*2*math.pi;x=.0085*r*math.cos(a);y=.014*r*math.sin(a)
            z=.0028*(1-r*r)-sideidx*.00055
            v.append(spoon_transform([x,y,z]));uv.append([i/48,j/12])
    off=sideidx*13*49
    for j in range(12):
        for i in range(48):
            a=off+j*49+i;face=[a,a+1,a+50,a+49];f.append(face if sideidx==0 else face[::-1])
for i in range(48):a=12*49+i;f.append([a,a+637,a+638,a+1])
# Elliptic sections gently widen towards the thumb end, then round to a tip.
base=len(v);rows=44;segments=16
for j in range(rows+1):
    t=j/rows;y=.012+.099*t
    radius=(.00135+.00165*t*t)*min(1,math.sqrt(max(.002,1-t))*6)
    for i in range(segments):
        a=i/segments*2*math.pi
        v.append(spoon_transform([radius*math.cos(a),y,-.0002+.00045*math.sin(a)]));uv.append([i/segments,t])
for j in range(rows):
    for i in range(segments):
        a=base+j*segments+i;b=base+j*segments+(i+1)%segments;f.append([a,b,b+segments,a+segments])
f.append([base+i for i in range(segments-1,-1,-1)]);f.append([base+rows*segments+i for i in range(segments)])
add(mesh('Concave teaspoon',v,f,uv,True),'nested-cups-stainless-teaspoon',steel,1101)

# Trace only the irregular black/white fragment actually visible in the photo.
# 35 x 27 mm is inferred relative to the cup, not a measured sticker dimension.
white=mat('Wall sticker · paper border',105,[.95,.947,.925],.88)
black=mat('Wall sticker · faded black print',105,[.10,.105,.11],.9)
taupe=mat('Wall sticker · pale fragment',105,[.67,.59,.55],.95)
def sticker_patch(name,points,mid,depth):
    # The actual interior wall is x=1.4; embed the paper's back at its surface.
    verts=[(1.4-depth,1.735+(1-vv)*.027,-.670+u*.035) for u,vv in points]
    bv=[Vector(p) for p in verts];tris=tessellate_polygon([bv])
    # Blender 5 returns indices; older supported builds return the input vectors.
    faces=[[p if isinstance(p,int) else min(range(len(bv)),key=lambda i:(bv[i]-p).length_squared) for p in tri] for tri in tris]
    o=attach(mesh(name,verts,faces,[(u,1-vv) for u,vv in points]),name,mid,0)
    # Resolve winding towards room (negative X).
    for poly in o.data.polygons:
        if poly.normal.x>0:poly.flip()
    activate(o);mod=o.modifiers.new('Paper thickness','SOLIDIFY');mod.thickness=.00015
    bpy.ops.object.modifier_apply(modifier=mod.name);o['photoEvidence']='visible fragment; identity not inferred';finish(o)
    return o
outline=[(0,.25),(.09,.02),(.24,.06),(.32,0),(.48,.10),(.65,.15),(.89,.17),(1,.39),(.93,.55),(.87,.58),(.89,.73),(.76,.78),(.66,.68),(.49,.83),(.20,1),(.12,.97),(.24,.70),(.32,.47),(.15,.49)]
sticker_patch('photo-wall-sticker-white-contour',outline,white,.0005)
sticker_patch('photo-wall-sticker-black-fragment',[(.44,.14),(.60,.18),(.87,.22),(.95,.41),(.87,.53),(.72,.58),(.56,.66),(.36,.57)],black,.00068)
sticker_patch('photo-wall-sticker-pale-fragment',[(.34,.60),(.52,.70),(.28,.89),(.21,.91)],taupe,.0007)
for i,p in enumerate([[(.15,.14),(.20,.17),(.13,.28),(.09,.30)],[(.22,.20),(.25,.22),(.20,.40),(.16,.41)],[(.26,.21),(.42,.15),(.41,.20),(.25,.27)],[(.24,.31),(.39,.27),(.41,.31),(.23,.36)]]):
    sticker_patch(f'photo-wall-sticker-ink-stroke-{i}',p,black,.0007)

# No layout, lighting, wind, interactive refs or existing material is edited.
assert changed.intersection(set(range(len(before['nodes']))))=={1097,1099,1100,1102}
assert before['refs']==data['refs']
for i,n in enumerate(before['nodes']):
    if i not in changed:assert n==data['nodes'][i],i
assert before['materials']==data['materials'][:len(before['materials'])]
assert before['textures']==data['textures'][:len(before['textures'])]
data['statistics']['shelfDetails']={'revision':REV,'parentRevision':'sunview34','nestedCups':2,'rimSeparation':.0065,'spoon':True,'wallSticker':'photo-visible fragment','changedExistingNodes':[1097,1099,1100,1102]}
# Reuse append-only writer, retaining the exterior audit rather than overwriting it.
result=save(REV,copy.deepcopy(before['statistics']['exteriorRefinement']))
result['shelfDetails']=data['statistics']['shelfDetails']
