"""sunlight33 -> sunview34. A small natural canopy opening toward the sun.

Run only through Blender Lab MCP. Remove a few leaves, leaving all connected
wood, wind anchors, roots and approved interior shadow proxies untouched.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='sunlight33'
assert bpy.context.scene.get('web_revision')=='sunlight33'
bpy.context.view_layer.update()
origin=np.array([-.25,1.56,-2.0]);direction=np.array([2.6,5.7,-9.]);direction/=np.linalg.norm(direction)
side=np.cross(direction,[0,1,0]);side/=np.linalg.norm(side)
up=np.cross(side,direction)
report=[]
for nid in (644,649,654):
    desc=data['nodes'][nid];o=obs[nid]
    matrices=read(desc['instanceMatrix']).reshape(-1,4,4).transpose(0,2,1)
    world=np.array(C.inverted()@o.matrix_world@C)
    centers=(world@np.column_stack([matrices[:,:3,3],np.ones(len(matrices))]).T).T[:,:3]
    relative=centers-origin;along=relative@direction
    a=relative@side;b=relative@up
    # Slightly irregular, narrow gap. The extra radius accommodates leaf
    # width and the existing breeze, rather than requiring a pixel-exact view.
    radius=.29+.025*np.sin(along*2.3)+.025*np.sin(np.arctan2(b,a)*3+along)
    keep=~((a*a+(b*1.05)**2<radius*radius)&(along>2)&(along<15))
    removed=int((~keep).sum())
    if not removed:continue
    assert removed<len(matrices)*.012,('Unexpectedly broad pruning',nid,removed)
    matrices=matrices[keep];colors=read(desc['instanceColor']).reshape(-1,3)[keep]
    placements=o.data
    attributes=[]
    for attr in placements.attributes:
        if attr.domain!='POINT' or attr.name=='position':continue
        if attr.data_type=='FLOAT_VECTOR':prop,width='vector',3
        elif attr.data_type in ('FLOAT_COLOR','BYTE_COLOR'):prop,width='color',4
        elif attr.data_type in ('FLOAT','INT','BOOLEAN'):prop,width='value',1
        else:raise AssertionError(('Unsupported placement attribute',attr.name,attr.data_type))
        values=np.empty(len(keep)*width,dtype=np.int32 if attr.data_type in ('INT','BOOLEAN') else np.float32)
        attr.data.foreach_get(prop,values)
        attributes.append((attr.name,attr.data_type,prop,values.reshape(len(keep),width)[keep].ravel()))
    coords=np.empty(len(keep)*3,dtype=np.float32);placements.vertices.foreach_get('co',coords)
    me=bpy.data.meshes.new(placements.name+' · sun opening');me.from_pydata(coords.reshape(-1,3)[keep].tolist(),[],[])
    for mat in placements.materials:me.materials.append(mat)
    for name,kind,prop,values in attributes:
        attr=me.attributes.new(name,kind,'POINT');attr.data.foreach_set(prop,values)
    me.update();o.data=me
    desc['count']=int(keep.sum());desc['instanceMatrix']=pack(matrices.transpose(0,2,1).reshape(-1));desc['instanceColor']=pack(colors.reshape(-1))
    desc['userData']['solarCanopyOpening']='sunview34';changed.add(nid)
    report.append({'node':nid,'removedLeaves':removed,'remainingLeaves':desc['count']})
assert sum(r['removedLeaves'] for r in report)==203
for nid in (640,641,642,643,645,646,647,648,650,651,652,653):assert data['nodes'][nid]==before['nodes'][nid]
details=copy.deepcopy(before['statistics']['exteriorRefinement'])
details['leafCount']=sum(data['nodes'][i]['count'] for i in (644,649,654))
for tree in details['trees']:tree['count']=data['nodes'][tree['node']]['count']
details['solarOpening']={'viewOrigin':origin.tolist(),'direction':direction.tolist(),'trees':report,'preserved':'all wood, leaf anchors, wind semantics and interior shadow proxies'}
result=save('sunview34',details)
