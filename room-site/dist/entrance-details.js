import data from './assets/door-details/models.js?v=blender18';
export function addEntranceDetails(c,door){
  const {THREE}=c;
  for(const [name,items] of Object.entries(data.groups)){
    const group=new THREE.Group();group.name={lock:'fitted-lever-door-lock',charm:'lion-dance-rabbit-keychain',thumbturn:'clickable-privacy-thumbturn'}[name];group.userData.authoring='Blender';
    group.position.set(...({lock:[-.78,1.02,-.043],charm:[-.45,1.93,-.060],thumbturn:[-.78,.986,-.055]}[name]));
    // Handle extends toward the centre of the door, away from the latch edge.
    if(name!=='charm')group.scale.x=-1;
    if(name==='thumbturn'){group.userData.interactive='doorLock';group.userData.dynamic=true;group.userData.locked=false;}
    for(const item of items){
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(item.position,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(item.normal,3));g.setIndex(item.index);g.computeBoundingSphere();
      const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial(data.materials[item.material]));m.castShadow=m.receiveShadow=true;m.userData.parts=item.parts;group.add(m);
    }
    door.add(group);
  }
}
