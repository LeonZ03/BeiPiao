// One connected fixture, in local coordinates: wall is z=0, bathroom is +Z.
export function addShowerFixture({THREE,mat,box,cylinder,rod,path,M},bath){
  const root=new THREE.Group();root.name='connected-wall-mounted-shower';root.position.set(-1.00,0,1.934);bath.add(root);
  const chrome=mat('#c4cacc',.19,{metalness:.92}),rubber=mat('#485052',.68),white=M.white;
  const railZ=.052,gripBase=[0,1.710,.149],headCentre=[0,1.963,.252],outlet=[0,.946,.099];
  function pipe(a,b,r=.009,m=chrome,parent=root){return rod(a,b,r,m,parent);}
  function disc(p,r,length,m=chrome,parent=root){const o=cylinder(r,r,length,m,...p,parent,32);o.rotation.x=Math.PI/2;return o;}
  // Two wall anchors and short standoffs, not a rail floating away from its wall.
  for(const y of [1.16,1.91]){disc([0,y,.003],.027,.009);pipe([0,y,.003],[0,y,railZ],.011);disc([0,y,railZ],.017,.027);}
  pipe([0,1.137,railZ],[0,1.934,railZ],.009);
  // Sliding clamp and the cradle that physically holds the handpiece.
  cylinder(.017,.017,.052,chrome,0,1.765,railZ,root,32);
  pipe([0,1.765,railZ],[0,1.765,.170],.011);
  const holder=cylinder(.019,.019,.030,chrome,0,1.765,.170,root,32);holder.rotation.x=.40;
  const liner=cylinder(.015,.015,.032,rubber,0,1.765,.170,root,32);liner.rotation.x=.40;
  pipe(gripBase,[0,1.925,.240],.012);
  pipe([0,1.696,.143],[0,1.724,.155],.0135);
  const head=new THREE.Group();head.name='wall-normal-shower-head';head.userData.interactive='shower';head.position.set(...headCentre);
  head.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),new THREE.Vector3(0,-.30,.954).normalize());root.add(head);
  cylinder(.051,.046,.022,chrome,0,0,0,head,56);
  cylinder(.046,.046,.0025,mat('#c7cfcb',.40),0,.012,0,head,48);
  const nozzles=[];
  for(let ring=1;ring<=4;ring++)for(let i=0;i<ring*9;i++){const a=i/(ring*9)*Math.PI*2;nozzles.push([Math.cos(a)*ring*.009,.0138,Math.sin(a)*ring*.009]);}
  const nozzleMesh=new THREE.InstancedMesh(new THREE.CylinderGeometry(.00125,.001,.0015,6),rubber,nozzles.length),dummy=new THREE.Object3D();
  nozzles.forEach((p,i)=>{dummy.position.set(...p);dummy.updateMatrix();nozzleMesh.setMatrixAt(i,dummy.matrix);});head.add(nozzleMesh);
  // Surface-mounted hot/cold supplies end in the two wall fittings of the mixer.
  const mixer=new THREE.Group();mixer.name='clickable-shower-mixer';mixer.userData.interactive='shower';root.add(mixer);
  for(const [x,floorY]of [[-.075,.09],[.075,.16]]){
    path([[x,floorY,.016],[x,.925,.016],[x,.99,.025]],.012,white,root);
    disc([x,.99,.015],.030,.012,chrome,mixer);pipe([x,.99,.015],[x,.99,.098],.014,chrome,mixer);
    for(const y of [.30,.67]){box(.034,.015,.027,white,x,y,.014,root,.003);}
  }
  pipe([-.105,.99,.099],[.105,.99,.099],.025,chrome,mixer);
  // Upright lever stem and gently rounded horizontal mixer lever.
  cylinder(.016,.016,.033,chrome,0,1.026,.099,mixer,24);
  box(.021,.010,.087,chrome,0,1.046,.130,mixer,.005);
  cylinder(.003,.003,.001,mat('#547a95',.45),-.006,1.052,.106,mixer,12);
  cylinder(.003,.003,.001,mat('#bf6758',.45),.006,1.052,.106,mixer,12);
  pipe([0,.979,.099],outlet,.012,chrome,mixer);
  const points=[outlet,[.014,.90,.112],[.13,.69,.163],[.12,.535,.160],[-.12,.532,.145],[-.205,.69,.12],[-.12,1.12,.11],[0,1.675,.135],gripBase];
  const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)),false,'centripetal');
  const hose=new THREE.Mesh(new THREE.TubeGeometry(curve,160,.0067,10,false),chrome);hose.name='continuous-flexible-shower-hose';hose.castShadow=hose.receiveShadow=true;root.add(hose);
  // Fine corrugations share one GPU draw, including the two threaded end collars.
  const rings=new THREE.InstancedMesh(new THREE.TorusGeometry(.00685,.00065,4,10),chrome,330);
  for(let i=0;i<330;i++){const t=i/329;dummy.position.copy(curve.getPointAt(t));dummy.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),curve.getTangentAt(t).normalize());dummy.updateMatrix();rings.setMatrixAt(i,dummy.matrix);}root.add(rings);
  for(const t of [0,1]){const p=curve.getPointAt(t),tangent=curve.getTangentAt(t),a=p.clone().addScaledVector(tangent,t===0?.025:-.025);pipe(p.toArray(),a.toArray(),.010);}
  root.userData.connections={hoseMixer:outlet,hoseHandpiece:gripBase,head:headCentre};
  return root;
}
