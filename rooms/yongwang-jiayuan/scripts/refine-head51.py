"""correction51 -> correction51b: classic Mk-II angular helmet only.

Official Blender Lab MCP. User authorized a classic reference head after the
original head close-up could not be located. Bandai RG Mk-II product images:
https://www.bandaispirits.co.jp/products/search/detail.php?grp_id=5325&prd_id=4543112763198000
Keep the existing Mk-II face, V-fin, sensors, body, weapons and pose.
"""
from pathlib import Path
import ast,bpy,bmesh,math,json,copy
from mathutils import Vector
from mathutils.kdtree import KDTree
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='correction51'
tree=ast.parse((HERE/'refine-correction51.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ('export_fit','finish')],type_ignores=[]),'fit51','exec'))
mini=ROOT/'rooms/yongwang-jiayuan/assets/shelf-gundam/shelf-gundam.blend'
with bpy.data.libraries.load(str(mini),link=False)as(src,dst):dst.objects=['helmet main shell']
part=dst.objects[0];collection.objects.link(part);bpy.context.view_layer.update()
floor=json.loads((ROOT/'rooms/yongwang-jiayuan/history/inputs/viewer26-head-points.json').read_text('utf8'))['floor']
old=[(2.45,.125,.110),(2.49,.147,.128),(2.57,.157,.134),(2.65,.147,.122),(2.70,.125,.105),(2.732,.080,.065),(2.742,.012,.012)]
new=[(2.45,.119,.104),(2.49,.143,.119),(2.57,.153,.125),(2.65,.143,.118),(2.70,.125,.105),(2.733,.107,.091),(2.739,.103,.088)]
kd=KDTree(224);replacement=[]
# A chamfered rectangular outline: broad front/side armour planes and a flat
# crown, not an ellipsoid or a spherical cap. Match 32 vertices per ring to
# the rejected patch so the material batch and all body topology remain stable.
for k,((oz,ox,oy),(nz,nx,ny))in enumerate(zip(old,new)):
    for j in range(32):
        a=math.tau*j/32;p=part.matrix_world@Vector((ox*math.cos(a),.030+oy*math.sin(a),oz))-Vector((0,0,floor))
        kd.insert(p,k*32+j)
        # Four subdivisions per octagonal edge retain clean planar armour.
        c,s=math.cos(a),math.sin(a)
        radius=min(1/max(1e-8,abs(c)),1/max(1e-8,abs(s)),1.65/(abs(c)+abs(s)))
        x=nx*radius*c;y=.030+ny*radius*s
        replacement.append(part.matrix_world@Vector((x,y,nz))-Vector((0,0,floor)))
kd.balance();o=obs[1253];o.data=o.data.copy();original=[v.co.copy()for v in o.data.vertices];selected=set()
for v in o.data.vertices:
    p,i,d=kd.find(v.co)
    # Join-to-batch float32 transform round trip shifted this entire shell by
    # 3.80–3.83 micrometres. Explicitly verified all 224 points, not a broad
    # spatial head mask; the unique-count assertion guards unrelated armour.
    if d<5e-6:v.co=replacement[i];selected.add(v.index)
assert len(selected)==224,('Head-only vertex mapping',len(selected))
for f in o.data.polygons:
    flags=[i in selected for i in f.vertices]
    assert all(flags)or not any(flags),'Partial head/body polygon'
    if all(flags):f.use_smooth=False
assert all(v.co==p for v,p in zip(o.data.vertices,original)if v.index not in selected)
finish(o);bpy.data.objects.remove(part,do_unlink=True)
result=save('correction51b',{'parent':'correction51','head':'Bandai classic RX-178 Mk-II faceted crown; 224 helmet-shell vertices only','bodyUnchanged':True,'source':'Bandai RG product images; user-authorized classic substitute'})
