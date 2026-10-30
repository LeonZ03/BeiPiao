"""finish50b/finish50c -> finish50d: room-facing label normals/UV and cap fit.

Official Blender Lab MCP only. Both explicitly recognized review parents have
identical geometry; finish50c already reversed label face normals. Correct
label U orientation and hide the molded neck inside the cobalt flip cap.
"""
from pathlib import Path
import bpy,bmesh,copy
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
parent=data['revision']
assert parent==bpy.context.scene.get('web_revision') and parent in ('finish50b','finish50c')
for nid in [2039,2040,2041]:
    o=obs[nid];o.data=o.data.copy()
    if parent=='finish50b':
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for layer in o.data.uv_layers:
        for item in layer.data:item.uv.x=1-item.uv.x
    o.data.update()
    if parent=='finish50b':
        export(o);g=data['geometries'][data['nodes'][nid]['geometry']];g['attributes']['uv1']=copy.deepcopy(g['attributes']['uv'])
    else:
        g=data['geometries'][data['nodes'][nid]['geometry']];desc=g['attributes']['uv'];a=read(desc);a[:,0]=1-a[:,0]
        raw[desc['offset']:desc['offset']+desc['length']*4]=a.astype('<f4').tobytes()
        changed.add(nid);geometry_changed.add(nid)
o=obs[1529];o.data=o.data.copy();limit=.174*.84
for v in o.data.vertices:
    if v.co.z>limit:v.co.z=limit+(v.co.z-limit)*.10
o.data.update()
g=data['geometries'][data['nodes'][1529]['geometry']]
for attr,values in [('position',[(v.co.x,v.co.z,-v.co.y)for l in o.data.loops for v in [o.data.vertices[l.vertex_index]]]),('normal',[(n.vector.x,n.vector.z,-n.vector.y)for n in o.data.corner_normals])]:
    d=g['attributes'][attr];a=np.asarray(values,dtype='<f4');assert a.size==d['length'];raw[d['offset']:d['offset']+d['length']*4]=a.tobytes()
changed.add(1529);geometry_changed.add(1529)
result=save('finish50d',{'parent':parent,'reason':'Correct outward label UV direction and Safeguard molded neck under flip cap','geometry':'same index/UV layout; no appended hidden geometry on review correction'})
