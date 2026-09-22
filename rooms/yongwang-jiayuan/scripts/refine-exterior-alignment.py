"""exterior31f -> exterior32. Fix exported attachments and exterior finishes.

Execute through official Blender Lab MCP. No room geometry, lighting, trees,
window positions or motorcycle changes. Finish values are photo estimates.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='exterior31f'
assert bpy.context.scene.get('web_revision')=='exterior31f'

bpy.context.view_layer.update()
glasses=[n for n in before['nodes'] if before['materials'][n.get('material',0)]['userData'].get('windowReflection')]
assert len(glasses)==43
glass_heights={g['id']:float(np.ptp(read(before['geometries'][g['geometry']]['attributes']['position'])[:,1])) for g in glasses}
attachments=[];corrected=[]
for nid,o in obs.items():
    purpose=o.get('purpose')
    if purpose not in ('Window cavity','Window sill drip'):continue
    d=data['nodes'][nid]
    matrix=flat(C.inverted()@o.matrix_local@C)
    if not np.allclose(matrix,d['matrix'],atol=1e-6):corrected.append(nid)
    d['matrix']=matrix
    coords=np.array([[v.co.x,v.co.z,-v.co.y] for v in o.data.vertices]);center=(coords.min(0)+coords.max(0))/2
    def expected_y(g):return g['matrix'][13]-(glass_heights[g['id']]/2+.056 if purpose=='Window sill drip' else 0)
    matches=[g for g in glasses if g['parent']==d['parent'] and abs(g['matrix'][12]-center[0])<.001 and abs(expected_y(g)-center[1])<.001]
    assert matches,('Missing window',nid,list(center),[(g['id'],g['matrix'][12:15]) for g in glasses if g['parent']==d['parent']][:4])
    target=min(matches,key=lambda g:abs(g['matrix'][13]-center[1]))
    assert abs(expected_y(target)-center[1])<.001
    d['userData'].update(exteriorWindowGlass=target['id'],exteriorWindowPart=purpose,revision='exterior32')
    o['web_user_data']=json.dumps(d['userData']);changed.add(nid);attachments.append(nid)
assert len(attachments)==86 and len(corrected)==60

# Neutral concrete and light mineral coatings. These PNG samples are sRGB;
# leave the room's exposure and lighting unchanged instead of compensating there.
rng=np.random.default_rng(3201);N=512;y,x=np.mgrid[0:N,0:N]/N
patch=.006*np.sin(x*math.tau*2+.5*np.sin(y*math.tau*3))+.004*np.cos(y*math.tau*3+x*5)
grain=rng.normal(0,.0035,(N,N))
def albedo(name,base,variation=1):
    pixels=np.array(base)[None,None,:]+(patch+grain)[:,:,None]*variation
    tid=texture(name,pixels)
    # Verify saved byte samples before publishing to avoid double sRGB decoding.
    check=bpy.data.images.load(str(SOURCE/'textures'/f'{name}.png'),check_existing=False)
    values=np.array(check.pixels[:]).reshape(-1,4)[:,:3].mean(0)
    assert np.max(np.abs(values-np.array(base)))<.012,(name,values)
    bpy.data.images.remove(check)
    return tid
grey_t=albedo('exterior32-light-grey-render',(.765,.78,.774))
cream_t=albedo('exterior32-light-ivory-render',(.852,.844,.811))
cement_t=albedo('exterior32-grey-cement',(.566,.592,.607),.75)
coping_t=albedo('exterior32-concrete-coping',(.64,.66,.667),.7)
remap={}
for old,tid,label in [(213,grey_t,'Light mineral grey'),(214,cream_t,'Light ivory render'),(228,cream_t,'Light ivory distant render'),(229,grey_t,'Light grey distant render'),(215,coping_t,'Grey concrete coping'),(230,coping_t,'Grey concrete distant coping'),(216,cement_t,'Neutral grey cement ground'),(217,cement_t,'Neutral grey cement paving')]:
    tex=copy.deepcopy(before['materials'][old]['textures']);tex['map']=tid
    remap[old]=material('Courtyard · '+label,old,color=(1,1,1),rough=.87,textures=tex)
    data['materials'][remap[old]]['userData']['revision']='exterior32'
    mats[remap[old]]['web_user_data']=json.dumps(data['materials'][remap[old]]['userData'])
for d in data['nodes']:
    if d.get('material') in remap:set_material(d['id'],remap[d['material']])

# World-space source/pack equality, including transformed-parent attachments.
def web_world(nid):
    d=data['nodes'][nid];m=Matrix(np.array(d['matrix']).reshape(4,4).T.tolist())
    return web_world(d['parent'])@m if d.get('parent') is not None and d['parent']>=0 else m
for nid in attachments:
    authored=C.inverted()@obs[nid].matrix_world@C
    assert np.max(np.abs(np.array(authored)-np.array(web_world(nid))))<1e-5,('World transform mismatch',nid)
for n in before['nodes'][:193]+before['nodes'][640:1861]:
    assert data['nodes'][n['id']]==n,('Protected room/tree/vehicle',n['id'])
details=copy.deepcopy(before['statistics']['exteriorRefinement'])
details.update(attachmentWorldTransformsVerified=86,attachmentTransformsCorrected=len(corrected),groundFinish='neutral grey cement',wallFinish='light grey and ivory mineral render',colorEncoding='sRGB byte samples, decoded only when sampled')
result=save('exterior32',details)
