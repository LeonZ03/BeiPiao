"""wardrobe29b -> exterior31a. Blender Lab MCP only. Preserve shadow proxies."""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='wardrobe29b'
assert bpy.context.scene.get('web_revision')=='wardrobe29b'

# Fine bark: vertical fissures with irregular length, never oversized noise bumps.
rng=np.random.default_rng(3101);y,x=np.mgrid[0:512,0:512]/512
ridge=np.sin(x*math.tau*43+.7*np.sin(y*math.tau*3)+.35*np.sin(x*31+y*22))
fissure=np.maximum(0,ridge-.68)**1.6
noise=rng.normal(0,.008,(512,512));bark=.48+.028*np.sin(x*43+y*6)-.20*fissure+noise
bark_tex=texture('exterior31-bark',np.stack([bark*1.03,bark,bark*.92],axis=-1),(2,5))
bark_height=texture('exterior31-bark-height',np.clip(.60-.85*fissure+noise,0,1),(2,5),False)
bark_mid=material('Summer poplar · fissured grey brown bark',34,color=(1,1,1),rough=.87,textures={'map':bark_tex,'bumpMap':bark_height},bumpScale=.0035)

# A neutral reflectance atlas leaves hue to the spatially coherent instance tint.
y,x=np.mgrid[0:256,0:128];y=y/256;x=x/128;midrib=np.exp(-((x-.5)/.018)**2)
vein=np.exp(-(np.sin((y+abs(x-.5)*.47)*math.tau*9)/.17)**2)*abs(x-.5)*.03
base=.88+midrib*.028+vein+.012*np.sin(x*math.tau)
leaf_tex=texture('exterior31-leaf-veins',np.stack([base*.98,base,base*.95],axis=-1))
leaf_mid=material('Summer poplar · leaf reflectance',36,color=(1,1,1),rough=.68,textures={'map':leaf_tex},metadata={'leafSurface':True})

def warp(p,variant):
    x,y,z=p;h=max(0,min(1,(y-2.6)/8.8));rad=math.hypot(x,z)
    # One smooth field for wood and leaf attachment points. Fine branch curvature
    # changes without floating leaf clusters or moving trunks/root positions.
    wave=.085*math.sin(y*1.55+x*.58+variant*1.8)*h
    return np.array([x+wave+.085*h*math.sin(z*1.1+y*.77),y+.055*h*math.sin(x*1.25+z*.91+variant),z+.095*h*math.sin(y*1.21+x*.62+variant)])

leaf_bounds=[]
for variant,(root,branch,leaf) in enumerate([(640,641,644),(645,646,649),(650,651,654)]):
    o=obs[branch];o.data=o.data.copy()
    for v in o.data.vertices:
        p=np.array([v.co.x,v.co.z,-v.co.y]);v.co=bp(warp(p,variant))
    # Smooth only the round wood; preserve original root and every shadow object.
    for f in o.data.polygons:f.use_smooth=True
    o.data.update();set_material(branch,bark_mid);export(o)
    # Three shared curved leaves, one per tree. Twelve nondegenerate triangles
    # replace sixteen (four formerly degenerate) without increasing leaf size.
    verts=[(0,0,-.128)];uvs=[(.5,0)]
    for j in [1,2,3]:
        t=j/4;w=.063*math.sin(t*math.pi)**(.79+variant*.05)
        for s in [-1,0,1]:
            verts.append((w*s*(1+.055*variant*s),.010*math.sin(t*math.pi)*(1-abs(s))+.018*(t*t)+.006*s*math.sin(t*math.pi+variant),-.128+t*.256));uvs.append(((s+1)/2,t))
    verts.append((.003*(variant-1),.018,.128));uvs.append((.5,1))
    faces=[(0,2,1),(0,3,2)]
    for j in range(2):
        for i in range(2):
            a=1+j*3+i;faces.extend([(a,a+1,a+3),(a+1,a+4,a+3)])
    faces.extend([(7,8,10),(8,9,10)])
    me=mesh(f'Poplar curved leaf variant {variant}',verts,faces,uvs,True)
    # Face orientation: leaves are double-sided, but smooth normals still matter.
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    proto=bpy.data.objects.get(f'Instance prototype {leaf}');proto.data=me;me.materials.append(mats[leaf_mid])
    if proto.material_slots:proto.material_slots[0].link='OBJECT';proto.material_slots[0].material=mats[leaf_mid]
    desc=data['nodes'][leaf];desc['geometry']=export_mesh(me,'CurvedPoplarLeaf');desc['material']=leaf_mid
    matrices=read(desc['instanceMatrix']).reshape(-1,4,4).transpose(0,2,1)
    original=matrices.copy();anchors=[]
    for M in matrices:
        a=(M@np.array([0,0,-.128,1]))[:3];anchors.append(a)
        # Affine Jacobian carries the leaf orientation with its supporting twig.
        J=np.column_stack([(warp(a+np.eye(3)[j]*.001,variant)-warp(a-np.eye(3)[j]*.001,variant))/.002 for j in range(3)])
        scale=np.linalg.norm(M[:3,:3],axis=0);R=J@M[:3,:3];u,_,vh=np.linalg.svd(R);M[:3,:3]=(u@vh)*scale
        M[:3,3]=warp(a,variant)-M[:3,:3]@np.array([0,0,-.128])
    anchors=np.array(anchors)
    # Directional canopy occlusion is baked per leaf, not real-time shadow maps.
    grid=np.floor(anchors/.48).astype(int);counts={}
    for key in map(tuple,grid):counts[key]=counts.get(key,0)+1
    local_sun=(C.inverted()@obs[root].matrix_world.inverted()@C).to_3x3()@Vector((.24,.54,-.91));local_sun.normalize();sun=np.array(local_sun)
    colors=[]
    for i,p in enumerate(anchors):
        density=sum(counts.get(tuple(np.floor((p+sun*d)/.48).astype(int)),0)*weight for d,weight in [(.48,1),(.96,.70),(1.44,.42)])
        exposure=.48+.52*math.exp(-density/38)
        patch=.5+.5*math.sin(p[0]*1.9+p[1]*.74+math.sin(p[2]*1.4)+variant*1.2)
        green=np.array([.31+.07*patch,.44+.065*patch,.205+.018*patch])
        colors.append(srgb(green)*exposure)
    colors=np.array(colors,dtype=np.float32)
    desc['instanceMatrix']=pack(matrices.transpose(0,2,1).reshape(-1),None);desc['instanceColor']=pack(colors.reshape(-1),None)
    desc['userData'].update(exteriorRefinement='exterior31a',bakedCanopyOcclusion=True,leafRoot=[0,0,-.128])
    changed.add(leaf);geometry_changed.add(leaf)
    placements=obs[leaf].data;positions=[];rotations=[];scales=[]
    for m in matrices:
        position,rotation,scale=(C@Matrix(m.tolist())@C.inverted()).decompose();positions.append(position);rotations.append(rotation.to_euler());scales.append(scale)
    placements.vertices.foreach_set('co',np.asarray(positions,dtype=np.float32).ravel())
    for name,values in [('rotation',rotations),('scale',scales)]:placements.attributes[name].data.foreach_set('vector',np.asarray(values,dtype=np.float32).ravel())
    tint=placements.attributes.get('InstanceTint') or placements.attributes.new('InstanceTint','FLOAT_COLOR','POINT')
    tint.data.foreach_set('color',np.column_stack([colors,np.ones(len(colors))]).astype(np.float32).ravel());placements.update()
    leaf_bounds.append({'node':leaf,'count':len(matrices),'anchorMaxMovement':float(np.max(np.linalg.norm(matrices[:,:3,3]-original[:,:3,3],axis=1))),'colorRange':[colors.min(axis=0).tolist(),colors.max(axis=0).tolist()]})

for n in [642,643,647,648,652,653]:assert data['nodes'][n]==before['nodes'][n]
result=save('exterior31a',{'stage':'trees','leafCount':48412,'variants':3,'trianglesPerLeaf':12,'shadowsPreserved':True,'trees':leaf_bounds})
