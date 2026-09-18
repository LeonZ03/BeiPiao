# 窗帘提花底色贴图

输出：`ivory-jacquard-albedo.png`。使用内置 imagegen，一次生成；参考用户提供的闭帘实拍。用于3D模型的底色，不含几何褶皱、投影、窗框、帘头、流苏或室内环境。

目视核对：四列五行20个交替玫瑰椭圆与郁金香矩形纹样，浅奶油底与藤蔓底纹、细织纹可见，照明均匀。交替图案主要以棋盘序列排列，列中心只有轻微自然偏差，并非明显横向错列。此为依据单张实拍推定的纹样，不声称原厂纹样逐线一致。

提示词：

```text
Use case: style-transfer, precise textile pattern extraction.
Asset type: a flat UV ALBEDO / BASE COLOR texture map for a 3D ivory sheer-jacquard curtain, portrait approximately 1024 x 1536.
Input image 1 is a material and pattern reference ONLY: the cream glowing curtain in the room photograph. Extract its fabric weave and woven motifs, not the room or lighting. The output MUST NOT be a curtain photograph or hanging curtain: it is a perfectly flat rectangular textile swatch laid out exactly facing the viewer, all pixels in one plane, uniform neutral illumination, no folds, no drape, no perspective, no highlights, no illumination gradient, no cast shadows, no wrinkles.
Material: delicate pale warm ivory/cream sheer jacquard, fine realistic linen-like woven threads visible at close range, an intricate faint white tiny curling vine/leaf floral filigree ground throughout. Gentle naturally irregular micro-thread variation only. No holes or transparent background, opaque base-color image.
Main motif layout: exactly 4 columns by 5 rows of small sparse woven medallions on an offset/staggered grid. Alternate two distinct motif types across every row and column: (A) a tall white oval medallion containing a single stylized rose bloom with a thin stem and a pair of leaves, and (B) a tall narrow pale-white rectangular medallion containing two to three stylized upright tulips on stems and leaves. These match the reference curtain's repeated rose ovals and tulip rectangles. Stagger alternate rows slightly, keep complete motifs comfortably within canvas, and leave generous blank filigree fabric space between medallions. Each medallion should occupy approximately 10–12% of image width and 10–12% of image height. Motifs are woven slightly denser white threads within the ivory cloth, pale tonal and low contrast but clearly identifiable; their edges are soft textile thread boundaries, NOT opaque printed blocks, NOT colored flowers, NOT sharp vector icons. The interior motif strokes are pale greige/ivory density changes. Preserve natural subtlety of the real fabric.
Composition: fabric fills 100% of the rectangular output. No outer border, no selvedge, no top band, no bottom band, no tabs, no curtain rail, no hem, no fringe, no frame, no background room, no UI, no text, no objects. This texture will be mapped onto already modeled 3D folds, so ABSOLUTELY NO baked-in folds or vertical shadow stripes. Surface color and thread texture only.
```
