# 房间实录音效

以下录音的原发布页均标注 [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)，可用于本项目与再分发。这些是公开素材，并非在永旺家园现场录制。

| 用途 | 原录音与作者 |
| --- | --- |
| 水龙头：连续水柱落在陶瓷表面 | [Tap running — peridactyloptrix](https://freesound.org/people/peridactyloptrix/sounds/202529/) |
| 花洒：浴室内连续喷淋 | [Shower — vmgraw](https://freesound.org/people/vmgraw/sounds/235624/) |
| 柜门：短促轻声开门 | [door open - fast, quietly, squeak — zajac27](https://freesound.org/people/zajac27/sounds/848136/) |

从原页公开的高质量 MP3 预览裁取稳定片段，去除直流偏移、滤除极低/极高频、处理循环接缝并控制峰值，输出 24 kHz 单声道 16 位 PCM WAV。完整来源、原下载 SHA-256 和裁切参数保存在 `sources.json`。

如需重新制作，在仓库根目录运行 `python room-site/tools/prepare-room-audio.py`（需 Python 和 PATH 中的 ffmpeg）。输入缓存位于忽略的 `analysis/audio-source/`。网站直接播放已提交 WAV，普通用户无需安装制作工具。

三段素材合计约 0.92 MB，仅在用户取消静音后加载；水流使用持续循环声源，开关关闭时淡出，不重新播放启停片段。柜门录音单独使用两级 1.8 kHz 低通削弱尖锐高频，首尾淡入淡出、较低音量，每次运动只播放一次、保持原音调；不循环、不随门速降调，门被阻挡或停止时立即淡出。
