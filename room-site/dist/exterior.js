import {addSummerTrees} from './summer-refinement.js?v=blender18';
// Relative arrangement comes from the supplied exterior videos. Dimensions are
// proportional estimates, not a site survey. Ground is below the fourth-floor room.
import {createMotorcycle} from './gsx250r.js?v=blender18';
export function addExterior({THREE,world,mat,box,cylinder,rod}){
  const outside=new THREE.Group();outside.name='reference-courtyard';world.add(outside);
  const ground=-9.4;
  function surface(base,kind){
    const c=document.createElement('canvas');c.width=c.height=256;const p=c.getContext('2d');p.fillStyle=base;p.fillRect(0,0,256,256);
    let seed=71;const random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
    for(let i=0;i<23000;i++){const value=random();p.fillStyle=value>.5?'rgba(255,255,235,.07)':'rgba(40,38,29,.07)';const x=random()*256,y=random()*256;p.fillRect(x,y,kind==='bark'?1:2,kind==='bark'?7+random()*24:1);}
    if(kind==='wall')for(let i=0;i<25;i++){p.fillStyle='rgba(73,68,52,.022)';p.fillRect(random()*256,random()*256,2+random()*22,10+random()*80);}
    const map=new THREE.CanvasTexture(c);map.colorSpace=THREE.SRGBColorSpace;map.wrapS=map.wrapT=THREE.RepeatWrapping;map.repeat.set(kind==='wall'?5:8,kind==='bark'?5:4);map.anisotropy=8;return map;
  }
  const concrete=surface('#bec9c7','wall'),road=surface('#868b80','road'),treeBark=surface('#807160','bark');
  // The north-facing facade receives outdoor skylight even while it is shaded.
  const grey=mat('#ffffff',.96,{map:concrete,bumpMap:concrete,bumpScale:.017,emissive:'#93acb2',emissiveIntensity:.25}),edge=mat('#a4aba5',.92),sill=mat('#7b827d',.92);
  const glass=mat('#2e3b37',.69),glassDim=mat('#48534b',.74),cream=mat('#d3d0bd',.96);
  const metal=mat('#4c5550',.7),bark=mat('#eeeeea',1,{map:treeBark,bumpMap:treeBark,bumpScale:.045}),earth=mat('#827765',1);
  box(65,.16,65,mat('#82857c',1),0,ground-.12,-22,outside);
  // Courtyard lane, paved verge and tree pits.
  box(33,.035,3.3,mat('#ffffff',.99,{map:road,bumpMap:road,bumpScale:.016}),3,ground-.014,-5.05,outside);
  box(30,.035,1.75,mat('#aaa99c',1),3,ground,-8.65,outside);
  for(const z of [-3.30,-6.77,-9.50])box(31,.095,.10,edge,3,ground+.025,z,outside);
  for(let x=-10;x<16;x+=.75)box(.007,.004,1.7,sill,x,ground+.021,-8.65,outside);
  for(const x of [.10,4.7,10.4]){
    box(1.5,.035,1.45,earth,x,ground+.03,-7.25,outside);
    for(const z of [-6.5,-8])box(1.7,.08,.08,edge,x,ground+.05,z,outside);
    for(const xx of [x-.8,x+.8])box(.08,.08,1.5,edge,xx,ground+.05,-7.25,outside);
  }
  // Blank left bay and projecting right facade. Roof lies ABOVE the eye line.
  const near=new THREE.Group();near.name='near-three-storey-building';outside.add(near);
  box(18.0,12.35,5.4,grey,5.2,ground+6.175,-14.0,near);
  box(13.0,12.35,1.20,grey,7.7,ground+6.175,-10.70,near);
  box(18.45,.22,5.65,edge,5.2,2.98,-14.0,near);
  box(13.45,.22,1.48,edge,7.7,3.00,-10.73,near);
  box(18.0,.27,.13,sill,5.2,2.67,-11.22,near);
  box(13.0,.27,.13,sill,7.7,2.69,-10.055,near);
  box(.11,12.1,.11,edge,1.14,-3.4,-10.02,near);
  box(.11,12.1,.11,edge,14.17,-3.4,-10.02,near);
  function windowAt(parent,x,y,z,w,h,grille=false,shade=false){
    box(w+.12,h+.10,.07,sill,x,y,z,parent);
    box(w,h,.08,shade?glassDim:glass,x,y,z+.045,parent);
    box(.035,h,.025,edge,x,y,z+.099,parent);
    box(w,.025,.025,metal,x,y+h*.27,z+.10,parent);
    box(w+.18,.065,.20,edge,x,y-h/2-.045,z+.08,parent);
    if(grille){
      for(let k=-2;k<=2;k++)rod([x+k*w/6,y-h/2,z+.17],[x+k*w/6,y+h/2,z+.17],.011,metal,parent);
      for(const yy of [y-h*.30,y+h*.30])rod([x-w/2,yy,z+.17],[x+w/2,yy,z+.17],.009,metal,parent);
    }
  }
  for(const [x,w] of [[2.60,1.10],[6.60,1.0],[10.0,.85],[13.2,1.04]]){
    windowAt(near,x,.59,-10.008,w,1.72,false,x>9);
    windowAt(near,x,-3.50,-10.008,w,x<4?1.28:1.55,false,x>9);
    windowAt(near,x,-7.22,-10.008,w,1.17,true);
  }
  // Ground-floor entrance, sheet-metal awning, and dark low extension on the left.
  box(.97,2.2,.06,glass,7.48,ground+1.13,-9.99,near);
  const awning=box(2.7,.085,1.0,mat('#626e60',.8),7.5,ground+2.45,-9.58,near);awning.rotation.x=.07;
  for(const x of [6.40,8.57])rod([x,ground+1.75,-10],[x,ground+2.40,-9.22],.021,metal,near);
  box(.37,.15,.01,mat('#c2b467',.95),3.55,ground+2.02,-9.948,near);
  box(4.9,3.25,3.0,mat('#626b5b',.97),-1.15,ground+1.625,-9.72,near);
  const shedRoof=box(5.20,.16,3.30,mat('#786f5b',.99),-1.15,ground+3.33,-9.72,near);shedRoof.rotation.x=-.035;
  windowAt(near,-1.72,ground+1.52,-8.17,.81,1.38,true);
  box(.94,2.16,.03,glass,-.20,ground+1.09,-8.16,near);
  for(const x of [-3.36,1.04])box(.045,3.15,.047,metal,x,ground+1.60,-8.13,near);
  // Far residential block offset LEFT: projecting balconies, AC and slab bands.
  const flats=new THREE.Group();flats.name='left-residential-block';flats.position.x=2.8;outside.add(flats);
  box(11.2,31,7.2,cream,-11.1,ground+15.5,-24.1,flats);
  box(5.25,30.8,.08,mat('#a8aaa0',.97),-13.95,ground+15.4,-20.45,flats);
  box(2.3,30.8,1.0,cream,-6.95,ground+15.4,-20.05,flats);
  box(11.55,.25,7.55,edge,-11.1,21.73,-24.1,flats);
  function railing(parent,x,y,z,w,h){
    rod([x-w/2,y,z],[x+w/2,y,z],.025,metal,parent);
    rod([x-w/2,y+h,z],[x+w/2,y+h,z],.025,metal,parent);
    for(const xx of [x-w/2,x,x+w/2])rod([xx,y,z],[xx,y+h,z],.022,metal,parent);
    rod([x-w/2,y,z],[x+w/2,y+h,z],.018,metal,parent);
    rod([x-w/2,y+h,z],[x+w/2,y,z],.018,metal,parent);
  }
  for(let level=0;level<10;level++){
    const y=ground+1.75+level*3.04;
    for(const x of [-15.0,-11.8])windowAt(flats,x,y,-20.35,1.15,1.56,false,level%3===0);
    windowAt(flats,-7.03,y,-19.49,1.43,1.73);
    box(2.66,.17,1.02,edge,-7.03,y-1.01,-19.46,flats);
    railing(flats,-7.03,y-.92,-18.92,2.34,.68);
    box(.63,.46,.35,edge,-10.66,y-.22,-20.09,flats);
    const fan=new THREE.Mesh(new THREE.CircleGeometry(.16,16),metal);fan.position.set(-10.66,y-.22,-19.90);flats.add(fan);
    if(level%2===1)box(11.2,.14,.25,edge,-11.1,y+1.31,-20.32,flats);
  }
  // Farther central gable is largely plain, as the video shows.
  box(8.6,27.0,7.5,cream,2.2,ground+13.5,-39,outside);
  box(6.7,.45,7.8,edge,1.25,17.84,-39,outside);
  for(let y=-7.2;y<17.8;y+=3.2)box(8.7,.095,.13,sill,2.2,y,-35.2,outside);
  box(.10,26.8,.09,edge,-1.82,4.0,-35.18,outside);
  box(.10,26.8,.09,edge,5.90,4.0,-35.18,outside);
  // Summer foliage uses Blender branches and shared GPU leaf instances.
  addSummerTrees({THREE,outside,bark,ground});
  // Bicycles and covered scooters, below the fourth-floor sightline.
  function bicycle(x,z,angle){
    const g=new THREE.Group();g.position.set(x,ground+.05,z);g.rotation.y=angle;outside.add(g);
    for(const wx of [-.53,.53]){const wheel=new THREE.Mesh(new THREE.TorusGeometry(.31,.022,6,22),metal);wheel.position.set(wx,.34,0);g.add(wheel);for(let n=0;n<6;n++){const a=n*Math.PI/3;rod([wx,.34,0],[wx+Math.cos(a)*.30,.34+Math.sin(a)*.30,0],.004,edge,g);}}
    for(const [a,b] of [[[0,.32,0],[-.53,.34,0]],[[0,.32,0],[-.22,.83,0]],[[-.53,.34,0],[-.22,.83,0]],[[-.22,.83,0],[.35,.86,0]],[[.35,.86,0],[0,.32,0]],[[.35,.86,0],[.53,.34,0]]])rod(a,b,.017,metal,g);
    box(.24,.045,.14,glass,-.22,.87,0,g);rod([.35,.86,0],[.32,1.12,0],.018,metal,g);rod([.32,1.12,-.18],[.32,1.12,.18],.015,metal,g);
  }
  for(const [x,z,a] of [[-3.8,-8.4,.2],[2.6,-8.6,-.25],[7.1,-8.8,.1]])bicycle(x,z,a);
  function scooter(x,z,angle,covered){
    const g=new THREE.Group();g.position.set(x,ground+.06,z);g.rotation.y=angle;outside.add(g);
    for(const zz of [-.52,.52]){const wheel=cylinder(.20,.20,.12,glass,0,.22,zz,g,16);wheel.rotation.z=Math.PI/2;}
    box(.45,.40,.84,covered?mat('#b3bdb5',.98):mat('#647f74',.72),0,.44,0,g,.06);
    box(.43,.075,.58,glass,0,.70,.10,g,.025);
    rod([0,.42,-.51],[0,1.10,-.48],.025,metal,g);rod([-.31,1.10,-.48],[.31,1.10,-.48],.022,metal,g);
    if(covered){const cover=box(.52,.48,1.1,mat('#bdc8be',.97),0,.80,-.03,g,.08);cover.rotation.x=-.13;}
  }
  scooter(4.0,-7.7,.2,true);scooter(.2,-3.6,.03,false);scooter(1.15,-3.6,-.15,true);
  // User-marked position to the right of the covered scooter. Confirmed front faces the grey wall (-Z).
  const bike=createMotorcycle(THREE);bike.position.set(6.65,ground+.04,-7.73);bike.rotation.z=.045;outside.add(bike);
  bike.traverse(o=>{if(o.isMesh){o.castShadow=!o.material.transparent;o.receiveShadow=true;}});
  const shadeCanvas=document.createElement('canvas');shadeCanvas.width=128;shadeCanvas.height=256;const c=shadeCanvas.getContext('2d');
  const shade=c.createRadialGradient(64,128,5,64,128,115);shade.addColorStop(0,'rgba(26,30,25,.36)');shade.addColorStop(1,'rgba(26,30,25,0)');c.fillStyle=shade;c.fillRect(0,0,128,256);
  const contact=new THREE.Mesh(new THREE.PlaneGeometry(1.2,2.5),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(shadeCanvas),transparent:true,depthWrite:false}));contact.rotation.x=-Math.PI/2;contact.position.set(6.65,ground+.026,-7.73);outside.add(contact);
  return outside;
}
