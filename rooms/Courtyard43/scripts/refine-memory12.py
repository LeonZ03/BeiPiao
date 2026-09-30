"""Official Blender Lab MCP only: interior11 -> interior12.
Repair screen depth, gathered blackout cloth and the existing doorway finish.
Approved wall/doorway boundaries and interaction pivots are retained.
"""
from pathlib import Path
import bpy, json, math, hashlib
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43';s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior11'
bpy.context.preferences.filepaths.save_version=0
def smooth(t):
 t=max(0,min(1,t));return t*t*(3-2*t)
def web(v):return Vector((v[0],-v[2],v[1]))
def replace_box(name,lo,hi,mat,bevel=0):
 o=bpy.data.objects[name];inv=o.matrix_world.inverted()
 vs=[inv@web((x,y,z)) for x,y,z in [(lo[0],lo[1],lo[2]),(hi[0],lo[1],lo[2]),(hi[0],hi[1],lo[2]),(lo[0],hi[1],lo[2]),(lo[0],lo[1],hi[2]),(hi[0],lo[1],hi[2]),(hi[0],hi[1],hi[2]),(lo[0],hi[1],hi[2])]]
 # web -> Blender is right-handed; consistent exterior face winding.
 fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(3,7,6,2),(0,4,7,3),(1,2,6,5)]
 m=bpy.data.meshes.new(name+'_memory12');m.from_pydata(vs,[],fs);m.materials.append(mat);m.update();o.data=m
 bpy.context.view_layer.objects.active=o;o.select_set(True)
 if bevel:
  mod=o.modifiers.new('Soft painted edge','BEVEL');mod.width=bevel;mod.segments=3
  bpy.ops.object.modifier_apply(modifier=mod.name)
 m=o.data;uv=m.uv_layers.new(name='UVMap')
 for p in m.polygons:
  axis=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=axis]
  for li in p.loop_indices:
   v=o.matrix_world@m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(v[axes[0]],v[axes[1]])
 o.select_set(False)
 return o

# Flat coplanar plaster surfaces with consistent material: no rounded joints.
wall=bpy.data.materials['C43_Warm_white_plaster']
replace_box('C43_Wall_Entry_Left',(-2.025,0,2.85),(1.055,2.75,2.97),wall)
replace_box('C43_Wall_Entry_Header',(1.055,2.10,2.85),(1.905,2.75,2.97),wall)
replace_box('C43_Wall_Entry_Right',(1.905,0,2.85),(2.225,2.75,2.97),wall)
paint=bpy.data.materials['C43_Aged_ivory_painted_trim']
# 13 mm proud of plaster; liners stand 6 mm inside the opening, never coplanar.
replace_box('C43_Door_Jamb',(1.017,0,2.837),(1.061,2.091,2.979),paint,.0012)
replace_box('C43_Door_Jamb.001',(1.899,0,2.837),(1.943,2.091,2.979),paint,.0012)
replace_box('C43_Door_Jamb_Header',(1.017,2.092,2.837),(1.943,2.132,2.979),paint,.0012)
# Correct the old leaf/jamb overlap without moving the approved hinge or handle.
o=bpy.data.objects['C43_Door_Leaf'];o.data=o.data.copy();inv=o.matrix_world.inverted()
for v in o.data.vertices:
 p=o.matrix_world@v.co;p.x=1.066+(p.x-1.039)/.842*.828;p.z=.008+p.z/2.10*2.077;v.co=inv@p
o['memory12']='Leaf edge clearance fitted to existing approved opening and pivot'

# The reed-pattern screen is visually opaque, unlike the separate clear window.
m=bpy.data.materials['C43_Reed_pattern_frosted_glass'];bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Alpha'].default_value=1
props=json.loads(m.get('web_props','{}'));props.update(opacity=1,transparent=False,depthWrite=True,roughness=.88);m['web_props']=json.dumps(props)
meta=json.loads(m.get('web_userData','{}'));meta['opaquePrivacyScreen']=True;m['web_userData']=json.dumps(meta)

# Keep the approved closed outline, broaden only the gathered bundle.
# Thickness is offset along the actual surface normal, not just the room axis.
n=121*65
for side in ['Left','Right']:
 o=bpy.data.objects['C43_Curtain_'+side];o.data=o.data.copy()
 for key in o.data.shape_keys.key_blocks:
  old=[v.co.copy() for v in key.data];centres=[]
  for i in range(n):
   p=(old[i]+old[i+n])*.5
   if key.name=='Open':p.x=(-.68+(p.x+.68)*(.31/.215)) if side=='Left' else (1.48-(1.48-p.x)*(.31/.215))
   centres.append(p)
  for i in range(n):
   j,k=divmod(i,121);a=k/120;t=j/64
   du=centres[j*121+min(120,k+1)]-centres[j*121+max(0,k-1)]
   dv=centres[min(64,j+1)*121+k]-centres[max(0,j-1)*121+k]
   normal=du.cross(dv).normalized()
   if normal.y>0:normal=-normal
   half=(old[i]-old[i+n]).length*.5
   # Preserve the sewn header/rings and fixed side return exactly; the body
   # gains real normal thickness even on the steep gathered folds.
   w=smooth(t/.08)*smooth(min(a,1-a)/.045)
   offset=Vector((0,-half,0)).lerp(normal*max(half,.0017),w)
   key.data[i].co=centres[i]+offset;key.data[i+n].co=centres[i]-offset
 for v,k in zip(o.data.vertices,o.data.shape_keys.key_blocks[0].data):v.co=k.co
 o['memory12']='Broad gathered bundle with normal-offset two-sided opaque fabric'
 m=o.data.materials[0].copy();m.name='C43_Dry_Blackout_'+side;o.data.materials[0]=m
 bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
 bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=.025;bs.inputs['Sheen Weight'].default_value=0
 for node in m.node_tree.nodes:
  if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.035
 props=json.loads(m['web_props']);props.update(roughness=1,sheen=0,specularIntensity=.035,envMapIntensity=.12);m['web_props']=json.dumps(props)
 rings=bpy.data.objects[o.name+'_Rings'];rings.data=rings.data.copy();key=rings.data.shape_keys.key_blocks['Open']
 for r in range(11):
  points=list(key.data)[r*160:(r+1)*160];x=sum(v.co.x for v in points)/160
  target=(-.68+(x+.68)*(.31/.215)) if side=='Left' else (1.48-(1.48-x)*(.31/.215))
  for v in points:v.co.x+=target-x
 for v,k in zip(rings.data.vertices,rings.data.shape_keys.key_blocks[0].data):v.co=k.co
bpy.context.view_layer.update()
component=ROOM/'assets/blackout-curtains/Courtyard43-blackout-curtains.blend'
objects={bpy.data.objects['C43_Curtain_'+side+suffix] for side in ['Left','Right'] for suffix in ['', '_Rings','_Pivot']}
bpy.data.libraries.write(str(component),objects,path_remap='RELATIVE',fake_user=True,compress=True)
components=json.loads(s['components'])
for c in components:
 if c['component']=='blackout-curtains':c['revision']='blackout12';c['sha256']=hashlib.sha256(component.read_bytes()).hexdigest()
s['components']=json.dumps(components);s['parent_web_revision']='courtyard43-interior11';s['web_revision']='courtyard43-interior12'
s['memory12']='Opaque privacy screen, fitted flush doorway and dry gathered blackout cloth; original scene layout retained'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
p=ROOM/'scripts/export-interior.py';d={'__file__':str(p),'__name__':'memory_export'};exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),d)
result=d['export_interior']()
