"""interior10 -> interior11: heavy matte blackout cloth and first-entry defaults.
Run ONLY through official Blender Lab MCP. Approved room/exterior retained.
"""
from pathlib import Path
import bpy,json,math,hashlib
from mathutils import Quaternion,Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior10'
bpy.context.preferences.filepaths.save_version=0
def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def horizontal(a,side):
    # 30 mm overlaps beyond both jambs; 66 mm combined centre overlap.
    return (-.050*(1-a)+.031*a) if side=='Left' else (-.027*(1-a)+.050*a)
for side in ['Left','Right']:
    o=bpy.data.objects['C43_Curtain_'+side];o.data=o.data.copy();n=121*65
    for key in o.data.shape_keys.key_blocks:
        opened=key.name=='Open'
        original=[v.co.copy() for v in key.data]
        for i,v in enumerate(key.data):
            j,k=divmod(i%n,121);a=k/120;t=j/64
            outer=(1-a) if side=='Left' else a
            shift=horizontal(a,side) if not opened else (-.05*(1-a) if side=='Left' else .05*a)
            p=original[i].copy();p.x+=shift
            # Closed two-sided shell, increased body thickness; header still sewn to rings.
            partner=original[(i+n)%(2*n)];mid=(p.y+partner.y)/2
            p.y=mid+(p.y-mid)*(1+.7*smooth(t/.08))
            # Fixed side returns approach the jamb face below the sewn header.
            w=smooth((outer-.94)/.06)*smooth(t/.10)
            p.y=p.y*(1-w)+(-.004+(p.y-mid))*w
            # Header overlaps the lintel by 1 mm; lower hem/support is unchanged.
            p.z+=.002*smooth((.07-t)/.07)
            v.co=p
    for v,k in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data):v.co=k.co
    o['cloth_thickness_m']=.00289;o['blackout11']='Opaque matte double-sided cloth; 30mm side coverage, 66mm centre overlap, fixed jamb returns'
    m=o.data.materials[0].copy();m.name='C43_Heavy_Matte_Blackout_'+side;o.data.materials[0]=m
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Roughness'].default_value=.94;bs.inputs['Sheen Weight'].default_value=.08
    bs.inputs['Sheen Roughness'].default_value=.9;bs.inputs['Emission Strength'].default_value=0
    bs.inputs['Alpha'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.18
    for node in list(m.node_tree.nodes):
        if node.get('web_map')=='emissiveMap':m.node_tree.nodes.remove(node)
        elif node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.13
    m['web_props']=json.dumps({'side':2,'roughness':.94,'sheen':.08,'specularIntensity':.3,'emissiveIntensity':0})
    m['web_userData']=json.dumps({'surfaceFinish':'thick matte blackout woven cloth','blackoutCurtain':True,'curtainSide':side.lower()})
    rings=bpy.data.objects[o.name+'_Rings'];rings.data=rings.data.copy()
    for key in rings.data.shape_keys.key_blocks:
        for r in range(11):
            a=.016+r*(.984-.016)/10
            shift=horizontal(a,side) if key.name!='Open' else (-.05*(1-a) if side=='Left' else .05*a)
            for v in list(key.data)[r*160:(r+1)*160]:v.co.x+=shift
    for v,k in zip(rings.data.vertices,rings.data.shape_keys.key_blocks[0].data):v.co=k.co
    pivot=bpy.data.objects[o.name+'_Pivot'];meta=json.loads(pivot['c43_interaction']);meta['defaultOpen']=True;pivot['c43_interaction']=json.dumps(meta)
door=bpy.data.objects['C43_Door_Hinge'];meta=json.loads(door['c43_interaction'])
assert meta['defaultOpen'] is True
q=door.rotation_euler.to_quaternion()@Quaternion(Vector((0,0,1)),-meta['openAngle'])
door.rotation_euler=q.to_euler(door.rotation_mode);meta['defaultOpen']=False;door['c43_interaction']=json.dumps(meta)
bpy.context.view_layer.update()
component=ROOM/'assets/blackout-curtains';component.mkdir(exist_ok=True)
objects={bpy.data.objects['C43_Curtain_'+side+suffix] for side in ['Left','Right'] for suffix in ['', '_Rings','_Pivot']}
p=component/'Courtyard43-blackout-curtains.blend'
bpy.data.libraries.write(str(p),objects,path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(s['components']);components.append({'component':'blackout-curtains','revision':'blackout11','source':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
s['components']=json.dumps(components);s['parent_web_revision']='courtyard43-interior10';s['web_revision']='courtyard43-interior11'
s['initial_state11']='Both curtains open, entry door closed, ceiling light off, audio muted. User confirmed.'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';d={'__file__':str(p),'__name__':'blackout_export'}
exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),d)
result=d['export_interior']()
