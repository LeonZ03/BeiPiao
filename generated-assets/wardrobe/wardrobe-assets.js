/* Wardrobe props for Three.js r180. All dimensions are metres; +Y is up and +Z faces the room. */
function carbonTexture(THREE) {
  if (typeof document === 'undefined') return null;
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'); x.fillStyle = '#111318'; x.fillRect(0,0,128,128);
  x.globalAlpha = .72; x.strokeStyle = '#5c626b'; x.lineWidth = 2;
  // fine 2x2 twill weave, suitable for glossy PBR reflections
  x.lineWidth = 1;
  for (let i=-128;i<256;i+=7) { x.beginPath(); x.moveTo(i,0); x.lineTo(i+128,128); x.stroke(); x.beginPath(); x.moveTo(i,128); x.lineTo(i+128,0); x.stroke(); }
  const t = new THREE.CanvasTexture(c); t.wrapS=t.wrapT=THREE.RepeatWrapping; t.repeat.set(5,5); return t;
}
function m(THREE, color, roughness=.4, metalness=.05, extra={}) { return new THREE.MeshPhysicalMaterial(Object.assign({color,roughness,metalness},extra)); }
function tube(THREE, a, b, r, material, radial=8) {
  const d = new THREE.Vector3().subVectors(b,a), g = new THREE.CylinderGeometry(r,r,d.length(),radial,1);
  const o = new THREE.Mesh(g,material); o.position.copy(a).add(b).multiplyScalar(.5); o.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize()); return o;
}
function ellipseCurve(THREE, rx, ry, y0, z, n=48) {
  const p=[]; for(let i=0;i<n;i++){const a=i/n*Math.PI*2; p.push(new THREE.Vector3(rx*Math.cos(a),y0+ry*Math.sin(a),z));} return new THREE.CatmullRomCurve3(p,true,'centripetal',.12);
}
function makeLogo(THREE, text, color, w=.07, h=.018) {
  if(typeof document==='undefined') return null; const c=document.createElement('canvas'); c.width=256;c.height=64; const x=c.getContext('2d'); x.clearRect(0,0,256,64); x.fillStyle=color; x.font='bold italic 48px Arial'; x.textAlign='center'; x.textBaseline='middle'; x.fillText(text,128,34); const t=new THREE.CanvasTexture(c); const q=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map:t,transparent:true,side:THREE.DoubleSide})); return q;
}

export function createHelmet(THREE) {
  const g=new THREE.Group(); g.name='LS2 FF801 Carbon Full-Face Helmet';
  const carbon=carbonTexture(THREE), shellMat=m(THREE,0x111318,.22,.48, {clearcoat:.72,clearcoatRoughness:.16}); if(carbon) shellMat.map=carbon;
  const black=m(THREE,0x08090b,.27,.38,{clearcoat:.8,clearcoatRoughness:.14}), trim=m(THREE,0x252a31,.22,.65), rubber=m(THREE,0x0b0c0e,.72,.05);
  const shell=new THREE.Mesh(new THREE.SphereGeometry(1,32,20),shellMat); shell.scale.set(.145,.155,.19); shell.position.set(0,.19,0); g.add(shell);
  // lower neck roll and pronounced jaw/chin guard create a real full-helmet silhouette
  const roll=new THREE.Mesh(new THREE.TorusGeometry(.116,.018,8,32),rubber); roll.rotation.x=Math.PI/2; roll.position.set(0,.035,.005); roll.scale.z=1.22; g.add(roll);
  // recessed face opening / inner liner keeps the visor visibly separated from the shell
  const opening=new THREE.Mesh(new THREE.SphereGeometry(1,24,12),rubber); opening.scale.set(.116,.078,.018); opening.position.set(0,.205,.176); g.add(opening);
  const chin=new THREE.Mesh(new THREE.SphereGeometry(1,24,12),black); chin.scale.set(.125,.058,.105); chin.position.set(0,.105,.112); g.add(chin);
  const hingeMat=m(THREE,0x9b9fa6,.28,.75); for(const sx of [-1,1]){const hinge=new THREE.Mesh(new THREE.CylinderGeometry(.012,.012,.008,16),hingeMat); hinge.rotation.z=Math.PI/2; hinge.position.set(sx*.118,.205,.17); g.add(hinge);}
  const chinVent=new THREE.Mesh(new THREE.BoxGeometry(.072,.014,.008),trim); chinVent.position.set(0,.12,.212); g.add(chinVent);
  // curved visor with amber/red gradient, mounted just ahead of the brow
  let visorMat=m(THREE,0xf06b13,.12,.18,{transparent:true,opacity:.78,transmission:.12,ior:1.45,clearcoat:.8,clearcoatRoughness:.1});
  if(typeof document!=='undefined'){const c=document.createElement('canvas');c.width=256;c.height=128;const x=c.getContext('2d');const q=x.createLinearGradient(0,0,256,0);q.addColorStop(0,'#f8bd21');q.addColorStop(.38,'#ef6920');q.addColorStop(.62,'#b51e45');q.addColorStop(1,'#f7a918');x.fillStyle=q;x.fillRect(0,0,256,128);const t=new THREE.CanvasTexture(c);visorMat.map=t;}
  const vg=new THREE.BufferGeometry(), va=[], vu=[]; const cols=20, rows=8; for(let j=0;j<=rows;j++){const v=j/rows, yy=.22-.105*v, rx=.113-.012*Math.sin(v*Math.PI); for(let i=0;i<=cols;i++){const u=i/cols, xx=(u-.5)*2*rx, zz=.198+.018*Math.cos((u-.5)*Math.PI); va.push(xx,yy,zz); vu.push(u,1-v);}} const idx=[];for(let j=0;j<rows;j++)for(let i=0;i<cols;i++){const a=j*(cols+1)+i;idx.push(a,a+cols+2,a+1,a,a+cols+1,a+cols+2);} vg.setAttribute('position',new THREE.Float32BufferAttribute(va,3));vg.setAttribute('uv',new THREE.Float32BufferAttribute(vu,2));vg.setIndex(idx);vg.computeVertexNormals(); const visor=new THREE.Mesh(vg,visorMat); visor.material.side=THREE.DoubleSide; visor.rotation.x=-.12; visor.position.z=.012; g.add(visor);
  const seal=new THREE.Mesh(new THREE.TorusGeometry(.108,.006,6,32,Math.PI),trim); seal.rotation.x=Math.PI/2; seal.rotation.z=Math.PI; seal.position.set(0,.22,.19); seal.scale.y=.56; g.add(seal);
  // rear upper aerodynamic tail wing
  const wing=new THREE.Mesh(new THREE.BoxGeometry(.15,.012,.055),black); wing.position.set(0,.335,-.115); wing.rotation.x=-.14; g.add(wing);
  for(const x of [-.075,-.042,.042,.075]) { const vent=new THREE.Mesh(new THREE.BoxGeometry(.012,.006,.032),trim); vent.position.set(x,.325,-.095); vent.rotation.x=-.28; g.add(vent); }
  const ls=makeLogo(THREE,'LS2','#f2f4f6',.075,.019); if(ls){ls.position.set(-.075,.285,.145);ls.rotation.y=-.15;g.add(ls);} const ff=makeLogo(THREE,'FF801','#d7d9dc',.055,.012); if(ff){ff.position.set(.088,.105,.128);ff.rotation.y=.2;g.add(ff);}
  g.scale.x=.93; g.scale.z=.885; g.position.y=-.013; g.userData.dimensions={width:.27,height:.36,depth:.36}; return g;
}

export function createRacket(THREE,{variant=0}={}) {
  const g=new THREE.Group(); g.name='Tennis Racket '+variant; const orange=variant?0xff6b18:0xff3d12, dark=0x11151b, grip=m(THREE,0xf4f1e7,.82,.02), frame=m(THREE,orange,.27,.3,{clearcoat:.45}), throat=m(THREE,dark,.3,.35);
  const handle=new THREE.Mesh(new THREE.CylinderGeometry(.012,.015,.185,12),grip); handle.position.y=.0925; g.add(handle);
  const butt=new THREE.Mesh(new THREE.CylinderGeometry(.018,.018,.018,12),throat); butt.position.y=.005; g.add(butt);
  const curve=ellipseCurve(THREE,.135,.205,.455,.018,56); g.add(new THREE.Mesh(new THREE.TubeGeometry(curve,56,.006,8,true),frame));
  // deep graphite side sections, with orange crown and shoulders
  g.add(tube(THREE,new THREE.Vector3(-.135,.455,.018),new THREE.Vector3(-.105,.34,.018),.006,throat)); g.add(tube(THREE,new THREE.Vector3(.135,.455,.018),new THREE.Vector3(.105,.34,.018),.006,throat));
  // Y-shaped throat, with a dark split and orange shoulders
  g.add(tube(THREE,new THREE.Vector3(-.012,.185,.018),new THREE.Vector3(-.072,.29,.018),.009,throat)); g.add(tube(THREE,new THREE.Vector3(.012,.185,.018),new THREE.Vector3(.072,.29,.018),.009,throat)); g.add(tube(THREE,new THREE.Vector3(-.072,.29,.018),new THREE.Vector3(-.105,.36,.018),.007,frame)); g.add(tube(THREE,new THREE.Vector3(.072,.29,.018),new THREE.Vector3(.105,.36,.018),.007,frame));
  const sm=m(THREE,variant?0xe85a18:0xf08022,.62,.05,{transparent:true,opacity:.72}); const lines=[]; for(let i=0;i<9;i++){const x=-.105+i*.02625, lim=.205*Math.sqrt(Math.max(0,1-(x/.135)*(x/.135))); lines.push(x,.455-lim,.027,x,.455+lim,.027);} for(let i=0;i<13;i++){const y=.31+i*.027, t=Math.max(0,Math.min(1,(y-.25)/.41)), half=.135*Math.sin(Math.PI*t);lines.push(-half,y,.028,half,y,.028);} const sg=new THREE.BufferGeometry();sg.setAttribute('position',new THREE.Float32BufferAttribute(lines,3));g.add(new THREE.LineSegments(sg,new THREE.LineBasicMaterial({color:variant?0xff8a27:0xffa03a,transparent:true,opacity:.9}))); g.position.y=.004; g.userData.dimensions={width:.27,height:.68,depth:.045}; return g;
}

export function createCap(THREE) {
  const g=new THREE.Group(); g.name='Black LA Baseball Cap'; const cloth=m(THREE,0x0b0c10,.78,.02), seam=m(THREE,0x333741,.68,.03);
  const crown=new THREE.Mesh(new THREE.SphereGeometry(1,24,12,0,Math.PI*2,0,Math.PI*.62),cloth); crown.scale.set(.09,.08,.125); crown.position.set(0,.087,0); g.add(crown);
  const band=new THREE.Mesh(new THREE.TorusGeometry(.078,.009,8,32),cloth); band.rotation.x=Math.PI/2; band.position.y=.048; band.scale.z=1.45; g.add(band);
  const shape=new THREE.Shape(); shape.moveTo(-.075,0);shape.quadraticCurveTo(0,-.055,.09,-.015);shape.quadraticCurveTo(.11,.005,.075,.02);shape.quadraticCurveTo(0,.045,-.075,.018);shape.closePath(); const brim=new THREE.Mesh(new THREE.ExtrudeGeometry(shape,{depth:.012,bevelEnabled:true,bevelSegments:2,bevelSize:.004,bevelThickness:.003}),cloth); brim.rotation.x=Math.PI/2-.12; brim.position.set(0,.05,.105); g.add(brim);
  for(let i=-2;i<=2;i++){const s=new THREE.Mesh(new THREE.TorusGeometry(.078,.0025,5,18,Math.PI*.62),seam);s.rotation.y=i*.16;s.rotation.x=Math.PI/2;s.position.set(i*.018,.095,.002);g.add(s);} const la=makeLogo(THREE,'LA','#f3f3f0',.043,.022); if(la){la.position.set(0,.105,.116);la.rotation.x=-.1;g.add(la);} g.scale.x=.887; g.scale.z=.936; g.position.y=-.031; g.userData.dimensions={width:.18,height:.15,depth:.25}; return g;
}

export default {createHelmet,createRacket,createCap};
