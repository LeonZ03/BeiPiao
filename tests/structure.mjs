// Validate authoring paths without opening Blender or executing historical builders.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
function existing(relative, directory = false) {
  assert.equal(typeof relative, 'string');
  assert.ok(!path.isAbsolute(relative) && !path.win32.isAbsolute(relative), `Must be repo-relative: ${relative}`);
  const full = path.resolve(root, relative);
  assert.ok(full.startsWith(root), `Path escapes repository: ${relative}`);
  const stat = fs.statSync(full);
  assert.ok(directory ? stat.isDirectory() : stat.isFile(), relative);
  return full;
}
const ids = new Set(), runtimePaths = new Set();
for (const entry of fs.readdirSync(path.join(root, 'rooms'), {withFileTypes: true})) {
  if (!entry.isDirectory()) continue;
  const prefix = `rooms/${entry.name}/`;
  const room = JSON.parse(fs.readFileSync(existing(prefix + 'room.json')));
  assert.equal(room.schemaVersion, 1);
  assert.equal(room.id, entry.name);
  // Preserve user-selected directory spelling, including Courtyard43, while
  // rejecting aliases that collide on Windows' case-insensitive filesystem.
  assert.match(room.id, /^[A-Za-z][A-Za-z0-9-]*$/);
  const canonicalId = room.id.toLowerCase();
  assert.ok(!ids.has(canonicalId)); ids.add(canonicalId);
  assert.ok(['pending', 'ready'].includes(room.status));
  existing(prefix + 'README.md');
  if (room.scripts !== null) { assert.ok(room.scripts.startsWith(prefix)); existing(room.scripts, true); }
  if (room.history !== null) { assert.ok(room.history.startsWith(prefix)); existing(room.history); }
  if (room.sourceBlend !== null) {
    assert.ok(room.sourceBlend.startsWith(prefix + 'assets/')); existing(room.sourceBlend);
  }
  if (room.runtimeScene !== null) {
    assert.ok(!runtimePaths.has(room.runtimeScene), 'Rooms cannot overwrite each other');
    runtimePaths.add(room.runtimeScene);
    const namespace = room.id === 'yongwang-jiayuan' ? 'room-site/dist/assets/full-room/' : `room-site/dist/assets/rooms/${room.id}/`;
    assert.equal(room.runtimeScene, namespace + 'scene.json');
    const scene = JSON.parse(fs.readFileSync(existing(room.runtimeScene)));
    assert.equal(scene.format, 'blender-room-pack-1');
    assert.ok(scene.revision);
  }
  if (room.status === 'ready') assert.ok(room.sourceBlend && room.runtimeScene && room.scripts && room.history);
}
// This base capture is still needed to reproduce the historical authoring chain.
const base = JSON.parse(fs.readFileSync(existing('rooms/yongwang-jiayuan/assets/full-room/source-scene.json')));
for (const texture of base.textures) existing(texture.file);
for (const name of ['floor19-geometry-report.json', 'viewer26-head-points.json'])
  JSON.parse(fs.readFileSync(existing('rooms/yongwang-jiayuan/history/inputs/' + name)));
const records = JSON.parse(fs.readFileSync(existing('room-site/dist/assets/audio/sources.json')));
for (const record of records) if (record.source) existing(record.source);
console.log(`PASS structure: ${ids.size} room(s), independent sources, portable capture textures, historical inputs and audio provenance.`);
