// Scoped checks for the user-requested shape corrections, with immutable parent.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {gunzipSync} from 'node:zlib';
import * as T from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const root=new URL('../',import.meta.url), dir=new URL('room-site/dist/assets/full-room/',root);
const p=JSON.parse(fs.readFileSync(new URL('scene.json',dir))), raw=fs.readFileSync(new URL('geometry.bin',dir));
const previous=JSON.parse(execFileSync('git',['show','1075201:room-site/dist/assets/full-room/scene.json'],{cwd:root,encoding:'utf8',maxBuffer:20e6}));
assert.equal(p.revision,'correction51c');assert.ok(raw.length<100*1024*1024);
assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',dir))),raw);
const allowed=new Set([789,790,793,794,795,839,...Array.from({length:6},(_,i)=>847+i),1253,1528,1529,1530,1531,1532,1533,1701,2039,2040,2041]);
assert.deepEqual(p.refs,previous.refs);assert.deepEqual(p.materials,previous.materials);assert.deepEqual(p.textures,previous.textures);
for(const n of previous.nodes)if(!allowed.has(n.id))assert.deepEqual(p.nodes[n.id],n,'Unrelated node '+n.id);
function read(d){const A={Float32Array,Uint32Array,Uint16Array,Int16Array}[d.type];return new A(raw.buffer,raw.byteOffset+d.offset,d.length);}
for(const id of allowed){
 const g=p.geometries[p.nodes[id].geometry];
 for(const a of Object.values(g.attributes))assert.ok(read(a).every(Number.isFinite),id+' finite');
 assert.ok(g.attributes.uv1,id+' secondary UV');
 assert.ok(read(g.index).every(i=>i<g.attributes.position.length/3),id+' index range');
 const ns=read(g.attributes.normal);for(let i=0;i<ns.length;i+=3)assert.ok(Math.abs(Math.hypot(ns[i],ns[i+1],ns[i+2])-1)<.002,id+' unit normal');
}
const alias=structuredClone(p);alias.nodes.forEach(n=>n.name='N'+n.id);
const {world}=parseBlenderRoom(T,alias,raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength),p.textures.map(()=>new T.Texture()));world.updateMatrixWorld(true);
const object=i=>world.getObjectByName('N'+i), box=i=>new T.Box3().setFromObject(object(i));
for(const [id,aspect]of [[1528,.166/.060],[1529,.174*.855/.063],[1530,.195/.090]]){
 const b=box(id).getSize(new T.Vector3());assert.ok(Math.abs(b.y/b.x-aspect)<.04,'Photo front aspect '+id);
 const shelf=id===1530?1517:1522;assert.ok(Math.abs(box(id).min.y-box(shelf).max.y)<1e-6,'Shelf contact '+id);
}
for(const [body,label]of [[1528,2039],[1529,2040],[1530,2041]]){
 const target=box(body).getCenter(new T.Vector3()),origin=target.clone();origin.z=2.7;
 const hits=new T.Raycaster(origin,target.clone().sub(origin).normalize(),0,.6).intersectObject(world,true);
 assert.equal(hits[0]?.object,object(label),'Label remains on visible front '+body);
}
assert.ok(box(1531).min.y<=box(1529).max.y+1e-5,'Blue lid meets body');
assert.ok(box(1532).min.y<=box(1530).max.y+1e-5,'Pump collar meets shoulder');
const bill=object(839).geometry.boundingBox;assert.ok(bill.min.y>-.030&&bill.max.z<.177,'Smooth controlled brim extent');
const base=object(1701).geometry.attributes.position;
for(let i=0;i<base.count;i++)if(base.getX(i)<-.20)assert.ok(Math.abs(base.getZ(i))<.212,'No projecting rear seat corner');
console.log('PASS correction51: scoped nodes/refs/materials, data/gzip/UV/normals, product aspect/contact/front labels, solid lid/pump, restrained brim and recessed seat corners.');
