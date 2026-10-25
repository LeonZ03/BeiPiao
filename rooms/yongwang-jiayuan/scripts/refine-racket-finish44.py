"""props44 -> props44a. Photo colour and graphite/cyan finish after web review."""
from pathlib import Path
import bpy,copy,math
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props44'
for text,color in [('Radical orange',[1,.50,.025]),('orange polyester strings',[.98,.45,.035]),('Clash graphite grey',[.43,.47,.49])]:
    old=next(i for i,m in mats.items() if text in m.name)
    new=material('Racket44a '+text,old,color,metadata={'exteriorSurface':False,'revision':'props44a'})
    for node in data['nodes']:
        if node.get('material')==old:set_material(node['id'],new)
cyan=next(i for i,m in mats.items() if 'Radical cyan' in m.name)
verts=[];faces=[]
# Short cyan frame accents and thin stripe along the left throat, per photograph.
for side in [-1,1]:
    a=side*2.28
    for k in range(6):
        a0=a+k*.011;a1=a+(k+1)*.011;start=len(verts)
        for ang,rr in [(a0,-.007),(a0,.007),(a1,.007),(a1,-.007)]:
            verts.append(((.129+rr)*math.sin(ang),.497+(.176+rr)*math.cos(ang),.0118))
        faces.append(tuple(start+j for j in range(4)))
# Four-point stripe stays within the molded branch's front face.
start=len(verts);verts.extend([(-.018,.202,.0110),(-.020,.202,.0110),(-.061,.322,.0110),(-.059,.322,.0110)]);faces.append(tuple(start+j for j in range(4)))
o=attach(mesh('Radical44a cyan paint',verts,faces),'Radical44a cyan paint',cyan,811);export(o)
result=save('props44a',{**copy.deepcopy(before['statistics'].get('exteriorRefinement',{})),'finish44a':'Web review: orange strings and frame, graphite grey, photo cyan accents'})
