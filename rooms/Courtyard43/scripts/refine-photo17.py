"""Official Blender Lab MCP only: interior16 -> interior17.

Correct front/back chair support and independently calibrate exterior plaster.
Photo estimates; approved room/exterior anchors remain fixed.
"""
from pathlib import Path
import ast, bpy, bmesh, hashlib, json
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]; ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior16'
bpy.context.preferences.filepaths.save_version=0
p=ROOM/'scripts/refine-furnishings.py'
tree=ast.parse(p.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),str(p),'exec'))
before={o.name:digest(o) for o in s.objects}
targets={'C43_Chair15_ContinuousBackLeg_L','C43_Chair15_ContinuousBackLeg_R','C43_Chair15_CurvedTopRail'}
web=lambda p:Vector((p[0],p[2],-p[1]))
bp=lambda p:Vector((p[0],-p[2],p[1]))
for name in targets:
    o=bpy.data.objects[name];o.data=o.data.copy();inv=o.matrix_world.inverted()
    for v in o.data.vertices:
        q=web(o.matrix_world@v.co)
        if 'TopRail' in name:
            q.y-=.019
            q.z+=.015
        else:
            # The upper tube is behind the curved white shell, while the feet
            # and under-seat frame keep their accepted footprint and contacts.
            a=max(0,min(1,(q.y-.43)/.19));a=a*a*(3-2*a)
            q.z+=(.023+.011*max(0,min(1,(q.y-.62)/.265)))*a
            q.y-=.019*max(0,min(1,(q.y-.80)/.075))
        v.co=inv@bp(q)
    bm=bmesh.new();bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    assert bm.calc_volume(signed=True)>0
    bm.to_mesh(o.data);bm.free();o.data.update()

# The inherited mineral image averages only ~.29 sRGB, whereas winter10's
# material multiplier assumed .58. This both darkened and green-tinted walls.
# Retain its mineral variation/relief, normalize to neutral .58 once in source.
m=bpy.data.materials['C43_ZWinter_BeigePink_Plaster']
source=next(n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE')
a=np.array(source.pixels[:],dtype=np.float32).reshape(source.size[1],source.size[0],4)
gray=a[:,:,:3]@np.array([.2126,.7152,.0722],dtype=np.float32)
neutral=np.clip(.58+(gray-gray.mean())*.76,.43,.70)
pixels=np.ones_like(a);pixels[:,:,:3]=neutral[:,:,None]
im=bpy.data.images.new('C43_photo17_neutral_mineral',width=source.size[0],height=source.size[1],alpha=False)
im.colorspace_settings.name='sRGB';im.pixels.foreach_set(pixels.ravel())
path=ROOM/'assets/winter-exterior/textures/photo17-neutral-mineral.png'
im.filepath_raw=str(path);im.file_format='PNG';im.save()
im.filepath=bpy.path.relpath(str(path),start=str(ROOM/'assets/full-room'))
def lin(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
palette={
    'BeigePink_Plaster':(.67,.615,.590),
    'Muted_Pink_Wall':(.655,.601,.585),
    'Old_Cream_Plaster':(.725,.713,.670),
    'Distant_Pale_Yellow':(.73,.709,.595),
    'Concrete':(.49,.505,.49),
}
for suffix,color in palette.items():
    m=bpy.data.materials['C43_ZWinter_'+suffix]
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    albedo=bs.inputs['Base Color'].links[0].from_node;albedo.image=im
    bs.inputs['Roughness'].default_value=.91
    bs.inputs['Metallic'].default_value=0
    bs.inputs['Emission Color'].default_value=(*[lin(c) for c in color],1)
    bs.inputs['Emission Strength'].default_value=.08
    props=json.loads(m.get('web_props','{}'))
    props.update(color=[lin(c)/lin(.58) for c in color],roughness=.91,metalness=0,specularIntensity=.25,envMapIntensity=.35)
    m['web_props']=json.dumps(props)
    for n in m.node_tree.nodes:
        if n.type=='BUMP':n.inputs['Distance'].default_value=.0012
    targets.update(o.name for o in s.objects if o.type=='MESH' and m in list(o.data.materials))
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets)
component=ROOM/'assets/winter-exterior/Courtyard43-winter-exterior.blend'
bpy.data.libraries.write(str(component),{bpy.data.collections['C43_ZWinter']},path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(s['components'])
for item in components:
    if item['component']=='winter-exterior':item.update(revision='photo17',sha256=hashlib.sha256(component.read_bytes()).hexdigest())
s['components']=json.dumps(components)
s['parent_web_revision']='courtyard43-interior16';s['web_revision']='courtyard43-interior17'
s['photo17']=json.dumps({'chair':'back supports behind white shell; lower frame/feet unchanged','exterior':'neutralized mineral albedo, individually photo-calibrated plaster','untouchedObjects':len(set(before)-targets)})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';ns={'__file__':str(p)}
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns)
result=ns['export_interior']();result['untouchedObjects']=len(set(before)-targets)
report=ROOT/'analysis/Courtyard43/photo17/model-report.json';report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps(result,indent=2),encoding='utf8')
