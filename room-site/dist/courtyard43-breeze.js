// Reuse Yongwang's slow gust timing, adapted to a sheltered winter balcony.
// Authored Blender meshes/pivots remain authoritative. No simulation, geometry
// uploads, dynamic shadow maps or additional render passes are required.
export const courtyardGust=t=>.53+.21*Math.sin(t*.23)+.12*Math.sin(t*.071+1.2);
export const hangerAngle=(t,phase)=>.075*courtyardGust(t)*(Math.sin(t*.81+phase)*.76+Math.sin(t*.37+phase*.7)*.24);
const clothShader=`
uniform float c38Time,c38Power,c38Top,c38Bottom,c38Amplitude,c38Phase;
// Displacement and d(displacement)/dy, for a consistent softly sheared normal.
vec4 c38Cloth(vec3 p){
  float h=max(.1,c38Top-.035-c38Bottom);
  float t=clamp((c38Top-.035-p.y)/h,0.,1.);
  float w=t*t, dw=t>0.&&t<1.?-2.*t/h:0.;
  float phase=c38Time*.63+c38Phase-p.y*.28;
  float wave=.55+.45*sin(phase), derivative=-.126*cos(phase);
  float z=c38Amplitude*c38Power*w*wave;
  float dz=c38Amplitude*c38Power*(dw*wave+w*derivative);
  return vec4(0.,z,0.,dz);
}
`;
export function createCourtyardBreeze({THREE,world,camera,media=matchMedia}){
  const reduced=media('(prefers-reduced-motion: reduce)'),coarse=media('(pointer: coarse)');
  const clock={value:0},power={value:0},cloth=[],hangers=[],objects=[];
  const frustum=new THREE.Frustum(),vp=new THREE.Matrix4(),axis=new THREE.Vector3(1,0,0),turn=new THREE.Quaternion();
  let elapsed=0,next=0,enabled=false,visible=0,revision=0;
  world.updateMatrixWorld(true);
  world.traverse(mesh=>{
    if(!mesh.isMesh)return;
    if(mesh.userData.breezeHanger){
      hangers.push({mesh,base:mesh.quaternion.clone(),phase:mesh.userData.breezePhase??0});objects.push(mesh);return;
    }
    const outer=!!mesh.userData.breezeCloth,grey=mesh.userData.surface==='grey-curtain';
    if(!outer&&!grey)return;
    const bounds=new THREE.Box3().setFromObject(mesh).expandByScalar(.025);
    const uniforms={c38Time:clock,c38Power:power,c38Top:{value:mesh.userData.fixedTop},c38Bottom:{value:bounds.min.y},c38Amplitude:{value:outer?.025:.012},c38Phase:{value:mesh.userData.breezePhase??0}};
    const originals=Array.isArray(mesh.material)?mesh.material:[mesh.material];
    const copies=originals.map(original=>{
      const material=original.clone(),prior=original.onBeforeCompile,key=original.customProgramCacheKey();
      material.onBeforeCompile=(shader,renderer)=>{
        prior.call(original,shader,renderer);Object.assign(shader.uniforms,uniforms);
        shader.vertexShader=clothShader+shader.vertexShader;
        shader.vertexShader=shader.vertexShader.replace('#include <defaultnormal_vertex>','vec4 c38N=c38Cloth(position); objectNormal.y-=c38N.w*objectNormal.z;\n#include <defaultnormal_vertex>');
        shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','vec4 c38D=c38Cloth(transformed); transformed.z+=c38D.y;\n#include <project_vertex>');
      };
      material.customProgramCacheKey=()=>key+':courtyard-breeze38';return material;
    });
    mesh.material=Array.isArray(mesh.material)?copies:copies[0];
    mesh.userData.dynamic=true;cloth.push({mesh,originals,copies,bounds});objects.push(mesh);
  });
  function shown(mesh){for(let p=mesh;p;p=p.parent)if(!p.visible)return false;return true;}
  function reset(){power.value=0;for(const e of hangers)e.mesh.quaternion.copy(e.base);}
  return{objects,
    update(dt,{active,openness=1}={}){
      // Lighting owns the original material records. Keep the wind copies in
      // step when either independent curtain or the ceiling switch changes.
      for(const e of cloth)for(let i=0;i<e.copies.length;i++)e.copies[i].emissiveIntensity=e.originals[i].emissiveIntensity;
      if(!active||reduced.matches){const changed=enabled;enabled=false;visible=0;if(changed){reset();revision++;}return changed;}
      enabled=true;elapsed+=Math.min(Math.max(dt,0),.05);
      if(elapsed+1e-6<next)return false;
      next=elapsed+1/(coarse.matches?24:30);clock.value=elapsed;
      camera.updateMatrixWorld();vp.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);frustum.setFromProjectionMatrix(vp);
      visible=cloth.filter(e=>shown(e.mesh)&&frustum.intersectsBox(e.bounds)).length;
      const fade=Math.min(1,elapsed/2);power.value=fade*courtyardGust(elapsed-1.4)*(.68+.32*openness);
      for(const e of hangers){e.mesh.quaternion.copy(e.base).multiply(turn.setFromAxisAngle(axis,fade*hangerAngle(elapsed,e.phase)));if(shown(e.mesh)&&frustum.intersectsObject(e.mesh))visible++;}
      revision++;return visible>0;
    },
    get active(){return enabled&&visible>0;},
    get state(){return{version:'balcony38',enabled,visibleMeshes:visible,clothMeshes:cloth.length,hangers:hangers.length,time:+elapsed.toFixed(2),revision,reducedMotion:reduced.matches,hangerAngles:hangers.map(e=>+e.mesh.quaternion.angleTo(e.base).toFixed(5))};},
    dispose(){reset();for(const e of cloth){e.mesh.material=e.originals.length===1?e.originals[0]:e.originals;for(const m of e.copies)m.dispose();}}
  };
}
