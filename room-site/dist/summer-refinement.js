import assets from './assets/summer/models.js?v=soft9';
import {refineCottonPillow} from './close-refinements.js?v=blender18';
import {createLushTrees} from './lush-trees.js?v=blender18';

// These are evaluated Blender meshes, exported in metres into the room's Y-up
// coordinate system. Geometry and material instances are shared on the GPU.
const geometries=new Map();
function geometry(THREE,name){
  if(!geometries.has(name)){
    const data=assets.meshes[name],g=new THREE.BufferGeometry();
    g.setAttribute('position',new THREE.Float32BufferAttribute(data.position,3));
    g.setAttribute('normal',new THREE.Float32BufferAttribute(data.normal,3));
    g.setAttribute('uv',new THREE.Float32BufferAttribute(data.uv,2));
    g.setIndex(data.index);g.computeBoundingBox();g.computeBoundingSphere();
    g.userData.authoring=assets.metadata.authoring;geometries.set(name,g);
  }
  return geometries.get(name);
}

export function refineBlenderBedding({THREE,bed}){
  for(const name of ['duvet-top','duvet-underside']){
    const mesh=bed.getObjectByName(name);mesh.geometry.dispose();mesh.geometry=geometry(THREE,name);
    mesh.userData.authoring='Blender';mesh.material.roughness=.86;
  }
  const pillow=bed.getObjectByName('single-centered-pillow');
  refineCottonPillow(THREE,pillow);
  // Join the actual cloth boundaries, rather than leaving two disconnected skins.
  const g=geometry(THREE,'duvet-top'),p=g.attributes.position,u=g.attributes.uv;
  const border=[];
  for(let i=0;i<p.count;i++){
    const x=u.getX(i),y=u.getY(i);
    if(x<.00001||x>.99999||y<.00001||y>.99999){
      const t=y<.00001?x:x>.99999?1+y:y>.99999?3-x:4-y;
      border.push({t,p:new THREE.Vector3().fromBufferAttribute(p,i)});
    }
  }
  border.sort((a,b)=>a.t-b.t);
  const edge=bed.getObjectByName('duvet-stitched-edge');edge.geometry.dispose();
  edge.geometry=new THREE.TubeGeometry(new THREE.CatmullRomCurve3(border.map(v=>v.p),true),256,.0024,6,true);
  const positions=[],indices=[];
  border.forEach(({p},i)=>{positions.push(p.x,p.y,p.z,p.x,.555,p.z);const n=(i+1)%border.length;indices.push(i*2,n*2,n*2+1,i*2,n*2+1,i*2+1);});
  const side=new THREE.BufferGeometry();side.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));side.setIndex(indices);side.computeVertexNormals();
  const seam=new THREE.Mesh(side,edge.material);seam.name='blender-duvet-tailored-side';seam.castShadow=seam.receiveShadow=true;bed.add(seam);
}

export function refineBlenderChair({THREE,chair}){
  for(const o of chair.children){
    if(!o.isMesh)continue;
    const name=Math.abs(o.position.y-.455)<.001?'chair-seat':Math.abs(o.position.y-.685)<.001?'chair-back':null;
    if(name){o.geometry=geometry(THREE,name);o.name='blender-upholstered-'+name;o.userData.authoring='Blender';}
  }
}

export function addSummerTrees({THREE,outside,bark,ground}){
  return createLushTrees({THREE,outside,bark,ground,assets,geometry});
}

// Diffuse indirect lighting baked in Blender Cycles, spatially filtered to remove
// Monte Carlo noise. uv1 is world-mapped so each tile samples its real room position.
export function applyBakedRoomLight({THREE,world,M,loader}){
  const mats=new Map(),point=new THREE.Vector3();
  function material(base,name){
    const key=base.uuid+'/'+name;
    if(!mats.has(key)){
      const m=base.clone(),map=loader.load('./assets/summer/indirect-'+name+'.png');
      map.colorSpace=THREE.NoColorSpace;map.channel=1;map.minFilter=THREE.LinearMipmapLinearFilter;
      m.lightMap=map;m.lightMapIntensity=.46;m.userData.bakedIndirect=name;mats.set(key,m);
    }
    return mats.get(key);
  }
  world.updateMatrixWorld(true);
  for(const o of world.children){
    if(!o.isMesh)continue;
    let name,uv;
    if(o.material===M.tile){name='floor';uv=p=>[(p.x+1.4)/2.8,(3.18-p.z)/4.98];}
    else if(o.material===M.gray){name='left';uv=p=>[(1.8-p.z)/3.6,p.y/2.65];}
    else if(o.material===M.pink&&o.position.x>1.4){name='right';uv=p=>[(p.z+1.8)/4.98,p.y/2.65];}
    else if(o.material===M.white&&Math.abs(o.position.z-1.83)<.01){name='head';uv=p=>[(.32-p.x)/1.72,p.y/2.65];}
    else if(o.material===M.ceiling){name='ceiling';uv=p=>[(p.x+1.4)/2.8,(p.z+1.8)/4.98];}
    if(!name)continue;
    o.geometry=o.geometry.clone();const p=o.geometry.attributes.position,values=[];
    for(let i=0;i<p.count;i++){point.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);values.push(...uv(point).map(v=>THREE.MathUtils.clamp(v,0,1)));}
    o.geometry.setAttribute('uv1',new THREE.Float32BufferAttribute(values,2));o.material=material(o.material,name);
  }
  return amount=>{for(const m of mats.values())m.lightMapIntensity=.24+.22*amount;};
}
