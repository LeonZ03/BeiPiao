// Geometry, placements, PBR surfaces and pivots come from the editable Blender
// project. The browser only uploads the evaluated meshes and animates objects.
import {installExteriorSurface} from './exterior-surface.js?v=exterior31';
export function parseBlenderRoom(THREE,manifest,buffer,textures){
  if(manifest.format!=='blender-room-pack-1')throw new Error('Unsupported room asset');
  const array=a=>new ({Float32Array,Uint32Array,Uint16Array,Int16Array}[a.type])(buffer,a.offset,a.length);
  const materials=manifest.materials.map(desc=>{
    const Constructor=THREE[desc.type];if(!Constructor)throw new Error('Unknown room material '+desc.type);
    const m=new Constructor();
    for(const[key,value]of Object.entries(desc.props))if(key in m)m[key]=value;
    for(const[key,value]of Object.entries(desc.colors))if(key in m)m[key]=new THREE.Color().fromArray(value);
    for(const[key,value]of Object.entries(desc.vectors))m[key]=new THREE.Vector2().fromArray(value);
    for(const[key,value]of Object.entries(desc.textures))m[key]=textures[value];
    m.userData={...desc.userData,authoring:'Blender'};
    if(m.userData.multiplyCurtainAlbedo){
      m.onBeforeCompile=shader=>{shader.fragmentShader=shader.fragmentShader.replace('#include <emissivemap_fragment>',`#include <emissivemap_fragment>
        #ifdef USE_MAP
        totalEmissiveRadiance *= texture2D(map,vMapUv).rgb;
        #endif
      `);};
      m.customProgramCacheKey=()=> 'woven-curtain-backlight-v1';
    }
    installExteriorSurface(m);
    return m;
  });
  const geometries=manifest.geometries.map(desc=>{
    const g=new THREE.BufferGeometry();
    for(const[key,value]of Object.entries(desc.attributes)){
      let data=array(value);
      if(value.decodeScale){const unpacked=new Float32Array(data.length);for(let i=0;i<data.length;i++){const axis=i%value.itemSize;unpacked[i]=data[i]*value.decodeScale[axis]+value.decodeOffset[axis];}data=unpacked;}
      if(value.normalized){const unpacked=new Float32Array(data.length);for(let i=0;i<data.length;i++)unpacked[i]=Math.max(-1,data[i]/32767);data=unpacked;}
      g.setAttribute(key,new THREE.BufferAttribute(data,value.itemSize));
    }
    g.setIndex(new THREE.BufferAttribute(array(desc.index),1));
    // Both states are authored in Blender; animate cloth without squashing its
    // depth, hem or fringe along with the width of the curtain.
    if(desc.morphTargets){
      for(const[key,targets]of Object.entries(desc.morphTargets))g.morphAttributes[key]=targets.map(a=>new THREE.BufferAttribute(array(a),a.itemSize));
      g.morphTargetsRelative=false;
    }
    for(const group of desc.groups)g.addGroup(group.start,group.count,group.materialIndex);
    g.userData={...desc.userData,blenderGeometry:desc.id};g.computeBoundingBox();g.computeBoundingSphere();return g;
  });
  const nodes=manifest.nodes.map(desc=>{
    let o;
    if(desc.type==='Group')o=new THREE.Group();
    else{
      const m=Array.isArray(desc.material)?desc.material.map(i=>materials[i]):materials[desc.material];
      o=desc.type==='InstancedMesh'?new THREE.InstancedMesh(geometries[desc.geometry],m,desc.count):new THREE.Mesh(geometries[desc.geometry],m);
      if(desc.instanceMatrix){o.instanceMatrix.array.set(array(desc.instanceMatrix));o.instanceMatrix.needsUpdate=true;}
      if(desc.instanceColor)o.instanceColor=new THREE.InstancedBufferAttribute(array(desc.instanceColor),3);
      if(o.isInstancedMesh){o.computeBoundingBox();o.computeBoundingSphere();}
    }
    o.name=desc.name;o.userData={...desc.userData};o.visible=desc.visible;
    o.castShadow=desc.castShadow;o.receiveShadow=desc.receiveShadow;o.renderOrder=desc.renderOrder;o.frustumCulled=desc.frustumCulled;
    o.matrix.fromArray(desc.matrix);o.matrix.decompose(o.position,o.quaternion,o.scale);return o;
  });
  manifest.nodes.forEach((desc,i)=>{if(desc.parent>=0)nodes[desc.parent].add(nodes[i]);});
  const refs={};for(const[key,value]of Object.entries(manifest.refs))refs[key]=Array.isArray(value)?value.map(i=>nodes[i]):nodes[value];
  refs.world.updateMatrixWorld(true);
  return {world:refs.world,refs,materials,statistics:{...manifest.statistics,objects:manifest.nodes.length,source:'Blender',revision:manifest.revision}};
}

export async function loadBlenderRoom(THREE,manager,onProgress=()=>{}){
  onProgress(3,'正在读取房间');
  const response=await fetch('./assets/full-room/scene.json?v=exterior31f');
  if(!response.ok)throw new Error('Room manifest '+response.status);
  const manifest=await response.json(),compressed=typeof DecompressionStream!=='undefined';
  let geometryProgress=0,textureCount=0;
  const update=()=>onProgress(8+60*geometryProgress+20*textureCount/Math.max(1,manifest.textures.length),geometryProgress<1?'正在载入房间':'正在准备材质');
  update();
  const binary=fetch((compressed?manifest.compressedBinary:manifest.binary)+'?v='+manifest.revision).then(async r=>{
    if(!r.ok)throw new Error('Room geometry '+r.status);
    const total=Number(r.headers.get('Content-Length')),chunks=[];
    let received=0,bytes;
    if(r.body){
      const reader=r.body.getReader();
      while(true){const {done,value}=await reader.read();if(done)break;chunks.push(value);received+=value.length;if(total>0){geometryProgress=Math.min(.99,received/total);update();}}
      bytes=new Uint8Array(received);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    }else bytes=new Uint8Array(await r.arrayBuffer());
    const buffer=compressed?await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():bytes.buffer;
    geometryProgress=1;update();return buffer;
  });
  const loader=new THREE.TextureLoader(manager);
  const texturePromise=Promise.all(manifest.textures.map(async desc=>{
    const t=await loader.loadAsync(desc.webPath);
    for(const key of ['wrapS','wrapT','magFilter','minFilter','anisotropy','flipY','colorSpace','channel','rotation','premultiplyAlpha','generateMipmaps','mapping'])if(desc[key]!==undefined)t[key]=desc[key];
    for(const key of ['repeat','offset','center'])t[key].fromArray(desc[key]);
    t.needsUpdate=true;textureCount++;update();return t;
  }));
  const [buffer,textures]=await Promise.all([binary,texturePromise]);
  onProgress(90,'正在整理房间');
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  return parseBlenderRoom(THREE,manifest,buffer,textures);
}
