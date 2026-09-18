import {propGeometry} from './prop-assets.js?v=blender18';
// Soft seagrass basket, thick rolled paper-bract flowers, asymmetrical dry stems.
export function addFloralBasket({THREE,desk,mat,cylinder,path}){
  const basket=new THREE.Group();basket.name='woven-basket-and-white-everlastings';basket.position.set(.065,1.222,.30);desk.add(basket);
  const straw=mat('#b28d57',.95),twine=mat('#b69b6f',1);
  function surface(a,v,inset=0){
    const bulge=.076+.019*Math.sin(v*Math.PI*.83);
    const r=bulge+.0028*Math.sin(a*3+v*3)+.0017*Math.cos(a*5-v*4)-.0045*Math.exp(-(((a-2.4)/.4)**2))*v-inset;
    return [Math.cos(a)*r*(1+.03*v),.005+v*(.224+.004*Math.sin(a*3)+.003*Math.cos(a*2)),Math.sin(a)*r*.96];
  }
  // Outer and inner walls meet at the irregular rim: a visibly hollow, pliable bag.
  const p=[],ix=[],N=80,H=24;
  for(const inset of [0,.0032])for(let j=0;j<=H;j++)for(let i=0;i<N;i++)p.push(...surface(i/N*Math.PI*2,j/H,inset));
  const off=(H+1)*N;
  for(let j=0;j<H;j++)for(let i=0;i<N;i++){const a=j*N+i,b=j*N+(i+1)%N,c=b+N,d=a+N;ix.push(a,d,b,b,d,c,a+off,b+off,d+off,b+off,c+off,d+off);}
  for(let i=0;i<N;i++){const a=H*N+i,b=H*N+(i+1)%N;ix.push(a,b,a+off,b,b+off,a+off);}
  const shell=new THREE.BufferGeometry();shell.setAttribute('position',new THREE.Float32BufferAttribute(p,3));shell.setIndex(ix);shell.computeVertexNormals();
  const body=new THREE.Mesh(shell,straw);body.name='soft-hollow-woven-basket';body.castShadow=body.receiveShadow=true;basket.add(body);
  cylinder(.076,.073,.005,straw,0,.005,0,basket,48);
  // Closed, raised weave ribbons follow the dents in the soft basket body.
  const wp=[],wi=[],wc=[];const tone=new THREE.Color();const bands=38,steps=56;
  for(let family=0;family<2;family++)for(let band=0;band<bands;band++){
    const start=wp.length/3,sign=family?1:-1;tone.set(['#c9a573','#bb945d','#d0af7c','#b89b69','#c3a06a'][band%5]);
    for(let j=0;j<=steps;j++)for(let k=0;k<4;k++){
      const v=.012+j/steps*.975,a=band/bands*Math.PI*2+sign*v*2.9+(k%2-.5)*.145;
      const weave=.0010*Math.sin(v*bands*2.9*2+(family?Math.PI:0)+band*Math.PI);
      wp.push(...surface(a,v,(k<2?-.0012:.0001)-weave));
      const shade=k<2?1:.77;wc.push(tone.r*shade,tone.g*shade,tone.b*shade);
    }
    for(let j=0;j<steps;j++){const k=start+j*4;wi.push(k,k+4,k+1,k+1,k+4,k+5,k+2,k+3,k+6,k+3,k+7,k+6,k,k+2,k+4,k+2,k+6,k+4,k+1,k+5,k+3,k+3,k+5,k+7);}
  }
  const weaveGeo=new THREE.BufferGeometry();weaveGeo.setAttribute('position',new THREE.Float32BufferAttribute(wp,3));weaveGeo.setAttribute('color',new THREE.Float32BufferAttribute(wc,3));weaveGeo.setIndex(wi);weaveGeo.computeVertexNormals();
  const weave=new THREE.Mesh(weaveGeo,mat('#ffffff',.95,{vertexColors:true}));weave.name='solid-undulating-straw-weave';weave.castShadow=weave.receiveShadow=true;basket.add(weave);
  const rim=[];for(let i=0;i<=180;i++)rim.push(new THREE.Vector3(...surface(i/180*Math.PI*2,1,-.001)));
  basket.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(rim),180,.0025,7,false),straw));
  cylinder(.073,.065,.003,mat('#594b31',1),0,.190,0,basket,48);
  const leather=mat('#a87349',.91);
  for(const sign of [-1,1]){
    const attachment=new THREE.Group();attachment.position.set(-.072,.201,sign*.049);attachment.rotation.y=-Math.PI/2-sign*.45;attachment.rotation.x=sign*.10;basket.add(attachment);
    const shape=new THREE.Shape();shape.moveTo(-.017,-.027);shape.quadraticCurveTo(0,-.034,.017,-.027);shape.lineTo(.018,.026);shape.quadraticCurveTo(0,.029,-.018,.026);shape.closePath();
    attachment.add(new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:.0025,bevelEnabled:true,bevelSize:.001,bevelThickness:.0008,bevelSegments:2,steps:1}),leather));
    for(const s of [-1,1])path([[s*.010,-.02,.004],[0,0,.007],[-s*.010,.019,.004]],.00135,twine,attachment);
    // A complete slack loop, with BOTH ends threaded through the same leather
    // reinforcement; endpoint positions are transformed from the patch itself.
    attachment.updateMatrix();
    const end=(x,y)=>new THREE.Vector3(x,y,.005).applyMatrix4(attachment.matrix).toArray();
    const a=end(-.010,.019),b=end(.010,.019);
    const handlePoints=[a,[-.106,.245,sign*.071],[-.145,.220,sign*.085],[-.157,.173,sign*.091],[-.136,.153,sign*.082],[-.100,.179,sign*.068],b];
    const handle=path(handlePoints,.0034,mat('#795437',.95),basket);handle.name='continuous-basket-rope-handle';handle.userData.endpoints=[a,b];
    for(const [x,y]of [[-.010,.019],[.010,.019]]){
      const knot=path([[x-.004,y,.005],[x,y+.003,.008],[x+.004,y,.005],[x,y-.003,.003],[x-.004,y,.005]],.0015,twine,attachment);knot.name='rope-threaded-through-leather';
    }
  }
  const petalGeo=propGeometry(THREE,'petal','cupped-solid-everlasting-petal');
  const flowerCount=72,petalCount=30;
  const petals=new THREE.InstancedMesh(petalGeo,mat('#fffdf8',.91),flowerCount*petalCount);petals.name='thick-cupped-ivory-petals';
  const hearts=new THREE.InstancedMesh(new THREE.SphereGeometry(1,12,8),mat('#b5a066',1),flowerCount),seeds=new THREE.InstancedMesh(new THREE.SphereGeometry(1,5,3),mat('#927843',1),flowerCount*16);
  const stems=new THREE.InstancedMesh(new THREE.CylinderGeometry(1,1,1,6),mat('#8c815e',1),flowerCount*2),buds=new THREE.InstancedMesh(new THREE.SphereGeometry(1,12,8),mat('#d9d4bc',1),20);
  const dummy=new THREE.Object3D(),head=new THREE.Object3D(),part=new THREE.Object3D(),matrix=new THREE.Matrix4(),a=new THREE.Vector3(),b=new THREE.Vector3(),up=new THREE.Vector3(0,1,0),tint=new THREE.Color();
  for(let i=0;i<flowerCount;i++){
    const angle=i*2.399963,rad=.124*Math.sqrt((i+.5)/flowerCount),x=Math.cos(angle)*rad-.009,z=Math.sin(angle)*rad;
    const y=.249+.100*Math.sqrt(1-(rad/.150)**2)+.053*Math.sin(i*9.1)+.011*Math.cos(i*2.8);
    const nod=i%6===0?-.19:.30+((i*7)%13)/11;
    head.position.set(x,y,z);head.quaternion.setFromUnitVectors(up,new THREE.Vector3(Math.cos(angle)*(.55+.45*Math.sin(i*7))-.23,nod,Math.sin(angle)*.86).normalize());head.updateMatrix();
    const scale=.66+((i*11)%17)/29,cupped=i%5===0;
    for(let j=0;j<petalCount;j++){
      const inner=j>=18,k=inner?j-18:j,count=inner?12:18,theta=k/count*Math.PI*2+(inner?.13:0)+.06*Math.sin(i*7+j*3);
      part.position.set(Math.sin(theta)*.003,inner?.003:0,Math.cos(theta)*.003);
      part.rotation.set((cupped?-.91:inner?-.48:-.10)-.20*Math.sin(i*2+j),theta,.12*Math.sin(i+j),'YXZ');part.scale.set(scale*(inner?.78:1),scale,scale*(inner?.72:1));part.updateMatrix();
      petals.setMatrixAt(i*petalCount+j,matrix.multiplyMatrices(head.matrix,part.matrix));tint.setHSL(.12,.09+((i+j)%5)*.014,.83+((i*3+j)%7)*.018);petals.setColorAt(i*petalCount+j,tint);
    }
    part.position.set(0,.003,0);part.rotation.set(0,0,0);part.scale.set(.0064*scale,.0042,.0064*scale);part.updateMatrix();hearts.setMatrixAt(i,matrix.multiplyMatrices(head.matrix,part.matrix));
    for(let j=0;j<16;j++){const theta=j*2.39996,r=.0048*Math.sqrt(j/16)*scale;part.position.set(Math.sin(theta)*r,.0064+.001*(1-r/.006),Math.cos(theta)*r);part.scale.setScalar(.00075);part.updateMatrix();seeds.setMatrixAt(i*16+j,matrix.multiplyMatrices(head.matrix,part.matrix));}
    const middle=[x*.50,.249,z*.55];for(let k=0;k<2;k++){a.set(...(k?middle:[x*.17,.165,z*.17]));b.set(...(k?[x,y,z]:middle));dummy.position.copy(a).add(b).multiplyScalar(.5);dummy.scale.set(k?.00065:.0009,a.distanceTo(b),k?.00065:.0009);dummy.quaternion.setFromUnitVectors(up,b.sub(a).normalize());dummy.updateMatrix();stems.setMatrixAt(i*2+k,dummy.matrix);}
    if(i<20){dummy.position.set(x*1.10,y-.031,z*1.10);dummy.rotation.set(.3,i,0);dummy.scale.set(.0042,.0064,.0042);dummy.updateMatrix();buds.setMatrixAt(i,dummy.matrix);}
  }
  for(const o of [petals,hearts,seeds,stems,buds]){o.castShadow=true;o.receiveShadow=true;o.computeBoundingSphere();basket.add(o);}
  return basket;
}
