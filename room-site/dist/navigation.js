import {bayWindow as bay} from './room-layout.js?v=blender18';
// A 2 mm point, swept against actual indoor surfaces. Furniture is never a full-height column.
export function createFlyNavigation(THREE,world,excluded=[]){
  const clearance=.002, meshes=[],dynamic=[],ray=new THREE.Raycaster(),dir=new THREE.Vector3(),end=new THREE.Vector3();
  const expanded=new THREE.Box3(),segment=new THREE.Box3(),hit=new THREE.Vector3();
  world.updateMatrixWorld(true);
  function collect(o,moving=false){
    if(excluded.includes(o)||o.userData.noCollision)return;
    moving=moving||!!o.userData.collisionDynamic;
    if(o.isMesh&&!o.isInstancedMesh&&!o.material.transparent&&!o.material.isShaderMaterial){
      o.geometry.computeBoundingBox();const bounds=o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld);
      if(bounds.max.y>=0&&bounds.min.y<2.7&&bounds.max.z>=bay.backZ&&bounds.min.z<3.19){const item={object:o,bounds};meshes.push(item);if(moving)dynamic.push(item);}
    }
    o.children.forEach(child=>collect(child,moving));
  }collect(world);
  function updateDynamic(){for(const {object,bounds}of dynamic){object.updateWorldMatrix(true,false);bounds.copy(object.geometry.boundingBox).applyMatrix4(object.matrixWorld);}}
  function canTravel(from,to){
    const inBay=to.x>bay.left+clearance&&to.x<bay.right-clearance&&to.y>bay.bottom+.043+clearance&&to.y<bay.top-clearance&&to.z>bay.frameZ+.066;
    if(to.x<=-1.4+clearance||to.x>=1.4-clearance||(to.z<=bay.roomZ+clearance&&!inBay)||to.z>=3.18-clearance||to.y<.017||to.y>2.64)return false;
    dir.subVectors(to,from);const distance=dir.length();if(distance<1e-8)return true;
    dir.divideScalar(distance);end.copy(to).addScaledVector(dir,clearance);segment.setFromPoints([from,end]);segment.expandByScalar(clearance);
    ray.set(from,dir);ray.near=0;ray.far=distance+clearance;
    for(const {object,bounds}of meshes){
      if(!segment.intersectsBox(bounds))continue;
      expanded.copy(bounds).expandByScalar(clearance);if(!ray.ray.intersectBox(expanded,hit))continue;
      if(ray.intersectObject(object,false).length)return false;
    }return true;
  }
  return {canTravel,updateDynamic,clearance,surfaces:meshes.length,dynamicSurfaces:dynamic.length};
}

// Combine static siblings by material. Moving/interactive objects and cutaway surfaces retain identity.
export function batchStaticGeometry(THREE,root,excluded=[]){
  let removed=0;
  function visit(parent){
    if(excluded.includes(parent)||parent.userData.interactive||parent.userData.dynamic)return;
    [...parent.children].filter(o=>!o.isMesh).forEach(visit);
    const sets=new Map();
    for(const o of parent.children){
      if(!o.isMesh||o.isInstancedMesh||o.name||excluded.includes(o)||o.userData.interactive||o.userData.dynamic||Array.isArray(o.material)||o.material.isShaderMaterial||!o.geometry.attributes.normal)continue;
      const key=`${o.material.uuid}/${o.castShadow}/${o.receiveShadow}`;if(!sets.has(key))sets.set(key,[]);sets.get(key).push(o);
    }
    for(const list of sets.values()){
      if(list.length<3)continue;
      const positions=[],normals=[],uvs=[],uv1s=[],colors=[],indices=[];let offset=0;
      const useColor=list[0].material.vertexColors,useLightMap=!!list[0].material.lightMap;
      for(const o of list){
        o.updateMatrix();const g=o.geometry.clone().applyMatrix4(o.matrix),p=g.attributes.position,n=g.attributes.normal,u=g.attributes.uv,l=g.attributes.uv1,c=g.attributes.color;
        for(let i=0;i<p.count;i++){positions.push(p.getX(i),p.getY(i),p.getZ(i));normals.push(n.getX(i),n.getY(i),n.getZ(i));uvs.push(u?u.getX(i):0,u?u.getY(i):0);if(useLightMap)uv1s.push(l?l.getX(i):0,l?l.getY(i):0);if(useColor)colors.push(c?c.getX(i):1,c?c.getY(i):1,c?c.getZ(i):1);}
        const index=g.index,count=index?index.count:p.count,flip=o.matrix.determinant()<0;
        for(let i=0;i<count;i+=3){const a=index?index.getX(i):i,b=index?index.getX(i+1):i+1,c=index?index.getX(i+2):i+2;indices.push(offset+a,offset+(flip?c:b),offset+(flip?b:c));}
        offset+=p.count;g.dispose();parent.remove(o);
      }
      const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uvs,2));if(useLightMap)g.setAttribute('uv1',new THREE.Float32BufferAttribute(uv1s,2));if(useColor)g.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));g.setIndex(indices);g.computeBoundingSphere();
      const mesh=new THREE.Mesh(g,list[0].material);mesh.name='static-material-batch';mesh.castShadow=list[0].castShadow;mesh.receiveShadow=list[0].receiveShadow;
      if(list.every(o=>o.geometry.userData.authoring==='Blender')){g.userData.authoring='Blender';mesh.userData.authoring='Blender';}
      parent.add(mesh);removed+=list.length-1;
    }
  }visit(root);return removed;
}
