# 本地房间网页与 Cloudflare 访问

首次运行会自动准备缺少的 Node.js 22+ 和 cloudflared；官方下载地址与校验值在 `runtime-versions.json`，便携工具放在根目录 `.runtime/`。无需提前安装 Blender 或 make。可提前执行 `init-room.ps1`，更多命令见 [项目 README](../README.md)。

- 双击 BeiPiao 目录下的 `启动房间.cmd`：打开一个 PowerShell 窗口，启动本地网页和 Cloudflare。默认浏览器始终打开本机地址，窗口会另外显示经过验证的公开链接。这里的 `Start-Room.cmd` 也是同一个启动入口。
- `current-link.txt`：公开页面验证成功时，第一行是本次公开网址；验证失败时会写明本机地址、候选地址和失败原因。
- 电脑本地访问：http://127.0.0.1:48173
- 停止：直接关闭这个 PowerShell 窗口，或按 `Ctrl+C`。网页服务和 Cloudflare 都会立即结束，不需要结束脚本。
- 重复双击不会重复启动服务；会显示原窗口的当前状态，并再次用浏览器打开本机地址。

电脑必须开机、保持联网，且不能休眠。网页在本机运行，只公开 `room-site/dist` 内的网页成品，不公开工程目录。没有设置开机自启。

这是 Cloudflare 临时中转，每次重新建立中转可能获得不同网址。若日后需要固定网址，可改用自己的域名和 Cloudflare 账户创建固定 Tunnel。

网页更新后刷新即可；重启中转后请重新复制 `current-link.txt` 中的网址。

启动器不会仅凭 Cloudflare 显示“连接已注册”就宣告成功。它还会通过 HTTPS 获取公开首页，并核对房间页面标记；短暂传播期间会重试，超时后保留本机服务并把公开地址标记为“未验证”。详细日志在 `server.err.log`、`tunnel.err.log` 和 `public-check.log`。

启动检查使用首页中固定的 `<!-- beipiao-room-app:v1 -->` 应用标记，本机与公网检查共用同一规则，不依赖首页元素、属性或脚本文件名。更换 UI 时请保留该标记。2026-09-17 已修复 B 方案首页被旧检查规则误判为未启动的问题；控制台改用 PowerShell 原生 Unicode 输出，不强制切换代码页。

对应回归脚本为 `../tests/test-start-room.ps1`，在独立测试端口验证 Windows PowerShell 5 启动、新版首页及资源响应、拒绝无关页面、重复启动和关闭父进程后的子进程回收。默认跳过公网，不会创建 Cloudflare 链接；只有显式加 `-WithTunnel` 才测试中转。历史备份仅保存在作者本机，不随仓库提供。

本次本地与公网流程均实测通过。公网验证使用公共 DNS 地址进行独立 HTTPS 内容检查（`verified-direct`）；当时系统 DNS 尚不能正常解析新临时域名，因此不代表所有设备、网络都能立即通过默认 DNS 访问。测试退出后已确认测试用网页服务和 Cloudflare 均停止，没有保留测试隧道。

若窗口提示“公网隧道已验证，但系统 DNS 无法解析”，说明公开页面本身可用，而当前电脑所用 DNS 没有返回该临时域名。启动器只会为验证请求临时查询公共 DNS，不会修改 Windows 的 DNS、代理、证书、hosts 或防火墙设置。本机继续使用 `http://127.0.0.1:48173`；手机可切换移动网络后再试公开链接。若提示常规 HTTPS 路径失败，检查现有代理工具中 `trycloudflare.com` 的规则。

进程生命周期由 Windows Job Object 管理：只包含本次启动的网页服务与 Cloudflare，不包含浏览器。即使直接关闭窗口或强制结束启动进程，两个服务也会退出。强制关闭时 `runtime.json`、`current-link.txt` 可能保留上次信息，下次启动会校验进程身份并更新；旧链接不会继续工作。
