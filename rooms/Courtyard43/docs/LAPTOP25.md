# 灵越 14 笔记本：laptop25 / inspiron41

父提交 `71742e8`；43号院从 `courtyard43-props24` 更新为 `courtyard43-laptop25`，永旺从 `laptop40` 更新为 `inspiron41`。只替换两房笔记本及为其重接的短接头/输出线，房间布局、灯光、调色、雪尘和其他物件保持。

## 参考与不确定性

用户确认 2023 年购买戴尔灵越14。房间照片可确认银色闭合外壳，不能识别准确型号。当前以 **Inspiron 14 5430 银色、上出音扬声器版本** 为候选，不声称用户实物已经确认为5430，也不宣称测量级1:1。

- [戴尔官方尺寸](https://www.dell.com/support/manuals/en-au/inspiron-14-5430-laptop/inspiron-14-5430-setup-and-specifications/dimensions-and-weight?guid=guid-fd63de7b-017e-47f6-bf15-8a816ca0a3c7&lang=en-us)：314 × 226.6 mm；上出音版本前15.74 / 后17.67 mm。模型合盖最大厚度约17.65 mm，底部局部截面由照片估计。
- [官方显示屏规格](https://www.dell.com/support/manuals/en-na/inspiron-14-5430-laptop/inspiron-14-5430-setup-and-specifications/display?guid=guid-5579fc11-9b22-44fa-ba0d-ae67ba34e9f8&lang=en-us)：可视区301.59 × 188.50 mm，16:10。
- [官方触控板规格](https://www.dell.com/support/manuals/en-au/inspiron-14-5430-laptop/inspiron-14-5430-setup-and-specifications/touchpad?guid=guid-b0f011d5-f758-47d8-8f6d-0afe7346643b&lang=en-us)：115 × 80 mm。
- [产品多角度实拍](https://www.dellonline.co.za/products/dell-inspiron-5430-14-inch-core-i5-1335u-8gb-ram-512gb-ssd-win-11-home-laptop-172128)：键位、机壳、接口与转轴参考。参考图片仅保存在忽略的references中，不发布厂商照片。

接口位置、摄像头、标志尺寸、成型截面及键帽深度为图片估计；未添加不可辨识的底部铭牌、序列号、系统桌面或硬件贴纸。屏幕保持熄灭，仅机械开合。

## 实现

通过官方 Blender Lab MCP 从现有完整源增量制作，保留根节点和盖轴的交互语义。重建圆角银色上盖、收薄下壳、独立黑色边框、六排不同宽度键帽与字符、大触控板、双铰链、摄像头遮挡片、两侧细密扬声器孔阵、侧面凹入接口与圆形DELL标志。按材质和运动父节点合并为12个主要网格，避免每颗键帽单独绘制。

永旺保留原摆放和默认打开；43号院独立复制网格、材质，保留原摆放和默认合上。插头随新机壳宽度重新连接；两房电源/USB用途分别保留。修正布尔接口后的源材质绑定，确保完整源与网页材质一致。

可重复脚本：`rooms/yongwang-jiayuan/scripts/refine-inspiron41.py` 和 `rooms/Courtyard43/scripts/refine-laptop25.py`；必须从各自父revision经官方MCP执行。主工程保存最终微调结果，禁止用旧完整生成器覆盖。

## 定向验收

两房网页检查闭合、打开、盖轴连续运动、机壳轮廓及接头；模型检查21个开合状态、合盖与键帽间隙、实际宽度、有限属性/索引、贴图存在及gzip一致性。运行 `tests/laptop-props.mjs`、相关JS语法检查和Pages打包检查，不运行无关整房回归。43号院549个非目标源对象摘要保持。手机尺寸检查为浏览器视口模拟，非实体手机硬件测试。

本轮未使用子智能体。
