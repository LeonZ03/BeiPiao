// Focused exported-asset checks: hanging rackets, cabinet plinth and 86 rockers.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const web=new URL('../room-site/dist/',import.meta.url);
function load(path){
  const dir=new URL(path,web),m=JSON.parse(fs.readFileSync(new URL('scene.json',dir))),b=fs.readFileSync(new URL('geometry.bin',dir));
  assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',dir))),b,'Same-export compressed and raw binary');
  const textures=m.textures.map(t=>{assert.ok(fs.existsSync(new URL(t.webPath,web)));return new THREE.Texture();});
  const parsed=parseBlenderRoom(THREE,m,b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),textures);
  return {m,...parsed};
}
const yw=load('assets/full-room/'),c43=load('assets/rooms/Courtyard43/interior/');
const targets=[];
for(const [prefix,parent] of [['Clash44',824],['Radical44',811]]){
  const nodes=yw.m.nodes.filter(n=>n.name.startsWith(prefix));assert.ok(nodes.length>=10);
  for(const n of nodes){assert.equal(n.parent,parent);assert.equal(n.visible,true);targets.push(yw.world.getObjectByName(n.name));}
}
for(const id of [823,836])assert.equal(yw.m.nodes[id].visible,false,'Old block hook retired');
assert.equal(yw.m.nodes[781].material,yw.m.nodes[773].material,'Visible cabinet base uses same veneer as fixed side');
if(yw.m.statistics.exteriorRefinement?.props45){
  const report=yw.m.statistics.exteriorRefinement.props45;
  assert.ok(report.frameFrontWidthM<.015,'Slim frontal frame section');
  assert.ok(report.surfacePrint.length>=6,'Visible frame prints follow their source surface');
  assert.equal(yw.m.nodes[1483].matrix[12],Math.fround(1.387),'Export must not retain the old protruding switch origin');
  const a=yw.world.getObjectByName('light-switch-rocker'),b=c43.world.getObjectByName('C43_Switch_Rocker');
  const bounds=o=>new THREE.Box3().setFromBufferAttribute(o.geometry.attributes.position).getSize(new THREE.Vector3());
  assert.ok(bounds(a).distanceTo(bounds(b))<1e-7,'Reused switch has the same geometry size');
  assert.ok(a.material.color.toArray().every((v,i)=>Math.abs(v-b.material.color.toArray()[i])<1e-7),'Reused switch base color');
  for(let id=1070;id<=1077;id++)yw.world.traverse(o=>{if(o.isMesh&&o.geometry.userData.blenderGeometry===yw.m.nodes[id].geometry)targets.push(o);});
  for(let id=1078;id<1096;id++)assert.equal(yw.m.nodes[id].visible,false,'Old disconnected tuft pieces retired');
  for(const name of ['C43_WardrobeFarMirror_Reflection','C43_WardrobeFarMirror_Edge']){
    const n=c43.m.nodes.find(n=>n.name===name);assert.ok(n);assert.equal(c43.m.nodes[n.parent].name,'C43_WardrobeDoorFarPivot');
    assert.equal(n.userData.noCollision,true);assert.equal(n.castShadow,false);targets.push(c43.world.getObjectByName(name));
  }
}
for(const root of [yw.world,c43.world]){
  const rocker=root.getObjectByName(root===yw.world?'light-switch-rocker':'C43_Switch_Rocker');assert.ok(rocker);targets.push(rocker);
  const box=new THREE.Box3().setFromBufferAttribute(rocker.geometry.attributes.position),size=box.getSize(new THREE.Vector3());
  assert.ok(size.x<.006&&size.y>.060&&size.z>.060,'Broad thin rocker, not a protruding toggle');
  for(const angle of [0,.05,.10,.13]){const q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),angle);const points=[];for(let x of [box.min.x,box.max.x])for(let y of [box.min.y,box.max.y])for(let z of [box.min.z,box.max.z])points.push(new THREE.Vector3(x,y,z).applyQuaternion(q));assert.ok(points.every(p=>Math.abs(p.x)<.007),'Rocker travel remains inside shallow housing');}
}
let triangles=0;
for(const mesh of targets){assert.ok(mesh?.isMesh);const g=mesh.geometry,n=g.attributes.position.count;for(const a of Object.values(g.attributes))for(const v of a.array)assert.ok(Number.isFinite(v));for(const i of g.index.array)assert.ok(i>=0&&i<n);triangles+=g.index.count/3;
 const ns=g.attributes.normal;for(let i=0;i<ns.count;i++){const length=Math.hypot(ns.getX(i),ns.getY(i),ns.getZ(i));assert.ok(length>.9&&length<1.1,'Finite normalized surface normals');}}
assert.ok(triangles<110000,'Rackets, switch, toothbrush and mirror remain bounded');
console.log(JSON.stringify({result:'PASS',targetMeshes:targets.length,targetTriangles:triangles,revisions:[yw.m.revision,c43.m.revision]}));
