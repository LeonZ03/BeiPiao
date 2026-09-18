import assert from 'node:assert/strict';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {createSoftDaylight} from '../room-site/dist/soft-daylight.js';

globalThis.matchMedia=()=>({matches:false});
const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(62,1.6,.003,80);
scene.background=new THREE.Color('#c9d2cd');
camera.position.set(0,1.5,2);camera.lookAt(0,1,-1);camera.updateMatrixWorld();
const solid=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());solid.name='stationary';scene.add(solid);
const leaves=new THREE.Mesh(new THREE.PlaneGeometry(),new THREE.MeshStandardMaterial());leaves.name='moving';leaves.layers.enable(1);scene.add(leaves);
const glass=new THREE.Mesh(new THREE.PlaneGeometry(),new THREE.MeshStandardMaterial({transparent:true,opacity:.055,depthWrite:true}));glass.name='glass';scene.add(glass);
const sun=new THREE.DirectionalLight();sun.position.set(2.7,5.8,-8);sun.shadow.map={texture:new THREE.Texture()};scene.add(sun);
const passes=[];
const renderer={
  isWebGLRenderer:true,autoClear:true,shadowMap:{needsUpdate:true},info:{autoReset:true,reset(){}},
  getDrawingBufferSize:v=>v.set(1280,720),getClearAlpha:()=>1,getClearColor:c=>c.set(0),setClearColor(){},setRenderTarget(target){this.target=target;},
  render(s,c){if(s===scene)passes.push({names:s.children.filter(o=>o.isMesh&&o.layers.test(c.layers)).map(o=>o.name),target:this.target,clear:this.autoClear,background:s.background,shadow:this.shadowMap.needsUpdate});}
};
const breeze={objects:[leaves],movingObjects:[leaves],active:true};
const daylight=createSoftDaylight({THREE,renderer,scene,camera,sun,breeze});
daylight.render(0,false);assert.deepEqual(passes[0].names,['stationary','moving','glass']);
const originalBackground=scene.background;
daylight.animate(.1,false,true);
assert.deepEqual(passes[1].names,['stationary'],'Cache only opaque stationary objects; transparent window cannot occlude moving foliage');
assert.deepEqual(passes[2].names,['moving','glass'],'Render foliage and transparent window together, in normal material order');
assert.notEqual(passes[1].target,passes[2].target,'Static color/depth are independent from the moving image');
assert.equal(passes[2].target,passes[0].target,'Full and moving passes share the final depth texture');
assert.equal(passes[2].clear,false,'Dynamic overlay retains restored color/depth');
assert.equal(passes[2].background,null,'Background cannot erase the cached room');
assert.equal(passes[1].shadow,false);assert.equal(passes[2].shadow,false);
assert.equal(scene.background,originalBackground);assert.equal(camera.layers.mask,1);assert.equal(renderer.autoClear,true);assert.equal(renderer.shadowMap.needsUpdate,true);
const n=passes.length;daylight.animate(.2,false,true);
assert.equal(passes.length,n+1,'Idle breeze reuses the cache');
assert.deepEqual(daylight.statistics,{fullFrames:1,ambientFrames:2,cacheBuilds:1});
daylight.render(.3,false);daylight.animate(.4,false,true);
assert.equal(daylight.statistics.cacheBuilds,2,'Camera/light changes invalidate the cached static image');
daylight.resize();daylight.animate(.5,false,true);assert.equal(daylight.statistics.cacheBuilds,3);
const stopped=passes.length;breeze.active=false;daylight.animate(.6,false,false);assert.equal(passes.length,stopped,'No rendering when both dust and breeze are inactive');
console.log('PASS HDR cache: glass ordering, independent depth, stationary reuse, camera/resize invalidation, restored renderer state and pause.');
