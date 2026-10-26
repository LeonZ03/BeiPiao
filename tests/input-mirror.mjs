import assert from 'node:assert/strict';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {movementKey,releaseMovementKey,touchMovementKeys,verticalMovement,wheelHeightDelta,bindWalkWheel} from '../room-site/dist/room-input.js';
import {installDoorMirror} from '../room-site/dist/wardrobe.js';

const held=new Set();
const down=e=>{const key=movementKey(e);if(key)held.add(key);};
const up=e=>held.delete(releaseMovementKey(e));
for(const event of [{key:'Fn',code:''},{code:'Fn'},{code:'FnLock'},{code:'ShiftLeft'},{code:'ShiftRight'},{code:'ControlLeft'},{code:'KeyC'}]){
  down(event);assert.equal(held.size,0,'Removed height bindings never latch movement');
}
assert.equal(verticalMovement(new Set(['ShiftLeft','ShiftRight','Fn'])),0);
down({code:'ArrowUp'});assert.equal(verticalMovement(held),1,'Up arrow raises the view');
assert.ok(held.has('MoveUp'));assert.ok(!held.has('ArrowUp'),'Height arrow never enters forward movement');
up({code:'ArrowUp'});down({code:'ArrowDown'});assert.equal(verticalMovement(held),-1,'Down arrow lowers the view');
assert.ok(held.has('MoveDown'));assert.ok(!held.has('ArrowDown'),'Height arrow never enters backward movement');
held.add(touchMovementKeys.down);up({code:'ArrowDown'});
assert.equal(verticalMovement(held),-1,'Releasing a physical key does not release touch descent');
held.add(touchMovementKeys.up);assert.equal(verticalMovement(held),0,'Opposite height buttons cancel');
held.clear();assert.equal(verticalMovement(held),0,'Blur/session clear releases all movement');
down({code:'KeyW'});down({code:'KeyS'});assert.ok(held.has('KeyW')&&held.has('KeyS'),'W and S retain horizontal movement');
assert.equal(verticalMovement(held),0);held.clear();

assert.equal(wheelHeightDelta({deltaY:-100,deltaMode:0}),.15,'Forward wheel raises the view');
assert.ok(Math.abs(wheelHeightDelta({deltaY:3,deltaMode:1})+.072)<1e-12,'Line units normalize to pixels');
assert.equal(wheelHeightDelta({deltaY:1,deltaMode:2},844),-.18,'Page or large deltas are capped');
assert.equal(wheelHeightDelta({deltaY:Infinity}),0);
assert.equal(wheelHeightDelta({deltaY:-100,ctrlKey:true}),0,'Trackpad pinch is not height movement');
const wheelCanvas=new EventTarget();wheelCanvas.clientHeight=844;
let walking=true,height=1.5;
const unbind=bindWalkWheel({canvas:wheelCanvas,enabled:()=>walking,move:delta=>height+=delta});
const wheel=delta=>{const event=new Event('wheel',{cancelable:true});Object.assign(event,{deltaY:delta,deltaMode:0});wheelCanvas.dispatchEvent(event);return event;};
assert.equal(wheel(-100).defaultPrevented,true);assert.equal(height,1.65);
wheel(100);assert.equal(height,1.5);
walking=false;assert.equal(wheel(-100).defaultPrevented,false,'Overview retains the unmodified wheel for orbit zoom');assert.equal(height,1.5);
walking=true;unbind();assert.equal(wheel(-100).defaultPrevented,false);assert.equal(height,1.5);

class ProbeReflector extends THREE.Mesh{
  constructor(geometry,options){super(geometry,new THREE.MeshBasicMaterial());this.options=options;this.calls=0;this.onBeforeRender=()=>this.calls++;}
}
const world=new THREE.Group(),door=new THREE.Group(),scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera();
scene.add(world,new THREE.HemisphereLight());world.add(door);world.userData.geometryRevision=0;
const source=new THREE.Mesh(new THREE.PlaneGeometry(.265,1.385),new THREE.MeshStandardMaterial());
source.name='C43_WardrobeFarMirror_Reflection';source.position.set(.03,1,.28);source.rotation.y=Math.PI/2;source.userData.mirrorSurface=true;door.add(source);
const expected=source.matrix.clone();source.updateMatrix();expected.copy(source.matrix);
let open=false;
const renderer={isWebGLRenderer:true,shadowMap:{needsUpdate:true}};
const mirror=installDoorMirror({THREE,world,renderer,source,Reflector:ProbeReflector,clipBias:0,enabled:()=>open});
world.updateMatrixWorld(true);camera.updateMatrixWorld();
assert.equal(mirror.parent,door,'Mirror retains the moving cabinet door parent');
assert.equal(mirror.options.clipBias,0,'C43 clips at the surface, excluding its own 4 mm opaque backing');
assert.equal(source.parent,null,'Original face is replaced, not overlaid');
assert.equal(mirror.geometry,source.geometry,'Reuse authored mirror geometry and UV');
assert.ok(mirror.matrix.equals(expected));assert.ok(mirror.userData.noCollision);
mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,0,'Closed door does not render a hidden inner mirror');
open=true;mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,1);
mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,1,'Stationary reflection stays cached');
door.rotation.y=-.7;world.updateMatrixWorld(true);mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,2,'Moving door immediately updates reflection');
world.userData.geometryRevision++;mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,3,'Other object changes invalidate the mirror');
world.userData.reflectionPass=true;world.userData.geometryRevision++;mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,3,'Nested reflection cannot recurse');
world.userData.reflectionPass=false;open=false;camera.position.x+=.1;camera.updateMatrixWorld();mirror.onBeforeRender(renderer,scene,camera);assert.equal(mirror.calls,3);
assert.equal(renderer.shadowMap.needsUpdate,true,'Reflection preserves the caller shadow update flag');
console.log('Input and mirror: walk wheel / overview zoom isolation, arrows/touch, removed Shift/Fn, door binding, visibility, refresh and recursion PASS');
