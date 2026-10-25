import assert from 'node:assert/strict';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {createCourtyardLighting} from '../room-site/dist/courtyard43-effects.js';
let probeMeshes=0,probeDisposed=false;
class ProbeGenerator{fromScene(probe){probe.traverse(o=>{if(o.isMesh)probeMeshes++;});return{texture:new THREE.Texture(),dispose(){probeDisposed=true;}};}dispose(){}}
const lightingScene=new THREE.Scene(),lightingRenderer={shadowMap:{}},originalShadowChunk=THREE.ShaderChunk.shadowmap_pars_fragment;
const fixture=new THREE.MeshStandardMaterial();fixture.userData.lightFixture=true;
const clothSides=['left','right'].map(side=>{const m=new THREE.MeshStandardMaterial();m.emissiveIntensity=0;m.userData={blackoutCurtain:true,curtainSide:side};return m;});
const lights=createCourtyardLighting({...THREE,PMREMGenerator:ProbeGenerator},lightingScene,lightingRenderer,[fixture,...clothSides]);
THREE.ShaderChunk.shadowmap_pars_fragment=originalShadowChunk;
const lightingSources=lightingScene.children.filter(o=>o.isLight),ceiling=lightingScene.getObjectByName('C43_Ceiling_Light'),leftFill=lightingScene.getObjectByName('C43_Window_Fill_Left'),rightFill=lightingScene.getObjectByName('C43_Window_Fill_Right');
assert.equal(lightingSources.length,6,'Calibration keeps the existing light budget');
assert.equal(lightingSources.filter(o=>o.castShadow).length,2,'Only north daylight and one ceiling emitter cast shadows');
assert.ok(probeMeshes<=3,'Reflection probe has no unsupported side studio emitter');
assert.equal(ceiling.intensity,0);assert.equal(fixture.emissiveIntensity,0,'The ceiling fixture starts switched off');
assert.ok(ceiling.shadow.intensity>0&&ceiling.shadow.intensity<1,'Diffuse ceiling shadows retain occlusion at reduced contrast');
assert.ok(ceiling.shadow.radius>2,'Native point PCF has a wider softening footprint');
const closedEnvironment=lightingScene.environmentIntensity;
lights.update(.5,false,{left:1,right:0});
assert.ok(leftFill.intensity>rightFill.intensity,'Only the opened side admits stronger local daylight');
assert.equal(clothSides[0].emissiveIntensity,0);assert.equal(clothSides[1].emissiveIntensity,0,'Closed blackout cloth never emits window light');
const independentFills=[leftFill.intensity,rightFill.intensity],dayIntensity=lights.daylight.intensity;
lights.update(.5,true,{left:1,right:0});
assert.deepEqual([leftFill.intensity,rightFill.intensity],independentFills,'The ceiling switch does not alter individual window inputs');
assert.equal(lights.daylight.intensity,dayIntensity);assert.ok(ceiling.intensity>0&&fixture.emissiveIntensity>0);
assert.ok(lightingScene.environmentIntensity>closedEnvironment,'Switched light includes a modest indirect response');
lights.update(0,false);assert.equal(ceiling.intensity,0);assert.equal(fixture.emissiveIntensity,0);assert.equal(leftFill.intensity,rightFill.intensity);
lights.dispose();assert.equal(probeDisposed,true,'Lighting disposal releases its generated environment');


console.log("Courtyard43 lighting: source budget, independent panels, light switch, disposal PASS");
