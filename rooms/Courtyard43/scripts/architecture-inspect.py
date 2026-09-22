"""Read-only source inspection and temporary QA renders, via official MCP."""
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'analysis/Courtyard43/architecture'
OUT.mkdir(parents=True,exist_ok=True)
assert bpy.context.scene.get('component')=='architecture'
scene=bpy.context.scene
coll=bpy.data.collections['C43_Architecture']
def bp(p):return (p[0],-p[2],p[1])
checks=[]
for o in coll.all_objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data)
    checks.append({'name':o.name,'nonManifoldEdges':sum(not e.is_manifold for e in bm.edges),'zeroAreaFaces':sum(f.calc_area()<1e-14 for f in bm.faces),
                   'vertices':len(o.data.vertices),'uv':len(o.data.uv_layers),'morphs':list(o.data.shape_keys.key_blocks.keys()) if o.data.shape_keys else []})
    bm.free()
missing=[im.filepath for im in bpy.data.images if im.filepath and not Path(bpy.path.abspath(im.filepath)).exists()]
assert not missing,missing
assert not [c for c in checks if c['zeroAreaFaces']]
assert not [c for c in checks if c['nonManifoldEdges']]
diagnostics={'missingImages':missing,'geometry':checks,'parentedObjects':[{'name':o.name,'parent':o.parent.name} for o in coll.all_objects if o.parent],
             'interactions':[{'name':o.name,'data':json.loads(o['c43_interaction'])} for o in coll.all_objects if o.get('c43_interaction')]}
(OUT/'source-inspection.json').write_text(json.dumps(diagnostics,indent=2),encoding='utf-8')
# Temporary photographic preview lights, not saved into the component source.
scene.render.engine='CYCLES'
scene.cycles.samples=8
scene.cycles.use_denoising=True
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
if scene.world is None:scene.world=bpy.data.worlds.new('QA World')
scene.world.use_nodes=True
bg=next((n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND'),None) or scene.world.node_tree.nodes.new('ShaderNodeBackground')
wo=next((n for n in scene.world.node_tree.nodes if n.type=='OUTPUT_WORLD'),None) or scene.world.node_tree.nodes.new('ShaderNodeOutputWorld')
scene.world.node_tree.links.new(bg.outputs[0],wo.inputs[0])
bg.inputs[0].default_value=(.65,.73,.82,1)
bg.inputs[1].default_value=.45
scene.view_settings.view_transform='AgX'
def area(name,power,size,pos,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    o=bpy.data.objects.new(name,data);scene.collection.objects.link(o);o.location=bp(pos)
    o.rotation_euler=(Vector(bp(target))-o.location).to_track_quat('-Z','Y').to_euler()
area('QA broad window daylight',350,3,(.1,2.1,-1.5),(.1,1.0,1.3))
area('QA ceiling ambient',170,3,(.1,2.5,1.3),(.1,0,1.3))
area('QA entry fill',80,2,(1.1,2.1,2.5),(.1,1,0))
camdata=bpy.data.cameras.new('QA camera');cam=bpy.data.objects.new('QA camera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.lens=19.5
def render(name,pos,target,opened):
    for o in coll.all_objects:
        if o.type=='MESH' and o.data.shape_keys:o.data.shape_keys.key_blocks['Open'].value=opened
    cam.location=bp(pos);cam.rotation_euler=(Vector(bp(target))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
views=globals().get('QA_VIEWS',['entry-closed'])
if 'entry-closed' in views:render('entry-closed',(1.60,1.60,2.64),(-.40,1.15,.25),0)
if 'entry-open' in views:render('entry-open',(1.60,1.60,2.64),(-.40,1.15,.25),1)
if 'partition-open' in views:
    camdata.lens=29
    render('partition-open',(.55,1.58,1.67),(.77,1.40,-.11),1)
result={'rendered':views,'meshChecks':len(checks),'nonManifold':0,'zeroArea':0,'missingImages':missing}
