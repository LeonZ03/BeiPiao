// Keep the existing low-density shadow casters unchanged. The denser visible
// canopy has its own geometry, so the established sunbeam/dapple pattern remains.
export function createLushTrees({THREE,outside,bark,ground,assets,geometry}){
  const canvas=document.createElement('canvas');canvas.width=128;canvas.height=256;const ink=canvas.getContext('2d');
  const grad=ink.createLinearGradient(0,0,128,0);for(const [t,c]of [[0,'#bdcba9'],[.46,'#e4efd7'],[.51,'#d6e5c5'],[1,'#bccfa9']])grad.addColorStop(t,c);
  ink.fillStyle=grad;ink.fillRect(0,0,128,256);ink.strokeStyle='#eaf3d56b';ink.lineWidth=1;
  for(let y=22;y<249;y+=23)for(const s of [-1,1]){ink.beginPath();ink.moveTo(64,y);ink.quadraticCurveTo(64+s*24,y-6,64+s*58,y-23);ink.stroke();}
  ink.beginPath();ink.moveTo(64,0);ink.lineTo(64,256);ink.stroke();
  const map=new THREE.CanvasTexture(canvas);map.colorSpace=THREE.SRGBColorSpace;map.anisotropy=4;
  const leafMat=new THREE.MeshStandardMaterial({color:'#ffffff',map,roughness:.92,side:THREE.DoubleSide,emissive:'#344a25',emissiveIntensity:.04});
  // Leaves are distant and small: retain the arched midrib with fewer triangles,
  // keeping the denser canopy cheaper than repeating the former 48-triangle leaf.
  const lp=[],lu=[],li=[];
  for(let j=0;j<=4;j++)for(let i=0;i<=2;i++){
    const v=j/4,u=i/2,s=2*u-1,width=.063*Math.pow(Math.sin(v*Math.PI),.72);
    lp.push(width*s,.014*Math.pow(2*v-1,2)+.008*(1-Math.abs(s))*Math.sin(v*Math.PI),(v-.5)*.256);lu.push(u,v);
  }
  for(let j=0;j<4;j++)for(let i=0;i<2;i++){const a=j*3+i;li.push(a,a+3,a+1,a+1,a+3,a+4);}
  const visibleLeaf=new THREE.BufferGeometry();visibleLeaf.setAttribute('position',new THREE.Float32BufferAttribute(lp,3));visibleLeaf.setAttribute('uv',new THREE.Float32BufferAttribute(lu,2));visibleLeaf.setIndex(li);visibleLeaf.computeVertexNormals();visibleLeaf.computeBoundingSphere();
  const shadowMat=new THREE.MeshBasicMaterial({colorWrite:false,depthWrite:false,side:THREE.DoubleSide});
  const dummy=new THREE.Object3D(),color=new THREE.Color();
  const hash=n=>{const t=Math.sin(n*127.1+311.7)*43758.5453;return t-Math.floor(t);};
  const configs=[[0,.10,-7.25,1,0],[1,4.7,-7.25,1.075,1.9],[2,10.4,-7.25,1.025,3.8]];
  for(const [id,x,z,scale,rotation] of configs){
    const tree=new THREE.Group();tree.name='blender-summer-poplar-'+id;tree.position.set(x,ground,z);tree.scale.setScalar(scale);tree.rotation.y=rotation;outside.add(tree);
    const deform=(x,y,z)=>{const a=Math.min(1,Math.max(0,(y-3)/8));return [x*([1.05,.88,1.14][id]+.07*Math.sin(y*.61+id))+a*.26*Math.sin(y*.48+id*1.7),y*(1+[0,.028,-.025][id]*a),z*([.91,1.12,1.02][id]+.05*Math.cos(y*.72+id))+a*.18*Math.sin(y*.71+id*2)];};
    const branchGeo=geometry(THREE,'summer-branches').clone(),bp=branchGeo.attributes.position;
    for(let i=0;i<bp.count;i++)bp.setXYZ(i,...deform(bp.getX(i),bp.getY(i),bp.getZ(i)));branchGeo.computeVertexNormals();branchGeo.computeBoundingSphere();
    const branches=new THREE.Mesh(branchGeo,bark);branches.name='tapered-poplar-branches';branches.receiveShadow=true;tree.add(branches);
    const branchShadow=new THREE.Mesh(geometry(THREE,'summer-branches'),shadowMat);branchShadow.name='preserved-branch-shadow';branchShadow.castShadow=true;tree.add(branchShadow);
    const oldPoses=assets.leaves.filter((_,i)=>i%7===0);
    const shadows=new THREE.InstancedMesh(geometry(THREE,'summer-leaf'),shadowMat,oldPoses.length);shadows.name='summer-leaf-shadow-layer';
    oldPoses.forEach(([x,y,z,yaw,tilt,size],i)=>{dummy.position.set(x,y,z);dummy.rotation.set(tilt,yaw,yaw*.13);dummy.scale.setScalar(size*.77);dummy.updateMatrix();shadows.setMatrixAt(i,dummy.matrix);});
    shadows.castShadow=true;shadows.computeBoundingSphere();tree.add(shadows);
    const poses=[];
    assets.leaves.forEach((p,i)=>{
      for(let cluster=0;cluster<4;cluster++)poses.push([...p,i,cluster]);
      if(i%3===id)poses.push([...p,i,4]);
    });
    const leaves=new THREE.InstancedMesh(visibleLeaf,leafMat,poses.length);leaves.name='summer-leaf-canopy';
    poses.forEach(([x,y,z,yaw,tilt,size,t,index,extra],i)=>{
      const seed=index+id*7289+extra*6121,r=hash(seed),a=hash(seed+2)*Math.PI*2;
      if(extra){const distance=.045+.12*r;x+=Math.cos(a)*distance;y+=(hash(seed+4)-.35)*.11;z+=Math.sin(a)*distance;}
      dummy.position.set(...deform(x,y,z));dummy.rotation.set(tilt+(hash(seed+7)-.5)*.38,yaw+extra*.93,(yaw*.13)+(r-.5)*.38);
      dummy.scale.set(size*(.50+hash(seed+5)*.16),size*(.52+hash(seed+6)*.15),size*(.50+hash(seed+5)*.16));dummy.updateMatrix();leaves.setMatrixAt(i,dummy.matrix);
      color.setHSL(.29+hash(seed+8)*.035,.39+hash(seed+9)*.15,.44+hash(seed+10)*.10,THREE.SRGBColorSpace);leaves.setColorAt(i,color);
    });
    leaves.castShadow=false;leaves.receiveShadow=false;leaves.computeBoundingSphere();tree.add(leaves);
    tree.userData.authoring=assets.metadata.authoring;tree.userData.season='summer';tree.userData.crownVariant=id;
  }
}
