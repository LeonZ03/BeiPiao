"""finish50d -> finish50e: continue the soft rear wrap to the base underside.

Official Blender Lab MCP only. Same topology/indices/UV layout; update the
active attribute ranges in place to avoid shipping obsolete mesh copies.
"""
from pathlib import Path
import bpy,bmesh,math,copy
from mathutils import Vector,Matrix
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='finish50d'
def export_in_place(o):
    nid=int(o['web_node_id']);g=data['geometries'][data['nodes'][nid]['geometry']];me=o.data
    me.calc_loop_triangles();assert g['index']['length']==len(me.loop_triangles)*3
    attrs={'position':[(v.co.x,v.co.z,-v.co.y)for l in me.loops for v in [me.vertices[l.vertex_index]]],
           'normal':[(n.vector.x,n.vector.z,-n.vector.y)for n in me.corner_normals],
           'uv':[tuple(item.uv)for item in me.uv_layers.active.data]}
    for name,values in attrs.items():
        d=g['attributes'][name];a=np.asarray(values,dtype='<f4');assert a.size==d['length'],(nid,name)
        raw[d['offset']:d['offset']+d['length']*4]=a.tobytes()
    changed.add(nid);geometry_changed.add(nid)
ns={};exec(compile((HERE/'finish50-chair.py').read_text('utf8'),str(HERE/'finish50-chair.py'),'exec'),ns)
ctx=dict(globals());ctx['export']=export_in_place
details=ns['refine_chair50'](ctx)
result=save('finish50e',{'parent':'finish50d','chair':details,'reason':'Rear lower upholstery covers the old exposed base strip; approved seat and legs stay fixed'})
