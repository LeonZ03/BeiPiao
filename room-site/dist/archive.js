import {startRoomLoading,failRoomLoading} from './room-loading.js?v=viewer26';
const archive=document.getElementById('archive'),app=document.getElementById('app');
const directory=document.getElementById('directoryDialog');
let roomPromise,roomModule,routeVersion=0;
document.getElementById('directoryBtn').onclick=()=>directory.showModal();
document.getElementById('closeDirectoryBtn').onclick=()=>directory.close();
directory.addEventListener('click',e=>{if(e.target===directory){const r=directory.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)directory.close();}});
for(const event of ['selectstart','dragstart','contextmenu'])archive.addEventListener(event,e=>e.preventDefault());
async function route(){
  const version=++routeVersion,view=location.hash==='#overview'?'overview':location.hash==='#room'?'walk':null;
  directory.close();
  if(!view){
    roomModule?.pauseRoom();
    // A legacy app-only fullscreen element must leave the top layer before it
    // is hidden; otherwise it can intercept the archive's entry links.
    if(document.fullscreenElement===app){try{await document.exitFullscreen();}catch{}}
    if(version!==routeVersion)return;
    app.hidden=true;archive.hidden=false;document.title='北漂 · 居住记录';return;
  }
  archive.hidden=true;app.hidden=false;document.title='永旺家园 · 北漂';
  try{
    if(!roomPromise){startRoomLoading();roomPromise=import('./main.js?v=wardrobe29b');}
    roomModule=await roomPromise;
    if(version===routeVersion){roomModule.enterRoom(view);document.getElementById('world').focus({preventScroll:true});}
  }catch(error){if(version===routeVersion)failRoomLoading();console.error('Room could not load',error);}
}
window.addEventListener('hashchange',route);
route();
