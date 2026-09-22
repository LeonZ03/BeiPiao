# 房间建模资料

每个真实房间一个稳定的英文目录 ID。当前只有 [永旺家园](yongwang-jiayuan/README.md) 已接入网站；首页其余房间继续显示“待录入”。

[Courtyard43](Courtyard43/README.md) 正在结构白模阶段，保留用户指定的目录大小写，当前为 `pending`。已有独立源及网页审阅入口，尚未获用户结构确认，也未接入正式首页。原始照片和补充视频仍在本地忽略目录。

## 新增房间

1. 新建 `rooms/<room-id>/`，将 [约束模板](ROOM_TEMPLATE.md) 保存为该房间的 `README.md`。先记录参考来源、拍摄时期、朝向和尺寸依据，未知内容留空。
2. 原图和视频放 `references/`（默认忽略）；经过确认、可提交的定稿放 `docs/`，完整工程和贴图放 `assets/full-room/`，独立物件放 `assets/<asset>/`。
   建模前先盘点现有房间已认可的物件：相同物件直接复用，相似物件复制到新房间后修改，找不到合适基础才新建。在房间 README 的复用清单中记录来源文件、对象、提交/版本和差异；完整场景可能比独立资产源更新，应核对后选择。
3. 本房间脚本放 `scripts/`。新建简洁的分阶段生成链，不复制永旺家园的一长串历史补丁。所有 Blender 操作仍通过官方 MCP，遵守根目录 AGENTS.md。
4. 按永旺家园 `room.json` 的字段建立索引，状态先用 `pending`，`sourceBlend`、`runtimeScene`、`scripts`、`history` 尚不存在时用 `null`。所有路径相对仓库根目录；房间 ID 与目录名一致。
5. 导出到 `room-site/dist/assets/rooms/<room-id>/`，使用独立 revision。确认网页中实际可加载、交互及灯光正确后，再接入首页选择和加载逻辑，状态改为 `ready`。仅新建目录或改索引不会自动增加网页房间。
6. 阶段经验记入 `HISTORY.md`；可复用方法提炼进 AGENTS.md。必要输入放 `history/inputs/`，临时输出放根目录 `analysis/<room-id>/`，不要混放。

复用时通过官方 Blender MCP 导入对象及必要依赖，保留材质、贴图和交互枢轴。目标房间需要改动的数据先制作独立副本，不回写旧房间；只复制对象而仍共享可写网格或材质会连带改坏来源。导入后重新核对尺度、接触、光照和交互，不照搬原房间的灯光或节点 ID。细则见 AGENTS.md 第 4.3 节。

确有多个房间反复使用的资产，再按需提取到根目录 `shared-assets/<asset-id>/`，记录版本与使用方；该目录是后续约定，目前无需为了建库迁移现有模型。共享版本升级不应自动改变所有房间，差异变体仍由各房间单独保存。

## 现有目录

| 路径 | 作用 |
| --- | --- |
| `<room-id>/room.json` | 人和检查工具读取的资料索引，不是网页配置 |
| `<room-id>/assets/` | 可编辑模型、源纹理、原始录音等重要资料 |
| `<room-id>/scripts/` | 有版本约束的建模/精修及素材处理 |
| `<room-id>/docs/`、`HISTORY.md` | 定稿、制作经验和历史说明 |
| `<room-id>/history/inputs/` | 已审查、可提交的历史输入 |
| `<room-id>/references/`、`local-history/` | 本地私人资料与尚未提炼的历史资料，不入库 |

网站公共 UI 位于 `docs/ui-concepts/`，共用工具在根目录 `tools/`。发布只从 `room-site/dist/` 构建，不包含这里的建模源或私人资料。运行 `npm run test:structure` 可检查资料索引和关键路径。
