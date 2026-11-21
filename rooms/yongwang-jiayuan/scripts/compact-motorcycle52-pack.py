"""Lossless delivery cleanup after moto52, executed through official Blender MCP.

Retain all node/geometry IDs. Unreferenced historical geometry gets an empty
descriptor; every live array is copied byte-for-byte into the compact binary.
The editable Blender scene and all live topology/materials remain unchanged.
"""
from pathlib import Path
from bisect import bisect_right
import gzip
import json
import os

import bpy

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'room-site/dist/assets/full-room'
manifest = json.loads((OUT / 'scene.json').read_text('utf8'))
assert manifest['revision'] == bpy.context.scene.get('web_revision') == 'moto52'
raw = (OUT / 'geometry.bin').read_bytes()
sizes = dict(Float32Array=4, Uint32Array=4, Uint16Array=2, Int16Array=2, Uint8Array=1)


def descriptors(value):
    if isinstance(value, dict):
        if value.get('type') in sizes and 'offset' in value and 'length' in value:
            yield value
        else:
            for child in value.values():
                yield from descriptors(child)
    elif isinstance(value, list):
        for child in value:
            yield from descriptors(child)


live = {node['geometry'] for node in manifest['nodes'] if 'geometry' in node}
unused = set(range(len(manifest['geometries']))) - live
for index in unused:
    geometry = manifest['geometries'][index]
    for descriptor in descriptors(geometry):
        descriptor.update(offset=0, length=0)
    geometry['groups'] = []

arrays = list(descriptors(manifest))
ranges = sorted({(a['offset'], a['offset'] + a['length'] * sizes[a['type']])
                 for a in arrays if a['length']})
merged = []
for start, end in ranges:
    if merged and start <= merged[-1][1]:
        merged[-1][1] = max(merged[-1][1], end)
    else:
        merged.append([start, end])
compact = bytearray()
for span in merged:
    while len(compact) % 4:
        compact.append(0)
    span.append(len(compact))
    compact.extend(raw[span[0]:span[1]])
starts = [span[0] for span in merged]
for descriptor in arrays:
    if not descriptor['length']:
        descriptor['offset'] = 0
        continue
    old = descriptor['offset']
    start, end, output = merged[bisect_right(starts, old) - 1]
    length = descriptor['length'] * sizes[descriptor['type']]
    assert old + length <= end
    descriptor['offset'] = output + old - start
    new = descriptor['offset']
    assert memoryview(raw)[old:old + length] == memoryview(compact)[new:new + length]

assert len(compact) < 100 * 1024 * 1024, 'GitHub single-file delivery limit'
manifest['statistics']['triangles'] = sum(g.get('index', {}).get('length', 0) // 3
                                          for g in manifest['geometries'])
original_bytes = manifest['statistics'].get('motorcycle52Delivery', {}).get('originalBytes', len(raw))
manifest['statistics']['motorcycle52Delivery'] = dict(
    unusedGeometries=len(unused), originalBytes=original_bytes, compactBytes=len(compact),
    liveArraysByteIdentical=True, stableGeometryIds=True)
for name, payload in [('geometry.bin', compact),
                      ('geometry.bin.gz', gzip.compress(compact, compresslevel=6, mtime=0)),
                      ('scene.json', json.dumps(manifest, ensure_ascii=False, separators=(',', ':')).encode('utf8'))]:
    target = OUT / name
    stage = target.with_name(name + '.stage')
    stage.write_bytes(payload)
    os.replace(stage, target)
result = manifest['statistics']['motorcycle52Delivery']
