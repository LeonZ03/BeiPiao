# 球拍、柜底和普通开关（props44a）

父版本为 `props43a` / Git `053d9f2`。通过官方 Blender Lab MCP 执行 `refine-rackets-switch44.py`、`refine-racket-finish44.py`，完整源与网页包同步保存。保留球拍组824、811的原锚点、柜体和房间布局；隐藏原球拍子网格与块状挂钩823、836，不改交互引用。

## 参考与不确定性

- 用户2026-10-26提供的两张实物近照优先：Wilson 黑灰红框、橙线、浅灰绿缠绕手胶；HEAD 橙黑框、青蓝点缀、黑线、白手胶与蓝色系结。
- Wilson 为第一代 Clash 外观，2021购入；具体100/100L/100 Pro等子型号未确认，不印未确认型号或重量。长约685.8mm、16×19和24.5mm截面参考 [Wilson 2021厂商目录](https://catalogs.asbsports.com/vendors/pdfs/wilson-tennis-2021.pdf)。拍面采用100级比例作为照片估计。
- HEAD 照片可读 Graphene XT、Radical MP；按2016代MP轮廓，约685mm、98in²、16×19、20/23/21mm变截面。[HEAD 官方2017目录](https://cdn-magento2-media.head.com/wysiwyg/japan/catalogs/2017HEADtennisConsumer_Racquet_01.pdf)、[官方系列历史](https://www.head.com/de_CH/rs/stories/history-of-the-head-radical-series)。L3是握把号，不是型号，[官方握把表](https://www.head.com/en_MT/sizeguide-grip-size)。
- 厂商目录本次由搜索索引核对规格，PDF直开受大小/502限制。其余轮廓、贴印、手胶和挂钩细节根据照片估计，未声称测量级复刻。
- Wilson印字复用已审查官方字标输入 `history/inputs/wilson43/`。HEAD等可读文字按实拍排布，字形为近似；不添加不可辨认参数。

## 制作

两拍分别制作扁椭圆成型截面、连续Y形喉部、弧形桥、上部护框和线孔套；球线交错穿织，手胶为八角基体上的螺旋搭接。新弯钩位于最顶部第一根横线下方，承托间隙约0.08mm为建模约束，非实测值。重复细件按材料合并。

柜底781保持几何与位置，独立网格调整UV，材质与固定侧板773一致。两房普通开关使用独立白色PC薄方框、大翘板和细凹缝，不添加品牌；通用约86mm尺寸为估计。参考[普通单键开关厂商数据表](https://storage.googleapis.com/eezee-technical-data/v3_DLvv9T_Tfma58hgCsTV.pdf)、[公牛官方系列外观](https://www.gongniu.cn/product/switchs-series.html)。保留原点击根和转轴方向。

## 定向验收

运行 `tests/rackets-switches.mjs` 检查新几何数值、索引、法线、薄翘板运动余量、旧挂钩隐藏、柜底木纹和压缩一致性。网页查看球拍正常距离及近景、挂点、柜底和开关点击。源脚本断言非目标描述符及交互refs不变。

上述检查通过。导出清单比较确认1982个原有非目标节点与交互refs不变；22个目标网格共93548三角面，压缩模型增幅约5.4%。两房开关均在网页实际点击开关往返，球拍与第一行球线挂点、柜底木纹已近看。网页截图保存在本地忽略的 `analysis/rackets44/`，不上传私人实拍原图。
