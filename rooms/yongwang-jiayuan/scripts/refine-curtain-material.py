import os
import bpy, json, copy, math, shutil
import numpy as np
from pathlib import Path
root=Path(os.environ.get('BEIPIAO_ROOT', Path(__file__).resolve().parents[3]));out=root/'room-site/dist/assets/full-room'
data=json.loads((out/'scene.json').read_text(encoding='utf-8'));assert data['revision'] in ('curtain23','curtain23b')
mat=next(m for m in bpy.data.materials if m.get('web_material_id')==160)
source=root/'rooms/yongwang-jiayuan/assets/curtain23/ivory-jacquard-albedo.png'
shutil.copyfile(source,out/'curtain23-jacquard-albedo.png')
im=bpy.data.images.load(str(source),check_existing=False);im.colorspace_settings.name='sRGB';im.pack()
def tex(name,img):
    old=next((t for t in data['textures'] if t.get('webPath')=='./assets/full-room/'+name),None)
    if old is not None:return old['id']
    desc=copy.deepcopy(data['textures'][40]);desc.update(id=len(data['textures']),webPath='./assets/full-room/'+name,colorSpace='srgb',wrapS=1001,wrapT=1001,repeat=[1,1])
    data['textures'].append(desc);return desc['id']
base_id=tex('curtain23-jacquard-albedo.png',im)
# A diffuse-light transport mask: denser gathered seams transmit less light;
# a broad right-hand highlight corresponds to the photographed sunny window.
h=1536;w=1024;Y,X=np.mgrid[:h,:w];u=X/(w-1);v=Y/(h-1)
trans=.57+.17*np.sin(v*math.pi*.88+.15)+.09*np.sin(u*7-v*2)
trans+=.47*np.exp(-((u-.86)/.10)**2)*np.exp(-((v-.47)/.31)**2)
for k,c in enumerate([.083,.215,.367,.513,.674,.813,.955]):
    center=c+.013*np.sin(k*1.8+(1-v)*2.7)*(1-v)
    trans*=1-.31*np.exp(-((u-center)/(.018+.012*(1-v)))**2)
trans*=1-.54*(v>.963)-.62*(v<.029)
color=np.ones((h,w,3))*np.array([.86,.89,.85])
edge=np.exp(-((u-.86)/.14)**2)[:,:,None]
color=color*(1-edge*.45)+np.array([1.,.89,.73])*edge*.45
pixels=np.ones((h,w,4),dtype=np.float32);pixels[:,:,:3]=np.clip(color*trans[:,:,None],0,1)
glow=bpy.data.images.new('curtain23-photo-diffuse-transport',width=w,height=h,alpha=False);glow.colorspace_settings.name='sRGB'
glow.pixels.foreach_set(pixels.ravel());glow.filepath_raw=str(out/'curtain23-photo-diffuse-transport.png');glow.file_format='PNG';glow.save();glow.pack()
glow_id=tex('curtain23-photo-diffuse-transport.png',glow)
nodes=mat.node_tree.nodes;links=mat.node_tree.links
bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
base=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image and 'ivory-jacquard' in n.image.name)
base.image=im
gl=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image and ('diffuse-translucency' in n.image.name or 'photo-diffuse-transport' in n.image.name))
gl.image=glow
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
links.new(base.outputs['Color'],mix.inputs[1]);links.new(gl.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Emission Color'])
bs.inputs['Emission Strength'].default_value=3.0
for n in nodes:
    if n.type=='BUMP':n.inputs['Distance'].default_value=.00012
# Six motif columns across the curtain, without stretching the woven artwork.
data['textures'][base_id]['repeat']=[1.5,1];data['textures'][base_id]['wrapS']=1000
uv=next(n for n in nodes if n.type=='UVMAP')
mapping=next((n for n in nodes if n.type=='MAPPING'),None) or nodes.new('ShaderNodeMapping')
mapping.inputs['Scale'].default_value=(1.5,1,1)
links.new(uv.outputs[0],mapping.inputs['Vector']);links.new(mapping.outputs[0],base.inputs['Vector'])
d=data['materials'][160];d['textures']['map']=base_id;d['textures']['emissiveMap']=glow_id;d['props']['bumpScale']=.00012
d['props']['emissiveIntensity']=3.0
d['userData'].update(photoWovenPattern=True,revision='curtain23b')
# Albedo also attenuates the web backlight, keeping the jacquard and weave visible.
d['userData']['multiplyCurtainAlbedo']=True
data['revision']='curtain23b';bpy.context.scene['web_revision']='curtain23b'
bpy.ops.wm.save_as_mainfile(filepath=str(root/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'))
(out/'scene.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
result={'revision':'curtain23b','packedWovenAlbedo':True,'geometryUnchanged':True,'broadFolds':7}
