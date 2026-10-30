import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
import {createCourtyardBreeze,hangerAngle} from '../room-site/dist/courtyard43-breeze.js';
import {batchCourtyardGeometry,installCourtyardCurtainTransmission} from '../room-site/dist/courtyard43-effects.js';
const base=new URL('../room-site/dist/assets/rooms/Courtyard43/interior/',import.meta.url);
const p=JSON.parse(fs.readFileSync(new URL('scene.json',base))),raw=fs.readFileSync(new URL('geometry.bin',base));
const buffer=raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength);
const {world}=parseBlenderRoom(THREE,p,buffer,p.textures.map(()=>new THREE.Texture()));
const protectedMeshes=[];world.traverse(o=>{if(o.userData.breezeCloth||o.userData.breezeHanger)protectedMeshes.push(o);});
batchCourtyardGeometry(THREE,world,protectedMeshes);
assert.equal(protectedMeshes.filter(o=>o.userData.breezeCloth).length,2);
const originals=new Map(),positions=new Map(),indices=new Map();
world.traverse(o=>{if(!o.isMesh)return;originals.set(o,o.material);positions.set(o,o.geometry.attributes.position.version);indices.set(o,o.geometry.index.version);for(const m of Array.isArray(o.material)?o.material:[o.material])installCourtyardCurtainTransmission(m);});
const camera=new THREE.PerspectiveCamera(64,1.7,.003,60);camera.position.set(.1,1.57,-.19);camera.lookAt(.1,2.095,-.76);
const reduced={matches:false},coarse={matches:false};
const wind=createCourtyardBreeze({THREE,world,camera,media:q=>q.includes('reduced')?reduced:coarse});
assert.equal(wind.state.clothMeshes,4);assert.equal(wind.state.hangers,2);
for(const o of wind.objects.filter(o=>!o.userData.breezeHanger)){
  const mats=Array.isArray(o.material)?o.material:[o.material];
  for(const m of mats){
    const shader={uniforms:{},vertexShader:'#include <common>\n#include <defaultnormal_vertex>\n#include <project_vertex>\n#include <worldpos_vertex>',fragmentShader:'#include <common>\n#include <emissivemap_fragment>'};
    m.onBeforeCompile(shader,{});
    assert.ok(shader.vertexShader.includes('transformed.z+=c38D.y'));
    if(m.userData.curtainDiffuseTransmission)assert.ok(shader.fragmentShader.includes('c43WindowTransmission'),'Keep existing transmission hook');
    assert.ok(m.customProgramCacheKey().includes('courtyard-breeze39'));
  }
}
const pivots=wind.objects.filter(o=>o.userData.breezeHanger).map(o=>o.getWorldPosition(new THREE.Vector3()));
for(let i=0;i<900;i++)wind.update(1/60,{active:true,openness:i<450?1:0});
assert.ok(wind.state.time>14&&wind.state.visibleMeshes>0);
assert.ok(wind.state.hangerAngles.some(a=>a>.001));
for(let i=0;i<2;i++)assert.ok(wind.objects.filter(o=>o.userData.breezeHanger)[i].getWorldPosition(new THREE.Vector3()).distanceTo(pivots[i])<1e-9,'Hook stays fixed');
for(let t=0;t<120;t+=.1)assert.ok(Math.abs(hangerAngle(t,1.7))<.065,'Gentle pendulum stays below 3.8 degrees');
for(const [o,v]of positions)assert.equal(o.geometry.attributes.position.version,v,'No per-frame position upload');
for(const [o,v]of indices)assert.equal(o.geometry.index.version,v,'No per-frame index upload');
const elapsed=wind.state.time;wind.update(.05,{active:false});assert.equal(wind.active,false);
assert.ok(wind.state.hangerAngles.every(a=>a<1e-7));
for(let i=0;i<100;i++)wind.update(.05,{active:false});assert.equal(wind.state.time,elapsed,'Hidden/overview pauses time');
reduced.matches=true;wind.update(.05,{active:true});assert.equal(wind.state.enabled,false);
wind.dispose();for(const o of wind.objects)assert.deepEqual(o.material,originals.get(o));
console.log('PASS: four cloth panels, two pinned hangers, shading chain, no buffer updates, pause/reduced-motion/disposal.');
