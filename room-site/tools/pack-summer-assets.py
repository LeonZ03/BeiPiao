"""Index Blender loop vertices and spatially filter diffuse irradiance maps."""
import json
from pathlib import Path
from PIL import Image,ImageFilter
root=Path(__file__).resolve().parents[1]
p=root/'dist/assets/summer/models.js'
a=json.loads(p.read_text(encoding='utf8').split('export default ',1)[1].strip().removesuffix(';'))
for name,m in a['meshes'].items():
 if 'index' in m: continue
 vertices={};pos=[];normal=[];uv=[];index=[]
 for i in range(len(m['position'])//3):
  v=tuple(m['position'][i*3:i*3+3]+m['normal'][i*3:i*3+3]+m['uv'][i*2:i*2+2])
  if v not in vertices:
   vertices[v]=len(pos)//3;pos.extend(v[:3]);normal.extend(v[3:6]);uv.extend(v[6:])
  index.append(vertices[v])
 a['meshes'][name]={'position':pos,'normal':normal,'uv':uv,'index':index}
 print(name,len(m['position'])//3,'->',len(pos)//3)
p.write_text('/* Blender-authored indexed meshes; Y-up metres. */\nexport default '+json.dumps(a,separators=(',',':'))+';\n',encoding='utf8')
original=root.parent/'generated-assets/summer/raw-irradiance';original.mkdir(exist_ok=True)
for image in p.parent.glob('indirect-*.png'):
 raw=original/image.name
 if not raw.exists():raw.write_bytes(image.read_bytes())
 # Indirect irradiance is low-frequency; remove Monte Carlo noise without
 # blurring the material textures or the realtime direct-light shadows.
 Image.open(raw).filter(ImageFilter.GaussianBlur(6)).save(image,optimize=True)
print('Packed',p.stat().st_size,'bytes')
