"""Official MCP interior17 -> interior18, updated close-up chair reference.

Importing this module is deliberately inert. The host's official Blender MCP
edit session must explicitly call ``main()`` after loading the
approved full-room scene. This function changes only objects named C43_Chair*.
Stable Chair15 node names are retained for runtime/test compatibility.
The source photos support the visible silhouette and construction, not a
measured or CAD-accurate 1:1 claim.
"""
import bpy
import bmesh
import json
import math
from mathutils import Vector


def apply_chair18():
    """Replace the chair geometry in-place while preserving its room anchor."""
    scene = bpy.context.scene
    chair_root = bpy.data.objects.get('C43_DeskChair')
    assert chair_root is not None and chair_root.type == 'EMPTY'
    assert scene.get('room_id') == 'Courtyard43'

    # Preserve the accepted centre/facing. Coordinates below are in the web
    # convention (X right, Y up, Z forward); the chair faces toward the desk.
    # The approved root is a zero-origin grouping empty; chair geometry in the
    # component uses room coordinates. Keep the accepted desk-side footprint.
    anchor_x, anchor_z = -1.35, .75
    floor_y = 0.0

    # Retire only the current chair's generated pieces. Do not touch shared
    # materials or any desk, bed, wall, or room object.
    retired = sorted(obj.name for obj in scene.objects
                     if obj != chair_root and obj.name.startswith('C43_Chair'))
    for obj in list(scene.objects):
        if obj != chair_root and obj.name.startswith('C43_Chair'):
            bpy.data.objects.remove(obj, do_unlink=True)

    collection = bpy.data.collections.get('C43_Furniture')
    assert collection is not None

    def web_to_blender(p):
        return (p[0], -p[2], p[1])

    def finish_mesh(mesh):
        # All chair meshes are closed solids. Normalize winding and add a
        # stable object-space UV map for the room exporter.
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        if bm.calc_volume(signed=True) < 0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        uv = mesh.uv_layers.new(name='UVMap')
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                co = mesh.vertices[mesh.loops[li].vertex_index].co
                uv.data[li].uv = (co.x, co.y)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        volume = bm.calc_volume(signed=True)
        bm.free()
        assert volume > 1e-10, (mesh.name, volume)

    def material(name, color, roughness, metallic=0.0):
        mat = bpy.data.materials.get(name)
        if mat is None:
            mat = bpy.data.materials.new(name)
            mat.diffuse_color = (*color, 1)
            mat.use_nodes = True
            bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
            bsdf.inputs['Base Color'].default_value = (*color, 1)
            bsdf.inputs['Roughness'].default_value = roughness
            bsdf.inputs['Metallic'].default_value = metallic
        return mat

    white = material('C43_Chair18_WhiteShell', (.78, .79, .76), .48, 0)
    nickel = material('C43_Chair18_SatinSteel', (.43, .45, .46), .38, .68)
    black = material('C43_Chair15_BlackThinSeat', (.025, .027, .026), .83)
    rubber = material('C43_Chair15_RubberFeet', (.018, .019, .018), .90)

    def parent_keep_world(obj):
        bpy.context.view_layer.update()
        matrix = obj.matrix_world.copy()
        obj.parent = chair_root
        obj.matrix_world = matrix
        if collection not in obj.users_collection:
            collection.objects.link(obj)
        return obj

    def tube(name, points, radius, mat, sides=14):
        # A swept round tube with capped ends; all control points are web-space.
        if 'ContinuousBackLeg' in name:
            # Keep round tube front entirely behind the opaque shell, including
            # the narrower rounded corners; don't cut metallic wedges into it.
            points=[(x,y,z+.010*max(0,min(1,(y-.53)/.09))) for x,y,z in points]
        pts = [Vector(web_to_blender(p)) for p in points]
        if len(pts)>=4:
            # Smooth bends in the continuous tube, retaining exact end points.
            dense=[]
            for k in range(len(pts)-1):
                a,b,c,d=pts[max(0,k-1)],pts[k],pts[k+1],pts[min(len(pts)-1,k+2)]
                for j in range(4):
                    t=j/4
                    dense.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
            pts=dense+[pts[-1]]
        verts, faces = [], []
        for i, point in enumerate(pts):
            tangent = (pts[min(i + 1, len(pts) - 1)] -
                       pts[max(0, i - 1)]).normalized()
            guide = Vector((0, 1, 0)) if abs(tangent.y) < .92 else Vector((1, 0, 0))
            u = tangent.cross(guide).normalized()
            v = tangent.cross(u).normalized()
            for j in range(sides):
                a = 2 * math.pi * j / sides
                q = point + radius * (math.cos(a) * u + math.sin(a) * v)
                verts.append(tuple(q))
        for i in range(len(pts) - 1):
            for j in range(sides):
                a = i * sides + j
                b = i * sides + (j + 1) % sides
                faces.append((a, b, b + sides, a + sides))
        faces.extend([tuple(reversed(range(sides))),
                      tuple((len(pts) - 1) * sides + j for j in range(sides))])
        mesh = bpy.data.meshes.new(name + '_Mesh')
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(mat)
        finish_mesh(mesh)
        for poly in mesh.polygons:
            poly.use_smooth = True
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj['web_tags'] = json.dumps({'noCollision': True})
        return parent_keep_world(obj)

    def rounded_box(name, center, size, mat, bevel):
        bpy.ops.mesh.primitive_cube_add(size=1, location=web_to_blender(center))
        obj = bpy.context.object
        obj.name = name
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
        obj.dimensions = (size[0], size[2], size[1])
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(mat)
        finish_mesh(obj.data)
        if bevel:
            mod = obj.modifiers.new('Soft moulded edge', 'BEVEL')
            mod.width = bevel
            mod.segments = 4
            mod.harden_normals = True
            obj.modifiers.new('Weighted corner normals', 'WEIGHTED_NORMAL')
        return parent_keep_world(obj)

    cx, floor, cz = anchor_x, floor_y, anchor_z
    # A slim black pad sits on a narrow metal seat ring; it retains the
    # photographed shallow, almost square outline and rounded corners.
    rounded_box('C43_Chair15_SeatFrame', (cx, floor + .427, cz),
                (.415, .022, .397), white, .010)
    rounded_box('C43_Chair15_BlackSeatPad', (cx, floor + .453, cz - .008),
                (.394, .022, .394), black, .017)

    # Front legs rake gently forward. The paired rear tubes are continuous:
    # each rises from the floor, sweeps behind the seat and curves up the side
    # of the back panel, matching the visible silver tubular frame.
    for side, sx in [('L', -1), ('R', 1)]:
        x = cx + sx * .183
        tube('C43_Chair15_FrontLeg_' + side,
             [(x, floor + .012, cz - .194),
              (x + sx*.002, floor + .260, cz - .184),
              (x + sx*.002, floor + .355, cz - .182),
              (x, floor + .402, cz - .164),
              (x, floor + .431, cz - .135)], .0085, nickel, 16)
        tube('C43_Chair15_ContinuousBackLeg_' + side,
             [(x, floor + .012, cz + .205),
              (x, floor + .155, cz + .198),
              (x, floor + .344, cz + .174),
              (x, floor + .440, cz + .164),
              (x + sx*.003, floor + .505, cz + .176),
              (x + sx*.005, floor + .650, cz + .199),
              (x + sx*.014, floor + .780, cz + .219),
              (x + sx*.008, floor + .868, cz + .225)], .0085, nickel, 18)
        # Side tie below the seat, plus the narrow lateral tie between the
        # rear uprights visible behind the white back shell.
        tube('C43_Chair15_SideTie_' + side,
             [(x, floor + .415, cz - .158),
              (x, floor + .415, cz + .145)], .0075, nickel, 12)
        tube('C43_Chair15_Foot_' + side,
             [(x, floor, cz - .194), (x, floor + .018, cz - .194)],
             .011, rubber, 12)
        tube('C43_Chair15_FootRear_' + side,
             [(x, floor, cz + .205), (x, floor + .018, cz + .205)],
             .011, rubber, 12)

    tube('C43_Chair15_RearCrossTie',
         [(cx - .168, floor + .305, cz + .193),
          (cx, floor + .305, cz + .198),
          (cx + .168, floor + .305, cz + .193)], .007, nickel, 12)

    # Shallow, slightly crowned white moulded back, with real thickness and
    # rounded perimeter. Its endpoints sit against the uprights.
    verts, faces = [], []
    nx, ny = 36, 20
    for layer in range(2):
        for j in range(ny + 1):
            v = j / ny
            for i in range(nx + 1):
                u = 2 * i / nx - 1
                width = .202 - .013 * (1 - v) ** 3 - .004 * abs(2 * v - 1) ** 10
                # The photographed top edge rises toward both outer corners.
                y = floor + .638 + v * .222 + .013 * abs(u) ** 2 - .003 * abs(u) ** 8
                z = cz + .193 + .024 * v + .031 * (1 - u * u) + layer * .008
                verts.append(web_to_blender((cx + width * u, y, z)))
    layer_size = (nx + 1) * (ny + 1)
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i
            faces.append((k, k + 1, k + nx + 2, k + nx + 1))
            faces.append((k + layer_size, k + nx + 1 + layer_size,
                          k + nx + 2 + layer_size, k + 1 + layer_size))
    boundary = list(range(nx + 1))
    boundary += [j * (nx + 1) + nx for j in range(1, ny + 1)]
    boundary += [ny * (nx + 1) + i for i in range(nx - 1, -1, -1)]
    boundary += [j * (nx + 1) for j in range(ny - 1, 0, -1)]
    for i, k in enumerate(boundary):
        nxt = boundary[(i + 1) % len(boundary)]
        faces.append((k, nxt, nxt + layer_size, k + layer_size))
    mesh = bpy.data.meshes.new('C43_Chair15_CurvedBack_Mesh')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(white)
    finish_mesh(mesh)
    for poly in mesh.polygons:
        poly.use_smooth = True
    back = bpy.data.objects.new('C43_Chair15_WhiteCurvedBack', mesh)
    collection.objects.link(back)
    back['web_tags'] = json.dumps({'noCollision': True})
    parent_keep_world(back)

    # The photograph has a rounded WHITE upper shell edge, not an extra
    # chrome crossbar drawn across either face. Both edges follow the shell.
    top_points = []
    for i in range(25):
        u = -1 + 2 * i / 24
        top_points.append((cx + .198 * u, floor + .860 + .013 * u*u - .003*abs(u)**8,
                           cz + .217 + .031 * (1 - u * u)+.003))
    tube('C43_Chair15_CurvedTopRail', top_points, .0042, white, 16)
    bottom_points=[(cx+.185*(-1+2*i/24),floor+.638+.013*(-1+2*i/24)**2-.003*abs(-1+2*i/24)**8,
                    cz+.196+.031*(1-(-1+2*i/24)**2)) for i in range(25)]
    tube('C43_Chair18_LowerShellLip',bottom_points,.0035,white,14)

    # Fine white loop ties wrap the two rear corners of the thin seat cushion.
    strap = material('C43_Chair15_WhiteSideTies', (.72, .73, .70), .78)
    for side, sx in [('L', -1), ('R', 1)]:
        x = cx + sx * .183
        y = floor + .443
        z = cz + .172
        loop = [(x - .010, y - .004, z), (x - .009, y + .004, z),
                (x, y + .005, z + .010), (x + .009, y + .004, z),
                (x + .010, y - .004, z), (x, y - .005, z - .010)]
        tube('C43_Chair15_SeatTieLoop_' + side, loop, .0018, strap, 8)
        # Unequal thin tails are knotted to the rear corner, as in the photo.
        tube('C43_Chair18_TieTailA_'+side,[(x,y,z),(x+sx*.019,y-.013,z+.009),
             (x+sx*.027,y-.045,z+.019),(x+sx*.023,y-.078,z+.024)],.0016,strap,8)
        tube('C43_Chair18_TieTailB_'+side,[(x,y,z),(x-sx*.011,y-.021,z+.011),
             (x-sx*.015,y-.056,z+.017)],.0016,strap,8)

    bpy.context.view_layer.update()
    created = sorted(o.name for o in scene.objects if o.name.startswith(('C43_Chair15_','C43_Chair18_')))
    return {'chair': 'C43_Chair15', 'anchorWeb': [anchor_x, anchor_z],
            'retired': retired, 'created': created, 'targets': retired + created}


def main():
    from pathlib import Path
    import hashlib, ast
    root=Path(__file__).resolve().parents[3];room=root/'rooms/Courtyard43'
    s=bpy.context.scene
    assert s.get('web_revision')=='courtyard43-interior17'
    source=root/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
    old_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    helper=room/'scripts/refine-furnishings.py'
    tree=ast.parse(helper.read_text(encoding='utf8'));ns={'hashlib':hashlib}
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),str(helper),'exec'),ns)
    before={o.name:ns['digest'](o) for o in s.objects if not o.name.startswith('C43_Chair')}
    data=apply_chair18()
    assert all(ns['digest'](bpy.data.objects[n])==v for n,v in before.items())
    assert hashlib.sha256(source.read_bytes()).hexdigest()==old_hash
    s['parent_web_revision']='courtyard43-interior17';s['web_revision']='courtyard43-interior18'
    s['chair18']='Wider shallow curved white shell, rolled white rims, bent thin steel frame, black tied pad; photo-estimated dimensions, stable anchor.'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(room/'assets/full-room/Courtyard43-interior.blend'))
    p=room/'scripts/export-interior.py';scope={'__file__':str(p)}
    exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),scope)
    result=scope['export_interior']();result['untouchedObjects']=len(before)
    report=root/'analysis/Courtyard43/dust18/model-report.json';report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(result,indent=2),encoding='utf8')
    return result
