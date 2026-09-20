// CC0 recorded water loops and one-shot wood foley, fetched only after opt-in.
// Cloth and small clicks remain synthesized. No autoplay or saved opt-in.
// Motion follows authored animation, so blocked doors and stopped curtains are silent.
const positions={curtain:[0,1.6,-1.9],wardrobeLeft:[-1.2,1.2,-.9],wardrobeMiddle:[-1.2,1.2,-.4],wardrobeRight:[-1.2,1.2,.1],shower:[-.95,1.4,2.65],faucet:[-.065,.89,2.986],doorLock:[1.5,1.05,2.6],light:[1.4,1.3,2.3]};
const profiles={curtain:[950,.55,.36],wardrobe:[1800,.5,.30],shower:[7500,.5,.72],faucet:[6800,.5,.7]};
export function createRoomAudio({createContext=()=>{const Audio=globalThis.AudioContext||globalThis.webkitAudioContext;return Audio?new Audio({latencyHint:'interactive'}):null;},loadSample=async(kind,ctx)=>{
  const file=kind==='wardrobe'?'wardrobe-soft.wav':`${kind}-loop.wav`;
  const response=await fetch(new URL(`./assets/audio/${file}`,import.meta.url));
  if(!response.ok)throw new Error(`Room audio ${response.status}`);
  return ctx.decodeAudioData(await response.arrayBuffer());
},onChange=()=>{}}={}){
  let context=null,master=null,buffer=null,muted=true,active=false,disposed=false,serial=0;
  let listener={x:0,y:1.5,z:0,yaw:0},previous=null,pending=0;
  const loops=new Map(),shots=new Set();
  const samples=new Map();let samplePromise=null;
  function loadRecordings(){
    if(!samplePromise)samplePromise=Promise.all(['wardrobe','shower','faucet'].map(async kind=>{
      if(!samples.has(kind))samples.set(kind,await loadSample(kind,context));
    })).catch(error=>{samplePromise=null;throw error;});
    return samplePromise;
  }
  const audible=()=>!!context&&!muted&&active&&!disposed&&context.state==='running';
  const notify=()=>onChange(muted);
  function ramp(param,value,time=.05){param.setTargetAtTime(value,context.currentTime,time);}
  function createNoise(){
    const rate=context.sampleRate,length=rate*4,result=context.createBuffer(1,length,rate),data=result.getChannelData(0);
    let smooth=0;
    for(let i=0;i<length;i++){
      const white=Math.random()*2-1;smooth=.965*smooth+.035*white;
      // Slow, seamless amplitude variation avoids a static white-noise hiss.
      const phase=i/length*Math.PI*2;
      data[i]=(.68*white+2.2*smooth)*(.77+.13*Math.sin(phase*7)+.1*Math.sin(phase*19));
    }return result;
  }
  function spatial(voice,position){
    const [x,y,z]=position,dx=x-listener.x,dz=z-listener.z,distance=Math.hypot(dx,y-listener.y,dz);
    const pan=(dx*Math.cos(listener.yaw)-dz*Math.sin(listener.yaw))/Math.max(1,distance);
    ramp(voice.pan.pan,Math.max(-.8,Math.min(.8,pan)),.08);
    return 1/(1+.28*distance*distance);
  }
  function voice(frequency,q,kind=null){
    const source=context.createBufferSource(),filter=context.createBiquadFilter(),gain=context.createGain(),pan=context.createStereoPanner();
    const sample=samples.get(kind);
    source.buffer=sample||buffer;source.loop=kind!=='wardrobe';filter.type=sample?'lowpass':'bandpass';filter.frequency.value=frequency;filter.Q.value=q;gain.gain.value=0;
    source.connect(filter);filter.connect(gain);gain.connect(pan);pan.connect(master);source.start(0,sample?0:Math.random()*3);
    const v={source,filter,gain,pan,stopped:false};
    source.onended=()=>{for(const n of [source,filter,gain,pan])n.disconnect();shots.delete(v);};
    return v;
  }
  function stop(voice,immediate=false){
    if(voice.stopped)return;voice.stopped=true;
    if(immediate){voice.gain.gain.cancelScheduledValues(context.currentTime);voice.gain.gain.setValueAtTime(0,context.currentTime);}
    else ramp(voice.gain.gain,0,.025);
    voice.source.stop(context.currentTime+(immediate?0:.18));
  }
  function silence(){for(const v of loops.values())stop(v,true);loops.clear();for(const v of shots)stop(v,true);shots.clear();previous=null;pending=0;}
  function sync(){
    if(!context)return;
    master.gain.cancelScheduledValues(context.currentTime);master.gain.setValueAtTime(0,context.currentTime);
    if(muted||!active||disposed){silence();void context.suspend().catch(()=>{});}
    else {void context.resume().then(()=>{if(audible())ramp(master.gain,.65,.045);}).catch(()=>{muted=true;silence();notify();});}
  }
  async function setMuted(next){
    const request=++serial;muted=!!next;notify();
    if(muted){sync();return true;}
    try{
      if(disposed)throw new Error('Audio disposed');
      if(!context){context=createContext();if(!context)throw new Error('Web Audio unavailable');master=context.createGain();master.gain.value=0;master.connect(context.destination);buffer=createNoise();}
      // Called directly by the sound button's user gesture, including on iOS.
      if(active)await context.resume();
      await loadRecordings();
      if(request!==serial||disposed)return true;
      if(active&&context.state!=='running')throw new Error('Audio could not start');
      sync();return true;
    }catch{if(request===serial){muted=true;sync();notify();}return false;}
  }
  function setActive(value){value=!!value;if(active===value)return;active=value;sync();}
  function impact(id,heavy=false){
    if(!audible())return;
    // Bound transient voices during repeated clicks.
    if(shots.size>=8){const old=shots.values().next().value;stop(old,true);shots.delete(old);}
    const v=voice(heavy?150:1800,heavy?.8:1.2);shots.add(v);
    const now=context.currentTime,level=(heavy?.58:.16)*spatial(v,positions[id]||positions.light);
    v.gain.gain.setValueAtTime(0,now);v.gain.gain.linearRampToValueAtTime(level,now+.008);v.gain.gain.exponentialRampToValueAtTime(.0001,now+(heavy?.23:.065));
    v.source.stop(now+(heavy?.28:.09));
  }
  function interaction(id){if(['light','doorLock','shower','faucet'].includes(id))impact(id);}
  function sustain(id,kind,amount){
    let v=loops.get(id);
    if(amount<.002){if(v){stop(v);loops.delete(id);}return;}
    const [frequency,q,level]=profiles[kind];
    if(kind!=='curtain'&&!samples.has(kind))return;
    if(!v){v=voice(frequency,q,kind);loops.set(id,v);}
    // Keep a completed cabinet voice until motion stops, so it cannot retrigger
    // every frame. Natural pitch stays fixed instead of sweeping with door speed.
    ramp(v.gain.gain,level*(kind==='wardrobe'?Math.sqrt(Math.min(1,amount)):Math.min(1,amount))*spatial(v,positions[id]),.055);
  }
  function update(dt,{curtain,doors,water,position,yaw}){
    if(!audible()){previous=null;pending=0;return;}
    pending+=dt;if(pending<.05)return;dt=pending;pending=0;
    listener={x:position.x,y:position.y,z:position.z,yaw};
    const current={curtain,doors:doors.map(d=>d.amount)};
    sustain('shower','shower',water.shower?1:0);sustain('faucet','faucet',water.faucet?1:0);
    const elapsed=Math.max(.016,dt);
    sustain('curtain','curtain',previous?Math.min(1,Math.abs(curtain-previous.curtain)/elapsed)*.9:0);
    doors.forEach((d,i)=>{
      const before=previous?.doors[i]??d.amount,speed=d.blocked?0:Math.abs(d.amount-before)/elapsed;
      sustain(d.id,'wardrobe',Math.min(1,speed));
      if(before>0&&d.amount===0)impact(d.id,true);
    });
    previous=current;
  }
  function dispose(){disposed=true;serial++;muted=true;silence();void context?.close().catch(()=>{});notify();}
  notify();
  return {setMuted,setActive,interaction,update,dispose,get muted(){return muted;},get state(){return {muted,active,context:context?.state||'not-created',recordings:samples.size,loops:[...loops.keys()],transients:shots.size};}};
}
