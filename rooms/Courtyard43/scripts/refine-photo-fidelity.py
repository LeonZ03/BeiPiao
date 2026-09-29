"""Photo-led macro-form pass, only via official Blender Lab MCP.

Parents: interior07 / architecture08 / furniture06 / props02. P04 is the
occupied-room reference; small proportions and hidden bag contents are estimates.
No approved architectural/furniture anchor moves. Historical helpers are loaded
as function definitions only: their old scene mutations are never executed.
"""
from pathlib import Path
import ast, bpy, bmesh, numpy as np, math, json, hashlib
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ROOM=ROOT/'rooms/Courtyard43'
scene=bpy.context.scene
kind=scene.get('component')
full=scene.get('stage')=='interior' and kind not in ('architecture','furniture','props')
parents={'architecture':'architecture08','furniture':'courtyard43-furniture06','props':'courtyard43-props02'}
assert scene.get('web_revision')=='courtyard43-interior07' if full else scene.get('component_revision')==parents[kind]
bpy.context.preferences.filepaths.save_version=0
bp=lambda p:Vector((p[0],-p[2],p[1]))
web=lambda p:Vector((p[0],p[2],-p[1]))
targets=set()
helper=ROOM/'scripts/refine-furnishings.py'
names={'digest','shader','material','assign','replace','solid','tube','lathe'}
tree=ast.parse(helper.read_text(encoding='utf-8'))
definitions=ast.unparse(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]))
definitions=definitions.replace("bpy.data.collections['C43_Props']", "bpy.data.collections['C43_Furniture' if kind=='furniture' else 'C43_Props']")
exec(compile(definitions,str(helper),'exec'))
bpy.context.view_layer.update()
before={o.name:digest(o) for o in scene.objects}

def smooth(x):
    x=max(0.,min(1.,x));return x*x*(3-2*x)

def deform(o,fn):
    targets.add(o.name);o.data=o.data.copy();inv=o.matrix_world.inverted()
    for v in o.data.vertices:v.co=inv@bp(fn(web(o.matrix_world@v.co)))
    o.data.update()

def duvet_field(p):
    x,y,z=p
    # Three local gathered folds, unequal in length and curvature. This field
    # is shared by BOTH shell layers and sewn hems, keeping connected edges.
    release=smooth((y-.48)/.08)
    q=x+.62-.48*(z-2.04)-.13*math.sin(z*3.3)
    q2=z-2.17+.38*x+.045*math.sin(x*6)
    rise=.102*math.exp(-(q/.12)**2-((z-2.1)/.66)**2)
    rise+=.074*math.exp(-(q2/.095)**2-((x+.3)/.85)**2)
    rise+=.031*math.exp(-((x+.95)/.22)**2-((z-1.6)/.30)**2)
    y+=rise*release
    return x,y,z

if full or kind=='furniture':
    for name in ['C43_FloralDuvet','C43_FloralDuvetSewnHem']:
        deform(bpy.data.objects[name],duvet_field)
    duvet=bpy.data.objects['C43_FloralDuvet']
    for uv in duvet.data.uv_layers['UVMap'].data:uv.uv*=1.10
    duvet['photo08']='P04 irregular gathered diagonal folds; shared shell/seam deformation; inferred height'
    # Visible small ochre marks on the headboard; no invented lettering.
    board=bpy.data.objects['C43_BedHeadboard']
    pts=[web(board.matrix_world@v.co) for v in board.data.vertices]
    front=max(p.x for p in pts)
    ochre=material('Headboard_small_ochre_marks',(.36,.24,.09),.85)
    for i,z in enumerate([1.78,2.15]):
        o=lathe('C43_Headboard_mark_'+str(i),(0,0,0),[(0,0),(.012,0),(.012,.0005),(0,.0005)],ochre,32)
        deform(o,lambda p,z=z:(front+.001+p.y,.98+p.x,z+p.z))

if full or kind=='architecture':
    for side in ['Left','Right']:
        o=bpy.data.objects['C43_Curtain_'+side];targets.add(o.name);o.data=o.data.copy()
        inv=o.matrix_world.inverted();n=121*65
        for key in o.data.shape_keys.key_blocks:
            for i,vtx in enumerate(key.data):
                j,k=divmod(i%n,121);a=k/120;v=j/64;p=web(o.matrix_world@vtx.co)
                seam=smooth(a/.09)*smooth((1-a)/.09)
                weight=smooth(v/.11)*seam*(.18 if key.name=='Open' else 1)
                # Broad irregular troughs drift down the cloth; top, hem
                # height and overlap edges remain exactly as the approved source.
                p.z+=weight*(.010*math.sin(a*17+.8*math.sin(v*3)+.4)+.004*math.sin(a*39-v*2.5))
                vtx.co=inv@bp(p)
        o.data.update()
        m=o.data.materials[0].copy();m.name='C43_Grey_satin_photo08_'+side;assign(o,[m]);b=shader(m)
        b.inputs['Roughness'].default_value=.58
        b.inputs['Sheen Weight'].default_value=.48;b.inputs['Sheen Roughness'].default_value=.55
        o['photo08']='Unequal drifting folds with pinned rings and preserved seam overlap; soft satin sheen'

if full or kind=='props':
    # Thin packaging bag, P04. The broad printed areas are visible but its
    # lettering is unreadable: retain colour blocking without invented text.
    navy=material('Packaging_muted_indigo',(.055,.061,.10),.47)
    cream=material('Packaging_offwhite',(.66,.67,.63),.56)
    vv=[];ff=[];uv=[];n=80;rows=41
    for j in range(rows):
        t=j/(rows-1);w=np.interp(t,[0,.12,.45,.76,1],[.075,.133,.141,.119,.068]);d=np.interp(t,[0,.12,.5,1],[.024,.056,.055,.022])
        for i in range(n):
            a=i*math.tau/n;env=math.sin(math.pi*t)
            fold=(.006*math.sin(5*a+t*14)+.003*math.sin(11*a-t*17))*env
            x=1.955+.026*math.sin(t*3.2)+(w+fold)*math.copysign(abs(math.cos(a))**.66,math.cos(a))
            y=1.215+.323*t+.012*math.sin(a*3+t*5)*env-.011*math.sin(a)**2*t**9
            z=1.455+(d+fold)*math.copysign(abs(math.sin(a))**.7,math.sin(a))
            vv.append((x,y,z));uv.append((i/n,t))
    for j in range(rows-1):
        for i in range(n):ff.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    ff.append(tuple(reversed(range(n))))
    bag=replace('C43_Hanging_bag',vv,ff,[cream,navy],uv);solid(bag,.0008)
    for p in bag.data.polygons:p.material_index=int(p.index>=16*n and len(p.vertices)==4)
    bag['photo08']='Short crumpled packaging bag with visible blue round content; unreadable branding omitted'
    # Short crinkled handles join the actual mouth and the existing hook.
    for k in range(2):
        lip=[Vector(p) for p in vv[-n:]]
        a=min(lip,key=lambda p:(p-Vector((1.90,1.537,1.43+k*.04))).length)
        b=min(lip,key=lambda p:(p-Vector((2.01,1.537,1.43+k*.04))).length)
        pts=[]
        for i in range(41):
            t=i/40;s=math.sin(math.pi*t);p=a.lerp(b,t);p.y+=.076*s;p.z=p.z*(1-s**2)+1.412*s**2;pts.append(p)
        verts=[];faces=[]
        for i,p in enumerate(pts):
            tangent=(pts[min(i+1,40)]-pts[max(i-1,0)]).normalized();across=Vector((tangent.y,-tangent.x,0))
            verts.extend(tuple(p+across*s*.006) for s in [-1,1])
        for i in range(40):faces.append((2*i,2*i+1,2*i+3,2*i+2))
        strap=replace('C43_Bag_strap_'+str(k),verts,faces,[navy]);solid(strap,.0008)
    blue=material('Visible_blue_round_content',(.10,.42,.64),.36)
    disc=lathe('C43_Bag_visible_blue_round_item',(0,0,0),[(0,0),(.032,0),(.038,.005),(.039,.017),(.036,.022),(0,.022)],blue,64)
    deform(disc,lambda p:(1.865+p.x,1.465+p.z,1.493+p.y))
    tube('C43_Bag_round_rim',[(1.865+.032*math.cos(a),1.465+.032*math.sin(a),1.516) for a in np.linspace(0,math.tau,65)],.0017,blue)
    # Differentiate one round hanging item from the two actual cap silhouettes.
    old=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('C43_Cap1_')]
    points=[web(o.matrix_world@v.co) for o in old for v in o.data.vertices]
    cx=(min(p.x for p in points)+max(p.x for p in points))/2
    cy=(min(p.y for p in points)+max(p.y for p in points))/2
    for o in old:targets.add(o.name);bpy.data.objects.remove(o,do_unlink=True)
    black=material('Round_hanging_charcoal',(.023,.025,.024),.67)
    disc=lathe('C43_Round_hanging_item',(0,0,0),[(0,0),(.056,0),(.061,.006),(.061,.014),(.054,.020),(0,.020)],black,64)
    deform(disc,lambda p:(cx+p.x,cy+p.z,.020+p.y))
    hook=bpy.data.objects['C43_Cap_hook_0'];hp=[web(hook.matrix_world@v.co) for v in hook.data.vertices]
    top=max(p.y for p in hp)
    tube(hook.name,[(cx,top,.002),(cx,top,.029),(cx,cy+.047,.029)],.0025,black)
    # Existing caps stay connected but cease to be identical silhouettes.
    for prefix,scale in [('C43_Cap2_',(.91,1.07,1.0)),('C43_Cap3_',(1.08,.92,.90))]:
        group=[o for o in scene.objects if o.type=='MESH' and o.name.startswith(prefix)]
        pts=[web(o.matrix_world@v.co) for o in group for v in o.data.vertices]
        center=Vector(tuple((min(p[k] for p in pts)+max(p[k] for p in pts))/2 for k in range(3)))
        # Keep the stitched crown and hook connections unchanged; only bills
        # are reshaped smoothly from their roots, using identical seam field.
        for o in group:
            if 'bill' in o.name:
                deform(o,lambda p,c=center,s=scale:tuple(c[k]+(p[k]-c[k])*(1+(s[k]-1)*smooth((c.y-p.y)/.08)) for k in range(3)))
    # Thin clear plastic needs a readable rim rather than nearly invisible walls.
    for name,alpha,rough in [('C43_Ribbed_water_bottle',.19,.12),('C43_Plastic_cup',.28,.23)]:
        o=bpy.data.objects[name];m=o.data.materials[0].copy();m.name=name+'_photo08';assign(o,[m]);b=shader(m)
        b.inputs['Alpha'].default_value=alpha;b.inputs['Roughness'].default_value=rough
        b.inputs['Coat Weight'].default_value=.32;b.inputs['Coat Roughness'].default_value=.13
        props=json.loads(m.get('web_props','{}'));props['opacity']=alpha;m['web_props']=json.dumps(props)
    # Compress the tissue package and its paper/slot together, preserving support.
    for o in list(scene.objects):
        if o.type=='MESH' and o.name.startswith('C43_Tissue_'):
            deform(o,lambda p:(p.x,1.0125+(p.y-1.0125)*.69,p.z+.0018*math.sin((p.x-1.1)*93)*smooth((p.y-1.013)/.025)))

bpy.context.view_layer.update()
unchanged={n:digest(bpy.data.objects[n]) for n in before if n not in targets}
assert all(v==before[n] for n,v in unchanged.items()),'Unrelated object changed'
if full:
    scene['parent_web_revision']='courtyard43-interior07';scene['web_revision']='courtyard43-interior08'
    records=json.loads(scene['components'])
    for r in records:r['sha256']=hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest()
    scene['components']=json.dumps(records);output=ROOM/'assets/full-room/Courtyard43-interior.blend'
else:
    scene['component_parent_revision']=scene['component_revision']
    scene['component_revision']={'architecture':'architecture09','furniture':'courtyard43-furniture07','props':'courtyard43-props03'}[kind]
    output=ROOM/f'assets/{kind}/Courtyard43-{kind}.blend'
scene['photo08']='P04 macro folds, uneven satin drapes, packaging bag silhouette and supported small details; estimated, not measured'
for im in bpy.data.images:
    if im.source=='FILE' and im.filepath:im.filepath=bpy.path.relpath(bpy.path.abspath(im.filepath,library=im.library),start=str(output.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(output))
result={'saved':str(output),'targets':sorted(targets),'unchangedObjects':len(unchanged)}
if full:
    p=ROOM/'scripts/export-interior.py';scope={'__file__':str(p),'__name__':'export'}
    exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),scope);result['export']=scope['export_interior']()
