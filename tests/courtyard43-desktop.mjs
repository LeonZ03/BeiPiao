// Contract checks for the photographed kit: tabletop support and asset boundary.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from '../room-site/dist/vendor/three.module.js';
const base=new URL('../room-site/dist/assets/rooms/Courtyard43/interior/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',base),'utf8'));
const binary=fs.readFileSync(new URL('geometry.bin',base));
const named=new Map(manifest.nodes.map(n=>[n.name,n]));
function bounds(node){
  const a=manifest.geometries[node.geometry].attributes.position;
  const v=new Float32Array(binary.buffer,binary.byteOffset+a.offset,a.length);
  const b=new THREE.Box3(),m=new THREE.Matrix4().fromArray(node.matrix);
  for(let i=0;i<v.length;i+=3)b.expandByPoint(new THREE.Vector3().fromArray(v,i).applyMatrix4(m));
  return b;
}
const kit=manifest.nodes.filter(n=>n.name.startsWith('C43_DevKit_'));
assert.equal(kit.length,10);
assert.ok(!manifest.nodes.some(n=>n.name==='C43_Mousepad'||n.name.startsWith('C43_Mouse_')),'Old pad and mouse are archived, not intersecting the boards');
const desk=bounds(named.get('C43_DeskTop')),mat=bounds(named.get('C43_DevKit_Mousemat'));
assert.ok(Math.abs(mat.min.y-desk.max.y)<.0002,'Fabric underside touches the table');
assert.ok(mat.min.x>desk.min.x&&mat.max.x<desk.max.x&&mat.min.z>desk.min.z&&mat.max.z<desk.max.z,'Mat remains inside the unchanged desk outline');
for(const node of kit){
  const b=bounds(node);
  assert.equal(node.userData.noCollision,true);
  assert.ok(b.min.y>=desk.max.y-.0002,'No object sinks into the desktop: '+node.name);
  assert.ok(b.min.x>desk.min.x&&b.max.x<-.77,'Keep kit inside right desk and clear of curtain sweep: '+node.name);
}
for(const name of ['Main_board','Expansion_board']){
  const b=bounds(named.get('C43_DevKit_'+name));
  assert.ok(Math.abs(b.min.y-.7433)<.0001,'PCB lower edges touch the 3.3mm fabric');
  assert.ok(b.max.y-b.min.y>.05,'Real sloping board assemblies retain depth');
}
for(const suffix of ['mousemat','cardboard','soldermask']){
  const m=manifest.materials.find(m=>m.name==='C43_DevKit_'+suffix);
  assert.ok(m.textures.bumpMap!==undefined,'Fine surface map exported: '+suffix);
}
const film=manifest.materials.find(m=>m.name==='C43_DevKit_bubble_film');
assert.equal(film.props.depthWrite,false);
assert.ok(film.props.opacity<.3);
console.log('PASS desktop kit: table contact, board slopes, curtain-side clearance, separate old mouse, and exported fine-scale surface maps.');
