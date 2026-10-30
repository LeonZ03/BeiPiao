"""Photo-led continuous baseball brim, shared by independent room copies.

Pure mesh construction in web X/right, Y/up, Z/front metres. Execute/import
only inside official Blender Lab MCP; it does not save or touch a scene.
"""
import math
from mathutils import Vector


def brim51(u, v):
    a = u * 1.24
    # One smooth sheet: no inverse asin, clamp seam, flared side or folded tip.
    x = .093 * math.sin(a) * (1 - .025 * v * v)
    z = .104 * math.cos(a) + .070 * v * (.40 + .60 * math.cos(a))
    y = -.0015 - .005 * v - .020 * math.sin(a)**2 * v
    return (x, y, z)


def bill_mesh51():
    nx, ny, thickness = 48, 16, .0028
    verts, uv, faces = [], [], []
    for side in (0, 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                x, y, z = brim51(i / nx * 2 - 1, j / ny)
                verts.append((x, y - side * thickness, z))
                uv.append((i / nx, j / ny))
    count = (nx + 1) * (ny + 1)
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i
            faces.extend([(k, k + 1, k + nx + 2, k + nx + 1),
                          (count+k+nx+1, count+k+nx+2, count+k+1, count+k)])
    border = list(range(nx + 1)) + [j*(nx+1)+nx for j in range(1, ny+1)]
    border += [ny*(nx+1)+i for i in range(nx-1, -1, -1)]
    border += [j*(nx+1) for j in range(ny-1, 0, -1)]
    for k, a in enumerate(border):
        b = border[(k+1) % len(border)]
        faces.append((a, a+count, b+count, b))
    return verts, faces, uv


def stitch_mesh51(v):
    verts, faces, uv = [], [], []
    path = [Vector(brim51(i/48*2-1, v)) for i in range(49)]
    for i, p in enumerate(path):
        tangent = (path[min(48, i+1)] - path[max(0, i-1)]).normalized()
        a = tangent.cross(Vector((0, 1, 0))).normalized()
        b = tangent.cross(a).normalized()
        for j in range(6):
            q = p + Vector((0, .00028, 0)) + .00018 * (a*math.cos(j*math.tau/6)+b*math.sin(j*math.tau/6))
            verts.append(tuple(q)); uv.append((i/48, j/6))
        if i:
            for j in range(6):
                faces.append(((i-1)*6+j, (i-1)*6+(j+1)%6, i*6+(j+1)%6, i*6+j))
    faces += [tuple(reversed(range(6))), tuple(48*6+j for j in range(6))]
    return verts, faces, uv
