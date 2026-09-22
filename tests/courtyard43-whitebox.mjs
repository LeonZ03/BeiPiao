// Data and real-surface regressions for the independent structural review pack.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const base=new URL('../room-site/dist/assets/rooms/Courtyard43/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',base)));
assert.equal(manifest.roomId,'Courtyard43');
assert.equal(manifest.stage,'whitebox');assert.equal(manifest.structureApproved,false);
assert.match(manifest.revision,/^courtyard43-whitebox/);
assert.ok(manifest.binary.startsWith('./assets/rooms/Courtyard43/'));
const data=fs.readFileSync(new URL('geometry.bin',base));
assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',base))),data);
const buffer=data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength);
const read=d=>new ({Float32Array,Uint32Array}[d.type])(buffer,d.offset,d.length);
let triangles=0;
for(const g of manifest.geometries){
  for(const name of ['position','normal','uv']){
    const attr=g.attributes[name];assert.ok(attr);assert.equal(attr.offset%4,0);
    for(const value of read(attr))assert.ok(Number.isFinite(value));
  }
  const p=read(g.attributes.position),n=read(g.attributes.normal),index=read(g.index);
  assert.equal(p.length,n.length);assert.equal(index.length%3,0);
  for(let i=0;i<n.length;i+=3)assert.ok(Math.abs(Math.hypot(n[i],n[i+1],n[i+2])-1)<.001);
  for(const i of index)assert.ok(i<p.length/3);
  for(let i=0;i<index.length;i+=3){
    const a=new THREE.Vector3().fromArray(p,index[i]*3),b=new THREE.Vector3().fromArray(p,index[i+1]*3),c=new THREE.Vector3().fromArray(p,index[i+2]*3);
    assert.ok(b.sub(a).cross(c.sub(a)).lengthSq()>1e-16,'Degenerate triangle');
  }
  triangles+=index.length/3;
}
assert.equal(triangles,manifest.statistics.triangles);
const {world,refs}=parseBlenderRoom(THREE,manifest,buffer,[]),meshes=[];
world.traverse(o=>{if(o.isMesh&&!o.material.transparent&&!o.userData.noCollision)meshes.push(o);});
function hits(from,to){
  const start=new THREE.Vector3(...from),delta=new THREE.Vector3(...to).sub(start),distance=delta.length();
  return new THREE.Raycaster(start,delta.normalize(),0,distance).intersectObjects(meshes,false);
}
assert.equal(hits([-.45,1.5,.5],[-.45,1.5,-.6]).length,0,'Balcony passage must remain open');
assert.equal(hits([-.7,.20,1.1],[-.7,.20,2.80]).length,0,'The empty gap under the bed must remain traversable');
assert.ok(hits([-.7,.49,1.1],[-.7,.49,2.80]).length,'The mattress must block movement');
const right=(manifest.review.room.centerX??0)+manifest.review.room.width/2;
assert.ok(hits([right-.3,1.2,2.0],[right-.3,1.2,.8]).length,'Wardrobe must block movement');
assert.ok(right-.125>1.625,'Retain passage beyond the original right wall');
assert.equal(hits([1.5,1.5,1.7],[right-.125,1.5,1.7]).length,0,'The aisle must cross the original wall and stop inside the current boundary');
assert.ok(hits([right-.1,1.5,1.7],[right+.2,1.5,1.7]).length,'The new right wall must remain solid');
assert.ok(!manifest.nodes.some(n=>n.name.startsWith('spare-chair')),'User requires the entrance to have no chair');
assert.equal(hits([1.8,.45,2.4],[1.8,.45,1.55]).length,0,'The former entrance chair position must be clear');
const bounds=name=>new THREE.Box3().setFromObject(world.getObjectByName(name));
const desk=bounds('desk-top'),seat=bounds('desk-chair-seat'),back=bounds('desk-chair-back'),bed=bounds('bed-frame');
assert.ok(desk.max.x-desk.min.x>desk.max.z-desk.min.z,'Desk long edge must follow the balcony wall');
assert.ok(desk.max.x<manifest.review.balcony.openingLeft,'Desk must stay left of the balcony doorway');
assert.ok(seat.getCenter(new THREE.Vector3()).z>desk.max.z,'Chair must sit on the bed side of the desk');
assert.ok(back.getCenter(new THREE.Vector3()).z>seat.getCenter(new THREE.Vector3()).z,'Chair back must face the bed, not the passage');
assert.ok(back.max.z<bed.min.z&&seat.max.x<manifest.review.balcony.openingLeft,'Chair must clear both bed and doorway');
assert.equal(hits([-.35,.45,.8],[-.35,.45,-.5]).length,0,'Desk and chair must leave the low balcony passage open');
assert.ok(refs.ceilings.length&&refs.cutaway.length);
assert.equal(Object.keys(manifest.review.viewpoints).length,6);
const room=JSON.parse(fs.readFileSync(new URL('../rooms/Courtyard43/room.json',import.meta.url)));
// This preserved pack remains a historical review after its geometry is approved.
// A ready room must point to the separate refined source and runtime, never here.
assert.ok(['pending','ready'].includes(room.status));
if(room.status==='ready'){
  assert.equal(room.runtimeScene,'room-site/dist/assets/rooms/Courtyard43/interior/scene.json');
  assert.equal(room.sourceBlend,'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend');
  assert.equal(JSON.parse(fs.readFileSync(new URL('../rooms/Courtyard43/history/inputs/approved-layout.json',import.meta.url))).structureApproved,true);
}
assert.ok(fs.existsSync(new URL('../'+room.sourceBlend,import.meta.url)));
console.log(`PASS Courtyard43 whitebox: ${manifest.statistics.meshes} meshes, ${triangles} triangles, normals/UV/index/gzip, open passage, under-bed gap and solid obstacles.`);
