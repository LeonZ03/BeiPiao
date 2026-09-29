"""window37 -> window38: corner-side AC entry and original handles, color only.
Run via official Blender Lab MCP. Original handle geometry remains in the pack.
"""
from pathlib import Path
exec(compile((Path(__file__).parent/'exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).parent/'exterior-authoring.py'),'exec'))
assert data['revision']=='window37' and bpy.context.scene['web_revision']=='window37'
REV='window38'
def meta(nid,**extra):
    data['nodes'][nid]['userData'].update(revision=REV,**extra)
    obs[nid]['web_user_data']=json.dumps(data['nodes'][nid]['userData']);changed.add(nid)

# Restore the exact original rounded rectangular mesh and UVs, including the
# authored corner normals. Its historical binary ranges were never overwritten.
g=data['geometries'][426];positions=read(g['attributes']['position']);normals=read(g['attributes']['normal']);uv=read(g['attributes']['uv']);indices=read(g['index']).reshape(-1,3)
original=mesh('original-rounded-cabinet-handle',positions,indices,uv.tolist(),smooth=True)
original.normals_split_custom_set([bp(normals[l.vertex_index]) for l in original.loops])
mid=len(data['materials']);desc=copy.deepcopy(data['materials'][17]);desc['id']=mid
desc['colors']['color']=copy.deepcopy(data['materials'][247]['colors']['color'])
desc['userData']={'revision':REV,'surfaceFinish':'original cabinet pull, warm brown color only'}
data['materials'].append(desc)
mat=mats[17].copy();mat.name='original-handle-warm-brown';mat['web_material_id']=mid;mat['web_user_data']=json.dumps(desc['userData'])
mat.diffuse_color=(*desc['colors']['color'],1)
for node in mat.node_tree.nodes:
    if node.type=='BSDF_PRINCIPLED':node.inputs['Base Color'].default_value=(*desc['colors']['color'],1)
mats[mid]=mat
for nid in [776,778,780]:
    obs[nid].data=original;data['nodes'][nid]['geometry']=426
    data['nodes'][nid]['userData'].pop('handleFingerClearance',None)
    set_material(nid,mid);meta(nid,originalHandleGeometry=426)

# Move the sleeve 12 cm toward the existing corner, leaving its outer edge
# about 4 cm clear of the side wall. Entry remains on the window wall.
obs[1319].location.x+=.12;bpy.context.view_layer.update()
data['nodes'][1319]['matrix']=flat(C.inverted()@obs[1319].matrix_local@C)
meta(1319,cornerSideCorrection=.12)
segments=[[(1.34,2.185,-1.12),(1.352,2.177,-1.19),(1.351,2.117,-1.48),(1.316,2.086,-1.61)],
          [(1.316,2.086,-1.61),(1.291,2.064,-1.704),(1.18,2.04,-1.706),(1.18,2.04,-1.819)]]
def centers_for(route):
    points=[]
    for si,seg in enumerate(route):
        a,b,c,d=map(np.array,seg)
        for i in range(121):
            if si and i==0:continue
            t=i/120;points.append((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d)
    return np.array(points)
old=centers_for(segments)
segments[1][2]=(1.30,2.04,-1.706);segments[1][3]=(1.30,2.04,-1.819)
new=centers_for(segments)
pipe=obs[1322];pipe.data=pipe.data.copy();assert len(pipe.data.vertices)==len(old)*28
for i in range(len(old)):
    j,k=max(0,i-1),min(len(old)-1,i+1)
    old_tangent=Vector(bp(old[k]-old[j])).normalized();new_tangent=Vector(bp(new[k]-new[j])).normalized()
    turn=old_tangent.rotation_difference(new_tangent)
    for vertex in list(pipe.data.vertices)[i*28:(i+1)*28]:
        vertex.co=Vector(bp(new[i]))+turn@(vertex.co-Vector(bp(old[i])))
pipe.data.update();export(pipe);meta(1322,endpoints=[list(p) for p in new[::120]])
data['geometries'][data['nodes'][1322]['geometry']]['userData']['revision']=REV
bpy.context.view_layer.update()
assert max((pipe.matrix_world@v.co).x for v in pipe.data.vertices)<1.4
assert np.linalg.norm(new[0]-old[0])<1e-9 and abs(new[-1][0]-1.30)<1e-9
for nid in [776,778,780]:
    assert data['nodes'][nid]['matrix']==before['nodes'][nid]['matrix']
data['statistics']['windowWallRefinement'].update(revision=REV,pipeEntry=[1.30,2.04,-1.8],handles='original geometry 426; warm brown color only')
result=save(REV,copy.deepcopy(before['statistics']['exteriorRefinement']))
