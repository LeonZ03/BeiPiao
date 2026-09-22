// Courtyard-specific geometry batching, real-surface navigation and neutral
// lighting. No Yongwang layout, vegetation, time-of-day or particle assumptions.
export const DOOR_RESPONSE=3.1;
export function easedAmount(current,target,dt,response=DOOR_RESPONSE){const next=current+(target-current)*(1-Math.exp(-Math.max(0,Math.min(.05,dt))*response));return Math.abs(next-target)<.001?target:next;}
// A blocked door can stop with a fractional target. Subsequent clicks still
// choose a complete endpoint, while a moving door reverses its intended state.
export function oppositeEndpoint(target,amount=0){return (Number.isFinite(target)?target:amount)>=.5?0:1;}
export function courtyardOverviewView(view){return{...view,position:view.position.map((value,i)=>view.target[i]+(value-view.target[i])*.85),target:[...view.target]};}
export function courtyardLockView(THREE,door,lock,review){
  door.updateWorldMatrix(true,true);const target=lock.getWorldPosition(new THREE.Vector3());
  const normal=new THREE.Vector3(0,0,-1).applyQuaternion(door.getWorldQuaternion(new THREE.Quaternion()));
  const position=target.clone().addScaledVector(normal,.26).add(new THREE.Vector3(0,.13,0));
  const r=review.room,cx=r.centerX??0;position.x=THREE.MathUtils.clamp(position.x,cx-r.width/2+.08,cx+r.width/2-.08);position.z=THREE.MathUtils.clamp(position.z,-review.balcony.depth+.08,r.depth-.08);
  return{position:position.toArray(),target:target.toArray()};
}

export function batchCourtyardGeometry(THREE,world,excluded=[]){
  const protectedRoots=new Set(excluded),batches=new Map();world.updateMatrixWorld(true);
  function visit(o,protectedBranch=false){const protect=protectedBranch||protectedRoots.has(o)||o.userData.interactive||o.userData.curtainPanels||o.userData.ceilings||o.userData.cutaway||o.userData.glass;
    if(o.isMesh&&!protect&&!o.isInstancedMesh&&!Array.isArray(o.material)&&!o.material.transparent&&!o.geometry.morphAttributes.position&&!o.children.length){const key=[o.material.uuid,o.castShadow,o.receiveShadow,!!o.userData.noCollision,!!o.geometry.attributes.uv1,!!o.geometry.attributes.color].join('/');if(!batches.has(key))batches.set(key,[]);batches.get(key).push(o);}for(const child of o.children)visit(child,protect);
  }visit(world);let removed=0,created=0;const inverse=world.matrixWorld.clone().invert();
  for(const list of batches.values()){
    if(list.length<3)continue;const attrs={},indices=[];let offset=0;
    const names=['position','normal','uv',...(list[0].geometry.attributes.uv1?['uv1']:[]),...(list[0].geometry.attributes.color?['color']:[])];
    for(const name of names)attrs[name]=[];
    for(const o of list){const matrix=inverse.clone().multiply(o.matrixWorld),g=o.geometry.clone().applyMatrix4(matrix),p=g.attributes.position;
      for(const name of names){const attr=g.attributes[name],size=name==='uv'||name==='uv1'?2:3;for(let i=0;i<p.count;i++)for(let c=0;c<size;c++)attrs[name].push(attr?attr.array[i*attr.itemSize+c]:name==='color'?1:0);}
      const index=g.index,count=index?index.count:p.count,flip=matrix.determinant()<0;
      for(let i=0;i<count;i+=3){const a=index?index.getX(i):i,b=index?index.getX(i+1):i+1,c=index?index.getX(i+2):i+2;indices.push(offset+a,offset+(flip?c:b),offset+(flip?b:c));}offset+=p.count;g.dispose();o.removeFromParent();
    }
    const geometry=new THREE.BufferGeometry();for(const name of names)geometry.setAttribute(name,new THREE.Float32BufferAttribute(attrs[name],name==='uv'||name==='uv1'?2:3));geometry.setIndex(indices);geometry.computeBoundingBox();geometry.computeBoundingSphere();geometry.userData.authoring='Blender';
    const mesh=new THREE.Mesh(geometry,list[0].material);mesh.name=`C43_Static_Batch_${++created}`;mesh.castShadow=list[0].castShadow;mesh.receiveShadow=list[0].receiveShadow;mesh.userData={authoring:'Blender',noCollision:!!list[0].userData.noCollision,sourceCount:list.length};world.add(mesh);removed+=list.length-1;
  }world.updateMatrixWorld(true);return{removed,created};
}

export function createCourtyardNavigation(THREE,world,review,movingRoots=[]){
  const radius=.002,surfaces=[],dynamic=[],ray=new THREE.Raycaster(),dir=new THREE.Vector3(),segment=new THREE.Box3(),moving=new Set(movingRoots);
  world.updateMatrixWorld(true);
  function collect(o,isMoving=false){if(o.userData.noCollision||o.userData.curtainPanels)return;isMoving=isMoving||moving.has(o);if(o.isMesh&&!o.isInstancedMesh){o.geometry.computeBoundingBox();const record={object:o,bounds:o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld)};surfaces.push(record);if(isMoving)dynamic.push(record);}for(const c of o.children)collect(c,isMoving);}collect(world);
  function updateDynamic(){world.updateMatrixWorld(true);for(const item of dynamic)item.bounds.copy(item.object.geometry.boundingBox).applyMatrix4(item.object.matrixWorld);}
  function canTravel(from,to){const r=review.room,cx=r.centerX??0;if(to.x<=cx-r.width/2+radius||to.x>=cx+r.width/2-radius||to.z<=-review.balcony.depth+.025||to.z>=r.depth-radius||to.y<.025||to.y>r.height-.02)return false;dir.subVectors(to,from);const length=dir.length();if(length<1e-8)return true;dir.divideScalar(length);ray.set(from,dir);ray.near=0;ray.far=length+radius;segment.setFromPoints([from,to]);segment.expandByScalar(radius);return !surfaces.some(({object,bounds})=>segment.intersectsBox(bounds)&&ray.intersectObject(object,false).length);}
  return{canTravel,updateDynamic,radius,surfaces:surfaces.length,dynamicSurfaces:dynamic.length};
}

export function createCourtyardLighting(THREE,scene,renderer,materials){
  const studio=new THREE.Scene();studio.background=new THREE.Color('#b7c3ca');
  const enclosure=new THREE.Mesh(new THREE.BoxGeometry(12,9,12),new THREE.MeshBasicMaterial({color:'#d4d0c9',side:THREE.BackSide}));studio.add(enclosure);
  function panel(w,h,pos,target,strength){const mesh=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color('#fff9ef').multiplyScalar(strength),side:THREE.DoubleSide}));mesh.position.fromArray(pos);mesh.lookAt(...target);studio.add(mesh);}
  panel(5,3,[.2,1.7,-5.8],[0,1.2,0],2.8);panel(6,5,[0,4.4,0],[0,0,0],.85);panel(4,4,[-5.8,1,0],[0,1,0],.65);
  const pmrem=new THREE.PMREMGenerator(renderer),environment=pmrem.fromScene(studio,.04,.1,25);scene.environment=environment.texture;pmrem.dispose();studio.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
  const sky=new THREE.HemisphereLight('#fffaf2','#8b7261',.62);scene.add(sky);
  // Broad neutral daylight; compass direction and real season are unknown.
  const daylight=new THREE.DirectionalLight('#fff6e9',1.4);daylight.position.set(-.4,4.8,-4);daylight.target.position.set(.25,.4,1.3);daylight.castShadow=true;daylight.shadow.mapSize.set(2048,2048);Object.assign(daylight.shadow.camera,{left:-3.5,right:3.5,top:3.6,bottom:-3.4,near:.1,far:14});daylight.shadow.normalBias=.003;daylight.shadow.bias=-.00006;daylight.shadow.radius=4;daylight.shadow.camera.updateProjectionMatrix();scene.add(daylight,daylight.target);
  const windowFill=new THREE.PointLight('#fffaed',2.0,7,2);windowFill.position.set(.15,1.9,-.4);scene.add(windowFill);
  const bounce=new THREE.PointLight('#f4e7d8',.85,6,1);bounce.position.set(-.7,1.1,1.3);scene.add(bounce);
  const ceiling=new THREE.PointLight('#fff0da',0,6,2);ceiling.position.set(.1,2.45,1.5);scene.add(ceiling);
  const fixtureMaterials=materials.filter(m=>m.name?.includes('Downlight')||m.userData?.lightFixture),clothMaterials=materials.filter(m=>m.userData.curtainBacklight);
  for(const m of clothMaterials){m.emissive=new THREE.Color('#9e9c96');m.emissiveIntensity=.025;}
  function update(curtainOpen,lightOn){const a=Math.max(0,Math.min(1,curtainOpen));scene.environmentIntensity=.34+.09*a;sky.intensity=.83-.06*a;daylight.intensity=.24+1.35*a;windowFill.intensity=1.5+.9*a;bounce.intensity=1.16+.09*a;ceiling.intensity=lightOn?5:0;for(const m of fixtureMaterials)m.emissiveIntensity=lightOn?.7:.025;for(const m of clothMaterials)m.emissiveIntensity=.035*(1-a);renderer.shadowMap.needsUpdate=true;}
  update(0,false);return{update,daylight,dispose(){environment.dispose();}};
}

export function createCourtyardFinish(THREE,renderer,scene,camera){
  const target=new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,samples:Math.min(4,renderer.capabilities.maxSamples||0)});target.depthTexture=new THREE.DepthTexture(1,1,THREE.UnsignedIntType);
  const passScene=new THREE.Scene(),passCamera=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
  const material=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,uniforms:{source:{value:target.texture},depth:{value:target.depthTexture},inverseProjection:{value:camera.projectionMatrixInverse},projection:{value:camera.projectionMatrix},resolution:{value:new THREE.Vector2()},strength:{value:.35}},vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:`varying vec2 vUv;uniform sampler2D source,depth;uniform mat4 inverseProjection,projection;uniform vec2 resolution;uniform float strength;
  vec3 viewPosition(vec2 uv){vec4 p=inverseProjection*vec4(uv*2.-1.,texture2D(depth,uv).x*2.-1.,1.);return p.xyz/p.w;}
  void main(){vec3 color=texture2D(source,vUv).rgb;vec3 p=viewPosition(vUv);vec3 n=normalize(cross(dFdx(p),dFdy(p)));if(dot(n,-p)<0.)n=-n;float occ=0.;float radius=.12;vec2 size=min(vec2(projection[0][0],projection[1][1])*radius/max(.08,-p.z)*.5,vec2(20.)/resolution);
  for(int i=0;i<8;i++){float a=float(i)*2.399963;vec2 uv=clamp(vUv+vec2(cos(a),sin(a))*sqrt((float(i)+.5)/8.)*size,vec2(.001),vec2(.999));vec3 delta=viewPosition(uv)-p;float dist=length(delta);occ+=max(dot(n,delta/max(dist,.0001))-.12,0.)*(1.-smoothstep(.025,radius,dist));}
  float ao=1.-strength*occ/8.;color*=ao;gl_FragColor=vec4(color,1.);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
  }`});
  const quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2),material);passScene.add(quad);let frames=0;
  function resize(){const size=renderer.getDrawingBufferSize(new THREE.Vector2());target.setSize(size.x,size.y);material.uniforms.resolution.value.copy(size);}
  function render(){renderer.info.reset();renderer.setRenderTarget(target);renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.render(passScene,passCamera);frames++;}
  resize();return{render,resize,get frames(){return frames;},dispose(){target.dispose();material.dispose();quad.geometry.dispose();}};
}
