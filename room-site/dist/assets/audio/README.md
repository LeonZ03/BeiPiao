# 房间实录音效

两段水声的原发布页标注 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)。柜门音频由项目所有者提供并指定用于网站，未提供原作者或许可证信息，因此不将柜门素材标注为 CC0。这些素材不是永旺家园现场录音。

| 用途 | 原录音与作者 |
| --- | --- |
| 水龙头：连续水柱落在陶瓷表面 | [Tap running — peridactyloptrix](https://freesound.org/people/peridactyloptrix/sounds/202529/) |
| 花洒：浴室内连续喷淋 | [Shower — vmgraw](https://freesound.org/people/vmgraw/sounds/235624/) |
| 柜门：打开、关闭分别播放 | 用户提供的 `cabinet-door-small-cabinet-door-opens-and-closes.mp3`，源文件保留在 `rooms/yongwang-jiayuan/assets/audio/cabinet-door-opens-and-closes.mp3` |

水声从原页公开的高质量 MP3 预览裁取稳定片段，去除直流偏移、滤除极低/极高频、处理循环接缝并控制峰值。柜门保留原声的音调及相对音量，只裁掉静音、分离动作并在裁切边缘做 6 毫秒淡入淡出：开门为原音频 0.32–1.43 秒，关门为 3.30–4.82 秒。输出为 24 kHz 单声道 16 位 PCM WAV；完整来源、SHA-256 和裁切参数保存在 `sources.json`。

如需重新制作，在仓库根目录运行 `python rooms/yongwang-jiayuan/scripts/prepare-room-audio.py`（需 Python 和 PATH 中的 ffmpeg）。输入缓存位于忽略的 `analysis/audio-source/`。网站直接播放已提交 WAV，普通用户无需安装制作工具。

四段素材合计约 1 MB，仅在用户取消静音后加载。水流持续循环，关闭时淡出。柜门按实际运动方向播放不同录音：开门时播放前半段，关门接近合拢时播放后半段，保留关门尾音；中途反向或被阻挡会停止旧动作声。没有额外的合成关门撞击声，也不循环或变调。
