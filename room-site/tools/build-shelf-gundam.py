"""Build the photo-matched shelf Gundam as a browser-ready, Y-up mesh asset.

Authoring coordinates use Blender X/right, -Y/front, Z/up.  Export converts to
X/right, Y/up, Z/front.  The model stands on Y=0 in the exported asset.
"""
import bpy
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist/assets/shelf-gundam"
SOURCE = ROOT.parent / "generated-assets/shelf-gundam"
OUT.mkdir(parents=True, exist_ok=True)
SOURCE.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

PALETTE = {
    "armor": ((0.63, 0.66, 0.65, 1), 0.05, 0.34),
    "armorLight": ((0.79, 0.81, 0.78, 1), 0.03, 0.3),
    "edgeGrey": ((0.29, 0.31, 0.34, 1), 0.22, 0.3),
    "frame": ((0.075, 0.082, 0.105, 1), 0.35, 0.25),
    "navy": ((0.025, 0.038, 0.072, 1), 0.18, 0.3),
    "red": ((0.64, 0.018, 0.014, 1), 0.12, 0.24),
    "yellow": ((0.95, 0.55, 0.015, 1), 0.05, 0.26),
    "green": ((0.05, 0.86, 0.38, 1), 0.18, 0.12),
    "gunmetal": ((0.11, 0.12, 0.15, 1), 0.58, 0.2),
}

mats = {}
objects = []
for name, (color, metal, rough) in PALETTE.items():
    m = bpy.data.materials.new(name)
    m.diffuse_color = color
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = color
    bs.inputs["Metallic"].default_value = metal
    bs.inputs["Roughness"].default_value = rough
    if name == "green":
        bs.inputs["Emission Color"].default_value = (0.01, 0.6, 0.18, 1)
        bs.inputs["Emission Strength"].default_value = 1.25
    mats[name] = m


def finish(o, mat, bevel=0.0, smooth=False):
    o.data.materials.append(mats[mat])
    if bevel:
        mod = o.modifiers.new("machined bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
    if smooth:
        for p in o.data.polygons:
            p.use_smooth = True
    objects.append(o)
    return o


def box(name, loc, scale, mat="armor", bevel=0.025, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, mat, bevel)


def taper(name, loc, bottom, top, height, mat="armor", bevel=0.02, rot=(0, 0, 0)):
    bx, by = bottom
    tx, ty = top
    z0, z1 = -height / 2, height / 2
    verts = [(-bx/2,-by/2,z0),(bx/2,-by/2,z0),(bx/2,by/2,z0),(-bx/2,by/2,z0),
             (-tx/2,-ty/2,z1),(tx/2,-ty/2,z1),(tx/2,ty/2,z1),(-tx/2,ty/2,z1)]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return finish(o, mat, bevel)


def sloped_box(name, loc, width, depth, front_height, rear_height, mat="armor", bevel=0.02, rot=(0,0,0)):
    """A long foot/cover wedge, low at -Y (front) and high at +Y (rear)."""
    w, d = width/2, depth/2
    verts = [(-w,-d,0),(w,-d,0),(w,d,0),(-w,d,0),
             (-w,-d,front_height),(w,-d,front_height),(w,d,rear_height),(-w,d,rear_height)]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
    o = bpy.data.objects.new(name,me); bpy.context.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot
    return finish(o,mat,bevel)


def prism(name, profile, depth, mat="armor", bevel=0.015, y=-0.02):
    """Extrude an X/Z front profile through Y; profile points are clockwise."""
    n = len(profile)
    verts = [(x, y-depth/2, z) for x,z in profile] + [(x, y+depth/2, z) for x,z in profile]
    faces = [tuple(range(n)), tuple(range(2*n-1, n-1, -1))]
    for i in range(n):
        j = (i + 1) % n
        faces.append((i, j, n+j, n+i))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    return finish(o, mat, bevel)


def cylinder(name, loc, radius, depth, mat="frame", vertices=12, rot=(0,0,0), smooth=True):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.object
    o.name = name
    return finish(o, mat, 0.008 if radius > 0.045 else 0.003, smooth)


def sphere(name, loc, scale, mat="frame", segments=16):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=8, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, mat, 0, True)


def bone(name, a, b, width, depth, mat="frame", bevel=0.02):
    a, b = Vector(a), Vector(b)
    mid = (a + b) * 0.5
    vec = b - a
    o = box(name, mid, (width, depth, vec.length), mat, bevel)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0,0,1)).rotation_difference(vec.normalized())
    return o


def rod(name, a, b, radius, mat="frame", vertices=10):
    a, b = Vector(a), Vector(b)
    vec = b - a
    mid = (a+b)*0.5
    o = cylinder(name, mid, radius, vec.length, mat, vertices)
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = Vector((0,0,1)).rotation_difference(vec.normalized())
    return o


def joint(name, loc, r=0.11, axis="Y"):
    rot = (math.pi/2, 0, 0) if axis == "Y" else (0, math.pi/2, 0)
    cylinder(name+"-outer", loc, r, r*1.16, "edgeGrey", 16, rot)
    cylinder(name+"-hub", (loc[0], loc[1]-0.005, loc[2]), r*.55, r*1.28, "frame", 12, rot)


# Feet: long sloping toe shells, narrow ankles, and an outward display stance.
for s in (-1, 1):
    x = s * 0.39
    yaw = -s * 0.055
    sloped_box(f"foot-red-sole-{s}", (x,-0.055,0.0), .42,.66,.10,.15,"red",.028,(0,0,yaw))
    sloped_box(f"foot-main-wedge-{s}", (x,-0.08,0.12), .38,.55,.11,.24,"armorLight",.025,(0,0,yaw))
    sloped_box(f"foot-toe-shell-{s}", (x,-0.29,0.19), .36,.22,.06,.16,"armor",.022,(0,0,yaw))
    prism(f"foot-dark-instep-{s}", [(x-.10,.23),(x+.10,.23),(x+.075,.34),(x-.075,.34)], .15, "edgeGrey", .012, -.13)
    taper(f"ankle-white-collar-{s}", (x,0.055,0.34), (.32,.25), (.27,.22), .14, "armorLight", .022, (0,-s*.04,yaw))
    joint(f"ankle-{s}", (x,0.02,0.37), .09, "Y")

    # Tapered calf with a raised center plate and real side facets.
    taper(f"lower-leg-core-{s}", (x-s*.02,0.015,0.65), (.34,.29), (.25,.23), .57, "armor", .032, (0,-s*.055,-s*.025))
    prism(f"shin-front-plate-{s}", [(x-.14,.42),(x+.14,.42),(x+.105,.75),(x+.065,.86),(x-.065,.86),(x-.105,.75)], .065, "armorLight", .016, -.17)
    box(f"shin-panel-groove-{s}", (x,-.211,.64), (.018,.012,.25), "edgeGrey", .003)
    box(f"shin-top-groove-{s}", (x,-.212,.77), (.17,.012,.017), "edgeGrey", .002)
    box(f"calf-side-armor-{s}", (x+s*.155,.06,.65), (.09,.25,.38), "armorLight", .022, (0,s*.09,0))
    box(f"calf-yellow-mark-{s}", (x+s*.175,-.096,.57), (.025,.02,.14), "yellow", .005, (0,s*.12,0))
    joint(f"knee-{s}", (x,-.005,.91), .115, "Y")
    prism(f"knee-cap-{s}", [(x-.145,.80),(x+.145,.80),(x+.12,1.02),(x,1.08),(x-.12,1.02)], .14, "armorLight", .024, -.13)

    # Thigh core and floating armor panels.
    taper(f"thigh-{s}", (s*.34,.025,1.20), (.27,.25), (.34,.31), .48, "armorLight", .032, (0,-s*.075,-s*.018))
    box(f"thigh-front-panel-{s}", (s*.35,-.165,1.22), (.16,.035,.29), "armor", .012, (0,-s*.07,-s*.018))
    box(f"thigh-panel-line-{s}", (s*.35,-.186,1.22), (.012,.008,.18), "edgeGrey", .002)
    joint(f"hip-joint-{s}", (s*.29,.01,1.46), .115, "X")

# Pelvis mechanics and five overlapping skirt plates.
box("pelvis-frame", (0,.01,1.43), (.54,.34,.30), "frame", .05)
box("waist-ring-low", (0,-.005,1.57), (.47,.32,.13), "edgeGrey", .05)
cylinder("waist-pivot", (0,0,1.64), .19, .24, "frame", 16)
prism("front-skirt-center", [(-.075,1.61),(.075,1.61),(.10,1.35),(0,1.27),(-.10,1.35)], .11, "armorLight", .014, -.225)
# Four separate tapered leaves reveal the dark hip frame between their overlaps.
prism("front-skirt-inner-left", [(-.055,1.59),(-.12,1.61),(-.30,1.55),(-.31,1.32),(-.20,1.23),(-.10,1.31)], .105, "armorLight", .016, -.205)
prism("front-skirt-inner-right", [( .055,1.59),( .12,1.61),( .30,1.55),( .31,1.32),( .20,1.23),( .10,1.31)], .105, "armorLight", .016, -.205)
for s in (-1,1):
    outer = [(s*.27,1.55),(s*.45,1.52),(s*.50,1.35),(s*.40,1.24),(s*.29,1.29)]
    prism(f"front-skirt-outer-{s}", outer, .10, "armor", .017, -.17)
    box(f"skirt-panel-notch-{s}", (s*.27,-.268,1.43), (.07,.010,.014), "edgeGrey", .002, (0,0,s*.16))
    taper(f"side-skirt-{s}", (s*.49,.02,1.44), (.14,.25), (.20,.29), .31, "armor", .024, (0,s*.12,0))

# Torso: dark block with grey ribs, yellow slatted vents and long red sternum.
taper("torso-dark", (0,.015,1.80), (.60,.35), (.83,.39), .47, "navy", .055)
taper("upper-chest-armor", (0,-.03,1.97), (.76,.32), (.66,.30), .22, "edgeGrey", .035)
box("lower-chest-frame", (0,-.205,1.69), (.46,.07,.17), "frame", .025)
prism("red-chest-keel", [(-.052,2.02),(.052,2.02),(.055,1.66),(0,1.59),(-.055,1.66)], .068, "red", .014, -.238)
for s in (-1,1):
    # Recessed vent frame, bright panel, and four raised grille ribs.
    box(f"chest-vent-frame-{s}", (s*.255,-.236,1.86), (.27,.06,.18), "frame", .025)
    box(f"chest-yellow-vent-{s}", (s*.255,-.273,1.86), (.235,.025,.145), "yellow", .022)
    for i in range(4):
        box(f"chest-vent-rib-{s}-{i}", (s*.255,-.293,1.815+i*.031), (.18,.012,.009), "edgeGrey", .002)
    box(f"chest-green-lamp-{s}", (s*.405,-.246,2.015), (.035,.025,.065), "green", .005)

# Backpack and tall aerials visible behind the head.
box("backpack", (0,.23,1.97), (.55,.24,.45), "frame", .035)
for s in (-1,1):
    box(f"backpack-rail-{s}", (s*.29,.20,2.17), (.105,.12,.53), "edgeGrey", .018, (0,s*.10,-s*.12))
    rod(f"backpack-antenna-{s}", (s*.28,.22,2.32), (s*.34,.21,2.72), .018, "gunmetal", 8)

# Neck and layered Gundam helmet.
cylinder("neck", (0,0,2.08), .12, .17, "frame", 14)
box("head-core", (0,-.02,2.20), (.34,.29,.32), "armorLight", .045)
prism("face-mask", [(-.12,2.18),(-.09,2.08),(0,2.045),(.09,2.08),(.12,2.18),(.075,2.21),(-.075,2.21)], .065, "armor", .018, -.215)
prism("red-chin", [(-.042,2.085),(.042,2.085),(.046,2.03),(0,2.005),(-.046,2.03)], .07, "red", .010, -.235)
# A dark visor slot separates the two narrow luminous eyes.
prism("black-eye-band", [(-.145,2.275),(.145,2.275),(.13,2.205),(-.13,2.205)], .035, "frame", .008, -.226)
box("helmet-brow", (0,-.236,2.29), (.31,.045,.055), "armorLight", .014)
for s in (-1,1):
    # glowing eye, temple housing and cheek vent.
    if s < 0:
        eye = [(-.125,2.255),(-.035,2.252),(-.045,2.225),(-.112,2.226)]
    else:
        eye = [( .035,2.252),( .125,2.255),( .112,2.226),( .045,2.225)]
    prism(f"green-eye-{s}", eye, .012, "green", .003, -.248)
    box(f"temple-block-{s}", (s*.19,-.035,2.22), (.11,.28,.24), "edgeGrey", .025)
    box(f"cheek-vent-{s}", (s*.135,-.235,2.12), (.07,.018,.07), "frame", .008, (0,0,s*.16))
box("forehead-green-camera", (0,-.235,2.405), (.055,.018,.07), "green", .004)
prism("forehead-red-crest", [(-.045,2.39),(.045,2.39),(.058,2.31),(0,2.275),(-.058,2.31)], .055, "red", .010, -.248)
box("helmet-top", (0,-.01,2.38), (.24,.26,.16), "armorLight", .035)
rod("helmet-spike", (0,.02,2.42), (0,.02,2.69), .015, "edgeGrey", 8)
# V-fin triangles are thin solid prisms, not texture decals.
prism("v-fin-left", [(-.015,2.35),(-.36,2.56),(-.12,2.32)], .025, "yellow", .006, -.25)
prism("v-fin-right", [( .015,2.35),( .36,2.56),( .12,2.32)], .025, "yellow", .006, -.25)

# Arms: layered shoulder shells, cylindrical joints, long forearms.
# Viewer-left arm hangs and grips the rifle.
prism("left-shoulder-armor", [(-.48,2.03),(-.82,2.06),(-.90,1.88),(-.77,1.77),(-.49,1.83)], .34, "armor", .035, -.01)
box("left-shoulder-panel", (-.69,-.205,1.94), (.20,.018,.12), "armorLight", .008, (0,0,-.10))
joint("left-shoulder-joint", (-.54,0,1.89), .12, "Y")
bone("left-upper-arm", (-.67,0,1.82), (-.76,-.01,1.56), .20,.22,"armorLight",.03)
joint("left-elbow", (-.78,-.01,1.51), .10, "Y")
bone("left-forearm", (-.79,-.01,1.47), (-.91,-.03,1.23), .23,.24,"armor",.03)
box("left-forearm-panel", (-.89,-.17,1.34), (.11,.035,.20), "armorLight", .012, (0,-.08,-.30))

# Viewer-right arm bends up behind the shield.
prism("right-shoulder-armor", [(.48,2.03),(.82,2.06),(.90,1.88),(.77,1.77),(.49,1.83)], .34, "armor", .035, -.01)
box("right-shoulder-panel", (.69,-.205,1.94), (.20,.018,.12), "armorLight", .008, (0,0,.10))
joint("right-shoulder-joint", (.54,0,1.89), .12, "Y")
bone("right-upper-arm", (.67,0,1.83), (.81,-.01,1.62), .20,.22,"armorLight",.03)
joint("right-elbow", (.84,-.015,1.61), .10, "Y")
bone("right-forearm", (.86,-.015,1.64), (.94,-.03,1.90), .23,.24,"armor",.03)
box("right-forearm-panel", (.91,-.18,1.78), (.12,.035,.20), "armorLight", .012, (0,.06,.28))

# Mechanical hands and separately readable gripping fingers.
for side, cx, cz in (("left",-.95,1.19),("right",.98,1.96)):
    sphere(f"{side}-palm", (cx,-.11,cz), (.105,.085,.10), "frame", 12)
    for i in range(4):
        x = cx + (i-1.5)*.032
        rod(f"{side}-finger-{i}", (x,-.19,cz+.035), (x,-.21,cz-.055), .016, "edgeGrey", 8)
    rod(f"{side}-thumb", (cx-.07 if side=='right' else cx+.07,-.18,cz+.03), (cx-.10 if side=='right' else cx+.10,-.20,cz-.025), .019, "edgeGrey", 8)

# Rifle: one continuous downward axis with an angular receiver, stock and foregrip.
prism("rifle-angular-receiver", [(-1.055,.83),(-.96,1.18),(-.88,1.44),(-.78,1.47),(-.755,1.34),(-.86,.94),(-.94,.82)], .15, "gunmetal", .018, -.25)
prism("rifle-side-plate", [(-1.015,.94),(-.93,1.22),(-.875,1.38),(-.815,1.39),(-.885,1.08),(-.95,.91)], .022, "edgeGrey", .006, -.336)
bone("rifle-long-barrel", (-1.21,-.25,.27), (-1.00,-.25,.92), .07,.065,"gunmetal",.010)
bone("rifle-foregrip", (-1.105,-.26,.56), (-.99,-.26,.92), .13,.13,"gunmetal",.014)
box("rifle-muzzle-block", (-1.215,-.25,.24), (.09,.09,.15), "frame", .010, (0,-.29,-.29))
rod("rifle-bore", (-1.245,-.25,.15), (-1.20,-.25,.30), .020, "frame", 10)
# Stock continues the receiver's line instead of forming a hammer-like crossbar.
bone("rifle-stock-spine", (-.82,-.23,1.40), (-.60,-.20,1.54), .105,.11,"gunmetal",.014)
prism("rifle-stock-butt", [(-.67,1.43),(-.55,1.48),(-.51,1.61),(-.61,1.66),(-.73,1.55)], .12, "gunmetal", .015, -.21)
bone("rifle-pistol-grip", (-.87,-.26,1.24), (-.94,-.26,1.08), .075,.09,"frame",.012)
prism("rifle-magazine", [(-.96,1.05),(-.85,1.08),(-.84,.84),(-.93,.78),(-1.00,.84)], .105, "gunmetal", .014, -.255)
rod("rifle-top-rail", (-.91,-.33,1.35), (-.73,-.29,1.53), .016, "edgeGrey", 8)
box("rifle-front-sight", (-.93,-.315,1.25), (.045,.04,.12), "edgeGrey", .007, (0,-.20,-.29))
box("rifle-trigger-guard", (-.88,-.335,1.18), (.09,.022,.07), "frame", .010, (0,0,-.29))

# Tall raised shield, with an angular pale shell and deep navy inset.
shield_profile = [(0.89,2.68),(1.01,2.82),(1.30,2.68),(1.34,2.10),(1.26,1.61),(1.12,1.46),(.98,1.55),(.91,1.96)]
prism("shield-shell", shield_profile, .12, "armorLight", .028, -.25)
shield_inset = [(.96,2.61),(1.05,2.72),(1.23,2.61),(1.26,2.13),(1.19,1.87),(1.02,1.91),(.97,2.05)]
prism("shield-navy-inset", shield_inset, .026, "navy", .012, -.321)
prism("shield-yellow-inset", [(1.05,1.84),(1.20,1.79),(1.17,1.59),(1.09,1.63)], .028, "yellow", .008, -.324)
box("shield-red-crossbar", (1.18,-.337,1.57), (.29,.045,.085), "red", .012, (0,0,.05))
for x in (.98,1.27):
    rod("shield-top-prong", (x,-.25,2.66), (x+(.03 if x>1 else -.03),-.25,2.92), .022, "armorLight", 8)
box("shield-grip", (1.02,-.11,1.96), (.10,.14,.28), "gunmetal", .018)

# Small armor fasteners and raised technical panels.
for s in (-1,1):
    cylinder(f"shoulder-fastener-{s}", (s*.69,-.221,1.97), .025, .018, "edgeGrey", 12, (math.pi/2,0,0))
    cylinder(f"knee-fastener-{s}", (s*.36,-.205,.95), .022, .018, "edgeGrey", 12, (math.pi/2,0,0))
    box(f"chest-clavicle-{s}", (s*.23,-.218,2.015), (.22,.035,.055), "yellow", .01, (0,0,-s*.22))


def export_asset():
    deps = bpy.context.evaluated_depsgraph_get()
    by_mat = {k: {"name": f"gundam-{k}", "material": k, "position": [], "normal": [], "uv": [], "index": []} for k in PALETTE}
    mins = [1e9,1e9,1e9]
    maxs = [-1e9,-1e9,-1e9]
    triangle_count = 0
    for ob in objects:
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        mx = ob.matrix_world
        nm = mx.to_3x3().inverted().transposed()
        matname = ob.data.materials[0].name
        d = by_mat[matname]
        seen = {}
        for tri in me.loop_triangles:
            triangle_count += 1
            for li in tri.loops:
                co = mx @ me.vertices[me.loops[li].vertex_index].co
                no = (nm @ me.corner_normals[li].vector).normalized()
                # Blender (x,y,z) -> browser (x,z,-y), with front +Z.
                p = (round(co.x,6), round(co.z,6), round(-co.y,6))
                n = (round(no.x,5), round(no.z,5), round(-no.y,5))
                uv = (0.0,0.0)
                key = p+n+uv
                if key not in seen:
                    seen[key] = len(d["position"])//3
                    d["position"].extend(p)
                    d["normal"].extend(n)
                    d["uv"].extend(uv)
                    for j in range(3):
                        mins[j] = min(mins[j], p[j]); maxs[j] = max(maxs[j], p[j])
                d["index"].append(seen[key])
        ev.to_mesh_clear()
    meshes = [d for d in by_mat.values() if d["index"]]
    palette = {name: {"color": list(v[0]), "metalness": v[1], "roughness": v[2]} for name,v in PALETTE.items()}
    result = {
        "metadata": {
            "name": "Photo-matched shelf Gundam",
            "authoring": "Blender " + bpy.app.version_string,
            "units": "normalized model units",
            "upAxis": "Y", "frontAxis": "+Z", "floorY": 0,
            "bodyHeight": 2.72, "overallHeight": round(maxs[1],6),
            "triangleCount": triangle_count, "drawCount": len(meshes),
            "usage": "Create one BufferGeometry per meshes entry; apply palette[mesh.material]. Model already stands on y=0."
        },
        "bounds": {"min": [round(v,6) for v in mins], "max": [round(v,6) for v in maxs]},
        "palette": palette,
        "meshes": meshes
    }
    (OUT/"models.js").write_text("export default "+json.dumps(result,separators=(",",":"))+";\n", encoding="utf-8")
    return result


result = export_asset()

# Save the reusable source scene, then add a non-exported studio for preview.
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/"shelf-gundam.blend"))

ground_mat = bpy.data.materials.new("previewGround")
ground_mat.diffuse_color = (0.055,0.062,0.075,1)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0,0,0))
ground = bpy.context.object; ground.data.materials.append(ground_mat)

bpy.ops.object.light_add(type="AREA", location=(-3,-4,6)); bpy.context.object.data.energy=950; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=4
bpy.ops.object.light_add(type="AREA", location=(4,-1,3)); bpy.context.object.data.energy=650; bpy.context.object.data.size=3
bpy.ops.object.light_add(type="AREA", location=(0,4,4)); bpy.context.object.data.energy=800; bpy.context.object.data.size=2
bpy.ops.object.camera_add(location=(4.0,-8.2,3.25))
cam = bpy.context.object
direction = Vector((0,-.02,1.43)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.55
bpy.context.scene.camera = cam
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 760; scene.render.resolution_y = 900; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(SOURCE/"shelf-gundam-preview.png")
scene.render.film_transparent = False
scene.world = bpy.data.worlds.new("previewWorld")
scene.world.color = (0.018,0.022,0.03)
scene.view_settings.look = 'AgX - Medium High Contrast'
bpy.ops.render.render(write_still=True)
print("SHELF_GUNDAM_EXPORTED", json.dumps(result["metadata"]), result["bounds"], flush=True)
