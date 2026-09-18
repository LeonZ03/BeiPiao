// Independent, photo-guided artwork is wrapped over a hollow porcelain body.
// The source room photograph is deliberately not shipped as a public asset.
export function addReferenceMug({THREE,desk,texture,ellipsoid}){
  const mug=new THREE.Group();mug.name='photo-matched-monster-mug';mug.position.set(-.156,.798,-.404);mug.rotation.y=-Math.PI/2;desk.add(mug);
  const ceramic=new THREE.MeshPhysicalMaterial({color:'#fff9e8',roughness:.24,clearcoat:.36,clearcoatRoughness:.18});
  const profile=[[0,.002],[.033,.002],[.036,.003],[.038,.007],[.0388,.015],[.043,.098],[.044,.105],[.0438,.107],[.0427,.108],[.0415,.107],[.0404,.104],[.0360,.014],[.034,.009],[0,.009]].map(([r,y])=>new THREE.Vector2(r,y));
  const shell=new THREE.Mesh(new THREE.LatheGeometry(profile,96),ceramic);shell.name='hollow-ceramic-mug';shell.castShadow=shell.receiveShadow=true;mug.add(shell);
  const handlePoints=[[.040,.087,0],[.061,.088,0],[.080,.074,0],[.085,.054,0],[.077,.031,0],[.055,.020,0],[.040,.020,0]].map(p=>new THREE.Vector3(...p));
  const handle=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(handlePoints),64,.0058,12,false),ceramic);handle.name='rounded-porcelain-mug-handle';handle.castShadow=handle.receiveShadow=true;mug.add(handle);
  for(const y of [.020,.086])ellipsoid(.040,y,0,.008,.008,.006,ceramic,mug);
  const photo=texture('mug-monster-texture.png');photo.anisotropy=8;
  const print=new THREE.MeshPhysicalMaterial({map:photo,color:'#ffffff',roughness:.30,clearcoat:.3,clearcoatRoughness:.2});
  function patch(name,nx,ny,point,uv){
    const pos=[],tex=[],index=[];
    for(let j=0;j<=ny;j++)for(let i=0;i<=nx;i++){pos.push(...point(i/nx,j/ny));tex.push(...uv(i/nx,j/ny));}
    for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){const a=j*(nx+1)+i;index.push(a,a+1,a+nx+2,a,a+nx+2,a+nx+1);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(pos,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(tex,2));g.setIndex(index);g.computeVertexNormals();
    const mesh=new THREE.Mesh(g,print);mesh.name=name;mesh.receiveShadow=true;mug.add(mesh);return mesh;
  }
  patch('reference-monster-artwork',96,36,(u,v)=>{const a=(u-.5)*3.25,y=.008+v*.096,r=.0384+v*.0055;return [Math.sin(a)*r,y,Math.cos(a)*r];},(u,v)=>[u,v]);
  const words=document.createElement('canvas');words.width=1024;words.height=128;
  const ink=words.getContext('2d');ink.clearRect(0,0,1024,128);ink.fillStyle='#333123';ink.font='italic 600 69px Georgia';ink.textAlign='center';ink.textBaseline='middle';ink.fillText('Meet you like the wind',512,67,1000);
  const wordMap=new THREE.CanvasTexture(words);wordMap.colorSpace=THREE.SRGBColorSpace;wordMap.anisotropy=8;
  function inside(a,y){const r=.036+(y-.014)*(.0044/.09)-.00012;return [Math.sin(a)*r,y,Math.cos(a)*r];}
  const inner=patch('inner-rim-message',64,8,(u,v)=>inside(Math.PI+(.5-u)*1.44,.093+v*.008),(u,v)=>[u,v]);
  inner.material=new THREE.MeshStandardMaterial({map:wordMap,transparent:true,roughness:.33,depthWrite:false,side:THREE.DoubleSide});
  const sun=patch('inner-rim-yellow-sun',16,12,(u,v)=>inside(Math.PI+.83+(.5-u)*.20,.0915+v*.010),(u,v)=>[.265+u*.333,.57+v*.36]);sun.material=print.clone();sun.material.side=THREE.DoubleSide;
  mug.userData.reference='Visible front artwork reconstructed from user photo; unseen reverse remains plain ivory';
  return mug;
}
