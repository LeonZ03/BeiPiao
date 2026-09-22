# 网站运行层

`dist/` 是直接维护、可运行的网站源码和资源，**不是可删除的构建缓存**。本地服务和 Cloudflare Pages 均从这里读取，发布构建才生成根目录 `.pages-dist/`。

永旺家园建模源及脚本已移至 [rooms/yongwang-jiayuan](../rooms/yongwang-jiayuan/README.md)，完整制作经验见该目录 [HISTORY.md](../rooms/yongwang-jiayuan/HISTORY.md)。全站 UI 定稿见 [docs/ui-concepts](../docs/ui-concepts/README.md)。

新增房间遵循 [rooms/README.md](../rooms/README.md)，为新房间建立独立资源目录和加载映射，不覆盖当前 `dist/assets/full-room/`。运行方法见根目录 [README.md](../README.md)。
