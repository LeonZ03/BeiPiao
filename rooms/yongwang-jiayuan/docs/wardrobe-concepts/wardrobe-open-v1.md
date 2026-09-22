# 衣柜开启效果提案 v1

- 图像：`wardrobe-open-v1.png`
- 生成方式：内置 image_gen，基于项目现有衣柜实拍、窗边实拍及已认可的暖色氛围图。
- 状态：供用户审阅的设计图，尚未修改 Blender 模型或网页交互。
- 外部：保留三扇白色平开门、木纹固定侧板、球拍、帽子和顶部头盔。
- 内部提案：左侧双门挂衣区（顶层板、挂衣杆、空下柜），右侧窄柜三块层板形成四格；暖浅木纹、可见板厚和金属铰链，右门内侧保留参考照片中的镜子；全部收纳区留空。
- 内部分隔为设计推定，非实测复刻。生成图用于确认观感；后续建模需通过 Blender Lab 官方 MCP，基于现有柜体尺寸设计铰链轴、开门限位，并验证柜门与床、窗帘、相邻门扇的运动间距，不能用图片代替碰撞验收。

## 最终生成提示词

```text
Use case: precise-object-edit.
Asset type: One high-quality wardrobe-open design approval image for the user's existing small Beijing rental-room 3D website.
Inputs: Image 1 is the authoritative wardrobe reference and object to modify (reference-closet-new.jpg). Image 2 is the authoritative room layout reference (reference-window-new.jpg). Image 3 is the approved lighting/material mood reference only (B-hero-clean.png).
Primary request: Show this SAME existing wardrobe with its three hinged white doors open, revealing a believable, completely EMPTY wooden cabinet interior. This is a proposed interior design, not a claim of measured reconstruction.
Preserve: the existing wardrobe's tall narrow proportions, three equally narrow full-height matte ivory-white flat door leaves, light warm natural wood-grain carcass and fixed left side panel, plain slim vertical handles, the TWO tennis rackets and ONE black LA cap attached to the FIXED left side panel, and the black full-face helmet resting on top. The fixed side panel with rackets must NOT become a door. The wardrobe remains in its existing position along the gray left bedroom wall beside the pink bay-window wall. Retain the warm ivory jacquard curtain at right, sparse broad natural folds, white ceiling cornice, cream floor tiles with understated joints, and a small glimpse of the floral bed in the foreground. Do not redesign the room, enlarge the wardrobe, change its number of doors, or add furniture.
Interior proposal: two bays divided by one vertical wooden partition: a wider left bay behind the first two doors (two-thirds of total width), a narrow right bay behind the third door (one-third width). Left bay: one upper storage shelf and a single brushed-metal clothes rail underneath, generous empty hanging space and plain bottom board. Right bay: three simple evenly spaced wooden shelves forming four empty storage compartments. Continuous warm light-oak laminated wood on the inside and back, restrained vertical grain, real approx 18 mm board thickness, softly eased edges, panel joinery and realistic contact shadows. No clothes, hangers, baskets, boxes, drawers or decorations inside. No integrated LED strips. Show real small nickel concealed cup hinges attaching each door to the relevant fixed side/partition; each door remains connected. The rightmost door may retain the slim inset mirror visible on the inside of the reference photo, with a quiet physically plausible room reflection.
Door mechanics: open the two doors of the wide bay outward in opposite directions about 80 degrees, and open the narrow-bay door toward the right about 85 degrees. Their free edges project into the aisle, without intersecting the bed, one another, the cabinet or the curtain; doors are not lying against walls. Choose a viewing angle that makes the empty hanging area and shelves both readable. Maintain normal slab-door thickness and proper hinges.
Composition: one continuous photorealistic interior design render, landscape 3:2, eye-level three-quarter FRONT view from slightly left of the wardrobe, looking back toward the bay window. Frame the entire cabinet from plinth to top with open doors fully legible; the wardrobe occupies most of the image, with a restrained amount of real room context on the right and the racket-bearing fixed side visible on the left. Rectilinear perspective, natural 35 mm equivalent lens, no fisheye, no collage or secondary panels.
Lighting: match image 3's comfortable early-afternoon warm-neutral diffuse light through the ivory curtain, light softly enters the empty cabinet from the window side with natural interior depth shadows, readable inside but not artificially lit. Refined physically plausible wood, satin white laminate, subtle hinges, quiet natural surface imperfections. Pleasant and lived-in, not a luxury showroom, not a cartoon, not plastic glossy.
No labels, no titles, no UI overlays, no watermark, no people. Output one final design image.
```

