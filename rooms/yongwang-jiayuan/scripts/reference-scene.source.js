import * as THREE from 'three';
import {RoundedBoxGeometry} from './vendor/RoundedBoxGeometry.js';
import {OrbitControls} from './vendor/OrbitControls.js';
import {tileTexture,addBedding} from './precision-models.js?v=detail17';
import {addDetails} from './details.js?v=detail17';
import {buildArchitecture,canOccupy,floorHeight} from './room-layout.js?v=detail17';
import {addExterior} from './exterior.js?v=detail17';
import {createAfternoon} from './afternoon.js?v=detail17';
import {refineBlenderBedding,refineBlenderChair,applyBakedRoomLight} from './summer-refinement.js?v=detail17';
import {installSoftSunShadows,createSoftDaylight} from './soft-daylight.js?v=detail17';

import {createFlyNavigation,batchStaticGeometry} from './navigation.js?v=detail17';
import {createInteractions} from './interactions.js?v=detail17';
import {addAirConditioner} from './air-conditioner.js?v=detail17';
import {addBayWindow} from './bay-window.js?v=detail17';

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
const world=new THREE.Group();scene.add(world);
// All dimensions are metres. The footprint is inferred, not measured.
const room={width:2.8,depth:3.6,height:2.65};
const colliders=[];const cutaway=[];const ceilings=[];
let renderSignature='';
const manager=new THREE.LoadingManager(()=>{renderSignature='';$('loading').hidden=true;});
const loader=new THREE.TextureLoader(manager);
function texture(name,rx=1,ry=1){const t=loader.load('./assets/'+name);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(rx,ry);t.anisotropy=renderer.capabilities.getMaxAnisotropy();return t;}
const tx={pink:texture('pink-plaster.jpg',5,4),wood:texture('wood.jpg',1,2),cloth:texture('woven-cloth.jpg',3,4),quilt:texture('quilt-flat-floral-v2.png',1.45,1.65),floor:tileTexture(THREE),gray:texture('gray-wall.jpg',5,4),marble:texture('bath-marble.jpg',2,3)};
const mat=(color,roughness=.7,other={})=>new THREE.MeshStandardMaterial({color,roughness,...other});
const M={pink:mat('#f5d9d2',.84,{map:tx.pink}),gray:mat('#edf1ec',.87,{map:tx.gray}),white:mat('#fbfaf4',.43),ceiling:mat('#faf8f2',.98),trim:mat('#fffdf8',.48),black:mat('#282722',.67),wood:mat('#fff4e3',.50,{map:tx.wood}),bedWood:mat('#c59f6d',.58),metal:mat('#8b8c82',.28,{metalness:.78}),brass:mat('#786047',.37,{metalness:.55}),cloth:mat('#fffdf7',.86,{map:tx.cloth}),quilt:mat('#fffdf8',.86,{map:tx.quilt}),chair:mat('#b4b6af',.95,{map:tx.cloth}),glass:mat('#fffaf2',.32,{transparent:true,opacity:.055,metalness:0,envMapIntensity:.08}),tile:new THREE.MeshPhysicalMaterial({color:'#fffaf1',map:tx.floor,roughness:.29,metalness:0,clearcoat:.24,clearcoatRoughness:.27}),bathTile:mat('#eeeeea',.38),marble:mat('#f3f3ef',.30,{map:tx.marble}),grout:mat('#c0c4bd',.8),doorWood:mat('#90512b',.50,{map:tx.wood}),dark:mat('#171c1b',.75)};
const geoCache=new Map();
function box(w,h,d,m,x=0,y=0,z=0,parent=world,r=0){
  // Small, real bevels catch light on joinery and painted edges. Structural walls
  // keep their measured footprint; thin trim never rounds beyond its thickness.
  if(!r&&[M.white,M.trim,M.wood,M.bedWood,M.doorWood].includes(m)&&Math.max(w,h,d)<2.35)r=Math.min(.009,Math.min(w,h,d)*.24);
  const key=[w,h,d,r].join(',');if(!geoCache.has(key))geoCache.set(key,r?new RoundedBoxGeometry(w,h,d,3,r):new THREE.BoxGeometry(w,h,d));const o=new THREE.Mesh(geoCache.get(key),m);o.position.set(x,y,z);o.castShadow=!m.transparent;o.receiveShadow=true;parent.add(o);return o;
}
function cylinder(rt,rb,h,m,x,y,z,parent=world,n=24){const o=new THREE.Mesh(new THREE.CylinderGeometry(rt,rb,h,n),m);o.position.set(x,y,z);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
function ellipsoid(x,y,z,sx,sy,sz,m,parent=world){const o=new THREE.Mesh(new THREE.SphereGeometry(1,24,16),m);o.scale.set(sx,sy,sz);o.position.set(x,y,z);o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
function rod(a,b,r,m,parent=world){const A=new THREE.Vector3(...a),B=new THREE.Vector3(...b);const c=cylinder(r,r,A.distanceTo(B),m,0,0,0,parent,12);c.position.copy(A).add(B).multiplyScalar(.5);c.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),B.sub(A).normalize());return c;}
function path(points,r,m,parent=world){const curve=new THREE.CatmullRomCurve3(points.map(v=>new THREE.Vector3(...v)));const o=new THREE.Mesh(new THREE.TubeGeometry(curve,48,r,8,false),m);o.castShadow=true;parent.add(o);return o;}
function obstacle(x1,x2,z1,z2){colliders.push({x1,x2,z1,z2});}
function wall(w,h,d,m,x,y,z,hide=false){const o=box(w,h,d,m,x,y,z);obstacle(x-w/2,x+w/2,z-d/2,z+d/2);if(hide)cutaway.push(o);return o;}
buildArchitecture({THREE,world,M,box,wall,obstacle,cutaway,ceilings});
const updateIndirect=applyBakedRoomLight({THREE,world,M,loader});
addBayWindow({THREE,world,M,mat,box,cylinder,rod});
const outside=addExterior({THREE,world,mat,box,cylinder,rod});
// Wardrobe: wood side faces the entrance, white doors face into the room.
const wardrobe=new THREE.Group();wardrobe.name='window-side-wardrobe';wardrobe.position.set(-1.1,0,-1.135);world.add(wardrobe);
box(.57,2.1,1.17,M.wood,0,1.05,0,wardrobe);box(.57,.065,1.19,M.wood,0,2.09,0,wardrobe);
for(let i=0;i<3;i++){let z=-.386+i*.386;box(.025,2.025,.376,M.white,.294,1.065,z,wardrobe,.008);box(.025,.18,.017,M.metal,.322,.94,z+(i===0?.13:-.13),wardrobe,.004);}
box(.58,.09,1.14,M.dark,0,.075,0,wardrobe);obstacle(-1.4,-.79,-1.73,-.54);
// Bed: head against entrance-side wall; feet toward the window (user confirmed).
const bed=new THREE.Group();bed.position.set(-.6,0,.64);world.add(bed);
for(const x of [-.67,.67])for(const z of [-.92,.92])box(.075,.35,.075,M.bedWood,x,.19,z,bed,.006);
box(1.48,.14,2.05,M.bedWood,0,.32,0,bed,.014);box(1.42,.16,1.98,M.white,0,.46,0,bed,.045);
box(1.51,.69,.065,M.bedWood,0,.65,1.06,bed,.05);
addBedding({THREE,bed,M,mat});
refineBlenderBedding({THREE,bed});
obstacle(-1.36,.17,-.42,1.71);
// White ladder desk along the right-hand wall.
const desk=new THREE.Group();desk.position.set(1.035,0,-.76);world.add(desk);
box(.60,.045,1.02,M.white,0,.765,0,desk,.008);box(.55,.12,.98,M.white,.016,.679,0,desk,.008);
box(.01,.013,.45,M.metal,-.274,.685,0,desk);
for(const z of [-.495,.495]){rod([-.31,.03,z],[.24,1.88,z],.017,M.white,desk);rod([.26,.03,z],[.26,1.88,z],.017,M.white,desk);}
box(.48,.022,.985,M.white,.047,1.21,0,desk);box(.29,.022,.985,M.white,.139,1.65,0,desk);rod([-.3,.055,-.49],[-.3,.055,.49],.012,M.white,desk);
obstacle(.72,1.4,-1.285,-.235);
// Radiator ribs and pipework behind the desk, below the window side.
const radiator=new THREE.Group();radiator.name='window-side-radiator';radiator.position.set(1.26,0,-1.32);world.add(radiator);
for(let i=0;i<13;i++)box(.13,.65,.049,M.white,0,.44,-.38+i*.063,radiator,.023);
rod([0,.15,-.43],[0,.15,.43],.024,M.white,radiator);rod([0,.73,-.43],[0,.73,.43],.023,M.white,radiator);
path([[1.26,.15,-1.75],[1.33,.15,-1.75],[1.33,.12,-1.78]],.018,M.white);
// Upholstered chair; its back faces the bed, seat faces the desk.
const chair=new THREE.Group();chair.position.set(.48,0,-.99);chair.rotation.y=.08;world.add(chair);
box(.45,.085,.43,M.chair,0,.455,0,chair,.06);const cb=box(.075,.45,.44,M.chair,-.206,.685,0,chair,.06);cb.rotation.z=.13;
for(const x of [-.15,.15])for(const z of [-.16,.16])rod([x*1.28,.035,z*1.25],[x,.42,z],.019,M.bedWood,chair);
refineBlenderChair({THREE,chair});
obstacle(.23,.71,-1.25,-.72);
// Connected wall-mounted pipework, power lead and the reference energy label.
addAirConditioner({THREE,world,M,mat,box,cylinder,path});
// Translucent, pleated curtain with stitched borders. Open/closed are interactive.
const curtain=new THREE.Group();world.add(curtain);const curtainPanels=[];const curtainRings=[];
const curtainMat=mat('#f7eedc',.94,{side:THREE.DoubleSide,transparent:true,opacity:.96});
for(let k=0;k<1;k++){const g=new THREE.PlaneGeometry(2.03,1.93,140,35);const p=g.attributes.position;for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i);p.setZ(i,.032*Math.cos(x*28)+.010*Math.sin(y*2.5+x*5));}g.computeVertexNormals();const mesh=new THREE.Mesh(g,curtainMat);mesh.position.set(.12,1.395,-1.585);mesh.castShadow=false;mesh.receiveShadow=true;curtain.add(mesh);curtainPanels.push(mesh);for(let j=0;j<14;j++){const ring=new THREE.Mesh(new THREE.TorusGeometry(.023,.005,7,14),M.brass);ring.position.set(-.865+j*.15,2.389,-1.59);ring.userData.closedX=ring.position.x;curtainRings.push(ring);curtain.add(ring);} }
rod([-1.1,2.405,-1.57],[1.25,2.405,-1.57],.016,M.brass);for(const x of [-1.12,1.28])ellipsoid(x,2.405,-1.57,.035,.025,.025,M.brass);
// Ceiling lamp and layered daylight.
const ceilingLamp=cylinder(.185,.165,.07,M.white,0,2.56,.03,world,48);const diffuser=cylinder(.155,.175,.05,mat('#fff5df',.4,{emissive:'#fff0ce',emissiveIntensity:.1}),0,2.517,.03,world,48);ceilings.push(ceilingLamp,diffuser);
const {windowLight,sun}=createAfternoon({THREE,scene,renderer,world});
const daylight=createSoftDaylight({THREE,renderer,scene,camera,sun});
const lamp=new THREE.PointLight('#ffdca5',0,6,2);lamp.position.set(0,2.35,.05);scene.add(lamp);
const bathLight=new THREE.PointLight('#f0f5ed',3,4,2);bathLight.position.set(-.55,2.30,2.48);scene.add(bathLight);

const ctx={THREE,world,scene,M,mat,box,cylinder,ellipsoid,rod,path,obstacle,bed,desk,chair,wardrobe,curtainPanels,cutaway,ceilings,texture};
addDetails(ctx);
curtain.userData.dynamic=true;
const navigation=createFlyNavigation(THREE,world,[outside,curtain]);
const batchedMeshes=batchStaticGeometry(THREE,world,[curtain,...cutaway,...ceilings]);
const orbit=new OrbitControls(camera,canvas);orbit.enabled=false;orbit.enableDamping=true;orbit.minDistance=3;orbit.maxDistance=12;orbit.maxPolarAngle=Math.PI*.46;orbit.target.set(-.3,.65,.7);
let mode='walk',yaw=.12,pitch=-.08,locked=false,drag=null,curtainOpen=true,lightOn=false,curtainAmount=1;
const keys=new Set();let last=performance.now();let toastTimer;
const viewpoints={gundam:{p:[.79,1.80,-.505],yaw:-Math.PI/2,pitch:-.085,label:'高达细节'},paperCup:{p:[.84,1.75,-.89],yaw:-Math.PI/2,pitch:-.13,label:'纸杯图案'},shelf:{p:[.35,1.84,-.71],yaw:-Math.PI/2,pitch:-.16,label:'桌架摆件'},mug:{p:[.59,1.05,-1.115],yaw:-1.405,pitch:-.54,label:'杯子细节'},radiator:{p:[.50,.71,-1.10],yaw:-1.3,pitch:-.2,label:'暖气位置'},ac:{p:[.54,2.21,-.71],yaw:-Math.PI/2,pitch:.08,label:'空调细节'},tabletop:{p:[.52,1.20,-.52],yaw:-Math.PI/2,pitch:-.64,label:'桌面细节'},basket:{p:[.62,1.53,-.43],yaw:-Math.PI/2,pitch:.03,label:'花篮细节'},doorframe:{p:[.93,2.05,2.67],yaw:-Math.PI/2,pitch:.25,label:'门框细节'},grille:{p:[.34,1.73,-1.49],yaw:-.63,pitch:0,label:'窗栏细节'},helmetSide:{p:[-.42,2.33,-.95],yaw:Math.PI/2,pitch:-.045,label:'头盔侧面'},helmet:{p:[-.48,2.35,-.29],yaw:.72,pitch:-.07,label:'头盔细节'},pillow:{p:[.27,1.10,1.0],yaw:1.88,pitch:-.40,label:'枕头细节'},shower:{p:[.20,1.40,2.82],yaw:.98,pitch:-.035,label:'花洒细节'},lock:{p:[1.05,1.03,2.38],yaw:-1.48,pitch:-.075,label:'反锁旋钮'},entry:{p:[.92,1.56,2.77],yaw:.08,pitch:-.09,label:'入口过道'},bed:{p:[.48,1.30,.45],yaw:.22,pitch:-.04,label:'床边'},desk:{p:[.42,1.50,-.05],yaw:-1.05,pitch:-.26,label:'书桌'},window:{p:[-.25,1.56,-1.27],yaw:.02,pitch:.02,label:'窗边'},yard:{p:[-.38,1.63,-1.75],yaw:-.83,pitch:-.87,label:'窗边 · 楼下'},closet:{p:[.42,1.54,.55],yaw:.98,pitch:0,label:'衣柜'},door:{p:[.51,1.50,2.70],yaw:-Math.PI/2,pitch:.05,label:'门上细节'},toilet:{p:[-.50,1.15,2.12],yaw:Math.PI-.24,pitch:-.55,label:'洁具细节'},bath:{p:[.04,1.645,2.43],yaw:Math.PI/2,pitch:-.20,label:'卫生间'}};
function toast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),3600);}
function setMode(next){mode=next;keys.clear();document.querySelectorAll('.held').forEach(b=>b.classList.remove('held'));$('interactionHint').hidden=true;renderer.shadowMap.needsUpdate=true;const overview=mode==='overview';orbit.enabled=overview;cutaway.forEach(o=>o.visible=!overview);ceilings.forEach(o=>o.visible=!overview);outside.visible=!overview;$('walkBtn').classList.toggle('active',!overview);$('overviewBtn').classList.toggle('active',overview);$('walkBtn').setAttribute('aria-pressed',String(!overview));$('overviewBtn').setAttribute('aria-pressed',String(overview));$('app').classList.toggle('overview',overview);if(overview){if(document.pointerLockElement)document.exitPointerLock();camera.position.set(5.5,6.1,7.0);orbit.target.set(-.25,.7,.8);orbit.update();scene.background.set('#dfe3dc');}else{scene.background.set('#e5ebe5');goTo('entry',false);}}
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
const interactions=createInteractions({THREE,world,camera,canvas,curtain,toggleCurtain,toggleLight,toast,hint:$('interactionHint')});
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
window.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]'))return;if(e.code==='KeyH'&&!e.repeat)toggleImmersive();if(['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight','ControlLeft','ControlRight'].includes(e.code)){e.preventDefault();keys.add(e.code);}});
window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',()=>{keys.clear();drag=null;});document.addEventListener('visibilitychange',()=>keys.clear());
for(const b of document.querySelectorAll('[data-move]')){const code={forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',up:'ShiftLeft',down:'ControlLeft'}[b.dataset.move];b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(code);b.classList.add('held');});for(const t of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(t,()=>{keys.delete(code);b.classList.remove('held');});}

$('walkBtn').onclick=()=>setMode('walk');$('overviewBtn').onclick=()=>setMode('overview');$('resetBtn').onclick=()=>{if(mode==='overview')setMode('overview');else{goTo('entry');camera.position.set(.83,1.48,1.66);yaw=.20;pitch=-.20;camera.rotation.set(pitch,yaw,0,'YXZ');}};
function toggleCurtain(){curtainOpen=!curtainOpen;toast(curtainOpen?'窗帘已拉开':'窗帘已合上');}
function toggleLight(){lightOn=!lightOn;lamp.intensity=lightOn?7:0;diffuser.material.emissiveIntensity=lightOn?1.5:.1;const rocker=world.getObjectByName('light-switch-rocker');if(rocker)rocker.rotation.z=lightOn?.13:0;toast(lightOn?'房间灯已打开':'房间灯已关闭');}

let immersive=false;
function toggleImmersive(){immersive=!immersive;$('app').classList.toggle('immersive',immersive);$('immersiveBtn').textContent=immersive?'退出沉浸':'沉浸看房';$('immersiveBtn').setAttribute('aria-pressed',String(immersive));}
$('immersiveBtn').onclick=toggleImmersive;
$('fullscreenBtn').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else{await $('app').requestFullscreen();if(navigator.maxTouchPoints>0)await screen.orientation?.lock?.('landscape').catch(()=>{});}}catch{toast('当前浏览器不支持全屏，可放大窗口浏览');}};
function showDialog(id){keys.clear();if(document.pointerLockElement)document.exitPointerLock();$(id).showModal();}
$('helpBtn').onclick=()=>showDialog('helpDialog');$('referenceBtn').onclick=()=>showDialog('referenceDialog');
document.querySelectorAll('dialog').forEach(d=>{d.querySelectorAll('.close,.close-action').forEach(b=>b.onclick=()=>d.close());d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});});
const photos=[['reference-window.jpg','窗边与床铺 · 装修后'],['reference-desk.jpg','书桌与生活用品 · 装修后'],['reference-bed.jpg','纱帘与床品 · 装修后'],['reference-entry.jpg','入口与家具布局 · 入住前'],['reference-bath.jpg','卫生间 · 入住后的洗衣机'],['reference-bath-new.jpg','卫生间 · 左侧洁具与右侧花洒'],['reference-entry-new.jpg','门口 · 左转卫生间、前方卧室'],['reference-headboard.jpg','床头后的白色卫生间隔墙'],['reference-closet-new.jpg','衣柜侧面的球拍与帽子'],['reference-window-new.jpg','窗台与晾衣杆 · 入住后'],['reference-exterior-level.jpg','窗外 · 近处灰楼与左侧住宅楼（视频帧）'],['reference-motorcycle.jpg','蓝色 Suzuki GSX250R · 车辆细节'],['reference-helmet.jpg','LS2 FF801 碳纤维头盔 · 实物'],['reference-bike-position.jpg','窗外摩托车位置 · 车头朝灰楼墙面'],['reference-exterior-down.jpg','窗外 · 楼下树木与道路（视频帧）']];let photoIndex=0;
function photo(delta){photoIndex=(photoIndex+delta+photos.length)%photos.length;$('referenceImage').src='./assets/'+photos[photoIndex][0];$('referenceImage').alt=photos[photoIndex][1];$('photoCaption').textContent=photos[photoIndex][1];}$('prevPhoto').onclick=()=>photo(-1);$('nextPhoto').onclick=()=>photo(1);
function resize(){const w=$('app').clientWidth,h=$('app').clientHeight;camera.aspect=w/h;camera.updateProjectionMatrix();renderer.setSize(w,h,false);daylight.resize();renderSignature='';}window.addEventListener('resize',resize);window.visualViewport?.addEventListener('resize',resize);window.addEventListener('orientationchange',()=>requestAnimationFrame(resize));
function tick(now){requestAnimationFrame(tick);const dt=Math.min((now-last)/1000,.05);last=now;if(document.hidden)return;if(mode==='walk'){const forward=(keys.has('KeyW')||keys.has('ArrowUp')?1:0)-(keys.has('KeyS')||keys.has('ArrowDown')?1:0);const side=(keys.has('KeyD')||keys.has('ArrowRight')?1:0)-(keys.has('KeyA')||keys.has('ArrowLeft')?1:0);const norm=Math.hypot(forward,side)||1;const speed=dt/norm;const vertical=(keys.has('ShiftLeft')||keys.has('ShiftRight')?1:0)-(keys.has('ControlLeft')||keys.has('ControlRight')?1:0);moveVertical(vertical*dt*.8);move((-Math.sin(yaw)*forward+Math.cos(yaw)*side)*speed,(-Math.cos(yaw)*forward-Math.sin(yaw)*side)*speed);camera.rotation.set(pitch,yaw,0,'YXZ');}else orbit.update();const target=curtainOpen?1:0;curtainAmount+=(target-curtainAmount)*Math.min(dt*5,1);curtainPanels.forEach((p,i)=>{p.scale.x=1-.79*curtainAmount;p.position.x=.12+.91*curtainAmount;});curtainRings.forEach(r=>r.position.x=.12+.91*curtainAmount+(r.userData.closedX-.12)*(1-.79*curtainAmount));windowLight.intensity=.65+.65*curtainAmount;sun.intensity=.95+4.85*curtainAmount;updateIndirect(curtainAmount);interactions.update(now/1000);const signature=[mode,...camera.position.toArray(),...camera.quaternion.toArray(),Math.round(curtainAmount*10000),lightOn,innerWidth,innerHeight,interactions.active].join('/');if(signature!==renderSignature||interactions.active){renderSignature=signature;daylight.render(now/1000,mode==='walk'&&curtainAmount>.1);}else daylight.animate?.(now/1000,mode==='walk'&&curtainAmount>.1);}
requestAnimationFrame(tick);
manager.onError=url=>{toast('一张材质未能载入，刷新页面可重试');console.warn('Texture failed',url);};
window.addEventListener('error',()=>{if(!$('loading').hidden){$('loading').hidden=true;$('error').hidden=false;}});
// Read-only diagnostics for local verification; no network or user data.
window.roomDiagnostics={get state(){return{mode,position:camera.position.toArray(),yaw,pitch,curtainOpen,lightOn,objects:world.children.length,colliders:navigation.surfaces,collisionRadius:navigation.clearance,batchedMeshes,water:interactions.state,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles};},canStand,canTravel:(a,b)=>navigation.canTravel(new THREE.Vector3(...a),new THREE.Vector3(...b))};
const modelContext=document.modelContext;
if(modelContext?.registerTool){
  const lifecycle=new AbortController();
  const register=t=>{try{Promise.resolve(modelContext.registerTool(t,{signal:lifecycle.signal})).catch(()=>{});}catch{}};
  register({name:'get_room_view',description:'读取当前房间漫游视角、物品开关状态与渲染信息。',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true,untrustedContentHint:false},execute(){return {mode,position:camera.position.toArray(),curtainOpen,lightOn,water:interactions.state,rendering:{graphicsDevice,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,mergedObjects:batchedMeshes}};}});
  register({name:'navigate_room',description:'切换房间的可见视角：门口、床边、书桌、窗边、楼下摩托车、衣柜、卫生间、门上细节、洁具细节或空间总览。',inputSchema:{type:'object',properties:{view:{type:'string',enum:['entry','bed','desk','window','yard','closet','bath','door','toilet','helmet','helmetSide','pillow','shower','lock','ac','tabletop','basket','doorframe','grille','mug','radiator','gundam','paperCup','shelf','overview']}},required:['view'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){if(!input||!['entry','bed','desk','window','yard','closet','bath','door','toilet','helmet','helmetSide','pillow','shower','lock','ac','tabletop','basket','doorframe','grille','mug','radiator','gundam','paperCup','shelf','overview'].includes(input.view))throw new Error('Unknown view');if(input.view==='overview')setMode('overview');else goTo(input.view);return {mode,position:camera.position.toArray()};}});
  register({name:'walk_room',description:'沿当前朝向在房间中移动。遇到墙壁或家具时会停下，单次最多两米。',inputSchema:{type:'object',properties:{direction:{type:'string',enum:['forward','back','left','right','up','down']},distance:{type:'number',minimum:.05,maximum:2}},required:['direction','distance'],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:false},execute(input){if(!input||!['forward','back','left','right','up','down'].includes(input.direction)||!Number.isFinite(input.distance)||input.distance<.05||input.distance>2)throw new Error('Invalid movement');if(mode!=='walk')throw new Error('Switch to a walking viewpoint first');const start=camera.position.clone();const f=input.direction==='forward'?1:input.direction==='back'?-1:0;const s=input.direction==='right'?1:input.direction==='left'?-1:0;const steps=Math.ceil(input.distance/.025),length=input.distance/steps;for(let i=0;i<steps;i++){if(input.direction==='up'||input.direction==='down')moveVertical(length*(input.direction==='up'?1:-1));else move((-Math.sin(yaw)*f+Math.cos(yaw)*s)*length,(-Math.cos(yaw)*f-Math.sin(yaw)*s)*length);}return {position:camera.position.toArray(),distanceMoved:start.distanceTo(camera.position)};}});
  window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
}
