"""finish39 -> cap40, official Blender Lab MCP only.

Reuse the corrected Yongwang brim surface, not its full-room assembly.
All room placement, crown, logo, materials, curtains and breeze stay intact.
"""
from pathlib import Path
import bpy,bmesh,json,ast,math
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]; ROOM=ROOT/'rooms/Courtyard43'
assert bpy.context.scene.get('web_revision')=='courtyard43-finish39'
bpy.context.preferences.filepaths.save_version=0
source=ROOT/'rooms/yongwang-jiayuan/scripts/cap-bill51.py'
exec(compile(source.read_text('utf8'),str(source),'exec'))
tree=ast.parse((ROOM/'scripts/refine-furnishings.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='digest'],type_ignores=[]),'digest','exec'))
import hashlib
targets=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('C43_Baseball15_') and 'bill' in o.name]
assert len(targets)==7
before={o.name:digest(o)for o in bpy.context.scene.objects if o not in targets}
for o in targets:
    if 'attached' in o.name:values=bill_mesh51()
    else:
        suffix=o.name.split('bill-top-stitch')[-1]
        i=int(suffix[1:]) if suffix else 0
        values=stitch_mesh51([.12,.30,.48,.66,.84,.98][i])
    vs,fs,uv=values; me=bpy.data.meshes.new(o.name+' cap40')
    me.from_pydata([(x,-z,y)for x,y,z in vs],[],fs);me.update()
    for mat in o.data.materials:me.materials.append(mat)
    for f in me.polygons:f.use_smooth=True
    layer=me.uv_layers.new(name='UVMap')
    for l in me.loops:layer.data[l.index].uv=uv[l.vertex_index]
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o.data=me;o.modifiers.clear();o['reuse_cap40']='Yongwang correction51 continuous brim; independent local mesh'
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==h for n,h in before.items())
s=bpy.context.scene;s['parent_web_revision']='courtyard43-finish39';s['web_revision']='courtyard43-cap40'
s['cap40']=json.dumps({'source':'Yongwang correction51','unchangedObjects':len(before),'scope':'brim and its six fine stitch lines only'})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';ns={'__file__':str(p)};exec(compile(p.read_text('utf8'),str(p),'exec'),ns)
result={**ns['export_interior'](),'unchangedObjects':len(before)}
