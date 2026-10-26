# 近窗柜门内镜面（mirror29a）

父版本 `ce9e183 / courtyard43-switch28`；官方 Blender Lab MCP 执行 `refine-mirror29.py`、`refine-mirror-clearance29a.py`。只在近窗侧 `C43_WardrobeDoorFarPivot` 下追加镜面和玻璃边，两者来源均为永旺完整源的已用成品：

- `wardrobe-right-inner-mirror-reflection`（源节点1818）
- `wardrobe-right-inner-mirror-glass-edge`（源节点1819）

原网格不拉伸，约265×1385mm、玻璃厚4mm；位置依据用户截图估计。独立复制网格与材料，不回写永旺镜子，不导入灯光或相机。原578个场景对象摘要保持。反射面采用原资产约0.4mm表面余量：初版0.04mm在小near-plane、斜视网页中出现深度冲突，实际移动检查后修正。

运行层 `mirror29b` 复用 `wardrobe.js` 的镜面安装器和递归保护；镜子随柜门转动、仍可点击柜门，关闭与总览时暂停更新。相机或交互变化更新反射，静止复用缓存。桌面256×512、粗指针设备128×256，未增加常驻全分辨率反射。43号院镜面使用零clipBias按实际表面裁剪：原正偏差在小near-plane下会放进镜子自身玻璃底面，呈现灰块。永旺的默认clipBias保持原值。

两房控制共用 `room-input.js`：WASD平面移动、←/→横移、Shift/↑上升、Fn/↓下降；按用户选择取消C备用与Ctrl下降。Fn可能由键盘固件处理而不发送事件，↓是普通键备用。手机升降保持独立逻辑，避免不同输入来源互相释放。

定向数据和交互检查见 `tests/input-mirror.mjs`、`tests/rackets-switches.mjs`、`tests/wardrobe.mjs`；实际网页检查柜门打开/关闭、移动时反射及手机视口。原有 `daylight28`、布料、布局、默认状态和声音保持。
