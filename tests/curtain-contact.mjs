import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
import {createWardrobe} from '../room-site/dist/wardrobe.js';
import {createCurtainDoorContact} from '../room-site/dist/curtain-contact.js';

const dir=new URL('../room-site/dist/assets/full-room/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',dir))),bytes=fs.readFileSync(new URL('geometry.bin',dir));
const pack=parseBlenderRoom(THREE,manifest,bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),manifest.textures.map(()=>new THREE.Texture()));
createWardrobe({THREE,world:pack.world,camera:new THREE.PerspectiveCamera(),refs:pack.refs});
const contact=createCurtainDoorContact({THREE,world:pack.world});
const pivot=pack.refs.wardrobeDoors[2],leaf=pack.world.getObjectByName('wardrobe-right-door');
leaf.geometry.computeBoundingBox();
const originalHash=createHash('sha256').update(bytes).digest('hex');
const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);};
let checked=0,penetrations=0,minBehind=Infinity,maxPush=0;
for(const amount of [0,.02,.1,.25,.5,.75,1]){
  pivot.rotation.y=pivot.userData.openAngle*amount;pack.world.updateMatrixWorld(true);contact.update(.016,{immediate:true});
  const inverse=new THREE.Matrix4().copy(leaf.matrixWorld).invert(),box=leaf.geometry.boundingBox;
  for(const panel of pack.refs.curtainPanels){
    const p=panel.geometry.attributes.position,m=panel.geometry.morphAttributes.position[0];
    for(const openness of [0,.35,1])for(const time of [0,2.5,5])for(let i=0;i<p.count;i++){
      let x=p.getX(i)*(1-openness)+m.getX(i)*openness,y=p.getY(i)*(1-openness)+m.getY(i)*openness,z=p.getZ(i)*(1-openness)+m.getZ(i)*openness;
      if(x>-.15||y>2.24)continue;
      const left=panel.userData.closedLeft+(panel.userData.fixedRight-panel.userData.openWidth-panel.userData.closedLeft)*openness;
      const sides=smooth(0,.085,x-left)*smooth(0,.085,panel.userData.fixedRight-x),lower=smooth(.04,1.35,2.36-y),phase=time*.82+x*2.1-y*.4,cloth=.86*sides*lower;
      z+=.10*cloth*(.5+.5*Math.sin(phase));x+=.040*cloth*Math.sin(phase-.65)*(1-.5*openness);y+=.012*cloth*Math.sin(phase+.4);
      const q=contact.deform({x,y,z});maxPush=Math.max(maxPush,z-q.z);assert.equal(q.x,x);assert.equal(q.y,y);assert.ok(q.z<=z+1e-9);
      const local=new THREE.Vector3(q.x,q.y,q.z).applyMatrix4(inverse);
      if(amount>0&&local.y>box.min.y+.0001&&local.y<box.max.y-.0001&&local.z>box.min.z+.0001&&local.z<box.max.z-.0001&&local.x>box.min.x+.0001&&local.x<box.max.x-.0001)penetrations++;
      checked++;
    }
  }
  const top={x:-.6,y:2.36,z:-1.6};assert.deepEqual(contact.deform(top),top,'Rod attachment never moves');
}
assert.equal(penetrations,0,'Actual morphed/wind-displaced vertices never enter the moving leaf');
assert.ok(maxPush>.06&&maxPush<.24,'Contact remains local and bounded');
assert.equal(contact.allowsDoorHit({x:-.6,y:1.2,z:-1.6}),true,'Core contact patch lets the actual visible door own its ray');
assert.equal(contact.allowsDoorHit({x:-.288461,y:.479641,z:-1.612549}),false,'Transition cloth still occludes the door, even when slightly moved');
pivot.rotation.y=0;pack.world.updateMatrixWorld(true);
let previous=contact.state.proxyAngle,lastPoint=null,tailStep=0;
const edgePoint={x:-.7935000062,y:1.4689269066,z:-1.5964856148};
for(let i=0;i<420;i++){
  contact.update(1/60);assert.ok(contact.state.proxyAngle<=previous);assert.ok(contact.state.proxyAngle>=contact.state.actualAngle);previous=contact.state.proxyAngle;
  const point=contact.deform(edgePoint);if(contact.state.release<.01&&lastPoint)tailStep=Math.max(tailStep,Math.abs(point.z-lastPoint.z));lastPoint=point;
}
assert.equal(contact.state.proxyAngle,0,'Release settles instead of sticking to the cabinet');
assert.ok(tailStep<.001,'The real pinned-edge sample returns continuously, without an end-of-release snap');
pivot.rotation.y=1;contact.update(.016,{immediate:true});assert.equal(contact.state.proxyAngle,1,'Reduced motion still enforces physical clearance');
assert.equal(createHash('sha256').update(bytes).digest('hex'),originalHash,'No model buffers rewritten');
console.log(JSON.stringify({result:'PASS',checked,penetrations,maxPushM:maxPush,sourceUnchanged:true}));
