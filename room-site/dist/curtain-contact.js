// A bounded contact field for the existing authored cloth, not a cloth solver.
// The door is sampled from its real leaf. No authored vertex buffer is edited.
const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t);};

export const curtainContactVertex=`
uniform vec4 curtainDoorPose,curtainDoorRange,curtainDoorShape;
uniform float curtainDoorActive;
varying float vCurtainContact;
vec3 curtainContact(vec3 p){
  if(curtainDoorActive<.5||p.x<curtainDoorRange.x||p.x>curtainDoorRange.y+.12||p.y>2.24)return p;
  float mask=smoothstep(curtainDoorRange.x-.025,curtainDoorRange.x,p.x)
    *(1.-smoothstep(curtainDoorRange.y,curtainDoorRange.y+.12,p.x))
    *(1.-smoothstep(curtainDoorRange.w,2.24,p.y));
  float limit=curtainDoorPose.y+(curtainDoorPose.w*(p.x-curtainDoorPose.x)-curtainDoorShape.x)/max(.001,curtainDoorPose.z);
  // Past the finite hinge end is also safe; do not project to an infinite plane
  // metres behind the room at very small opening angles.
  limit=max(limit,curtainDoorPose.y-.010);
  float q=p.z-limit;
  float push=.5*(q+sqrt(q*q+.000009))*mask*curtainDoorShape.y;
  p.z-=push;
  return p;
}
`;
export const curtainContactFragment=`
varying float vCurtainContact;
`;
export const curtainContactNormal=`
if(vCurtainContact>.001){
  vec3 contactFace=normalize(cross(dFdx(vViewPosition),dFdy(vViewPosition)));
  if(dot(contactFace,normal)<0.)contactFace=-contactFace;
  normal=normalize(mix(normal,contactFace,vCurtainContact));
}
`;

export function createCurtainDoorContact({THREE,world}){
  let pivot=null;world.traverse(o=>{if(o.userData.interactive==='wardrobeRight')pivot=o;});
  let leaf=null;pivot?.traverse(o=>{if(o.userData.blenderNode===pivot.userData.leafNodeId)leaf=o;});
  const uniforms={curtainDoorPose:{value:new THREE.Vector4()},curtainDoorRange:{value:new THREE.Vector4()},curtainDoorShape:{value:new THREE.Vector4()},curtainDoorActive:{value:0}};
  if(!leaf)return {uniforms,update:()=>false,get revision(){return 0;},get state(){return{active:false};},deform:p=>({...p})};
  world.updateMatrixWorld(true);leaf.geometry.computeBoundingBox();
  const inverse=new THREE.Matrix4().copy(pivot.matrixWorld).invert();
  const box=leaf.geometry.boundingBox.clone().applyMatrix4(new THREE.Matrix4().multiplyMatrices(inverse,leaf.matrixWorld));
  const hinge=new THREE.Vector3().setFromMatrixPosition(pivot.matrixWorld),rest=pivot.rotation.y;
  const shape={hingeX:hinge.x,hingeZ:hinge.z,minX:box.min.x,maxX:box.max.x,minY:box.min.y,maxY:box.max.y,minZ:box.min.z,maxZ:box.max.z};
  let angle=0,actual=0,release=0,revision=0,reviewEnabled=true;
  function update(dt,{immediate=false}={}){
    actual=Math.max(0,pivot.rotation.y-rest);
    let next=actual>=angle||immediate?actual:angle+(actual-angle)*(1-Math.exp(-Math.min(.05,dt)/.55));
    let nextRelease=actual>0?1:immediate?0:release*Math.exp(-Math.min(.05,dt)/.4);
    if(nextRelease<.00005)nextRelease=0;
    if(next<.00005)next=0;
    if(Math.abs(next-angle)<1e-7&&Math.abs(nextRelease-release)<1e-7)return false;
    angle=next;release=nextRelease;revision++;
    const sin=Math.sin(angle),cos=Math.cos(angle);
    uniforms.curtainDoorPose.value.set(hinge.x,hinge.z,sin,cos);
    uniforms.curtainDoorRange.value.set(hinge.x+box.min.x-.008,hinge.x+box.max.x*cos+box.max.z*sin+.012,hinge.y+box.min.y,hinge.y+box.max.y);
    // Keep the clearance in world Z; a fixed normal offset divided by sin(theta)
    // would keep a wide strip pinned backwards until the door was fully closed.
    uniforms.curtainDoorShape.value.set(box.max.x+.008*sin,release,0,0);
    uniforms.curtainDoorActive.value=reviewEnabled&&angle>0&&release>0?1:0;
    return true;
  }
  function deform(p){
    const range=uniforms.curtainDoorRange.value,pose=uniforms.curtainDoorPose.value;
    if(!reviewEnabled||!angle||p.x<range.x||p.x>range.y+.12||p.y>2.24)return {...p};
    const mask=smooth(range.x-.025,range.x,p.x)*(1-smooth(range.y,range.y+.12,p.x))*(1-smooth(range.w,2.24,p.y));
    const limit=Math.max(hinge.z-.010,hinge.z+(pose.w*(p.x-hinge.x)-uniforms.curtainDoorShape.value.x)/Math.max(.001,pose.z));
    const q=p.z-limit,push=.5*(q+Math.sqrt(q*q+.000009))*mask*release;
    return{x:p.x,y:p.y,z:p.z-push};
  }
  return{uniforms,update,deform,allowsDoorHit(p){const r=uniforms.curtainDoorRange.value;return reviewEnabled&&angle>0&&p.x>=r.x&&p.x<=r.y&&p.y<=r.w;},setReviewEnabled(value){reviewEnabled=!!value;uniforms.curtainDoorActive.value=reviewEnabled&&angle>0&&release>0?1:0;revision++;},get reviewEnabled(){return reviewEnabled;},get revision(){return revision;},get state(){return{version:'contact33',active:reviewEnabled&&angle>0&&release>0,reviewEnabled,actualAngle:actual,proxyAngle:angle,release,revision,shape};}};
}
