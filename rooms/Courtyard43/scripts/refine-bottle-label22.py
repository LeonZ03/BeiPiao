"""Official Blender Lab MCP only: replace front-only ink with a wrap label.

Parent interior21. Print scene remains editable in the complete source. Product
front/side photography establishes repeated branding and the mineral table;
unseen production/address microcopy is intentionally not fabricated.
"""
import ast, bpy, bmesh, hashlib, json, math, os
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]; ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior21'
bpy.context.preferences.filepaths.save_version=0
p=ROOM/'scripts/refine-furnishings.py'
tree=ast.parse(p.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='digest'],type_ignores=[]),str(p),'exec'))
bpy.context.view_layer.update()
before={o.name:digest(o) for o in scene.objects}
ink=[o for o in scene.objects if o.name.startswith('C43_Nongfu16_logo_') or o.name in {'C43_Nongfu16_brand','C43_Nongfu16_english','C43_Nongfu16_water','C43_Nongfu16_volume'}]
targets={o.name for o in ink}|{'C43_Bottle_label'}
cx,base,cz=.56,1.0125,.215
radius=.04385; width=math.tau*radius; height=.125
out=ROOM/'assets/props/textures/nongfu-wrap22.png'
out.parent.mkdir(parents=True,exist_ok=True)

# A native, editable print layout; emission renders flat albedo, without baked
# scene highlights, shadows or lighting. Its objects are outside the room scene.
printscene=bpy.data.scenes.new('C43_BottleLabel_Print22')
printscene.render.engine='BLENDER_EEVEE'
printscene.render.resolution_x=2048;printscene.render.resolution_y=930
printscene.render.resolution_percentage=100
printscene.render.image_settings.file_format='PNG'
printscene.render.image_settings.color_mode='RGB'
printscene.render.filepath=str(out)
printscene.view_settings.view_transform='Standard'
printscene.view_settings.look='None';printscene.view_settings.exposure=0
printscene.view_settings.gamma=1
printscene.world=bpy.data.worlds.new('C43_Label22_unlit_world')
printscene.world.color=(0,0,0)
colors={'red':(.76,.008,.012),'white':(.93,.93,.88),'green':(.008,.14,.075),'black':(.009,.012,.011)}
paints={}
def paint(name,color):
    m=bpy.data.materials.new('C43_LabelPrint22_'+name);m.use_nodes=True
    m.node_tree.nodes.clear()
    e=m.node_tree.nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color[:3],1)
    output=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(e.outputs[0],output.inputs[0])
    return m
for k,c in colors.items():paints[k]=paint(k,c)
def polygon(name,points,mat,z=0):
    me=bpy.data.meshes.new(name);me.from_pydata([(x,y,z) for x,y in points],[],[tuple(range(len(points)))])
    ob=bpy.data.objects.new(name,me);printscene.collection.objects.link(ob);me.materials.append(mat);return ob
def rectangle(name,x,y,w,h,mat,z=.0001):
    return polygon(name,[(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)],mat,z)
rectangle('Paper',0,0,width,height,paints['white'],0)
points=[(-width/2,-height/2),(width/2,-height/2)]
for i in range(161):
    x=width/2-width*i/160
    points.append((x,.123-.003*math.cos(2*(x/ radius))- .047-height/2))
polygon('Wave red field',points,paints['red'],.0001)
for y in [-height/2+.001,height/2-.001]:rectangle('Green trim',0,y,width,.0012,paints['green'],.0002)

# Unroll existing approved brand artwork rather than redraw or replace its font.
# Two repeated brand faces are visible at opposite edges of the side photograph.
for source in ink:
    me=source.data.copy()
    for v in me.vertices:
        p=source.matrix_world@v.co
        x=radius*math.atan2(p.x-cx,-p.y-cz)
        v.co=(x,p.z-base-.047-height/2,.001+(p.z*0))
    me.materials.clear()
    sm=source.data.materials[0]
    bs=next(n for n in sm.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    color=bs.inputs['Base Color'].default_value
    key=sm.name
    if key not in paints:paints[key]=paint(key,color)
    me.materials.append(paints[key])
    # Snow must sit above the mountain in the flat albedo layout.
    for v in me.vertices:v.co.z=.0012 if source.name.endswith('_snow') else .001
    for center in [-width/4,width/4]:
        ob=bpy.data.objects.new(source.name+'_Print22',me);printscene.collection.objects.link(ob);ob.location.x=center

fontpath=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/msyh.ttc'
font=bpy.data.fonts.load(str(fontpath))
def text(name,body,x,y,size,mat,maxwidth=None):
    cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.font=font
    cu.size=size;cu.align_x='CENTER';cu.align_y='CENTER';cu.resolution_u=3
    ob=bpy.data.objects.new(name,cu);printscene.collection.objects.link(ob)
    ob.location=(x,y,.002);cu.materials.append(mat)
    bpy.context.view_layer.update()
    # Fonts are sized to the observed panel, no invented miniature filler text.
    if maxwidth:
        # Blender font dimensions update after depsgraph evaluation of its scene.
        dg=printscene.view_layers[0].depsgraph;dg.update()
        w=ob.evaluated_get(dg).dimensions.x
        if w>maxwidth:ob.scale.x=maxwidth/w
    return ob

# Side A: literal legible information from the product side photograph.
rows=[('饮用天然水特征性指标',.0029),('每100ml含量 (μg/100ml)',.0025),
      ('钙             ≥400',.003),('镁              ≥50',.003),
      ('钾              ≥35',.003),('钠              ≥80',.003),
      ('偏硅酸          ≥180',.003),('pH值 (25℃)  7.3±0.5',.0028)]
for i,(body,size) in enumerate(rows):text('Mineral_'+str(i),body,0,.048-i*.005,size,paints['red'],.054)
for y in [.045,.039]:rectangle('Table rule',0,y,.050,.00025,paints['red'],.002)
for i,body in enumerate(['基于我们的理念，','农夫山泉','从不添加任何人工矿物质']):
    text('Observed principle_'+str(i),body,0,-.004-i*.008,.0032 if i!=1 else .005,paints['white'],.053)

# Side B crosses the texture seam: verified 1.5 L EAN. No fictional factory,
# source location, licence, production date or lot number is printed.
ean='6921168520015'
assert (sum(map(int,ean[:12:2]))+3*sum(map(int,ean[1:12:2]))+int(ean[-1]))%10==0
L=['0001101','0011001','0010011','0111101','0100011','0110001','0101111','0111011','0110111','0001011']
G=['0100111','0110011','0011011','0100001','0011101','0111001','0000101','0010001','0001001','0010111']
parity=['LLLLLL','LLGLGG','LLGGLG','LLGGGL','LGLLGG','LGGLLG','LGGGLL','LGLGLG','LGLGGL','LGGLGL'][int(ean[0])]
bits='101'+''.join((L if p=='L' else G)[int(d)] for p,d in zip(parity,ean[1:7]))+'01010'+''.join(''.join('1' if b=='0' else '0' for b in L[int(d)]) for d in ean[7:])+'101'
for x in [-width/2,width/2]:
    text('Reverse product','饮用天然水',x,.046,.0035,paints['red'],.05)
    text('Reverse volume','净含量 1.5L',x,.039,.0035,paints['red'],.05)
    rectangle('Barcode paper',x,-.026,.050,.029,paints['white'],.002)
    for i,b in enumerate(bits):
        if b=='1':rectangle('EAN bar',x+(i-47)*.00043,-.024,.00043,.018,paints['black'],.003)
    text('EAN digits',ean,x,-.037,.0033,paints['black'],.048)
    text('Reverse brand','农夫山泉',x,.003,.005,paints['white'],.050)

camdata=bpy.data.cameras.new('Label22_orthographic');cam=bpy.data.objects.new('Label22_orthographic',camdata)
printscene.collection.objects.link(cam);cam.location=(0,0,1);camdata.type='ORTHO';camdata.ortho_scale=width
printscene.camera=cam
bpy.ops.render.render(write_still=True,scene=printscene.name)
# Keep the print scene portable without relying on installed font files.
bpy.context.window.scene=printscene
dg=bpy.context.evaluated_depsgraph_get()
dg.update()
for ob in list(printscene.objects):
    if ob.type!='FONT':continue
    me=bpy.data.meshes.new_from_object(ob.evaluated_get(dg),depsgraph=dg)
    replacement=bpy.data.objects.new(ob.name+'_outlined',me)
    printscene.collection.objects.link(replacement);replacement.matrix_world=ob.matrix_world.copy()
    bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.window.scene=scene

label=bpy.data.objects['C43_Bottle_label'];label.data=label.data.copy()
mat=bpy.data.materials['C43_Nongfu16_label_white'].copy();mat.name='C43_Nongfu_wrap22'
bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
image=bpy.data.images.load(str(out),check_existing=False);image.colorspace_settings.name='sRGB'
image.filepath=bpy.path.relpath(str(out),start=str(ROOM/'assets/full-room'))
tx=mat.node_tree.nodes.new('ShaderNodeTexImage');tx.image=image
uvnode=mat.node_tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UVMap'
mat.node_tree.links.new(uvnode.outputs[0],tx.inputs['Vector']);mat.node_tree.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.70
props=json.loads(mat.get('web_props','{}'));props.update(roughness=.70,metalness=0,specularIntensity=.22,clearcoat=0)
mat['web_props']=json.dumps(props)
label.data.materials.append(mat);slot=len(label.data.materials)-1
uv=label.data.uv_layers['UVMap']
for poly in label.data.polygons:
    mid=label.matrix_world@poly.center;n=label.matrix_world.to_3x3()@poly.normal
    outward=n.x*(mid.x-cx)+n.y*(mid.y+cz)>0
    if outward:poly.material_index=slot
    angles=[]
    for li in poly.loop_indices:
        p=label.matrix_world@label.data.vertices[label.data.loops[li].vertex_index].co
        angles.append((math.atan2(p.x-cx,-p.y-cz)/math.tau+.25)%1)
    if max(angles)-min(angles)>.5:angles=[a+1 if a<.5 else a for a in angles]
    for li,u in zip(poly.loop_indices,angles):
        p=label.matrix_world@label.data.vertices[label.data.loops[li].vertex_index].co
        uv.data[li].uv=(u,(p.z-base-.047)/height)
for o in ink:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==v for n,v in before.items() if n not in targets),'Non-label object changed'
scene['web_revision']='courtyard43-interior22'
scene['bottle22']=json.dumps({'parent':'courtyard43-interior21','targets':sorted(targets),'unchanged':len(before)-len(targets),'texture':str(out.relative_to(ROOT)),'limitedEvidence':'Reverse microcopy omitted; reverse panel positioning photo-estimated'})
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'revision':scene['web_revision'],'unchangedObjects':len(before)-len(targets),'texture':str(out),'removedInkMeshes':len(ink)}
