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
assert.equal(hits([1.5,1.5,1.7],[2.3,1.5,1.7]).length,0,'The enlarged aisle must cross the old right wall');
assert.ok(hits([right-.1,1.5,1.7],[right+.2,1.5,1.7]).length,'The new right wall must remain solid');
assert.ok(!manifest.nodes.some(n=>n.name.startsWith('spare-chair')),'User requires the entrance to have no chair');
assert.equal(hits([1.8,.45,2.4],[1.8,.45,1.55]).length,0,'The former entrance chair position must be clear');
assert.ok(refs.ceilings.length&&refs.cutaway.length);
assert.equal(Object.keys(manifest.review.viewpoints).length,6);
const room=JSON.parse(fs.readFileSync(new URL('../rooms/Courtyard43/room.json',import.meta.url)));
assert.equal(room.status,'pending','A review must not claim final readiness');
assert.ok(fs.existsSync(new URL('../'+room.sourceBlend,import.meta.url)));
console.log(`PASS Courtyard43 whitebox: ${manifest.statistics.meshes} meshes, ${triangles} triangles, normals/UV/index/gzip, open passage, under-bed gap and solid obstacles.`);
