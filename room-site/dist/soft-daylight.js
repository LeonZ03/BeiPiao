import {createSunlitDust} from './sunlit-dust.js?v=breeze27';
// A small, on-demand HDR pipeline: contact shading, restrained highlight bloom,
// and filmic output. The room is rendered once; bloom runs at quarter resolution.
export function installSoftSunShadows(THREE){
  const chunk=THREE.ShaderChunk.shadowmap_pars_fragment;
  const start=chunk.indexOf('#if defined( SHADOWMAP_TYPE_PCF )');
  const end=chunk.indexOf('#elif defined( SHADOWMAP_TYPE_PCF_SOFT )',start);
  if(start<0||end<0)throw new Error('Unsupported shadow shader');
  const disk=Array.from({length:16},(_,i)=>{const a=i*2.39996323,r=Math.sqrt((i+.5)/16);return `vec2(${(Math.cos(a)*r).toFixed(6)},${(Math.sin(a)*r).toFixed(6)})`;});
  // Penumbra grows with blocker distance; nearby contact stays precise. A fixed
  // disk avoids the swimming grain of a per-frame random shadow filter.
  const search=disk.filter((_,i)=>i%2===0).map(v=>`{float d=unpackRGBAToDepth(texture2D(shadowMap,shadowCoord.xy+${v}*searchRadius));if(d<shadowCoord.z-.00015){blocker+=d;count+=1.;}}`).join('\n');
  const filter=disk.map(v=>`texture2DCompare(shadowMap,shadowCoord.xy+${v}*penumbra,shadowCoord.z)`).join('+');
  THREE.ShaderChunk.shadowmap_pars_fragment=chunk.slice(0,start)+`#if defined( SHADOWMAP_TYPE_PCF )
    vec2 texelSize=1./shadowMapSize;
    vec2 searchRadius=texelSize*18.;float blocker=0.;float count=0.;
    ${search}
    float gap=count>0.?max(0.,shadowCoord.z-blocker/count):0.;
    vec2 penumbra=texelSize*clamp(1.3+gap*230.,1.3,15.);
    shadow=(${filter})/16.;
  `+chunk.slice(end);
}

export function createSoftDaylight({THREE,renderer,scene,camera,sun,breeze}){
  if(!renderer.isWebGLRenderer)return {render:()=>renderer.render(scene,camera),resize:()=>{},setCurtain:()=>{}};
  renderer.info.autoReset=false;
  const target=new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,samples:4});
  target.depthTexture=new THREE.DepthTexture(1,1,THREE.UnsignedIntType);
  const bloomA=new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,depthBuffer:false});
  const bloomB=bloomA.clone(),volume=bloomA.clone();
  const screen=new THREE.Scene(),screenCamera=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
  const vertex=`varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}`;
  const quad=new THREE.Mesh(new THREE.PlaneGeometry(2,2),new THREE.MeshBasicMaterial());screen.add(quad);
  // Rasterize the HDR sun with scene geometry so leaves and window frames
  // occlude its coverage before the cached color and depth are composited.
  const solarDirection=sun.position.clone().sub(sun.target.position).normalize();
  const solarDistance=camera.far*.75;
  const solarDisc=new THREE.Mesh(new THREE.CircleGeometry(solarDistance*.00465,48),new THREE.MeshBasicMaterial({color:new THREE.Color(8,7.76,7.12),toneMapped:false,fog:false}));
  solarDisc.name='distant-solar-disc';solarDisc.frustumCulled=false;
  solarDisc.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1),solarDirection.clone().negate());
  solarDisc.onBeforeRender=(_renderer,_scene,viewCamera)=>{
    // Camera-relative distance is only a numerical device: direction and
    // apparent size stay fixed, including reflected views. It emits no light.
    solarDisc.position.copy(viewCamera.getWorldPosition(new THREE.Vector3())).addScaledVector(solarDirection,solarDistance);
    solarDisc.updateMatrixWorld(true);
  };
  scene.add(solarDisc);
  // Keep an HDR/depth image of the stationary room. While the camera is idle,
  // redraw only the Blender foliage/cloth/flowers over it (layer 1). No CPU
  // instance uploads, full-room shading or shadow-map updates for a breeze frame.
  let base=null,baseReady=false,lastAmbient=-1,overlays=[];
  const statistics={fullFrames:0,ambientFrames:0,cacheBuilds:0};
  const restoreBase=new THREE.ShaderMaterial({depthTest:true,depthWrite:true,depthFunc:THREE.AlwaysDepth,toneMapped:false,
    uniforms:{source:{value:null},depth:{value:null}},vertexShader:vertex,
    fragmentShader:`varying vec2 vUv;uniform sampler2D source,depth;
      void main(){gl_FragColor=texture2D(source,vUv);gl_FragDepth=texture2D(depth,vUv).r;}`});
  function prepareBase(){
    if(baseReady)return;
    if(!base){base=new THREE.WebGLRenderTarget(target.width,target.height,{type:THREE.HalfFloatType,samples:4});base.depthTexture=new THREE.DepthTexture(target.width,target.height,THREE.UnsignedIntType);}
    // Transparent glass must be composited AFTER moving foliage. Baking its
    // depth into the static image would hide every leaf behind the window.
    overlays=[];scene.traverse(o=>{if(o.isMesh&&(Array.isArray(o.material)?o.material:[o.material]).some(m=>m.transparent)&&!breeze.objects.includes(o))overlays.push(o);});
    const moving=[...breeze.movingObjects,...overlays],masks=moving.map(o=>o.layers.mask),shadow=renderer.shadowMap.needsUpdate;
    const reflectionRoots=[];scene.traverse(o=>{if(o.userData&&o.userData.geometryRevision!==undefined){reflectionRoots.push([o,o.userData.staticCacheCapture]);o.userData.staticCacheCapture=true;}});
    try{
      scene.traverse(o=>{if(o.isLight)o.layers.enable(1);});
      moving.forEach(o=>o.layers.disable(0));renderer.shadowMap.needsUpdate=false;
      renderer.setRenderTarget(base);renderer.render(scene,camera);
      baseReady=true;statistics.cacheBuilds++;
    }finally{moving.forEach((o,i)=>o.layers.mask=masks[i]);overlays.forEach(o=>o.layers.enable(1));renderer.shadowMap.needsUpdate=shadow;reflectionRoots.forEach(([o,value])=>o.userData.staticCacheCapture=value);}
  }
  function renderMovingObjects(){
    prepareBase();
    restoreBase.uniforms.source.value=base.texture;restoreBase.uniforms.depth.value=base.depthTexture;
    quad.material=restoreBase;renderer.setRenderTarget(target);renderer.render(screen,screenCamera);
    const mask=camera.layers.mask,background=scene.background,clear=renderer.autoClear,shadow=renderer.shadowMap.needsUpdate;
    try{
      renderer.autoClear=false;renderer.shadowMap.needsUpdate=false;scene.background=null;camera.layers.set(1);
      renderer.render(scene,camera);
    }finally{camera.layers.mask=mask;scene.background=background;renderer.autoClear=clear;renderer.shadowMap.needsUpdate=shadow;}
    statistics.ambientFrames++;
  }
  const blur=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,
    uniforms:{source:{value:null},stepUV:{value:new THREE.Vector2()},extract:{value:1}},vertexShader:vertex,
    fragmentShader:`varying vec2 vUv;uniform sampler2D source;uniform vec2 stepUV;uniform float extract;
    vec3 sampleLight(vec2 uv){vec3 c=texture2D(source,uv).rgb;float l=max(c.r,max(c.g,c.b));return c*mix(1.,smoothstep(.85,2.8,l),extract);}
    void main(){vec3 c=sampleLight(vUv)*.227027;c+=(sampleLight(vUv+stepUV*1.384615)+sampleLight(vUv-stepUV*1.384615))*.316216;c+=(sampleLight(vUv+stepUV*3.230769)+sampleLight(vUv-stepUV*3.230769))*.070270;gl_FragColor=vec4(c,1.);}`});
  const finish=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,
    uniforms:{source:{value:target.texture},bloom:{value:bloomB.texture},volume:{value:volume.texture},depth:{value:target.depthTexture},inverseProjection:{value:camera.projectionMatrixInverse},projection:{value:camera.projectionMatrix},cameraWorld:{value:camera.matrixWorld},sunMap:{value:null},sunMatrix:{value:sun.shadow.matrix},sunDirection:{value:sun.position.clone().sub(sun.target.position).normalize()},sunPower:{value:0},resolution:{value:new THREE.Vector2()},volumePixel:{value:new THREE.Vector2()},contactStrength:{value:.28}},vertexShader:vertex,
    fragmentShader:`varying vec2 vUv;uniform sampler2D source,bloom,depth,volume,dust;uniform mat4 inverseProjection,projection,cameraWorld;uniform vec2 resolution,volumePixel;uniform vec3 sunDirection;uniform float contactStrength;
    vec3 viewPosition(vec2 uv){float d=texture2D(depth,uv).x;vec4 p=inverseProjection*vec4(uv*2.-1.,d*2.-1.,1.);return p.xyz/p.w;}
    void main(){
      vec3 color=texture2D(source,vUv).rgb;vec3 p=viewPosition(vUv);
      vec3 skyRay=normalize(mat3(cameraWorld)*normalize(p));
      float skyVisible=step(.9999999,texture2D(depth,vUv).x);
      vec3 summerSky=mix(vec3(.76,.83,.84),vec3(.30,.48,.66),smoothstep(.03,.85,skyRay.y));
      float skyRadiance=max(color.r,max(color.g,color.b));
      // Grade the sky BEFORE adding bloom/air. Preserve HDR solar coverage:
      // far-depth rounding must not classify the luminous disc as background.
      color=mix(color,summerSky,skyVisible*(1.-smoothstep(1.,2.,skyRadiance)));
      vec3 normal=normalize(cross(dFdx(p),dFdy(p)));if(dot(normal,-p)<0.)normal=-normal;
      float occ=0.;float radius=.15;vec2 size=vec2(projection[0][0],projection[1][1])*radius/max(.08,-p.z)*.5;
      size=min(size,vec2(22.)/resolution);
      for(int i=0;i<8;i++){float a=float(i)*2.399963;vec2 offset=vec2(cos(a),sin(a))*sqrt((float(i)+.5)/8.)*size;vec3 delta=viewPosition(vUv+offset)-p;float distance=length(delta);
        occ+=max(dot(normal,delta/max(distance,.0001))-.12,0.)*(1.-smoothstep(.025,radius,distance));}
      float ao=1.-contactStrength*occ/8.;color*=vec3(ao,mix(1.,ao,.93),mix(1.,ao,.84));
      color+=texture2D(bloom,vUv).rgb*.11;
      vec3 air=texture2D(volume,vUv).rgb*.28;
      air+=(texture2D(volume,vUv+volumePixel).rgb+texture2D(volume,vUv-volumePixel).rgb+texture2D(volume,vUv+vec2(volumePixel.x,-volumePixel.y)).rgb+texture2D(volume,vUv+vec2(-volumePixel.x,volumePixel.y)).rgb)*.18;
      // Keep the approved shafts against indoor surfaces. A shallow outward
      // sightline through the bay window must not put the full indoor haze
      // over the courtyard; this mask affects neither sun nor room exposure.
      float surfaceZ=(cameraWorld*vec4(p,1.)).z;
      float airVisibility=mix(.18,1.,smoothstep(-2.15,-1.80,surfaceZ));
      color+=air*airVisibility+texture2D(dust,vUv).rgb;
      // A soft optical aureole makes the physical 0.53-degree disc legible.
      // It stays on sky depth; it cannot float in front of leaves or walls.
      float separation=length(skyRay-sunDirection);
      float solarHalo=1.2*exp(-pow(separation/.018,2.))+.12*exp(-pow(separation/.055,2.));
      color+=vec3(1.,.96,.86)*solarHalo*skyVisible;
      // Keep shadows neutral and lift only warm highlights, without a yellow veil.
      color*=vec3(1.025,1.008,.985);
      gl_FragColor=vec4(color,1.);
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }`});
  finish.uniforms.closedCurtain={value:0};
  finish.fragmentShader=finish.fragmentShader.replace('uniform float contactStrength;', 'uniform float contactStrength,closedCurtain;').replace('#include <colorspace_fragment>',`#include <colorspace_fragment>
      // Photo-matched warm film response only for the closed-curtain state.
      // Keep luminous ivory highlights neutral; lift darks towards soft brown.
      float luma=dot(gl_FragColor.rgb,vec3(.2126,.7152,.0722));
      vec3 warm=gl_FragColor.rgb*vec3(1.075,.968,.93);
      warm+=vec3(.033,.017,.012)*(1.-smoothstep(.18,.82,luma));
      warm=mix(warm,gl_FragColor.rgb,smoothstep(.72,.98,luma)*.65);
      gl_FragColor.rgb=mix(gl_FragColor.rgb,warm,closedCurtain);
  `);
  const air=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms:finish.uniforms,vertexShader:vertex,
    fragmentShader:`varying vec2 vUv;uniform sampler2D depth,sunMap;uniform mat4 inverseProjection,cameraWorld,sunMatrix;uniform vec3 sunDirection;uniform float sunPower;
    #include <packing>
    void main(){vec4 v=inverseProjection*vec4(vUv*2.-1.,texture2D(depth,vUv).x*2.-1.,1.);vec3 p=v.xyz/v.w;
      vec3 origin=cameraWorld[3].xyz,ray=mat3(cameraWorld)*normalize(p);float len=min(length(p),4.5),scatter=0.;
      float jitter=fract(52.9829189*fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))));
      for(int j=0;j<32;j++){vec3 q=origin+ray*((float(j)+jitter)/32.*len);float t=(-1.81-q.z)/sunDirection.z;vec3 w=q+sunDirection*t;
        float aperture=smoothstep(-.75,-.63,w.x)*(1.-smoothstep(.90,1.02,w.x))*smoothstep(.70,.82,w.y)*(1.-smoothstep(2.17,2.29,w.y));
        if(t>0.&&q.z<1.80&&q.z> -1.78&&q.y>.03&&q.y<2.64&&abs(q.x)<1.39){vec4 s=sunMatrix*vec4(q,1.);s.xyz/=s.w;float d=unpackRGBAToDepth(texture2D(sunMap,s.xy));scatter+=aperture*step(s.z-.0001,d);}}
      float phase=.82+.28*pow(max(0.,dot(ray,sunDirection)),3.);
      // Preserve readable sun shafts against the brighter floor19 daylight.
      // This only affects sunlit, shadow-tested air, not room exposure or dust.
      gl_FragColor=vec4(vec3(1.,.81,.55)*scatter/32.*len*sunPower*.042*phase,1.);
    }`});
  const dust=createSunlitDust(THREE,renderer,camera,finish.uniforms);finish.uniforms.dust={value:dust.texture};
  const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
  function resize(){const size=renderer.getDrawingBufferSize(new THREE.Vector2());target.setSize(size.x,size.y);base?.setSize(size.x,size.y);baseReady=false;dust.resize(size.x,size.y);bloomA.setSize(Math.max(1,Math.ceil(size.x/4)),Math.max(1,Math.ceil(size.y/4)));bloomB.setSize(bloomA.width,bloomA.height);volume.setSize(bloomA.width,bloomA.height);finish.uniforms.resolution.value.copy(size);finish.uniforms.volumePixel.value.set(1.5/volume.width,1.5/volume.height);}
  function composite(time,enabled){dust.draw(reducedMotion.matches?0:time,enabled);quad.material=finish;renderer.setRenderTarget(null);renderer.render(screen,screenCamera);}
  function animate(time,enabled,motionChanged=false){
    if(reducedMotion.matches)return;
    const moving=motionChanged&&breeze?.active;
    if(!moving&&(!enabled||!dust.visible||time-lastAmbient<1/24))return;
    renderer.info.reset();if(moving)renderMovingObjects();composite(time,enabled);lastAmbient=time;
  }
  function render(time=0,dustEnabled=true){
    baseReady=false;statistics.fullFrames++;
    renderer.info.reset();
    renderer.setRenderTarget(target);renderer.render(scene,camera);
    finish.uniforms.sunMap.value=sun.shadow.map.texture;finish.uniforms.sunPower.value=sun.intensity;
    quad.material=air;renderer.setRenderTarget(volume);renderer.render(screen,screenCamera);
    quad.material=blur;blur.uniforms.source.value=target.texture;blur.uniforms.extract.value=1;blur.uniforms.stepUV.value.set(1.65/bloomA.width,0);renderer.setRenderTarget(bloomA);renderer.render(screen,screenCamera);
    blur.uniforms.source.value=bloomA.texture;blur.uniforms.extract.value=0;blur.uniforms.stepUV.value.set(0,1.65/bloomA.height);renderer.setRenderTarget(bloomB);renderer.render(screen,screenCamera);
    composite(time,dustEnabled);
  }
  resize();return {render,resize,animate,statistics,setCurtain:openness=>finish.uniforms.closedCurtain.value=1-Math.max(0,Math.min(1,openness))};
}
