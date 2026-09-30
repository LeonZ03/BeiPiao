"""Extract private video evidence only; does not create or modify scene assets.

Requires ffmpeg and ffprobe on PATH. Run from any directory. Original frames
remain unaltered at native resolution; labels are added only to contact sheets.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOM = Path(__file__).resolve().parents[1]
REFS = ROOM / 'references'
OUT = REFS / 'exterior-corridor-review'
SOURCES = {
    'V01': ('05883f3539f35e9e073b6e2c5baf02dc.mp4', [3, 6.7, 8, 9.3, 10.3, 10.9, 11.5]),
    'V02': ('0df3940ce09ac52ea034bfdcdc10ec00.mp4', [3.8, 4.5, 6.6, 7, 7.2, 7.33, 7.8, 8.5, 9.2, 9.67, 10.2, 10.8, 11.6, 11.9, 12, 12.5]),
}
SHEETS = {
    'window-keyframes': [('V01', t) for t in [6.7, 8, 9.3, 10.3, 10.9, 11.5]],
    'corridor-keyframes': [('V02', t) for t in [7, 7.33, 9.2, 9.67, 10.8, 12]],
}


def run(*args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', *map(str, args)], check=True)


def frame_name(tag, seconds):
    return f'{tag}-{seconds:05.2f}s.png'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    sources = {}
    for tag, (filename, times) in SOURCES.items():
        source = REFS / filename
        metadata = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'quiet', '-show_streams', '-show_format', '-of', 'json', str(source)
        ], text=True))
        stream = next(s for s in metadata['streams'] if s['codec_type'] == 'video')
        sources[tag] = {'file': filename, 'sha256': hashlib.file_digest(source.open('rb'), 'sha256').hexdigest(),
                        'durationSeconds': float(metadata['format']['duration']),
                        'width': stream['width'], 'height': stream['height'], 'fps': stream['r_frame_rate']}
        for seconds in times:
            name = frame_name(tag, seconds)
            run('-ss', seconds, '-i', source, '-frames:v', 1, '-update', 1, OUT / name)
            rows.append({'file': name, 'source': tag, 'requestedTimeSeconds': seconds})
    (OUT / 'frames.json').write_text(json.dumps({'sources': sources, 'frames': rows}, indent=2), encoding='utf-8')

    # Contact sheets are previews, not modified evidence frames. Use optional
    # system font on Windows; ffmpeg's default font lookup elsewhere.
    font = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts/arial.ttf'
    font_arg = "fontfile='" + font.as_posix().replace(':', r'\:') + "':" if font.exists() else ''
    for sheet, selected in SHEETS.items():
        cards = OUT / (sheet + '-cards')
        cards.mkdir(exist_ok=True)
        for index, (tag, seconds) in enumerate(selected):
            vf = ("scale=270:480,pad=270:508:0:28:black,drawtext=" + font_arg
                  + f"text='{tag}  {seconds:.2f}s':fontsize=18:fontcolor=white:x=8:y=5")
            run('-i', OUT / frame_name(tag, seconds), '-vf', vf, '-frames:v', 1, '-update', 1, cards / f'{index:02d}.png')
        run('-framerate', 1, '-i', cards / '%02d.png', '-vf', 'tile=3x2', '-frames:v', 1, '-update', 1, OUT / (sheet + '.jpg'))
    lines = ['# 窗外与门外：私人视频关键帧', '', '原图为 540×960，无增强、补绘或裁切。时间为请求截帧时间，精度受视频帧率限制。', '',
             '[窗外精选](window-keyframes.jpg) · [门外精选](corridor-keyframes.jpg)', '']
    for tag, (filename, times) in SOURCES.items():
        lines.extend([f'## {tag} · {filename}', ''])
        lines.extend(f'- [{t:.2f} 秒]({frame_name(tag, t)})' for t in times)
        lines.append('')
    (OUT / 'README.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Saved {len(rows)} native frames and {len(SHEETS)} selected contact sheets to {OUT}')


if __name__ == '__main__':
    main()
