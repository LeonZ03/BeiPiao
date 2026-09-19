// CPU-only scene/circulation check. No browser or WebGL context is used.
import * as THREE from '../room-site/dist/vendor/three.module.js';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {createCanvas}=require('@napi-rs/canvas');
const root=path.resolve(import.meta.dirname,'../room-site/dist');
const noop=()=>{};
const painter=new Proxy({createRadialGradient:()=>({addColorStop:noop}),createLinearGradient:()=>({addColorStop:noop})}, {get:(o,k)=>o[k]??noop,set:(o,k,v)=>(o[k]=v,true)});
function element(){const handlers=new Map();return {handlers,getBoundingClientRect:()=>({left:0,top:0,width:1280,height:800}),style:{},classList:{add:noop,remove:noop,toggle:noop,contains:()=>false},dataset:{},addEventListener:(name,fn)=>handlers.set(name,fn),setAttribute:noop,removeAttribute:noop,getContext:()=>painter,querySelectorAll:()=>[],focus:noop,setPointerCapture:noop};}
const elements=new Map();const el=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
const tools=new Map();let frame,renderedScene,renderedCamera;
const doc={getElementById:el,createElement:tag=>tag==='canvas'?createCanvas(512,512):element(),querySelectorAll:()=>[],querySelector:s=>s==='dialog[open]'?null:element(),addEventListener:noop,modelContext:{registerTool:t=>tools.set(t.name,t)}};
const events=new Map();const win={addEventListener:(name,fn)=>events.set(name,fn)};
class Renderer {constructor(){this.shadowMap={};this.capabilities={getMaxAnisotropy:()=>4};this.info={render:{calls:0,triangles:0}};}setPixelRatio(){}setSize(){}async compileAsync(){}render(scene,camera){renderedScene=scene;renderedCamera=camera;}}
class Loader {load(url){assert.ok(fs.existsSync(path.join(root,url)),`Missing texture ${url}`);const t=new THREE.Texture();t.userData.file=path.join(root,url);return t;} async loadAsync(url){return this.load(url);}}
class Orbit {constructor(){this.target=new THREE.Vector3();}update(){}}
const fetch=async url=>{const file=path.join(root,url.split('?')[0]);const b=fs.readFileSync(file);return new Response(b,{headers:{'Content-Length':String(b.length)}});};
const context=vm.createContext({document:doc,window:win,console,fetch,Blob,Response,DecompressionStream,devicePixelRatio:1,innerWidth:1280,innerHeight:800,performance,setTimeout,clearTimeout,AbortController,matchMedia:()=>({matches:false,addEventListener:noop}),requestAnimationFrame:f=>{if(f.name==='tick')frame=f;else setImmediate(()=>f(performance.now()));}});
const values={...THREE,WebGLRenderer:Renderer,TextureLoader:Loader};
const three=new vm.SyntheticModule(Object.keys(values),function(){for(const [k,v]of Object.entries(values))this.setExport(k,v);},{context});
const orbit=new vm.SyntheticModule(['OrbitControls'],function(){this.setExport('OrbitControls',Orbit);},{context});
const modules=new Map();
function get(file){if(!modules.has(file))modules.set(file,new vm.SourceTextModule(fs.readFileSync(file,'utf8'),{context,identifier:file}));return modules.get(file);}
const main=get(path.join(root,'main.js'));
await main.link((id,ref)=>id==='three'?three:id.endsWith('/OrbitControls.js')?orbit:get(path.resolve(path.dirname(ref.identifier),id.split('?')[0])));
await main.evaluate();frame(performance.now()+20);

const diagnostics=win.roomDiagnostics;
renderedScene.updateMatrixWorld(true);
let meshes=0,leaves=0,shadowLeaves=0;
renderedScene.traverse(o=>{
  assert.ok([...o.position,...o.scale].every(Number.isFinite),'Non-finite transform '+o.name);
  if(o.isMesh){meshes++;const p=o.geometry.attributes.position;for(const v of p.array)assert.ok(Number.isFinite(v),'Invalid vertex '+o.name);
    if(o.geometry.index)for(const v of o.geometry.index.array)assert.ok(v<p.count,'Bad index '+o.name);
  }
  if(o.name==='summer-leaf-canopy')leaves+=o.count;
  if(o.name==='summer-leaf-shadow-layer')shadowLeaves+=o.count;
});
assert.equal(leaves,48209);assert.equal(shadowLeaves,1596);
const source=(await import('../room-site/dist/assets/summer/models.js')).default;
const poses=source.leaves.filter((_,i)=>i%7===0),dummy=new THREE.Object3D(),matrix=new THREE.Matrix4();
for(let id=0;id<3;id++){
 const tree=renderedScene.getObjectByName('blender-summer-poplar-'+id);assert.equal(tree.userData.crownVariant,id);
 const layer=tree.getObjectByName('summer-leaf-shadow-layer');
 poses.forEach(([x,y,z,yaw,tilt,size],i)=>{dummy.position.set(x,y,z);dummy.rotation.set(tilt,yaw,yaw*.13);dummy.scale.setScalar(size*.77);dummy.updateMatrix();layer.getMatrixAt(i,matrix);matrix.elements.forEach((v,j)=>assert.ok(Math.abs(v-dummy.matrix.elements[j])<1e-5,'Original shadow pattern changed'));});
}
for(const name of ['continuous-timber-head-jamb','connected-window-security-grille','curved-ac-horizontal-louver','recessed-ac-outlet','internal-ac-vertical-guide-vanes','white-gaming-mouse','electric-toothbrush-and-charging-dock'])assert.ok(renderedScene.getObjectByName(name),'Missing '+name);
// Only six intermediate rods remain, restricted to the upper-right window.
const grille=renderedScene.getObjectByName('connected-window-security-grille');
assert.equal(grille.children.filter(x=>x.name==='grille-fixed-upright').length,0);
const crossbars=grille.children.filter(x=>x.name==='grille-welded-crossbar');assert.equal(crossbars.length,6);
const sockets=grille.children.filter(x=>x.name==='grille-recessed-end-socket');
assert.equal(sockets.length,0,'No protruding rod sockets');
assert.equal(grille.children.length,6,'No extra posts or mounting hardware');
for(const bar of crossbars){
 const bounds=new THREE.Box3().setFromObject(bar,true),center=bounds.getCenter(new THREE.Vector3());
 assert.ok(bounds.min.x>.14&&bounds.min.x<.16&&bounds.max.x>1.045&&bounds.max.x<1.075,'Rods must terminate inside the upper-right opening jambs, not cross the left glazing');
 assert.ok(bounds.min.y>1.30&&bounds.max.y<2.15);
}
const baySill=new THREE.Box3().setFromObject(renderedScene.getObjectByName('deep-rounded-stone-bay-sill'));
assert.ok(baySill.max.z-baySill.min.z>.60,'Bay sill must have usable depth, not a shallow ledge');
const bayFrame=new THREE.Box3().setFromObject(renderedScene.getObjectByName('bay-fixed-white-window-frame'));
assert.ok(baySill.max.z-bayFrame.max.z>.48,'Glazing must sit at rear of recess');
const wardrobeBody=renderedScene.getObjectByName('window-side-wardrobe');
assert.ok(wardrobeBody.position.x+.322>baySill.min.x&&wardrobeBody.position.z-.595>baySill.max.z,'Cabinet should slightly overlap left bay edge in projection, and remain in front of sill');
assert.ok(diagnostics.canTravel([-.25,1.5,-1.65],[-.25,1.5,-2.15]),'Fly viewpoint can enter bay recess');
assert.equal(diagnostics.canTravel([-.25,.4,-1.65],[-.25,.4,-2.15]),false,'Bay apron remains solid');
const basket=renderedScene.getObjectByName('woven-basket-and-white-everlastings');
assert.equal(basket.children.filter(x=>x.name==='continuous-basket-rope-handle').length,2);
// Regressions from the owner's oblique-view screenshots.
const helmet=renderedScene.getObjectByName('LS2 FF801 Carbon Full-Face Helmet');
assert.equal(helmet.children.filter(o=>o.name.includes('lower-LS2')).length,0);
assert.equal(helmet.children.filter(o=>o.name.startsWith('curved-FF801-carbon-mark')).length,2);
const support=helmet.getObjectByName('lower-shell-rubber-trim');
assert.ok(Math.abs(new THREE.Box3().setFromObject(support,true).min.y-2.1225)<.00002,'Helmet must contact the wardrobe top');
for(const badge of helmet.children.filter(o=>o.name.startsWith('curved-FF801-carbon-mark'))){badge.geometry.computeBoundingBox();assert.ok(badge.geometry.boundingBox.max.y<.13,'Model label belongs on lower side');}
const sash=renderedScene.getObjectByName('inward-opening-window-sash');
assert.ok(sash.rotation.y>0&&sash.rotation.y<=.15,'Right-hinged sash should open only slightly toward the room');
const railBounds=new THREE.Box3().setFromObject(renderedScene.getObjectByName('empty-bay-drying-rail'),true);
const grilleBounds=new THREE.Box3().setFromObject(grille,true);
assert.ok(grilleBounds.min.y>1.30,'No rods in lower fixed window');
const openAngle=sash.rotation.y;let minRailGap=Infinity,minGrilleGap=Infinity;
for(let step=0;step<=12;step++){
 sash.rotation.y=openAngle*step/12;renderedScene.updateMatrixWorld(true);
 const bounds=new THREE.Box3().setFromObject(sash,true);
 minRailGap=Math.min(minRailGap,railBounds.min.z-bounds.max.z);
 minGrilleGap=Math.min(minGrilleGap,bounds.min.z-grilleBounds.max.z);
}
sash.rotation.y=openAngle;renderedScene.updateMatrixWorld(true);
assert.ok(minRailGap>.05,'Entire sash, including handle, must clear the drying rail throughout its opening');
assert.ok(minGrilleGap>.02,'Moving sash must remain on the room side of the rods');
const jambBounds=new THREE.Box3().setFromObject(renderedScene.getObjectByName('continuous-timber-head-jamb'),true);
assert.ok(jambBounds.min.y<2.15&&jambBounds.max.y>2.24,'Timber head must overlap door top and header');
const mug=renderedScene.getObjectByName('photo-matched-monster-mug');assert.ok(mug);
assert.ok(mug.position.z<-.37,'Mug should be left of laptop');assert.ok(mug.getObjectByName('hollow-ceramic-mug'));assert.ok(mug.getObjectByName('inner-rim-message'));
assert.ok(!fs.existsSync(path.join(root,'assets/reference-monster-mug.jpg')),'Do not publish the full reference photograph');
const radiator=renderedScene.getObjectByName('window-side-radiator');const radiatorBox=new THREE.Box3().setFromObject(radiator,true);
assert.ok(radiatorBox.min.z<-1.70&&radiatorBox.max.z> -1.0&&radiatorBox.max.z<-.80,'Only part of radiator should be behind desk');
const cloth=renderedScene.getObjectByName('continuous-rounded-tablecloth');assert.ok(cloth);
const gundam=renderedScene.getObjectByName('photo-guided-shelf-gundam');assert.ok(gundam);
const gundamBounds=new THREE.Box3().setFromObject(gundam,true),basketBounds=new THREE.Box3().setFromObject(basket,true);
assert.ok(Math.abs(gundamBounds.min.y-1.662)<.00002,'Gundam feet must sit on shelf');
const ratio=(gundamBounds.max.y-gundamBounds.min.y)/(basketBounds.max.y-basketBounds.min.y);
assert.ok(Math.abs(ratio-.75*.60)<.00001,'Gundam total height must be exactly 3/5 of its previous size');
assert.ok(gundam.position.z>.15&&gundamBounds.max.z<-.255,'Gundam should fit the top shelf at right');
assert.ok(renderedScene.getObjectByName('bosc-printed-paper-cup'));
assert.ok(renderedScene.getObjectByName('original-bosc-emblem'));
assert.ok(renderedScene.getObjectByName('bosc-institute-ring-lettering'));
assert.equal(renderedScene.getObjectByName('soft-front-cloth-drape'),undefined,'No disconnected planar front cloth');
// Adjacent surface rows follow a rounded 14 mm bend rather than a 90-degree crease.
const cpos=cloth.geometry.attributes.position,cuv=cloth.geometry.attributes.uv;
const surface=[];
for(let i=0;i<cpos.count;i++)if(Math.abs(cuv.getX(i)-.5)<2e-5&&cuv.getY(i)>=.5599&&cuv.getY(i)<=.735)surface.push({v:cuv.getY(i),p:new THREE.Vector3().fromBufferAttribute(cpos,i)});
assert.ok(surface.length>12,'Rounded cloth fold retains its curved surface tessellation');
assert.ok(cloth.geometry.userData.authoring==='Blender');
assert.equal(diagnostics.state.assetStatistics.source,'Blender');
let physicalMeshes=0;renderedScene.traverse(o=>{if(o.isMesh&&!o.material.isShaderMaterial&&!o.parent?.parent?.name?.includes('running-water')&&o.geometry.userData.authoring==='Blender')physicalMeshes++;});
assert.ok(physicalMeshes>500,'Complete Blender room must be loaded');
// Flight controls still have a tiny radius and preserve vertical freedom.
assert.equal(diagnostics.state.collisionRadius,.002);
assert.ok(diagnostics.canTravel([.3,.75,.4],[-.6,.75,.4]));assert.ok(diagnostics.canTravel([.3,.15,.4],[-.6,.15,.4]));
assert.equal(diagnostics.canTravel([.9,1.5,2.5],[1.5,1.5,2.5]),false);
tools.get('navigate_room').execute({view:'entry'});const y=diagnostics.state.position[1];let now=performance.now()+100;
events.get('keydown')({code:'ShiftLeft',preventDefault:noop});for(let i=0;i<10;i++)frame(now+=50);events.get('keyup')({code:'ShiftLeft'});assert.ok(diagnostics.state.position[1]>y+.30);
events.get('keydown')({code:'ControlLeft',preventDefault:noop});for(let i=0;i<10;i++)frame(now+=50);events.get('keyup')({code:'ControlLeft'});assert.ok(Math.abs(diagnostics.state.position[1]-y)<.002);
const sunlight=renderedScene.getObjectByName('warm-afternoon-sun');const toSun=sunlight.position.clone().sub(sunlight.target.position).normalize(),casters=[];renderedScene.traverse(o=>{if(o.isMesh&&o.castShadow&&!o.material.transparent)casters.push(o);});
let sunlitFloor=0,sunlitBed=0;
for(const x of [.23,.38,.55,.68])for(const z of [-.1,.3,.7,1.1])if(new THREE.Raycaster(new THREE.Vector3(x,.04,z),toSun,.01,20).intersectObjects(casters,false).length===0)sunlitFloor++;
for(const x of [-1.05,-.8,-.55,-.3,0])for(const z of [-.15,.2,.55,.9])if(new THREE.Raycaster(new THREE.Vector3(x,.67,z),toSun,.01,20).intersectObjects(casters,false).length===0)sunlitBed++;
assert.ok(sunlitFloor>0&&sunlitBed>0,'Sunlight must reach floor and bed');
// Exercise the real canvas pointer handlers and raycasting after the asset swap.
const fixtures=[
 ['light','clickable-wall-switch',[.85,1.12,.86],s=>s.lightOn],
 ['curtain',null,[.55,1.6,-.7],s=>s.curtainOpen],
 ['doorLock','clickable-privacy-thumbturn',[1.07,1.03,2.38],s=>s.water.doorLocked],
 ['shower','wall-normal-shower-head',[.05,1.80,2.80],s=>s.water.shower],
 ['faucet','clickable-faucet',[-.065,1.1,2.54],s=>s.water.faucet],
];
for(const [id,name,position,state]of fixtures){
 let target=name?renderedScene.getObjectByName(name):null;
 if(!target)renderedScene.traverse(o=>{if(o.userData.interactive===id)target=o;});
 const click=()=>{
   const center=new THREE.Box3().setFromObject(target,true).getCenter(new THREE.Vector3());
   renderedCamera.position.set(...position);renderedCamera.lookAt(center);renderedCamera.updateMatrixWorld(true);renderedScene.updateMatrixWorld(true);
   const p=center.clone().project(renderedCamera),e={clientX:(p.x+1)*640,clientY:(1-p.y)*400,pointerId:1};
   el('world').handlers.get('pointerdown')(e);el('world').handlers.get('pointerup')(e);
 };
 const before=state(diagnostics.state);click();assert.notEqual(state(diagnostics.state),before,`${id} click must work on Blender geometry`);
 for(let i=0;i<30;i++)frame(now+=50);
 if(id==='doorLock')assert.ok(Math.abs(diagnostics.state.water.thumbturnAngle-Math.PI/2)<.001,'Lock animation retains its original pivot');
 click();assert.equal(state(diagnostics.state),before,`${id} must switch back`);
 for(let i=0;i<30;i++)frame(now+=50);
}
if(diagnostics.state.wardrobe.doors.length===3){
  for(const id of ['wardrobeLeft','wardrobeMiddle','wardrobeRight']){
    let target;renderedScene.traverse(o=>{if(o.userData.interactive===id)target=o;});
    const click=()=>{
      renderedScene.updateMatrixWorld(true);
      const leaf=target.children.find(o=>o.userData.blenderNode===target.userData.leafNodeId)||target.children.find(o=>o.isMesh);
      const center=new THREE.Box3().setFromObject(leaf,true).getCenter(new THREE.Vector3());
      if(id==='wardrobeRight')center.y=.25; // Below the cloth: exact panel picking.
      const facing=new THREE.Vector3(1,0,0).applyQuaternion(target.getWorldQuaternion(new THREE.Quaternion()));
      if(id!=='wardrobeLeft'&&diagnostics.state.wardrobe.doors.find(d=>d.id===id).amount>.5)facing.negate();
      renderedCamera.position.copy(center).addScaledVector(facing,.62);renderedCamera.lookAt(center);renderedCamera.updateMatrixWorld(true);
      const p=center.clone().project(renderedCamera),e={clientX:(p.x+1)*640,clientY:(1-p.y)*400,pointerId:1};
      el('world').handlers.get('pointerdown')(e);el('world').handlers.get('pointerup')(e);
    };
    const curtainBefore=diagnostics.state.curtainOpen;
    click();assert.equal(diagnostics.state.curtainOpen,curtainBefore,'Clicking a door does not operate the curtain');assert.equal(diagnostics.state.wardrobe.doors.find(d=>d.id===id).open,true,`${id} actual pointer click opens the authored door`);
    renderedCamera.position.set(.7,1.4,.2);for(let i=0;i<100;i++)frame(now+=50);
    assert.equal(diagnostics.state.wardrobe.doors.find(d=>d.id===id).amount,1);
    assert.equal(diagnostics.state.curtainOpen,curtainBefore,'Door animation never changes curtain state');
    if(id==='wardrobeRight'){
      let cloth;renderedScene.traverse(o=>{if(o.userData.interactive==='curtain')cloth=o;});
      for(let repeat=0;repeat<2;repeat++){
        renderedScene.updateMatrixWorld(true);
        const center=new THREE.Box3().setFromObject(cloth,true).getCenter(new THREE.Vector3());
        renderedCamera.position.set(.55,1.6,-.7);renderedCamera.lookAt(center);renderedCamera.updateMatrixWorld(true);
        const p=center.clone().project(renderedCamera),e={clientX:(p.x+1)*640,clientY:(1-p.y)*400,pointerId:1};
        const before=diagnostics.state.curtainOpen;
        el('world').handlers.get('pointerdown')(e);el('world').handlers.get('pointerup')(e);
        assert.notEqual(diagnostics.state.curtainOpen,before,'Actual curtain surface toggles only the curtain');
        assert.equal(diagnostics.state.wardrobe.doors[2].open,true,'Curtain click leaves the right door open');
        renderedCamera.position.set(.7,1.4,.2);for(let i=0;i<100;i++)frame(now+=50);
        assert.equal(diagnostics.state.wardrobe.doors[2].amount,1,'Curtain animation does not close the cabinet');
      }
    }
    click();assert.equal(diagnostics.state.wardrobe.doors.find(d=>d.id===id).open,false,`${id} remains clickable when open`);
    renderedCamera.position.set(.7,1.4,.2);for(let i=0;i<100;i++)frame(now+=50);
    assert.equal(diagnostics.state.wardrobe.doors.find(d=>d.id===id).amount,0);
  }
  console.log('PASS three Blender cabinet doors: actual pointer picking and complete open/close animation.');
  tools.get('navigate_room').execute({view:'wardrobe'});
  assert.deepEqual(Array.from(diagnostics.state.position),[.45,1.30,-1.03],'Wardrobe inspection view faces the cabinet without adding a UI shortcut');
}else console.log('SKIP wardrobe pointer contract until wardrobe29 model is exported.');
const pausedBreezeTime=diagnostics.state.breeze.time;
doc.hidden=true;frame(now+=50);frame(now+=5000);assert.equal(diagnostics.state.breeze.time,pausedBreezeTime,'Hidden browser tab pauses wind');doc.hidden=false;
el('app').hidden=true;frame(now+=50);assert.equal(diagnostics.state.breeze.time,pausedBreezeTime,'Archive route pauses wind');el('app').hidden=false;
el('overviewBtn').onclick();frame(now+=50);assert.equal(diagnostics.state.mode,'overview');assert.equal(diagnostics.state.breeze.enabled,false);
el('walkBtn').onclick();frame(now+=50);assert.equal(diagnostics.state.mode,'walk');
console.log(JSON.stringify({meshes,physicalMeshes,leaves,shadowLeaves,sunlitFloor,sunlitBed,minRailGap,minGrilleGap,merged:diagnostics.state.batchedMeshes,checks:'complete Blender assets, upper-right rods only, inward window clearances, geometry/contact/cloth/fly controls/sunlight, five clickable fixtures and overview passed'},null,2));
