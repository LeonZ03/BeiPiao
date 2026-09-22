"""Keep the ceramic intact; replace overlapping grout beds with true joint meshes.
Run only via Blender Lab MCP, after curtain24.
"""
import os
import bpy,bmesh,copy,gzip,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
root=Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[3])); out=root/'room-site/dist/assets/full-room'
data=json.loads((out/'scene.json').read_text(encoding='utf-8')); assert data['revision']=='curtain24'
before=copy.deepcopy(data); raw=bytearray((out/'geometry.bin').read_bytes())
report=json.loads((root/'rooms/yongwang-jiayuan/history/inputs/floor19-geometry-report.json').read_text(encoding='utf-8'))
obs={o['web_node_id']:o for o in bpy.data.objects if 'web_node_id' in o}
def store(a,size=None):
    a=np.asarray(a);a=a.astype('<u4' if a.dtype.kind in 'iu' else '<f4').ravel()
    while len(raw)%4:raw.append(0)
    d={'offset':len(raw),'length':len(a),'type':'Uint32Array' if a.dtype.kind=='u' else 'Float32Array'}
    if size:d['itemSize']=size
    raw.extend(a.tobytes());return d
summary=[]
for nid,cells,top in [(1698,report['bedroom'][:30],.01075),(1699,report['bedroom'][30:],.01075),(1700,report['bathroom'],.09570)]:
    # Split by the actual bounds, rather than relying on the original grid order.
    if nid in (1698,1699): cells=[c for c in report['bedroom'] if (c['bounds'][2]<1.8-1e-6)==(nid==1698)]
    verts=[];faces=[];lookup={}; expected_area=0
    def vertex(x,z):
        k=(round(x,9),round(z,9))
        if k not in lookup:lookup[k]=len(verts);verts.append((k[0],-k[1],top))
        return lookup[k]
    def face(points):faces.append(tuple(vertex(*p) for p in points))
    for cell in cells:
        a,b,c,d=cell['bounds'];g=cell['gap']/2;r=.0004
        outer=[(a+r,c),(b-r,c),(b,c+r),(b,d-r),(b-r,d),(a+r,d),(a,d-r),(a,c+r)]
        inner=[(a+g+r,c+g),(b-g-r,c+g),(b-g,c+g+r),(b-g,d-g-r),(b-g-r,d-g),(a+g+r,d-g),(a+g,d-g-r),(a+g,c+g+r)]
        for i in range(8):j=(i+1)%8;face([outer[i],outer[j],inner[j],inner[i]])
        for p,i,j in [((a,c),7,0),((b,c),1,2),((b,d),3,4),((a,d),5,6)]:face([p,outer[j],outer[i]])
        expected_area+=(b-a)*(d-c)-((b-a-2*g)*(d-c-2*g)-2*r*r)
    # Weld all adjacent cells, then add a small real thickness around actual
    # boundaries only. There is no broad near-coplanar sheet beneath the tiles.
    top_faces=list(faces); edges={}; n=len(verts)
    for f in top_faces:
        for a,b in zip(f,f[1:]+f[:1]):
            k=tuple(sorted((a,b)));edges[k]=edges.get(k,0)+1
    verts.extend((x,y,z-.002) for x,y,z in list(verts))
    faces.extend(tuple(v+n for v in reversed(f)) for f in top_faces)
    faces.extend((a,b,b+n,a+n) for (a,b),count in edges.items() if count==1)
    ob=obs[nid];old_mat=ob.data.materials[0]
    mesh=bpy.data.meshes.new(ob.name+'-seams-only');mesh.from_pydata(verts,[],faces)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update()
    for p in mesh.polygons:p.use_smooth=False
    uv=mesh.uv_layers.new(name='UVMap');uv1=mesh.uv_layers.new(name='uv1')
    for loop in mesh.loops:
        v=mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv=(v.x/.6+.5,v.y/.6+.5)
        uv1.data[loop.index].uv=((v.x+1.4)/2.8,(3.18+v.y)/4.98)
    mesh.materials.append(old_mat);ob.modifiers.clear();ob.data=mesh;ob.matrix_local=Matrix.Identity(4)
    ob.material_slots[0].link='DATA';ob.material_slots[0].material=old_mat
    mesh.calc_loop_triangles()
    top_area=sum(t.area for t in mesh.loop_triangles if all(abs(mesh.vertices[i].co.z-top)<1e-7 for i in t.vertices))
    assert abs(top_area-expected_area)<1e-6,(nid,top_area,expected_area)
    # Every grout top triangle is outside every ceramic footprint. Check its
    # centroid against the chamfered octagon, including the tiny corner fills.
    for t in mesh.loop_triangles:
        if not all(abs(mesh.vertices[i].co.z-top)<1e-7 for i in t.vertices):continue
        p=sum((mesh.vertices[i].co for i in t.vertices),mesh.vertices[t.vertices[0]].co*0)/3
        x,z=p.x,-p.y
        for cell in cells:
            a,b,c,d=cell['bounds'];g=cell['gap']/2;r=.0004
            dx=min(x-(a+g),(b-g)-x);dz=min(z-(c+g),(d-g)-z)
            assert not (dx>1e-7 and dz>1e-7 and dx+dz>r+1e-7),'Grout beneath ceramic'
    positions=[];normals=[];uvs=[];uv1s=[]
    for loop in mesh.loops:
        p=mesh.vertices[loop.vertex_index].co;n=mesh.corner_normals[loop.index].vector
        positions.append((p.x,p.z,-p.y));normals.append((n.x,n.z,-n.y));uvs.append(tuple(uv.data[loop.index].uv));uv1s.append(tuple(uv1.data[loop.index].uv))
    nd=data['nodes'][nid];gid=nd['geometry']
    data['geometries'][gid].update(attributes={'position':store(positions,3),'normal':store(normals,3),'uv':store(uvs,2),'uv1':store(uv1s,2)},index=store([i for t in mesh.loop_triangles for i in t.loops]),groups=[],userData={'authoring':'Blender','sourceType':'NonoverlappingGroutNetwork','floorRevision':'floor25'})
    nd['matrix']=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    nd['userData'].update(floorRevision='floor25',seamsOnly=True)
    ob['web_user_data']=json.dumps(nd['userData']);ob['floor_revision']='floor25'
    summary.append({'node':nid,'tiles':len(cells),'groutTopArea':top_area,'expectedTopArea':expected_area,'triangles':len(mesh.loop_triangles)})
changed={1698,1699,1700}; gids={before['nodes'][i]['geometry'] for i in changed}
for i,n in enumerate(data['nodes']):
    if i not in changed:assert n==before['nodes'][i]
for i,g in enumerate(data['geometries']):
    if i not in gids:assert g==before['geometries'][i]
assert data['materials']==before['materials'] and data['textures']==before['textures']
data['revision']='floor25';data['statistics']['floorRefinement'].update(seamsOnlyGrout=True,overlappingGroutUnderTiles=False)
data['statistics']['triangles']=sum(g['index']['length']//3 for g in data['geometries'])
bpy.context.scene['web_revision']='floor25';bpy.context.scene['floor_notes']='Original 69 ceramic tiles and materials preserved. Welded 2mm thick grout only inside the actual joints; no near-coplanar grout bed under tile faces.'
bpy.ops.wm.save_as_mainfile(filepath=str(root/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'))
(out/'geometry.bin').write_bytes(raw);(out/'geometry.bin.gz').write_bytes(gzip.compress(raw,compresslevel=9))
(out/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'floor25','groutMeshes':summary,'ceramicMeshesAndMaterialsUnchanged':True,'curtainContactPreserved':True}
