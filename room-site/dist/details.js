import {addLaptop,addLumbarCushion} from './precision-models.js?v=blender18';
import {addBathroom} from './bathroom.js?v=blender18';
import {createHelmet,createRacket,createCap} from './wardrobe-assets.js?v=blender18';
import {addFloralBasket} from './floral-basket.js?v=blender18';
import {addDeskProps} from './desk-props.js?v=blender18';
import {addReferenceMug} from './reference-mug.js?v=blender18';
import {addShelfGundam} from './shelf-gundam.js?v=blender18';
export function addDetails(ctx) {
  const {THREE,world,scene,M,mat,box,cylinder,ellipsoid,rod,path,obstacle,desk,chair,wardrobe,curtainPanels,cutaway,ceilings,texture}=ctx;
  function canvasMap(draw,w=512,h=512){const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;}
  // Fine curtain embroidery, repeated sparsely over the pleated fabric.
  const lace=canvasMap((c,w,h)=>{c.fillStyle='#ece2c8';c.fillRect(0,0,w,h);for(let i=0;i<15000;i++){const x=(i*83)%w,y=(i*197)%h;c.fillStyle=i%2?'#fff9ed13':'#9f95681a';c.fillRect(x,y,1,3);}for(let row=0;row<4;row++)for(let col=0;col<3;col++){const x=col*166+80,y=row*126+55;c.fillStyle='#fff9e66b';c.fillRect(x-21,y-32,42,64);c.strokeStyle='#a8a27a60';c.lineWidth=2;c.beginPath();c.moveTo(x,y+24);c.lineTo(x,y-8);c.stroke();for(let s of [-1,1]){c.beginPath();c.ellipse(x+s*7,y+8,4,9,s*.65,0,Math.PI*2);c.fillStyle='#afa98475';c.fill();}c.beginPath();c.moveTo(x-9,y-22);c.bezierCurveTo(x-10,y-1,x+9,y-1,x+10,y-22);c.lineTo(x+3,y-16);c.lineTo(x,y-24);c.lineTo(x-3,y-16);c.closePath();c.fill();}c.fillStyle='#c2b38e';c.fillRect(0,0,w,9);c.fillRect(0,h-13,w,13);});
  for(const panel of curtainPanels){panel.material.map=lace;panel.material.needsUpdate=true;const fringe=new THREE.Group();panel.add(fringe);for(let i=0;i<130;i++){const x=-1+i/64.5;rod([x,-.96,0],[x+.003,-1.008,.004],.0018,M.cloth,fringe);} }
  // Photo-guided tabletop props replace the previous placeholder primitives.
  addDeskProps(ctx);
  addReferenceMug(ctx);
  addLaptop(ctx);
  // Woven basket and dried daisies on the shelf nearest the entrance.
  addFloralBasket(ctx);
  addShelfGundam(ctx);
  addLumbarCushion(ctx);
  // The carbon full-face helmet rests on top; two tennis rackets and a separate cap hang on the wood side.
  const helmet=createHelmet(THREE);helmet.position.set(.005,2.125,.18);helmet.rotation.set(-.18,.42,0);wardrobe.add(helmet);
  // Rest the solid lower rim on the actual cabinet top, after its resting tilt.
  wardrobe.updateMatrixWorld(true);
  const support=helmet.getObjectByName('lower-shell-rubber-trim');
  const supportBounds=new THREE.Box3().setFromObject(support,true);
  helmet.position.y+=wardrobe.position.y+2.1225-supportBounds.min.y;
  helmet.userData.supportHeight=2.1225;
  for(const [x,y,angle,variant]of [[.12,1.16,-.045,0],[-.09,.68,.07,1]]){
    const racket=createRacket(THREE,{variant});racket.position.set(x,y,.613);racket.rotation.z=angle;wardrobe.add(racket);
    box(.017,.022,.014,M.metal,x-Math.sin(angle)*.64,y+Math.cos(angle)*.64,.611,wardrobe,.004);
  }
  const cap=createCap(THREE);cap.position.set(-.145,1.78,.67);cap.rotation.x=1.05;cap.rotation.z=-.14;wardrobe.add(cap);
  wardrobe.updateMatrixWorld(true);const capBounds=new THREE.Box3().setFromObject(cap);cap.position.z+=wardrobe.position.z+.597-capBounds.min.z;
  rod([-.145,1.82,.586],[-.145,1.82,cap.position.z-.025],.004,M.metal,wardrobe);
  for(const prop of [helmet,cap,...wardrobe.children.filter(o=>o.name.startsWith('Tennis'))])prop.traverse(o=>{if(o.isMesh){o.castShadow=!o.material.transparent;o.receiveShadow=true;}});
  // Switch, outlets and the small mark in the pink wallpaper.
  const wallSwitch=new THREE.Group();wallSwitch.name='clickable-wall-switch';wallSwitch.userData.interactive='light';world.add(wallSwitch);
  box(.018,.085,.085,M.white,1.387,1.12,.86,wallSwitch);const rocker=box(.022,.034,.053,M.trim,1.372,1.12,.86,wallSwitch);rocker.name='light-switch-rocker';
  box(.016,.075,.13,M.white,1.389,.91,-1.10);for(const z of [-1.13,-1.07])for(const y of [.90,.918])box(.017,.012,.006,M.dark,1.378,y,z);
  box(.003,.018,.027,M.dark,1.395,1.76,-.65);
  addBathroom(ctx);
}
