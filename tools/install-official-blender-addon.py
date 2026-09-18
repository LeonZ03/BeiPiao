"""Install the verified Blender Lab extension using Blender's package manager."""
import bpy
import pathlib
import zipfile
import json

root = pathlib.Path(__file__).resolve().parent
source = root / 'blender-mcp-official/addon/blender_mcp_addon'
archive = root / 'blender-lab-mcp-1.0.0.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
    for file in source.rglob('*'):
        if file.is_file() and '__pycache__' not in file.parts:
            package.write(file, file.relative_to(source).as_posix())

repos = bpy.context.preferences.extensions.repos
repo = next((r for r in repos if r.module == 'user_default'), None)
if repo is None:
    bpy.ops.preferences.extension_repo_add(name='User Default', type='LOCAL')
    repo = next(r for r in repos if r.module == 'user_default')
module = 'bl_ext.' + repo.module + '.mcp'
if module not in bpy.context.preferences.addons:
    status = bpy.ops.extensions.package_install_files(
        filepath=str(archive), repo=repo.module, enable_on_install=True)
    if status != {'FINISHED'}:
        raise RuntimeError('Extension installation failed: ' + repr(status))
preferences = bpy.context.preferences.addons[module].preferences
preferences.host = '127.0.0.1'
preferences.port = 9876
preferences.use_autostart = False
bpy.ops.wm.save_userpref()
print('BLENDER_MCP_INSTALLED ' + json.dumps({
    'module': module, 'host': preferences.host, 'port': preferences.port,
    'auto_start': preferences.use_autostart,
    'online_access': bpy.app.online_access,
    'addon_directory': repo.directory,
    'version': bpy.app.version_string,
}))
