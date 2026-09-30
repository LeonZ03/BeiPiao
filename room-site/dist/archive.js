import {startRoomLoading,failRoomLoading} from './room-loading.js?v=viewer26';
const archive=document.getElementById('archive'),app=document.getElementById('app');
const directory=document.getElementById('directoryDialog');
const courtyard=document.getElementById('courtyardRoom');
const roomCover=document.getElementById('archiveCover'),roomNumber=document.getElementById('roomNumber'),roomTitle=document.getElementById('roomTitle'),enterRoom=document.getElementById('enterRoomBtn');
const roomChoices=[...document.querySelectorAll('[data-room-select]')];
let roomPromise,roomModule,routeVersion=0;
let courtyardCreated=false;
const rooms={
  'yongwang-jiayuan':{number:'ROOM 01',title:'永旺家园',hash:'#room',cover:'./assets/archive-hero.png',alt:'永旺家园的房间展示图，依据定稿中的衣柜、窗帘、床铺与书桌构图'},
  Courtyard43:{number:'ROOM 02',title:'43号院',hash:'#courtyard43',cover:'./assets/archive-courtyard43.jpg',alt:'冬日雪景中的43号院'}
};
function selectRoom(id){
  const room=rooms[id];if(!room)return;
  roomNumber.textContent=room.number;roomTitle.textContent=room.title;roomCover.src=room.cover;roomCover.alt=room.alt;enterRoom.href=room.hash;
  for(const choice of roomChoices){const selected=choice.dataset.roomSelect===id;choice.setAttribute('aria-pressed',String(selected));choice.closest('li')?.classList.toggle('current',selected);}
}
for(const choice of roomChoices)choice.addEventListener('click',()=>{
  selectRoom(choice.dataset.roomSelect);
  if(choice.closest('dialog')===directory){directory.close();enterRoom.focus({preventScroll:true});}
});
function syncCourtyard(){if(courtyardCreated)courtyard.contentWindow?.postMessage({type:'beipiao-room-active',active:!courtyard.hidden},location.origin);}
courtyard.addEventListener('load',syncCourtyard);
window.addEventListener('message',event=>{
  if(event.origin===location.origin&&event.source===courtyard.contentWindow&&event.data?.type==='beipiao-room-home'&&location.hash==='#courtyard43')location.hash='#';
});
document.getElementById('directoryBtn').onclick=()=>directory.showModal();
document.getElementById('closeDirectoryBtn').onclick=()=>directory.close();
directory.addEventListener('click',e=>{if(e.target===directory){const r=directory.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)directory.close();}});
for(const event of ['selectstart','dragstart','contextmenu'])archive.addEventListener(event,e=>e.preventDefault());
async function route(){
  const version=++routeVersion,view=location.hash==='#overview'?'overview':location.hash==='#room'?'walk':null;
  if(location.hash==='#courtyard43')selectRoom('Courtyard43');else if(view)selectRoom('yongwang-jiayuan');
  directory.close();
  const isCourtyard=location.hash==='#courtyard43';
  // A fullscreen child must leave the top layer before the archive can return.
  if(!isCourtyard&&document.fullscreenElement===courtyard){try{await document.exitFullscreen();}catch{}}
  if(version!==routeVersion)return;
  courtyard.hidden=!isCourtyard;syncCourtyard();
  if(isCourtyard){
    roomModule?.pauseRoom();app.hidden=true;archive.hidden=true;document.title='43号院 · 北漂';
    if(!courtyardCreated){courtyardCreated=true;courtyard.src='./courtyard43.html?embedded=1&v=memory12';}
    courtyard.focus({preventScroll:true});return;
  }
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
    if(!roomPromise){startRoomLoading();roomPromise=import('./main.js?v=session39');}
    roomModule=await roomPromise;
    if(version===routeVersion){roomModule.enterRoom(view);document.getElementById('world').focus({preventScroll:true});}
  }catch(error){if(version===routeVersion)failRoomLoading();console.error('Room could not load',error);}
}
window.addEventListener('hashchange',route);
route();
