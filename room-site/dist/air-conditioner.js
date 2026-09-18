// All pipe/cable endpoints terminate inside the unit, a wall sleeve or the plug.
export function addAirConditioner({THREE,world,M,mat,box,cylinder,path}){
  const ac=new THREE.Group();ac.name='wall-mounted-air-conditioner';world.add(ac);
  // Separate casing panels leave a real recessed air passage. Wall-mounted
  // splits use one curved broad flap with small upright vanes inside the duct.
  const body=box(.165,.275,.83,M.white,1.2925,2.29,-.91,ac,.030);body.name='air-conditioner-body';
  box(.079,.205,.80,M.white,1.180,2.327,-.91,ac,.029);
  for(const z of [-1.312,-.508])box(.23,.277,.044,M.white,1.26,2.29,z,ac,.019);
  const ductMat=mat('#242a28',.88),vaneMat=mat('#aeb2a7',.57);
  const duct=box(.008,.075,.739,ductMat,1.206,2.192,-.91,ac,.006);duct.name='recessed-ac-outlet';
  box(.084,.008,.744,M.white,1.173,2.229,-.91,ac,.003);
  box(.117,.014,.744,M.white,1.231,2.153,-.91,ac,.006);
  const flapGroup=new THREE.Group();flapGroup.name='curved-ac-horizontal-louver';flapGroup.position.set(1.167,2.174,-.91);flapGroup.rotation.z=-.24;ac.add(flapGroup);
  // A thin closed airfoil, rolled along its chord; rounded end caps meet axles.
  const p=[],ix=[],N=48,K=12;
  for(let side=0;side<2;side++)for(let j=0;j<=K;j++)for(let i=0;i<=N;i++){
    const u=i/N*2-1,v=j/K;const chord=.059*Math.sqrt(1-.14*Math.pow(Math.abs(u),12));
    p.push((v-.5)*chord,.0047*Math.sin(v*Math.PI)+(side?-.0014:.0014),u*.365);
  }
  const off=(K+1)*(N+1);
  for(let j=0;j<K;j++)for(let i=0;i<N;i++){const k=j*(N+1)+i;ix.push(k,k+1,k+N+2,k,k+N+2,k+N+1,k+off,k+N+2+off,k+1+off,k+off,k+N+1+off,k+N+2+off);}
  const border=[...Array(N+1).keys(),...Array.from({length:K},(_,j)=>(j+1)*(N+1)+N),...Array.from({length:N},(_,i)=>K*(N+1)+N-i-1),...Array.from({length:K-1},(_,j)=>(K-j-1)*(N+1))];
  border.forEach((a,i)=>{const b=border[(i+1)%border.length];ix.push(a,a+off,b,b,a+off,b+off);});
  const flapGeo=new THREE.BufferGeometry();flapGeo.setAttribute('position',new THREE.Float32BufferAttribute(p,3));flapGeo.setIndex(ix);flapGeo.computeVertexNormals();
  const flap=new THREE.Mesh(flapGeo,M.white);flap.castShadow=flap.receiveShadow=true;flapGroup.add(flap);
  for(const z of [-.372,.372]){const axle=cylinder(.0035,.0035,.017,M.white,0,0,z,flapGroup,12);axle.rotation.x=Math.PI/2;}
  const vanes=new THREE.Group();vanes.name='internal-ac-vertical-guide-vanes';ac.add(vanes);
  for(let i=0;i<12;i++){const fin=box(.043,.049,.0026,vaneMat,1.181,2.202,-1.244+i*.0605,vanes,.0012);fin.rotation.y=.17;}
  // Panel seam and the narrow lower lip, with gently rounded manufactured edges.
  box(.002,.0018,.748,mat('#b7b8ad',.69),1.139,2.245,-.91,ac,.0007);
  const hole=new THREE.Group();hole.name='air-conditioner-wall-sleeve';hole.position.set(1.391,1.88,-1.68);hole.rotation.z=Math.PI/2;ac.add(hole);
  cylinder(.061,.061,.012,M.white,0,0,0,hole,40);
  cylinder(.046,.046,.014,M.dark,0,.003,0,hole,40);
  const points=[[1.34,2.185,-1.12],[1.353,2.12,-1.17],[1.357,2.01,-1.34],[1.356,1.917,-1.59],[1.402,1.88,-1.68]];
  const wrapped=path(points,.036,mat('#c7bda9',.91),ac);wrapped.name='connected-insulated-ac-pipe';wrapped.userData.endpoints=points;
  // The photo's slack black lead is kept, but both ends are now connected and
  // the loop sits close to the wall rather than hanging in front of the casing.
  const socket=box(.022,.075,.061,M.white,1.39,2.085,-.94,ac,.007);socket.name='ac-power-socket';
  const plug=box(.030,.025,.025,M.dark,1.365,2.078,-.94,ac,.006);plug.name='ac-plug';
  const cablePoints=[[1.364,2.181,-.70],[1.371,2.105,-.71],[1.375,1.935,-.765],[1.374,1.887,-.845],[1.369,1.935,-.935],[1.35,2.078,-.94]];
  const cable=path(cablePoints,.0045,M.dark,ac);cable.name='connected-ac-power-cable';cable.userData.endpoints=[cablePoints[0],cablePoints.at(-1)];
  for(const [y,z]of [[2.105,-.71],[1.935,-.765]])box(.013,.012,.016,M.white,1.385,y,z,ac,.003);
  // Blue/white sticker layout is visible in the owner's reference. Appliance
  // model, certified class and consumption values are unreadable, so not invented.
  const canvas=document.createElement('canvas');canvas.width=384;canvas.height=600;const c=canvas.getContext('2d');
  c.fillStyle='#f4f8f7';c.fillRect(0,0,384,600);c.strokeStyle='#00769e';c.lineWidth=9;c.strokeRect(5,5,374,590);
  c.fillStyle='#007da7';c.fillRect(10,10,364,113);c.fillStyle='white';c.font='bold 34px "Microsoft YaHei", sans-serif';c.textAlign='center';c.fillText('中国能效标识',192,58);c.font='18px Arial';c.fillText('CHINA ENERGY LABEL',192,94);
  c.fillStyle='#225168';c.font='20px "Microsoft YaHei", sans-serif';c.fillText('能源效率',192,160);
  for(let i=0;i<5;i++){const x=32,y=187+i*40,w=146+i*31;c.fillStyle=['#118947','#6daf42','#e4d337','#e19a2d','#cf4d3c'][i];c.beginPath();c.moveTo(x,y);c.lineTo(x+w,y);c.lineTo(x+w+17,y+16);c.lineTo(x+w,y+32);c.lineTo(x,y+32);c.closePath();c.fill();c.fillStyle='white';c.font='bold 21px Arial';c.textAlign='left';c.fillText(String(i+1),x+12,y+24);}
  c.fillStyle='#1e4b61';c.font='18px "Microsoft YaHei", sans-serif';c.fillText('能效比',34,440);c.fillText('额定制冷量',34,478);c.fillText('输入功率',34,516);
  c.strokeStyle='#7099a6';c.lineWidth=1;for(const y of [451,489,527,563]){c.beginPath();c.moveTo(29,y);c.lineTo(354,y);c.stroke();}
  const map=new THREE.CanvasTexture(canvas);map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=4;
  const labelGeo=new THREE.PlaneGeometry(.078,.122,1,16),lp=labelGeo.attributes.position;
  for(let i=0;i<lp.count;i++){const y=lp.getY(i)+2.352,dy=Math.max(0,y-2.4005),surfaceX=1.1695-Math.sqrt(.029**2-dy**2)-.0007;lp.setZ(i,1.1425-surfaceX);}labelGeo.computeVertexNormals();
  const label=new THREE.Mesh(labelGeo,mat('#ffffff',.61,{map,polygonOffset:true,polygonOffsetFactor:-1}));label.name='blue-white-energy-efficiency-label';label.position.set(1.1425,2.352,-.607);label.rotation.y=-Math.PI/2;ac.add(label);
  return ac;
}
