import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {createWardrobe,guardRoomReflection} from '../room-site/dist/wardrobe.js';
import {createFlyNavigation,batchStaticGeometry} from '../room-site/dist/navigation.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';

const world=new THREE.Group(),camera=new THREE.PerspectiveCamera();camera.position.set(.7,1.5,.2);
const pivots=[-.556,-1.328,-1.715].map((z,i)=>{
  const g=new THREE.Group();g.position.set(-.794,0,z);g.userData.openAngle=i===0?-1.48:1.48;
  const mesh=new THREE.Mesh(new THREE.BoxGeometry(.024,1.98,.377),new THREE.MeshStandardMaterial());
  mesh.position.set(0,1.065,i===0?-.19:.19);g.add(mesh);world.add(g);return g;
});
const wardrobe=createWardrobe({THREE,world,camera,refs:{wardrobeDoors:pivots}});
const navigation=createFlyNavigation(THREE,world);
assert.equal(navigation.clearance,.002);assert.equal(navigation.dynamicSurfaces,3);
assert.equal(batchStaticGeometry(THREE,world),0,'Moving leaves retain their pivot identity');
function step(n=1){for(let i=0;i<n;i++)if(wardrobe.update(.05))navigation.updateDynamic();}
const path=[new THREE.Vector3(-.4,1,-.74),new THREE.Vector3(-1,1,-.74)];
assert.equal(navigation.canTravel(...path),false,'Closed panel blocks actual door surface');
wardrobe.toggle('wardrobeLeft');step(100);
assert.equal(wardrobe.state.doors[0].amount,1);assert.equal(wardrobe.state.doors[1].amount,0);
assert.equal(navigation.canTravel(...path),true,'Open door no longer leaves a stale collision in its old location');
assert.equal(navigation.canTravel(new THREE.Vector3(-.60,1,-.40),new THREE.Vector3(-.60,1,-.80)),false,'Open door collision moves into the aisle');
wardrobe.toggle('wardrobeLeft');step(3);const reversing=wardrobe.state.doors[0].amount;
wardrobe.toggle('wardrobeLeft');step();assert.ok(wardrobe.state.doors[0].amount>reversing,'Mid-motion reversal starts from the current pose');
step(100);const settledRevision=wardrobe.revision;step(30);assert.equal(wardrobe.revision,settledRevision,'Settled doors do not invalidate the room cache');
wardrobe.toggle('wardrobeRight');step();assert.ok(wardrobe.state.doors[2].amount>0,'Right door moves immediately without waiting for another fixture');
step(100);assert.equal(wardrobe.state.doors[2].amount,1);
wardrobe.toggle('wardrobeRight');step(100);assert.equal(wardrobe.state.doors[2].amount,0);

// Hold the viewpoint on an intermediate door arc: no sweep-through or camera push.
wardrobe.toggle('wardrobeLeft');step(100);
const obstacle=new THREE.Vector3(0,1,-.22).applyAxisAngle(new THREE.Vector3(0,1,0),-.60).add(pivots[0].position);
camera.position.copy(obstacle);wardrobe.toggle('wardrobeLeft');step(100);
assert.equal(wardrobe.state.doors[0].blocked,true);assert.ok(wardrobe.state.doors[0].amount>0&&wardrobe.state.doors[0].amount<1);
assert.deepEqual(camera.position.toArray(),obstacle.toArray(),'Door safety never moves the observer');
camera.position.set(.7,1.5,.2);step(100);assert.equal(wardrobe.state.doors[0].amount,1,'Move away to resume the requested motion');

function assertHingeConnections(root,mechanisms){
  root.updateMatrixWorld(true);const byId=new Map();root.traverse(o=>byId.set(o.userData.blenderNode,o));
  for(const group of mechanisms){
    const d=group.userData,upper=byId.get(d.upperArmNodeId),lower=byId.get(d.lowerArmNodeId),joint=byId.get(d.jointNodeId),door=byId.get(d.doorNodeId);
    const fixed=group.parent.localToWorld(new THREE.Vector3().fromArray(d.fixedAnchor));
    const moving=door.localToWorld(new THREE.Vector3().fromArray(d.movingAnchor));
    const a=upper.localToWorld(new THREE.Vector3(0,-.5,0)),b=upper.localToWorld(new THREE.Vector3(0,.5,0));
    const c=lower.localToWorld(new THREE.Vector3(0,-.5,0)),e=lower.localToWorld(new THREE.Vector3(0,.5,0));
    assert.ok(a.distanceTo(fixed)<1e-6&&b.distanceTo(c)<1e-6&&e.distanceTo(moving)<1e-6,'Hinge arms remain connected to both real anchors');
    assert.ok(b.distanceTo(joint.getWorldPosition(new THREE.Vector3()))<1e-6,'Elbow pin stays at the two-arm joint');
    assert.ok(Math.abs(a.distanceTo(b)-d.armLength)<1e-6&&Math.abs(c.distanceTo(e)-d.armLength)<1e-6,'Articulated links retain fixed physical length');
  }
}
const hingeWorld=new THREE.Group(),hingeDoor=new THREE.Group(),mechanism=new THREE.Group();hingeWorld.add(hingeDoor,mechanism);
hingeWorld.position.set(-.8,0,-1);hingeDoor.userData={blenderNode:100,openAngle:-1.48};
for(const id of [101,102,103]){const node=new THREE.Mesh(id===103?new THREE.SphereGeometry(.004):new THREE.BoxGeometry(.007,1,.011),new THREE.MeshStandardMaterial());node.userData.blenderNode=id;mechanism.add(node);}
mechanism.userData={doorNodeId:100,fixedAnchor:[-.045,1,0],movingAnchor:[-.015,1,.018],armLength:.055,elbowSign:-1,upperArmNodeId:101,lowerArmNodeId:102,jointNodeId:103};
const hingeController=createWardrobe({THREE,world:hingeWorld,camera,refs:{wardrobeDoors:[hingeDoor],wardrobeHingeMechanisms:[mechanism]}});
assertHingeConnections(hingeWorld,[mechanism]);hingeController.toggle('wardrobeLeft');
for(let i=0;i<80;i++){hingeController.update(.05,1);assertHingeConnections(hingeWorld,[mechanism]);}
hingeController.toggle('wardrobeLeft');for(let i=0;i<80;i++){hingeController.update(.05,1);assertHingeConnections(hingeWorld,[mechanism]);}

// Shared reflection guards prevent floor/mirror recursion and partial cache captures.
const scene=new THREE.Scene();scene.add(world,new THREE.HemisphereLight());
const renderer={shadowMap:{needsUpdate:true}},a=new THREE.Object3D(),b=new THREE.Object3D();world.add(a,b);
let aCalls=0,bCalls=0;
a.onBeforeRender=()=>{aCalls++;b.onBeforeRender(renderer,scene,camera);};
b.onBeforeRender=()=>{bCalls++;a.onBeforeRender(renderer,scene,camera);};
guardRoomReflection({THREE,world,reflection:a,interval:0});guardRoomReflection({THREE,world,reflection:b,interval:0});
world.updateMatrixWorld(true);camera.updateMatrixWorld();
a.onBeforeRender(renderer,scene,camera);b.onBeforeRender(renderer,scene,camera);
assert.equal(aCalls,1);assert.equal(bCalls,1);assert.equal(renderer.shadowMap.needsUpdate,true);
a.onBeforeRender(renderer,scene,camera);assert.equal(aCalls,1,'Unchanged reflection is reused');
world.userData.geometryRevision++;a.onBeforeRender(renderer,scene,camera);assert.equal(aCalls,2,'Door geometry invalidates its reflection');
world.userData.staticCacheCapture=true;world.userData.geometryRevision++;a.onBeforeRender(renderer,scene,camera);assert.equal(aCalls,2,'Do not capture reflection while ambient meshes are excluded');world.userData.staticCacheCapture=false;

// Rapid consecutive camera poses must each get a current mirror image.
const synced=new THREE.Object3D();let syncedFrames=0;synced.onBeforeRender=()=>syncedFrames++;world.add(synced);
guardRoomReflection({THREE,world,reflection:synced,interval:100000,synchronizeView:true});
synced.onBeforeRender(renderer,scene,camera);
for(let i=0;i<3;i++){camera.position.x+=.01;camera.updateMatrixWorld();synced.onBeforeRender(renderer,scene,camera);}
assert.equal(syncedFrames,4,'Motion must not reuse a stale mirror view due to time throttling');
synced.onBeforeRender(renderer,scene,camera);assert.equal(syncedFrames,4,'Stationary mirror remains cached');

const url=new URL('../room-site/dist/assets/full-room/',import.meta.url),manifest=JSON.parse(fs.readFileSync(new URL('scene.json',url)));
if(manifest.refs.wardrobeDoors){
  const bytes=fs.readFileSync(new URL('geometry.bin',url)),buffer=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
  const pack=parseBlenderRoom(THREE,manifest,buffer,manifest.textures.map(()=>new THREE.Texture()));
  assert.equal(pack.refs.wardrobeDoors?.length,3,'Three authored door pivots exported');
  for(const [i,door]of pack.refs.wardrobeDoors.entries()){
    assert.equal(door.parent,pack.refs.wardrobe);assert.equal(door.userData.interactive,['wardrobeLeft','wardrobeMiddle','wardrobeRight'][i]);
    assert.ok(door.children.some(o=>o.isMesh),'Door geometry belongs to its hinge');
    assert.ok((i===0?-1:1)*door.userData.openAngle>1);
    const expected=new THREE.Vector3(-.792,0,[-.556,-1.328,-1.715][i]);
    assert.ok(door.getWorldPosition(new THREE.Vector3()).distanceTo(expected)<.0001,'Authored hinge must stay on its actual cabinet edge, not world origin');
    const leaf=door.children.find(o=>o.userData.blenderNode===door.userData.leafNodeId);
    assert.ok(leaf,'Stable original door node is a child of its new hinge');
    assert.ok(leaf.getWorldPosition(new THREE.Vector3()).distanceTo(new THREE.Vector3(-.806,1.065,[-.749,-1.135,-1.521][i]))<.0001,'Closed door placement must preserve the approved cabinet exterior');
  }
  assert.ok(pack.refs.wardrobeMirror?.isMesh,'Right door has a Blender mirror face');
  let ancestor=pack.refs.wardrobeMirror;while(ancestor&&ancestor!==pack.refs.wardrobeDoors[2])ancestor=ancestor.parent;
  assert.equal(ancestor,pack.refs.wardrobeDoors[2],'Mirror must move with the right door');
  const observer=new THREE.PerspectiveCamera();observer.position.set(.6,1.5,.3);
  const controller=createWardrobe({THREE,world:pack.world,camera:observer,refs:pack.refs});
  if(pack.refs.wardrobeHingeMechanisms){assert.equal(pack.refs.wardrobeHingeMechanisms.length,9);assertHingeConnections(pack.world,pack.refs.wardrobeHingeMechanisms);}
  const nav=createFlyNavigation(THREE,pack.world,[pack.refs.outside,pack.refs.curtain]);
  const intoCabinet=[new THREE.Vector3(-.35,1.1,-.78),new THREE.Vector3(-1.10,1.1,-.78)];
  assert.equal(nav.canTravel(...intoCabinet),false,'Actual closed Blender door blocks entry');
  controller.toggle('wardrobeLeft');for(let i=0;i<100;i++)if(controller.update(.05,1)){nav.updateDynamic();if(pack.refs.wardrobeHingeMechanisms)assertHingeConnections(pack.world,pack.refs.wardrobeHingeMechanisms);}
  assert.equal(nav.canTravel(...intoCabinet),true,'Actual open Blender cabinet is hollow; no retained solid cabinet or stale door collider');
  for(const id of ['wardrobeMiddle','wardrobeRight']){
    controller.toggle(id);for(let i=0;i<100;i++)if(controller.update(.05,1)&&pack.refs.wardrobeHingeMechanisms)assertHingeConnections(pack.world,pack.refs.wardrobeHingeMechanisms);
  }
  for(const id of ['wardrobeLeft','wardrobeMiddle','wardrobeRight'])controller.toggle(id);
  for(let i=0;i<100;i++)if(controller.update(.05,1)&&pack.refs.wardrobeHingeMechanisms)assertHingeConnections(pack.world,pack.refs.wardrobeHingeMechanisms);
  console.log(`PASS ${manifest.revision} Blender refs, independent pivots, mirror ancestry, hollow cabinet collision and articulated hinge connections.`);
}else assert.fail('Current room pack must export its three wardrobe doors.');
console.log('PASS wardrobe: reversible independent motion, independent fixtures, dynamic collision, camera sweep safety, idle cache and reflection recursion.');
