// Structural review only. Geometry is authored and exported by official Blender
// Lab MCP; this viewer does not synthesize persistent room meshes.
import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {parseBlenderRoom} from './blender-room.js?v=pages1';
import {loadRoomBinary} from './room-binary.js?v=pages1';
import {startRoomLoading,reportRoomLoading,finishRoomLoading,failRoomLoading} from './room-loading.js?v=viewer26';

const $=id=>document.getElementById(id),canvas=$('world');
startRoomLoading();
try {
  const response=await fetch('./assets/rooms/Courtyard43/scene.json?v=courtyard43-whitebox02');
  if(!response.ok)throw Error(`房间清单读取失败 (${response.status})`);
  const manifest=await response.json();
  if(manifest.roomId!=='Courtyard43'||manifest.stage!=='whitebox')throw Error('白模资料版本不匹配');
  const buffer=await loadRoomBinary(manifest,p=>reportRoomLoading(8+p*72,'正在载入结构白模'));
  const {world,refs}=parseBlenderRoom(THREE,manifest,buffer,[]);
  const scene=new THREE.Scene();scene.background=new THREE.Color('#dfe3e3');scene.add(world);
  const renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'high-performance'});
  renderer.setPixelRatio(Math.min(devicePixelRatio,1.35));
  renderer.outputColorSpace=THREE.SRGBColorSpace;
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;
  // Neutral review illumination, not a claim about the real compass/time.
  scene.add(new THREE.HemisphereLight('#ffffff','#c5c1b9',2.2));
  const light=new THREE.DirectionalLight('#ffffff',2);light.position.set(-1.2,5,-4);
  light.target.position.set(0,0,1);light.castShadow=true;light.shadow.mapSize.set(1024,1024);
  Object.assign(light.shadow.camera,{left:-4,right:4,top:5,bottom:-5,near:.1,far:14});
  light.shadow.normalBias=.018;scene.add(light,light.target);
  const camera=new THREE.PerspectiveCamera(64,1,.003,40);camera.rotation.order='YXZ';
  const orbit=new OrbitControls(camera,canvas);orbit.enabled=false;orbit.enableDamping=true;
  orbit.minDistance=3;orbit.maxDistance=12;orbit.maxPolarAngle=Math.PI*.47;
  let mode='walk',yaw=0,pitch=0,drag=null,locked=false,immersive=false,last=performance.now(),signature='',frame=0;
  let renderCount=0;
  const keys=new Set(),surfaces=[],ray=new THREE.Raycaster(),dir=new THREE.Vector3(),segment=new THREE.Box3();
  world.updateMatrixWorld(true);
  world.traverse(o=>{if(o.isMesh&&!o.material.transparent&&!o.userData.noCollision){o.geometry.computeBoundingBox();surfaces.push({object:o,bounds:o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld)});}});
  const p=manifest.review,r=p.room;
  function canTravel(from,to){
    if(to.x<=-r.width/2+.002||to.x>=r.width/2-.002||to.z<=-p.balcony.depth+.025||to.z>=r.depth-.002||to.y<.025||to.y>r.height-.02)return false;
    dir.subVectors(to,from);const distance=dir.length();if(distance<1e-8)return true;
    dir.divideScalar(distance);ray.set(from,dir);ray.near=0;ray.far=distance+.002;
    segment.setFromPoints([from,to]);segment.expandByScalar(.002);
    return !surfaces.some(({object,bounds})=>segment.intersectsBox(bounds)&&ray.intersectObject(object,false).length);
  }
  function move(dx,dy,dz){
    for(const [axis,delta] of [['x',dx],['y',dy],['z',dz]]){
      if(!delta)continue;const target=camera.position.clone();target[axis]+=delta;
      if(canTravel(camera.position,target))camera.position.copy(target);
    }
  }
  function clearInput(){keys.clear();drag=null;document.querySelectorAll('.held').forEach(b=>b.classList.remove('held'));}
  function go(view){
    const v=p.viewpoints[view];if(!v)throw Error('Unknown viewpoint');
    mode=view==='overview'?'overview':'walk';clearInput();
    camera.near=mode==='overview'?.05:.003;camera.updateProjectionMatrix();
    [...refs.cutaway,...refs.ceilings].forEach(o=>o.visible=mode!=='overview');
    camera.position.fromArray(v.position);camera.lookAt(new THREE.Vector3(...v.target));
    yaw=camera.rotation.y;pitch=camera.rotation.x;
    orbit.enabled=mode==='overview';orbit.target.fromArray(v.target);if(orbit.enabled)orbit.update();
    $('walkBtn').classList.toggle('active',mode==='walk');$('overviewBtn').classList.toggle('active',mode==='overview');
    $('walkBtn').setAttribute('aria-pressed',String(mode==='walk'));$('overviewBtn').setAttribute('aria-pressed',String(mode==='overview'));
    $('app').classList.toggle('overview',mode==='overview');
    if(document.pointerLockElement)document.exitPointerLock();
    renderer.shadowMap.needsUpdate=true;signature='';
  }
  function resize(){
    const width=$('app').clientWidth,height=$('app').clientHeight;if(!width||!height)return;
    camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height,false);signature='';
    $('app').classList.toggle('touch-device',matchMedia('(pointer: coarse)').matches||innerWidth<=900);
  }
  function toggleImmersive(){immersive=!immersive;$('app').classList.toggle('immersive',immersive);$('immersiveBtn').textContent=immersive?'退出沉浸':'沉浸看房';$('immersiveBtn').setAttribute('aria-pressed',String(immersive));}
  canvas.addEventListener('pointerdown',e=>{if(mode!=='walk')return;canvas.focus();drag={x:e.clientX,y:e.clientY,id:e.pointerId};canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{
    if(mode!=='walk')return;
    if(locked){yaw-=e.movementX*.002;pitch-=e.movementY*.002;}
    else if(drag?.id===e.pointerId){yaw-=(e.clientX-drag.x)*.004;pitch-=(e.clientY-drag.y)*.003;drag.x=e.clientX;drag.y=e.clientY;}
    pitch=THREE.MathUtils.clamp(pitch,-1.5,1.5);
  });
  for(const type of ['pointerup','pointercancel','lostpointercapture'])canvas.addEventListener(type,()=>drag=null);
  canvas.addEventListener('dblclick',()=>{if(mode==='walk')canvas.requestPointerLock?.()?.catch(()=>{});});
  document.addEventListener('pointerlockchange',()=>{locked=document.pointerLockElement===canvas;});
  const movement=['KeyW','KeyA','KeyS','KeyD','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight','ControlLeft','ControlRight'];
  window.addEventListener('keydown',e=>{if(document.querySelector('dialog[open]'))return;if(e.code==='KeyH'&&!e.repeat)toggleImmersive();if(movement.includes(e.code)){e.preventDefault();keys.add(e.code);}});
  window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',clearInput);
  document.addEventListener('visibilitychange',()=>{clearInput();last=performance.now();});
  for(const b of document.querySelectorAll('[data-move]')){
    const code={forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',up:'ShiftLeft',down:'ControlLeft'}[b.dataset.move];
    b.addEventListener('pointerdown',e=>{e.preventDefault();b.setPointerCapture(e.pointerId);keys.add(code);b.classList.add('held');});
    for(const type of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(type,()=>{keys.delete(code);b.classList.remove('held');});
  }
  $('walkBtn').onclick=()=>go('entry');$('overviewBtn').onclick=()=>go('overview');
  $('resetBtn').onclick=()=>{go(mode==='overview'?'overview':'entry');canvas.focus({preventScroll:true});};
  $('immersiveBtn').onclick=toggleImmersive;
  $('fullscreenBtn').onclick=async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{}};
  document.addEventListener('fullscreenchange',()=>{$('fullscreenBtn').setAttribute('aria-label',document.fullscreenElement?'退出全屏':'全屏');resize();});
  $('helpBtn').onclick=()=>{clearInput();if(document.pointerLockElement)document.exitPointerLock();$('helpDialog').showModal();};
  for(const b of document.querySelectorAll('#helpDialog .close,#helpDialog .close-action'))b.onclick=()=>$('helpDialog').close();
  for(const type of ['selectstart','dragstart','contextmenu'])$('app').addEventListener(type,e=>e.preventDefault());
  window.addEventListener('resize',resize);window.visualViewport?.addEventListener('resize',resize);
  const state=()=>({room:'Courtyard43',revision:manifest.revision,stage:'whitebox',structureApproved:false,mode,position:camera.position.toArray(),yaw,pitch,muted:true,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,renderCount,surfaces:surfaces.length});
  window.whiteboxDiagnostics={get state(){return state();},canTravel:(a,b)=>canTravel(new THREE.Vector3(...a),new THREE.Vector3(...b))};
  const lifecycle=new AbortController();
  const register=t=>{try{Promise.resolve(document.modelContext?.registerTool(t,{signal:lifecycle.signal})).catch(()=>{});}catch{}};
  register({name:'get_whitebox_view',description:'读取 Courtyard43 白模视角、版本及渲染数据。',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:state});
  register({name:'navigate_whitebox',description:'切换白模六个核对视角；用于查看待确认结构。',inputSchema:{type:'object',properties:{view:{type:'string',enum:Object.keys(p.viewpoints)}},required:['view'],additionalProperties:false},execute({view}){go(view);return state();}});
  register({name:'walk_whitebox',description:'在白模中沿当前朝向移动并检查真实网格阻挡。',inputSchema:{type:'object',properties:{direction:{type:'string',enum:['forward','back','left','right','up','down']},distance:{type:'number',minimum:.05,maximum:2}},required:['direction','distance'],additionalProperties:false},execute({direction,distance}){if(mode!=='walk'||!['forward','back','left','right','up','down'].includes(direction)||!Number.isFinite(distance)||distance<.05||distance>2)throw Error('Invalid movement');const start=camera.position.clone(),f=direction==='forward'?1:direction==='back'?-1:0,s=direction==='right'?1:direction==='left'?-1:0,n=Math.ceil(distance/.025),step=distance/n;for(let i=0;i<n;i++)move((-Math.sin(yaw)*f+Math.cos(yaw)*s)*step,(direction==='up'?1:direction==='down'?-1:0)*step,(-Math.cos(yaw)*f-Math.sin(yaw)*s)*step);return{...state(),distanceMoved:start.distanceTo(camera.position)};}});
  function tick(now){
    frame=requestAnimationFrame(tick);const dt=Math.min((now-last)/1000,.05);last=now;if(document.hidden)return;
    if(mode==='walk'){
      const f=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown'));
      const s=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft'));
      const v=Number(keys.has('ShiftLeft')||keys.has('ShiftRight'))-Number(keys.has('ControlLeft')||keys.has('ControlRight'));
      const step=dt/(Math.hypot(f,s)||1);move((-Math.sin(yaw)*f+Math.cos(yaw)*s)*step,v*dt*.8,(-Math.cos(yaw)*f-Math.sin(yaw)*s)*step);
      camera.rotation.set(pitch,yaw,0,'YXZ');
    }else orbit.update();
    const next=[mode,...camera.position.toArray(),...camera.quaternion.toArray(),camera.aspect].join('/');
    if(next!==signature){renderer.render(scene,camera);signature=next;renderCount++;}
  }
  window.addEventListener('pagehide',e=>{clearInput();if(!e.persisted){cancelAnimationFrame(frame);lifecycle.abort();renderer.dispose();orbit.dispose();}},{once:true});
  go('entry');resize();reportRoomLoading(94,'正在准备白模视图');await renderer.compileAsync(scene,camera);
  renderer.render(scene,camera);await finishRoomLoading();frame=requestAnimationFrame(tick);
} catch(error) {
  console.error('Courtyard43 whitebox failed',error);failRoomLoading();
  $('errorDetail').textContent=error.message;
}
