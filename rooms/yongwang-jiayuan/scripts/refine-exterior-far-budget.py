"""exterior31e -> exterior31f. Simplify invisible far-building relief costs.
Execute through Blender Lab MCP. Actual recesses, albedo and reflections stay.
"""
from pathlib import Path
exec(compile(Path(__file__).with_name('exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).with_name('exterior-authoring.py')),'exec'))
assert data['revision']=='exterior31e'
assert bpy.context.scene.get('web_revision')=='exterior31e'
far={368,628};clones={}
for d in data['nodes']:
    if d['parent'] not in far and d['id'] not in far:continue
    if d.get('type')!='Mesh':continue
    nid=d['id'];old=d['material'];m=data['materials'][old]
    if not m['userData'].get('exteriorSurface'):continue
    if 'bumpMap' in m['textures'] or 'roughnessMap' in m['textures']:
        if old not in clones:
            textures={k:v for k,v in m['textures'].items() if k not in ('bumpMap','roughnessMap')}
            clones[old]=material(m['userData']['surfaceFinish']+' · distant finish',old,textures=textures)
        set_material(nid,clones[old])
    # Distant facades sit beyond the indoor sun-shadow frustum. Their modeled
    # cavities and vertex occlusion retain depth without a useless shadow lookup.
    d['receiveShadow']=False;obs[nid]['web_receive_shadow']=False;changed.add(nid)
details=copy.deepcopy(before['statistics']['exteriorRefinement'])
details['distantFinish']='albedo and baked occlusion; omit subpixel relief and out-of-range shadow receive'
result=save('exterior31f',details)
