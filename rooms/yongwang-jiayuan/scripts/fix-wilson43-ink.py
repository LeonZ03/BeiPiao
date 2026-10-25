"""props43 -> props43a: corrected SVG raster ink; official Blender MCP only."""
from pathlib import Path
import bpy,shutil,copy
HERE=Path(__file__).resolve().parent
exec(compile((HERE/'exterior-authoring.py').read_text('utf8'),str(HERE/'exterior-authoring.py'),'exec'))
assert data['revision']==bpy.context.scene.get('web_revision')=='props43'
src=HERE.parent/'history/inputs/wilson43/logo.png'
dst=SOURCE/'textures/wilson43-wordmark.png';shutil.copyfile(src,dst);shutil.copyfile(src,OUT/dst.name)
im=next(im for im in bpy.data.images if Path(bpy.path.abspath(im.filepath)).name==dst.name);im.reload()
result=save('props43a',copy.deepcopy(before['statistics']['exteriorRefinement']))
