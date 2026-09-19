import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
import {createRoomBreeze} from '../room-site/dist/room-breeze.js';
import {createRenderProbe} from '../room-site/dist/render-probe.js';

const url=new URL('../room-site/dist/assets/full-room/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',url)));
const bytes=fs.readFileSync(new URL('geometry.bin',url));
const pack=parseBlenderRoom(THREE,manifest,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),manifest.textures.map(()=>new THREE.Texture()));
const nodes=new Map();pack.world.traverse(o=>nodes.set(o.userData.blenderNode,o));pack.world.updateMatrixWorld(true);
const trees=[644,649,654].map(id=>nodes.get(id));
assert.equal(trees.reduce((n,o)=>n+o.count,0),48412);
assert.equal(new Set(trees.map(o=>o.geometry)).size,3);
for(const tree of trees){
  assert.equal(tree.castShadow,false,'Retain cheap separate shadow casters');
  assert.equal(tree.geometry.index.count/3,12);
  const positions=tree.geometry.attributes.position,normal=tree.geometry.attributes.normal;
  assert.ok(positions.count<=11,'Repeated corners must share vertices before running wind on 48k leaves');
  for(let i=0;i<normal.count;i++)assert.ok(Math.abs(new THREE.Vector3().fromBufferAttribute(normal,i).length()-1)<.005);
  const index=tree.geometry.index;
  for(let i=0;i<index.count;i+=3){
    const p=[0,1,2].map(j=>new THREE.Vector3().fromBufferAttribute(positions,index.getX(i+j)));
    assert.ok(new THREE.Vector3().subVectors(p[1],p[0]).cross(new THREE.Vector3().subVectors(p[2],p[0])).length()>1e-8,'No degenerate leaf-tip triangles');
  }
  const colors=tree.instanceColor.array;
  assert.ok(Math.max(...colors.slice(0,300))-Math.min(...colors.slice(0,300))>.05,'Canopy has spatially varied reflectance');
}
const ray=new THREE.Raycaster(new THREE.Vector3(2.6,.59,-9.5),new THREE.Vector3(0,0,-1));
const wall=ray.intersectObject(nodes.get(251),false);
assert.ok(wall.length>0&&wall[0].distance>.9,'The window is a true masonry recess, not a dark tile over a solid facade');
const glazing=ray.intersectObject(nodes.get(259),false);
assert.ok(glazing.length>0&&glazing[0].distance<wall[0].distance,'Recessed glass sits in front of cavity back');
const glassMaterials=pack.materials.filter(m=>m.userData.windowReflection);
assert.equal(glassMaterials.length,3);
for(const m of pack.materials)if(m.isMeshBasicMaterial)assert.equal(m.emissive,undefined,'Unlit materials must not acquire uniforms absent from their shader');
assert.ok(glassMaterials.every(m=>m.envMap===glassMaterials[0].envMap),'All windows share their reflection map');
assert.equal(manifest.statistics.exteriorRefinement.windows,43);

// All cavity backs and sill drips must align in WORLD space. A translated
// building parent used to shift 60 exported attachments 2.8 metres off the wall.
const windowParts=manifest.nodes.filter(n=>n.userData.exteriorWindowGlass!==undefined);
assert.equal(windowParts.length,86);
const windowPairs=new Map();
for(const part of windowParts){
  const glassId=part.userData.exteriorWindowGlass,glass=nodes.get(glassId);
  const gb=new THREE.Box3().setFromObject(glass),pb=new THREE.Box3().setFromObject(nodes.get(part.id));
  const gc=gb.getCenter(new THREE.Vector3()),pc=pb.getCenter(new THREE.Vector3());
  assert.ok(Math.abs(gc.x-pc.x)<.001,`Window attachment ${part.id} must align horizontally with glazing ${glassId}`);
  if(part.userData.exteriorWindowPart==='Window cavity'){
    assert.ok(Math.abs(gc.y-pc.y)<.001&&Math.abs(gc.z-pc.z-.18)<.001,'Cavity back stays centered and behind glass');
  }else{
    assert.ok(Math.abs(pb.max.y-gb.min.y+.04)<.002&&pc.z>gc.z,'Sill sits directly below this window');
  }
  windowPairs.set(glassId,(windowPairs.get(glassId)||0)+1);
}
assert.equal(windowPairs.size,43);assert.ok([...windowPairs.values()].every(n=>n===2));
assert.ok([193,194,195].every(id=>/cement/.test(pack.materials[manifest.nodes[id].material].userData.surfaceFinish)),'All courtyard walking/road surfaces use concrete');
for(const id of [166,172,178]){
  const glass=nodes.get(id).material;
  assert.ok(glass.isMeshPhysicalMaterial&&glass.specularIntensity<=.1,'Bay glazing must not amplify local fill lights into fireflies');
  assert.equal(glass.depthWrite,false,'Clear panes must not replace the opaque sky/leaf depth used for distant sun occlusion');
}

// Exterior shading must survive the breeze material clone, without installing
// exterior fog/backlight onto curtains or other approved interior finishes.
const camera=new THREE.PerspectiveCamera();
const breeze=createRoomBreeze({THREE,world:pack.world,camera,media:()=>({matches:false})});
for(const o of trees){
  const lib=o.material.isMeshLambertMaterial?THREE.ShaderLib.lambert:THREE.ShaderLib.standard;
  const shader={uniforms:{},vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader};
  o.material.onBeforeCompile(shader);
  assert.ok(shader.vertexShader.includes('breezeLeafRotation'));
  assert.ok(shader.fragmentShader.includes('courtyardHaze')&&shader.fragmentShader.includes('leafBacklight'));
}
assert.ok(!pack.materials.slice(0,211).some(m=>m.userData.exteriorSurface),'Original interior materials stay isolated');
assert.equal(breeze.objects.length,12);

const probe=createRenderProbe(),initial=camera.rotation.clone(),result=probe.start(camera);
for(let i=1;i<=360;i++)probe.update(i*16.67,true);
const timing=await result;assert.ok(timing.samples>200);assert.ok(Math.abs(timing.medianFrameMs-16.67)<.001);
assert.ok(camera.rotation.equals(initial),'Performance probe restores the viewing angle');
const cancel=probe.start(camera);probe.update(7000,true);probe.update(7001,false);assert.equal((await cancel).cancelled,true);
console.log('PASS exterior: shared curved leaves, valid normals, true window cavities, shared reflections, isolated shading, breeze compatibility and repeatable render probe.');
