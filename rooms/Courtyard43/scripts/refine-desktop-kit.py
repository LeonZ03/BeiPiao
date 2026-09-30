"""Official MCP only, desktop13 finish: visible silkscreen, weave and paper.
Requires add-desktop-kit.py and does not rebuild its assemblies or the room.
"""
from pathlib import Path
import ast, json
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43';ASSET=ROOM/'assets/development-kit'
assert bpy.context.scene.get('web_revision')=='courtyard43-interior13'
assert not bpy.context.scene.get('desktop13_finish')
# Reuse only pure mesh helper definitions, never execute the parent mutation.
p=ROOM/'scripts/add-desktop-kit.py'
tree=ast.parse(p.read_text(encoding='utf8'))
definitions=ast.Module(body=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom,ast.FunctionDef,ast.ClassDef))],type_ignores=[])
env={'__file__':str(p)};exec(compile(definitions,str(p),'exec'),env)
env['collection']=bpy.data.collections['C43_DevelopmentKit_desktop13']
env['materials']={m.name.removeprefix('C43_DevKit_'):m for m in bpy.data.materials if m.name.startswith('C43_DevKit_')}
Mesh=env['Mesh'];transform=env['board_transform'];smd=env['smd'];chip=env['chip']
main=Mesh('Main_silkscreen_and_SMD',transform((-1.130,.7433,.386),29,-5))
small=Mesh('Expansion_silkscreen_and_SMD',transform((-.964,.7433,.370),33,5))

def outline(m,x,y,w,h,z=.00194):
    m.tube([(x-w/2,y-h/2,z),(x+w/2,y-h/2,z),(x+w/2,y+h/2,z),(x-w/2,y+h/2,z),(x-w/2,y-h/2,z)],.00012,'silkscreen',4)

for i in range(4):
    x=-.065+i*.025
    outline(main,x,.131,.017,.018)
    main.text('RP'+str(i+1),x-.006,.119,.00198,.0020)
for i in range(5):
    y=.114-i*.021;outline(main,.077,y,.012,.012)
    main.text('RESET' if i==4 else 'B'+str(4-i),.083,y-.003,.00198,.0020,angle=90)
for i in range(8):
    x=.016+i*.006;outline(main,x,.129,.0038,.006)
    main.text('L'+str(8-i),x-.0016,.123,.00198,.0017)
for x in [-.060,-.047,-.034]:
    for y in [.091,.087,.082]:smd(main,x,y)
for i in range(2):
    x=-.060+i*.009
    main.text('GND' if i==0 else ('3V3' if i==1 else ''),x,.002,.0020,.002)
outline(main,-.027,.104,.029,.011)
outline(main,.014,.104,.014,.011)
outline(main,.047,.105,.021,.021)
main.text('SWCLK',.011,.090,.0020,.0023)
main.text('GXCT',-.077,.023,.0091,.009,angle=90)
# White plated-through-hole marks alongside the LCD daughterboard.
for i in range(17):
    x=.064;y=.057+(i-8)*.00254
    outline(main,x,y,.0021,.0021,.0084)
for i in range(8):smd(main,.080,.004+i*.003)
main.finish()

for row in range(2):
    for i in range(4):
        x=-.045+i*.019;y=.113-row*.015
        outline(small,x,y,.011,.011)
for i,(x,y) in enumerate([(.037,.109),(.059,.109),(.005,.085),(.027,.085),(.061,.084),(.005,.056),(.027,.056)]):
    outline(small,x,y,.016,.016)
    small.text('RP',x-.004,y+.009,.00198,.0018)
for i in range(14):
    x=-.065+i*.008;outline(small,x,.074,.0028,.0045)
    small.text('R',x-.001,.069,.00199,.0019)
for i in range(3):
    small.text('DS'+str(3-i),-.061+i*.021,.033,.00199,.0022)
for y in [.049,.045,.041]:
    for x in [.002,.012,.024,.037,.051,.063]:
        smd(small,x,y,True);outline(small,x,y,.003,.0042)
for i in range(8):
    x=.010+i*.007
    small.box((x,.006,.0021),(.0035,.0035,.0003),'solder')
    small.cyl((x,.006,.00235),.0008,.0003,'black_moulding',8)
small.text('GXCT',.036,.042,.0021,.007,angle=90)
small.finish()

# Fine-scale image maps survive the custom PBR exporter. Their scale derives
# from the authored metre UVs (20 repeats/m), not image-camera perspective.
TEX=ASSET/'textures';TEX.mkdir(exist_ok=True)
rng=np.random.default_rng(4313);n=512
y,x=np.mgrid[0:n,0:n];noise=rng.random((n,n))
weave=.50+.14*np.sin(x*2*np.pi/8)*np.sin(y*2*np.pi/8)+.05*(noise-.5)
paper=.5+.12*(noise-.5)+.045*np.sin(x*2*np.pi/157)*np.cos(y*2*np.pi/193)

def image(name,values):
    img=bpy.data.images.new(name,width=n,height=n,alpha=False)
    img.colorspace_settings.name='Non-Color'
    rgba=np.ones((n,n,4),np.float32);rgba[:,:,:3]=values[:,:,None]
    img.pixels.foreach_set(rgba.ravel());img.filepath_raw=str(TEX/(name+'.png'));img.file_format='PNG';img.save()
    img.filepath=bpy.path.relpath(img.filepath_raw)
    return img

def bump(key,img,distance):
    m=env['materials'][key];nodes=m.node_tree.nodes;links=m.node_tree.links
    p=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    t=nodes.new('ShaderNodeTexImage');t.image=img
    b=nodes.new('ShaderNodeBump');b.inputs['Distance'].default_value=distance;b.inputs['Strength'].default_value=.65
    links.new(t.outputs['Color'],b.inputs['Height']);links.new(b.outputs['Normal'],p.inputs['Normal'])
bump('mousemat',image('black-textile-weave',weave),.00010)
bump('cardboard',image('corrugated-paper-grain',paper),.00016)
bump('soldermask',image('pcb-soldermask-microfinish',.5+.035*(noise-.5)),.000012)

scene=bpy.context.scene;scene['desktop13_finish']=True
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
# Reopen the saved main in a separate MCP call and run save-desktop-kit-source.py.
# Blender 5.2 partial-library writing of a freshly created Scene can crash in
# BKE_view_layer_copy_data; normal save_as_mainfile keeps a complete view layer.
result={'objects':len(env['collection'].objects),'revision':scene['web_revision'],'textures':3}
