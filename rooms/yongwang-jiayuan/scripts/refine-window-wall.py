"""shelf36 -> window37. Photo-guided window-wall, AC route and cabinet pulls.

Execute only through Blender Lab MCP against the current complete source.
Dimensions are estimates from the owner's photograph, not measurements.
"""
from pathlib import Path
exec(compile((Path(__file__).parent/'exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).parent/'exterior-authoring.py'),'exec'))
assert data['revision']=='shelf36' and bpy.context.scene['web_revision']=='shelf36'
REV='window37'
LEFT=-.86; OLD_RIGHT=1.08; RIGHT=.78
FACTOR=(RIGHT-LEFT)/(OLD_RIGHT-LEFT)
def mapx(x): return LEFT+(x-LEFT)*FACTOR
def metadata(nid,**extra):
    d=data['nodes'][nid];d['userData'].update(revision=REV,**extra)
    obs[nid]['web_user_data']=json.dumps(d['userData']);changed.add(nid)
def transform(nid):
    bpy.context.view_layer.update()
    data['nodes'][nid]['matrix']=flat(C.inverted()@obs[nid].matrix_local@C);changed.add(nid)
def deform_world_x(nid,fn):
    o=obs[nid];o.data=o.data.copy();mw=o.matrix_world.copy();inv=mw.inverted()
    for v in o.data.vertices:
        p=mw@v.co;p.x=fn(p.x);v.co=inv@p
    o.data.update();export(o)
def resize_span(nid):
    o=obs[nid];xs=[(o.matrix_world@v.co).x for v in o.data.vertices]
    lo,hi=min(xs),max(xs);center=(lo+hi)/2
    if hi-lo<.20:
        deform_world_x(nid,lambda x:x+mapx(center)-center)
    else:
        # Preserve bevels and end cross-sections instead of squashing them.
        a,b=mapx(lo),mapx(hi);edge=min(.045,(hi-lo)*.08)
        def remap(x):
            if x<lo+edge:return a+x-lo
            if x>hi-edge:return b+x-hi
            return a+edge+(x-lo-edge)*(b-a-2*edge)/(hi-lo-2*edge)
        deform_world_x(nid,remap)

# Retain the room corner, cupboard, desk, sill depth and window height.
deform_world_x(74,lambda x:RIGHT+(x-OLD_RIGHT)*(1.4-RIGHT)/(1.4-OLD_RIGHT))
for nid in [75,76,152,153,*range(155,173),*range(183,192)]:
    if obs[nid].type=='MESH':resize_span(nid)
# Right-hinged inward sash: shorten its horizontal members but retain hardware,
# frame thickness and the approved 0.12 rad opening / drying-rail clearance.
sash=obs[173];sash.location.x=mapx(sash.location.x);transform(173)
for nid in range(174,182):
    o=obs[nid];o.data=o.data.copy();xs=[v.co.x for v in o.data.vertices]
    width=max(xs)-min(xs);center=(max(xs)+min(xs))/2
    # Coordinates are relative to the hinge, including the mesh origin.
    shift=(o.location.x+center)*(FACTOR-1)
    if width<.20:
        o.location.x+=shift
    else:
        half=width/2;edge=.024
        for v in o.data.vertices:
            x=v.co.x-center
            if abs(x)>half-edge:v.co.x=center+math.copysign(half*FACTOR-(half-abs(x)),x)
            else:v.co.x=center+x*(half*FACTOR-edge)/(half-edge)
        o.location.x+=shift
    o.data.update();transform(nid);export(o)
metadata(151,apertureLeft=LEFT,apertureRight=RIGHT,photoEstimated=True)

# Curtain retains its weave, sparse folds, thickness, fringe, left contact and
# gathered width. Export both absolute morph shapes with freshly computed normals.
panel=obs[1330];me=panel.data;closed=me.shape_keys.key_blocks['Closed'];opened=me.shape_keys.key_blocks['Gathered right']
left=data['nodes'][1330]['userData']['closedLeft'];right=.83
for i,p in enumerate(closed.data):
    p.co.x=left+(p.co.x-left)*(right-left)/(1.13-left);me.vertices[i].co=p.co
for p in opened.data:p.co.x-=.30
closed.value=0;opened.value=0;me.update()
export(panel);g=data['geometries'][data['nodes'][1330]['geometry']]
tmp=me.copy()
for i,v in enumerate(tmp.vertices):v.co=opened.data[i].co
tmp.update();positions=[];normals=[]
for l in tmp.loops:
    p=tmp.vertices[l.vertex_index].co;n=tmp.corner_normals[l.index].vector
    positions.append((p.x,p.z,-p.y));normals.append((n.x,n.z,-n.y))
g['morphTargets']={'position':[pack(positions,3)],'normal':[pack(normals,3)]}
bpy.data.meshes.remove(tmp)
metadata(1330,fixedRight=right,closedLeft=left,openWidth=.345)
for nid in data['refs']['curtainRings']:
    u=data['nodes'][nid]['userData']['slideU'];x=left+(right-left)*u
    obs[nid].location.x=x;transform(nid)
    metadata(nid,closedX=x,fixedRight=right,closedWidth=right-left)
deform_world_x(1476,lambda x:-1.1+(x+1.1)*(2.35-.30)/2.35)
obs[1478].location.x-=.30;transform(1478)

# A raised, warm brown U pull. The open middle provides real finger clearance.
pullmat=material('warm-brown-cabinet-pulls',data['nodes'][776]['material'],color=(.43,.32,.205),rough=.48,textures={},metadata={'exteriorSurface':False,'revision':REV})
# Profile in local X/Y, extruded across Z. Door face lies at X=-0.0155 here.
profile=[(-.016,-.098),(.020,-.098),(.020,.098),(-.016,.098),(-.016,.080),(.008,.080),(.008,-.080),(-.016,-.080)]
verts=[(x,y,z) for z in [-.007,.007] for x,y in profile]
faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
for nid in [776,778,780]:
    o=obs[nid];o.data=mesh('raised-brown-pull',verts,faces)
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.0018,segments=3,affect='EDGES')
    bm.to_mesh(o.data);bm.free();o.data.update();set_material(nid,pullmat);export(o)
    metadata(nid,handleFingerClearance=.0235,photoEstimated=True)

# Pipe sleeve normal points into the room from the window wall (web +Z),
# replacing the erroneous side-wall penetration. No AC/body/cable reposition.
sleeve=obs[1319]
web=Matrix.Translation(Vector((1.18,2.04,-1.790)))@Matrix.Rotation(math.pi/2,4,'X')
sleeve.matrix_local=C@web@C.inverted();transform(1319)
metadata(1319,wall='window-wall',wallPlaneZ=-1.8)
# Slightly irregular elliptical insulation with a shallow helical tape lap.
# Bezier route has tangent continuity, terminates inside the sleeve and starts
# inside the underside of the existing AC housing.
segments=[[(1.34,2.185,-1.12),(1.352,2.177,-1.19),(1.351,2.117,-1.48),(1.316,2.086,-1.61)],
          [(1.316,2.086,-1.61),(1.291,2.064,-1.704),(1.18,2.04,-1.706),(1.18,2.04,-1.819)]]
centers=[]
for si,seg in enumerate(segments):
    a,b,c,d=map(np.array,seg)
    for i in range(121):
        if si and i==0:continue
        t=i/120;centers.append((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d)
centers=np.array(centers);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(centers,axis=0),axis=1))]
verts=[];uv=[];faces=[];sides=28
for i,p in enumerate(centers):
    tangent=centers[min(i+1,len(centers)-1)]-centers[max(0,i-1)];tangent/=np.linalg.norm(tangent)
    u=np.cross(tangent,[0,1,0]);u/=np.linalg.norm(u);v=np.cross(tangent,u)
    for j in range(sides):
        th=2*math.pi*j/sides;lap=(arc[i]/.025-th/(2*math.pi))%1
        r=.027*(1+.023*math.sin(arc[i]*51)+.012*math.cos(th*3+arc[i]*17))+.00065*math.exp(-((lap-.88)/.085)**2)
        verts.append(tuple(p+r*(math.cos(th)*u+.89*math.sin(th)*v)));uv.append((j/sides,arc[i]/.025))
for i in range(len(centers)-1):
    for j in range(sides):
        k=i*sides+j;n=i*sides+(j+1)%sides;faces.append((k,n,n+sides,k+sides))
faces.extend([tuple(reversed(range(sides))),tuple(range((len(centers)-1)*sides,len(centers)*sides))])
pipe=obs[1322];pipe.data=mesh('wrapped-ac-insulation',verts,faces,uv,smooth=True)
set_material(1322,data['nodes'][1322]['material'])
bm=bmesh.new();bm.from_mesh(pipe.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pipe.data);bm.free();pipe.data.update()
export(pipe);metadata(1322,endpoints=[list(p) for p in centers[::120]],wall='window-wall',wrapPitch=.025)

# Bounds and whole-motion checks before saving. No hidden source-only changes.
bpy.context.view_layer.update()
base=np.array([tuple(v.co) for v in closed.data]);target=np.array([tuple(v.co) for v in opened.data])
assert abs(base[:,0].min()-left)<1e-6 and abs(base[:,0].max()-right)<1e-6
for ob in [obs[772]]+list(obs[772].children_recursive):
    if ob.type!='MESH':continue
    p=np.array([tuple(ob.matrix_world@Vector(c)) for c in ob.bound_box]);lo=p.min(axis=0);hi=p.max(axis=0)
    for t in np.linspace(0,1,41):
        sample=base*(1-t)+target*t
        assert not (np.all(sample>lo+1e-6,axis=1)&np.all(sample<hi-1e-6,axis=1)).any(),(ob.name,t)
assert centers[-1][2]<-1.8 and RIGHT+.06<centers[-1][0]<1.4-.06
data['statistics']['windowWallRefinement']={'revision':REV,'apertureRight':RIGHT,'closedCurtainRight':right,'visibleWallWidth':1.4-right,'pipeEntry':[1.18,2.04,-1.8],'dimensions':'estimated from owner photograph','clothSweepSamples':41}
for nid in geometry_changed:data['geometries'][data['nodes'][nid]['geometry']]['userData']['revision']=REV
result=save(REV,copy.deepcopy(before['statistics']['exteriorRefinement']))
