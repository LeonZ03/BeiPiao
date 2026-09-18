import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
import {createRoomBreeze} from '../room-site/dist/room-breeze.js';
import {createCurtainController} from '../room-site/dist/curtain.js';

const root=new URL('../room-site/dist/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('assets/full-room/scene.json',root)));
const bytes=fs.readFileSync(new URL('assets/full-room/geometry.bin',root));
const pack=parseBlenderRoom(THREE,manifest,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),manifest.textures.map(()=>new THREE.Texture()));
const hash=()=>createHash('sha256').update(bytes).digest('hex'),before=hash();
const transforms=[];pack.world.traverse(o=>transforms.push([o,o.matrix.clone(),o.material,o.instanceMatrix?.version]));
const camera=new THREE.PerspectiveCamera(62,1.6,.003,80);camera.position.set(.83,1.48,1.66);camera.rotation.set(-.20,.20,0,'YXZ');
const reduced={matches:false},coarse={matches:false};
const breeze=createRoomBreeze({THREE,world:pack.world,camera,media:q=>q.includes('reduced')?reduced:coarse});
assert.equal(breeze.objects.length,12);assert.equal(breeze.state.leafInstances,48412);
const animated=new Set(breeze.objects);
for(const [object,,material] of transforms){
  if(animated.has(object)){assert.notEqual(object.material,material,'Animation must clone shared materials');assert.ok(object.layers.isEnabled(0),'Picking stays on layer 0');}
  else assert.equal(object.material,material,'Do not animate solid furnishings or preserved shadow proxies');
}
const compiled=breeze.objects.map(object=>{
  const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  object.material.onBeforeCompile(shader);
  assert.ok(shader.vertexShader.includes('breezeTime'));
  if(object.userData.curtainShapeKey){
    assert.ok(shader.fragmentShader.includes('totalEmissiveRadiance *= texture2D(map,vMapUv).rgb'),'Preserve photo-matched curtain emission');
    assert.ok(shader.vertexShader.indexOf('#include <morphtarget_vertex>')<shader.vertexShader.indexOf('float left=mix('),'Apply wind after the authored curtain morph');
  }
  return {object,shader};
});
for(let i=0;i<600;i++)breeze.update(1/60,0,true);
assert.ok(breeze.time>9.8&&breeze.time<=10.01);
assert.ok(!breeze.movingObjects.some(o=>o.userData.breezeKind==='leaf'),'Closed curtain avoids rendering concealed trees every frame');
for(const {shader}of compiled)assert.ok(shader.uniforms.breezePower.value>=0&&shader.uniforms.breezePower.value<=.86);
const openCurtain=createCurtainController(pack.refs.curtainPanels,pack.refs.curtainRings);
openCurtain(1);
for(let i=0;i<120;i++)breeze.update(1/60,1,true);
assert.equal(breeze.movingObjects.filter(o=>o.userData.breezeKind==='leaf').length,3);
for(const panel of pack.refs.curtainPanels)assert.equal(panel.morphTargetInfluences[0],1,'Wind must preserve interactive curtain shape keys');
const flowers=compiled.filter(x=>x.object.userData.breezeKind==='flower');
assert.equal(flowers.length,5);
assert.ok(flowers.every(x=>x.shader.uniforms.breezePower.value===flowers[0].shader.uniforms.breezePower.value),'All flower components use identical flow strength; no separating stems/petals');
const t=breeze.time;reduced.matches=true;assert.equal(breeze.update(.05,1,true),true);
for(let i=0;i<60;i++)breeze.update(.05,1,true);
assert.equal(breeze.time,t);assert.equal(breeze.active,false);
for(const {shader}of compiled)assert.equal(shader.uniforms.breezePower.value,0);
reduced.matches=false;breeze.update(.05,1,true);assert.ok(breeze.time>t);
const beforeOverview=breeze.time;breeze.update(.05,1,false);breeze.update(10,1,false);
assert.equal(breeze.time,beforeOverview);assert.equal(breeze.active,false);
// Resume is bounded, even if the host submits a long suspended-frame interval.
breeze.update(120,1,true);assert.ok(breeze.time-beforeOverview<=.050001);
for(const [object,matrix,,version]of transforms){
  assert.ok(object.matrix.equals(matrix),'No authored object placement is changed');
  if(object.isInstancedMesh)assert.equal(object.instanceMatrix.version,version,'No per-frame instance uploads');
}
assert.equal(hash(),before,'Blender vertex and instance buffers are unmodified');
console.log('PASS breeze: 48,412 leaves, pinned curtain morphs, coherent flower flow, static furnishings/shadows, reduced motion, pause/resume, unchanged Blender buffers.');
