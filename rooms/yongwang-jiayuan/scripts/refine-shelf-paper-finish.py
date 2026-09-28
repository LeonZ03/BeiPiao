"""shelf35 -> shelf36: remove the old sticker placeholder and relax tissue tips.
Run through Blender Lab MCP on the complete shelf35 source, after browser review.
"""
from pathlib import Path
import bpy, math, json, copy
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text(encoding='utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']=='shelf35' and bpy.context.scene.get('web_revision')=='shelf35'
# Preserve its stable ID, but retire the old opaque cuboid that hid the decal.
old=obs[1489];old.hide_render=True;old.hide_viewport=True
data['nodes'][1489]['visible']=False;data['nodes'][1489]['castShadow']=False
data['nodes'][1489]['name']='retired-wall-sticker-placeholder';old.name='retired-wall-sticker-placeholder';old['web_name']=old.name
changed.add(1489)
for k,nid in enumerate([1099,1100]):
    v=[];f=[];uv=[];N=32;M=24
    for j in range(M+1):
        t=j/M
        for i in range(N+1):
            u=i/N
            if k==0:
                x=-.003-.043*t*t+.009*math.sin(u*7.5+.6)*math.sin(t*math.pi/2)
                y=.094+t*(.034+.038*math.sin(math.pi*(.10+.90*u)))+.004*math.sin(u*13)*t
                z=(u-.5)*(.082+.028*t)
            else:
                x=.003+.014*t+.010*math.sin(u*9+t*3)*t
                y=.094+t*(.050+.068*math.exp(-((u-.72)/.19)**2))
                z=(u-.5)*(.082+.010*t)+.008*math.sin(t*3)*t
            v.append([x,y,z]);uv.append([u,t])
    for j in range(M):
        for i in range(N):
            a=j*(N+1)+i;f.append([a,a+1,a+N+2,a+N+1])
    o=attach(mesh('Soft tissue sheet',v,f,uv,True),f'raised-folded-tissue-{k}',before['nodes'][nid]['material'],1096,nid)
    activate(o);mod=o.modifiers.new('Thin tissue thickness','SOLIDIFY');mod.thickness=.00018
    bpy.ops.object.modifier_apply(modifier=mod.name);export(o)
    meta={'authoring':'Blender','blenderNode':nid,'revision':'shelf36','shelfDetail':True}
    o['web_user_data']=json.dumps(meta);data['nodes'][nid]['userData']=meta
    data['geometries'][-1]['userData']['revision']='shelf36'
data['statistics']['shelfDetails']['revision']='shelf36'
data['statistics']['shelfDetails']['retiredPlaceholder']=1489
assert changed=={1099,1100,1489}
result=save('shelf36',copy.deepcopy(before['statistics']['exteriorRefinement']))
