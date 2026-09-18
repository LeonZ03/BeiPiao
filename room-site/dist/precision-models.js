// Close-view meshes. Dimensions are metres; soft objects are closed surfaces.
export function tileTexture(THREE) {
  const c=document.createElement('canvas');c.width=c.height=512;
  const p=c.getContext('2d');p.fillStyle='#e2dccf';p.fillRect(0,0,512,512);
  // Low-contrast mineral clouds only. Tile joints belong to the floor geometry.
  for(let i=0;i<1400;i++){
    const x=(i*137.508)%512,y=(i*73.117)%512,r=4+(i%37);
    const g=p.createRadialGradient(x,y,0,x,y,r);
    g.addColorStop(0,i%2?'rgba(255,253,240,.035)':'rgba(135,127,110,.025)');g.addColorStop(1,'rgba(210,204,188,0)');
    p.fillStyle=g;p.fillRect(x-r,y-r,r*2,r*2);
  }
  for(let i=0;i<32000;i++){p.fillStyle=i%2?'rgba(255,251,238,.035)':'rgba(107,100,89,.025)';p.fillRect((i*167.37)%512,(i*83.79)%512,1,1);}
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=8;return t;
}

function skin(THREE,nx,ny,surface) {
  const positions=[],uv=[],indices=[];
  for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++){positions.push(...surface(i/nx*2-1,j/ny*2-1));uv.push(i/nx,j/ny);}
  for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const k=j*(nx+1)+i;indices.push(k,k+1,k+nx+2,k,k+nx+2,k+nx+1);}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setIndex(indices);g.computeVertexNormals();return g;
}
function outline(THREE,surface,nx=64,ny=64) {
  const a=[];for(let i=0;i<nx;i++)a.push(new THREE.Vector3(...surface(-1+i/nx*2,-1)));
  for(let i=0;i<ny;i++)a.push(new THREE.Vector3(...surface(1,-1+i/ny*2)));
  for(let i=0;i<nx;i++)a.push(new THREE.Vector3(...surface(1-i/nx*2,1)));
  for(let i=0;i<ny;i++)a.push(new THREE.Vector3(...surface(-1,1-i/ny*2)));
  return new THREE.CatmullRomCurve3(a,true);
}
function mesh(THREE,g,m,parent,name){const o=new THREE.Mesh(g,m);o.name=name;o.castShadow=o.receiveShadow=true;parent.add(o);return o;}
function label(THREE,text,width,height,color='#deded9'){
  const c=document.createElement('canvas');c.width=512;c.height=128;const x=c.getContext('2d');x.clearRect(0,0,512,128);x.font='600 58px Arial';x.textAlign='center';x.textBaseline='middle';x.fillStyle=color;x.fillText(text,256,64);
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
  return new THREE.Mesh(new THREE.PlaneGeometry(width,height),new THREE.MeshStandardMaterial({map:t,transparent:true,roughness:.9,depthWrite:false}));
}

export function addBedding({THREE,bed,M,mat}) {
  const cloth=M.quilt.clone();cloth.side=THREE.DoubleSide;
  const fold=(u,v)=>.009*Math.sin(u*7+v*4)*Math.sin(v*5+1)+.008*Math.sin(v*13+u*6)+.024*Math.exp(-(((u*.8-v*.46-.20)/.15)**2))+.012*Math.exp(-(((u+v*.3+.40)/.18)**2));
  const top=(u,v)=>{
    const edge=Math.pow(Math.max(0,(1-u*u)*(1-v*v)),.28);
    return [u*.657*(1-.025*Math.pow(Math.abs(v),12)),.558+edge*(.040+fold(u,v)),v*.747-.22+.012*Math.sin(u*7)*Math.pow(Math.abs(v),8)];
  };
  const bottom=(u,v)=>{const a=top(u,v);a[1]=.558-Math.pow(Math.max(0,(1-u*u)*(1-v*v)),.35)*.005;return a;};
  mesh(THREE,skin(THREE,100,110,top),cloth,bed,'duvet-top');
  mesh(THREE,skin(THREE,72,80,bottom),cloth,bed,'duvet-underside');
  mesh(THREE,new THREE.TubeGeometry(outline(THREE,top),256,.0024,6,true),M.cloth,bed,'duvet-stitched-edge');
  // One centered pillow, with rounded corners and pinched fabric at the seam.
  const pillow=new THREE.Group();pillow.name='single-centered-pillow';pillow.position.set(0,.606,.76);bed.add(pillow);
  const shape=(u,v,sign)=>{const puff=Math.pow(Math.max(0,(1-u*u)*(1-v*v)),.38);return [u*.328*Math.sqrt(1-.14*v*v),sign*(.004+.058*puff),v*.205*Math.sqrt(1-.14*u*u)];};
  const pillowMat=M.cloth.clone();pillowMat.side=THREE.DoubleSide;
  for(const sign of [-1,1])mesh(THREE,skin(THREE,60,44,(u,v)=>shape(u,v,sign)),pillowMat,pillow,'pillow-soft-surface');
  mesh(THREE,new THREE.TubeGeometry(outline(THREE,(u,v)=>shape(u,v,0)),216,.002,6,true),mat('#d6d3c7',.98),pillow,'pillow-seam');
}

export function addLaptop({THREE,desk,mat,box,cylinder}) {
  const laptop=new THREE.Group();laptop.name='detailed-laptop';laptop.position.set(-.026,.812,-.105);laptop.rotation.y=-Math.PI/2;desk.add(laptop);
  const aluminum=new THREE.MeshPhysicalMaterial({color:'#8d9294',metalness:.78,roughness:.30,clearcoat:.2});
  const graphite=mat('#20262b',.6),rubber=mat('#101416',.9),letter=mat('#bec6c9',.8);
  box(.350,.013,.238,aluminum,0,0,0,laptop,.005);
  box(.342,.002,.232,mat('#767e83',.43,{metalness:.65}),0,.007,0,laptop,.003);
  // Real keys catch small highlights. Legends are a single transparent overlay.
  const keyRows=[14,14,13,12,12];
  for(let row=0;row<5;row++)for(let col=0;col<keyRows[row];col++){
    const w=col===keyRows[row]-1&&row>1?.032:.018;
    box(w,.0035,.0158,graphite,-.148+col*.022+(row>1?.005:0),.010,-.073+row*.022,laptop,.002);
  }
  for(const [x,w]of [[-.140,.025],[-.11,.023],[-.078,.025],[-.006,.106],[.071,.022],[.097,.022],[.129,.034]])box(w,.0035,.015,graphite,x,.010,.037,laptop,.002);
  const c=document.createElement('canvas');c.width=1024;c.height=512;const p=c.getContext('2d');p.clearRect(0,0,1024,512);p.font='19px Arial';p.fillStyle='#b5bfc2';p.textAlign='left';
  const rows=['1234567890-=⌫','QWERTYUIOP[]','ASDFGHJKL;','ZXCVBNM,./'];
  for(let row=0;row<4;row++)for(let k=0;k<rows[row].length;k++)p.fillText(rows[row][k],35+k*66+(row>0?10:0),125+row*86);
  const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
  const legends=new THREE.Mesh(new THREE.PlaneGeometry(.342,.129),new THREE.MeshStandardMaterial({map:t,transparent:true,roughness:.7,depthWrite:false}));legends.rotation.x=-Math.PI/2;legends.position.set(0,.012,-.028);laptop.add(legends);
  box(.106,.001,.053,mat('#a1a6a7',.48,{metalness:.5}),-.018,.0088,.080,laptop,.003);
  // Thin trackpad rim, palm-rest badges, side ports and recessed hinge.
  for(const x of [-.071,.035])box(.0007,.001,.053,graphite,x,.0094,.080,laptop);
  for(const z of [.0535,.1065])box(.106,.001,.0007,graphite,-.018,.0094,z,laptop);
  box(.016,.0005,.015,mat('#4b859f',.45),-.138,.009,.085,laptop,.001);
  box(.015,.0005,.012,mat('#adb699',.55),-.119,.009,.086,laptop,.001);
  for(const z of [-.063,-.031,.002])box(.001,.003,.015,rubber,-.175,.001,z,laptop,.001);
  for(const x of [-.120,.12]){const h=cylinder(.006,.006,.055,aluminum,x,.006,-.112,laptop,20);h.rotation.z=Math.PI/2;}
  const lid=new THREE.Group();lid.name='laptop-open-lid';lid.position.set(0,.01,-.112);lid.rotation.x=-.21;laptop.add(lid);
  box(.350,.226,.0065,aluminum,0,.111,0,lid,.005);
  box(.338,.213,.0017,graphite,0,.113,.004,lid,.004);
  const screenCanvas=document.createElement('canvas');screenCanvas.width=512;screenCanvas.height=320;const s=screenCanvas.getContext('2d');
  const grad=s.createLinearGradient(0,0,512,320);grad.addColorStop(0,'#29363b');grad.addColorStop(.4,'#131b20');grad.addColorStop(1,'#0b1014');s.fillStyle=grad;s.fillRect(0,0,512,320);
  const smap=new THREE.CanvasTexture(screenCanvas);smap.colorSpace=THREE.SRGBColorSpace;
  const screenMat=new THREE.MeshPhysicalMaterial({color:0xffffff,map:smap,roughness:.21,metalness:.18,clearcoat:.6,clearcoatRoughness:.2});
  box(.319,.184,.0008,screenMat,0,.118,.0052,lid,.001);
  const webcam=cylinder(.0016,.0016,.001,rubber,0,.214,.0055,lid,12);webcam.rotation.x=Math.PI/2;
  const logo=label(THREE,'Lenovo',.022,.004,'#919b9f');logo.position.set(0,.012,.0058);lid.add(logo);
  laptop.userData.dimensions={width:.350,depth:.238,screenHeight:.226};return laptop;
}

export function addLumbarCushion({THREE,chair,M,mat}) {
  const g=new THREE.Group();g.name='black-contoured-lumbar-cushion';g.position.set(-.146,.686,0);g.rotation.y=Math.PI/2;g.rotation.z=-.08;chair.add(g);
  const fabric=new THREE.MeshStandardMaterial({color:'#111419',roughness:.98,bumpMap:M.cloth.map,bumpScale:.00065,side:THREE.DoubleSide});
  const shape=new THREE.Shape();shape.moveTo(0,.149);
  shape.bezierCurveTo(.062,.149,.092,.184,.140,.184);
  shape.bezierCurveTo(.186,.184,.207,.157,.194,.108);
  shape.bezierCurveTo(.183,.065,.168,.022,.178,-.034);
  shape.bezierCurveTo(.192,-.087,.219,-.144,.194,-.173);
  shape.bezierCurveTo(.163,-.210,.075,-.169,0,-.168);
  shape.bezierCurveTo(-.075,-.169,-.163,-.210,-.194,-.173);
  shape.bezierCurveTo(-.219,-.144,-.192,-.087,-.178,-.034);
  shape.bezierCurveTo(-.168,.022,-.183,.065,-.194,.108);
  shape.bezierCurveTo(-.207,.157,-.186,.184,-.140,.184);
  shape.bezierCurveTo(-.092,.184,-.062,.149,0,.149);
  const boundary=shape.getSpacedPoints(192),nr=48,nt=boundary.length-1;
  for(const front of [true,false]){
    const positions=[],uv=[],indices=[];
    for(let j=0;j<=nr;j++)for(let i=0;i<=nt;i++){
      const r=j/nr,x=boundary[i].x*r,y=boundary[i].y*r,edge=Math.pow(Math.max(0,1-r*r),.52);
      const wing=.037*Math.exp(-Math.pow((Math.abs(x)-.134)/.048,2));
      const lumbar=.071*Math.exp(-Math.pow((y+.078)/.090,2)-Math.pow(x/.091,2));
      const upperRecess=.017*Math.exp(-Math.pow((y-.079)/.066,2)-Math.pow(x/.085,2));
      positions.push(x,y,front?.027+edge*(.037+wing+lumbar-upperRecess):-.020-edge*.012);uv.push(x/.42+.5,y/.40+.5);
    }
    for(let j=0;j<nr;j++)for(let i=0;i<nt;i++){const k=j*(nt+1)+i;indices.push(k,k+nt+2,k+1,k,k+nt+1,k+nt+2);}
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));geometry.setIndex(indices);geometry.computeVertexNormals();
    const normals=geometry.attributes.normal,centreNormal=new THREE.Vector3();for(let i=nt+1;i<=2*nt+1;i++)centreNormal.add(new THREE.Vector3().fromBufferAttribute(normals,i));centreNormal.normalize();for(let i=0;i<=nt;i++)normals.setXYZ(i,centreNormal.x,centreNormal.y,centreNormal.z);
    mesh(THREE,geometry,fabric,g,front?'lumbar-sculpted-front':'lumbar-back');
  }
  const sidePos=[],sideUv=[],sideIndex=[];
  for(let j=0;j<=12;j++)for(let i=0;i<=nt;i++){const t=j/12,p=boundary[i],round=1+.021*Math.sin(t*Math.PI);sidePos.push(p.x*round,p.y*round,.027-.047*t);sideUv.push(i/nt,t);}
  for(let j=0;j<12;j++)for(let i=0;i<nt;i++){const k=j*(nt+1)+i;sideIndex.push(k,k+1,k+nt+2,k,k+nt+2,k+nt+1);}
  const side=new THREE.BufferGeometry();side.setAttribute('position',new THREE.Float32BufferAttribute(sidePos,3));side.setAttribute('uv',new THREE.Float32BufferAttribute(sideUv,2));side.setIndex(sideIndex);side.computeVertexNormals();mesh(THREE,side,fabric,g,'lumbar-thick-rounded-sidewall');
  const seam=new THREE.CatmullRomCurve3(boundary.slice(0,-1).map(p=>new THREE.Vector3(p.x,p.y,.027)),true);
  mesh(THREE,new THREE.TubeGeometry(seam,256,.0015,6,true),mat('#303237',.98),g,'lumbar-piping');
  const logo=label(THREE,'YISHANG',.066,.012,'#dfdfd9');logo.position.set(0,.117,.053);logo.rotation.x=.19;g.add(logo);
  return g;
}
