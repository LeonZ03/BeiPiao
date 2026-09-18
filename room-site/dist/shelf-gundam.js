import model from './assets/shelf-gundam/models.js?v=blender18';

export function addShelfGundam({THREE,desk}){
  const root=new THREE.Group();root.name='photo-guided-shelf-gundam';root.position.set(.135,1.662,.255);root.rotation.y=-Math.PI/2;desk.add(root);
  const materials={};
  for(const [name,p] of Object.entries(model.palette))materials[name]=new THREE.MeshStandardMaterial({color:new THREE.Color().fromArray(p.color),metalness:p.metalness,roughness:Math.min(1,p.roughness+.10)});
  for(const item of model.meshes){
    const g=new THREE.BufferGeometry();
    for(const [name,size] of [['position',3],['normal',3],['uv',2]])g.setAttribute(name,new THREE.Float32BufferAttribute(item[name],size));
    g.setIndex(item.index);g.computeBoundingSphere();
    const mesh=new THREE.Mesh(g,materials[item.material]);mesh.name=item.name;mesh.castShadow=mesh.receiveShadow=true;root.add(mesh);
  }
  // Keep the whole miniature (shield included) at exactly 3/5 of its previous height.
  const basket=desk.getObjectByName('woven-basket-and-white-everlastings');desk.updateMatrixWorld(true);
  const basketHeight=new THREE.Box3().setFromObject(basket,true).getSize(new THREE.Vector3()).y;
  const targetHeight=basketHeight*.75*.60;root.scale.setScalar(targetHeight/model.metadata.overallHeight);
  root.userData.authoring='Blender';root.userData.ratioToBasket=.45;root.userData.scaleVsPrevious=.60;root.userData.overallHeight=targetHeight;
  return root;
}
