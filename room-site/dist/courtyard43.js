// Independent completed-room viewer. Blender owns persistent shapes/materials;
// this module owns input, sound, live lighting and reversible state animation.
import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {parseBlenderRoom} from './blender-room.js?v=pages1';
import {loadRoomBinary} from './room-binary.js?v=pages1';
import {startRoomLoading,reportRoomLoading,finishRoomLoading,failRoomLoading} from './room-loading.js?v=viewer26';
import {createCourtyardAudio} from './courtyard43-audio.js?v=courtyard43-interior01';
import {batchCourtyardGeometry,createCourtyardNavigation,createCourtyardLighting,createCourtyardFinish,easedAmount,oppositeEndpoint,courtyardLockView,courtyardOverviewView} from './courtyard43-effects.js?v=courtyard43-interior01';

const $=id=>document.getElementById(id),canvas=$('world');
let toastTimer,entered=false,disposed=false,frame=0,renderer=null;
function toast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('toast').classList.remove('show'),2600);}
const audio=createCourtyardAudio({onChange(muted){$('soundBtn').setAttribute('aria-pressed',String(!muted));$('soundBtn').setAttribute('aria-label',muted?'开启声音':'静音');$('soundBtn').title=muted?'开启声音':'静音';}});
$('soundBtn').onclick=async()=>{if(!await audio.setMuted(!audio.muted))toast('声音暂时无法开启，请再点一次重试');};
startRoomLoading();

try{
  const response=await fetch('./assets/rooms/Courtyard43/interior/scene.json?v=courtyard43-interior01');
  if(!response.ok)throw Error(`房间清单读取失败 (${response.status})`);
  const manifest=await response.json();
  if(manifest.roomId!=='Courtyard43'||manifest.stage!=='interior'||!manifest.structureApproved)throw Error('房间资料版本不匹配');
  let geometryProgress=0,textureDone=0;
  const updateProgress=()=>reportRoomLoading(6+58*geometryProgress+23*textureDone/Math.max(1,manifest.textures.length),geometryProgress<1?'正在载入房间':'正在准备材质');
  const textureLoader=new THREE.TextureLoader();
  const [buffer,textures]=await Promise.all([
    loadRoomBinary(manifest,p=>{geometryProgress=p;updateProgress();}),
    Promise.all(manifest.textures.map(async desc=>{const t=await textureLoader.loadAsync(desc.webPath);for(const key of ['wrapS','wrapT','magFilter','minFilter','anisotropy','flipY','colorSpace','channel','rotation','premultiplyAlpha','generateMipmaps','mapping'])if(desc[key]!==undefined)t[key]=desc[key];for(const key of ['repeat','offset','center'])if(desc[key])t[key].fromArray(desc[key]);t.needsUpdate=true;textureDone++;updateProgress();return t;}))
  ]);
  const {world,refs,materials,statistics}=parseBlenderRoom(THREE,manifest,buffer,textures),review=manifest.review;
  const scene=new THREE.Scene();scene.background=new THREE.Color('#d7e0e3');scene.add(world);
  renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,matchMedia('(pointer: coarse)').matches?1.2:1.4));
  renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.02;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;renderer.info.autoReset=false;
  const camera=new THREE.PerspectiveCamera(64,1,.003,60);camera.rotation.order='YXZ';
  const orbit=new OrbitControls(camera,canvas);orbit.enabled=false;orbit.enableDamping=true;orbit.dampingFactor=.10;orbit.minDistance=2.5;orbit.maxDistance=13;orbit.maxPolarAngle=Math.PI*.48;
  const axes={x:new THREE.Vector3(1,0,0),y:new THREE.Vector3(0,1,0),z:new THREE.Vector3(0,0,1)};
  const interactions=(manifest.interactions||[]).map(desc=>{
    const node=world.getObjectByName(manifest.nodes[desc.node].name);if(!node)throw Error(`缺少可操作物件 ${desc.id}`);
    node.userData.interactive=true;const amount=desc.defaultOpen?1:0,axis=axes[desc.axis]||axes.y,angle=desc.kind==='hinge'?desc.openAngle:desc.kind==='lock'?Math.PI/2:.10;
    const base=node.quaternion.clone();if(desc.kind==='hinge'&&amount)base.multiply(new THREE.Quaternion().setFromAxisAngle(axis,-angle));
    const record={...desc,node,amount,target:amount,base,axis,angle,serial:0,blocked:false,moving:false,position:new THREE.Vector3(),meshes:[]};
    node.traverse(o=>{if(o.isMesh){record.meshes.push(o);o.userData.interactive=true;}});return record;
  });
  const byId=new Map(interactions.map(x=>[x.id,x])),byObject=new Map(interactions.map(x=>[x.node,x]));
  const curtain=byId.get('curtain');
  const hinges=interactions.filter(x=>x.kind==='hinge');
  for(const o of refs.lightFixture||[])o.traverse(n=>{if(!n.name.includes('Diffuser'))return;for(const m of n.isMesh?(Array.isArray(n.material)?n.material:[n.material]):[])m.userData.lightFixture=true;});
  for(const o of refs.glass||[])o.castShadow=false;
  const landmarks=new Map();world.updateMatrixWorld(true);world.traverse(o=>{if(o.isMesh)landmarks.set(o.name,new THREE.Box3().setFromObject(o));});
  const batching=batchCourtyardGeometry(THREE,world,interactions.map(x=>x.node));
  const navigation=createCourtyardNavigation(THREE,world,review,hinges.map(x=>x.node));
  const lighting=createCourtyardLighting(THREE,scene,renderer,materials),finish=createCourtyardFinish(THREE,renderer,scene,camera);
  const pickMeshes=[];world.traverse(o=>{if(o.isMesh)pickMeshes.push(o);});
  const pickRay=new THREE.Raycaster(),pointer=new THREE.Vector2(),tmp=new THREE.Vector3(),bounds=new THREE.Box3();
  const keys=new Set();let mode='walk',yaw=0,pitch=0,drag=null,locked=false,immersive=false,dirty=true,last=performance.now(),lightOn=false,lockOn=false;
  const extraViews={
    wardrobe:{position:[.76,1.28,.86],target:[1.70,1.06,.8]},
    radiator:{position:[.49,1.13,1.18],target:[.84,.82,.14]},
    curtain:{position:[-.08,1.47,1.12],target:[.28,1.35,.07]},
    tabletop:{position:[-.76,1.14,1.13],target:[-1.25,.76,.30]},
    bedding:{position:[.69,1.03,1.98],target:[-1.15,.63,2.04]},
    window:{position:[-.22,1.58,-.37],target:[.28,1.45,-1.12]},
    switch:{position:[2.04,1.48,1.78],target:[(review.room.centerX??0)+review.room.width/2-.019,1.26,2.40]},
    lock:{position:[1.48,1.15,1.71],target:[1.90,1.00,2.07]}
  };
  const viewNames=[...Object.keys(review.viewpoints),...Object.keys(extraViews)];
  function invalidate(shadows=false){dirty=true;if(shadows)renderer.shadowMap.needsUpdate=true;if(!frame&&!document.hidden&&!disposed)frame=requestAnimationFrame(tick);}
  function clearInput(){keys.clear();drag=null;canvas.style.cursor='grab';document.querySelectorAll('.held').forEach(b=>b.classList.remove('held'));}
  function isVisible(o){for(let n=o;n;n=n.parent)if(!n.visible)return false;return true;}
  function owner(o){for(let n=o;n;n=n.parent){const item=byObject.get(n);if(item)return item;}return null;}
  function pick(clientX,clientY){if(mode!=='walk')return null;const rect=canvas.getBoundingClientRect();pointer.set(locked?0:(clientX-rect.left)/rect.width*2-1,locked?0:1-(clientY-rect.top)/rect.height*2);pickRay.setFromCamera(pointer,camera);pickRay.far=4;world.updateMatrixWorld(true);const hits=pickRay.intersectObjects(pickMeshes.filter(isVisible),false);for(const hit of hits){const mats=Array.isArray(hit.object.material)?hit.object.material:[hit.object.material];if(mats.every(m=>m.transparent&&m.opacity<.25))continue;return owner(hit.object);}return null;}
  function move(dx,dy,dz){let changed=false;for(const [axis,delta]of [['x',dx],['y',dy],['z',dz]]){if(!delta)continue;tmp.copy(camera.position);tmp[axis]+=delta;if(navigation.canTravel(camera.position,tmp)){camera.position.copy(tmp);changed=true;}}return changed;}
  function go(view){let v=review.viewpoints[view]||extraViews[view];if(!v)throw Error('Unknown viewpoint');if(view==='overview')v=courtyardOverviewView(v);if(view==='lock'){
      // The lock belongs to the moving door. Observe its current room-facing
      // side; rotating the thumbturn itself must not rotate the camera offset.
      v=courtyardLockView(THREE,byId.get('entry-door').node,byId.get('entry-lock').node,review);
    }mode=view==='overview'?'overview':'walk';clearInput();camera.near=mode==='overview'?.04:.003;camera.updateProjectionMatrix();for(const o of [...(refs.cutaway||[]),...(refs.ceilings||[])])o.visible=mode!=='overview';camera.position.fromArray(v.position);camera.lookAt(new THREE.Vector3(...v.target));yaw=camera.rotation.y;pitch=camera.rotation.x;orbit.enabled=mode==='overview';orbit.target.fromArray(v.target);if(orbit.enabled)orbit.update();$('walkBtn').classList.toggle('active',mode==='walk');$('overviewBtn').classList.toggle('active',mode==='overview');$('walkBtn').setAttribute('aria-pressed',String(mode==='walk'));$('overviewBtn').setAttribute('aria-pressed',String(mode==='overview'));$('app').classList.toggle('overview',mode==='overview');if(document.pointerLockElement)document.exitPointerLock();invalidate(true);}
  function apply(item){if(item.kind==='curtain'){for(const mesh of item.meshes)if(mesh.morphTargetInfluences)mesh.morphTargetInfluences[0]=item.amount;}else item.node.quaternion.copy(item.base).multiply(new THREE.Quaternion().setFromAxisAngle(item.axis,item.angle*item.amount));}
  function blocksViewer(item){if(mode!=='walk')return false;item.node.updateWorldMatrix(true,true);return item.meshes.some(mesh=>{if(mesh.userData.noCollision)return false;bounds.copy(mesh.geometry.boundingBox||mesh.geometry.computeBoundingBox()).applyMatrix4(mesh.matrixWorld).expandByScalar(.018);return bounds.containsPoint(camera.position);});}
  function activate(item,value){if(!item)return false;if(item.id==='entry-door'&&lockOn&&item.target<.5){toast('门已反锁');return false;}audio.setListener(camera.position,yaw);item.blocked=false;item.serial++;const target=value===undefined?oppositeEndpoint(item.target,item.amount):Number(!!value);item.target=target;
    if(item.kind==='switch'){lightOn=!!target;audio.interaction('switch',item.node.getWorldPosition(tmp).toArray());toast(lightOn?'灯已打开':'灯已关闭');}
    else if(item.kind==='lock'){if(target&&byId.get('entry-door')?.amount>.04){item.target=0;toast('先关上房门再反锁');return false;}lockOn=!!target;audio.interaction('lock',item.node.getWorldPosition(tmp).toArray());toast(lockOn?'门已反锁':'反锁已解除');}
    else if(item.kind==='curtain')toast(target?'窗帘正在拉开':'窗帘正在合上');
    else toast(target?'门正在打开':'门正在合上');
    invalidate(true);return true;
  }
  function updateInteractions(dt){let active=false,changed=false,curtainSpeed=0;for(const item of interactions){item.moving=false;if(item.amount===item.target)continue;active=true;const old=item.amount;item.amount=easedAmount(old,item.target,dt,item.kind==='hinge'?3.1:item.kind==='curtain'?2.7:9);apply(item);if(item.kind==='hinge'&&blocksViewer(item)){item.amount=old;item.target=old;item.blocked=true;apply(item);toast('请稍微离开门边');}else{item.moving=Math.abs(item.amount-old)>1e-7;changed=changed||item.moving;}if(item.kind==='curtain')curtainSpeed=Math.abs(item.amount-old)/Math.max(.001,dt);}
    if(changed){navigation.updateDynamic();lighting.update(curtain?.amount||0,lightOn);dirty=true;}
    audio.update(dt,{curtainSpeed,doors:hinges.map(item=>({...item,position:item.node.getWorldPosition(item.position).toArray()})),position:camera.position,yaw});return active;
  }
  function resize(){const width=$('app').clientWidth,height=$('app').clientHeight;if(!width||!height)return;camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height,false);finish.resize();$('app').classList.toggle('touch-device',matchMedia('(pointer: coarse)').matches||innerWidth<=900);invalidate(true);}
  function toggleImmersive(){immersive=!immersive;$('app').classList.toggle('immersive',immersive);$('immersiveBtn').textContent=immersive?'退出沉浸':'沉浸看房';$('immersiveBtn').setAttribute('aria-pressed',String(immersive));invalidate();}
  function tick(now){frame=0;if(disposed||document.hidden)return;const dt=Math.min(Math.max((now-last)/1000,.001),.05);last=now;let keep=false;
    if(mode==='walk'){const f=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')),s=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft')),v=Number(keys.has('ShiftLeft')||keys.has('ShiftRight'))-Number(keys.has('ControlLeft')||keys.has('ControlRight'));if(f||s||v){const step=dt/(Math.hypot(f,s)||1);dirty=move((-Math.sin(yaw)*f+Math.cos(yaw)*s)*step,v*dt*.8,(-Math.cos(yaw)*f-Math.sin(yaw)*s)*step)||dirty;keep=true;}camera.rotation.set(pitch,yaw,0,'YXZ');}
    else if(orbit.update()){dirty=true;keep=true;}
    keep=updateInteractions(dt)||keep;if(dirty){finish.render();dirty=false;}if(keep&&!frame)frame=requestAnimationFrame(tick);
  }
  orbit.addEventListener('change',()=>invalidate());
  canvas.addEventListener('pointerdown',e=>{if(mode!=='walk'||e.button!==0)return;canvas.focus({preventScroll:true});drag={x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,id:e.pointerId,moved:false};canvas.setPointerCapture(e.pointerId);canvas.style.cursor='grabbing';last=performance.now();});
  canvas.addEventListener('pointermove',e=>{if(mode!=='walk')return;if(locked){yaw-=e.movementX*.002;pitch-=e.movementY*.002;if(drag&&(Math.abs(e.movementX)+Math.abs(e.movementY)>2))drag.moved=true;dirty=true;invalidate();}else if(drag?.id===e.pointerId){const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.hypot(e.clientX-drag.startX,e.clientY-drag.startY)>5)drag.moved=true;if(drag.moved){yaw-=dx*.004;pitch-=dy*.003;invalidate();}drag.x=e.clientX;drag.y=e.clientY;}else canvas.style.cursor=pick(e.clientX,e.clientY)?'pointer':'grab';pitch=THREE.MathUtils.clamp(pitch,-1.5,1.5);});
  canvas.addEventListener('pointerup',e=>{const action=drag&&drag.id===e.pointerId&&!drag.moved;drag=null;if(action)activate(pick(e.clientX,e.clientY));canvas.style.cursor='grab';if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);});
  for(const type of ['pointercancel','lostpointercapture'])canvas.addEventListener(type,()=>{drag=null;canvas.style.cursor='grab';});
  canvas.addEventListener('dblclick',()=>{if(mode==='walk')canvas.requestPointerLock?.()?.catch(()=>{});});
  document.addEventListener('pointerlockchange',()=>{locked=document.pointerLockElement===canvas;$('crosshair').hidden=!locked;drag=null;});
  const movement=['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight','ControlLeft','ControlRight'];
  window.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]'))return;if(e.code==='KeyH'&&!e.repeat)toggleImmersive();if((e.code==='Enter'||e.code==='Space')&&document.activeElement===canvas&&!e.repeat){e.preventDefault();const rect=canvas.getBoundingClientRect();activate(pick(rect.left+rect.width/2,rect.top+rect.height/2));}if(movement.includes(e.code)){e.preventDefault();keys.add(e.code);last=performance.now();invalidate();}});
  window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',clearInput);
  for(const b of document.querySelectorAll('[data-move]')){const code={forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',up:'ShiftLeft',down:'ControlLeft'}[b.dataset.move];b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(code);b.classList.add('held');last=performance.now();invalidate();});for(const type of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(type,()=>{keys.delete(code);b.classList.remove('held');});}
  $('walkBtn').onclick=()=>go('entry');$('overviewBtn').onclick=()=>go('overview');$('resetBtn').onclick=()=>{go(mode==='overview'?'overview':'entry');canvas.focus({preventScroll:true});};$('immersiveBtn').onclick=toggleImmersive;
  $('fullscreenBtn').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{toast('当前浏览器暂不支持全屏');}};
  document.addEventListener('fullscreenchange',()=>{$('fullscreenBtn').setAttribute('aria-label',document.fullscreenElement?'退出全屏':'全屏');resize();});
  $('archiveHomeBtn').onclick=async e=>{e.preventDefault();const href=e.currentTarget.href;entered=false;audio.setActive(false);clearInput();if(document.pointerLockElement)document.exitPointerLock();if(document.fullscreenElement)try{await document.exitFullscreen();}catch{}location.assign(href);};
  $('helpBtn').onclick=()=>{clearInput();if(document.pointerLockElement)document.exitPointerLock();$('helpDialog').showModal();};for(const b of document.querySelectorAll('#helpDialog .close,#helpDialog .close-action'))b.onclick=()=>$('helpDialog').close();
  for(const type of ['selectstart','dragstart','contextmenu'])$('app').addEventListener(type,e=>e.preventDefault());
  window.addEventListener('resize',resize);window.visualViewport?.addEventListener('resize',resize);
  document.addEventListener('visibilitychange',()=>{clearInput();last=performance.now();audio.setActive(entered&&!document.hidden);if(document.hidden){cancelAnimationFrame(frame);frame=0;}else invalidate();});
  const state=()=>({room:'Courtyard43',revision:manifest.revision,stage:'interior',structureApproved:true,mode,position:camera.position.toArray(),yaw,pitch,immersive,fullscreen:!!document.fullscreenElement,lightOn,lockOn,curtainOpen:curtain?.target===1,curtainAmount:curtain?.amount??0,sound:audio.state,interactions:interactions.map(({id,kind,amount,target,blocked,openAngle,defaultOpen})=>({id,kind,amount,target,blocked,openAngle,defaultOpen:!!defaultOpen})),rendering:{drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,renderCount:finish.frames,batchedMeshes:batching.removed,batches:batching.created,collisionSurfaces:navigation.surfaces,collisionRadius:navigation.radius},assetStatistics:statistics});
  window.courtyard43Diagnostics={get state(){return state();},canTravel:(a,b)=>navigation.canTravel(new THREE.Vector3(...a),new THREE.Vector3(...b)),navigate:go,interact:(id,value)=>{const item=byId.get(id);if(!item)throw Error('Unknown object');activate(item,value);return state();},getObjectBounds:name=>landmarks.get(name)?.clone()};
  const lifecycle=new AbortController(),register=t=>{try{Promise.resolve(document.modelContext?.registerTool(t,{signal:lifecycle.signal})).catch(()=>{});}catch{}};
  register({name:'get_courtyard43_view',description:'读取Courtyard43成品房间的视角、材质版本、门帘开关、静音与实际渲染计数。',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:state});
  register({name:'navigate_courtyard43',description:'切换Courtyard43入口、床边、桌面、阳台、反看、总览及物件近景。',inputSchema:{type:'object',properties:{viewpoint:{type:'string',enum:viewNames}},required:['viewpoint'],additionalProperties:false},execute({viewpoint}){go(viewpoint);return state();}});
  register({name:'walk_courtyard43',description:'沿当前视角小步移动，使用真实实体表面检查阻挡。',inputSchema:{type:'object',properties:{direction:{type:'string',enum:['forward','back','left','right','up','down']},distance:{type:'number',minimum:.01,maximum:2}},required:['direction','distance'],additionalProperties:false},execute({direction,distance}){if(mode!=='walk'||!['forward','back','left','right','up','down'].includes(direction)||!Number.isFinite(distance)||distance<.01||distance>2)throw Error('Invalid movement');const start=camera.position.clone(),f=direction==='forward'?1:direction==='back'?-1:0,s=direction==='right'?1:direction==='left'?-1:0,n=Math.ceil(distance/.02),step=distance/n;for(let i=0;i<n;i++)move((-Math.sin(yaw)*f+Math.cos(yaw)*s)*step,(direction==='up'?1:direction==='down'?-1:0)*step,(-Math.cos(yaw)*f-Math.sin(yaw)*s)*step);invalidate();return{...state(),distanceMoved:start.distanceTo(camera.position)};}});
  register({name:'interact_courtyard43',description:'通过同一状态控制器操作已建模窗帘、双柜门、房门、开关和反锁。',inputSchema:{type:'object',properties:{id:{type:'string',enum:interactions.map(x=>x.id)},open:{type:'boolean'}},required:['id'],additionalProperties:false},execute({id,open}){const item=byId.get(id);if(!item)throw Error('Unknown object');activate(item,open);return state();}});
  window.addEventListener('pagehide',e=>{entered=false;audio.setActive(false);clearInput();cancelAnimationFrame(frame);frame=0;if(!e.persisted){disposed=true;lifecycle.abort();audio.dispose();finish.dispose();lighting.dispose();orbit.dispose();renderer.dispose();} });
  window.addEventListener('pageshow',e=>{if(e.persisted){entered=true;void audio.setMuted(true);audio.setActive(!document.hidden);last=performance.now();resize();}});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();cancelAnimationFrame(frame);frame=0;audio.setActive(false);failRoomLoading();$('errorDetail').textContent='图形显示暂时中断，请重新打开房间。';});
  go('entry');resize();reportRoomLoading(94,'正在准备光影');await renderer.compileAsync(scene,camera);finish.render();await finishRoomLoading();entered=true;audio.setActive(!document.hidden);last=performance.now();invalidate();
}catch(error){console.error('Courtyard43 failed',error);audio.setActive(false);failRoomLoading();$('errorDetail').textContent=error.message||'请检查连接，或使用支持 WebGL 的浏览器。';}
