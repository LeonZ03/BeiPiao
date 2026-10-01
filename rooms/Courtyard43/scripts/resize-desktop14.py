"""Official Blender Lab MCP only. User correction: portrait 430x280x2mm mat,
uniformly smaller boards, shorter box. Parent interior13, no room rebuild.
The provided product bitmap is unchanged; UVs select only its mat rectangle.
"""
from pathlib import Path
import bpy, json, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[3];ROOM=ROOT/'rooms/Courtyard43'
s=bpy.context.scene
assert s.get('web_revision')=='courtyard43-interior13' and s.get('desktop13_fitted')
old=Vector((-1.037,.7433,.30));new=Vector((-1.030,.742,.260));scale=.70
web=lambda v:Vector((v.x,v.z,-v.y))
bp=lambda v:Vector((v.x,-v.z,v.y))
kit=[o for o in s.objects if o.name.startswith('C43_DevKit_')]
assert len(kit)==10
# Keep the board aspect, components, bevels, and relative board arrangement.
for o in kit:
    if o.name=='C43_DevKit_Mousemat':continue
    o.data=o.data.copy()
    for v in o.data.vertices:v.co=bp(new+(web(v.co)-old)*scale)
    o.data.update()

# Box width was oversized relative to the two boards. Narrow its body/cover,
# reduce the height of the hinged lid without changing the support rim.
box=bpy.data.objects['C43_DevKit_Open_cardboard_box']
box_cx=new.x+(-1.063-old.x)*scale
lid_hinge=new.y+(.798-old.y)*scale
for v in box.data.vertices:
    p=web(v.co);p.x=box_cx+(p.x-box_cx)*.86
    if p.y>lid_hinge:p.y=lid_hinge+(p.y-lid_hinge)*.78
    v.co=bp(p)
box.data.update()
# Refit the film as a smaller intact sheet; preserve circular air pockets.
film=bpy.data.objects['C43_DevKit_Bubble_wrap']
film_c=Vector((box_cx,new.y+(.748-old.y)*scale,new.z+(.205-old.z)*scale))
for v in film.data.vertices:v.co=bp(film_c+(web(v.co)-film_c)*.86)
film.data.update()

# Replace the old approximated lettering/linework as one actual 2mm fabric mat.
o=bpy.data.objects['C43_DevKit_Mousemat'];old_mesh=o.data
body=bpy.data.materials['C43_DevKit_mousemat']
top=body.copy();top.name='C43_DevKit_mousemat_product_print'
nodes=top.node_tree.nodes;links=top.node_tree.links
bs=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
img=bpy.data.images.load(str(ROOM/'assets/development-kit/textures/mousemat-product-reference.jpg'),check_existing=True)
img.colorspace_settings.name='sRGB';img.filepath=bpy.path.relpath(img.filepath)
tex=nodes.new('ShaderNodeTexImage');tex.image=img;tex.extension='EXTEND'
uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],bs.inputs['Base Color'])
bs.inputs['Roughness'].default_value=.99
top['web_userData']=json.dumps({'surfaceFinish':'Printed matte woven mousemat','reference':'User product graphic; UV crop only; no generated replacement print','sizeSource':'430x280x2mm printed on supplied product image'})
# Weave retains its physical density on a distinct coordinate set. The printed
# product texture is not used as bump, so diagrams do not become raised plastic.
for m in [body,top]:
    for n in list(m.node_tree.nodes):
        if n.type=='TEX_IMAGE' and n.image and n.image.name=='black-textile-weave':
            u=m.node_tree.nodes.new('ShaderNodeUVMap');u.uv_map='UV1';m.node_tree.links.new(u.outputs['UV'],n.inputs['Vector'])

cx=-1.03;front=.49;back=.06;w=.28;d=.43;r=.015
vs=[];fs=[];mis=[]
def outline(inset,y):
    pts=[]
    for x,z,start in [(cx+w/2-r,front-r,0),(cx-w/2+r,front-r,90),(cx-w/2+r,back+r,180),(cx+w/2-r,back+r,270)]:
        for i in range(9):
            a=math.radians(start+i*90/8)
            pts.append((x+(r-inset)*math.cos(a),y,z+(r-inset)*math.sin(a)))
    return pts
# Cross-section rounded only at the tiny upper/lower edge, preserving the
# nominal overall 280x430mm envelope and exact tabletop contact.
for inset,y in [(.00025,.740),(0,.74025),(0,.74175),(.00025,.742)]:vs.extend(outline(inset,y))
n=36
fs.append(tuple(range(n-1,-1,-1)));mis.append(0)
for ring in range(3):
    for i in range(n):fs.append((ring*n+i,ring*n+(i+1)%n,(ring+1)*n+(i+1)%n,(ring+1)*n+i));mis.append(0)
fs.append(tuple(range(3*n,4*n)));mis.append(1)
mesh=bpy.data.meshes.new('C43_DevKit_portrait_430x280x2');mesh.from_pydata([bp(Vector(p)) for p in vs],[],fs)
mesh.materials.append(body);mesh.materials.append(top);mesh.update()
# Web-to-Blender coordinates are right handed; correct winding for the XZ
# perimeter, whose top face normal initially points downward.
import bmesh
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
for p,mi in zip(mesh.polygons,mis):p.material_index=mi
uv0=mesh.uv_layers.new(name='UVMap');uv1=mesh.uv_layers.new(name='UV1')
for p in mesh.polygons:
    for li in p.loop_indices:
        v=web(mesh.vertices[mesh.loops[li].vertex_index].co)
        # Rotate the landscape product artwork 90 degrees on the portrait mat:
        # long printed X axis runs from desk front to wall, matching close-up.
        a=(front-v.z)/d;b=(cx+w/2-v.x)/w
        uv0.data[li].uv=(104/640+a*432/640,(640-403)/640+b*288/640)
        uv1.data[li].uv=(v.x*20,v.z*20)
o.data=mesh;o['source']='User product spec 430x280x2mm; portrait placement, unmodified bitmap sampled by UV'
o['web_userData']=json.dumps({'physicalSize':[.28,.002,.43],'orientation':'long side front-to-back','revision':'desktop14'})
bpy.context.view_layer.update()

def tree(name):
    ob=bpy.data.objects['C43_DevKit_'+name];m=ob.data
    return BVHTree.FromPolygons([ob.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
main,small,box_tree=[tree(n) for n in ['Main_board','Expansion_board','Open_cardboard_box']]
assert not main.overlap(small),'Board separation changed'
assert not main.overlap(box_tree) and not small.overlap(box_tree),'Box crosses a board'
s['parent_web_revision']='courtyard43-interior13';s['web_revision']='courtyard43-interior14';s['desktop_kit_revision']='desktop14'
s['desktop14_notes']='430x280x2mm portrait mat from product reference; boards/case/contents 70% uniform scale; box width 86% and lid height 78% after uniform scale.'
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOM/'assets/full-room/Courtyard43-interior.blend'))
result={'revision':s['web_revision'],'kitObjects':len(kit),'scale':scale,'matSize':[w,.002,d],'boardAndBoxIntersections':0}
