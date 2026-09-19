import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {Reflector} from './vendor/Reflector.js';
import {createAfternoon} from './afternoon.js?v=wardrobe30';
import {installSoftSunShadows,createSoftDaylight} from './soft-daylight.js?v=exterior31f';
import {createFlyNavigation,batchStaticGeometry} from './navigation.js?v=wardrobe29b';
import {createInteractions} from './interactions.js?v=wardrobe29b';
import {loadBlenderRoom} from './blender-room.js?v=exterior31f';
import {reportRoomLoading,finishRoomLoading,nextPaint} from './room-loading.js?v=viewer26';
import {createCurtainController} from './curtain.js?v=curtain23d';
import {createRoomBreeze} from './room-breeze.js?v=breeze28';
import {createWardrobe} from './wardrobe.js?v=wardrobe30';
import {createRenderProbe} from './render-probe.js?v=exterior31f';

const $ = (id) => document.getElementById(id);
const canvas = $('world');
for(const event of ['selectstart','dragstart','contextmenu'])$('app').addEventListener(event,e=>e.preventDefault());
const touchQuery=matchMedia('(pointer: coarse)');
const updateTouch=()=> $('app').classList.toggle('touch-device',touchQuery.matches||innerWidth<=900);updateTouch();touchQuery.addEventListener('change',updateTouch);window.addEventListener('resize',updateTouch);
window.addEventListener('blur',()=>document.querySelectorAll('.held').forEach(b=>b.classList.remove('held')));
let renderer;
try { renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'}); }
catch(e) { $('loading').hidden=true; $('error').hidden=false; throw e; }
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.35));
renderer.setSize(innerWidth,innerHeight,false);
renderer.shadowMap.enabled=true;
installSoftSunShadows(THREE);
renderer.shadowMap.type=THREE.PCFShadowMap;
renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.0;
const gl=renderer.getContext?.(),gpuInfo=gl?.getExtension('WEBGL_debug_renderer_info');
const graphicsDevice=gpuInfo?gl.getParameter(gpuInfo.UNMASKED_RENDERER_WEBGL):'浏览器未公开显卡名称';
const scene=new THREE.Scene();scene.background=new THREE.Color('#c9d2cd');
const camera=new THREE.PerspectiveCamera(62,innerWidth/innerHeight,.003,80);
camera.rotation.order='YXZ';

let renderSignature='',curtainOpen=false,curtainAmount=0;
const manager=new THREE.LoadingManager();
let roomAsset;
try {roomAsset=await loadBlenderRoom(THREE,manager,reportRoomLoading);}
catch(error){$('loading').hidden=true;$('error').hidden=false;throw error;}
const {world,materials,statistics:assetStatistics}=roomAsset;
const {outside,curtain,curtainPanels,curtainRings,diffuser,cutaway,ceilings}=roomAsset.refs;
scene.add(world);
const indirectMaterials=materials.filter(m=>m.userData.bakedIndirect);
const updateIndirect=amount=>indirectMaterials.forEach(m=>m.lightMapIntensity=.17+.29*amount);
const {windowLight,sun,setCurtainLight}=createAfternoon({THREE,scene,renderer,world});
const updateCurtain=createCurtainController(curtainPanels,curtainRings);
const wardrobe=createWardrobe({THREE,world,camera,renderer,Reflector,refs:roomAsset.refs,toast});
const breeze=createRoomBreeze({THREE,world,camera});
const daylight=createSoftDaylight({THREE,renderer,scene,camera,sun,breeze});
const lamp=new THREE.PointLight('#ffdca5',0,6,2);lamp.position.set(0,2.35,.05);scene.add(lamp);
const bathLight=new THREE.PointLight('#f0f5ed',3.3,4,2);bathLight.position.set(-.55,2.30,2.48);scene.add(bathLight);
const navigation=createFlyNavigation(THREE,world,[outside,curtain]);
const batchedMeshes=batchStaticGeometry(THREE,world,[curtain,...cutaway,...ceilings]);
renderer.shadowMap.needsUpdate=true;
reportRoomLoading(95,'正在准备光影');await nextPaint();
const orbit=new OrbitControls(camera,canvas);orbit.enabled=false;orbit.enableDamping=true;orbit.minDistance=3;orbit.maxDistance=12;orbit.maxPolarAngle=Math.PI*.46;orbit.target.set(-.3,.65,.7);
let mode='walk',yaw=.12,pitch=-.08,locked=false,drag=null,lightOn=false;
const keys=new Set();let last=performance.now();let toastTimer;
const viewpoints={wardrobe:{p:[.45,1.30,-1.03],yaw:Math.PI/2,pitch:-.06,label:'衣柜正面'},chair:{p:[1.0,1.10,.08],yaw:.47,pitch:-.44,label:'椅子细节'},rackets:{p:[-.93,1.35,.78],yaw:.012,pitch:-.035,label:'球拍网线'},gundam:{p:[.79,1.80,-.505],yaw:-Math.PI/2,pitch:-.085,label:'高达细节'},paperCup:{p:[.84,1.75,-.89],yaw:-Math.PI/2,pitch:-.13,label:'纸杯图案'},shelf:{p:[.35,1.84,-.71],yaw:-Math.PI/2,pitch:-.16,label:'桌架摆件'},mug:{p:[.59,1.05,-1.115],yaw:-1.405,pitch:-.54,label:'杯子细节'},radiator:{p:[.50,.71,-1.10],yaw:-1.3,pitch:-.2,label:'暖气位置'},ac:{p:[.54,2.21,-.71],yaw:-Math.PI/2,pitch:.08,label:'空调细节'},tabletop:{p:[.52,1.20,-.52],yaw:-Math.PI/2,pitch:-.64,label:'桌面细节'},basket:{p:[.62,1.53,-.43],yaw:-Math.PI/2,pitch:.03,label:'花篮细节'},doorframe:{p:[.93,2.05,2.67],yaw:-Math.PI/2,pitch:.25,label:'门框细节'},grille:{p:[.34,1.73,-1.49],yaw:-.63,pitch:0,label:'窗栏细节'},helmetSide:{p:[-.42,2.33,-.95],yaw:Math.PI/2,pitch:-.045,label:'头盔侧面'},helmet:{p:[-.48,2.35,-.29],yaw:.72,pitch:-.07,label:'头盔细节'},pillow:{p:[.27,1.10,1.0],yaw:1.88,pitch:-.40,label:'枕头细节'},shower:{p:[.20,1.40,2.82],yaw:.98,pitch:-.035,label:'花洒细节'},lock:{p:[1.05,1.03,2.38],yaw:-1.48,pitch:-.075,label:'反锁旋钮'},entry:{p:[.92,1.56,2.77],yaw:.08,pitch:-.09,label:'入口过道'},bed:{p:[.48,1.30,.45],yaw:.22,pitch:-.04,label:'床边'},desk:{p:[.42,1.50,-.05],yaw:-1.05,pitch:-.26,label:'书桌'},window:{p:[-.25,1.56,-1.27],yaw:.02,pitch:.02,label:'窗边'},yard:{p:[-.38,1.63,-1.75],yaw:-.83,pitch:-.87,label:'窗边 · 楼下'},closet:{p:[.42,1.54,.55],yaw:.98,pitch:0,label:'衣柜'},door:{p:[.51,1.50,2.70],yaw:-Math.PI/2,pitch:.05,label:'门上细节'},toilet:{p:[-.50,1.15,2.12],yaw:Math.PI-.24,pitch:-.55,label:'洁具细节'},bath:{p:[.04,1.645,2.43],yaw:Math.PI/2,pitch:-.20,label:'卫生间'}};
function toast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),3600);}
function setMode(next){mode=next;camera.near=next==='overview'?.05:.003;camera.updateProjectionMatrix();keys.clear();document.querySelectorAll('.held').forEach(b=>b.classList.remove('held'));$('interactionHint').hidden=true;renderer.shadowMap.needsUpdate=true;const overview=mode==='overview';orbit.enabled=overview;cutaway.forEach(o=>o.visible=!overview);ceilings.forEach(o=>o.visible=!overview);outside.visible=!overview;$('walkBtn').classList.toggle('active',!overview);$('overviewBtn').classList.toggle('active',overview);$('walkBtn').setAttribute('aria-pressed',String(!overview));$('overviewBtn').setAttribute('aria-pressed',String(overview));$('app').classList.toggle('overview',overview);if(overview){if(document.pointerLockElement)document.exitPointerLock();camera.position.set(5.5,6.1,7.0);orbit.target.set(-.25,.7,.8);orbit.update();scene.background.set('#dfe3dc');}else{scene.background.set('#e5ebe5');goTo('entry',false);}}
function goTo(name,switchMode=true){$('interactionHint').hidden=true;if(switchMode&&mode!=='walk')setMode('walk');const v=viewpoints[name];camera.position.set(...v.p);yaw=v.yaw;pitch=v.pitch;camera.rotation.set(pitch,yaw,0,'YXZ');}
goTo('entry');
// Begin just inside the bedroom, where the sunlit bedding and the window can be
// appreciated together. The entrance shortcut retains the original doorway view.
camera.position.set(.83,1.48,1.66);yaw=.20;pitch=-.20;camera.rotation.set(pitch,yaw,0,'YXZ');
function canStand(x,z,y=camera.position.y){return navigation.canTravel(camera.position,new THREE.Vector3(x,y,z));}
function moveVertical(dy){if(!dy)return;const target=camera.position.clone();target.y+=dy;if(navigation.canTravel(camera.position,target))camera.position.copy(target);}
function move(dx,dz){
  const target=camera.position.clone();target.x+=dx;if(dx&&navigation.canTravel(camera.position,target))camera.position.x=target.x;
  target.copy(camera.position);target.z+=dz;if(dz&&navigation.canTravel(camera.position,target))camera.position.z=target.z;
}
const interactions=createInteractions({THREE,world,camera,canvas,curtain,toggleCurtain,toggleLight,wardrobe,toast,hint:$('interactionHint')});
let lastHover=0;
canvas.addEventListener('pointerdown',e=>{if(mode!=='walk')return;canvas.focus();drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,id:e.pointerId,moved:false};canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{
  if(mode!=='walk')return;
  if(locked){yaw-=e.movementX*.002;pitch-=e.movementY*.002;}
  else if(drag&&drag.id===e.pointerId){if(Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)>5)drag.moved=true;if(drag.moved){yaw-=(e.clientX-drag.x)*.004;pitch-=(e.clientY-drag.y)*.003;}drag.x=e.clientX;drag.y=e.clientY;}
  pitch=THREE.MathUtils.clamp(pitch,-1.5,1.5);
  if(!drag&&performance.now()-lastHover>120){lastHover=performance.now();interactions.hover(e.clientX,e.clientY,locked);}
});
canvas.addEventListener('pointerup',e=>{if(drag&&!drag.moved&&mode==='walk'){const id=interactions.pick(e.clientX,e.clientY,locked);if(id)interactions.perform(id);}drag=null;});
canvas.addEventListener('pointercancel',()=>drag=null);
canvas.addEventListener('dblclick',()=>{if(mode==='walk')canvas.requestPointerLock?.()?.catch(()=>toast('可直接拖动画面环顾'));});
document.addEventListener('pointerlockchange',()=>{locked=document.pointerLockElement===canvas;$('crosshair').hidden=!locked;});
window.addEventListener('keydown',e=>{if($('app').hidden||document.querySelector('dialog[open]'))return;if(e.code==='KeyH'&&!e.repeat)toggleImmersive();if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight','ControlLeft','ControlRight'].includes(e.code)){e.preventDefault();keys.add(e.code);}});
window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',()=>{keys.clear();drag=null;});document.addEventListener('visibilitychange',()=>keys.clear());
for(const b of document.querySelectorAll('[data-move]')){const code={forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',up:'ShiftLeft',down:'ControlLeft'}[b.dataset.move];b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(code);b.classList.add('held');});for(const t of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(t,()=>{keys.delete(code);b.classList.remove('held');});}

function resetView(){if(mode==='overview')setMode('overview');else{goTo('entry');camera.position.set(.83,1.48,1.66);yaw=.20;pitch=-.20;camera.rotation.set(pitch,yaw,0,'YXZ');}}
$('walkBtn').onclick=()=>setMode('walk');$('overviewBtn').onclick=()=>setMode('overview');$('resetBtn').onclick=()=>{resetView();canvas.focus({preventScroll:true});};
function toggleCurtain(){curtainOpen=!curtainOpen;toast(curtainOpen?'正在拉开窗帘':'正在合上窗帘');}
function toggleLight(){lightOn=!lightOn;lamp.intensity=lightOn?7:0;diffuser.material.emissiveIntensity=lightOn?1.5:.1;const rocker=world.getObjectByName('light-switch-rocker');if(rocker)rocker.rotation.z=lightOn?.13:0;toast(lightOn?'房间灯已打开':'房间灯已关闭');}

let immersive=false;
function toggleImmersive(){immersive=!immersive;$('app').classList.toggle('immersive',immersive);$('immersiveBtn').textContent=immersive?'退出沉浸':'沉浸看房';$('immersiveBtn').setAttribute('aria-pressed',String(immersive));}
$('immersiveBtn').onclick=toggleImmersive;
$('fullscreenBtn').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else{await document.documentElement.requestFullscreen();if(navigator.maxTouchPoints>0)await screen.orientation?.lock?.('landscape').catch(()=>{});}}catch{toast('当前浏览器不支持全屏，可放大窗口浏览');}};
document.addEventListener('fullscreenchange',()=>{$('fullscreenBtn').setAttribute('aria-label',document.fullscreenElement?'退出全屏':'全屏');resize();});
function showDialog(id){keys.clear();if(document.pointerLockElement)document.exitPointerLock();$(id).showModal();}
$('helpBtn').onclick=()=>showDialog('helpDialog');$('referenceBtn').onclick=()=>showDialog('referenceDialog');
document.querySelectorAll('dialog').forEach(d=>{d.querySelectorAll('.close,.close-action').forEach(b=>b.onclick=()=>d.close());d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});});
const photos=[['reference-window.jpg','窗边与床铺 · 装修后'],['reference-desk.jpg','书桌与生活用品 · 装修后'],['reference-bed.jpg','纱帘与床品 · 装修后'],['reference-entry.jpg','入口与家具布局 · 入住前'],['reference-bath.jpg','卫生间 · 入住后的洗衣机'],['reference-bath-new.jpg','卫生间 · 左侧洁具与右侧花洒'],['reference-entry-new.jpg','门口 · 左转卫生间、前方卧室'],['reference-headboard.jpg','床头后的白色卫生间隔墙'],['reference-closet-new.jpg','衣柜侧面的球拍与帽子'],['reference-window-new.jpg','窗台与晾衣杆 · 入住后'],['reference-exterior-level.jpg','窗外 · 近处灰楼与左侧住宅楼（视频帧）'],['reference-motorcycle.jpg','蓝色 Suzuki GSX250R · 车辆细节'],['reference-helmet.jpg','LS2 FF801 碳纤维头盔 · 实物'],['reference-bike-position.jpg','窗外摩托车位置 · 车头朝灰楼墙面'],['reference-exterior-down.jpg','窗外 · 楼下树木与道路（视频帧）']];let photoIndex=0;
function photo(delta){photoIndex=(photoIndex+delta+photos.length)%photos.length;$('referenceImage').src='./assets/'+photos[photoIndex][0];$('referenceImage').alt=photos[photoIndex][1];$('photoCaption').textContent=photos[photoIndex][1];}$('prevPhoto').onclick=()=>photo(-1);$('nextPhoto').onclick=()=>photo(1);
function resize(){const w=$('app').clientWidth,h=$('app').clientHeight;if(w<=0||h<=0)return;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);daylight.resize();renderSignature='';}window.addEventListener('resize',resize);window.visualViewport?.addEventListener('resize',resize);window.addEventListener('orientationchange',()=>requestAnimationFrame(resize));
const renderProbe=createRenderProbe();
function tick(now){
  requestAnimationFrame(tick);
  const dt=Math.min((now-last)/1000,.05);last=now;
  if(document.hidden||$('app').hidden){renderProbe.update(now,false);return;}
  if(mode==='walk'){
    const forward=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0);
    const side=(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0);
    const norm=Math.hypot(forward,side)||1,speed=dt/norm;
    const vertical=(keys.has('ShiftLeft')||keys.has('ShiftRight')?1:0)-(keys.has('ControlLeft')||keys.has('ControlRight')?1:0);
    moveVertical(vertical*dt*.8);
    move((-Math.sin(yaw)*forward+Math.cos(yaw)*side)*speed,(-Math.cos(yaw)*forward-Math.sin(yaw)*side)*speed);
    camera.rotation.set(pitch,yaw,0,'YXZ');
  }else orbit.update();
  renderProbe.update(now,true);
  const target=curtainOpen?1:0;
  curtainAmount+=(target-curtainAmount)*Math.min(dt*5,1);
  if(Math.abs(target-curtainAmount)<.0001)curtainAmount=target;
  updateCurtain(curtainAmount);setCurtainLight(curtainAmount);daylight.setCurtain(curtainAmount);updateIndirect(curtainAmount);
  const doorChanged=wardrobe.update(dt);
  if(doorChanged){navigation.updateDynamic();renderer.shadowMap.needsUpdate=true;}
  interactions.update(now/1000);
  const motionChanged=breeze.update(dt,curtainAmount,mode==='walk');
  const signature=[mode,...camera.position.toArray(),...camera.quaternion.toArray(),Math.round(curtainAmount*10000),lightOn,innerWidth,innerHeight,interactions.active,wardrobe.revision,breeze.enabled,breeze.visibilityMask].join('/');
  const dustEnabled=mode==='walk'&&curtainAmount>.1;
  if(signature!==renderSignature||interactions.active){
    renderSignature=signature;daylight.render(breeze.time,dustEnabled);
  }else daylight.animate?.(breeze.time,dustEnabled,motionChanged);
}
manager.onError=url=>{toast('一张材质未能载入，刷新页面可重试');console.warn('Texture failed',url);};
window.addEventListener('error',()=>{if(!$('loading').hidden){$('loading').hidden=true;$('error').hidden=false;}});
// Read-only diagnostics for local verification; no network or user data.
window.roomDiagnostics={get state(){return{mode,position:camera.position.toArray(),yaw,pitch,curtainOpen,lightOn,objects:world.children.length,colliders:navigation.surfaces,collisionRadius:navigation.clearance,batchedMeshes,assetStatistics,water:interactions.state,wardrobe:wardrobe.state,breeze:breeze.state,frameCache:daylight.statistics,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles};},canStand,canTravel:(a,b)=>navigation.canTravel(new THREE.Vector3(...a),new THREE.Vector3(...b))};
const modelContext=document.modelContext;
if(modelContext?.registerTool){
  const lifecycle=new AbortController();
  const register=t=>{try{Promise.resolve(modelContext.registerTool(t,{signal:lifecycle.signal})).catch(()=>{});}catch{}};
  register({name:'measure_room_rendering',description:'在当前视角左右缓慢转动约 5 秒，测量帧间隔后恢复视角，用于本地性能比较。',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:false},execute(){if(mode!=='walk')throw new Error('Use a walking viewpoint');keys.clear();return renderProbe.start(camera);}});
  register({name:'get_room_view',description:'读取当前房间漫游视角、物品开关状态与渲染信息。',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:false},execute(){return {mode,position:camera.position.toArray(),curtainOpen,lightOn,water:interactions.state,wardrobe:wardrobe.state,rendering:{graphicsDevice,breeze:breeze.state,frameCache:daylight.statistics,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,mergedObjects:batchedMeshes}};}});
  register({name:'navigate_room',description:'切换房间的可见视角：门口、床边、书桌、窗边、楼下摩托车、衣柜、衣柜正面、卫生间、门上细节、洁具细节或空间总览。',inputSchema:{type:'object',properties:{view:{type:'string',enum:['entry','bed','desk','window','yard','closet','bath','door','toilet','helmet','helmetSide','pillow','shower','lock','ac','tabletop','basket','doorframe','grille','mug','radiator','gundam','paperCup','shelf','chair','rackets','wardrobe','overview']}},required:['view'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){if(!input||!['entry','bed','desk','window','yard','closet','bath','door','toilet','helmet','helmetSide','pillow','shower','lock','ac','tabletop','basket','doorframe','grille','mug','radiator','gundam','paperCup','shelf','chair','rackets','wardrobe','overview'].includes(input.view))throw new Error('Unknown view');if(input.view==='overview')setMode('overview');else goTo(input.view);return {mode,position:camera.position.toArray()};}});
  register({name:'walk_room',description:'沿当前朝向在房间中移动。遇到墙壁或家具时会停下，单次最多两米。',inputSchema:{type:'object',properties:{direction:{type:'string',enum:['forward','back','left','right','up','down']},distance:{type:'number',minimum:.05,maximum:2}},required:['direction','distance'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){if(!input||!['forward','back','left','right','up','down'].includes(input.direction)||!Number.isFinite(input.distance)||input.distance<.05||input.distance>2)throw new Error('Invalid movement');if(mode!=='walk')throw new Error('Switch to a walking viewpoint first');const start=camera.position.clone();const f=input.direction==='forward'?1:input.direction==='back'?-1:0;const s=input.direction==='right'?1:input.direction==='left'?-1:0;const steps=Math.ceil(input.distance/.025),length=input.distance/steps;for(let i=0;i<steps;i++){if(input.direction==='up'||input.direction==='down')moveVertical(length*(input.direction==='up'?1:-1));else move((-Math.sin(yaw)*f+Math.cos(yaw)*s)*length,(-Math.cos(yaw)*f-Math.sin(yaw)*s)*length);}return {position:camera.position.toArray(),distanceMoved:start.distanceTo(camera.position)};}});
  window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
}


export function enterRoom(view='walk'){keys.clear();setMode(view==='overview'?'overview':'walk');if(view!=='overview')resetView();resize();last=performance.now();}
export function pauseRoom(){keys.clear();drag=null;document.querySelectorAll('.held').forEach(b=>b.classList.remove('held'));if(immersive)toggleImmersive();$('interactionHint').hidden=true;document.querySelectorAll('#app dialog[open]').forEach(d=>d.close());if(document.pointerLockElement)document.exitPointerLock();}
updateCurtain(0);setCurtainLight(0);daylight.setCurtain(0);updateIndirect(0);
await renderer.compileAsync(scene,camera);
reportRoomLoading(98,'正在呈现房间');await nextPaint();
daylight.render(0,false);
await finishRoomLoading();
requestAnimationFrame(tick);
