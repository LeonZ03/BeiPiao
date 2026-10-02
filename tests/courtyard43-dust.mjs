import assert from 'node:assert/strict';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import { createCourtyardDust, courtyardDustShouldRun } from '../room-site/dist/courtyard43-dust.js';

const scene = new THREE.Scene();
const anchor = new THREE.Vector3(.24, 1.3, .08);
const dust = createCourtyardDust(THREE, scene, anchor);
assert.equal(dust.count, 128, 'Indoor motes stay sparse');
assert.equal(scene.children.length, 1);
const points = scene.children[0];
assert.equal(points.name, 'C43_Indoor_Dust');
assert.equal(points.visible, false);
assert.equal(points.material.depthTest, true, 'Opaque furniture and walls occlude indoor motes');
assert.equal(points.material.depthWrite, false, 'Motes do not write depth');
assert.equal(points.material.blending, THREE.NormalBlending, 'Motes use restrained alpha blending');
assert.equal(points.geometry.getAttribute('position').count, 128);
const position = points.geometry.getAttribute('position');
const positionArray = position.array;
const initial = positionArray.slice();
for (let i = 0; i < position.count; i++) {
  assert.ok(position.getX(i) >= -1.82 && position.getX(i) <= 1.28);
  assert.ok(position.getY(i) >= .84 && position.getY(i) <= 2.38);
  assert.ok(position.getZ(i) >= .30 && position.getZ(i) <= 2.5, 'Motes stay within room air volume');
}
assert.ok(courtyardDustShouldRun({ active: true, overview: false, reducedMotion: false, cameraPosition: { z: .7 }, forward: { z: -.9 } }));
for (const blocked of [
  { active: false, overview: false, reducedMotion: false, cameraPosition: { z: .7 }, forward: { z: -.9 } },
  { active: true, overview: true, reducedMotion: false, cameraPosition: { z: .7 }, forward: { z: -.9 } },
  { active: true, overview: false, reducedMotion: true, cameraPosition: { z: .7 }, forward: { z: -.9 } },
  { active: true, overview: false, reducedMotion: false, cameraPosition: { z: 3.1 }, forward: { z: -.9 } },
  { active: true, overview: false, reducedMotion: false, cameraPosition: { z: -.5 }, forward: { z: .1 } }
]) assert.equal(courtyardDustShouldRun(blocked), false);

dust.setEnabled(true);
assert.equal(dust.active, true);
assert.equal(points.visible, true);
assert.equal(dust.update(.05, 1.25, .5), true);
assert.equal(dust.elapsed, .05);
assert.equal(points.material.uniforms.uPixelRatio.value, 1.25);
assert.equal(points.material.uniforms.uCurtainOpen.value, .5);
assert.equal(position.array, positionArray, 'GPU animation retains the original geometry buffer');
assert.deepEqual(position.array, initial, 'Animation does not rewrite positions on the CPU');
dust.setEnabled(false);
assert.equal(dust.active, false);
assert.equal(dust.update(.05), false);
dust.dispose();
assert.equal(scene.children.length, 0);
assert.equal(dust.update(.05), false);
console.log('Courtyard43 indoor dust bounds, alpha/depth behavior, GPU animation, gating, and disposal passed.');
