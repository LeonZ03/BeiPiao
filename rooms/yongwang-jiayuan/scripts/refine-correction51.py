"""finish50e -> correction51. Official Blender Lab MCP only.

Correct the rejected brim, bottle silhouettes, exposed seat corners and
over-short helmet spoiler. Keep head pending actual close-up evidence.
"""
from pathlib import Path
import bpy, bmesh, copy, math, json
from mathutils import Vector
HERE = Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'), str(HERE/'exterior-authoring.py'), 'exec'))
assert data['revision'] == bpy.context.scene.get('web_revision') == 'finish50e'
bpy.context.preferences.filepaths.save_version = 0
exec(compile((HERE/'cap-bill51.py').read_text('utf8'), str(HERE/'cap-bill51.py'), 'exec'))
original_raw_length = len(raw)


def export_fit(o):
    """Reuse the target's own attribute capacity; append only if it grows.

    Old descriptors remain unmodified. New descriptors reference the same
    ranges only when no other active node uses them. No unrelated range changes.
    """
    nid = int(o['web_node_id']); old = data['geometries'][data['nodes'][nid]['geometry']]
    assert sum(n.get('geometry') == old['id'] for n in data['nodes']) == 1
    me = o.data; me.calc_loop_triangles()
    values = {'position': [(me.vertices[l.vertex_index].co.x, me.vertices[l.vertex_index].co.z, -me.vertices[l.vertex_index].co.y) for l in me.loops],
              'normal': [(n.vector.x, n.vector.z, -n.vector.y) for n in me.corner_normals],
              'uv': [tuple(u.uv) for u in me.uv_layers.active.data]}
    attrs = {}
    def write(values, prior, size=None, integer=False):
        a = np.asarray(values, dtype='<u4' if integer else '<f4').ravel()
        if prior and prior['type'] == ('Uint32Array' if integer else 'Float32Array') and a.size <= prior['length']:
            d = {'offset': prior['offset'], 'length': int(a.size), 'type': 'Uint32Array' if integer else 'Float32Array'}
            if size: d['itemSize'] = size
            raw[d['offset']:d['offset']+a.nbytes] = a.tobytes()
            return d
        return pack(a, size)
    for key, a in values.items(): attrs[key] = write(a, old['attributes'].get(key), 2 if key == 'uv' else 3)
    attrs['uv1'] = copy.deepcopy(attrs['uv'])
    index = write([i for t in me.loop_triangles for i in t.loops], old['index'], integer=True)
    gid = len(data['geometries'])
    data['geometries'].append({'id': gid, 'attributes': attrs, 'index': index, 'groups': [],
                              'userData': {'authoring':'Blender','sourceType':o.name,'revision':'correction51'}})
    data['nodes'][nid]['geometry'] = gid
    geometry_changed.add(nid); changed.add(nid)


def finish(o):
    me = o.data
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(me); bm.free()
    me.update()
    if not me.uv_layers:
        layer = me.uv_layers.new(name='UVMap')
        for l in me.loops:
            p = me.vertices[l.vertex_index].co; layer.data[l.index].uv = (p.x, p.z)
    export_fit(o)


def replace_mesh(nid, values):
    o = obs[nid]; materials=list(o.data.materials)
    o.data = mesh(o.name+' correction51', *values[:2], uvs=values[2], smooth=True)
    for mat in materials:o.data.materials.append(mat)
    o.modifiers.clear(); finish(o)


replace_mesh(839, bill_mesh51())
for nid, v in zip(range(847,853), [.12,.30,.48,.66,.84,.98]): replace_mesh(nid, stitch_mesh51(v))

# Recess just the old projecting lower rear seat corners. The soft shell and
# wooden legs stay exactly where approved; the base still covers the leg tops.
o = obs[1701]; o.data = o.data.copy()
for v in o.data.vertices:
    x, z = v.co.x, -v.co.y
    t = max(0., min(1., (-x-.065)/.145)); t = t*t*(3-2*t)
    v.co.y *= 1-.15*t
finish(o)

# Photo has a distinct integrated tail, between the rejected long and tiny
# versions. Reconstruct the previous coordinate before applying this extent.
for nid in [789,790,793,794,795]:
    o = obs[nid]; o.data = o.data.copy()
    for v in o.data.vertices:
        z = -v.co.y; old_z = -.104+(z+.104)/.48
        v.co.y = -(-.104+(old_z+.104)*.76)
        v.co.z += .018
    finish(o)


def hermite(profile, t):
    """Monotone PCHIP profile: continuous shoulder/waist, no linear ring kinks."""
    xs=[p[0] for p in profile]; ys=[p[1] for p in profile]
    ds=[(ys[i+1]-ys[i])/(xs[i+1]-xs[i]) for i in range(len(xs)-1)]
    slopes=[ds[0]]
    for i in range(1,len(xs)-1):
        a,b=ds[i-1],ds[i]
        if a*b<=0: slopes.append(0.)
        else:
            h0,h1=xs[i]-xs[i-1],xs[i+1]-xs[i]
            w0,w1=2*h1+h0,h1+2*h0
            slopes.append((w0+w1)/(w0/a+w1/b))
    slopes.append(ds[-1])
    k=next((i for i in range(len(xs)-1) if t<=xs[i+1]),len(xs)-2)
    h=xs[k+1]-xs[k]; q=(t-xs[k])/h
    return (2*q**3-3*q*q+1)*ys[k]+(q**3-2*q*q+q)*h*slopes[k]+(-2*q**3+3*q*q)*ys[k+1]+(q**3-q*q)*h*slopes[k+1]


# Front widths are traced from the supplied product silhouettes. Depth remains
# an explicitly estimated shallow oval. Body/cap share the same contact ring.
profiles = {
 'rejoice': [(0,.77),(.02,.84),(.09,.94),(.23,.99),(.52,1),(.68,.97),(.79,.88),(.87,.72),(.93,.53),(.945,.50),(1,.46)],
 'safeguard': [(0,.91),(.025,1),(.07,.97),(.25,.88),(.52,.88),(.73,.94),(.83,1),(.845,.96),(1,.96)],
 'lux': [(0,.93),(.02,1),(.09,1),(.80,.97),(.88,.95),(.94,.78),(.975,.36),(1,.29)]
}
specs={1528:('rejoice',.166,.060,.036,1.),1529:('safeguard',.174,.057,.034,.855),1530:('lux',.195,.074,.044,1.)}


def bottle_mesh51(height,width,depth,profile,top=1.,segments=20):
    verts,faces,uv=[],[],[]; n=64
    for j in range(segments+1):
        y=top*j/segments; r=hermite(profile,y)
        for i in range(n):
            a=i*math.tau/n
            verts.append((width*.5*r*math.sin(a),height*y,-depth*.5*r*math.cos(a)))
            uv.append((i/n,j/segments))
    for j in range(segments):
        for i in range(n):faces.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    faces += [tuple(reversed(range(n))), tuple(segments*n+i for i in range(n))]
    return verts,faces,uv


for nid,(key,height,width,depth,top) in specs.items():
    replace_mesh(nid,bottle_mesh51(height,width,depth,profiles[key],top))
    # Correct the existing label to the same continuous silhouette and outward
    # facing orientation; its original UV and image are preserved.
    lid={1528:2039,1529:2040,1530:2041}[nid]; o=obs[lid]; o.data=o.data.copy()
    coords={}
    for l in o.data.loops:
        u,vt=o.data.uv_layers.active.data[l.index].uv
        # The correction50 label UV is already readable: U=1 at positive X.
        a=(1-u*2)*.92
        old= o.data.vertices[l.vertex_index].co
        y=old.z/height; r=hermite(profiles[key],y)
        coords[l.vertex_index]=( (width*.5*r+.00035)*math.sin(a), (depth*.5*r+.00035)*math.cos(a), height*y )
    for i,p in coords.items():o.data.vertices[i].co=p
    finish(o)

# A low blue flip cap, with a broad rounded top, never a tall cylinder.
cap_profile=[(0,.98),(.07,1),(.20,1),(.75,.99),(.93,.95),(1,.88)]
replace_mesh(1531,bottle_mesh51(.174*.145,.057,.034,cap_profile,segments=8))
o=obs[1531]; o.location.z=obs[1529].location.z+.174*.855; bpy.context.view_layer.update()
data['nodes'][1531]['matrix']=flat(C.inverted()@o.matrix_local@C); changed.add(1531)

# Rejoice's integral flip-cap outline is shallow, without an exposed
# narrow neck. Continuous body has the actual shoulder slope from the photo.
# LUX pump and tissue retain their current placement and materials.
assert len(raw) < 100*1024*1024, ('Package limit',len(raw))
result=save('correction51',{'parent':'finish50e','reason':'Fix rejected continuous brim, product silhouettes, hidden chair corners and intermediate spoiler extent','head':'pending original close-up','rawGrowth':len(raw)-original_raw_length})
