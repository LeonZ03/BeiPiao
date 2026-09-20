"""Build compact, seamless PCM loops from public CC0 Freesound previews.
Requires ffmpeg on PATH. Inputs are cached in ignored analysis/audio-source.
Only sound assets are authored here; this does not modify Blender geometry.
"""
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import subprocess
import urllib.request
import wave

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'analysis' / 'audio-source'
OUT = ROOT / 'room-site' / 'dist' / 'assets' / 'audio'
SOURCES = {
    'faucet': ('202/202529_2737063', 'peridactyloptrix', '202529', 4, 12, .35),
    'shower': ('235/235624_4028838', 'vmgraw', '235624', 1.2, 7, .35),
    'wardrobe': ('478/478600_300738', 'brunoboselli', '478600', 3.45, 1.25, .06),
}

def build():
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise RuntimeError('Install ffmpeg and put it on PATH before authoring audio.')
    CACHE.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for name, (preview, author, sound, start, duration, overlap) in SOURCES.items():
        url = f'https://cdn.freesound.org/previews/{preview}-hq.mp3'
        source = CACHE / f'{name}.mp3'
        if not source.exists():
            urllib.request.urlretrieve(url, source)
        decoded = CACHE / f'{name}-trim.wav'
        subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                        '-ss', str(start), '-t', str(duration), '-ac', '1', '-ar', '24000',
                        '-af', 'highpass=f=75,lowpass=f=7800', str(decoded)], check=True)
        with wave.open(str(decoded)) as f:
            rate = f.getframerate()
            data = list(struct.unpack('<' + 'h' * f.getnframes(), f.readframes(f.getnframes())))
        mean = sum(data) / len(data)
        data = [v - mean for v in data]
        fade = round(overlap * rate)
        # Rotate the seam into an equal-power overlap: the end and start now
        # continue through adjacent samples, without a silence gap or attack.
        joined = data[fade:-fade] + [
            data[-fade+i] * math.cos(i/(fade-1)*math.pi/2) +
            data[i] * math.sin(i/(fade-1)*math.pi/2) for i in range(fade)]
        rms = math.sqrt(sum(v*v for v in joined) / len(joined))
        gain = min(.15 * 32767 / rms, .85 * 32767 / max(abs(v) for v in joined))
        pcm = [round(v * gain) for v in joined]
        output = OUT / f'{name}-loop.wav'
        with wave.open(str(output), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(rate)
            f.writeframes(struct.pack('<' + 'h' * len(pcm), *pcm))
        records.append({'file': output.name, 'author': author,
                        'page': f'https://freesound.org/people/{author}/sounds/{sound}/',
                        'preview': url, 'license': 'CC0-1.0',
                        'sourceSha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'trimSeconds': [start, duration], 'overlapSeconds': overlap,
                        'durationSeconds': len(pcm)/rate, 'bytes': output.stat().st_size})
    (OUT / 'sources.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(records, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    build()
