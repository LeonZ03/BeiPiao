import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gunzipSync } from 'node:zlib';
import assert from 'node:assert/strict';

const root = fileURLToPath(new URL('../room-site/dist/', import.meta.url));
const scene = JSON.parse(fs.readFileSync(path.join(root, 'assets/full-room/scene.json')));
assert.equal(scene.format, 'blender-room-pack-1');
const asset = name => {
  const file = path.resolve(root, name);
  assert.ok(file.startsWith(root) && fs.statSync(file).isFile(), `Missing/invalid asset: ${name}`);
  return fs.readFileSync(file);
};
const binary = asset(scene.binary);
assert.deepEqual(gunzipSync(asset(scene.compressedBinary)), binary, 'Compressed and raw geometry differ');
for (const texture of scene.textures) asset(texture.webPath);
const types = { Float32Array, Uint32Array, Uint16Array, Int16Array, Uint8Array };
function read(descriptor) {
  const Type = types[descriptor.type];
  assert.ok(Type, `Unsupported typed array ${descriptor.type}`);
  assert.ok(descriptor.offset >= 0 && descriptor.offset + descriptor.length * Type.BYTES_PER_ELEMENT <= binary.length);
  const data = new Type(binary.buffer, binary.byteOffset + descriptor.offset, descriptor.length);
  for (const value of data) assert.ok(Number.isFinite(value), 'Non-finite geometry');
  return data;
}
for (const geometry of scene.geometries) {
  const position = geometry.attributes.position;
  for (const a of Object.values(geometry.attributes)) read(a);
  if (geometry.index) for (const i of read(geometry.index)) assert.ok(i < position.length / position.itemSize, 'Index out of bounds');
  for (const list of Object.values(geometry.morphAttributes || {})) for (const a of list) read(a);
}
const nodeIds = new Set(scene.nodes.map(n => n.id));
for (const node of scene.nodes) {
  assert.ok(node.parent === -1 || nodeIds.has(node.parent), 'Missing parent');
  assert.ok(node.matrix.every(Number.isFinite), 'Invalid transform');
  if (node.geometry !== undefined) assert.ok(scene.geometries[node.geometry]);
}
assert.ok(asset('index.html').includes('<!-- beipiao-room-app:v1 -->'));
console.log(`PASS ${scene.revision}: ${scene.nodes.length} nodes, ${scene.geometries.length} geometries, ${scene.textures.length} textures; gzip matches raw data.`);
