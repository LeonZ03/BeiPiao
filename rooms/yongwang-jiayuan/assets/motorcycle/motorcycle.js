/*
 * Suzuki GSX250R inspired display asset.
 * Coordinate system: Y up, front points toward -Z, wheels touch y=0.
 * No external textures or network resources are required.
 */

export function createMotorcycle(THREE) {
  const root = new THREE.Group();
  root.name = 'Suzuki_GSX250R';

  const materials = {
    blue: new THREE.MeshStandardMaterial({ color: 0x0879db, metalness: 0.72, roughness: 0.22 }),
    blueDark: new THREE.MeshStandardMaterial({ color: 0x0756b8, metalness: 0.65, roughness: 0.26 }),
    blueGloss: new THREE.MeshStandardMaterial({ color: 0x118cf0, metalness: 0.8, roughness: 0.14 }),
    black: new THREE.MeshStandardMaterial({ color: 0x101318, metalness: 0.25, roughness: 0.43 }),
    tire: new THREE.MeshStandardMaterial({ color: 0x080a0c, metalness: 0.03, roughness: 0.88 }),
    charcoal: new THREE.MeshStandardMaterial({ color: 0x242a30, metalness: 0.42, roughness: 0.36 }),
    silver: new THREE.MeshStandardMaterial({ color: 0xaeb7c0, metalness: 0.9, roughness: 0.2 }),
    steel: new THREE.MeshStandardMaterial({ color: 0x555f68, metalness: 0.88, roughness: 0.28 }),
    white: new THREE.MeshStandardMaterial({ color: 0xf3f6f7, metalness: 0.1, roughness: 0.35 }),
    neon: new THREE.MeshStandardMaterial({ color: 0xcaff00, emissive: 0x263900, metalness: 0.3, roughness: 0.28 }),
    red: new THREE.MeshStandardMaterial({ color: 0xd91622, emissive: 0x2c0204, metalness: 0.25, roughness: 0.3 }),
    amber: new THREE.MeshStandardMaterial({ color: 0xff9b19, emissive: 0x331400, metalness: 0.18, roughness: 0.35 }),
    glass: new THREE.MeshPhysicalMaterial({ color: 0x32465e, transparent: true, opacity: 0.38, roughness: 0.1, metalness: 0.05, side: THREE.DoubleSide, depthWrite: false }),
  };

  const add = (obj, name, parent = root) => { obj.name = name; parent.add(obj); return obj; };
  const mesh = (geometry, material, name, parent = root) => add(new THREE.Mesh(geometry, material), name, parent);
  const cyl = (radius, length, material, name, radial = 12, parent = root) => mesh(new THREE.CylinderGeometry(radius, radius, length, radial, 1), material, name, parent);

  // A smooth longitudinal volume assembled from elliptical cross-sections.
  // This is used for the painted tank, fairing and tail instead of box primitives.
  function loft(sections, material, name, segments = 20, parent = root) {
    const positions = [], normals = [], uvs = [], indices = [];
    for (let i = 0; i < sections.length; i++) {
      const s = sections[i];
      for (let j = 0; j < segments; j++) {
        const a = (j / segments) * Math.PI * 2;
        const ca = Math.cos(a), sa = Math.sin(a);
        positions.push(s.w * ca, s.y + s.h * 0.5 * sa, s.z);
        // Approximate smooth radial normals; computeVertexNormals will refine joins.
        normals.push(ca, sa, 0);
        uvs.push(i / (sections.length - 1), j / segments);
      }
    }
    for (let i = 0; i < sections.length - 1; i++) {
      for (let j = 0; j < segments; j++) {
        const a = i * segments + j;
        const b = i * segments + (j + 1) % segments;
        const c = (i + 1) * segments + (j + 1) % segments;
        const d = (i + 1) * segments + j;
        indices.push(a, b, d, b, c, d);
      }
    }
    // cap both ends so the volume remains a complete solid object
    const start = positions.length / 3;
    const s0 = sections[0], s1 = sections[sections.length - 1];
    positions.push(0, s0.y, s0.z, 0, s1.y, s1.z);
    normals.push(0, 0, -1, 0, 0, 1);
    uvs.push(0.5, 0.5, 0.5, 0.5);
    for (let j = 0; j < segments; j++) {
      const n = (j + 1) % segments;
      indices.push(start, n, j);
      const e = (sections.length - 1) * segments;
      indices.push(start + 1, e + j, e + n);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uvs, 2));
    g.setIndex(indices); g.computeVertexNormals();
    return mesh(g, material, name, parent);
  }

  function tubeBetween(a, b, radius, material, name, radial = 10, parent = root) {
    const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b);
    const delta = vb.clone().sub(va), length = delta.length();
    const o = cyl(radius, length, material, name, radial, parent);
    o.position.copy(va).add(vb).multiplyScalar(0.5);
    o.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
    return o;
  }

  function torus(radius, tube, material, name, position, parent = root) {
    const o = mesh(new THREE.TorusGeometry(radius, tube, 12, 36), material, name, parent);
    // TorusGeometry's native hole axis is Z; motorcycle wheel axles run across X.
    o.rotation.y = Math.PI / 2; o.position.set(...position); return o;
  }

  function disk(radius, depth, material, name, x, y, z, parent = root) {
    const o = cyl(radius, depth, material, name, 24, parent);
    o.rotation.z = Math.PI / 2; o.position.set(x, y, z); return o;
  }

  function rimRing(inner, outer, material, name, x, y, z, parent = root) {
    const ringMaterial = material.clone(); ringMaterial.side = THREE.DoubleSide;
    const o = mesh(new THREE.RingGeometry(inner, outer, 32, 2), ringMaterial, name, parent);
    o.rotation.y = Math.PI / 2; o.position.set(x, y, z); return o;
  }

  function panel(side, points, thickness, material, name, parent = root) {
    // points are [z,y], side is +/-X. Slightly triangulated surfaces read as fairing panels.
    const x0 = side * 0.002, x1 = side * thickness;
    const p = [], u = [], ind = [], count = points.length;
    for (const [z, y] of points) p.push(x0, y, z);
    for (const [z, y] of points) p.push(x1, y, z);
    for (let i = 1; i < count - 1; i++) { ind.push(0, i + 1, i, count, count + i, count + i + 1); }
    for (let i = 0; i < count; i++) { const n = (i + 1) % count; ind.push(i, count + i, n, n, count + i, count + n); }
    for (let i = 0; i < count; i++) { u.push(0, i / (count - 1)); }
    for (let i = 0; i < count; i++) { u.push(1, i / (count - 1)); }
    const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3)); g.setAttribute('uv', new THREE.Float32BufferAttribute(u, 2)); g.setIndex(ind); g.computeVertexNormals();
    return mesh(g, material, name, parent);
  }

  function makeDecalTexture(text, accent = '#ffffff') {
    if (typeof document === 'undefined') return null;
    const c = document.createElement('canvas'); c.width = 512; c.height = 128;
    const ctx = c.getContext('2d'); ctx.clearRect(0, 0, c.width, c.height);
    ctx.font = '900 82px Arial Black, Arial'; ctx.fillStyle = accent; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.shadowColor = 'rgba(0,0,0,.42)'; ctx.shadowBlur = 5; ctx.fillText(text, 256, 66);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  }

  function decalPlane(text, side, z, y, width, height) {
    const tex = makeDecalTexture(text);
    if (!tex) return;
    const m = new THREE.MeshBasicMaterial({ map: tex, transparent: true, side: THREE.DoubleSide, depthWrite: false });
    const o = mesh(new THREE.PlaneGeometry(width, height), m, `${text}_decal_${side}`);
    // Keep the graphic just outside the side panel so it survives normal depth testing.
    o.position.set(side * 0.425, y, z); o.rotation.set(0, side < 0 ? -Math.PI / 2 : Math.PI / 2, 0);
    return o;
  }

  // Wheels: broad sport tyres, black multi-spoke rims, hubs, brake rotors and neon rim tape.
  function wheel(z, isFront) {
    const y = 0.335, r = 0.335;
    // major radius + tube radius equals the axle height, so the tyre sits exactly on y=0.
    const w = torus(r - 0.063, 0.063, materials.tire, isFront ? 'front_tire' : 'rear_tire', [0, y, z]);
    // subtle tread ribs, kept low-poly and instanced by reusing the same geometry/material
    const treadGeo = new THREE.BoxGeometry(0.007, 0.018, 0.055);
    const treadMat = materials.charcoal;
    const tread = new THREE.InstancedMesh(treadGeo, treadMat, 18); tread.name = isFront ? 'front_tread' : 'rear_tread';
    for (let i = 0; i < 18; i++) {
      const a = (i / 18) * Math.PI * 2; const m = new THREE.Matrix4();
      // Tyre tread lives in the Y/Z wheel plane and follows the wheel curvature.
      m.makeRotationX(a); m.setPosition(0, y + Math.cos(a) * (r - .02), z + Math.sin(a) * (r - .02));
      tread.setMatrixAt(i, m);
    }
    tread.instanceMatrix.needsUpdate = true;
    // The tread instances are intentionally centered on the tyre profile to avoid oversized blocks.
    add(tread, tread.name);
    // Leave the spoke field open: a thin annular rim gives the black wheel its depth
    // while the silver spokes remain visible through the center.
    rimRing(.115, .245, materials.black, isFront ? 'front_rim_ring' : 'rear_rim_ring', -.058, y, z);
    rimRing(.115, .245, materials.black, isFront ? 'front_rim_ring_outer' : 'rear_rim_ring_outer', .058, y, z);
    disk(0.065, 0.15, materials.steel, isFront ? 'front_hub' : 'rear_hub', 0, y, z);
    torus(0.272, 0.012, materials.neon, isFront ? 'front_neon_rim_tape' : 'rear_neon_rim_tape', [0, y, z]);
    const spokeGeo = new THREE.CylinderGeometry(0.012, 0.012, 0.205, 8);
    const spokes = new THREE.InstancedMesh(spokeGeo, materials.steel, 7); spokes.name = isFront ? 'front_7_spokes' : 'rear_7_spokes';
    for (let i = 0; i < 7; i++) {
      const a = i * Math.PI * 2 / 7; const m = new THREE.Matrix4();
      // CylinderGeometry is Y-axis aligned; rotate around the X axle into Y/Z.
      m.makeRotationX(a); m.setPosition(0, y + Math.cos(a) * .1025, z + Math.sin(a) * .1025); spokes.setMatrixAt(i, m);
    }
    spokes.instanceMatrix.needsUpdate = true;
    add(spokes, spokes.name);
    if (isFront) {
      disk(0.235, 0.018, materials.steel, 'front_brembo_style_rotor', -0.082, y, z);
      disk(0.062, 0.022, materials.charcoal, 'front_caliper', -0.101, y + .03, z - .055);
    } else {
      disk(0.215, 0.018, materials.steel, 'rear_brake_rotor', 0.079, y, z);
      disk(0.055, 0.024, materials.charcoal, 'rear_caliper', 0.097, y + .02, z - .05);
    }
    return w;
  }
  wheel(-0.715, true); wheel(0.715, false);

  // Main painted volumes. Their ring sections give the correct pinched tank and sharp sport-bike nose from above.
  loft([
    { z: -1.055, w: .115, y: .69, h: .18 }, { z: -.97, w: .285, y: .64, h: .35 },
    { z: -.76, w: .37, y: .61, h: .44 }, { z: -.42, w: .405, y: .62, h: .49 },
    { z: -.17, w: .37, y: .67, h: .47 },
  ], materials.blueGloss, 'front_full_fairing', 24);
  loft([
    { z: -.45, w: .17, y: .75, h: .27 }, { z: -.28, w: .31, y: .78, h: .39 },
    { z: -.02, w: .35, y: .83, h: .43 }, { z: .20, w: .33, y: .83, h: .42 },
    { z: .40, w: .22, y: .77, h: .30 },
  ], materials.blueGloss, 'fuel_tank', 24);
  loft([
    { z: .24, w: .29, y: .72, h: .31 }, { z: .46, w: .32, y: .72, h: .31 },
    { z: .72, w: .29, y: .73, h: .29 }, { z: .98, w: .145, y: .76, h: .20 },
    { z: 1.045, w: .055, y: .73, h: .12 },
  ], materials.blue, 'raised_rear_tail', 20);
  loft([
    { z: -.87, w: .14, y: .42, h: .10 }, { z: -.68, w: .23, y: .39, h: .11 },
    { z: -.37, w: .29, y: .40, h: .13 }, { z: .12, w: .275, y: .42, h: .13 },
  ], materials.blueDark, 'lower_belly_fairing', 20);

  // Black tank knee pads and crisp side fairing silhouettes.
  loft([{ z: -.27, w: .31, y: .77, h: .15 }, { z: .22, w: .30, y: .77, h: .15 }], materials.black, 'tank_knee_center', 18);
  for (const s of [-1, 1]) {
    panel(s, [[-.92,.52],[-.78,.46],[-.34,.43],[-.04,.49],[-.20,.69],[-.65,.67]], .414, materials.blue, `left_right_upper_side_fairing_${s}`);
    panel(s, [[-.52,.40],[-.28,.31],[.08,.34],[.27,.53],[-.10,.59]], .419, materials.white, `white_graphic_panel_${s}`);
    panel(s, [[.14,.39],[.42,.39],[.83,.49],[.77,.66],[.42,.68]], .415, materials.blueDark, `tail_side_panel_${s}`);
    // dark frame / knee insert visible below the fairing
    panel(s, [[-.18,.52],[.06,.46],[.35,.46],[.24,.62],[-.06,.67]], .425, materials.charcoal, `black_knee_insert_${s}`);
    decalPlane('SUZUKI', s, -.34, .55, .42, .105);
    decalPlane('GSX250R', s, -.70, .59, .29, .055);
  }

  // Graphics visible from the elevated fourth-floor camera: white Suzuki-style
  // slashes over the tank and a small tail stripe. They sit just above the
  // curved paint rather than relying on a perspective-facing side decal.
  const tankStripe = mesh(new THREE.PlaneGeometry(.105, .34), materials.white, 'tank_top_white_stripe');
  tankStripe.position.set(-.045, 1.049, -.015); tankStripe.rotation.x = -Math.PI / 2; tankStripe.rotation.y = -.17;
  const tankFlash = mesh(new THREE.PlaneGeometry(.055, .22), materials.neon, 'tank_top_lime_flash');
  tankFlash.position.set(.09, 1.05, -.02); tankFlash.rotation.x = -Math.PI / 2; tankFlash.rotation.y = -.17;
  const tailStripe = mesh(new THREE.PlaneGeometry(.10, .27), materials.white, 'tail_top_white_stripe');
  tailStripe.position.set(.02, .887, .64); tailStripe.rotation.x = -Math.PI / 2; tailStripe.rotation.y = .12;

  // Seat and separate raised pillion: thin custom lofts conform to the stepped silhouette.
  loft([{ z: .13, w: .22, y: .87, h: .095 }, { z: .36, w: .225, y: .88, h: .09 }, { z: .62, w: .19, y: .87, h: .085 }], materials.black, 'rider_seat', 20);
  loft([{ z: .58, w: .17, y: .93, h: .08 }, { z: .78, w: .17, y: .95, h: .075 }, { z: .91, w: .13, y: .91, h: .07 }], materials.black, 'raised_pillion_seat', 18);
  loft([{ z: .30, w: .225, y: .90, h: .035 }, { z: .63, w: .19, y: .90, h: .035 }], materials.charcoal, 'seat_edge', 18);

  // Chassis, engine and rear swingarm.
  tubeBetween([-.22,.39,-.20], [-.14,.76,.18], .035, materials.charcoal, 'left_frame_rail');
  tubeBetween([.22,.39,-.20], [.14,.76,.18], .035, materials.charcoal, 'right_frame_rail');
  tubeBetween([-.25,.41,.20], [-.12,.76,.48], .032, materials.black, 'left_subframe');
  tubeBetween([.25,.41,.20], [.12,.76,.48], .032, materials.black, 'right_subframe');
  tubeBetween([-.10,.31,.27], [-.08,.34,.70], .055, materials.charcoal, 'left_swingarm');
  tubeBetween([.10,.31,.27], [.08,.34,.70], .055, materials.charcoal, 'right_swingarm');
  // Engine case and cylinders, visible from either side.
  for (const s of [-1, 1]) {
    disk(.18, .08, materials.black, `engine_case_${s}`, s * .235, .43, -.02);
    disk(.105, .09, materials.charcoal, `engine_clutch_cover_${s}`, s * .282, .46, -.02);
    for (let i = 0; i < 5; i++) tubeBetween([s*.24,.53,-.19 + i*.075], [s*.24,.53,-.16 + i*.075], .018, materials.steel, `engine_fin_${s}_${i}`, 8);
  }
  // Rear mono-shock and triangular linkage.
  tubeBetween([0,.37,.22], [0,.70,.48], .035, materials.red, 'rear_monoshock');
  tubeBetween([-.18,.30,.45], [0,.52,.25], .023, materials.silver, 'left_linkage');
  tubeBetween([.18,.30,.45], [0,.52,.25], .023, materials.silver, 'right_linkage');

  // Front suspension and steering. The two fork legs angle forward toward the axle.
  for (const s of [-1, 1]) {
    tubeBetween([s*.115,.91,-.49], [s*.115,.39,-.715], .027, materials.silver, `front_fork_${s}`, 12);
    tubeBetween([s*.115,.86,-.49], [s*.115,.39,-.715], .043, materials.black, `front_fork_lower_${s}`, 12);
  }
  tubeBetween([-.18,.92,-.48], [.18,.92,-.48], .021, materials.steel, 'upper_triple_clamp');
  tubeBetween([-.40,.93,-.43], [.40,.93,-.43], .018, materials.black, 'clip_on_handlebar');
  for (const s of [-1, 1]) {
    const grip = cyl(.027, .16, materials.black, `rubber_grip_${s}`, 12);
    grip.rotation.z = Math.PI / 2; grip.position.set(s*.36,.93,-.43);
    const lever = cyl(.008, .18, materials.silver, `brake_lever_${s}`, 8);
    lever.rotation.z = Math.PI / 2; lever.position.set(s*.31,.965,-.41);
  }
  // Dash and ignition barrel.
  loft([{ z: -.42, w: .115, y: .93, h: .08 }, { z: -.30, w: .12, y: .94, h: .09 }], materials.black, 'instrument_cluster', 16);
  disk(.04,.06,materials.steel,'ignition_barrel',0,.98,-.35);

  // Smoked angular windscreen, with a subtle blue lower lip.
  const wg = new THREE.BufferGeometry();
  wg.setAttribute('position', new THREE.Float32BufferAttribute([
    -.235,.94,-.83,  .235,.94,-.83,  .18,1.135,-.61,  -.18,1.135,-.61,
    -.235,.935,-.83, .235,.935,-.83,
  ], 3));
  wg.setIndex([0,1,2,0,2,3,4,5,1,4,1,0]); wg.computeVertexNormals();
  mesh(wg, materials.glass, 'smoked_windscreen');
  tubeBetween([-.235,.94,-.83],[.235,.94,-.83],.012,materials.blue,'windscreen_lower_lip',8);

  // Mirrors: slim stalks with flattened oval reflective shells.
  for (const s of [-1, 1]) {
    tubeBetween([s*.28,1.01,-.51], [s*.35,1.035,-.60], .012, materials.black, `mirror_stalk_${s}`, 8);
    const mirror = mesh(new THREE.SphereGeometry(1, 16, 8), materials.black, `mirror_shell_${s}`);
    mirror.position.set(s*.375,1.055,-.61); mirror.scale.set(.045,.078,.022);
    const inset = mesh(new THREE.SphereGeometry(1, 16, 8), materials.steel, `mirror_glass_${s}`);
    inset.position.set(s*.375,1.057,-.631); inset.scale.set(.034,.062,.008);
  }

  // Headlamp lens and front indicators read correctly from the elevated room camera.
  const lamp = mesh(new THREE.SphereGeometry(1, 20, 10), materials.glass, 'projector_headlamp');
  lamp.position.set(0,.71,-1.055); lamp.scale.set(.095,.08,.018);
  for (const s of [-1,1]) {
    const ind = mesh(new THREE.SphereGeometry(1, 12, 8), materials.amber, `front_indicator_${s}`);
    ind.position.set(s*.285,.56,-.90); ind.scale.set(.035,.025,.022);
  }

  // Long black/silver exhaust canister and silver header under the right side.
  tubeBetween([.23,.36,.02], [.29,.30,.52], .025, materials.steel, 'exhaust_header', 10);
  tubeBetween([.29,.30,.52], [.32,.39,.80], .032, materials.steel, 'exhaust_mid_pipe', 10);
  const can = cyl(.071,.62,materials.black,'large_exhaust_muffler',16); can.rotation.x = Math.PI/2; can.rotation.z = .07; can.position.set(.325,.34,.69);
  const cap = cyl(.075,.035,materials.silver,'exhaust_silver_cap',16); cap.rotation.x = Math.PI/2; cap.rotation.z = .07; cap.position.set(.345,.342,1.00);
  tubeBetween([.22,.38,.37], [.34,.43,.67], .014, materials.silver, 'exhaust_heat_shield_mount',8);
  // angular stamped heat shield
  panel(1, [[.45,.39],[.83,.43],[.91,.48],[.55,.48]], .45, materials.silver, 'exhaust_heat_shield');

  // Foot controls, rear pegs, chain and black rear plate bracket. The plate is deliberately blank.
  for (const s of [-1,1]) {
    tubeBetween([s*.28,.25,.34],[s*.38,.24,.37],.012,materials.silver,`footpeg_bracket_${s}`,8);
    cyl(.025,.06,materials.black,`footpeg_${s}`,10).rotation.z=Math.PI/2;
    root.children[root.children.length-1].position.set(s*.40,.24,.37);
  }
  torus(.20,.012,materials.black,'rear_chain',[.11,.38,.715]);
  const bracket = panel(1, [[.91,.55],[1.02,.55],[1.01,.31],[.92,.31]], .08, materials.black, 'rear_plate_bracket');
  bracket.position.x = .02;
  const plate = panel(1, [[1.00,.47],[1.045,.47],[1.045,.34],[1.00,.34]], .07, materials.charcoal, 'blank_rear_plate'); plate.position.x = .02;
  const tailLight = mesh(new THREE.BoxGeometry(.17,.055,.025), materials.red, 'tail_light'); tailLight.position.set(0,.78,1.02);

  // Small fasteners add scale and highlight around the fairing seams.
  for (const s of [-1,1]) for (const [z,y] of [[-.82,.50],[-.40,.43],[-.05,.48],[.40,.51]]) {
    const bolt = mesh(new THREE.SphereGeometry(.009,8,6), materials.silver, `fairing_fastener_${s}_${z}`);
    bolt.position.set(s*.413,y,z);
  }

  // The GSX250R's quoted width is close to 0.75 m; slim the detailed construction
  // slightly on X so the mirrors/clip-ons remain within that real-world envelope.
  root.scale.x = 0.86;
  // Keep a useful semantic handle for scene placement and camera targeting.
  root.userData = { asset: 'Suzuki GSX250R', units: 'meters', front: '-Z', contactY: 0, approximate: true };
  return root;
}

export default createMotorcycle;
