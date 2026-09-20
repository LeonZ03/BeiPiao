import assert from 'node:assert/strict';
import {createRoomAudio} from '../room-site/dist/room-audio.js';

class Param {value=0;setTargetAtTime(v){this.value=v;}setValueAtTime(v){this.value=v;}linearRampToValueAtTime(v){this.value=v;}exponentialRampToValueAtTime(v){this.value=v;}cancelScheduledValues(){}}
class Node {gain=new Param();frequency=new Param();Q=new Param();pan=new Param();connect(){}disconnect(){}start(){this.started=true;}stop(t){this.stopAt=t;}}
class Context {
  state='suspended';currentTime=0;sampleRate=8000;destination=new Node();sources=[];
  createBuffer(channels,length){const data=new Float32Array(length);return {getChannelData:()=>data};}
  createGain(){return new Node();}createBiquadFilter(){return new Node();}createStereoPanner(){return new Node();}
  createBufferSource(){const n=new Node();this.sources.push(n);return n;}
  async resume(){this.state='running';}async suspend(){this.state='suspended';}async close(){this.state='closed';}
}
let created=0;const ctx=new Context();
const audio=createRoomAudio({createContext:()=>{created++;return ctx;}});
const state={curtain:0,doors:[{id:'wardrobeLeft',amount:0,blocked:false}],water:{shower:false,faucet:false},position:{x:0,y:1.5,z:0},yaw:0};
const step=()=>audio.update(.05,state);
audio.setActive(true);state.water.shower=true;step();audio.interaction('light');
assert.equal(created,0,'Entering/operating a muted room must not even create audio');
assert.equal(audio.muted,true);
await audio.setMuted(false);step();
assert.equal(created,1);assert.deepEqual(audio.state.loops,['shower']);
for(let i=0;i<60;i++)step();assert.equal(ctx.sources.length,1,'Continuous water reuses a single source');
state.water.faucet=true;step();assert.equal(audio.state.loops.length,2);
state.curtain=.1;state.doors[0].amount=.1;step();
assert.ok(audio.state.loops.includes('curtain'));assert.ok(audio.state.loops.includes('wardrobeLeft'));
state.doors[0].blocked=true;step();assert.ok(!audio.state.loops.includes('wardrobeLeft'));
assert.ok(!audio.state.loops.includes('curtain'),'Still cloth must become quiet');
state.doors[0].blocked=false;state.doors[0].amount=0;step();assert.equal(audio.state.transients,1,'Closing reaches a soft impact');
await audio.setMuted(true);assert.equal(ctx.state,'suspended');assert.deepEqual(audio.state.loops,[]);
audio.interaction('doorLock');assert.equal(audio.state.transients,0);
await audio.setMuted(false);step();assert.deepEqual(audio.state.loops,['shower','faucet']);
audio.setActive(false);assert.equal(ctx.state,'suspended');assert.deepEqual(audio.state.loops,[]);
audio.setActive(true);await Promise.resolve();step();assert.equal(audio.state.loops.length,2,'Returning restores currently running water');
state.water.shower=false;state.water.faucet=false;step();assert.equal(audio.state.loops.length,0);
for(let i=0;i<30;i++)audio.interaction('light');assert.ok(audio.state.transients<=8,'Repeated input stays bounded');
audio.dispose();assert.equal(ctx.state,'closed');assert.equal(audio.muted,true);
const unavailable=createRoomAudio({createContext:()=>null});unavailable.setActive(true);
assert.equal(await unavailable.setMuted(false),false);assert.equal(unavailable.muted,true);
console.log('PASS audio: default silence, opt-in, sustained/moving sources, mute/background/re-entry, bounded clicks and unavailable audio.');
