"""laptop42b -> props43. Official Blender Lab MCP only.

Remove the mouse lead; correct the existing lower/left racket brand plate.
Wilson wordmark: Amer Sports official brand SVG, archived in history/inputs.
Racket model is not known; preserve its approved frame, strings and position.
"""
from pathlib import Path
import bpy, copy, shutil
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='laptop42b'

# The mouse lead is separate from the black laptop supply and earbud case.
o=obs[1041];assert o.parent==obs[878] and data['nodes'][1041]['material']==91
o.hide_render=True;o.hide_set(True);data['nodes'][1041]['visible']=False;changed.add(1041)
o['retired_reason']='User confirmed wireless mouse, 2026-10-25'

path=HERE.parent/'history/inputs/wilson43/logo.png'
dst=SOURCE/'textures/wilson43-wordmark.png';shutil.copyfile(path,dst)
shutil.copyfile(path,OUT/dst.name)
im=bpy.data.images.load(str(dst),check_existing=False);im.colorspace_settings.name='sRGB'
tid=len(data['textures']);td=copy.deepcopy(data['textures'][24]);td.update(id=tid,webPath='./assets/full-room/'+dst.name,repeat=[1,1]);data['textures'].append(td);images[tid]=im
mid=material('Wilson43 white printed wordmark',78,[.92,.92,.90],.8,{'map':tid},transparent=True,alphaTest=.3,depthWrite=False,polygonOffset=True,polygonOffsetFactor=-1,polygonOffsetUnits=-1)
m=mats[mid];bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=next(n for n in m.node_tree.nodes if n.type=='TEX_IMAGE');m.node_tree.links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
target=obs[835];assert target.parent==obs[824]
target.data=target.data.copy()
# Respect the official artwork aspect ratio on the existing throat label.
for v in target.data.vertices:v.co.z*=.034/(89.64/21.17)/.006
set_material(835,mid);export(target)
target.name='Wilson43 left racket brand';target['web_name']=target.name;data['nodes'][835]['name']=target.name
result=save('props43',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'props43':{'parent':'laptop42b','wirelessMouse':True,'leftRacketBrand':'Wilson','brandNode':835,'frameUnchanged':True}})
