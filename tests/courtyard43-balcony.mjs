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
// The counter's former right-hand slot must be closed even at oblique angles,
// from the floor through the underside and overhang of its cap.
const counterReturn=world.getObjectByName('C43_Wall_Balcony_Pier_Right');
for(const x of [1.392,1.405,1.425,1.445])for(const y of [.006,.05,.4,.98,1.01]){
  for(const dx of [-.12,0,.12]){
    const origin=new THREE.Vector3(x+dx,y,.5),target=new THREE.Vector3(x,y,-.02);
    const ray=new THREE.Raycaster(origin,target.sub(origin).normalize(),0,.6);
    assert.ok(ray.intersectObject(counterReturn).length,'Wall closes the right counter junction');
  }
}
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
    assert.ok(b.min.y>=.015&&b.max.y>1.1&&b.max.y<1.24,'Taller cabinets retain floor contact');
    assert.ok(b.min.x>=-2.025&&b.max.x<=2.225,'Cabinet remains within approved walls');
  }
  assert.ok(world.getObjectByName(`C43_B35_OldCurtain${side}`));
}
assert.equal(added.filter(n=>/RackScissor\d_\d_\d$/.test(n.name)).length,8);
assert.equal(added.filter(n=>/DryingRailWallSocket/.test(n.name)).length,0,'Ceiling supports replace the mistaken wall sockets');
assert.equal(added.filter(n=>/RackCeilingPlate|RackParallelRail|RackEndCrossbar/.test(n.name)).length,0,'Single pole has no upper rectangle, second pole or crossbars');
assert.equal(added.filter(n=>/RackCeilingStud\d_\d$/.test(n.name)).length,4);
for(const n of added.filter(n=>/RackCeilingStud\d_\d$/.test(n.name))){
  const b=new THREE.Box3().setFromObject(world.getObjectByName(n.name));
  assert.ok(b.min.y<2.75&&b.max.y>2.75,'Small studs enter the balcony ceiling directly');
}
for(const n of added.filter(n=>/RackScissor\d_\d_\d$/.test(n.name))){
  const b=new THREE.Box3().setFromObject(world.getObjectByName(n.name));
  assert.ok(b.max.x-b.min.x>.17&&b.max.z-b.min.z<.005,'Scissor plane follows the single pole after the 90 degree rotation');
}
const rightCabinet=new THREE.Box3().makeEmpty();
for(const n of added.filter(n=>n.name.startsWith('C43_B35_RightCabinet'))){
  rightCabinet.union(new THREE.Box3().setFromObject(world.getObjectByName(n.name)));
}
const leftWall=world.getObjectByName('C43_Wall_Balcony_Left');
const rightWall=world.getObjectByName('C43_Wall_Balcony_Right');
assert.ok(rightWall?.userData.cutaway,'Right wall preserves the overview cutaway');
assert.equal(rightWall.material.name,leftWall.material.name,'Both ends use the same plaster');
const rightBounds=new THREE.Box3().setFromObject(rightWall);
assert.ok(rightBounds.min.x-rightCabinet.max.x>.09,'Right cabinet clears the wall');
assert.ok(rightBounds.getSize(new THREE.Vector3()).distanceTo(
  new THREE.Box3().setFromObject(leftWall).getSize(new THREE.Vector3()))<.00001,'Wall sections match');
for(const y of [.35,1.55,2.5])for(const z of [-.95,-.55,-.15]){
  const ray=new THREE.Raycaster(new THREE.Vector3(2.1,y,z),new THREE.Vector3(1,0,0),0,.2);
  assert.equal(ray.intersectObject(rightWall)[0]?.object,rightWall,'End wall closes the full opening');
}
assert.ok(!pack.nodes.some(n=>/^C43_Window_Return_|^C43_Wall_Balcony_Brick_Return$/.test(n.name)));
const frames=new THREE.Box3().setFromObject(world.getObjectByName('C43_Window_White_Frames'));
assert.ok(frames.max.z<-1.05&&frames.max.x>2.24,'Front PVC frames and corner mullion are retained');
for(const n of added.filter(n=>/WireHanger\d$/.test(n.name))){
  const o=world.getObjectByName(n.name),b=new THREE.Box3().setFromObject(o);
  assert.ok(b.max.x-b.min.x<.005&&b.max.z-b.min.z>.37,'Hanger plane is perpendicular to pole');
  const pivot=o.getWorldPosition(new THREE.Vector3());assert.ok(Math.abs(pivot.y-2.105)<.0001,'Hook pivot follows lowered rail');
  assert.equal(o.userData.breezeHanger,true);
}
const pole=new THREE.Box3().setFromObject(world.getObjectByName('C43_B35_DryingRail'));
assert.ok(Math.abs(pole.getCenter(new THREE.Vector3()).y-2.095)<.0001,'Single pole lowered 14 cm');
for(const side of ['Left','Right']){
  const cabinet=new THREE.Box3().makeEmpty();
  for(const n of added.filter(n=>n.name.startsWith(`C43_B35_${side}Cabinet`)))cabinet.union(new THREE.Box3().setFromObject(world.getObjectByName(n.name)));
  const cloth=new THREE.Box3().setFromObject(world.getObjectByName(`C43_B35_OldCurtain${side}`));
  assert.ok(cabinet.min.z-cloth.max.z>.025,'Case clears the curtain including breeze allowance');
}
const sill=new THREE.Box3().setFromObject(world.getObjectByName('C43_Window_Stone_Sill'));
const curtain=world.getObjectByName('C43_B35_OldCurtainRight');
const clothBounds=new THREE.Box3().setFromObject(curtain);
assert.ok(clothBounds.min.y<sill.min.y&&clothBounds.max.y>sill.max.y,'Curtain still falls below the sill');
const positions=curtain.geometry.attributes.position;
const point=new THREE.Vector3();
for(let i=0;i<positions.count;i++){
  point.fromBufferAttribute(positions,i).applyMatrix4(curtain.matrixWorld);
  // Include the rows either side of the sill so interpolated faces clear it too.
  if(point.y>=sill.min.y-.07&&point.y<=sill.max.y+.07){
    assert.ok(point.z>sill.max.z+.012,'Both fabric surfaces pass in front of the sill');
  }
  assert.ok(point.x<rightBounds.min.x-.04,'Fabric clears the solid side wall');
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
