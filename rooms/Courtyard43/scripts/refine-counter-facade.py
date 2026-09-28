"""Photo-led counter facade only; execute with official Blender Lab MCP.

architecture05 -> architecture06, then interior04 -> interior05.
The approved envelope and all non-counter objects/materials remain unchanged.
Slat count, recess depth and fabrication dimensions are photo estimates.
"""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROOM = ROOT / 'rooms/Courtyard43'
scene = bpy.context.scene
component = scene.get('component') == 'architecture'
assert (scene.get('component_revision') == 'architecture05' if component
        else scene.get('web_revision') == 'courtyard43-interior04')
assert scene['source_layout'] == 'courtyard43-whitebox06'
bpy.context.preferences.filepaths.save_version = 0
targets = {o.name for o in scene.objects if o.name.startswith('C43_Radiator_')}
assert len(targets) == 5

def digest(o):
    h = hashlib.sha256(repr((o.name, tuple(tuple(r) for r in o.matrix_world),
        o.parent.name if o.parent else None, dict(o.items()))).encode())
    if o.type == 'MESH':
        h.update(repr(([tuple(v.co) for v in o.data.vertices],
            [(tuple(p.vertices), p.material_index) for p in o.data.polygons],
            [(u.name, [tuple(d.uv) for d in u.data]) for u in o.data.uv_layers],
            [m.name for m in o.data.materials])).encode())
    return h.hexdigest()

before = {o.name: digest(o) for o in scene.objects if o.name not in targets}
original_materials = {m.name: (tuple(m.diffuse_color),
    tuple((n.name, tuple((s.name, str(s.default_value)) for s in n.inputs
        if hasattr(s, 'default_value'))) for n in m.node_tree.nodes))
    for m in bpy.data.materials if m.use_nodes}

def variant(source, name, color, roughness):
    m = bpy.data.materials[source].copy()
    m.name = name
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for socket in ['Base Color', 'Roughness', 'Metallic']:
        assert not p.inputs[socket].is_linked
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = 0
    m.diffuse_color = (*color, 1)
    return m

paint = variant('C43_Aged_ivory_painted_trim', 'C43_Counter_Ivory_Paint', (.76,.74,.68), .48)
blue = variant('C43_Muted_teal_radiator_stripes', 'C43_Counter_Blue_Inset_Paint', (.045,.28,.355), .48)
skirt = variant('C43_Dark_red_brown_skirt', 'C43_Counter_Dark_red_brown_skirt', (.15,.046,.03), .52)
recess = variant('C43_Aged_ivory_painted_trim', 'C43_Counter_Recess_Backing', (.20,.16,.12), .78)

def box(lo, hi, material):
    # Inputs are web coordinates: X horizontal, Y up, Z roomward.
    c = [(lo[i]+hi[i])/2 for i in range(3)]
    d = [hi[i]-lo[i] for i in range(3)]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(c[0],-c[2],c[1]))
    o = bpy.context.object
    o.dimensions = (d[0],d[2],d[1])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(material)
    return o

def finish(o, bevel):
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    if bevel:
        mod = o.modifiers.new('Small manufactured edge', 'BEVEL')
        mod.width, mod.segments = bevel, 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in o.data.polygons:
        p.use_smooth = p.area < .001
    mod = o.modifiers.new('Face weighted normals', 'WEIGHTED_NORMAL')
    mod.keep_sharp = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    uv = o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
    for p in o.data.polygons:
        axis = max(range(3), key=lambda a: abs(p.normal[a]))
        axes = [a for a in range(3) if a != axis]
        for li in p.loop_indices:
            v = o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv = (v[axes[0]],v[axes[1]])
    return o

def replace(name, pieces):
    bpy.ops.object.select_all(action='DESELECT')
    for p in pieces:
        p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    if len(pieces) > 1:
        bpy.ops.object.join()
    temporary = bpy.context.object
    old = bpy.data.objects[name]
    temporary.data.transform(old.matrix_world.inverted() @ temporary.matrix_world)
    old.data = temporary.data
    bpy.data.objects.remove(temporary, do_unlink=True)
    return old

# A closed solid with a shallow front recess, not an open-backed enclosure.
body = box((.29,0,-.12),(1.39,.9875,.246),paint)
cut = box((.312,.125,.221),(1.368,.9755,.30),paint)
bpy.context.view_layer.objects.active = body
mod = body.modifiers.new('Shallow facade recess in solid body','BOOLEAN')
mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', cut
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cut,do_unlink=True)
body.data.materials.append(recess)
body.data.materials.append(skirt)
bm = bmesh.new()
bm.from_mesh(body.data)
# Split lower faces so the red-brown toe reaches the floor on the returns too.
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
    plane_co=(0,0,.11-body.location.z),plane_no=(0,0,1),dist=1e-7)
bm.to_mesh(body.data)
bm.free()
body.data.update()
for p in body.data.polygons:
    center = body.matrix_world @ p.center
    if center.z < .10999:
        p.material_index = 2
    elif abs(center.y + .221) < 1e-5:
        p.material_index = 1
body = replace('C43_Radiator_Solid_Body',[finish(body,.0012)])
body['construction'] = 'Closed solid, shallow 25 mm front pocket; backing finish inferred, no hollow balcony face'

# Thin cap: original width, depth and top height retain prop/partition contacts.
replace('C43_Radiator_Cap_Front',[
    finish(box((.255,.9875,-.12),(1.425,1.0125,.28),paint),.002)])

parts = []
def piece(lo,hi,mat=paint,bevel=.001):
    parts.append(finish(box(lo,hi,mat),bevel))

# Side stiles and restrained rails, no second ledge beneath the cap.
for x0,x1 in [(.29,.312),(1.368,1.39)]:
    piece((x0,.11,.238),(x1,.9875,.268))
piece((.3115,0,.20),(1.3685,.11,.256),skirt,.0015)
for y0,y1 in [(.11,.125),(.27,.277),(.447,.454),(.675,.682),(.842,.849),(.9755,.9875)]:
    piece((.31,y0,.238),(1.37,y1,.268))

# 41 estimated slats in each of three visible fields. Slots are wider than ribs.
for y0,y1 in [(.124,.271),(.453,.676),(.848,.9765)]:
    for i in range(41):
        x = .323 + i * (1.357-.323)/40
        piece((x-.0045,y0,.255),(x+.0045,y1,.267),bevel=.0008)
grille = replace('C43_Radiator_White_Vertical_Grille',parts)
grille['construction'] = '41 spaced ribs per field, three fields; inset bands and floor-contact red-brown toe'
grille['photo_estimate'] = 'Rib count and section inferred from P01/P03 and user close-up, not measured'
for i,(y0,y1) in enumerate([(.277,.447),(.682,.842)]):
    bar = replace('C43_Radiator_Teal_Crossbar_'+str(i),[
        finish(box((.312,y0,.237),(1.368,y1,.266),blue),.001)])
    bar['construction'] = 'Blue painted inset panel, 2 mm behind white frame face'

bpy.context.view_layer.update()
assert before == {o.name:digest(o) for o in scene.objects if o.name in before}
for name,old in original_materials.items():
    m = bpy.data.materials[name]
    current = (tuple(m.diffuse_color),tuple((n.name,tuple((s.name,str(s.default_value))
        for s in n.inputs if hasattr(s,'default_value'))) for n in m.node_tree.nodes))
    assert old == current, name
checks=[]
for name in sorted(targets):
    o=bpy.data.objects[name]
    bm=bmesh.new();bm.from_mesh(o.data)
    assert not any(not e.is_manifold for e in bm.edges),name
    assert not any(f.calc_area()<1e-14 for f in bm.faces),name
    checks.append({'name':name,'volume':bm.calc_volume(signed=True)})
    bm.free()
assert next(c['volume'] for c in checks if c['name']==body.name)>.35
if component:
    scene['component_parent_revision']='architecture05'
    scene['component_revision']='architecture06'
    output=ROOM/'assets/architecture/Courtyard43-architecture.blend'
else:
    scene['parent_web_revision']='courtyard43-interior04'
    scene['web_revision']='courtyard43-interior05'
    records=json.loads(scene['components'])
    for record in records:
        if record['component']=='architecture':
            record['sha256']=hashlib.sha256((ROOT/record['source']).read_bytes()).hexdigest()
    scene['components']=json.dumps(records)
    output=ROOM/'assets/full-room/Courtyard43-interior.blend'
scene['counter_facade_revision']='Photo-led facade with recessed slots, inset blue bands and thinner cap; approved envelope preserved'
bpy.ops.wm.save_as_mainfile(filepath=str(output))
result={'saved':str(output),'unchangedObjects':len(before),'checks':checks}
if not component:
    script=ROOM/'scripts/export-interior.py'
    scope={'__file__':str(script),'__name__':'courtyard43_export'}
    exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),scope)
    result['export']=scope['export_interior']()
