# 同步修正帽檐

`courtyard43-finish39 → courtyard43-cap40`，来源为永旺 `correction51` 的 `cap-bill51.py`。重新构造同一连续实体帽檐及六条细缝线，修正旧反算变形造成的侧根折角。只修改七个目标网格，673个其他对象摘要不变；帽冠、LA标识、材质、挂点、家具、风动、色调和交互均保留。

官方Blender Lab MCP保存完整源并同次导出。三角面677,496，比finish39少1,104；缓存版本cap40，风动实现仍finish39。源码 `scripts/refine-cap40.py`，复用独立网格，不回写永旺来源。

网页hats机位确认LA标识、连续帽檐与原挂点；本轮不改风动和色彩。
