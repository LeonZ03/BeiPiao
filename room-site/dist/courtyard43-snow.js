// Courtyard43-only exterior snowfall. Particle positions are generated once;
// the vertex shader advances them without touching room geometry on the CPU.
export function createCourtyardSnow(THREE, scene, { count = 360 } = {}) {
  const amount = Math.max(250, Math.min(450, Math.round(count)));
  const positions = new Float32Array(amount * 3);
  const seeds = new Float32Array(amount);
  // Fixed, reproducible distribution outside the balcony plane (z < -1.3).
  let seed = 0x43a10;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = 0; i < amount; i++) {
    positions[i * 3] = (random() - .5) * 22;
    positions[i * 3 + 1] = .42 + random() * 6.2;
    positions[i * 3 + 2] = -1.46 - random() * 21;
    seeds[i] = random();
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
  const material = new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, toneMapped: false,
    uniforms: { uTime: { value: 0 }, uPixelRatio: { value: 1 } },
    vertexShader: `attribute float aSeed; uniform float uTime, uPixelRatio; varying float vAlpha;
      void main(){ vec3 p=position; float phase=aSeed*6.2831853;
        p.y=mod(p.y-0.42-uTime*(0.28+aSeed*0.22),6.2)+0.42;
        p.x+=sin(uTime*0.42+phase)*0.20 + sin(uTime*0.07+phase)*0.35;
        p.z+=cos(uTime*0.31+phase)*0.12;
        vec4 mv=modelViewMatrix*vec4(p,1.0); gl_Position=projectionMatrix*mv;
        gl_PointSize=clamp((1.1+aSeed*1.5)*uPixelRatio*(3.8/max(1.0,-mv.z)),1.0,3.2);
        vAlpha=(0.28+aSeed*0.38)*smoothstep(0.42,0.95,p.y)*(1.0-smoothstep(6.0,6.62,p.y));
      }`,
    fragmentShader: `varying float vAlpha; void main(){ vec2 p=gl_PointCoord-0.5;
      float r=length(p); if(r>0.5) discard; gl_FragColor=vec4(0.82,0.90,0.96,vAlpha*(1.0-smoothstep(0.20,0.5,r))); }`
  });
  const points = new THREE.Points(geometry, material);
  points.name = 'C43_ZWinter_Snow';
  points.frustumCulled = false;
  points.renderOrder = 20;
  points.visible = false;
  points.userData.exteriorOnly = true;
  scene.add(points);
  let enabled = false, elapsed = 0, disposed = false;
  return {
    count: amount,
    setEnabled(value) { enabled = !!value && !disposed; points.visible = enabled; },
    update(dt, pixelRatio = 1) {
      if (!enabled || disposed) return false;
      elapsed += Math.min(Math.max(dt, 0), .05);
      material.uniforms.uTime.value = elapsed;
      material.uniforms.uPixelRatio.value = pixelRatio;
      return true;
    },
    dispose() { if (disposed) return; disposed = true; enabled = false; scene.remove(points); geometry.dispose(); material.dispose(); },
    get active() { return enabled && !disposed; }
  };
}

export function courtyardSnowShouldRun({ active, overview, reducedMotion, cameraPosition, forward }) {
  if (!active || overview || reducedMotion || !cameraPosition || !forward) return false;
  // The authored snowfall volume starts beyond the balcony edge; keep the
  // indoor renderer idle unless the visitor is at that edge and facing out.
  return cameraPosition.z < -0.55 && forward.z < -0.24;
}
