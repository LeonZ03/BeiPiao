import assert from 'node:assert/strict';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import { createCourtyardSnow, courtyardSnowShouldRun } from '../room-site/dist/courtyard43-snow.js';

const scene = new THREE.Scene();
const snow = createCourtyardSnow(THREE, scene, { count: 900 });
assert.equal(snow.count, 900);
assert.equal(scene.children.length, 1);
const points = scene.children[0];
assert.equal(points.name, 'C43_ZWinter_Snow');
assert.equal(points.visible, false);
assert.equal(points.material.depthTest, true, 'Snow flakes are occluded by opaque room and balcony surfaces');
assert.equal(points.material.depthWrite, false, 'Transparent flakes do not write a solid depth layer');
assert.ok(points.renderOrder < 0, 'Snow renders before clear window glazing');
const position = points.geometry.getAttribute('position');
const positionBuffer = position.array;
const initial = position.array.slice();
assert.equal(position.count, 900);
for (let i = 0; i < position.count; i++) {
  assert.ok(position.getZ(i) < -1.3, 'flakes are entirely beyond the balcony plane');
  assert.ok(position.getY(i) >= -.45 && position.getY(i) <= 6.55, 'bounded snowfall volume is depth-occluded by exterior surfaces');
}
assert.ok(courtyardSnowShouldRun({ active: true, overview: false, reducedMotion: false, cameraPosition: { z: -.72 }, forward: { z: -.9 } }));
for (const blocked of [
  { active: false, overview: false, reducedMotion: false, cameraPosition: { z: -1 }, forward: { z: -1 } },
  { active: true, overview: true, reducedMotion: false, cameraPosition: { z: -1 }, forward: { z: -1 } },
  { active: true, overview: false, reducedMotion: true, cameraPosition: { z: -1 }, forward: { z: -1 } },
  { active: true, overview: false, reducedMotion: false, cameraPosition: { z: .8 }, forward: { z: -1 }, curtainAmounts: {left:0,right:0} },
  { active: true, overview: false, reducedMotion: false, cameraPosition: { z: -1 }, forward: { z: .7 } }
]) assert.equal(courtyardSnowShouldRun(blocked), false);

assert.ok(courtyardSnowShouldRun({active:true,overview:false,reducedMotion:false,cameraPosition:{z:2.62},forward:{z:-.78},curtainAmounts:{left:1,right:0}}),'Snow remains visible from inside with either panel open');
snow.setEnabled(true);
assert.equal(snow.active, true);
assert.equal(points.visible, true);
assert.equal(snow.update(.05, 1.25), true);
assert.equal(points.material.uniforms.uTime.value, .05);
assert.equal(points.material.uniforms.uPixelRatio.value, 1.25);
assert.equal(position.array, positionBuffer, 'geometry buffer remains allocated');
assert.deepEqual(position.array, initial, 'shader animation does not rebuild or mutate particle geometry on the CPU');
snow.setEnabled(false);
assert.equal(snow.active, false);
assert.equal(snow.update(.05), false);
snow.dispose();
assert.equal(scene.children.length, 0);
assert.equal(snow.update(.05), false);
console.log('Courtyard43 snowfall lifecycle, exterior bounds, render gating, and static geometry checks passed.');
