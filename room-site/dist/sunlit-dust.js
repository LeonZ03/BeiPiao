// A tiny particle pass over the cached room image. Idle motes never re-render the
// expensive room geometry; both room depth and sun shadows occlude them.
export function createSunlitDust(THREE,renderer,camera,uniforms){
  const target=new THREE.WebGLRenderTarget(1,1,{type:THREE.HalfFloatType,depthBuffer:false});
  const scene=new THREE.Scene(),positions=[],seeds=[],direction=uniforms.sunDirection.value;
  const rand=i=>{const n=Math.sin(i*127.1+311.7)*43758.5453;return n-Math.floor(n);};
  for(let i=0;i<170;i++){
    const p=new THREE.Vector3(-.62+rand(i*5)*1.55,1.10+rand(i*5+1)*1.09,-1.80).addScaledVector(direction,-(.12+rand(i*5+2)*2.75));
    if(p.y<.15||p.x< -1.30||p.x>1.30)continue;positions.push(...p.toArray());seeds.push(rand(i*5+3));
  }
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('seed',new THREE.Float32BufferAttribute(seeds,1));geometry.computeBoundingBox();geometry.boundingBox.expandByScalar(.03);
  const u={...uniforms,time:{value:0}};
  const material=new THREE.ShaderMaterial({uniforms:u,transparent:true,blending:THREE.AdditiveBlending,depthTest:false,depthWrite:false,toneMapped:false,
    vertexShader:`attribute float seed;uniform float time;uniform vec2 resolution;uniform mat4 sunMatrix;varying vec4 vSun;varying vec3 vWorld;varying float vAlpha;
    void main(){vec3 p=position;float a=time*.19+seed*53.;p+=vec3(sin(a)*.018,cos(a*.73)*.024,sin(a*.61)*.013);
      vec4 view=modelViewMatrix*vec4(p,1.);gl_Position=projectionMatrix*view;
      gl_PointSize=clamp((.0011+seed*.0007)*resolution.y*projectionMatrix[1][1]/max(.1,-view.z),.65,2.6);
      vWorld=p;vSun=sunMatrix*vec4(p,1.);vAlpha=(.11+seed*.16)*smoothstep(.09,.25,-view.z);}`,
    fragmentShader:`uniform sampler2D depth,sunMap;uniform vec2 resolution;uniform vec3 sunDirection;uniform float sunPower;varying vec4 vSun;varying vec3 vWorld;varying float vAlpha;
    #include <packing>
    void main(){if(gl_FragCoord.z>texture2D(depth,gl_FragCoord.xy/resolution).x+.000001)discard;
      vec3 s=vSun.xyz/vSun.w;if(s.x<0.||s.x>1.||s.y<0.||s.y>1.||s.z>1.)discard;
      float visible=step(s.z-.00008,unpackRGBAToDepth(texture2D(sunMap,s.xy)));
      float t=(-1.81-vWorld.z)/sunDirection.z;vec3 w=vWorld+sunDirection*t;
      float aperture=smoothstep(-.73,-.63,w.x)*(1.-smoothstep(.92,1.02,w.x))*smoothstep(.72,.82,w.y)*(1.-smoothstep(2.17,2.29,w.y));
      float soft=1.-smoothstep(.02,.50,length(gl_PointCoord-.5));float alpha=soft*visible*aperture*vAlpha*clamp((sunPower-1.)/4.8,0.,1.);
      if(alpha<.003)discard;gl_FragColor=vec4(1.,.85,.62,alpha);}`});
  const motes=new THREE.Points(geometry,material);motes.frustumCulled=false;scene.add(motes);
  const clear=new THREE.Color(),frustum=new THREE.Frustum(),viewProjection=new THREE.Matrix4();let previous=-1;
  function draw(time,enabled){
    u.time.value=time;frustum.setFromProjectionMatrix(viewProjection.multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse));motes.visible=enabled&&frustum.intersectsBox(geometry.boundingBox);const alpha=renderer.getClearAlpha();renderer.getClearColor(clear);renderer.setClearColor(0,0);
    renderer.setRenderTarget(target);renderer.render(scene,camera);renderer.setClearColor(clear,alpha);previous=time;
  }
  return {texture:target.texture,draw,resize:(w,h)=>target.setSize(w,h),get last(){return previous;},get visible(){return motes.visible;},count:seeds.length};
}
