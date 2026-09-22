"""Close the cupboard/curtain seam. Execute through Blender Lab MCP only."""
import os
import bpy, copy, gzip, json
import numpy as np
from mathutils import Vector
from pathlib import Path

root=Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[3])); out=root/'room-site/dist/assets/full-room'
data=json.loads((out/'scene.json').read_text(encoding='utf-8'))
assert data['revision']=='curtain23b', 'Apply once to the backed-up curtain23b project.'
before=copy.deepcopy(data)
raw=bytearray((out/'geometry.bin').read_bytes()); raw_before=bytes(raw)
obs={o['web_node_id']:o for o in bpy.data.objects if 'web_node_id' in o}
panel=obs[1330]; mesh=panel.data; node=data['nodes'][1330]
closed=mesh.shape_keys.key_blocks['Closed']; opened=mesh.shape_keys.key_blocks['Gathered right']
open_before=np.array([tuple(v.co) for v in opened.data])
old_left=node['userData']['closedLeft']; right=node['userData']['fixedRight']
# Use the actual cabinet door face at the curtain's depth, not the handles
# protruding farther into the room. The two faces meet without interpenetration.
door=obs[775]
left=max((door.matrix_world@Vector(c)).x for c in door.bound_box)
scale=(right-left)/(right-old_left)
for i,p in enumerate(closed.data):
    p.co.x=right-(right-p.co.x)*scale
    mesh.vertices[i].co=p.co
closed.value=0; opened.value=0
mesh.update(); bpy.context.view_layer.update(); mesh.calc_loop_triangles()

geometry=data['geometries'][node['geometry']]
assert sum(n.get('geometry')==node['geometry'] for n in data['nodes'])==1
positions=[]; normals=[]
for loop in mesh.loops:
    p=mesh.vertices[loop.vertex_index].co; n=mesh.corner_normals[loop.index].vector
    positions.append((p.x,p.z,-p.y)); normals.append((n.x,n.z,-n.y))
changed_ranges=[]
for key,values in [('position',positions),('normal',normals)]:
    desc=geometry['attributes'][key]; a=np.asarray(values,dtype='<f4').ravel()
    assert desc['type']=='Float32Array' and len(a)==desc['length']
    start=desc['offset']; end=start+a.nbytes; raw[start:end]=a.tobytes()
    changed_ranges.append((start,end))
node['userData'].update(closedLeft=left,revision='curtain24',cupboardContact=True)
panel['web_user_data']=json.dumps(node['userData'])
geometry['userData']['revision']='curtain24'
for nid in data['refs']['curtainRings']:
    d=data['nodes'][nid]; u=d['userData']['slideU']; x=left+(right-left)*u
    d['matrix'][12]=x; obs[nid].location.x=x
    d['userData'].update(closedX=x,closedWidth=right-left)
    obs[nid]['web_user_data']=json.dumps(d['userData'])
bpy.context.view_layer.update()

# Check real per-part cupboard bounds, so distant handles do not create a
# fictitious full-height exclusion strip. Touching surfaces are allowed.
wardrobe=obs[772]; boxes=[]
for ob in [wardrobe]+list(wardrobe.children_recursive):
    if ob.type!='MESH':continue
    points=np.array([tuple(ob.matrix_world@Vector(c)) for c in ob.bound_box])
    boxes.append((points.min(axis=0),points.max(axis=0),ob.name))
base=np.array([tuple(v.co) for v in closed.data]); target=np.array([tuple(v.co) for v in opened.data])
assert np.array_equal(target,open_before), 'Gathered shape changed.'
for a in np.linspace(0,1,41):
    sample=base*(1-a)+target*a
    for lo,hi,name in boxes:
        hits=np.all(sample>lo+1e-6,axis=1)&np.all(sample<hi-1e-6,axis=1)
        assert not hits.any(), f'Cloth intersects {name} at openness {a}'
    for nid in data['refs']['curtainRings']:
        d=data['nodes'][nid]; u=d['userData']['slideU']
        wd=(right-left)*(1-a)+d['userData']['openWidth']*a
        delta=right-wd+wd*u-obs[nid].location.x
        points=np.array([tuple(obs[nid].matrix_world@Vector(c)) for c in obs[nid].bound_box]); points[:,0]+=delta
        rlo=points.min(axis=0); rhi=points.max(axis=0)
        for lo,hi,name in boxes:
            assert not np.all(np.minimum(rhi,hi)-np.maximum(rlo,lo)>1e-6), f'Ring intersects {name}'
# Exact contact at the left selvage and unchanged right edge.
assert abs(base[:,0].min()-left)<5e-7
assert abs(base[:,0].max()-right)<5e-7
remaining=bytearray(raw_before)
for start,end in changed_ranges:remaining[start:end]=raw[start:end]
assert remaining==raw, 'Unrelated geometry changed.'
assert data['materials']==before['materials'] and data['textures']==before['textures']
data['revision']='curtain24'; bpy.context.scene['web_revision']='curtain24'
data['statistics']['curtainRefinement'].update(cupboardSweepGap=0,closedSelvageContact=True)
bpy.context.scene['curtain_notes']='Sparse soft folds; closed left selvage touches cabinet door edge; gathered state preserved.'
bpy.ops.wm.save_as_mainfile(filepath=str(root/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'))
(out/'geometry.bin').write_bytes(raw); zipped=gzip.compress(raw,compresslevel=9)
assert gzip.decompress(zipped)==raw
(out/'geometry.bin.gz').write_bytes(zipped)
(out/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'curtain24','closedLeft':left,'extensionMm':(old_left-left)*1000,'clothAndRingsSweepChecked':41,'gatheredShapeUnchanged':True,'materialsUnchanged':True,'unrelatedGeometryUnchanged':True,'saved':True}
