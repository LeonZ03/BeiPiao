// CPU regressions against the actual interior pack plus injectable Web Audio.
// Browser/WebGL and perceptual QA remain separate, explicit release checks.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
import {batchCourtyardGeometry,createCourtyardNavigation,easedAmount,oppositeEndpoint,courtyardLockView,courtyardOverviewView} from '../room-site/dist/courtyard43-effects.js';
import {createCourtyardAudio} from '../room-site/dist/courtyard43-audio.js';

const base=new URL('../room-site/dist/assets/rooms/Courtyard43/interior/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('scene.json',base)));
assert.equal(manifest.stage,'interior');assert.equal(manifest.structureApproved,true);
const bytes=fs.readFileSync(new URL('geometry.bin',base)),buffer=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const textures=manifest.textures.map(t=>{assert.ok(fs.existsSync(new URL('../room-site/dist/'+t.webPath,import.meta.url)));return new THREE.Texture();});
const {world,refs}=parseBlenderRoom(THREE,manifest,buffer,textures);
const interactions=manifest.interactions.map(d=>({...d,object:world.getObjectByName(manifest.nodes[d.node].name)}));
assert.deepEqual(new Set(interactions.map(d=>d.id)),new Set(['curtain','entry-door','entry-lock','ceiling-switch','wardrobeFar','wardrobeNear']));
for(const i of interactions)assert.ok(i.object,'Every interactive pivot exists');
for(const id of ['entry-door','ceiling-switch'])assert.ok(refs.cutaway.includes(interactions.find(i=>i.id===id).object),`Overview hides the complete ${id} interaction root`);
assert.ok(refs.cutaway.some(o=>o.name==='C43_Switch_Backplate'),'Switch plate follows its hidden wall');
const deskOutlet=world.getObjectByName('C43_Desk_Outlet_Backplate');assert.ok(deskOutlet&&!refs.cutaway.includes(deskOutlet),'The outlet on the retained left wall stays visible');
const approvedOverview=JSON.stringify(manifest.review.viewpoints.overview),closerOverview=courtyardOverviewView(manifest.review.viewpoints.overview);
const cameraDistance=v=>new THREE.Vector3(...v.position).distanceTo(new THREE.Vector3(...v.target));
assert.ok(Math.abs(cameraDistance(closerOverview)/cameraDistance(manifest.review.viewpoints.overview)-.85)<1e-10);
assert.equal(JSON.stringify(manifest.review.viewpoints.overview),approvedOverview,'Overview zoom must not mutate approved layout data');
const curtains=refs.curtainPanels.slice();assert.equal(curtains.length,4);
for(const curtain of curtains){assert.equal(curtain.geometry.morphAttributes.position.length,1);assert.equal(curtain.morphTargetInfluences[0],0);assert.equal(curtain.geometry.attributes.position.count,curtain.geometry.morphAttributes.position[0].count);}
const capture=()=>{const meshes=[];world.traverse(o=>{if(o.isMesh&&!o.userData.noCollision)meshes.push(o);});return meshes;};
const samples=[[[1.1,1.5,1.7],[2.5,1.5,1.7]],[[-.45,1.5,.5],[-.45,1.5,-.6]],[[-.7,.2,1.1],[-.7,.2,2.70]],[[-.7,.49,1.1],[-.7,.49,2.80]],[[1.8,1.2,1.8],[1.8,1.2,.8]],[[0,.2,.6],[0,-.1,.6]],[[0,1.5,-.4],[0,1.5,-1.4]]];
const distances=meshes=>samples.map(([a,b])=>{const start=new THREE.Vector3(...a),delta=new THREE.Vector3(...b).sub(start),length=delta.length();return new THREE.Raycaster(start,delta.normalize(),0,length).intersectObjects(meshes,false).map(h=>h.distance).sort((a,b)=>a-b);});
const before=distances(capture());const batch=batchCourtyardGeometry(THREE,world,interactions.map(i=>i.object));
assert.ok(batch.removed>100,'Static material batches materially reduce draw calls');
const after=distances(capture());for(let i=0;i<before.length;i++){assert.equal(after[i].length,before[i].length,`Batch ray intersections ${i}`);for(let j=0;j<before[i].length;j++)assert.ok(Math.abs(before[i][j]-after[i][j])<2e-5,'Batching preserves actual surfaces');}
for(const i of interactions){assert.ok(i.object.parent);i.object.traverse(o=>{if(o.isMesh)assert.ok(o.geometry.attributes.normal);});}
for(const curtain of curtains)assert.ok(curtain.parent,'Curtain morph meshes must not become static batches');
for(const cutaway of [...refs.cutaway,...refs.ceilings])assert.ok(cutaway.parent,'Cutaway identity survives batching');
for(const cutaway of refs.cutaway)cutaway.visible=false;
const visibleThroughParents=o=>{for(let n=o;n;n=n.parent)if(!n.visible)return false;return true;};
for(const id of ['entry-door','ceiling-switch'])interactions.find(i=>i.id===id).object.traverse(o=>assert.equal(visibleThroughParents(o),false,'No door/switch descendants float after cutaway'));
for(const cutaway of refs.cutaway)cutaway.visible=true;
const navigation=createCourtyardNavigation(THREE,world,manifest.review,interactions.filter(i=>i.kind==='hinge').map(i=>i.object));
const travel=(a,b)=>navigation.canTravel(new THREE.Vector3(...a),new THREE.Vector3(...b));
assert.equal(travel([-.45,1.5,.5],[-.45,1.5,-.6]),true,'Real balcony passage stays open');
assert.equal(travel([1.9,1.5,1.7],[2.35,1.5,1.7]),false,'Room boundary remains solid');
assert.equal(travel([1.8,1.2,1.8],[1.8,1.2,.8]),false,'Wardrobe surfaces stop a viewpoint');
assert.equal(travel([-.7,.49,1.1],[-.7,.49,2.8]),false,'Mattress has a real collision surface');
assert.equal(travel([-.7,.2,1.1],[-.7,.2,2.7]),true,'Low, empty under-bed space is usable');
const door=interactions.find(i=>i.id==='entry-door');assert.equal(door.defaultOpen,true);
const initial=door.object.quaternion.clone(),axis=new THREE.Vector3(0,1,0),closed=initial.clone().multiply(new THREE.Quaternion().setFromAxisAngle(axis,-door.openAngle));
const restored=closed.clone().multiply(new THREE.Quaternion().setFromAxisAngle(axis,door.openAngle));assert.ok(initial.angleTo(restored)<1e-7,'Default-open orientation is not applied twice');
assert.ok(closed.angleTo(new THREE.Quaternion())<1e-6,'Entry door closed baseline matches the authored doorway');
const lock=interactions.find(i=>i.id==='entry-lock');
const allMeshes=[];world.traverse(o=>{if(o.isMesh)allMeshes.push(o);});
function aimedMesh(position,target){const p=new THREE.Vector3(...position),delta=new THREE.Vector3(...target).sub(p),distance=delta.length();return new THREE.Raycaster(p,delta.normalize(),0,distance+.05).intersectObjects(allMeshes,false)[0]?.object;}
const switchAim=aimedMesh([2.04,1.48,1.78],[(manifest.review.room.centerX??0)+manifest.review.room.width/2-.019,1.26,2.40]);
assert.equal(switchAim?.name,'C43_Switch_Rocker','Open door must not occlude the switch close-up');
const lockTargets=[];
for(const a of [0,.25,.5,.75,1]){
  door.object.quaternion.copy(closed).multiply(new THREE.Quaternion().setFromAxisAngle(axis,door.openAngle*a));world.updateMatrixWorld(true);
  const view=courtyardLockView(THREE,door.object,lock.object,manifest.review);lockTargets.push(view.target);
  assert.equal(aimedMesh(view.position,view.target)?.name,'C43_Door_Thumbturn',`Lock close-up remains visible at door amount ${a}`);
  assert.ok(view.position[0]<manifest.review.room.centerX+manifest.review.room.width/2-.04,'Lock camera stays inside the room');
}
assert.ok(new THREE.Vector3(...lockTargets[0]).distanceTo(new THREE.Vector3(...lockTargets.at(-1)))>.5,'Lock target follows the door instead of staying at a stale fixed point');
door.object.quaternion.copy(initial);world.updateMatrixWorld(true);navigation.updateDynamic();
let amount=1;for(let i=0;i<40;i++)amount=easedAmount(amount,0,.025);assert.ok(amount>.043&&amount<.047,'One second of cabinet response matches 3.1 exponential damping');
for(const partial of [.02,.17,.49,.5,.61,.88,.99]){
  const endpoint=oppositeEndpoint(partial,partial);assert.ok(endpoint===0||endpoint===1,'A blocked fractional target recovers to a complete endpoint');
  assert.equal(endpoint,partial>=.5?0:1);let current=partial;for(let i=0;i<160;i++)current=easedAmount(current,endpoint,.025);assert.equal(current,endpoint,'Unblocked follow-up reaches the selected endpoint');
}
assert.equal(oppositeEndpoint(1,.12),0,'An opening door can reverse before crossing halfway');assert.equal(oppositeEndpoint(0,.88),1,'A closing door can reverse before crossing halfway');assert.equal(oppositeEndpoint(undefined,.61),0);

class Param{value=0;setTargetAtTime(v){this.value=v;}setValueAtTime(v){this.value=v;}linearRampToValueAtTime(v){this.value=v;this.peak=v;}exponentialRampToValueAtTime(v){this.value=v;}cancelScheduledValues(){}}
class Node{gain=new Param();frequency=new Param();Q=new Param();pan=new Param();playbackRate={value:1};connect(){}disconnect(){}start(){this.started=true;}stop(t){this.stopAt=t;}}
class Context{state='suspended';currentTime=0;sampleRate=8000;destination=new Node();sources=[];gains=[];createBuffer(channels,length){const data=new Float32Array(length);return{getChannelData:()=>data};}createGain(){const n=new Node();this.gains.push(n);return n;}createBiquadFilter(){return new Node();}createStereoPanner(){return new Node();}createBufferSource(){const n=new Node();this.sources.push(n);return n;}async resume(){this.state='running';}async suspend(){this.state='suspended';}async close(){this.state='closed';}}
let created=0;const loaded=[],context=new Context(),audio=createCourtyardAudio({createContext:()=>{created++;return context;},loadSample:async kind=>{loaded.push(kind);return{kind};}});
const astate={position:{x:0,y:1.5,z:0},yaw:0,curtainSpeed:0,doors:[{id:'wardrobeFar',amount:0,target:0,serial:0,moving:false,blocked:false,position:[0,1.5,0]}]};
const step=()=>audio.update(.05,astate),cabinet=astate.doors[0];
audio.setActive(true);step();audio.interaction('lock',[0,1.5,0]);assert.equal(created,0);assert.equal(loaded.length,0);assert.equal(audio.muted,true);
await audio.setMuted(false);assert.equal(created,1);assert.deepEqual(loaded.sort(),['close','open']);
Object.assign(cabinet,{amount:.05,target:1,serial:1,moving:true});step();const opened=context.sources.at(-1);assert.equal(opened.buffer.kind,'open');assert.equal(opened.loop,false);assert.equal(opened.playbackRate.value,1);
const count=context.sources.length;opened.onended();for(let i=0;i<6;i++){cabinet.amount+=.05;step();}assert.equal(context.sources.length,count,'A finished opening sample never retriggers during that same gesture');
Object.assign(cabinet,{amount:.6,target:0,serial:2});step();assert.equal(context.sources.length,count,'A close recording waits for its physical lead-in');cabinet.amount=.18;step();const closing=context.sources.at(-1);assert.equal(closing.buffer.kind,'close');assert.equal(closing.loop,false);cabinet.amount=0;cabinet.moving=false;step();assert.equal(closing.stopAt,undefined,'Closing tail is not clipped at the visual endpoint');
Object.assign(cabinet,{amount:.02,target:1,serial:3,moving:true});step();const reopened=context.sources.at(-1);assert.equal(reopened.buffer.kind,'open');Object.assign(cabinet,{amount:.01,target:0,serial:4});step();assert.notEqual(reopened.stopAt,undefined,'Reversing motion stops the old recording');
cabinet.blocked=true;step();assert.ok(!audio.state.voices.includes(cabinet.id));
astate.curtainSpeed=.2;step();assert.ok(audio.state.voices.includes('cloth'));astate.curtainSpeed=0;step();assert.ok(!audio.state.voices.includes('cloth'));
audio.interaction('switch',[0,1.5,0]);const normal=context.gains.at(-1).gain.peak;audio.interaction('lock',[0,1.5,0]);assert.equal(context.gains.at(-1).gain.peak,normal*2.5);
for(let i=0;i<25;i++)audio.interaction('switch',[0,1.5,0]);assert.ok(audio.state.transients<=8);
audio.setActive(false);assert.equal(context.state,'suspended');assert.deepEqual(audio.state.voices,[]);assert.equal(audio.state.transients,0);
audio.setActive(true);await Promise.resolve();await audio.setMuted(true);assert.equal(audio.muted,true);assert.equal(context.state,'suspended');audio.dispose();assert.equal(context.state,'closed');
let failed=true;const retry=createCourtyardAudio({createContext:()=>new Context(),loadSample:async()=>{if(failed)throw Error('offline');return{};}});retry.setActive(true);assert.equal(await retry.setMuted(false),false);failed=false;assert.equal(await retry.setMuted(false),true);retry.dispose();
const html=fs.readFileSync(new URL('../room-site/dist/courtyard43.html',import.meta.url),'utf8');assert.match(html,/<!-- beipiao-room-app:v1 -->/);assert.doesNotMatch(html,/结构白模|待确认|review-note/);assert.match(html,/soundBtn" aria-label="开启声音"/);
console.log(`PASS Courtyard43 runtime: ${batch.removed} static meshes merged, geometry/ray parity, real-surface navigation, protected morphs/cutaways, default-open door, partial-target recovery, unobstructed switch and moving-lock close-ups, 3.1 easing, opt-in audio, closing lead-in, reversal, pause and retry.`);
