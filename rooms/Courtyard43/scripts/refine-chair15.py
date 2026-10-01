"""Build a photo-led chair refinement for the Courtyard43 interior.

Importing this module is deliberately inert. The host's official Blender MCP
edit session must explicitly call ``apply_chair15()`` after loading the
approved full-room scene. This function changes only objects named C43_Chair*.
The source photos support the visible silhouette and construction, not a
measured or CAD-accurate 1:1 claim.
"""
import bpy
import bmesh
import json
import math
from mathutils import Vector


def apply_chair15():
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

    white = material('C43_Chair15_WhitePaint', (.78, .79, .76), .39, .04)
    nickel = material('C43_Chair15_SatinSteel', (.43, .45, .46), .31, .72)
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
        pts = [Vector(web_to_blender(p)) for p in points]
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
                (.390, .030, .390), white, .008)
    rounded_box('C43_Chair15_BlackSeatPad', (cx, floor + .453, cz - .008),
                (.394, .022, .394), black, .013)

    # Front legs rake gently forward. The paired rear tubes are continuous:
    # each rises from the floor, sweeps behind the seat and curves up the side
    # of the back panel, matching the visible silver tubular frame.
    for side, sx in [('L', -1), ('R', 1)]:
        x = cx + sx * .171
        tube('C43_Chair15_FrontLeg_' + side,
             [(x, floor + .012, cz - .194),
              (x, floor + .115, cz - .181),
              (x, floor + .284, cz - .158),
              (x, floor + .431, cz - .145)], .009, nickel, 16)
        tube('C43_Chair15_ContinuousBackLeg_' + side,
             [(x, floor + .012, cz + .205),
              (x, floor + .155, cz + .204),
              (x, floor + .344, cz + .164),
              (x, floor + .421, cz + .155),
              (x, floor + .505, cz + .163),
              (x, floor + .670, cz + .188),
              (x - sx * .004, floor + .828, cz + .205),
              (x - sx * .012, floor + .884, cz + .202)], .009, nickel, 18)
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
    nx, ny = 24, 18
    for layer in range(2):
        for j in range(ny + 1):
            v = j / ny
            for i in range(nx + 1):
                u = 2 * i / nx - 1
                width = .183 - .012 * (1 - v) ** 3 - .008 * abs(2 * v - 1) ** 10
                # The photographed top edge rises toward both outer corners.
                y = floor + .621 + v * .252 + .018 * abs(u) ** 1.8 * v ** 7 - .007 * abs(u) ** 8
                z = cz + .192 + .025 * v + .012 * (1 - u * u) + layer * .006
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

    # Curved upper crossbar follows the raised top corners and meets both
    # uprights, completing the visible tube-to-back connection.
    top_points = []
    for i in range(25):
        u = -1 + 2 * i / 24
        top_points.append((cx + .171 * u, floor + .621 + .252 + .018 * abs(u) ** 1.8,
                           cz + .192 + .025 + .012 * (1 - u * u)))
    tube('C43_Chair15_CurvedTopRail', top_points, .008, nickel, 16)

    # Fine white loop ties wrap the two rear corners of the thin seat cushion.
    strap = material('C43_Chair15_WhiteSideTies', (.72, .73, .70), .78)
    for side, sx in [('L', -1), ('R', 1)]:
        x = cx + sx * .170
        y = floor + .443
        z = cz + .172
        loop = [(x - .010, y - .004, z), (x - .009, y + .004, z),
                (x, y + .005, z + .010), (x + .009, y + .004, z),
                (x + .010, y - .004, z), (x, y - .005, z - .010)]
        tube('C43_Chair15_SeatTieLoop_' + side, loop, .0018, strap, 8)

    bpy.context.view_layer.update()
    created = sorted(o.name for o in scene.objects if o.name.startswith('C43_Chair15_'))
    return {'chair': 'C43_Chair15', 'anchorWeb': [anchor_x, anchor_z],
            'retired': retired, 'created': created, 'targets': retired + created}
