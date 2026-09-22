# 衣柜开启效果提案 v2：按内部实拍调整

- 图像：`wardrobe-open-v2.png`
- 生成方式：内置 image_gen 编辑 v1，加入用户新提供的左侧双开柜、右侧单开柜内部实拍作为结构参考。
- 状态：定稿审阅图，尚未修改 Blender 模型或网页交互。
- 已确认：左侧双开门对应一个宽柜腔，右侧单开门对应窄柜腔，右门内侧有长镜；三个门扇独立、柜侧挂球拍和帽子的板固定不动。
- 本次修正：左柜顶格加高，顶层板及其下的挂衣杆下移，补充靠下的层板和底格；右柜按实拍保留三块层板、四个储物格及较高顶格；柜内全部留空，不添加衣服、鞋子、衣架或杂物。
- 延续：v1 的房间关系、柜体外观、木纹、金属铰链与柔暖午后光线。
- 精度说明：尺寸比例根据照片估计；左柜下层板的部分范围被衣物遮挡，图中按连续层板补全。照片未提供实测尺寸，不宣称测量级复刻。后续实现仍须在原模型坐标中通过 Blender Lab 官方 MCP 校核铰链、门扇和床/窗帘的运动间距。

## 最终生成提示词

```text
Use case: precise-object-edit.
Asset type: revised wardrobe-open design approval image for the same room, version 2.
Input roles: Image 1 (wardrobe-open-v1.png) is the existing design image to EDIT and retain almost unchanged. Image 2 (df8ae500...jpg) is the authoritative NEW real photograph of the LEFT DOUBLE-DOOR compartment. Image 3 (2ff1a4b2...jpg) is the authoritative NEW real photograph of the RIGHT SINGLE-DOOR compartment with its inside mirror. The photographs override the old concept only for cabinet internal structure and fittings. Clothes and personal belongings in the photographs must NOT be copied.
Primary task: Correct the old design's interior to match the newly supplied real photographs, with every storage compartment EMPTY. Keep the same room, framing, perspective, three open white door leaves, wood-grain fixed side with its two tennis rackets and black LA cap, top helmet, floral bed, chair, bay window and beautiful restrained warm afternoon light of Image 1. Do not redesign the room or invent furniture. Keep wardrobe overall exterior size and position unchanged.
LEFT WIDE BAY, two thirds of the cabinet width:
- This is ONE continuous wide compartment behind TWO outward-opening white doors: left leaf hinged on left carcass side and middle leaf hinged at the bay's right edge, opposing each other as a double-door pair. No central post, no center partition, no center stile in this wide bay.
- In the real photo the upper storage compartment is substantially TALLER than the shallow upper cubby in Image 1. Move the full-width upper horizontal shelf down so the top compartment occupies roughly the upper THIRD of the cabinet interior height. Compare directly with Image 2, not a generic wardrobe.
- The straight silver clothes rail spans the same wide bay immediately BELOW this shelf, at the corresponding lower height. Show a small realistic clearance between rail and shelf, supported by two wall sockets.
- ADD the missing low full-width horizontal wooden shelf approximately one quarter of the internal height above the bottom board, as suggested by the visible lower shelf in Image 2. It separates the hanging section from a single low empty shoe/storage compartment underneath. All surfaces clear and empty. No garments, no coats, no shoes, no bags, no hangers.
- Show three useful zones: tall upper cubby, empty rail/hanging space, low bottom cubby. No added drawers.
RIGHT NARROW BAY, one third of the width:
- A separate single white door hinged on the far right carcass side. There are THREE horizontal interior shelves, creating FOUR empty compartments, just as Image 3.
- Do not space them evenly. The upper compartment is the tallest, approximately the top third of the interior; the next two are medium-height and the lowest has practical low storage height. Place their shelf levels from Image 3. Its top shelf is approximately aligned with the wider bay's upper shelf.
- Retain the LONG slim, frameless, gently round-cornered mirror on the INSIDE face of this rightmost single door. Its top starts around the upper quarter of the door, its bottom ends near the plinth, matching Image 3. Reflection is a physically plausible EMPTY cabinet / curtain reflection, never a duplicate doorway, duplicated clothes or reflected clutter.
Fittings and material: white matte laminate door faces and inner faces; warmer honey natural woodgrain inside and on the structural panel edges, matching the real photographs while illuminated by Image 1's softer warmth. Real board thickness, continuous front-to-back shelf surfaces, visible small nickel concealed hinges at multiple heights, small appropriate handle hardware. All doors attached, all shelves connected, no floating boards. Cabinet side with rackets remains FIXED and does NOT open. Door leaves have the same actual width when perspective is accounted for. Do not relocate hinges to a free edge. Keep open door leaves visually distinct and physically plausible with no intersections.
Maintain Image 1's single continuous landscape 3:2 image, natural architectural photorealism, soft early-afternoon warm-neutral light and gentle interior occlusion. No labels, no text, no UI, no arrows, no watermark. No new clothes, hangers, shoes or objects inside. Output the revised design image only.
```

