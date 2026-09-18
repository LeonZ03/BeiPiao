import {Reflector} from './vendor/Reflector.js';
// Bright early-afternoon ambience; retain the approved sun direction and patches.
export function createAfternoon({THREE,scene,renderer,world}){
  scene.background=new THREE.Color('#e5ebe5');
  renderer.toneMappingExposure=1.01;
  scene.environmentIntensity=.25;
  scene.fog=new THREE.Fog('#eee8d9',8,49);
  if(renderer.isWebGLRenderer){
    const studio=new THREE.Scene();studio.background=new THREE.Color('#d8d4c9');
    const enclosure=new THREE.Mesh(new THREE.BoxGeometry(12,9,12),new THREE.MeshBasicMaterial({color:'#cec8bb',side:THREE.BackSide}));studio.add(enclosure);
    function panel(w,h,x,y,z,color,intensity,rx=0,ry=0){const m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({color:new THREE.Color(color).multiplyScalar(intensity),side:THREE.DoubleSide}));m.position.set(x,y,z);m.rotation.set(rx,ry,0);studio.add(m);}
    panel(3.0,4.6,0,1,-5.5,'#fff0d8',4.0);
    panel(7,6,0,4.3,0,'#fffaf1',1.25,Math.PI/2);
    panel(4,4,-5.7,.5,0,'#f0f0e8',1.35,0,Math.PI/2);
    panel(4,3,5.7,0,0,'#ebd6be',.95,0,Math.PI/2);
    const generator=new THREE.PMREMGenerator(renderer),environment=generator.fromScene(studio,.025,.1,30);
    scene.environment=environment.texture;generator.dispose();
    studio.traverse(o=>{o.geometry?.dispose();o.material?.dispose();});
  }
  const sky=new THREE.HemisphereLight('#fff8e9','#e1c5a0',.41);scene.add(sky);
  const sun=new THREE.DirectionalLight('#ffe0a8',5.8);
  sun.name='warm-afternoon-sun';sun.position.set(2.7,5.8,-8);sun.target.position.set(.10,.10,1.0);sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-2.6,right:2.6,top:3.3,bottom:-3.1,near:.1,far:22});
  sun.shadow.bias=-.00008;sun.shadow.normalBias=.004;sun.shadow.radius=3;sun.shadow.camera.updateProjectionMatrix();scene.add(sun,sun.target);
  const windowLight=new THREE.PointLight('#fff4df',1.60,7,2);windowLight.position.set(.12,1.85,-1.38);scene.add(windowLight);
  const bounce=new THREE.PointLight('#ffe4b8',.65,7,1);bounce.position.set(-.35,.84,.75);scene.add(bounce);
  const ceilingBounce=new THREE.PointLight('#fff1de',.44,8,1);ceilingBounce.position.set(.7,2.22,1.45);scene.add(ceilingBounce);
  if(renderer.isWebGLRenderer){
    const shader={
      uniforms:{color:{value:new THREE.Color(0xffffff)},tDiffuse:{value:null},textureMatrix:{value:new THREE.Matrix4()}},
      vertexShader:`uniform mat4 textureMatrix;varying vec4 reflectedUv;varying vec3 floorPosition;
        #include <common>
        #include <logdepthbuf_pars_vertex>
        void main(){reflectedUv=textureMatrix*vec4(position,1.0);floorPosition=(modelMatrix*vec4(position,1.0)).xyz;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);
        #include <logdepthbuf_vertex>
        }`,
      fragmentShader:`uniform sampler2D tDiffuse;uniform vec3 color;varying vec4 reflectedUv;varying vec3 floorPosition;
        #include <logdepthbuf_pars_fragment>
        void main(){
          #include <logdepthbuf_fragment>
          if(floorPosition.z>1.80&&floorPosition.x<.25)discard;
          vec2 uv=reflectedUv.xy/reflectedUv.w;
          vec2 stepUv=vec2(.0021,.0021);
          vec3 reflected=texture2D(tDiffuse,uv).rgb*.28;
          reflected+=(texture2D(tDiffuse,uv+vec2(stepUv.x,0.)).rgb+texture2D(tDiffuse,uv-vec2(stepUv.x,0.)).rgb+texture2D(tDiffuse,uv+vec2(0.,stepUv.y)).rgb+texture2D(tDiffuse,uv-vec2(0.,stepUv.y)).rgb)*.12;
          reflected+=(texture2D(tDiffuse,uv+stepUv).rgb+texture2D(tDiffuse,uv-stepUv).rgb+texture2D(tDiffuse,uv+vec2(stepUv.x,-stepUv.y)).rgb+texture2D(tDiffuse,uv+vec2(-stepUv.x,stepUv.y)).rgb)*.06;
          float grazing=1.-clamp(normalize(cameraPosition-floorPosition).y,0.,1.);
          // Same uninterrupted grid and 1.4 mm joints as the Blender ceramic.
          // Screen-space filtering keeps the fine grout stable when walking.
          vec2 cell=fract((floorPosition.xz+vec2(1.4,1.8))/.6);
          vec2 toJoint=min(cell,1.-cell)*.6;
          float jointDistance=min(toJoint.x,toJoint.y);
          float aa=max(fwidth(jointDistance)*.5,.00005);
          float joint=smoothstep(.0007-aa,.0007+aa,jointDistance);
          gl_FragColor=vec4(reflected*color,(.075+.15*pow(grazing,3.))*joint);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`
    };
    const reflection=new Reflector(new THREE.PlaneGeometry(2.8,4.98),{textureWidth:512,textureHeight:512,multisample:0,clipBias:.002,color:0xffffff,shader});
    reflection.name='polished-ceramic-floor-reflection';reflection.rotation.x=-Math.PI/2;reflection.position.set(0,.013,.69);reflection.material.transparent=true;reflection.material.depthWrite=false;reflection.renderOrder=1;world.add(reflection);
    const renderReflection=reflection.onBeforeRender,lastCamera=new THREE.Matrix4();let lastTime=-Infinity,lastLighting=-1;
    reflection.onBeforeRender=function(renderer,scene,camera,...args){
      const now=performance.now(),lighting=Math.round(scene.children.filter(o=>o.isLight).reduce((v,o)=>v+o.intensity,0)*1000);
      const changed=!lastCamera.equals(camera.matrixWorld)||lighting!==lastLighting||world.userData.waterActive;
      if(!changed||now-lastTime<33)return;
      lastTime=now;lastCamera.copy(camera.matrixWorld);lastLighting=lighting;renderReflection.call(this,renderer,scene,camera,...args);
    };
  }
  // Subtle contact shadows complement the directional shadows without black corners.
  const c=document.createElement('canvas');c.width=c.height=128;const ctx=c.getContext('2d');
  const gradient=ctx.createRadialGradient(64,64,4,64,64,62);gradient.addColorStop(0,'rgba(49,39,29,.22)');gradient.addColorStop(.55,'rgba(49,39,29,.10)');gradient.addColorStop(1,'rgba(49,39,29,0)');ctx.fillStyle=gradient;ctx.fillRect(0,0,128,128);
  const tex=new THREE.CanvasTexture(c);
  for(const [x,z,w,d]of [[-.60,.64,1.8,2.37],[.48,-.99,.78,.77],[1.04,-.76,.8,1.3],[-1.1,-1.135,.85,1.4]]){
    const shadow=new THREE.Mesh(new THREE.PlaneGeometry(w,d),new THREE.MeshBasicMaterial({map:tex,transparent:true,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2}));shadow.rotation.x=-Math.PI/2;shadow.position.set(x,.014,z);shadow.renderOrder=2;world.add(shadow);
  }
  // Closed curtains convert direct summer sun into a smaller, warm diffuse source.
  // At a=1 every value is exactly the previously approved open-curtain lighting.
  const openSky=new THREE.Color('#fff8e9'),closedSky=new THREE.Color('#f5d8c7');
  const openGround=new THREE.Color('#e1c5a0'),closedGround=new THREE.Color('#aa7965');
  const openWindow=new THREE.Color('#fff4df'),closedWindow=new THREE.Color('#fff4e9');
  const openBounce=new THREE.Color('#ffe4b8'),closedBounce=new THREE.Color('#f2b29a');
  function setCurtainLight(openness){
    const a=Math.max(0,Math.min(1,openness));
    renderer.toneMappingExposure=1.03-.02*a;
    scene.environmentIntensity=.09+.16*a;
    sky.intensity=.16+.25*a;sky.color.copy(closedSky).lerp(openSky,a);sky.groundColor.copy(closedGround).lerp(openGround,a);
    windowLight.intensity=1.75-.15*a;windowLight.color.copy(closedWindow).lerp(openWindow,a);
    // The diffuse source is behind the shut cloth, avoiding a bright point-light
    // hotspot on its room-facing surface. Restore the approved open position.
    windowLight.position.set(.12,1.60+.25*a,-1.91+.53*a);
    bounce.intensity=.37+.28*a;bounce.color.copy(closedBounce).lerp(openBounce,a);
    ceilingBounce.intensity=.13+.31*a;
    sun.intensity=.045+5.755*a;
  }
  return {windowLight,sun,setCurtainLight};
}
