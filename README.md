# 北漂 · 居住记录

把在北京住过的出租屋，留成可以重新走进去的记忆。

这是一个个人房间档案：用照片和视频整理空间，在 Blender 中建模，再放进浏览器里自由探索。首页沿居住顺序展开，目前可以进入 **永旺家园**，其他房间保留为“待录入”。

![北漂居住记录首页](generated-assets/ui-concepts/B-cinematic-timeline.png)

*首页设计参考。进入房间后是可交互的实时三维场景，不是这张静态图片。模型依据照片比例制作，未做实测扫描。*

## 快速开始

推荐 **Windows 10 / 11，64 位**，使用较新的 Edge 或 Chrome，并开启浏览器图形加速。

```powershell
git clone https://github.com/LeonZ03/BeiPiao.git
cd BeiPiao
```

双击根目录的 **`启动房间.cmd`**。

1. 弹出 PowerShell 窗口，自动检查 Node.js 和 Cloudflare。缺少的工具从官方源下载到项目的 `.runtime/`，核对 SHA-256 后使用，无需管理员权限。
2. 浏览器自动打开本地网页：**http://127.0.0.1:48173/**。
3. 窗口另外显示通过页面验证的 **`https://….trycloudflare.com`** 临时公开链接，可以发给手机或其他电脑访问。
4. **关闭这个 PowerShell 窗口即可停止网页服务和隧道**，也可以按 `Ctrl+C`。浏览器不会被关闭。

文件名是 `.cmd`，不是 `.md`；后者是说明文档。请先完整解压或 clone 仓库，不要在 ZIP 压缩包里直接双击。模型和运行素材均在仓库中，不需要 Git LFS、Blender、Python、npm 安装或编译才能看房。

首次下载工具需要能访问 [Node.js](https://nodejs.org/) 和 [Cloudflare 的官方 GitHub 发布页](https://github.com/cloudflare/cloudflared/releases)。已安装 Node.js 22+ 和 cloudflared 时优先使用现成工具；也可以先执行可选初始化：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/init-room.ps1
# 已装 make 的 Windows 用户也可以：make init
```

初始化不创建公网链接。Cloudflare 下载或连接失败不会关闭已经启动的本地网页。只想本地运行、完全不创建隧道时：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/start-room.ps1 -SkipTunnel
```

## 怎么看房

| 操作 | 方式 |
| --- | --- |
| 进入房间 | 首页点击“进入房间”，首次加载显示进度 |
| 环顾 | 鼠标或手指拖动画面；桌面双击画面可锁定鼠标，Esc 释放 |
| 移动 | WASD / 方向键；手机左下方向键 |
| 升降 | Shift 上升、Ctrl 下降；手机右下竖排升降键 |
| 查看整体 | 房间内切换“空间总览”，拖动旋转、滚轮缩放 |
| 回到初始视点 | 点击坐标形状的复位按钮 |
| 沉浸看房 | 右上角按钮 / H，收起界面；手机保留移动键 |
| 操作物品 | 点击窗帘、墙上开关、水龙头、花洒或反锁旋钮，再点可切回 |

手机支持横竖屏。实际帧率由访问设备的 GPU、分辨率和浏览器决定；本地服务和 Cloudflare 只负责传送文件，三维画面在访问者自己的设备上渲染。

## 常用命令

以下命令在仓库根目录执行；`make` 只是可选快捷方式。

| 用途 | PowerShell 命令 | 可选快捷命令 |
| --- | --- | --- |
| 准备运行工具 | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/init-room.ps1` | `make init` |
| 本地 + 临时公开链接 | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File local-access/start-room.ps1` | `make start` |
| 仅本地 | 上一条末尾加 `-SkipTunnel` | `make local` |
| 基础回归检查 | `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/check.ps1` | `make check` |

启动器还支持 `-Port 49273`（换端口）和 `-NoBrowser`（不自动打开浏览器）。重复双击同一端口不会再启动一套服务。macOS / Linux 可以安装 Node.js 22+ 后运行 `node local-access/serve-room.mjs`；双击入口、自动初始化和窗口关闭清理仅针对 Windows。

开发者可额外运行 CPU 场景回归；普通看房不需要这些开发依赖：

```powershell
npm ci
npm run test:scene
# 显式测试公网连接，会临时公开同一房间，结束后关闭测试隧道：
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests/test-start-room.ps1 -WithTunnel
```

## 公开链接与常见问题

- **本地网址只能在启动电脑上访问。** 手机需要用 PowerShell 显示的公开链接。
- **临时链接不是永久部署。** 电脑必须开机、联网、不休眠，窗口必须保持打开；重启后网址通常改变。[Cloudflare Quick Tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/) 不需要账号或自有域名，但没有可用性保证，不适合承诺长期稳定访问。
- **不是所有网络都能稳定打开 `trycloudflare.com`。** 是否需要 VPN 取决于访问者的网络环境，不能保证国内直连。启动器会验证 HTTPS 返回的确实是房间首页；验证失败会保留本地服务并标出原因，不会把“拿到了 URL”等同于“已经可访问”。
- 公开链接可被知道地址的人访问，当前没有登录限制；服务只提供 `room-site/dist/`，不会公开 `.blend`、日志或整个工程目录。
- 网址与诊断保存在 `local-access/current-link.txt`、`server.err.log`、`tunnel.err.log` 和 `public-check.log`。换端口时文件名带端口后缀。这些文件不提交 Git。
- 若报端口占用，关闭原来启动的窗口，或使用 `-Port` 换一个端口。若下载失败，可以手动安装 Node.js 22+、cloudflared 后重试；不需要修改系统 DNS 或关闭证书验证。
- 改完网页刷新即可；遇到旧缓存可用 `Ctrl+F5`。不要直接双击 `index.html`，浏览器模块和模型需要 HTTP 服务。

## 工程结构

```text
启动房间.cmd               Windows 双击启动入口
local-access/              初始化、本地静态服务、Cloudflare 和进程清理
room-site/dist/            自包含网页源码、Three.js、贴图和可运行模型包
room-site/tools/           Blender 建模与精修脚本，包含有父版本约束的历史脚本
generated-assets/          完整 .blend、独立资产源、材质、UI 定稿
tools/                     Blender Lab 官方 MCP 客户端及可选建模依赖
tests/                     资源完整性、路由/全屏、场景和启动器回归
AGENTS.md                  AI 建模与维护规范：已确认约束、工作流、踩坑和验收
```

这里的 `dist/` 是直接维护的可运行网站，**必须提交**，不要按一般前端项目习惯将其忽略。权威 Blender 工程是 `generated-assets/full-room/永旺家园-完整场景.blend`；网页使用同目录体系导出的 `scene.json`、`geometry.bin` 和压缩版本。Git 中保留实际模型文件，不依赖作者电脑上的路径。

原始私人参考目录 `Ref/`、过程报告 `analysis/`、历史备份 `backups/`、旧部署压缩包、工具安装目录和日志均不入库。网站实际使用的展示照片与纹理保留在运行资源中。

## 继续建模 / 增加房间

先读 [AGENTS.md](AGENTS.md)，再读 [建模工具说明](tools/README.md)。所有 Blender 操作使用 [Blender Lab 官方 MCP](https://projects.blender.org/lab/blender_mcp)，不是同名第三方插件。

不要重新运行历史 `build-full-room.py` 覆盖精修后的工程，也不要把全部 `refine-*` 依次执行当作初始化。当前 `.blend` 与网页包已是完成品。新房间建立独立工程和资源目录，从参考约束、结构、重点物件、材质光照到浏览器验收逐步推进。无需复制过去的整串试错补丁。

Three.js 的许可证随库保存在 `room-site/dist/vendor/LICENSE`。照片、个人场景与物品标识来自项目参考素材；本仓库暂未为原创内容指定通用开源授权，复用前请与作者确认。
