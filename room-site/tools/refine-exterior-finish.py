"""exterior31 -> exterior31c. Indexed leaf export and clear window glazing.

Run through Blender Lab MCP against the saved exterior31 source. Preserve every
triangle/normal/UV and the approved interior illumination and shadow proxies.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='exterior31'
assert bpy.context.scene.get('web_revision')=='exterior31'
leaf_vertices=[]
for nid in (644,649,654):
    d=data['nodes'][nid];g=copy.deepcopy(data['geometries'][d['geometry']])
    attrs={key:read(a) for key,a in g['attributes'].items()}
    # Equal corner attributes can share a GPU vertex without changing normals,
    # UV seams, the leaf silhouette or the breeze's leaf-root coordinate.
    unique={};first=[];remap=[]
    for i in range(len(attrs['position'])):
        key=tuple(float(x) for a in attrs.values() for x in a[i])
        if key not in unique:unique[key]=len(first);first.append(i)
        remap.append(unique[key])
    old_index=read(g['index']).astype(int)
    for key,a in attrs.items():g['attributes'][key]=pack(a[first],a.shape[1])
    g['index']=pack(np.array(remap,dtype=np.uint32)[old_index]);g['id']=len(data['geometries'])
    data['geometries'].append(g);d['geometry']=g['id'];changed.add(nid);geometry_changed.add(nid)
    assert len(first)<=11
    leaf_vertices.append(len(first))

# The room's glazing was a warm, diffusely shaded white surface, which laid a
# milky veil over near trees. Keep the glass itself and its reflections, with a
# small, clear coating rather than altering room exposure, fog or sun shafts.
glass=material('Bay window · clear thin glazing',16,color=(.93,.98,1),rough=.10,textures={},opacity=.012)
for nid in (166,172,178):set_material(nid,glass)
details=copy.deepcopy(before['statistics']['exteriorRefinement'])
details.update(indexedLeafVertices=leaf_vertices,clearBayGlazing=True)
result=save('exterior31c',details)
