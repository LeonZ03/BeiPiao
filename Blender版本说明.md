# 永旺家园 · Blender 版本

> 这是迁入 Blender 时的阶段记录。当前运行方式见 [README.md](README.md)，新电脑的可选建模环境安装见 [tools/README.md](tools/README.md)。下文的“已安装/已注册/本机备份”仅描述原开发环境，不代表 clone 后已安装这些工具，也不要求普通看房用户安装它们。

本轮保留已确认的房间结构和物品位置，将完整实体场景统一整理到 Blender 中精修，再由网页加载导出的模型。近景重点改进家具倒角、圆形零件、布料厚度、织物微纹理、陶瓷釉面与木材反光。

- **看房**：继续双击原来的 `启动房间.cmd`。当前本机服务为 http://127.0.0.1:48173/ ，刷新即可加载新版本。
- **完整 Blender 工程**：`generated-assets/full-room/永旺家园-完整场景.blend`，贴图已打包在工程中。
- **旧版备份**：`backups/room-detail17-before-all-blender.zip`，保留网页、已有 Blender 模型和启动脚本。
- **窗栏**：仅右上活动窗保留中间横杆；窗扇微微向内开，没有外露托座，避开晾衣杆。

此次不是重新测量或扫描：已认可的造型被保留，照片没有提供的尺寸和隐藏面仍按比例推定。MCP 是操作 Blender 的通道，质感提升仍来自具体建模、材质与灯光工作。

## 官方 Blender MCP

来源：[Blender Lab 官方说明](https://www.blender.org/lab/mcp-server/)。已安装官方 MCP 服务 1.0.2 与 Blender 扩展 1.0.0，来源版本固定为 `ff54e4d8f6b09502f2f466189cca0e52b4a91643`。

已经注册到 Codex，名称为 `blender`。当前任务可通过标准 MCP 客户端调用；重新打开 Codex 后可加载到其常规工具列表。后续项目规则已记录在 `AGENTS.md`。

已实际通过 MCP 打开完整房间工程：检查到 401 个倒角修改器、13 组共享实例系统、39 张打包图片，无缺失外部文件。服务提供 26 项官方工具。

为解决 Windows 中后台 Blender 继承 MCP 输入管道后启动超时的问题，`run-official-blender-mcp.py` 只在启动后台 Blender 子进程时隔离标准输入并禁用控制台窗口；官方 MCP 的工具和源代码保持原样。

使用按需后台模式，不需要提前打开 Blender，也不随 Blender 自动开放控制端口。扩展的 Auto Start 处于关闭状态。以后如果需要直接操作屏幕上的 Blender 会话，再单独启动本机连接。

MCP 的可选环境位于 `tools/blender-mcp-env`，不随 Git 提供；官方源码和虚拟环境可按工具说明重建。连接客户端保留在 `tools/`，网页运行不依赖这些本机安装目录。
