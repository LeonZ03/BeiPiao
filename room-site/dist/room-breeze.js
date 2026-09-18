// Animate the evaluated Blender meshes in the vertex shader. Instance buffers,
// authored shapes, attachment points and the approved sun-shadow proxies stay put.
const common=`
uniform float breezeTime,breezePower,breezePhase,breezeOpen;
uniform vec3 breezeDirection;
vec3 breezeTree(vec3 p){
  float tip=smoothstep(2.8,12.8,p.y)*smoothstep(.15,2.5,length(p.xz));
  float wave=sin(breezeTime*.57+breezePhase+p.y*.16)*.72
    +sin(breezeTime*.23+breezePhase*.71+p.x*.25+p.z*.2)*.28;
  return breezeDirection*(.11*breezePower*tip*wave);
}
vec3 breezeFlower(vec3 p){
  float height=clamp((p.y-.22)/.20,0.,1.);
  float wave=sin(breezeTime*.76+p.x*2.+p.z*2.)*.72+sin(breezeTime*.29+.8)*.28;
  return breezeDirection*(.016*breezePower*height*height*wave);
}
vec3 breezeInstanceLocal(vec3 d){
  #ifdef USE_INSTANCING
    // The exported instance transforms are orthogonal rotation/scale matrices.
    return vec3(dot(d,instanceMatrix[0].xyz)/dot(instanceMatrix[0].xyz,instanceMatrix[0].xyz),
      dot(d,instanceMatrix[1].xyz)/dot(instanceMatrix[1].xyz,instanceMatrix[1].xyz),
      dot(d,instanceMatrix[2].xyz)/dot(instanceMatrix[2].xyz,instanceMatrix[2].xyz));
  #else
    return d;
  #endif
}
mat3 breezeLeafRotation(){
  float phase=breezePhase;
  #ifdef USE_INSTANCING
    phase+=dot(instanceMatrix[3].xyz,vec3(1.9,.8,1.3));
  #endif
  float angle=breezePower*.23*(sin(breezeTime*1.31+phase)*.7+sin(breezeTime*.63+phase*.7)*.3);
  float c=cos(angle),s=sin(angle);return mat3(1.,0.,0.,0.,c,s,0.,-s,c);
}
`;
const deformation={
  branch:'transformed+=breezeTree(transformed);',
  leaf:`vec3 anchor=(instanceMatrix*vec4(0.,0.,-.128,1.)).xyz;
    transformed=breezeLeafRotation()*(transformed-vec3(0.,0.,-.128))+vec3(0.,0.,-.128);
    transformed+=breezeInstanceLocal(breezeTree(anchor));`,
  flower:`vec3 p=(instanceMatrix*vec4(transformed,1.)).xyz;
    transformed+=breezeInstanceLocal(breezeFlower(p));`,
  curtain:`
    float left=mix(-.7935000062,1.13-.345,breezeOpen);
    float sides=smoothstep(0.,.085,transformed.x-left)*smoothstep(0.,.085,1.13-transformed.x);
    float lower=smoothstep(.04,1.35,2.36-transformed.y);
    float phase=breezeTime*.82+transformed.x*2.1-transformed.y*.4;
    float wave=.5+.5*sin(phase);
    // A broad, visible billow, not extra pleats. Both attachment edges remain
    // pinned; depth only bows roomward, safely away from the bay and wardrobe.
    float cloth=breezePower*sides*lower;
    transformed.z+=.10*cloth*wave;
    transformed.x+=.040*cloth*sin(phase-.65)*mix(1.,.5,breezeOpen);
    transformed.y+=.012*cloth*sin(phase+.4);
  `
};

export function createRoomBreeze({THREE,world,camera,media=matchMedia}){
  const reduced=media('(prefers-reduced-motion: reduce)'),coarse=media('(pointer: coarse)');
  const clock={value:0},open={value:0},objects=[],entries=[],frustum=new THREE.Frustum(),vp=new THREE.Matrix4();
  const worldWind=new THREE.Vector3(.85,0,.53).normalize(),q=new THREE.Quaternion();
  let elapsed=0,nextStep=0,visible=0,enabled=false,revision=0;
  world.updateMatrixWorld(true);
  function attach(mesh,kind,phase=0){
    const original=mesh.material,material=original.clone();
    const direction=worldWind.clone().applyQuaternion(mesh.getWorldQuaternion(q).invert());
    const uniforms={breezeTime:clock,breezeOpen:open,breezePower:{value:0},breezePhase:{value:phase},breezeDirection:{value:direction}};
    const prior=original.onBeforeCompile,priorKey=original.customProgramCacheKey();
    material.onBeforeCompile=(shader,renderer)=>{
      prior.call(original,shader,renderer);
      Object.assign(shader.uniforms,uniforms);
      shader.vertexShader=common+shader.vertexShader;
      // This runs after Blender's Closed/Gathered morph, before world projection.
      shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>',deformation[kind]+'\n#include <project_vertex>');
      if(kind==='leaf')shader.vertexShader=shader.vertexShader.replace('#include <beginnormal_vertex>','#include <beginnormal_vertex>\nobjectNormal=breezeLeafRotation()*objectNormal;');
    };
    material.customProgramCacheKey=()=>priorKey+'-breeze28-'+kind;
    mesh.material=material;mesh.layers.enable(1);mesh.userData.dynamic=true;mesh.userData.breezeKind=kind;
    const bounds=new THREE.Box3().setFromObject(mesh).expandByScalar(kind==='branch'||kind==='leaf'?.17:.10);
    const center=kind==='flower'?new THREE.Vector3().setFromMatrixPosition(mesh.parent.matrixWorld):bounds.getCenter(new THREE.Vector3());
    objects.push(mesh);entries.push({mesh,kind,uniforms,bounds,center,moving:false});
  }
  world.traverse(o=>{
    if(o.name==='summer-leaf-canopy')attach(o,'leaf',o.parent.userData.crownVariant*1.7);
    else if(o.name==='tapered-poplar-branches')attach(o,'branch',o.parent.userData.crownVariant*1.7);
    else if(o.userData.curtainShapeKey)attach(o,'curtain');
    else if(o.isInstancedMesh&&o.parent?.name==='woven-basket-and-white-everlastings')attach(o,'flower');
  });
  function update(dt,openness,walking){
    open.value=openness;
    const active=walking&&!reduced.matches;
    if(!active){
      const changed=enabled;enabled=false;visible=0;
      if(changed){entries.forEach(e=>{e.uniforms.breezePower.value=0;e.moving=false;e.mesh.layers.disable(1);});revision++;}
      return changed;
    }
    enabled=true;elapsed+=Math.min(Math.max(dt,0),.05);
    const interval=1/(coarse.matches?24:30);
    if(elapsed+1e-6<nextStep)return false;
    nextStep+=Math.max(1,Math.floor((elapsed-nextStep+1e-6)/interval)+1)*interval;
    clock.value=elapsed;
    camera.updateMatrixWorld();vp.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);frustum.setFromProjectionMatrix(vp);
    const fade=Math.min(1,elapsed/2);
    // Long, uneven gusts; indoor flow follows the same weather with a soft delay.
    const gust=t=>.53+.21*Math.sin(t*.23)+.12*Math.sin(t*.071+1.2);
    visible=0;
    for(const e of entries){
      let shown=true;for(let p=e.mesh;p;p=p.parent)if(!p.visible){shown=false;break;}
      shown=shown&&frustum.intersectsBox(e.bounds);
      const distance=camera.position.distanceTo(e.center),range=e.kind==='flower'?6:40;
      if(distance>range)shown=false;
      // A closed curtain hides the trees from the room; keep their last static
      // image in the cache. A viewpoint inside the bay still sees the breeze.
      if((e.kind==='leaf'||e.kind==='branch')&&openness<.04&&camera.position.z> -1.60)shown=false;
      // Keep a constant physical breeze throughout the room: the old 3 m fade
      // reduced the already tiny flower motion to a fraction of a screen pixel.
      const attenuation=THREE.MathUtils.clamp((range-distance)/(e.kind==='flower'?1.5:5),0,1);
      const indoor=e.kind==='flower'||e.kind==='curtain';
      const indoorStrength=e.kind==='curtain'?.68+.32*openness:e.kind==='flower'?.42+.58*openness:1;
      e.uniforms.breezePower.value=fade*gust(elapsed-(indoor?1.4:0))*attenuation*indoorStrength;
      e.moving=shown;if(shown)e.mesh.layers.enable(1);else e.mesh.layers.disable(1);
      if(shown)visible++;
    }
    revision++;return visible>0;
  }
  return {objects,update,get movingObjects(){return entries.filter(e=>e.moving).map(e=>e.mesh);},get visibilityMask(){return entries.map(e=>Number(e.moving)).join('');},get enabled(){return enabled;},get time(){return clock.value;},get active(){return enabled&&visible>0;},
    get state(){return{version:'breeze28',enabled,visibleMeshes:visible,animatedMeshes:objects.length,leafInstances:objects.filter(o=>o.userData.breezeKind==='leaf').reduce((n,o)=>n+o.count,0),time:Number(clock.value.toFixed(2)),reducedMotion:reduced.matches,revision};}};
}
