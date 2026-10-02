"""Official MCP: interior20 -> interior21 material separation.

No geometry, transforms, pivots, layout, alpha ordering or product text edits.
Base colour files are encoded sRGB; micro-surface inputs remain linear data.
Constant Principled base colours below are linear reflectance, not sRGB bytes.
"""
from pathlib import Path
import bpy,json,math,hashlib,struct,zlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior20'
bpy.context.preferences.filepaths.save_version=0
def geometry_digest(o):
    h=hashlib.sha256(repr((o.name,tuple(tuple(r) for r in o.matrix_world),o.parent.name if o.parent else None,dict(o.items()))).encode())
    if o.type=='MESH':h.update(repr(([tuple(v.co) for v in o.data.vertices],[(tuple(p.vertices),p.material_index) for p in o.data.polygons])).encode())
    return h.hexdigest()
before={o.name:geometry_digest(o) for o in scene.objects}
reports=[]
def calibrate(name,rough=None,spec=None,sheen=None,env=None,color=None,coat=None):
    old=bpy.data.materials.get(name)
    assert old,name
    m=old.copy();m.name=name+'_quality21'
    b=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    props=json.loads(m.get('web_props','{}'))
    for k,value,prop in [('Roughness',rough,'roughness'),('Specular IOR Level',spec,'specularIntensity'),('Sheen Weight',sheen,'sheen'),('Coat Weight',coat,'clearcoat')]:
        if value is not None:
            # A roughness map is a full value field, not a multiplier. Preserve
            # mapped roughness unless this stage explicitly supplies a scalar.
            for link in list(b.inputs[k].links):m.node_tree.links.remove(link)
            b.inputs[k].default_value=value;props[prop]=value
    if color is not None:
        assert not b.inputs['Base Color'].is_linked,name
        b.inputs['Base Color'].default_value=(*color,1);props.pop('color',None)
    if env is not None:props['envMapIntensity']=env
    if sheen is not None:
        b.inputs['Sheen Roughness'].default_value=.85
        b.inputs['Sheen Tint'].default_value=(.32,.33,.34,1)
    m['web_props']=json.dumps(props)
    users=[]
    for o in scene.objects:
        if o.type!='MESH':continue
        for i,slot in enumerate(o.material_slots):
            if slot.material==old:slot.material=m;users.append(o.name)
    reports.append({'source':name,'material':m.name,'objects':users,'properties':props})
    return m,b

# Slightly varied dry weave with no photographed light or coarse repeating grid.
# It is a small neutral reflectance texture generated inside official Blender.
n=512;v,u=np.mgrid[0:n,0:n];rng=np.random.default_rng(4321)
weave=1.0*np.sin(u*math.pi*.79)+.6*np.sin(v*math.pi*.73)+rng.normal(0,.7,(n,n))
rgb=np.clip(np.array([105,106,105])[None,None,:]+weave[:,:,None],0,255).astype(np.uint8)
def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',n,n,8,2,0,0,0))+chunk(b'sRGB',b'\0')
data+=chunk(b'IDAT',zlib.compress(b''.join(b'\0'+r.tobytes() for r in rgb),6))+chunk(b'IEND',b'')
path=ROOM/'assets/architecture/textures/curtain-dry-weave21.png';path.write_bytes(data)
image=bpy.data.images.load(str(path),check_existing=False);image.colorspace_settings.name='sRGB'
for side in ('Left','Right'):
    m,b=calibrate('C43_Dry_Blackout15_'+side,rough=.96,spec=.12,sheen=.055,env=.20,coat=0)
    b.inputs['Base Color'].links[0].from_node.image=image
    for node in m.node_tree.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.004
    b.inputs['Metallic'].default_value=0;b.inputs['Emission Strength'].default_value=0
    props=json.loads(m['web_props']);props.update(metalness=0,emissiveIntensity=0);m['web_props']=json.dumps(props)

calibrate('C43_WarmWhiteLaminate_07',rough=.48,spec=.38,coat=.035,color=(.70,.685,.645))
calibrate('C43_Chair18_WhiteShell',rough=.43,spec=.43,coat=0,color=(.73,.75,.72))
calibrate('C43_Chair15_BlackThinSeat',rough=.90,spec=.22,sheen=.12,color=(.038,.041,.039))
calibrate('C43_Chair18_SatinSteel',rough=.36,spec=.5)
calibrate('C43_Counter_Ivory_Paint',rough=.56,spec=.35,color=(.73,.705,.64))
calibrate('C43_Counter_Blue_Inset_Paint',rough=.52,spec=.36)
for name in ('C43_Textile_PlainCotton','C43_Textile_FloralCotton'):
    calibrate(name,rough=.91,spec=.23,sheen=.12)
calibrate('C43_Bucket_black_cotton_15',rough=.92,spec=.18,sheen=.09,color=(.029,.030,.032))
calibrate('C43_Bag15_indigo_print_15',rough=.66,spec=.32)
calibrate('C43_Bag15_ivory_print_15',rough=.70,spec=.32)
calibrate('C43_Tissue_thin_fibre_07',rough=.98,spec=.10)
# The existing wood/paint maps already encode physical grain and independent
# UV1 contact shading. Keep texture density; soften only their clear varnish.
for name in ('C43_Timber_satin_07','C43_MapleLaminate'):
    calibrate(name,spec=.42,coat=.025)
for name in ('C43_Wall_Balcony_Pier_Left_contact_material','C43_Wall_Left_contact_material','C43_Wall_Right_contact_material'):
    calibrate(name,rough=.94,spec=.18)

assert before=={o.name:geometry_digest(o) for o in scene.objects},'Material stage changed geometry or anchors'
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file and im.filepath:
        absolute=Path(bpy.path.abspath(im.filepath,library=im.library))
        assert absolute.is_file(),str(absolute)
        im.filepath=bpy.path.relpath(str(absolute),start=str(ROOM/'assets/full-room'))
scene['parent_web_revision']='courtyard43-interior20';scene['web_revision']='courtyard43-interior21'
scene['quality21_materials']=json.dumps(reports)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'revision':scene['web_revision'],'materials':reports,'geometryUnchanged':len(before)}
