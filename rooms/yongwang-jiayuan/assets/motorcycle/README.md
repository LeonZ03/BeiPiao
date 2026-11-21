# 楼下 GSX250R · moto52

用户指定来源：相邻 GSX 工程的 `reconstruction_v2/model_history/GSX250R.blend`。
来源指纹、求值面数和网页预算见 [gsx52-source.json](gsx52-source.json)。源文件由用户提供，未覆盖或修改。

- `GSX250R-courtyard.blend`：经官方 Blender Lab MCP 处理的独立网页展示资产，米制，车头沿 Blender +Y；保留车身、轮胎、仪表、镜子、机械附件及原有涂装。
- `textures/gsx52-albedo.png`：源程序材质的基础色烘焙，sRGB，无灯光和阴影。
- `textures/gsx52-metalness.png`：金属度遮罩，Non-Color。
- 老的 `motorcycle.js` 保留作历史资产，本轮不作为建模来源。

处理方法：保留源薄壳体素精度，求值修改器后减少轮胎与机械细分，在最终几何上展开 UV，再烘焙原投影涂装。绝不能先把 2 mm 薄壳改成 4 mm 体素：这会让整流罩破损和丢失。源中相机、灯光、切割工具及私人参考图不进入正式展示资产。

复现：通过官方 MCP 执行 `../../scripts/prepare-gsx52.py`；`GSX52_INPUT` 指向用户提供的文件。先以 `GSX52_STAGE=freeze` 生成临时求值工程，再打开该工程以 `GSX52_STAGE=bake` 保存本目录资产。临时文件只用于这个显式制作阶段；房间接入脚本仅依赖本目录已保存的正式源与贴图。

房间接入：从 `correction51c` 完整源执行 `../../scripts/refine-motorcycle52.py`，只替换旧车的子网格，保留原停车根节点、朝向、倾斜及附近场景；源和网页三份模型包同次保存。三维外形沿用用户工程，不另行声明实测或毫米级精度。

接入脚本最后调用 `compact-motorcycle52-pack.py`，清理未被任何节点引用的历史网格载荷，并保留几何编号。所有仍使用的数组逐字节相同；位置、法线和 UV 的16位传输编码使用已有解码器，源工程仍保留浮点数据。这里的编码误差上限仅描述传输精度，不代表模型具有实测精度。
