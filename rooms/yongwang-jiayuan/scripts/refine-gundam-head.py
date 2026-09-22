"""Reduce only the named head assembly. Run via official Blender Lab MCP."""
import os
import bpy, json, gzip, copy
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

root=Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[3]))
out=root/'room-site/dist/assets/full-room'
data=json.loads((out/'scene.json').read_text(encoding='utf-8'))
assert data['revision']=='floor25'
before=copy.deepcopy(data)
source=json.loads((root/'rooms/yongwang-jiayuan/history/inputs/viewer26-head-points.json').read_text())
points=[Vector((x,y,z-source['floor'])) for x,y,z in source['points']]
tree=KDTree(len(points))
for i,p in enumerate(points):tree.insert(p,i)
tree.balance()
factor=.80
pivot=Vector((0,0,2.44-source['floor']))
web_pivot=np.array((pivot.x,pivot.z,-pivot.y))
raw=bytearray((out/'geometry.bin').read_bytes());original_raw=bytes(raw)
obs={o['web_node_id']:o for o in bpy.data.objects if 'web_node_id' in o}
changes=[]
def selected(p,tolerance):return tree.find(p)[2]<tolerance
types={'Float32Array':'<f4','Int16Array':'<i2','Uint16Array':'<u2','Uint32Array':'<u4'}
for nid in range(1252,1263):
    node=data['nodes'][nid];ob=obs[nid];mesh=ob.data
    original=np.array([tuple(v.co) for v in mesh.vertices])
    mask=np.array([selected(v.co,3e-6) for v in mesh.vertices])
    for face in mesh.polygons:
        flags=mask[list(face.vertices)]
        assert flags.all() or not flags.any(),(nid,'partial Blender polygon')
    if not mask.any():continue
    desc=data['geometries'][node['geometry']]['attributes']['position']
    packed=np.frombuffer(raw,dtype=types[desc['type']],count=desc['length'],offset=desc['offset']).copy().reshape(-1,3)
    positions=packed.astype(np.float32)
    if 'decodeScale' in desc:positions=positions*np.array(desc['decodeScale'])+np.array(desc['decodeOffset'])
    # Quantized web vertices have at most half a cell of uncertainty.
    tolerance=max(3e-6,np.linalg.norm(desc.get('decodeScale',[0,0,0]))*.6+2e-6)
    web_mask=np.array([selected(Vector((x,-z,y)),tolerance)for x,y,z in positions])
    geometry=data['geometries'][node['geometry']]
    ix=geometry['index'];indices=np.frombuffer(raw,dtype=types[ix['type']],count=ix['length'],offset=ix['offset']).copy().reshape(-1,3)
    flags=web_mask[indices]
    assert np.all(np.all(flags,axis=1)|~np.any(flags,axis=1)),(nid,'partial exported triangle')
    assert web_mask.any(),(nid,'head missing in export')
    for v,is_head in zip(mesh.vertices,mask):
        if is_head:v.co=pivot+(v.co-pivot)*factor
    mesh.update()
    unchanged=np.array([tuple(v.co)for v in mesh.vertices])[~mask]
    assert np.array_equal(unchanged,original[~mask]),'Body geometry changed'
    positions[web_mask]=web_pivot+(positions[web_mask]-web_pivot)*factor
    # Uniform scaling keeps normals, UVs, indices and all materials unchanged.
    new=positions.astype('<f4').ravel();raw.extend(b'\0'*((-len(raw))%4));offset=len(raw);raw.extend(new.tobytes())
    geometry['attributes']['position']={'type':'Float32Array','offset':offset,'length':len(new),'itemSize':3}
    changes.append({'node':nid,'blenderVertices':int(mask.sum()),'webVertices':int(web_mask.sum())})
assert {c['node']for c in changes}=={1252,1253,1254,1255,1257,1258,1260,1262},changes
assert raw[:len(original_raw)]==original_raw
assert data['materials']==before['materials'] and data['textures']==before['textures']
assert data['nodes']==before['nodes']
bpy.context.view_layer.update()
data['revision']='viewer26';bpy.context.scene['web_revision']='viewer26'
data['statistics']['gundamHeadRefinement']={'scale':factor,'parts':len(source['parts']),'bodyUnchanged':True,'neckPivot':list(pivot)}
bpy.ops.wm.save_as_mainfile(filepath=str(root/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'))
(out/'geometry.bin').write_bytes(raw);(out/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9))
(out/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
# Keep the editable miniature source consistent without regenerating the room.
bpy.ops.wm.open_mainfile(filepath=str(root/'rooms/yongwang-jiayuan/assets/shelf-gundam/shelf-gundam.blend'))
bpy.context.view_layer.update()
original_pivot=Vector((0,0,2.44))
transform=Matrix.Translation(original_pivot)@Matrix.Scale(factor,4)@Matrix.Translation(-original_pivot)
for name in source['parts']:
    ob=bpy.data.objects[name];ob.matrix_world=transform@ob.matrix_world
bpy.context.scene['head_scale_revision26']=factor
bpy.ops.wm.save_as_mainfile(filepath=str(root/'rooms/yongwang-jiayuan/assets/shelf-gundam/shelf-gundam.blend'))
result={'revision':'viewer26','headScale':factor,'changedMeshes':changes,'headParts':len(source['parts']),'bodyAndPoseUnchanged':True,'savedFullRoomAndMiniature':True}
