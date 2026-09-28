// Photo-specific geometry checks: no cup interpenetration, correct support and
// a real spoon. This complements browser close-ups; it is not visual approval.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const url=new URL('../room-site/dist/assets/full-room/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',url)));
const bytes=fs.readFileSync(new URL('geometry.bin',url));
const {world}=parseBlenderRoom(THREE,manifest,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),manifest.textures.map(()=>new THREE.Texture()));
world.updateMatrixWorld(true);
const object=name=>{const o=world.getObjectByName(name);assert.ok(o,name);return o;};
const bounds=name=>new THREE.Box3().setFromObject(object(name),true);
const lower=bounds('rolled-rim-hollow-paper-cup'),upper=bounds('second-nested-paper-cup');
assert.ok(Math.abs(lower.min.y-1.663)<1e-5,'Cup base retains its shelf contact');
assert.ok(Math.abs(upper.max.y-lower.max.y-.0065)<1e-5,'Two distinct nested rims');
const lowerNode=object('rolled-rim-hollow-paper-cup'),upperNode=object('second-nested-paper-cup');
assert.equal(lowerNode.parent,upperNode.parent,'Cups remain a single placed assembly');
// At the mouth of the lower cup, the upper cup clears its 30.4 mm inner radius.
const upperRadius=.024+(.079-.0065-.006)/.073*.007;
assert.ok(.0304-upperRadius>.00001,'Nested walls have positive radial clearance at the near-contact support');
const spoon=bounds('nested-cups-stainless-teaspoon');
assert.ok(spoon.min.y>lower.min.y && spoon.min.y<lower.max.y,'Spoon bowl is inside the cup');
assert.ok(spoon.max.y>upper.max.y+.02,'Spoon handle protrudes');
const packet=bounds('heart-print-soft-tissue-package').union(bounds('softpack-gingham-rounded-sides'));
assert.ok(Math.abs(packet.min.y-1.662)<.0001,'Softpack rests on original shelf');
assert.ok(Math.abs(packet.getSize(new THREE.Vector3()).z-.205)<.001,'Packet retains its original footprint');
const decal=bounds('photo-wall-sticker-white-contour');
assert.ok(decal.max.x<=1.40001 && decal.min.x>=1.399,'Decal lies directly against the real wall');
assert.ok(decal.getSize(new THREE.Vector3()).z<.04,'Sticker scale stays small');
assert.equal(manifest.nodes[1489].visible,false,'Old black cuboid cannot obscure the photo-matched sticker');
assert.equal(manifest.statistics.exteriorRefinement.leafCount,48209);
console.log('PASS shelf: two nested rims, wall clearance, teaspoon placement, original packet support and small wall decal.');
