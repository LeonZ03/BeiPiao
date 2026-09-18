// Progress follows resource completion and scene preparation, never a timer.
const panel=document.getElementById('loading');
const bar=document.getElementById('roomLoadProgress');
const value=document.getElementById('roomLoadValue');
const status=document.getElementById('roomLoadStatus');
let progress=0;
export function startRoomLoading(){
  progress=0;panel.hidden=false;document.getElementById('error').hidden=true;
  document.getElementById('world').setAttribute('aria-busy','true');
  reportRoomLoading(0,'正在打开房间');
}
export function reportRoomLoading(next,label){
  progress=Math.max(progress,Math.min(100,Math.round(next)));
  bar.value=progress;value.textContent=progress+'%';
  if(label)status.textContent=label;
}
export const nextPaint=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
export async function finishRoomLoading(){
  reportRoomLoading(100,'房间已就绪');await nextPaint();
  panel.hidden=true;document.getElementById('world').removeAttribute('aria-busy');
}
export function failRoomLoading(){
  panel.hidden=true;document.getElementById('world').removeAttribute('aria-busy');
  document.getElementById('error').hidden=false;
}
