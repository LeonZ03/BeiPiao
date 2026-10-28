"""props47 -> doorframe48: fit entrance trim to the wall rather than its face.

Official Blender Lab MCP only. Keep the door hinge, leaf, opening and refs fixed.
The previous casing was centred on the inner wall face: 85 mm room projection.
Closed uprights now project 12 mm, with a small clearance around the fixed leaf.
"""
from pathlib import Path
import bpy,bmesh,copy,json
from mathutils import Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props47'
targets={88,89,90,91,92}

def section(nid,polygon,lo,hi):
    o=obs[nid];inverse=o.matrix_world.inverted()
    vertices=[inverse@Vector(bp((x,y,z))) for y in [lo,hi] for x,z in polygon]
    n=len(polygon)
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new('Fitted doorframe48 %d'%nid);me.from_pydata(vertices,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bmesh.ops.bevel(bm,geom=list(bm.edges),offset=.0012,segments=3,affect='EDGES')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    uv=me.uv_layers.new(name='UVMap')
    for p in me.polygons:
        axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
        for li in p.loop_indices:
            v=me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv=(v[axes[0]]*.4,v[axes[1]]*.4)
    me.uv_layers.new(name='UV1',do_init=True)
    me.materials.append(mats[data['nodes'][nid]['material']]);o.data=me
    export(o)
    # These solid painted/wood trims have no baked lightmap. Preserve both UV
    # channels explicitly, using the same non-stretched metric mapping.
    data['geometries'][data['nodes'][nid]['geometry']]['attributes']['uv1']=copy.deepcopy(data['geometries'][data['nodes'][nid]['geometry']]['attributes']['uv'])
    o['doorframe48']='12 mm room projection; close-fitting casing and solid stop'

section(88,[(1.388,2.160),(1.552,2.160),(1.552,2.237),(1.424,2.237),(1.424,2.225),(1.388,2.225)],0,2.163)
section(89,[(1.388,3.133),(1.552,3.133),(1.552,3.194),(1.388,3.194)],0,2.163)
section(90,[(1.388,2.160),(1.552,2.160),(1.552,3.194),(1.388,3.194)],2.2075,2.2725)
section(91,[(1.388,2.160),(1.552,2.160),(1.552,3.194),(1.388,3.194)],2.163,2.2075)
section(92,[(1.424,2.237),(1.440,2.237),(1.440,3.133),(1.424,3.133)],2.148,2.163)
assert changed==targets
details={**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'doorframe48':{'parent':'props47','innerWallX':1.4,'roomFaceX':1.388,'projectionM':.012,'closedLeafSideClearanceM':.003,'unchangedDoorNodes':[1643,1644,1645,1646]}}
result=save('doorframe48',details)
