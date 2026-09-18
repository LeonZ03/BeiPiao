import {addBoscPaperCup} from './paper-cup.js?v=blender18';
// Photo-guided occupied desk: ivory woven cover, gaming mouse, toiletries,
// extension socket, gingham tissues, paper cup, remote and small earbud case.
export function addDeskProps(ctx){
  const {THREE,desk,M,mat,box,cylinder,ellipsoid,rod,path}=ctx;
  const white=mat('#f4f2e8',.43),rubber=mat('#262b2b',.88),paper=mat('#fffef8',.98),silver=mat('#a4a9a7',.28,{metalness:.7});
  const bristleWhite=mat('#e5f2e5',.78),bristleTeal=mat('#70b6b4',.78),remoteButton=mat('#c5c3b1',.73),remotePower=mat('#bcbfa2',.73),socketFace=mat('#e5e5db',.61),flowerInk=mat('#b17c62',.65);
  const makeGroup=(name,x,y,z)=>{const g=new THREE.Group();g.name=name;g.position.set(x,y,z);desk.add(g);return g;};
  const map=(w,h,draw)=>{const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;};
  function closedSheet(name,parent,surface,material,nx=24,ny=18,thickness=.00035){
    const p=[],uv=[],ix=[],off=(nx+1)*(ny+1);
    // Offset the underside along the local normal so a hanging fold has real thickness too.
    const du=new THREE.Vector3(),dv=new THREE.Vector3(),normal=new THREE.Vector3();
    for(let side=0;side<2;side++)for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++){
      const u=i/nx,v=j/ny,a=surface(u,v),e=.0001;
      const l=surface(Math.max(0,u-e),v),r=surface(Math.min(1,u+e),v),b=surface(u,Math.max(0,v-e)),t=surface(u,Math.min(1,v+e));
      du.set(r[0]-l[0],r[1]-l[1],r[2]-l[2]);dv.set(t[0]-b[0],t[1]-b[1],t[2]-b[2]);normal.crossVectors(dv,du).normalize().multiplyScalar(side?thickness:0);
      p.push(a[0]-normal.x,a[1]-normal.y,a[2]-normal.z);uv.push(u,v);
    }
    for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const a=j*(nx+1)+i,b=a+1,d=a+nx+1,c=d+1;ix.push(a,d,b,b,d,c,a+off,b+off,d+off,b+off,c+off,d+off);}
    const border=[...Array(nx+1).keys(),...Array.from({length:ny},(_,j)=>(j+1)*(nx+1)+nx),...Array.from({length:nx},(_,i)=>ny*(nx+1)+nx-i-1),...Array.from({length:ny-1},(_,j)=>(ny-j-1)*(nx+1))];
    border.forEach((a,i)=>{const b=border[(i+1)%border.length];ix.push(a,b,a+off,b,b+off,a+off);});
    const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(p,3));geo.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geo.setIndex(ix);geo.computeVertexNormals();
    const m=new THREE.Mesh(geo,material);m.name=name;m.castShadow=m.receiveShadow=true;parent.add(m);return m;
  }
  const cover=makeGroup('soft-woven-desk-cover',0,0,0);
  const weaveTexture=height=>map(512,512,(p,w,h)=>{
    const pixels=p.createImageData(w,h);
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){
      const rx=Math.exp(-Math.pow(Math.sin(x/64*Math.PI)*4,2)),ry=Math.exp(-Math.pow(Math.sin(y/64*Math.PI)*4,2));
      const fiber=.018*Math.sin(x*Math.PI*.5)+.016*Math.sin(y*Math.PI*.5);
      const relief=.28+.48*Math.max(rx,ry)+fiber;
      const shade=height?relief:.925+relief*.065;
      const i=(y*w+x)*4;pixels.data[i]=shade*(height?255:250);pixels.data[i+1]=shade*(height?255:247);pixels.data[i+2]=shade*(height?255:236);pixels.data[i+3]=255;
    }p.putImageData(pixels,0,0);
  });
  const waffle=weaveTexture(false),waffleBump=weaveTexture(true);waffleBump.colorSpace=THREE.NoColorSpace;
  for(const t of [waffle,waffleBump]){t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(12,8.5);}
  const woven=M.cloth.clone();woven.color.set('#fffef9');woven.map=waffle;woven.bumpMap=waffleBump;woven.bumpScale=.0012;woven.roughness=.98;
  function clothSurface(u,v){
    const z=(u-.5)*1.042,edge=THREE.MathUtils.smoothstep(Math.abs(z),.482,.521);
    const fold=Math.sin(u*37+.4)*.65+Math.sin(u*71)*.25+Math.sin(u*19)*.1;
    let x,y,hang=0;
    if(v<=.55){const t=v/.55;x=.305-.60*t;y=.794+.00065*Math.sin(u*39)*Math.sin(t*21);}
    else if(v<=.73){const a=(v-.55)/.18*Math.PI/2;x=-.295-.014*Math.sin(a);y=.794-.014*(1-Math.cos(a));}
    else{hang=(v-.73)/.27;x=-.309-.006*fold*hang*hang;y=.780-hang*(.112+.010*Math.sin(u*22+.7)+.003*Math.sin(u*53));}
    // Rounded corners sag slightly; the top and hanging face are one uninterrupted cloth.
    y-=edge*(.018+.012*hang);x-=edge*.003;
    return [x,y,z+.003*fold*hang];
  }
  const cloth=closedSheet('continuous-rounded-tablecloth',cover,clothSurface,woven,104,100,.0013);
  // Use physical distance in the weave UVs, avoiding stretched threads around the bend.
  const clothUV=cloth.geometry.attributes.uv;
  for(let i=0;i<clothUV.count;i++){const v=clothUV.getY(i);clothUV.setY(i,v<=.55?(v/.55)*.60/.734:v<=.73?(.60+(v-.55)/.18*.022)/.734:(.622+(v-.73)/.27*.112)/.734);}
  const hem=[];for(let i=0;i<=90;i++)hem.push(clothSurface(i/90,1));path(hem,.0011,M.cloth,cover);
  for(let i=0;i<65;i++){
    const [x,y,z]=clothSurface(i/64,1);
    for(let k=0;k<2;k++)path([[x,y,z+k*.0012],[x-.003,y-.01,z+.002+k*.0012],[x+.002,y-.020-(i%5)*.001,z-.002]],.00065,M.cloth,cover);
  }
  const matMap=map(768,1024,(p,w,h)=>{
    p.fillStyle='#171d20';p.fillRect(0,0,w,h);p.strokeStyle='#536069';p.fillStyle='#b8c0bd';p.font='bold 50px Arial';p.fillText('GLOCK',46,85);p.lineWidth=3;p.strokeRect(30,28,236,74);
    p.fillStyle='#647178';p.font='15px Arial';for(let row=0;row<30;row++){const y=146+row*25;p.fillText(String(row+1).padStart(2,'0'),36,y);for(let col=0;col<3;col++){p.fillRect(74+col*225,y-8,145+(row*17+col*21)%65,1);p.fillRect(74+col*225,y-3,96+(row*13+col*7)%72,1);}}
    p.lineWidth=1;for(let y=120;y<h;y+=28){p.beginPath();p.moveTo(20,y);p.lineTo(w-20,y);p.stroke();}
  });
  const mousepad=box(.273,.0032,.345,mat('#ffffff',.99,{map:matMap}),-.055,.801,.306,desk,.013);mousepad.name='printed-black-mouse-mat';
  const mouse=makeGroup('white-gaming-mouse',-.08,.804,.279);
  box(.089,.010,.058,rubber,0,.007,0,mouse,.010);
  ellipsoid(0,.017,0,.047,.020,.031,white,mouse);
  // The two front buttons stop at a real centre groove around the rubber wheel.
  for(const z of [-.014,.014]){const b=box(.040,.007,.024,white,.022,.030,z,mouse,.006);b.rotation.z=-.12;}
  path([[.005,.037,0],[.020,.036,0],[.041,.029,0]],.00065,rubber,mouse);
  const wheel=cylinder(.005,.005,.006,rubber,.023,.037,0,mouse,20);wheel.rotation.x=Math.PI/2;
  for(let i=0;i<9;i++){const a=i/9*Math.PI*2;box(.001,.001,.006,M.gray,.023+Math.cos(a)*.005,.037+Math.sin(a)*.005,0,mouse,.0004);}
  for(const x of [-.011,.002])box(.012,.003,.0027,silver,x,.025,-.030,mouse,.001);
  path([[-.033,.818,.279],[.018,.81,.368],[.17,.809,.29],[.22,.816,.14]],.0018,white,desk);
  const buds=makeGroup('ivory-earbud-case',-.10,.805,.423);
  box(.043,.020,.057,mat('#e5debf',.37),0,.010,0,buds,.009);
  path([[-.020,.012,-.019],[-.021,.012,.019],[0,.012,.028],[.021,.012,.019],[.021,.012,-.019],[0,.012,-.028],[-.020,.012,-.019]],.00045,mat('#bcb293',.68),buds);
  for(let i=0;i<5;i++){const a=i/5*Math.PI*2;ellipsoid(Math.cos(a)*.004,.020,Math.sin(a)*.006,.002,.0005,.003,flowerInk,buds);}
  const power=makeGroup('detailed-extension-socket',.205,.802,.13);
  box(.084,.024,.19,white,0,.012,0,power,.007);
  for(const z of [-.060,0,.060]){
    box(.054,.001,.046,socketFace,0,.0245,z,power,.007);
    for(const s of [-1,1]){const slit=box(.004,.0015,.014,rubber,s*.011,.0255,z,power,.0008);slit.rotation.y=s*.45;}
    box(.004,.0015,.012,rubber,0,.0255,z-.013,power,.0008);
  }
  const charger=makeGroup('plugged-in-usb-charger',.20,.827,.16);box(.031,.057,.030,white,0,.0285,0,charger,.005);
  box(.008,.003,.014,mat('#658b9a',.52),-.016,.028,0,charger,.001);
  path([[.2,.884,.16],[.19,.867,.05],[.25,.81,-.06],[.09,.811,-.14]],.0018,white,desk);
  path([[.205,.814,.225],[.252,.812,.26],[.283,.797,.23],[.296,.63,.27],[.285,.38,.24]],.0035,white,desk);
  const brush=makeGroup('electric-toothbrush-and-charging-dock',.19,.798,.405);
  cylinder(.027,.031,.026,white,0,.013,0,brush,32);cylinder(.012,.015,.125,white,0,.088,0,brush,32);
  cylinder(.007,.011,.028,silver,0,.164,0,brush,24);cylinder(.0035,.006,.031,white,0,.193,0,brush,16);
  const button=ellipsoid(-.012,.102,0,.0015,.010,.006,mat('#b2bbb6',.45),brush);
  box(.004,.022,.014,white,-.004,.215,0,brush,.005);
  for(let y=0;y<5;y++)for(let z=0;z<4;z++){
    rod([-.006,.207+y*.0035,-.005+z*.0035],[-.012,.207+y*.0035,-.005+z*.0035],.0007,z%3?bristleWhite:bristleTeal,brush);
  }
  const gingham=map(512,512,(p,w,h)=>{
    p.fillStyle='#f8edce';p.fillRect(0,0,w,h);for(let x=0;x<w;x+=48)for(let y=0;y<h;y+=48)if((x+y)%96===0){p.fillStyle='#e8c880';p.fillRect(x,y,48,48);}
    p.fillStyle='#fff9e9';p.beginPath();p.ellipse(256,256,132,210,0,0,7);p.fill();p.strokeStyle='#c89482';p.lineWidth=5;p.beginPath();p.ellipse(256,215,65,58,0,0,7);p.stroke();
    p.fillStyle='#d99d97';for(const x of [235,276]){p.beginPath();p.ellipse(x,211,6,7,0,0,7);p.fill();}p.beginPath();p.ellipse(256,241,23,13,0,0,7);p.fill();
    p.fillStyle='#b69670';p.textAlign='center';p.font='italic 42px Georgia';p.fillText('Soft',256,326);p.font='16px Arial';p.fillText('TISSUE',256,352);
  });
  const tissues=makeGroup('yellow-gingham-tissue-pack',.14,1.662,-.315);
  box(.123,.094,.205,mat('#ffffff',.9,{map:gingham}),0,.047,0,tissues,.015);
  box(.009,.001,.094,mat('#c3b59f',.94),0,.095,0,tissues,.004);
  for(let i=0;i<2;i++)closedSheet('raised-folded-tissue-'+i,tissues,(u,v)=>[(u-.5)*.090+(v-.5)*.015,.095+v*.077+Math.sin(u*Math.PI)*v*.012,(v-.5)*.045+.011*Math.sin(u*8+v*2+i)],paper,24,18,.00022);
  addBoscPaperCup(ctx);
  const lower=makeGroup('soft-white-tissue-packet',-.05,1.222,-.40);
  box(.083,.047,.123,mat('#f4f0e7',.95),0,.024,0,lower,.014);
  closedSheet('white-tissue-from-packet',lower,(u,v)=>[(u-.5)*.074,.047+v*.046+.006*Math.sin(u*9)*v,(v-.5)*.068+.008*Math.sin(u*6)],paper,22,16,.00025);
  const remote=makeGroup('ivory-air-conditioner-remote',-.07,1.222,-.22);
  box(.045,.014,.133,mat('#e1dcc1',.56),0,.007,0,remote,.008);
  box(.032,.001,.033,mat('#9da599',.68),0,.0147,-.038,remote,.0015);
  for(let row=0;row<4;row++)for(let col=0;col<3;col++)box(.008,.002,.009,row===0&&col===1?remotePower:remoteButton,(col-1)*.011,.015,-.008+row*.015,remote,.003);
}
