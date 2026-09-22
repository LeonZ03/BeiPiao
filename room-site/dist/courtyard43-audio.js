// Courtyard43 has no evidenced water fixtures. Only the two existing, user-
// supplied cabinet gestures are fetched, after the sound button is pressed.
const recordings={open:'wardrobe-open.wav',close:'wardrobe-close.wav'};
export function createCourtyardAudio({createContext=()=>{const C=globalThis.AudioContext||globalThis.webkitAudioContext;return C?new C({latencyHint:'interactive'}):null;},loadSample=async(kind,context)=>{
  const response=await fetch(new URL(`./assets/audio/${recordings[kind]}`,import.meta.url));
  if(!response.ok)throw Error(`Room audio ${response.status}`);
  return context.decodeAudioData(await response.arrayBuffer());
},onChange=()=>{}}={}){
  let context=null,master=null,noise=null,muted=true,active=false,disposed=false,serial=0,loading=null;
  let listener={x:0,y:1.5,z:0,yaw:0};
  const samples=new Map(),voices=new Map(),shots=new Set(),motions=new Map();
  const audible=()=>context&&!muted&&active&&!disposed&&context.state==='running';
  const notify=()=>onChange(muted);
  const ramp=(param,value,time=.045)=>param.setTargetAtTime(value,context.currentTime,time);
  function noiseBuffer(){const length=context.sampleRate*2,b=context.createBuffer(1,length,context.sampleRate),p=b.getChannelData(0);let smoothed=0;for(let i=0;i<length;i++){const v=Math.random()*2-1;smoothed=.96*smoothed+.04*v;p[i]=(.6*v+2*smoothed)*(.85+.15*Math.sin(i/length*Math.PI*14));}return b;}
  function spatial(v,position){const [x,y,z]=position||[.4,1.5,.1],dx=x-listener.x,dz=z-listener.z,distance=Math.hypot(dx,y-listener.y,dz);ramp(v.pan.pan,Math.max(-.8,Math.min(.8,(dx*Math.cos(listener.yaw)-dz*Math.sin(listener.yaw))/Math.max(1,distance))),.08);return 1/(1+.28*distance*distance);}
  function voice(kind){const source=context.createBufferSource(),filter=context.createBiquadFilter(),gain=context.createGain(),pan=context.createStereoPanner();source.buffer=samples.get(kind)||noise;source.loop=kind==='cloth';filter.type=kind==='cloth'?'bandpass':'lowpass';filter.frequency.value=kind==='cloth'?950:11000;filter.Q.value=.65;gain.gain.value=0;source.connect(filter);filter.connect(gain);gain.connect(pan);pan.connect(master);const v={source,filter,gain,pan,kind,stopped:false};source.onended=()=>{for(const n of [source,filter,gain,pan])n.disconnect();shots.delete(v);if(v.id&&voices.get(v.id)===v)voices.delete(v.id);};source.start(0,kind==='cloth'?Math.random():0);return v;}
  function stop(v,immediate=false){if(v.stopped)return;v.stopped=true;if(immediate){v.gain.gain.cancelScheduledValues(context.currentTime);v.gain.gain.setValueAtTime(0,context.currentTime);}else ramp(v.gain.gain,0,.025);v.source.stop(context.currentTime+(immediate?0:.15));}
  function silence(){for(const v of voices.values())stop(v,true);for(const v of shots)stop(v,true);voices.clear();shots.clear();motions.clear();}
  function sync(){if(!context)return;master.gain.cancelScheduledValues(context.currentTime);master.gain.setValueAtTime(0,context.currentTime);if(muted||!active||disposed){silence();void context.suspend().catch(()=>{});}else void context.resume().then(()=>{if(audible())ramp(master.gain,.65);}).catch(()=>{muted=true;silence();notify();});}
  async function setMuted(next){const request=++serial;muted=!!next;notify();if(muted){sync();return true;}try{if(disposed)throw Error('Disposed audio');if(!context){context=createContext();if(!context)throw Error('Web Audio unavailable');master=context.createGain();master.gain.value=0;master.connect(context.destination);noise=noiseBuffer();}if(active)await context.resume();if(!loading)loading=Promise.all(['open','close'].map(async k=>{if(!samples.has(k))samples.set(k,await loadSample(k,context));})).catch(error=>{loading=null;throw error;});await loading;if(request!==serial||disposed)return true;if(active&&context.state!=='running')throw Error('Audio suspended');sync();return true;}catch{if(request===serial){muted=true;sync();notify();}return false;}}
  function setActive(value){value=!!value;if(value===active)return;active=value;sync();}
  function setListener(position,yaw=0){listener={x:position.x,y:position.y,z:position.z,yaw};}
  function interaction(kind,position){if(!audible())return;if(shots.size>=8){const v=shots.values().next().value;stop(v,true);shots.delete(v);}const v=voice('click');v.source.loop=false;v.filter.type='bandpass';v.filter.frequency.value=kind==='lock'?1300:1800;shots.add(v);const now=context.currentTime,level=(kind==='lock'?.40:.16)*spatial(v,position);v.gain.gain.setValueAtTime(0,now);v.gain.gain.linearRampToValueAtTime(level,now+.008);v.gain.gain.exponentialRampToValueAtTime(.0001,now+.065);v.source.stop(now+.095);}
  function update(dt,{doors=[],curtainSpeed=0,curtainPosition=[.4,1.5,.07],position,yaw=0}){
    if(!audible())return;setListener(position,yaw);
    let cloth=voices.get('cloth');
    if(curtainSpeed>.001){if(!cloth){cloth=voice('cloth');cloth.id='cloth';voices.set('cloth',cloth);}ramp(cloth.gain.gain,.32*Math.min(1,curtainSpeed)*spatial(cloth,curtainPosition),.055);}else if(cloth){stop(cloth);voices.delete('cloth');}
    for(const door of doors){let v=voices.get(door.id),motion=motions.get(door.id);if(door.blocked){if(v)stop(v);voices.delete(door.id);motions.delete(door.id);continue;}if(v)ramp(v.gain.gain,.85*spatial(v,door.position),.055);if(!door.moving)continue;const direction=Math.sign(door.target-door.amount);if(!direction)continue;if(motion?.serial!==door.serial||motion?.direction!==direction){if(v)stop(v);voices.delete(door.id);motion={serial:door.serial,direction,played:false};motions.set(door.id,motion);}if(motion.played||(direction<0&&door.amount>.18))continue;const kind=direction>0?'open':'close';if(!samples.has(kind))continue;motion.played=true;v=voice(kind);v.id=door.id;voices.set(door.id,v);ramp(v.gain.gain,.85*spatial(v,door.position),.008);}
  }
  function dispose(){disposed=true;serial++;muted=true;silence();void context?.close().catch(()=>{});notify();}
  notify();return {setMuted,setActive,setListener,interaction,update,dispose,get muted(){return muted;},get state(){return{muted,active,context:context?.state||'not-created',recordings:samples.size,voices:[...voices.keys()],transients:shots.size};}};
}
