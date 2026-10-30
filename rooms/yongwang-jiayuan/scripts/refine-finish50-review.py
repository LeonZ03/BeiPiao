"""finish50 -> finish50b: actual browser and surface-ray fit corrections.

Official Blender Lab MCP only. Positions calibrated against real shelf/back
geometry; tap foot enters the curved ceramic rear rim by about 2mm.
"""
from pathlib import Path
import bpy,copy
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='finish50'
for nid in [1528,1529,1531]:
    o=obs[nid];o.location.y+=.0345;bpy.context.view_layer.update()
    data['nodes'][nid]['matrix']=flat(C.inverted()@o.matrix_local@C);changed.add(nid)
o=obs[1513];o.data=o.data.copy()
for v in o.data.vertices:
    if v.co.z<-.080:v.co.z-=.018
export(o);g=data['geometries'][data['nodes'][1513]['geometry']];g['attributes']['uv1']=copy.deepcopy(g['attributes']['uv'])
result=save('finish50b',{'parent':'finish50','reason':'browser review exposed side-bottle backboard occlusion and 16mm tap gap','sideBottleZ':3.0305,'tapBottomY':.864,'geometry':'curved ceramic surface at Y=.86643 under actual tap centre'})
