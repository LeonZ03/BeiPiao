// Actual exported surfaces: door edge occlusion, ceiling contact and socket wells.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const base=new URL('../room-site/dist/assets/full-room/',import.meta.url);
const pack=JSON.parse(fs.readFileSync(new URL('scene.json',base)));
const stopIds=pack.nodes.filter(n=>n.name.startsWith('Entrance49 continuous')).map(n=>n.id);
assert.equal(stopIds.length,2);
// Unique test aliases give access to unnamed historical nodes without changing
// the saved pack, its hierarchy, geometry, material or world transforms.
pack.nodes.forEach((n,i)=>n.name='fitting-check-'+i);
const raw=fs.readFileSync(new URL('geometry.bin',base));
assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',base))),raw);
const {world}=parseBlenderRoom(THREE,pack,raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength),pack.textures.map(()=>new THREE.Texture()));
const object=id=>world.getObjectByName('fitting-check-'+id);
const bounds=id=>new THREE.Box3().setFromObject(object(id));
const ray=new THREE.Raycaster();
const cast=(origin,direction,targets)=>{
  ray.set(new THREE.Vector3(...origin),new THREE.Vector3(...direction));ray.near=0;ray.far=.5;
  return ray.intersectObjects(targets,false);
};
assert.ok(Math.abs(bounds(1479).max.y-bounds(119).min.y)<.00001,'Lamp base seats on the actual ceiling');
const leaf=bounds(1643),stop=bounds(92);
assert.ok(leaf.min.x>bounds(89).min.x,'Complete leaf is recessed in the fitted casing');
assert.ok(stop.min.x-leaf.max.x>.001&&stop.min.x-leaf.max.x<.003,'Stop clears the outer leaf face');
const doorTargets=[88,89,90,91,92,1643,...stopIds].map(object);
for(const y of [.05,.45,1.05,1.9,2.14]){
  for(const z of [(bounds(88).max.z+leaf.min.z)/2,(leaf.max.z+bounds(89).min.z)/2]){
    assert.ok(cast([1.2,y,z],[1,0,0],doorTargets).length,'Actual timber stop blocks the side gap');
  }
}
for(const z of [leaf.min.z+.01,2.5,2.8,leaf.max.z-.01]){
  assert.ok(cast([1.2,(leaf.max.y+bounds(91).min.y)/2,z],[1,0,0],doorTargets).length,'Head stop blocks the top gap');
}
const cameraOrigin=new THREE.Vector3(.93,2.05,2.67),oblique=new THREE.Raycaster();oblique.far=2;
for(const y of [2.145,2.155,2.162])for(const z of [3.1275,3.13]){
  oblique.set(cameraOrigin,new THREE.Vector3(1.405,y,z).sub(cameraOrigin).normalize());
  const hit=oblique.intersectObjects([...doorTargets,object(71)],false)[0];
  assert.ok(hit&&hit.object!==object(71),'Timber lining covers the bright plaster return in the real oblique view');
}
const socketTargets=[1051,1974,1975,1976,1977,1978,1979].map(object);
const root=object(1050);
for(let i=0;i<3;i++){
  const face=object(1974+i*2),shutter=object(1975+i*2),z=[-.06,0,.06][i];
  for(const [x,dz]of [[-.0065,0],[.0065,0],[0,0],[-.0085,.016],[.0085,.016]]){
    const p=root.localToWorld(new THREE.Vector3(x,.045,z+dz));
    const hits=cast(p.toArray(),[0,-1,0],socketTargets);
    assert.equal(hits[0]?.object,shutter,'Each real opening exposes its recessed shutter, not the old solid body');
    const depth=bounds(1974+i*2).max.y-hits[0].point.y;
    assert.ok(i<2?depth>.001&&depth<.003:depth>.006,'Safety shutter is recessed; occupied unit is depressed');
  }
  const bridge=root.localToWorld(new THREE.Vector3(.0033,.045,z));
  assert.equal(cast(bridge.toArray(),[0,-1,0],socketTargets)[0]?.object,face,'Plastic remains between the aligned slots');
}
console.log('PASS fittings: seated lamp, 14 blocked door-gap rays, 6 lined oblique rays and 15 recessed socket apertures.');
