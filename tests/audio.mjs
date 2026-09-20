import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRoomAudio} from '../room-site/dist/room-audio.js';

class Param {value=0;setTargetAtTime(v){this.value=v;}setValueAtTime(v){this.value=v;}linearRampToValueAtTime(v){this.value=v;this.peak=v;}exponentialRampToValueAtTime(v){this.value=v;}cancelScheduledValues(){}}
class Node {gain=new Param();frequency=new Param();Q=new Param();pan=new Param();playbackRate=new Param();connect(){}disconnect(){}start(){this.started=true;}stop(t){this.stopAt=t;}}
class Context {
  state='suspended';currentTime=0;sampleRate=8000;destination=new Node();sources=[];gains=[];
  createBuffer(channels,length){const data=new Float32Array(length);return {getChannelData:()=>data};}
  createGain(){const n=new Node();this.gains.push(n);return n;}createBiquadFilter(){return new Node();}createStereoPanner(){return new Node();}
  createBufferSource(){const n=new Node();this.sources.push(n);return n;}
  async resume(){this.state='running';}async suspend(){this.state='suspended';}async close(){this.state='closed';}
}
let created=0,loaded=0;const ctx=new Context();
const audio=createRoomAudio({createContext:()=>{created++;return ctx;},loadSample:async kind=>{loaded++;return {kind};}});
const state={curtain:0,doors:[{id:'wardrobeLeft',amount:0,blocked:false}],water:{shower:false,faucet:false},position:{x:0,y:1.5,z:0},yaw:0};
const step=()=>audio.update(.05,state);
audio.setActive(true);state.water.shower=true;step();audio.interaction('light');
assert.equal(created,0,'Entering/operating a muted room must not even create audio');
assert.equal(loaded,0,'Muted visitors must not download recordings');
assert.equal(audio.muted,true);
await audio.setMuted(false);step();
assert.equal(created,1);assert.deepEqual(audio.state.loops,['shower']);
assert.equal(loaded,4);
for(let i=0;i<60;i++)step();assert.equal(ctx.sources.length,1,'Continuous water reuses a single source');
state.water.faucet=true;step();assert.equal(audio.state.loops.length,2);
assert.notEqual(ctx.sources[0].buffer,ctx.sources[1].buffer,'Faucet and shower must use distinct recordings');
state.curtain=.1;state.doors[0].amount=.1;step();
assert.ok(audio.state.loops.includes('curtain'));assert.ok(audio.state.loops.includes('wardrobeLeft'));
const creak=ctx.sources.find(s=>s.buffer.kind==='wardrobeOpen');
assert.equal(creak.loop,false,'Cabinet uses one short gesture, not a repeating squeal');
const sourceCount=ctx.sources.length;creak.onended();
for(let i=0;i<8;i++){state.doors[0].amount+=.01;step();}
assert.equal(ctx.sources.length,sourceCount,'A finished creak must not retrigger while the same motion continues');
state.doors[0].blocked=true;step();assert.ok(!audio.state.loops.includes('wardrobeLeft'));
assert.ok(!audio.state.loops.includes('curtain'),'Still cloth must become quiet');
state.doors[0].blocked=false;state.doors[0].amount=.8;step();state.doors[0].amount=.3;step();
assert.ok(!ctx.sources.some(s=>s.buffer.kind==='wardrobeClose'),'Do not play the latch while door is wide open');
state.doors[0].amount=.15;step();
const close=ctx.sources.find(s=>s.buffer.kind==='wardrobeClose');assert.ok(close);assert.equal(close.loop,false);
assert.notEqual(close.buffer,creak.buffer,'Opening and closing use different sections of the supplied recording');
state.doors[0].amount=0;step();assert.equal(audio.state.transients,0,'Do not add a synthesized impact over the recorded closing sound');
assert.equal(close.stopAt,undefined,'Let the recorded closing tail finish naturally');
close.onended();assert.ok(!audio.state.loops.includes('wardrobeLeft'));
state.doors[0].amount=.2;step();const openingAgain=ctx.sources.at(-1);
assert.equal(openingAgain.buffer.kind,'wardrobeOpen');
state.doors[0].amount=.1;step();assert.notEqual(openingAgain.stopAt,undefined,'Reversing stops the previous opening sound');
state.doors[0].amount=.02;step();assert.equal(ctx.sources.at(-1).buffer.kind,'wardrobeClose');
await audio.setMuted(true);assert.equal(ctx.state,'suspended');assert.deepEqual(audio.state.loops,[]);
audio.interaction('doorLock');assert.equal(audio.state.transients,0);
await audio.setMuted(false);step();assert.deepEqual(audio.state.loops,['shower','faucet']);
assert.equal(loaded,4,'Reuse decoded recordings after muting');
audio.setActive(false);assert.equal(ctx.state,'suspended');assert.deepEqual(audio.state.loops,[]);
audio.setActive(true);await Promise.resolve();step();assert.equal(audio.state.loops.length,2,'Returning restores currently running water');
state.water.shower=false;state.water.faucet=false;step();assert.equal(audio.state.loops.length,0);
audio.interaction('light');const lightPeak=ctx.gains.at(-1).gain.peak;
audio.interaction('doorLock');assert.ok(ctx.gains.at(-1).gain.peak>lightPeak*2,'Door lock click is distinctly louder without raising other switches');
for(let i=0;i<30;i++)audio.interaction('light');assert.ok(audio.state.transients<=8,'Repeated input stays bounded');
audio.dispose();assert.equal(ctx.state,'closed');assert.equal(audio.muted,true);
const unavailable=createRoomAudio({createContext:()=>null});unavailable.setActive(true);
assert.equal(await unavailable.setMuted(false),false);assert.equal(unavailable.muted,true);
let fail=true;
const retry=createRoomAudio({createContext:()=>new Context(),loadSample:async()=>{if(fail)throw Error('offline');return {};}});
retry.setActive(true);assert.equal(await retry.setMuted(false),false);assert.equal(retry.muted,true);
fail=false;assert.equal(await retry.setMuted(false),true);retry.dispose();
// PCM has no encoder delay. Inspect every 50 ms window and the wrap seam.
for(const kind of ['faucet','shower','wardrobe-open','wardrobe-close']){
  const cabinet=kind.startsWith('wardrobe');
  const filename=cabinet?`${kind}.wav`:`${kind}-loop.wav`;
  const wav=fs.readFileSync(new URL(`../room-site/dist/assets/audio/${filename}`,import.meta.url));
  assert.equal(wav.toString('ascii',0,4),'RIFF');assert.equal(wav.readUInt16LE(22),1);assert.equal(wav.readUInt32LE(24),24000);
  const pcm=[];for(let i=44;i<wav.length;i+=2)pcm.push(wav.readInt16LE(i));
  assert.ok(pcm.every(x=>Math.abs(x)<30000),'No clipped samples');
  const diffs=pcm.slice(1).map((x,i)=>Math.abs(x-pcm[i])).sort((a,b)=>a-b);
  if(!cabinet)assert.ok(Math.abs(pcm[0]-pcm.at(-1))<=diffs[Math.floor(diffs.length*.99)],'Wrap must not introduce an isolated click');
  const wholeRms=Math.sqrt(pcm.reduce((sum,x)=>sum+x*x,0)/pcm.length);
  if(cabinet){
    assert.ok(pcm.length/24000<1.6,'Exclude the gap between the original actions');
    assert.ok(Math.abs(pcm[0])<10&&Math.abs(pcm.at(-1))<10,'Quiet cut edges');
    assert.ok(wholeRms>300&&wholeRms<3400,'Both supplied actions must remain audible, with original restrained levels');
  }
  if(!cabinet)for(let i=0;i<pcm.length-1200;i+=1200){
    const rms=Math.sqrt(pcm.slice(i,i+1200).reduce((sum,x)=>sum+x*x,0)/1200);
    assert.ok(rms>wholeRms*.1,'Water must not drop more than 20 dB below its average into a quiet gap');
  }
}
console.log('PASS audio: opt-in recordings, distinct continuous water, PCM wrap seams, bounded sources, lifecycle and download retry.');
