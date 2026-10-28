// Published geometry checks for the photographed balcony and bedhead fixtures.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const base=new URL('../room-site/dist/assets/rooms/Courtyard43/interior/',import.meta.url);
const pack=JSON.parse(fs.readFileSync(new URL('scene.json',base)));
const raw=fs.readFileSync(new URL('geometry.bin',base)),gz=fs.readFileSync(new URL('geometry.bin.gz',base));
assert.deepEqual(gunzipSync(gz),raw);
const buffer=raw.buffer.slice(raw.byteOffset,raw.byteOffset+raw.byteLength);
const {world}=parseBlenderRoom(THREE,pack,buffer,pack.textures.map(()=>new THREE.Texture()));
world.updateMatrixWorld(true);
const added=pack.nodes.filter(n=>n.name.startsWith('C43_B35_'));
assert.ok(added.length>=50);
for(const n of added){
  const g=pack.geometries[n.geometry],count=g.attributes.position.length/3;
  assert.ok(g.attributes.uv&&g.attributes.uv1,n.name+' retains both UV channels');
  for(const d of Object.values(g.attributes)){
    const values=new Float32Array(buffer,d.offset,d.length);
    assert.ok([...values].every(Number.isFinite),n.name+' finite attributes');
  }
  const idx=new Uint32Array(buffer,g.index.offset,g.index.length);
  assert.ok([...idx].every(i=>i<count),n.name+' valid indices');
}
assert.equal(added.filter(n=>/BedheadLight\d_Diffuser$/.test(n.name)).length,3);
assert.equal(added.filter(n=>/WireHanger\d$/.test(n.name)).length,2);
for(const side of ['Left','Right']){
  const fronts=added.filter(n=>n.name.startsWith(`C43_B35_${side}Cabinet_Door`));
  assert.equal(fronts.length,side==='Left'?2:1);
  for(const n of fronts){
    const b=new THREE.Box3().setFromObject(world.getObjectByName(n.name));
    assert.ok(b.min.y>=.015&&b.max.y<.93,'Cabinets stand on the existing balcony floor');
    assert.ok(b.min.x>=-2.025&&b.max.x<=2.225,'Cabinet remains within approved walls');
  }
  assert.ok(world.getObjectByName(`C43_B35_OldCurtain${side}`));
}
const light=world.getObjectByName('C43_B35_BedheadLight0_Diffuser');
const centre=new THREE.Box3().setFromObject(light).getCenter(new THREE.Vector3());
// An actual opening through the soffit exposes the inset diffuser to the room.
const ray=new THREE.Raycaster(new THREE.Vector3(centre.x,2.40,centre.z),new THREE.Vector3(0,1,0),0,.35);
const hits=ray.intersectObject(world,true);
assert.equal(hits[0]?.object.name,light.name,'Recess is open; the soffit cannot cover the diffuser');
assert.ok(pack.statistics.triangles<=655632*1.15,'New details respect the existing triangle budget');
assert.ok(gz.length<=9809285*1.1,'Compressed pack growth remains bounded');
console.log(JSON.stringify({pass:true,addedMeshes:added.length,triangles:pack.statistics.triangles,gzipBytes:gz.length}));
