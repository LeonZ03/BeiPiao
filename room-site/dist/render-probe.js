// Local acceptance probe. No UI, network traffic or persistent camera changes.
export function createRenderProbe(){
  let run=null;
  const percentile=(a,p)=>a.slice().sort((x,y)=>x-y)[Math.floor((a.length-1)*p)]??0;
  return {
    start(camera){
      if(run)throw new Error('A rendering measurement is already running');
      return new Promise(resolve=>{run={camera,rotation:camera.rotation.clone(),start:0,last:0,frames:[],resolve};});
    },
    update(now,active){
      if(!run)return false;
      const r=run;
      if(!active){r.camera.rotation.copy(r.rotation);run=null;r.resolve({cancelled:true});return false;}
      if(!r.start)r.start=now;
      const elapsed=now-r.start;
      if(r.last&&elapsed>1000)r.frames.push(now-r.last);
      r.last=now;
      r.camera.rotation.copy(r.rotation);r.camera.rotation.y+=.12*Math.sin(elapsed/1000*1.4);
      if(elapsed<5500)return true;
      r.camera.rotation.copy(r.rotation);run=null;
      r.resolve({samples:r.frames.length,meanFrameMs:r.frames.reduce((a,b)=>a+b,0)/Math.max(1,r.frames.length),medianFrameMs:percentile(r.frames,.5),p90FrameMs:percentile(r.frames,.9),method:'5.5 second camera sweep; first second excluded; rAF intervals, not CPU submission time'});
      return true;
    }
  };
}
