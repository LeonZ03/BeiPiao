"""Courtyard43 stage 1, via Blender Lab official MCP only.

Independent, deliberately provisional photo-based blockout. Only creates this
room; no Yongwang generator or asset is executed. Parameters retain evidence
status. Once structure is approved/refined, this builder refuses to overwrite
the source; make a new stage with a new filename instead.
"""
import json
from pathlib import Path
import runpy

import bpy

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / "rooms/Courtyard43"
PARAMETERS = json.loads((ROOM / "history/inputs/whitebox-06.json").read_text(encoding="utf-8"))
OUT = ROOT / "room-site/dist/assets/rooms/Courtyard43/scene.json"
if OUT.exists():
    previous = json.loads(OUT.read_text(encoding="utf-8"))
    assert previous.get("stage") == "whitebox" and not previous.get("structureApproved"), "Do not overwrite an approved/refined room"
    assert previous["revision"] in {PARAMETERS["revision"], PARAMETERS.get("parentRevision")}, "Unexpected parent revision"

# This runs in a fresh MCP background process, never in the user's active editor.
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1
scene["room_id"] = "Courtyard43"
scene["stage"] = "whitebox"
scene["web_revision"] = PARAMETERS["revision"]
scene["review_parameters"] = json.dumps(PARAMETERS, ensure_ascii=False)
scene["dimensions_source"] = PARAMETERS["dimensionSource"]


def material(name, color, alpha=1):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, alpha)
    mat.roughness = 0.83
    mat["whitebox"] = True
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, alpha)
    shader.inputs["Roughness"].default_value = 0.83
    shader.inputs["Alpha"].default_value = alpha
    return mat


wall = material("whitebox-plaster", (.70, .69, .66))
floor = material("whitebox-floor", (.36, .34, .31))
furniture = material("whitebox-furniture", (.60, .60, .57))
soft = material("whitebox-soft-volume", (.48, .49, .48))
dark = material("whitebox-frame", (.20, .21, .21))
blue = material("whitebox-radiator-landmark", (.15, .36, .39))
unknown = material("whitebox-unconfirmed-boundary", (.58, .43, .27))
glass = material("whitebox-window", (.53, .65, .69), .14)


def box(name, center, size, mat=wall, bevel=.007, **tags):
    # Author dimensions in the documented browser basis; conversion lives here.
    x, y, z = center
    sx, sy, sz = size
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -z, y))
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = (sx, sz, sy)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Finite edge radius", "BEVEL")
        modifier.width = min(bevel, min(size) / 5)
        modifier.segments = 2
    obj["web_tags"] = json.dumps(tags)
    return obj


p = PARAMETERS
r, b = p["room"], p["balcony"]
w, d, h, t = r["width"], r["depth"], r["height"], r["wall"]
cx = r.get("centerX", 0)
left, right = cx-w/2, cx+w/2
box("bedroom-floor", (cx, -.065, d/2), (w, .13, d), floor)
box("balcony-floor", (cx, -.025, -b["depth"]/2), (w, .08, b["depth"]), furniture)
box("left-wall", (left-t/2, h/2, d/2), (t, h, d), wall)
box("right-wall", (right+t/2, h/2, d/2), (t, h, d), wall, cutaway=True)
entry = p["entry"]
door_l, door_r = entry["centerX"]-entry["width"]/2, entry["centerX"]+entry["width"]/2
for name, a, c in [("entry-wall-left", left, door_l), ("entry-wall-right", door_r, right)]:
    box(name, ((a+c)/2, h/2, d+t/2), (c-a, h, t), unknown, cutaway=True, uncertain=True)
box("entry-header", (entry["centerX"], (h+entry["height"])/2, d+t/2), (entry["width"], h-entry["height"], t), unknown, cutaway=True, uncertain=True)
box("door-open-provisional", (door_r-.02, entry["height"]/2, d-entry["width"]/2), (.04, entry["height"], entry["width"]), furniture, cutaway=True, uncertain=True)
box("ceiling", (cx, h+.065, d/2), (w+.24, .13, d+.24), wall, ceilings=True)
for x in [left+.14, right-.14]:
    box("ceiling-side-border", (x, h-.1, d/2), (.28, .2, d), wall, ceilings=True)
for z in [.14, d-.14]:
    box("ceiling-cross-border", (cx, h-.1, z), (w, .2, .28), wall, ceilings=True)

opening_l, opening_r = b["openingLeft"], b["openingRight"]
for name, a, c in [("balcony-left-pier", left, opening_l), ("balcony-right-pier", opening_r, right)]:
    box(name, ((a+c)/2, h/2, -.065), (c-a, h, .13), wall)
box("balcony-opening-lintel", ((opening_l+opening_r)/2, 2.575, -.065), (opening_r-opening_l, .35, .13), wall, ceilings=True)
box("balcony-threshold", ((opening_l+opening_r)/2, .022, 0), (opening_r-opening_l, .044, .15), dark)
box("balcony-left-unconfirmed", (left-t/2, h/2, -b["depth"]/2), (t, h, b["depth"]), unknown, uncertain=True)
# V01 11.6 s establishes a glazed right return, not a full-height solid wall.
box("balcony-right-parapet", (right+.06, b["sill"]/2, -b["depth"]/2), (.12, b["sill"], b["depth"]), furniture, cutaway=True)
for z in [-b["depth"], -.05]:
    box("balcony-return-window-post", (right, (b["sill"]+b["windowTop"])/2, z), (.075, b["windowTop"]-b["sill"], .045), furniture)
for y in [b["sill"], 1.98, b["windowTop"]]:
    box("balcony-return-window-rail", (right, y, -b["depth"]/2), (.075, .045, b["depth"]), furniture)
box("balcony-return-glass", (right+.018, (b["sill"]+b["windowTop"])/2, -b["depth"]/2), (.008, b["windowTop"]-b["sill"]-.045, b["depth"]-.045), glass, 0, noCollision=True)
box("balcony-ceiling-unconfirmed", (cx, h+.05, -b["depth"]/2), (w+.24, .1, b["depth"]), unknown, ceilings=True, uncertain=True)
box("balcony-window-parapet", (cx, b["sill"]/2, -b["depth"]-.06), (w, b["sill"], .12), furniture)
box("balcony-window-header", (cx, (h+b["windowTop"])/2, -b["depth"]-.06), (w, h-b["windowTop"], .12), unknown, ceilings=True, uncertain=True)
for x in [left, left+w/3, left+2*w/3, right]:
    box("outer-window-upright", (x, (b["sill"]+b["windowTop"])/2, -b["depth"]), (.045, b["windowTop"]-b["sill"], .075), furniture)
for y in [b["sill"], 1.98, b["windowTop"]]:
    box("outer-window-horizontal", (cx, y, -b["depth"]), (w, .045, .075), furniture)
box("window-glass-provisional", (cx, (b["sill"]+b["windowTop"])/2, -b["depth"]-.018), (w-.045, b["windowTop"]-b["sill"]-.045, .008), glass, 0, noCollision=True, uncertain=True)
box("clothes-rail", (cx, 2.27, -.85), (w-.14, .025, .025), dark)

# Characteristic partition and radiator cover: recognizable massing only.
box("radiator-cover-body", (.84, .48, .08), (1.1, .96, .34), furniture)
box("radiator-cover-cap", (.84, .99, .08), (1.17, .045, .40), wall)
for y in [.29, .69]:
    box("radiator-cover-blue-crossbar", (.84, y, .263), (1.1, .12, .025), blue)
for x in [.31, .62, 1.07, 1.38]:
    box("partition-upright", (x, 1.70, -.075), (.055, 1.42, .065), furniture)
for x in [.465, 1.225]:
    box("partition-frosted-panel-volume", (x, 1.70, -.075), (.255, 1.20, .018), soft)
for y in [1.15, 1.36, 1.57, 1.78, 1.99, 2.20, 2.39]:
    box("partition-horizontal-bar", (.845, y, -.075), (.40, .035, .055), dark)
# Curtain is deliberately parked to expose the structure for review.
for x in [opening_l+.07, opening_r-.07]:
    box("curtain-parked-mass", (x, 1.20, .17), (.14, 2.34, .13), soft, .025, curtainPanels=True, noCollision=True)
box("curtain-rail", ((opening_l+opening_r)/2, 2.44, .16), (opening_r-opening_l+.2, .03, .03), furniture)

bed = p["bed"]
bx, bz = left+.06+bed["length"]/2, bed["centerZ"]
box("bed-frame", (bx, .38, bz), (bed["length"], .07, bed["width"]), furniture)
box("mattress-volume", (bx, .485, bz), (bed["length"]-.025, .14, bed["width"]-.025), soft, .035)
box("bed-headboard", (left+.065, .72, bz), (.06, .78, bed["width"]+.04), furniture, .015)
for x in [left+.13, left+bed["length"]-.05]:
    for z in [bz-bed["width"]/2+.09, bz+bed["width"]/2-.09]:
        box("bed-leg", (x, .175, z), (.04, .35, .04), furniture)
desk = p["desk"]
dx, dz = left+desk["width"]/2+.025, desk["centerZ"]
# P01, P03 and V02: long edge across the balcony-side wall, not along the
# bed-head wall. The seated user faces -Z; the chair stays on the bed side.
assert dx+desk["width"]/2 < opening_l, "Desk must end left of the balcony passage"
box("desk-top", (dx, desk["height"]-.015, dz), (desk["width"], .03, desk["depth"]), furniture, .01)
for x in [dx-desk["width"]/2+.045, dx+desk["width"]/2-.045]:
    for z in [dz-desk["depth"]/2+.045, dz+desk["depth"]/2-.045]:
        box("desk-leg", (x, (desk["height"]-.03)/2, z), (.032, desk["height"]-.03, .032), furniture)


def chair(name, x, z):
    box(name+"-seat", (x, .445, z), (.40, .05, .41), dark, .018)
    box(name+"-back", (x, .69, z+.18), (.40, .44, .035), furniture, .02)
    for xx in [x-.15, x+.15]:
        for zz in [z-.16, z+.16]:
            box(name+"-leg", (xx, .21, zz), (.024, .42, .024), furniture)


chair("desk-chair", dx, p["deskChair"]["centerZ"])
# User correction: keep the entrance clear; no spare chair by the door.
wardrobe = p["wardrobe"]
box("wardrobe-unconfirmed-volume", (right-wardrobe["depth"]/2, wardrobe["height"]/2, wardrobe["centerZ"]),
    (wardrobe["depth"], wardrobe["height"], wardrobe["width"]), furniture, .012, uncertain=True)
# V01 5.2 s shows two white doors; interior and hinge travel remain unknown.
for z in [wardrobe["centerZ"]-wardrobe["width"]/4, wardrobe["centerZ"]+wardrobe["width"]/4]:
    box("wardrobe-white-door-volume", (right-wardrobe["depth"]-.014, wardrobe["height"]/2, z),
        (.028, wardrobe["height"]-.025, wardrobe["width"]/2-.008), wall, .006)
for z in [wardrobe["centerZ"]-.055, wardrobe["centerZ"]+.055]:
    box("wardrobe-door-handle-volume", (right-wardrobe["depth"]-.05, 1.00, z), (.025, .28, .02), dark)

exporter = runpy.run_path(str(ROOM / "scripts/export-whitebox.py"))
result = exporter["export_whitebox"]()
