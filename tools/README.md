# 建模工具（看房不需要安装）

网页运行只需要 Node.js；需要修改三维资产时才准备本目录的工具。所有建模、场景检查、材质编辑、渲染和导出均走 **Blender Lab 官方 MCP**。

## 准备

1. 安装 Blender（本工程使用 Blender 5.2 系列制作）和 Python 3.10+，确保已有 Git。
2. 在仓库根目录执行：

```powershell
python -m venv tools/blender-mcp-env
tools/blender-mcp-env/Scripts/python.exe -m pip install -r tools/requirements-blender.txt
$env:BLENDER_PATH = '你的 Blender 安装目录\blender.exe'
tools/blender-mcp-env/Scripts/python.exe tools/call-blender-mcp.py --list
```

依赖锁定到 `https://projects.blender.org/lab/blender_mcp` 的已知 commit。网络必须可访问该官方仓库。不要用名称相似的社区包替代。`BLENDER_PATH` 只在当前终端设置；客户端也会检查 PATH 和标准安装位置。运行依赖与第三方源码不提交 Git。

## 调用

优先使用宿主已暴露的 `blender` MCP 工具；否则 `call-blender-mcp.py` 使用标准 MCP STDIO 协议连接同一官方实现。先 `--list` 查看当前参数，不要猜字段名称。将 JSON 参数写入 `analysis/` 后：

```powershell
tools/blender-mcp-env/Scripts/python.exe tools/call-blender-mcp.py --tool execute_blender_code_for_cli --args-file analysis/task-args.json --output analysis/task-result.json
```

后台工具无需开启常驻 TCP 服务。`run-official-blender-mcp.py` 只修正 Windows 子进程继承输入管道和控制台的问题，实际 MCP 工具来自官方包。

使用脚本执行建模时，在 MCP 的代码中为脚本显式设置 `__file__`，并以实际仓库根目录设置 `BEIPIAO_ROOT`；不要依赖 Blender 当前目录。例如以下 **代码内容交给官方 MCP 执行**，不作为直接启动 Blender 的命令：

```python
from pathlib import Path
import os
root = Path(os.environ['BEIPIAO_ROOT'])
script = root / 'rooms/yongwang-jiayuan/scripts/your-stage.py'
exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'),
     {'__file__': str(script), '__name__': '__main__'})
```

客户端会将 `BEIPIAO_ROOT` 设为仓库根目录；如果直接调用宿主 MCP，则在代码里显式指定本次 clone 的根目录。不要复制作者旧电脑的盘符路径。

## 源工程与历史脚本

当前主工程在 `rooms/yongwang-jiayuan/assets/full-room/永旺家园-完整场景.blend`。材质源图在同级 `textures/`，浏览器最终包在 `room-site/dist/assets/full-room/`。修改前确认当前版本已有 Git 提交；修改后同步保存 `.blend`、完整模型包、运行用的 `geometry.bin.gz` 和 revision，检查真实浏览器并提交。项目不再生成备份压缩包。

`rooms/yongwang-jiayuan/scripts/build-*` 与 `refine-*` 保留了制作过程，**不是一条从头重跑的构建命令**。部分依赖特定父 revision 或本地私人参考；地砖与高达的必要阶段数据保存在该房间 `history/inputs/`。它们不能直接用于当前精修工程。不要删除版本断言后强跑。新房间遵循 `rooms/README.md`，创建自己的生成脚本，不复用一长串历史补丁。

`capture-room-for-blender.mjs` 是旧网页迁入 Blender 时的尺寸采集工具；需要 `npm ci` 的开发依赖，不是新房间建模入口。`install-official-blender-addon.py` 仅在确实需要交互扩展时使用，并需自行准备官方 `tools/blender-mcp-official/` 源码；常规后台 MCP 工作流不需要安装或启动该扩展。
