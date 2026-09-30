// Courtyard43-only exterior snowfall. Particle positions are generated once;
// the vertex shader advances them without touching room geometry on the CPU.
export function createCourtyardSnow(THREE, scene, { count = 900 } = {}) {
  const amount = Math.max(500, Math.min(1200, Math.round(count)));
  const positions = new Float32Array(amount * 3);
  const seeds = new Float32Array(amount);
  // Fixed, reproducible distribution outside the balcony plane (z < -1.3).
  let seed = 0x43a10;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  for (let i = 0; i < amount; i++) {
    const near = i < amount * .7;
    positions[i * 3] = (random() - .5) * (near ? 14 : 26);
    positions[i * 3 + 1] = -.45 + random() * 7.0;
    positions[i * 3 + 2] = near ? -1.46 - random() * 8 : -9.46 - random() * 15;
    seeds[i] = random();
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aSeed', new THREE.BufferAttribute(seeds, 1));
  const material = new THREE.ShaderMaterial({
    transparent: true, depthTest: true, depthWrite: false, toneMapped: false,
    uniforms: { uTime: { value: 0 }, uPixelRatio: { value: 1 } },
    vertexShader: `attribute float aSeed; uniform float uTime, uPixelRatio; varying float vAlpha;
      void main(){ vec3 p=position; float phase=aSeed*6.2831853;
        p.y=mod(p.y+0.45-uTime*(0.38+aSeed*0.32),7.0)-0.45;
        p.x+=sin(uTime*0.42+phase)*0.20 + sin(uTime*0.07+phase)*0.35;
        p.z+=cos(uTime*0.31+phase)*0.12;
        vec4 mv=modelViewMatrix*vec4(p,1.0); gl_Position=projectionMatrix*mv;
        gl_PointSize=clamp((2.0+aSeed*2.0)*uPixelRatio*(7.0/max(3.0,-mv.z)),1.1,5.3);
        vAlpha=(0.6+aSeed*0.3)*smoothstep(-0.45,-0.08,p.y)*(1.0-smoothstep(6.0,6.55,p.y));
      }`,
    fragmentShader: `varying float vAlpha; void main(){ vec2 p=gl_PointCoord-0.5;
      float r=length(p); if(r>0.5) discard; gl_FragColor=vec4(0.94,0.97,1.0,vAlpha*(1.0-smoothstep(0.20,0.5,r))); }`
  });
  const points = new THREE.Points(geometry, material);
  points.name = 'C43_ZWinter_Snow';
  points.frustumCulled = false;
  // Opaque objects populate depth first. Clear window glass must blend over
  // the flakes afterward, rather than flakes overlaying foreground glazing.
  points.renderOrder = -1;
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

export function courtyardSnowShouldRun({ active, overview, reducedMotion, cameraPosition, forward, curtainAmounts = { left: 1, right: 1 } }) {
  if (!active || overview || reducedMotion || !cameraPosition || !forward) return false;
  // Snow remains visible from the bedroom whenever an open panel exposes the
  // window; closed blackout curtains stop hidden animation behind the fabric.
  return forward.z < .25 && (cameraPosition.z < .04 || Math.max(curtainAmounts.left, curtainAmounts.right) > .08);
}
