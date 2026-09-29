"""window38 -> handles39. Owner's close photo: pale grey/satin silver, not brown.
Official Blender Lab MCP only. Original handle mesh, transforms and refs stay fixed.
"""
from pathlib import Path
exec(compile((Path(__file__).parent/'exterior-authoring.py').read_text(encoding='utf8'),str(Path(__file__).parent/'exterior-authoring.py'),'exec'))
assert data['revision']=='window38' and bpy.context.scene['web_revision']=='window38'
mid=material('photo-pale-grey-satin-handles',data['nodes'][776]['material'],color=(.72,.73,.70),rough=.48,metalness=.25,metadata={'exteriorSurface':False,'revision':'handles39'})
for nid in [776,778,780]:
    assert data['nodes'][nid]['geometry']==426
    set_material(nid,mid)
    data['nodes'][nid]['userData']['revision']='handles39'
    obs[nid]['web_user_data']=json.dumps(data['nodes'][nid]['userData'])
data['statistics']['windowWallRefinement']['handles']='original geometry 426; photo-corrected pale grey satin finish'
result=save('handles39',copy.deepcopy(before['statistics']['exteriorRefinement']))
