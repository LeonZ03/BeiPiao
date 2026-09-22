# Courtyard43 精修协作约定

用户已确认 `whitebox06`（Git `cb6fe56`）布局。唯一结构输入为 `history/inputs/approved-layout.json`。新完整源为 `assets/full-room/Courtyard43-interior.blend`，与白模源分离。精修期间不覆盖已发布白模；主智能体最终集中导出并接入网站。

## 组件与坐标

- `architecture`：墙地顶、踢脚、阳台、隔断/暖气罩、外窗、房门/门锁、开关、顶灯和灰窗帘。源 `assets/architecture/Courtyard43-architecture.blend`。
- `furniture`：床架/床头、床垫/枕被、书桌、单把桌前椅、衣柜柜体/柜门。源 `assets/furniture/Courtyard43-furniture.blend`。
- `props`：主智能体负责电脑、鼠标、可确认杂物、墙上帽子和低细节有证据的窗外关系。
- 所有持久建模、材质及导出经官方 Blender Lab MCP，后台进程各自打开文件；不能写其他组件或永旺家园。
- 米制；网页 `(x,y,z)` 映射 Blender `(x,-z,y)`。不得改变已确认大物件位置与房间边界。适当布料垂落、结构厚度和小物摆放可在该包围体内细化。
- 根集合 `C43_Architecture` / `C43_Furniture` / `C43_Props`；稳定对象前缀 `C43_`，对象命名使用英文，避免对全部物件强行合并。
- 追加到主工程时对象、材质、网格及可写贴图独立，不链接回旧房间。源材质、许可、复制方式记录到各组件说明。

## 材质与导出元数据

使用 Principled BSDF。PBR 图像节点直接连接对应颜色/粗糙度/金属度，法线经 Normal Map、凹凸经 Bump；复杂程序纹理需由 MCP 生成/烘焙为图像。图像用相对路径并保存到组件 `textures/`。基础色 sRGB；粗糙度/法线/高度为 Non-Color。不要烘死场景阴影。

对象自定义属性 `web_tags` 是 JSON 字符串，允许 `ceilings`、`cutaway`、`noCollision`、`curtainPanels`、`glass`、`lightFixture`、`switches` 等布尔标签。`noCollision` 只用于小装饰或柔帘，不能让实体墙、柜和门失去碰撞。集合/空对象的父子关系必须保留。

材质可用 `web_props` JSON 字符串覆写合法 Three.js PBR 参数；`web_userData` JSON 字符串保存布料/表面类别。不要依赖特定导出编号。玻璃默认透明、关闭 depthWrite、不投实心阴影。

## 可动件契约

枢轴 Empty 自定义 `c43_interaction` 为 JSON：`id`（稳定唯一）、`kind`（`hinge`/`curtain`/`switch`/`lock`）、`axis`（网页轴 `x/y/z`）、`openAngle`（弧度，仅铰链）、`audio`（如 `wardrobe`/`curtain`/`switch`/`lock`）。物件通过该枢轴下可见网格拾取，不能放巨大透明点击板。

窗帘使用 `Basis` 闭合与 `Open` 收拢形态键；保持厚度、顶部固定点和下摆连续性。挂环/轨道与帘顶连接；开合不能穿柜/罩体。形态键最好使用无改变拓扑的修改器或直接有厚度网格。布料风动固定点范围在组件说明中提供，网页根据新房间边界校准，绝不套用永旺家园节点名。

柜门独立枢轴，双门原位开合；柜内只是合理补全，不编造不可确认物件。房门/反锁以参考可见结构为准。无厨卫证据，不添加花洒和水龙头。

## 集成与验收

主智能体负责 `scripts/assemble-interior.py`、`scripts/export-interior.py`、完整源及最终 `dist/assets/rooms/Courtyard43/interior/` 导出。保留上一级已发布白模包作为结构检查点。组件作者交付脚本、源、贴图、来源/差异与几何检查结果。不得自行提交、推送、更新总 README/HISTORY 或启动浏览器；由主智能体统一集成和验收。网页最终 revision 初始为 `courtyard43-interior01`，须支持原 `blender-room-pack-1` 的 PBR、父子关系、UV/morph 和 refs。
