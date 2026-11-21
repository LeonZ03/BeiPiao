// Courtyard GSX replacement: scoped geometry/material/runtime contract.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';

const base=new URL('../room-site/dist/assets/full-room/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',base)));
const metadata=JSON.parse(fs.readFileSync(new URL('../rooms/yongwang-jiayuan/assets/motorcycle/gsx52-source.json',import.meta.url)));
const bytes=fs.readFileSync(new URL('geometry.bin',base));
assert.ok(bytes.length<100*1024*1024,'Keep the tracked binary below the hosting limit');
assert.equal(manifest.statistics.motorcycle52Delivery.liveArraysByteIdentical,true);
assert.equal(manifest.statistics.motorcycle52Delivery.stableGeometryIds,true);
const pack=parseBlenderRoom(THREE,manifest,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),manifest.textures.map(()=>new THREE.Texture()));
pack.world.updateMatrixWorld(true);
const nodes=new Map();
pack.world.traverse(o=>nodes.set(o.userData.blenderNode,o));
const parts=manifest.nodes.filter(n=>n.userData?.motorcycle52);
assert.equal(parts.length,manifest.statistics.exteriorRefinement.motorcycle52.batches);
assert.ok(parts.length<=24,'Do not expand the 1,128 source parts into individual draws');
assert.ok(metadata.sourceRemeshPreserved,'Preserve thin source fairings before mesh reduction');
assert.ok(metadata.triangles<=320000);
let triangles=0,vertices=0;
const bounds=new THREE.Box3();
for(const desc of parts){
  assert.equal(desc.parent,750,'Keep the existing parking transform');
  const obj=nodes.get(desc.id),g=obj.geometry,m=obj.material;
  assert.ok(g.attributes.uv&&g.attributes.uv1);
  assert.equal(g.index.count%3,0);
  triangles+=g.index.count/3;vertices+=g.attributes.position.count;
  bounds.union(new THREE.Box3().setFromObject(obj,true));
  const normal=g.attributes.normal;
  for(let i=0;i<normal.count;i++)assert.ok(Math.abs(new THREE.Vector3().fromBufferAttribute(normal,i).length()-1)<.01,'Unit normals survive export');
  const uv=g.attributes.uv.array;
  for(const v of uv)assert.ok(v>=-.001&&v<=1.001,'Atlas UVs remain within the baked image');
  assert.ok(m.map&&m.metalnessMap);
  assert.ok(m.roughness>=.03&&m.roughness<=1);
}
assert.equal(triangles,metadata.triangles);
assert.ok(vertices<triangles*2,'Use indexed geometry with shared vertices');
const size=bounds.getSize(new THREE.Vector3());
assert.ok(size.x>.5&&size.x<1.1&&size.z>1.8&&size.z<2.4,'Keep real motorcycle proportions');
assert.ok(bounds.min.y>-9.40&&bounds.min.y<-9.30,'Tyres remain on the courtyard paving');
for(const [id,expected] of [[750,'0115c010f2a239e8345ed380cdc26496bbfd52437372b06257ada92ddb8aed56'],[771,'c41b1104f53b53aa2ac3f2721f153f74e5beec90adcd6c3b0eb9af3f3a29897a']]){
  assert.equal(createHash('sha256').update(JSON.stringify(manifest.nodes[id])).digest('hex'),expected,'Keep the parking root and adjacent courtyard geometry unchanged');
}
for(const file of ['gsx52-albedo.png','gsx52-metalness.png']){
  const texture=manifest.textures.find(t=>t.webPath.endsWith(file));
  assert.ok(texture);assert.equal(texture.flipY,true);
  assert.equal(texture.colorSpace,file.includes('albedo')?'srgb':'');
}
console.log(`PASS motorcycle52: ${triangles} triangles, ${parts.length} material batches, ${vertices} indexed vertices; source fairings/UVs/parking retained.`);
