import data from './assets/refined-props/models.js?v=blender18';
const geometries=new Map(),materials=new Map();
export function propGeometry(THREE,group,name){
  const item=data.groups[group].find(o=>o.name===name),key=group+'/'+name;
  if(!geometries.has(key)){
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(item.position,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(item.normal,3));g.setIndex(item.index);
    g.computeBoundingBox();g.computeBoundingSphere();g.userData.authoring='Blender';geometries.set(key,g);
  }
  return geometries.get(key);
}
export function buildProp(THREE,group){
  const root=new THREE.Group();root.userData.authoring='Blender';
  const batches=new Map();
  for(const item of data.groups[group]){
    if(!materials.has(item.material))materials.set(item.material,new THREE.MeshPhysicalMaterial(data.materials[item.material]));
    // Wheel and screen identity is retained; the many fixed spokes, fittings and
    // panels share one draw per material instead of a draw for every component.
    if(group==='motorcycle'&&!/rounded-sport-tyre|curved-windscreen/.test(item.name)){
      if(!batches.has(item.material))batches.set(item.material,{position:[],normal:[],index:[],parts:[]});
      const batch=batches.get(item.material),offset=batch.position.length/3;
      for(const n of item.position)batch.position.push(n);for(const n of item.normal)batch.normal.push(n);
      for(const n of item.index)batch.index.push(n+offset);batch.parts.push(item.name);continue;
    }
    const m=new THREE.Mesh(propGeometry(THREE,group,item.name),materials.get(item.material));m.name=item.name;m.castShadow=m.receiveShadow=true;root.add(m);
  }
  for(const [name,batch]of batches){
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(batch.position,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(batch.normal,3));g.setIndex(batch.index);g.computeBoundingSphere();
    const m=new THREE.Mesh(g,materials.get(name));m.name='GSX250R '+name;m.userData.parts=batch.parts;m.castShadow=m.receiveShadow=true;root.add(m);
  }
  return root;
}
