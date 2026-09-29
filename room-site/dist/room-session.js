// A room document remains alive while the archive hides it. Only the trusted
// same-origin parent can change its activity; no assets or viewer are recreated.
export function createRoomSession({window:win=window,document:doc=document}={}){
  const embedded=win.parent!==win;
  let active=!embedded||!win.frameElement?.hidden,listener=()=>{};
  win.addEventListener('message',event=>{
    if(!embedded||event.source!==win.parent||event.origin!==win.location.origin||event.data?.type!=='beipiao-room-active')return;
    active=event.data.active===true;listener(active);
  });
  function home(event){
    if(!embedded)return;
    event.preventDefault();active=false;listener(false);
    win.parent.postMessage({type:'beipiao-room-home'},win.location.origin);
  }
  for(const link of doc.querySelectorAll('#archiveHomeBtn,.loading-back'))link.addEventListener('click',home);
  return {get active(){return active;},get embedded(){return embedded;},subscribe(fn){listener=fn;fn(active);}};
}
