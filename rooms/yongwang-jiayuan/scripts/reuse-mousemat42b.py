"""laptop42 -> laptop42b: reuse C43's approved 430x280x2mm printed mousemat.
Official Blender Lab MCP only. Preserve desk anchor, mouse, and source room.
"""
from pathlib import Path
import bpy, copy, json, shutil, hashlib
from mathutils import Vector
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='laptop42'
src=ROOT/'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend'
src_hash=hashlib.sha256(src.read_bytes()).hexdigest()
manifest=json.loads((ROOT/'room-site/dist/assets/rooms/Courtyard43/interior/scene.json').read_text('utf8'))
assert manifest['revision']=='courtyard43-logo26'
source_node=next(n for n in manifest['nodes'] if n['name']=='C43_DevKit_Mousemat')
with bpy.data.libraries.load(str(src),link=False) as (s,d):d.objects=['C43_DevKit_Mousemat']
donor=d.objects[0];me=donor.data.copy();target=obs[1022]
face_materials=[p.material_index for p in me.polygons]
# C43's long axis is front/back. Rotate it to match Yongwang's laptop orientation.
# Preserve original pad centre and top contact height, with no nonuniform scaling.
oldtop=max(v.co.z for v in target.data.vertices)
xs=[v.co.x for v in me.vertices];ys=[v.co.y for v in me.vertices];zs=[v.co.z for v in me.vertices]
cx=(min(xs)+max(xs))/2;cy=(min(ys)+max(ys))/2;top=max(zs)
for v in me.vertices:
    x,y,z=v.co;v.co=(y-cy,-(x-cx),z-top+oldtop)
newmats=[];texmap={}
for slot,mid in enumerate(source_node['material']):
    md=copy.deepcopy(manifest['materials'][mid]);newid=len(data['materials']);md['id']=newid
    material_copy=donor.data.materials[slot].copy();material_copy.name='Yongwang reused '+material_copy.name
    material_copy['web_material_id']=newid
    for key,tid in list(md['textures'].items()):
        if tid not in texmap:
            td=copy.deepcopy(manifest['textures'][tid]);newtid=len(data['textures'])
            original=ROOT/'room-site/dist'/td['webPath'];name='reused-c43-'+original.name
            shutil.copyfile(original,OUT/name)
            td.update(id=newtid,webPath='./assets/full-room/'+name);data['textures'].append(td);texmap[tid]=newtid
        md['textures'][key]=texmap[tid]
    for n in material_copy.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image:
            image=n.image.copy();p=Path(bpy.path.abspath(n.image.filepath,library=n.image.library))
            if not p.exists():p=src.parent/n.image.filepath.replace('\\','/').lstrip('/')
            targetpath=SOURCE/'textures'/('reused-c43-source-'+p.name)
            shutil.copyfile(p,targetpath);image.filepath=str(targetpath);n.image=image
    mats[newid]=material_copy;data['materials'].append(md);newmats.append(newid)
me.materials.clear()
for mid in newmats:me.materials.append(mats[mid])
target.data=me
for slot,mid in zip(target.material_slots,newmats):slot.link='DATA';slot.material=mats[mid]
for face,mid in zip(me.polygons,face_materials):face.material_index=mid
export(target);data['nodes'][1022]['material']=newmats
data['nodes'][1022]['userData']={**data['nodes'][1022].get('userData',{}),'reuse':'Courtyard43 C43_DevKit_Mousemat @ courtyard43-logo26','sizeSource':'supplied product graphic 430x280x2mm'}
target['web_user_data']=json.dumps(data['nodes'][1022]['userData'])
g=data['geometries'][data['nodes'][1022]['geometry']];groups=[]
for i,t in enumerate(me.loop_triangles):
    mi=me.polygons[t.polygon_index].material_index
    if groups and groups[-1]['materialIndex']==mi:groups[-1]['count']+=3
    else:groups.append({'start':i*3,'count':3,'materialIndex':mi})
g['groups']=groups
g['attributes']['uv1']=pack([tuple(me.uv_layers['UV1'].data[l.index].uv) for l in me.loops],2)
bpy.data.objects.remove(donor,do_unlink=True)
# Retire the old white plug stub belonging to the removed USB charger.
for o in obs.values():
    if o.get('purpose')=='USB adapter cable plug':
        nid=int(o['web_node_id']);o.hide_render=True;o.hide_set(True);data['nodes'][nid]['visible']=False;changed.add(nid)
assert hashlib.sha256(src.read_bytes()).hexdigest()==src_hash
result=save('laptop42b',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'mousemat42b':{'sourceRevision':'courtyard43-logo26','sourceObject':'C43_DevKit_Mousemat','sourceSHA256':src_hash,'dimensions_m':[.43,.28,.002],'mouseAndDeskUnchanged':True}})
