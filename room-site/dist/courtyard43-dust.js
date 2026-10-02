// Sparse indoor motes near the north window. Position and slow drift stay on
// the GPU; ordinary room depth keeps them behind furniture and walls.
export function createCourtyardDust(THREE, scene, anchor = new THREE.Vector3()) {
  const count = 192;
  const positions = new Float32Array(count * 3);
  const seeds = new Float32Array(count);
  let seed = 0x43d057;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = 0; i < count; i++) {
    // Bounded room air, with clearance from the bed, wardrobe, desk/counter.
    // This is a volume with parallax, not a sheet fixed to the curtain.
    let x,y,z;
    do { x=-1.82+random()*3.10; y=.84+random()*1.54; z=.30+random()*2.20; }
    while ((z>1.25 && x<.48 && y<.92) || (z<.72 && x<-.65 && y<.94) || (z<.45 && x>.20 && y<1.13));
    positions[i*3]=x; positions[i*3+1]=y; positions[i*3+2]=z;
    seeds[i] = random();
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
  const material = new THREE.ShaderMaterial({
    transparent: true, depthTest: true, depthWrite: false, toneMapped: false,
    uniforms: { uTime: { value: 0 }, uPixelRatio: { value: 1 }, uCurtainOpen: { value: 0 }, uLeft: { value: 0 }, uRight: { value: 0 }, uLight: { value: 0 }, uHeight: { value: 720 } },
    vertexShader: `attribute float aSeed; uniform float uTime,uPixelRatio,uHeight,uLeft,uRight,uLight; varying float vAlpha;
      void main(){ vec3 p=position; float phase=aSeed*6.2831853;
        p.x+=sin(uTime*.31+phase)*.038+sin(uTime*.11+phase*.61)*.018;
        p.y+=sin(uTime*.29+phase)*.034+cos(uTime*.13+phase*.73)*.018;
        p.z+=sin(uTime*.23+phase*.83)*.030;
        vec4 mv=modelViewMatrix*vec4(p,1.0); gl_Position=projectionMatrix*mv;
        // Preserve a small readable core at normal viewing distances. The old
        // subpixel soft edge erased most of the already faint particle alpha.
        float diameter=.0030+aSeed*.0020;
        gl_PointSize=clamp(diameter*uHeight*projectionMatrix[1][1]*.5/max(.30,-mv.z),1.6*uPixelRatio,3.1*uPixelRatio);
        float side=mix(uLeft,uRight,smoothstep(-.1,.9,p.x));
        float windowLight=exp(-p.z*.38)*(.10+.90*side);
        vAlpha=(.44+aSeed*.34)*(windowLight+uLight*.21)*smoothstep(.10,.45,-mv.z);
      }`,
    fragmentShader: `varying float vAlpha;
      void main(){ float r=length(gl_PointCoord-.5); if(r>.5) discard;
        float edge=1.0-smoothstep(.18,.5,r);
        gl_FragColor=vec4(.84,.82,.77,edge*vAlpha);
      }`
  });
  const points = new THREE.Points(geometry, material);
  points.name = 'C43_Indoor_Dust';
  points.frustumCulled = false;
  points.visible = false;
  scene.add(points);
  let active = false, elapsed = 0, disposed = false;
  return {
    count,
    setEnabled(value) { active = !!value && !disposed; points.visible = active; },
    update(dt, pixelRatio = 1, curtainOpen = 0, height = 720, sides = {left:curtainOpen,right:curtainOpen}, lightOn = false) {
      if (!active || disposed) return false;
      elapsed += Math.min(Math.max(dt, 0), .05);
      material.uniforms.uTime.value = elapsed;
      material.uniforms.uPixelRatio.value = pixelRatio;
      material.uniforms.uCurtainOpen.value = THREE.MathUtils.clamp(curtainOpen, 0, 1);
      material.uniforms.uHeight.value = height;
      material.uniforms.uLeft.value = sides.left;
      material.uniforms.uRight.value = sides.right;
      material.uniforms.uLight.value = lightOn?1:0;
      return true;
    },
    dispose() { if (disposed) return; disposed = true; active = false; scene.remove(points); geometry.dispose(); material.dispose(); },
    get active() { return active && !disposed; },
    get elapsed() { return elapsed; }
  };
}

export function courtyardDustShouldRun({ active, overview, reducedMotion, cameraPosition, forward }) {
  return !!active && !overview && !reducedMotion && !!cameraPosition && !!forward &&
    cameraPosition.z > -.2 && cameraPosition.z < 3.0;
}
