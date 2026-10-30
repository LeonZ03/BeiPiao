"""correction51b -> correction51c: final reference front-aspect calibration.

Official Blender Lab MCP. Match small Safeguard and LUX widths to their supplied
front photographs, and fit LUX collar/spout to the wider oval bottle.
"""
from pathlib import Path
import ast,bpy,bmesh,copy
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='correction51b'
tree=ast.parse((HERE/'refine-correction51.py').read_text('utf8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in ('export_fit','finish')],type_ignores=[]),'fit51','exec'))
for nid,factor in [(1529,.063/.057),(1531,.063/.057),(2040,.063/.057),(1530,.090/.074),(2041,.090/.074),(1533,.052/.044)]:
    o=obs[nid];o.data=o.data.copy()
    for v in o.data.vertices:v.co.x*=factor
    finish(o)
o=obs[1532];o.data=o.data.copy()
for v in o.data.vertices:v.co.x*=1.7;v.co.y*=1.7
finish(o)
result=save('correction51c',{'parent':'correction51b','reason':'Photo front aspect: Safeguard about 2.76:1 overall, LUX body about 2.17:1; widen pump collar to fit the molded shoulder','dimensions':'front ratios calibrated, absolute dimensions/depth remain estimates'})
