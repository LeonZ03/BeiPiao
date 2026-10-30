// Targeted geometry, source-provenance and visible-contact checks for finish50.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {gunzipSync} from 'node:zlib';
import * as T from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const root=new URL('../',import.meta.url),dir=new URL('room-site/dist/assets/full-room/',root);
const p=JSON.parse(fs.readFileSync(new URL('scene.json',dir))),raw=fs.readFileSync(new URL('geometry.bin',dir));
assert.equal(p.revision,'finish50e');assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',dir))),raw);
assert.ok(raw.length<100*1024*1024,'Keep the required editable/raw package below repository file limit');
const parent=JSON.parse(execFileSync('git',['show','150cd61:room-site/dist/assets/full-room/scene.json'],{cwd:root,encoding:'utf8',maxBuffer:20e6}));
const allowed=new Set([783,789,790,793,794,795,796,798,...Array.from({length:24},(_,i)=>838+i),1253,1254,1255,1282,1503,1513,...Array.from({length:7},(_,i)=>1528+i),1702,1703,1705,1706,1707]);
for(const n of parent.nodes)if(!allowed.has(n.id))assert.deepEqual(p.nodes[n.id],n,'Unrelated node '+n.id);
assert.deepEqual(p.refs,parent.refs);assert.deepEqual(p.materials.slice(0,parent.materials.length),parent.materials);assert.deepEqual(p.textures.slice(0,parent.textures.length),parent.textures);
for(const n of p.nodes.filter(n=>allowed.has(n.id)||n.id>=parent.nodes.length)){
 const g=p.geometries[n.geometry];if(!g||!g.index.length)continue;
 for(const d of Object.values(g.attributes)){const A={Float32Array,Int16Array,Uint16Array,Uint32Array}[d.type],a=new A(raw.buffer,raw.byteOffset+d.offset,d.length);assert.ok(a.every(Number.isFinite),n.id+' finite attributes');}
 assert.ok(g.attributes.uv,'UV0 '+n.id);
 if(n.geometry>=parent.geometries.length&&g.index.length)assert.ok(g.attributes.uv1,'New export retains UV1 '+n.id);
 const I={Uint32Array,Uint16Array}[g.index.type],index=new I(raw.buffer,raw.byteOffset+g.index.offset,g.index.length);assert.ok(index.every(i=>i<g.attributes.position.length/3),'Valid indices '+n.id);
}
const aliases=structuredClone(p);aliases.nodes.forEach(n=>n.name='N'+n.id);
const {world}=parseBlenderRoom(T,aliases,raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength),p.textures.map(()=>new T.Texture()));world.updateMatrixWorld(true);
const object=i=>world.getObjectByName('N'+i),bounds=i=>new T.Box3().setFromObject(object(i));
assert.equal(p.nodes[1503].visible,false,'No false white rear bar');
const ceramic=new T.Raycaster(new T.Vector3(-.065,1.2,3.08),new T.Vector3(0,-1,0),0,.6).intersectObject(object(1502))[0];
assert.ok(ceramic);assert.ok(bounds(1513).min.y<=ceramic.point.y&&ceramic.point.y-bounds(1513).min.y<.003,'Tap physically enters ceramic rear rim');
for(const [body,label]of [[1528,2039],[1529,2040],[1530,2041]]){
 const b=bounds(body),target=b.getCenter(new T.Vector3()),origin=target.clone();origin.z=2.7;
 const hits=new T.Raycaster(origin,target.clone().sub(origin).normalize(),0,.6).intersectObject(world,true);
 assert.equal(hits[0]?.object,object(label),'Visible front label is ahead of bottle and cabinet '+body);
 const shelf=body===1530?1517:1522;assert.ok(Math.abs(b.min.y-bounds(shelf).max.y)<1e-6,'Bottle rests on shelf');
}
assert.ok(Math.abs(bounds(1534).min.y-bounds(1517).max.y)<1e-6,'Toilet paper rests on top');
const paperCentre=bounds(1534).getCenter(new T.Vector3());paperCentre.y=2.2;
assert.equal(new T.Raycaster(paperCentre,new T.Vector3(0,-1,0),0,.1).intersectObject(object(1534)).length,0,'Real open roll core');
const cap=object(839).geometry.boundingBox;assert.ok(cap.max.z<.177&&cap.min.y<-.025,'Shorter downward-curved baseball bill');
assert.ok(bounds(795).max.y<2.43,'Rear spoiler remains seated below room ceiling');
console.log('PASS finish50: target data/gzip/UV, unchanged nodes/refs, tap support, shelf/label visibility, open tissue core and curved baseball bill.');
