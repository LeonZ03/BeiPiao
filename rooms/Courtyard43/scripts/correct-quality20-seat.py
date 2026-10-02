"""Official MCP quality20 fit correction: retain the photographed thin pad."""
import bpy
from pathlib import Path
scene=bpy.context.scene
assert scene.get('web_revision')=='courtyard43-interior20'
assert not scene.get('quality20_seat_fit')
o=bpy.data.objects['C43_Chair15_BlackSeatPad'];o.data=o.data.copy()
for j in range(41):
    for i in range(41):
        a=2*i/40-1;b=2*j/40-1
        t=max(0,(1-a*a)*(1-b*b))**.42
        o.data.vertices[j*41+i].co.z-=.008*t
o.data.update();scene['quality20_seat_fit']=True
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
result={'revision':scene['web_revision'],'correction':'8 mm crown reduction; support and binding preserved'}

