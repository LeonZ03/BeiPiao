"""Continuous rear/side upholstery refinement for the existing chair.

Imported by the finish50 coordinator inside official Blender Lab MCP only.
No standalone scene creation, file saving, material changes or room rebuild.
Keep the approved seat, wooden legs, lumbar cushion and root transform intact.
The added corner fullness is a restrained inference from the room photograph.
"""


def refine_chair50(ns):
    bpy, bmesh, math = ns['bpy'], ns['bmesh'], ns['math']
    Vector = ns['Vector']
    obs, export, changed = ns['obs'], ns['export'], ns['changed']
    data = ns['data']
    targets = (1282, 1702, 1703, 1705, 1706, 1707)
    # All surfaces below use the original chair's local web coordinates.
    # The root matrix is untouched; applying it again would move the chair.
    bp = lambda p: (p[0], -p[2], p[1])
    identity = tuple(tuple(r) for r in obs[1280].matrix_local)
    untouched = {i: (obs[i].data, tuple(tuple(r) for r in obs[i].matrix_local))
                 for i in (1281, 1283, 1284, 1285, 1286, 1287, 1701, 1704, 1708)}
    for i in targets:
        assert obs[i].type == 'MESH', i
        assert obs[i].parent == obs[1280], (i, 'unexpected chair parent')
    # X/Z/top/recline-weight: preserve .96m back height, .49m front arm tip,
    # existing width and forward reach. A broad cubic corner replaces the
    # old three independent rectangular rear caps and their overlapping piping.
    controls = [
        (.244, -.225, .492, 0.), (.150, -.235, .510, .06),
        (-.020, -.236, .590, .20), (-.115, -.230, .750, .60),
        (-.165, -.205, .920, .95), (-.180, -.140, .958, 1.),
        (-.188, 0., .960, 1.),
        (-.180, .140, .958, 1.), (-.165, .205, .920, .95),
        (-.115, .230, .750, .60), (-.020, .236, .590, .20),
        (.150, .235, .510, .06), (.244, .225, .492, 0.)
    ]
    per_segment, nv = 8, 28

    def curve(segment, t):
        a = controls[max(0, segment-1)]
        b = controls[segment]
        c = controls[segment+1]
        d = controls[min(len(controls)-1, segment+2)]
        return tuple(.5*((2*b[k])+(-a[k]+c[k])*t+
                          (2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+
                          (-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t)
                     for k in range(4))

    stations = [curve(j, k/per_segment)
                for j in range(len(controls)-1) for k in range(per_segment)]
    stations.append(controls[-1])
    count, stride = len(stations), nv+1
    length = [0.]
    for a, b in zip(stations, stations[1:]):
        length.append(length[-1]+math.hypot(b[0]-a[0], b[1]-a[1]))
    verts, uv, faces, face_region = [], [], [], []
    for side in (1, -1):
        for i, (x, z, top, recline) in enumerate(stations):
            prev, nex = stations[max(0, i-1)], stations[min(count-1, i+1)]
            dx, dz = nex[0]-prev[0], nex[1]-prev[1]
            norm = math.hypot(dx, dz)
            nx, nz = -dz/norm, dx/norm
            for j in range(stride):
                v = j/nv
                # The lower rear edge reaches the existing upholstered base;
                # it does not form another projecting horizontal frame.
                bottom = .399
                y = bottom+(top-bottom)*v
                swelling = max(0., math.sin(math.pi*v))**.44
                half = .006+(.014+.014*max(0., min(1., recline)))*swelling
                # Turn the lower rear shell back over the existing under-seat
                # edge (x about -.227). A merely longer vertical back would
                # leave that old projecting shelf exposed from behind.
                rear_wrap = .045*(1-v)**3*max(0., min(1., recline))
                xx = x-.20*(y-.47)*recline-rear_wrap + side*half*nx
                zz = z+side*half*nz
                verts.append(bp((xx, y, zz)))
                uv.append((length[i]/.06, y/.06))
    offset = count*stride

    def region(column):
        return 1702 if column < 4*per_segment else 1282 if column < 8*per_segment else 1703

    def add(face, owner):
        faces.append(face)
        face_region.append(owner)

    for i in range(count-1):
        owner = region(i)
        for j in range(nv):
            a, b = i*stride+j, (i+1)*stride+j
            add((a, a+1, b+1, b), owner)
            add((offset+a, offset+b, offset+b+1, offset+a+1), owner)
        for j in (0, nv):
            a, b = i*stride+j, (i+1)*stride+j
            add((a, b, offset+b, offset+a), owner)
    for i in (0, count-1):
        for j in range(nv):
            a = i*stride+j
            add((a, offset+a, offset+a+1, a+1), region(min(i, count-2)))

    whole = bpy.data.meshes.new('Finish50 continuous upholstery normal reference')
    whole.from_pydata(verts, [], faces)
    whole.update()
    bm = bmesh.new(); bm.from_mesh(whole)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(whole); bm.free(); whole.update()
    for f in whole.polygons:
        f.use_smooth = True
    # Capture shared normals before partitioning. Without this, closed caps on
    # each named piece would pull the outside corner normals into visible seams.
    shared = [[tuple(whole.corner_normals[li].vector) for li in f.loop_indices]
              for f in whole.polygons]
    stats = []
    ranges = {1702: (0, 4*per_segment), 1282: (4*per_segment, 8*per_segment),
              1703: (8*per_segment, count-1)}
    for nid in (1282, 1702, 1703):
        selected = [f.index for f in whole.polygons if face_region[f.index] == nid]
        original_faces = [tuple(whole.polygons[k].vertices) for k in selected]
        internal = []
        start, end = ranges[nid]
        for i in (start, end):
            if i in (0, count-1):
                continue
            for j in range(nv):
                a = i*stride+j
                internal.append((a, a+1, offset+a+1, offset+a))
        # Regions retain solid individual data and stable exported IDs. Their
        # mating caps are hidden inside the padding, never a visible patch.
        combined = original_faces+internal
        used = sorted({v for f in combined for v in f})
        remap = {v: k for k, v in enumerate(used)}
        me = bpy.data.meshes.new('Finish50 upholstery '+str(nid))
        me.from_pydata([verts[k] for k in used], [],
                       [tuple(remap[v] for v in f) for f in combined])
        me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(me); bm.free(); me.update()
        # Recalculation can flip polygon corner order. Match custom normals by
        # global vertex ID rather than relying on the original loop order.
        normal_by_face = [{v: normal for v, normal in
                           zip(whole.polygons[k].vertices, shared[k])}
                          for k in selected]
        layer = me.uv_layers.new(name='UVMap')
        for f in me.polygons:
            f.use_smooth = f.index < len(selected)
            for li in f.loop_indices:
                old_id = used[me.loops[li].vertex_index]
                layer.data[li].uv = uv[old_id]
        me.uv_layers.new(name='UV1', do_init=True)
        normals = [tuple(n.vector) for n in me.corner_normals]
        for f in me.polygons[:len(selected)]:
            for li in f.loop_indices:
                old_id = used[me.loops[li].vertex_index]
                normals[li] = normal_by_face[f.index][old_id]
        me.normals_split_custom_set(normals)
        me.update()
        o = obs[nid]
        old_materials = list(o.data.materials)
        for material in old_materials:
            me.materials.append(material)
        o.data = me
        o['finish50_chair'] = 'continuous U corner with shared external normals; original root/seat/legs'
        bm = bmesh.new(); bm.from_mesh(me)
        assert all(e.is_manifold for e in bm.edges), (nid, 'open upholstery region')
        assert all(f.calc_area() > 1e-12 for f in bm.faces), (nid, 'zero area upholstery')
        bm.free()
        export(o); changed.add(nid)
        stats.append({'node': nid, 'vertices': len(me.vertices), 'faces': len(me.polygons)})
    bpy.data.meshes.remove(whole)

    # One subtle, continuous top seam. The old closed rear/arm loops created
    # three overlapping rectangular outlines across the back of the chair.
    def seam_mesh(name, path, radius=.00065, sides=6):
        vv, ff = [], []
        for j, p in enumerate(path):
            tangent = (Vector(path[min(j+1, len(path)-1)])-
                       Vector(path[max(0, j-1)])).normalized()
            helper = Vector((0, 1, 0))
            a = tangent.cross(helper).normalized()
            b = tangent.cross(a).normalized()
            for k in range(sides):
                v = Vector(p)+radius*(math.cos(k*math.tau/sides)*a+
                                     math.sin(k*math.tau/sides)*b)
                vv.append(bp(v))
            if j:
                for k in range(sides):
                    q = (k+1)%sides
                    ff.append(((j-1)*sides+k, (j-1)*sides+q,
                               j*sides+q, j*sides+k))
        ff.extend([tuple(reversed(range(sides))),
                   tuple((len(path)-1)*sides+k for k in range(sides))])
        me = bpy.data.meshes.new(name)
        me.from_pydata(vv, [], ff); me.update()
        bm = bmesh.new(); bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(me); bm.free(); me.update()
        layer = me.uv_layers.new(name='UVMap')
        for f in me.polygons:
            f.use_smooth = True
            for li in f.loop_indices:
                v = me.vertices[me.loops[li].vertex_index].co
                layer.data[li].uv = (v.x/.06, v.z/.06)
        me.uv_layers.new(name='UV1', do_init=True)
        return me

    # In the same web-local coordinates as the surface, at its rounded top.
    seam = [(x-.20*(top-.47)*weight, top+.00025, z)
            for x, z, top, weight in stations]
    for nid, shell in ((1705, 1282), (1706, 1702), (1707, 1703)):
        lo, hi = ranges[shell]
        o = obs[nid]
        mats = list(o.data.materials)
        me = seam_mesh('Finish50 continuous upper seam '+str(nid), seam[lo:hi+1])
        for material in mats:
            me.materials.append(material)
        o.data = me
        o['finish50_chair'] = 'thin upper seam only; no closed intersecting rear rectangle'
        export(o); changed.add(nid)
    assert tuple(tuple(r) for r in obs[1280].matrix_local) == identity
    for nid, (mesh, matrix) in untouched.items():
        assert obs[nid].data == mesh and tuple(tuple(r) for r in obs[nid].matrix_local) == matrix, nid
    bpy.context.view_layer.update()
    return {'nodes': list(targets), 'surfaces': stats,
            'note': 'Continuous rounded back/arm corners and lower rear wrap; shared boundary normals; thin continuous upper seam; original seat, legs, lumbar cushion and placement unchanged.'}
