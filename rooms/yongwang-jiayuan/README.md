# 永旺家园

这是当前已上线房间的建模工作目录。网站入口、灯光、模型包和交互仍在仓库根目录的 `room-site/dist/`，双击根目录 `启动房间.cmd` 的方式不变。

- **当前源工程**：[完整场景](assets/full-room/永旺家园-完整场景.blend)，同级 `textures/` 保存源贴图。当前 revision 以网页 `scene.json` 为准。
- **独立物件/素材**：`assets/` 下的头盔、摩托车、高达、门饰、窗帘纹理、杯子图案及原始柜门录音，均保留。
- **建模和精修**：`scripts/`。这是有父版本约束的历史生成链，不是从头执行的安装脚本；尤其不能用 `build-full-room.py` 覆盖当前工程。
- **定稿**：`docs/wardrobe-concepts/`、`docs/summer-style/`。全站 UI 定稿另在 `../../docs/ui-concepts/`。
- **经验**：[HISTORY.md](HISTORY.md) 保留全部阶段记录；[Blender 迁移说明](docs/blender-migration.md) 是历史记录。当前规则以根目录 [AGENTS.md](../../AGENTS.md) 为准。
- **历史输入**：`history/inputs/floor19-geometry-report.json` 和 `viewer26-head-points.json` 是地砖稳定性、高达缩头步骤所需的数据，已从临时目录转入版本管理。
- **私人资料**：`references/` 保留原图/视频；`local-history/` 保留早期调查、试验脚本和有参考价值的报告，均忽略且不发布。后者是资料归档，不是版本备份；不能当作新机器可直接执行的正式脚本。

## 2026-09-22 目录迁移对照

| 原位置 | 新位置 |
| --- | --- |
| `generated-assets/`（房间素材） | 本目录 `assets/` |
| `generated-assets/ui-concepts/` | 根目录 `docs/ui-concepts/` |
| `generated-assets/wardrobe-concepts/` | 本目录 `docs/wardrobe-concepts/` |
| `room-site/tools/`、`room-site/prepare_assets.py` | 本目录 `scripts/` |
| `room-site/README.md` | 本目录 `HISTORY.md` |
| 根目录 `Blender版本说明.md` | 本目录 `docs/blender-migration.md` |
| `Ref/永旺家园/` | 本目录 `references/`（不入库） |
| `output/imagegen/warm-afternoon-style-v1.png` | 本目录 `docs/summer-style/` |
| 早期 `analysis/` 调查和试验资料 | 本目录 `local-history/`（不入库） |

目录迁移不改动房间布局、模型几何、材质或运行逻辑。源工程的外部贴图相对路径已随迁移修正；早期夏日工程依赖的五张原始光照贴图也一并保留，避免新克隆缺图。网页资源路径继续兼容既有 URL。
