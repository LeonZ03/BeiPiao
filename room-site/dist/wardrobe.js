// All planar mirrors share one recursion guard. A reflection may display the
// other mirror's cached texture, but never recursively render its camera.
export function guardRoomReflection({THREE,world,reflection,interval=50,synchronizeView=false}){
  const draw=reflection.onBeforeRender,previousCamera=new THREE.Matrix4(),previousMirror=new THREE.Matrix4();
  let last=-Infinity,lastLighting='',lastGeometry=-1;
  reflection.onBeforeRender=function(renderer,scene,camera,...args){
    if(world.userData.reflectionPass||world.userData.staticCacheCapture)return;
    const lighting=scene.children.filter(o=>o.isLight).map(o=>`${o.intensity.toFixed(4)}:${o.color.getHex()}`).join('/');
    const geometry=world.userData.geometryRevision||0;
    const viewChanged=!previousCamera.equals(camera.matrixWorld)||!previousMirror.equals(this.matrixWorld);
    const changed=viewChanged||lighting!==lastLighting||geometry!==lastGeometry||world.userData.waterActive;
    const now=performance.now();
    if(!changed||(!(synchronizeView&&viewChanged)&&geometry===lastGeometry&&now-last<interval))return;
    const shadows=renderer.shadowMap.needsUpdate;
    world.userData.reflectionPass=true;renderer.shadowMap.needsUpdate=false;
    try{
      draw.call(this,renderer,scene,camera,...args);
      last=now;previousCamera.copy(camera.matrixWorld);previousMirror.copy(this.matrixWorld);lastLighting=lighting;lastGeometry=geometry;
    }finally{world.userData.reflectionPass=false;renderer.shadowMap.needsUpdate=shadows;}
  };
  return reflection;
}

function installDoorMirror({THREE,world,renderer,source,Reflector}){
  if(!source||!renderer?.isWebGLRenderer)return source;
  const coarse=globalThis.matchMedia?.('(pointer: coarse)').matches;
  // Reduce pixel cost instead of skipping moving views, which causes judder.
  const mirror=new Reflector(source.geometry,{textureWidth:coarse?128:256,textureHeight:coarse?256:512,multisample:0,clipBias:.001,
    shader:{uniforms:{color:{value:new THREE.Color(0xffffff)},tDiffuse:{value:null},textureMatrix:{value:new THREE.Matrix4()}},
      vertexShader:'uniform mat4 textureMatrix;varying vec4 reflectedUv;void main(){reflectedUv=textureMatrix*vec4(position,1.);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
      fragmentShader:`uniform sampler2D tDiffuse;varying vec4 reflectedUv;void main(){gl_FragColor=vec4(texture2DProj(tDiffuse,reflectedUv).rgb*vec3(.94,.95,.95),1.);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`}
  });
  mirror.name=source.name;mirror.position.copy(source.position);mirror.quaternion.copy(source.quaternion);mirror.scale.copy(source.scale);
  mirror.visible=source.visible;mirror.renderOrder=source.renderOrder;mirror.frustumCulled=source.frustumCulled;
  mirror.userData={...source.userData,dynamic:true,noCollision:true};mirror.castShadow=false;mirror.receiveShadow=false;
  mirror.geometry.userData={...source.geometry.userData};
  source.parent.add(mirror);source.removeFromParent();
  return guardRoomReflection({THREE,world,reflection:mirror,interval:50,synchronizeView:true});
}

export function createWardrobe({THREE,world,camera,refs={},renderer,Reflector,toast=()=>{}}){
  world.userData.geometryRevision??=0;
  const axis=new THREE.Vector3(0,1,0),rotation=new THREE.Quaternion(),inverse=new THREE.Matrix4(),point=new THREE.Vector3(),box=new THREE.Box3();
  const nodes=new Map();world.traverse(o=>{if(o.userData.blenderNode!==undefined)nodes.set(o.userData.blenderNode,o);});
  const ids=['wardrobeLeft','wardrobeMiddle','wardrobeRight'];
  const doors=(refs.wardrobeDoors||[]).map((pivot,index)=>{
    pivot.userData.dynamic=true;pivot.userData.collisionDynamic=true;
    pivot.userData.interactive=ids[index];
    const surfaces=[];
    pivot.traverse(o=>{if(o.isMesh&&!o.userData.noCollision){o.geometry.computeBoundingBox();surfaces.push(o);}});
    const leaf=surfaces.find(o=>o.userData.blenderNode===pivot.userData.leafNodeId);
    return {pivot,id:ids[index],base:pivot.quaternion.clone(),openAngle:pivot.userData.openAngle??(index===0?-1.48:1.48),value:0,wanted:false,blocked:false,surfaces:leaf?[leaf]:surfaces};
  });
  const mechanisms=(refs.wardrobeHingeMechanisms||[]).map(group=>{
    group.userData.dynamic=true;group.userData.noCollision=true;
    const data=group.userData,door=nodes.get(data.doorNodeId),upper=nodes.get(data.upperArmNodeId),lower=nodes.get(data.lowerArmNodeId),joint=nodes.get(data.jointNodeId);
    if(!door||!upper||!lower||!joint)throw new Error('Missing authored wardrobe hinge nodes');
    return {group,door,upper,lower,joint,fixed:new THREE.Vector3().fromArray(data.fixedAnchor),moving:new THREE.Vector3().fromArray(data.movingAnchor),length:data.armLength,sign:data.elbowSign??1};
  });
  const anchorA=new THREE.Vector3(),anchorB=new THREE.Vector3(),elbow=new THREE.Vector3(),delta=new THREE.Vector3(),bend=new THREE.Vector3();
  function updateHinges(){
    for(const m of mechanisms){
      m.group.updateWorldMatrix(true,false);m.door.updateWorldMatrix(true,false);
      inverse.copy(m.group.matrixWorld).invert();
      anchorA.copy(m.fixed).applyMatrix4(m.group.parent.matrixWorld).applyMatrix4(inverse);
      anchorB.copy(m.moving).applyMatrix4(m.door.matrixWorld).applyMatrix4(inverse);
      delta.subVectors(anchorB,anchorA);const distance=delta.length();
      if(distance>2*m.length+.0001)throw new Error('Wardrobe hinge anchors exceed the two authored arm lengths');
      bend.set(-delta.z,0,delta.x);if(bend.lengthSq()<1e-12)bend.set(1,0,0);else bend.normalize();
      elbow.copy(anchorA).add(anchorB).multiplyScalar(.5).addScaledVector(bend,Math.sqrt(Math.max(0,m.length*m.length-distance*distance*.25))*m.sign);
      for(const [arm,start,end]of [[m.upper,anchorA,elbow],[m.lower,elbow,anchorB]]){
        arm.position.copy(start).add(end).multiplyScalar(.5);arm.quaternion.setFromUnitVectors(axis,delta.subVectors(end,start).normalize());arm.scale.y=m.length;arm.updateMatrix();
      }
      m.joint.position.copy(elbow);m.group.updateWorldMatrix(true,true);
    }
  }
  updateHinges();
  const mirror=installDoorMirror({THREE,world,renderer,source:refs.wardrobeMirror,Reflector});
  if(mirror)refs.wardrobeMirror=mirror;
  let revision=0,pendingTime=0;
  function toggle(id){
    const door=doors.find(d=>d.id===id);if(!door)return false;
    door.wanted=!door.wanted;door.blocked=false;
    toast(door.wanted?'正在打开柜门':'正在合上柜门');return true;
  }
  function place(door,value){door.pivot.quaternion.copy(door.base).multiply(rotation.setFromAxisAngle(axis,door.openAngle*value));door.pivot.updateWorldMatrix(true,true);}
  function cameraInside(door){
    for(const mesh of door.surfaces){
      if(!mesh.parent)continue;
      inverse.copy(mesh.matrixWorld).invert();point.copy(camera.position).applyMatrix4(inverse);
      box.copy(mesh.geometry.boundingBox).expandByScalar(.005);
      if(box.containsPoint(point))return true;
    }return false;
  }
  function update(dt){
    pendingTime+=Math.min(.05,Math.max(0,dt));
    if(pendingTime<1/30)return false;
    dt=pendingTime;pendingTime=0;
    let changed=false;
    for(const door of doors){
      const target=door.wanted?1:0;
      door.blocked=false;
      if(Math.abs(target-door.value)<1e-7)continue;
      // Slower travel leaves room for the wooden hinge creak (about 1 s to 95%).
      let next=door.value+(target-door.value)*(1-Math.exp(-Math.min(.05,Math.max(0,dt))*3.1));
      if(Math.abs(target-next)<.0004)next=target;
      // Sweep a 2 mm viewpoint against the moving solid door, not only its
      // final pose. A blocked door waits for the observer to move out of reach.
      const steps=Math.max(1,Math.ceil(Math.abs(next-door.value)*Math.abs(door.openAngle)/.006));
      for(let i=1;i<=steps;i++){
        place(door,door.value+(next-door.value)*i/steps);
        if(cameraInside(door)){door.blocked=true;break;}
      }
      if(door.blocked){place(door,door.value);continue;}
      if(Math.abs(next-door.value)>1e-8){door.value=next;changed=true;}
    }
    if(changed){updateHinges();revision++;world.userData.geometryRevision=(world.userData.geometryRevision||0)+1;}
    return changed;
  }
  return {toggle,update,mirror,
    get revision(){return revision;},
    get active(){return doors.some(d=>Math.abs((d.wanted?1:0)-d.value)>1e-7);},
    label(id){const d=doors.find(d=>d.id===id);return d?.wanted?'点击柜门 · 合上':'点击柜门 · 打开';},
    get state(){return {version:'wardrobe-audio2',doors:doors.map(d=>({id:d.id,open:d.wanted,amount:Number(d.value.toFixed(5)),angle:Number((d.value*d.openAngle).toFixed(5)),blocked:d.blocked})),revision};}
  };
}
