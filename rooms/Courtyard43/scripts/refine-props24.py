"""interior22 -> props24: thickness only, fresh bag rolls and approved reuse.

Official Blender Lab MCP only. Curtain paired surface midpoints, rings, folds,
anchors and all unrelated objects remain unchanged. Small prop sizes estimated.
"""
from pathlib import Path
import bpy,bmesh,math,json,ast,hashlib,shutil
import numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior22'
bpy.context.preferences.filepaths.save_version=0
bp=lambda p:Vector((p[0],-p[2],p[1]));web=lambda p:Vector((p[0],p[2],-p[1]))
targets=set()
helper=ROOM/'scripts/refine-furnishings.py';tree=ast.parse(helper.read_text(encoding='utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'digest','shader','material','assign','replace','solid','tube','lathe'}],type_ignores=[]),str(helper),'exec'))
before={o.name:digest(o) for o in scene.objects}

# Preserve the exact centre surface in both shape keys; only grow its normal
# offset. Six millimetres body / nine millimetres turned hem are visual estimates.
curtain_report={}
for side in ['Left','Right']:
    o=bpy.data.objects['C43_Curtain_'+side];targets.add(o.name);o.data=o.data.copy()
    for key in o.data.shape_keys.key_blocks:
        a=np.array([tuple(p.co) for p in key.data]);n=len(a)//2;assert n==121*65
        mid=(a[:n]+a[n:])*.5;offset=(a[:n]-a[n:])*.5
        lengths=np.linalg.norm(offset,axis=1);assert min(lengths)>1e-7
        edge=np.arange(n)//121/64
        half=.003+.0015*np.clip((edge-.96)/.04,0,1)
        new=offset/lengths[:,None]*half[:,None]
        for i in range(n):key.data[i].co=mid[i]+new[i];key.data[i+n].co=mid[i]-new[i]
        curtain_report[side+'_'+key.name]={'maxCentreDisplacement':0,'bodyThickness':.006,'hemThickness':.009}
    for v,p in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data):v.co=p.co
    m=o.data.materials[0].copy();m.name='C43_MatteHeavyCloth24_'+side;o.data.materials[0]=m
    bs=shader(m);bs.inputs['Roughness'].default_value=.98;bs.inputs['Sheen Weight'].default_value=0;bs.inputs['Specular IOR Level'].default_value=.10
    props=json.loads(m.get('web_props','{}'));props.update(roughness=.98,sheen=0,metalness=0,clearcoat=0,specularIntensity=.10,envMapIntensity=.12)
    m['web_props']=json.dumps(props);o['cloth_thickness_m']=.006;o['props24']='Centre surfaces and fold shapes unchanged; paired normal shell only'

def retire(o):targets.add(o.name);o.hide_render=True;o.hide_set(True)
for o in list(scene.objects):
    if o.name.startswith(('C43_Tissue_','C43_Laptop_')) or o.name=='C43_Hanging_bag' or o.name.startswith('C43_Bag15_') or o.name in ['C43_Bag_visible_blue_round_item','C43_Bag_round_rim']:retire(o)

# Append current approved complete-scene tissue and complete laptop. No source
# edits and no dependency on old standalone assets. Every editable data block is
# owned by this room. The desk and packet landing locations remain unchanged.
source=ROOT/'rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend'
source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'room-site/dist/assets/full-room/scene.json').read_text(encoding='utf8'));assert manifest['revision']=='laptop40'
with bpy.data.libraries.load(str(source),link=False) as (src,dst):dst.objects=list(src.objects)
loaded={int(o['web_node_id']):o for o in dst.objects if o and 'web_node_id' in o}
rootids=[1096,1132];keep=set()
for nid in rootids:keep.update([loaded[nid],*loaded[nid].children_recursive])
for o in list(dst.objects):
    if o and o not in keep:bpy.data.objects.remove(o,do_unlink=True)
material_cache={};texdir=ROOM/'assets/props/textures';texdir.mkdir(exist_ok=True)
for o in keep:
    scene.collection.objects.link(o);nid=int(o['web_node_id']);o.name='C43_Reuse24_'+(o.get('web_name') or 'Mesh_'+str(nid))
    o.hide_render=not manifest['nodes'][nid]['visible'];o.hide_set(o.hide_render);o['web_tags']=json.dumps({'noCollision':True})
    meta=json.loads(o.get('web_user_data','{}'));meta.pop('authoring',None);o['web_userData']=json.dumps(meta)
    if o.type!='MESH':continue
    o.data=o.data.copy()
    for slot in o.material_slots:
        old=slot.material;mid=int(old['web_material_id'])
        if mid not in material_cache:
            desc=manifest['materials'][mid];m=bpy.data.materials.new('C43_Reuse24_'+old.name);m.use_nodes=True;b=shader(m)
            b.inputs['Base Color'].default_value=(*desc['colors'].get('color',[1,1,1]),1)
            b.inputs['Roughness'].default_value=desc['props'].get('roughness',.6);b.inputs['Metallic'].default_value=desc['props'].get('metalness',0)
            m['web_props']=json.dumps(desc['props'])
            if 'Dell' in old.name:
                b.inputs['Base Color'].default_value=(.035,.037,.04,1);props=dict(desc['props']);props.update(side=2,metalness=0);m['web_props']=json.dumps(props)
            for key,tid in desc.get('textures',{}).items():
                assert key in ['map','roughnessMap','metalnessMap','normalMap','bumpMap','emissiveMap'],key
                td=manifest['textures'][tid];path=ROOT/'room-site/dist'/td['webPath'];target=texdir/('reuse24-'+path.name)
                if not target.exists():shutil.copyfile(path,target)
                im=bpy.data.images.load(str(target),check_existing=True);im.colorspace_settings.name='sRGB' if key in ['map','emissiveMap'] else 'Non-Color'
                tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=im
                uv=m.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap';mp=m.node_tree.nodes.new('ShaderNodeMapping');mp.inputs['Scale'].default_value=(*td.get('repeat',[1,1]),1)
                m.node_tree.links.new(uv.outputs[0],mp.inputs['Vector']);m.node_tree.links.new(mp.outputs[0],tx.inputs['Vector'])
                if key in ['map','roughnessMap','metalnessMap']:m.node_tree.links.new(tx.outputs['Color'],b.inputs[{'map':'Base Color','roughnessMap':'Roughness','metalnessMap':'Metallic'}[key]])
                elif key=='emissiveMap':tx['web_map']='emissiveMap'
                else:
                    normal=m.node_tree.nodes.new('ShaderNodeNormalMap' if key=='normalMap' else 'ShaderNodeBump')
                    m.node_tree.links.new(tx.outputs['Color'],normal.inputs['Color' if key=='normalMap' else 'Height']);m.node_tree.links.new(normal.outputs[0],b.inputs['Normal'])
            material_cache[mid]=m
        slot.link='DATA';slot.material=material_cache[mid]
packet=loaded[1096];packet.parent=None;packet.matrix_world=Matrix.Identity(4);packet.location=bp((1.195,1.0125,.215));packet.rotation_euler.z=math.pi/2
root=loaded[1132];root.parent=None;root.matrix_world=Matrix.Identity(4);root.location=bp((-1.57,.7465,.295))
root['web_userData']=json.dumps({'laptopRoot':True,'defaultOpen':False});root['reuse']='Yongwang laptop40 complete-scene laptop, isolated and placed at approved desk anchor'
lid=loaded[1220];lid.rotation_euler.x=math.pi/2;lid['c43_interaction']=json.dumps({'id':'laptop','kind':'laptop','axis':'x','openAngle':-.21-math.pi/2,'defaultOpen':False})
lid['web_userData']=json.dumps({'laptopLid':True,'defaultOpen':False,'openAngle':-.21,'closedAngle':math.pi/2})
for nid in [1133,1134,1221]:
    silver=bpy.data.materials.get('C43_Laptop_anodized_silver')
    if silver:loaded[nid].data.materials.clear();loaded[nid].data.materials.append(silver)

# An upright heat-sealed plastic retail pouch, filled with compact NEW rolls.
# It is not a textile tote: straight sealed perimeter, shallow roll-shaped bulk,
# small hanging header, opened upper-left lip and a visible cylindrical roll.
navy=material('Bag24_navy_print',(.028,.038,.062),.63)
cream=material('Bag24_cream_print',(.63,.64,.59),.68)
blue=material('Bag24_unused_blue_film',(.035,.18,.27),.66)
core=material('Bag24_roll_core',(.012,.040,.052),.91)
N=64;R=37;vv=[];ff=[]
for j in range(R):
    t=j/(R-1);w=float(np.interp(t,[0,.06,.16,.77,.90,1],[.070,.087,.094,.094,.087,.075]))
    d=float(np.interp(t,[0,.07,.19,.7,.87,1],[.001,.019,.034,.037,.022,.001]))
    for i in range(N):
        a=i/N*math.tau;c=math.cos(a);s=math.sin(a)
        wrinkle=.0018*math.sin(a*7+t*19)*math.sin(math.pi*t)**2
        vv.append((1.955+w*math.copysign(abs(c)**.35,c),1.29+.285*t,1.448+(d+wrinkle)*math.copysign(abs(s)**.50,s)))
for j in range(R-1):
    for i in range(N):ff.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
ff.append(tuple(reversed(range(N))))
bag=replace('C43_Bag24_retail_package',vv,ff,[cream,navy]);solid(bag,.00065)
for p in bag.data.polygons:p.material_index=0 if p.center.z<1.385 else 1
for v in bag.data.vertices:
    p=web(v.co);w=max(0,min(1,(p.y-1.49)/.085))*max(0,min(1,(1.95-p.x)/.055));p.y-=.065*w;v.co=bp(p)
bag['evidence']='User-confirmed unused rolled garbage bags; unresolvable branding omitted; estimated package dimensions'
# Flat header with an actual hanging hole over the existing hook.
bpy.ops.mesh.primitive_cube_add(size=1,location=bp((1.955,1.586,1.407)))
tab=bpy.context.object;tab.name='C43_Bag24_hanging_header';tab.dimensions=(.041,.0014,.041);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);tab.data.materials.append(navy)
bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.0065,depth=.008,location=bp((1.955,1.600,1.407)),rotation=(math.pi/2,0,0))
cutter=bpy.context.object;bpy.context.view_layer.objects.active=tab;mod=tab.modifiers.new('Hanging hole','BOOLEAN');mod.object=cutter;mod.operation='DIFFERENCE';bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
uv=tab.data.uv_layers.new(name='UVMap')
tab.data.materials.clear();tab.data.materials.append(navy)
for p in tab.data.polygons:p.material_index=0
for l in tab.data.loops:uv.data[l.index].uv=(tab.data.vertices[l.vertex_index].co.x,tab.data.vertices[l.vertex_index].co.z)
tab['web_tags']=json.dumps({'noCollision':True})
# Roll axis leans slightly left. Its lower half is inside the packet, with a
# visible wrapped cylindrical side and concentric cut layers, not a blue lid.
roll=lathe('C43_Bag24_new_roll',(0,0,0),[(.004,0),(.023,0),(.024,.002),(.024,.083),(.023,.085),(.004,.085),(.004,0)],blue,64)
def rollpos(p):return Vector((1.890+p.x,1.477+.55*p.y-.835*p.z,1.442+.835*p.y+.55*p.z))
for v in roll.data.vertices:v.co=bp(rollpos(web(v.co)))
for k,r in enumerate([.005,.009,.013,.018,.022]):
    tube('C43_Bag24_cut_layer_'+str(k),[rollpos(Vector((r*math.cos(a),.085,r*math.sin(a)))) for a in np.linspace(0,math.tau,65)],.00018,core)
# Seal folds bridge from the pouch to the supported header, leaving the roll lip.
for s in [-1,1]:tube('C43_Bag24_header_fold_'+str(s),[(1.955+s*.075,1.510 if s<0 else 1.575,1.448),(1.955+s*.020,1.575,1.416),(1.955+s*.018,1.582,1.407)],.0009,navy)
bpy.context.view_layer.update()
assert all(digest(bpy.data.objects[n])==v for n,v in before.items() if n not in targets),'Unrelated object changed'
assert hashlib.sha256(source.read_bytes()).hexdigest()==source_hash
scene['parent_web_revision']='courtyard43-interior22';scene['web_revision']='courtyard43-props24'
scene['props24']=json.dumps({'curtains':curtain_report,'reuseSource':'yongwang-jiayuan/laptop40','sourceSHA256':source_hash,'unchangedObjects':len(before)-len(targets),'targets':sorted(targets)})
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath,library=im.library),start=str(ROOM/'assets/full-room'))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
ns={'__file__':str(ROOM/'scripts/export-interior.py')};exec(compile(Path(ns['__file__']).read_text(encoding='utf8'),ns['__file__'],'exec'),ns);ns['export_interior']()
result={'revision':scene['web_revision'],'curtains':curtain_report,'unchanged':len(before)-len(targets)}
