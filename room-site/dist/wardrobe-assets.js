import {buildProp} from './prop-assets.js?v=blender18';
/* Wardrobe props for Three.js r180. All dimensions are metres; +Y is up and +Z faces the room. */
function m(THREE, color, roughness=.4, metalness=.05, extra={}) { return new THREE.MeshPhysicalMaterial(Object.assign({color,roughness,metalness},extra)); }
function ellipseCurve(THREE, rx, ry, y0, z, n=48) {
  const p=[]; for(let i=0;i<n;i++){const a=i/n*Math.PI*2; p.push(new THREE.Vector3(rx*Math.cos(a),y0+ry*Math.sin(a),z));} return new THREE.CatmullRomCurve3(p,true,'centripetal',.12);
}
function makeLogo(THREE, text, color, w=.07, h=.018) {
  if(typeof document==='undefined') return null; const c=document.createElement('canvas'); c.width=256;c.height=64; const x=c.getContext('2d'); x.clearRect(0,0,256,64); x.fillStyle=color; x.font='bold italic 48px Arial'; x.textAlign='center'; x.textBaseline='middle'; x.fillText(text,128,34); const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace; const q=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshBasicMaterial({map:t,transparent:true,side:THREE.DoubleSide})); return q;
}

import {createDetailedHelmet as createHelmet} from './close-refinements.js?v=blender18';
export {createHelmet};


export function createRacket(THREE,{variant=0}={}) {
  const g=new THREE.Group();g.name='Tennis Racket '+variant;
  const grip=m(THREE,0xe4e2d6,.86,0),graphite=m(THREE,0x171b21,.29,.2,{clearcoat:.5}),orange=m(THREE,variant?0xf27819:0xe84618,.3,.25,{clearcoat:.5});
  const handle=new THREE.Mesh(new THREE.CylinderGeometry(.013,.015,.188,8),grip);handle.name='racket-grip';handle.position.y=.094;g.add(handle);
  const butt=new THREE.Mesh(new THREE.CylinderGeometry(.017,.019,.014,8),graphite);butt.position.y=.001;g.add(butt);
  const tape=[];for(let i=0;i<400;i++){const y=.014+i/399*.17,a=i/399*Math.PI*2*14,r=.015-y*.011;tape.push(new THREE.Vector3(r*Math.cos(a),y,r*Math.sin(a)));}
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(tape),360,.0007,4,false),m(THREE,0xbebeb4,.88,0)));
  // Grip, Y-shaped throat, hoop and strings all share the same centre plane.
  const rx=.131,ry=.185,cy=.470;
  const hoop=new THREE.Mesh(new THREE.TubeGeometry(ellipseCurve(THREE,rx,ry,cy,0,96),128,.0067,10,true),orange);hoop.name='racket-hoop';g.add(hoop);
  for(const sign of [-1,1]){
    const points=[[0,.166,0],[sign*.008,.203,0],[sign*.048,.271,0],[sign*.095,.342,0]].map(p=>new THREE.Vector3(...p));
    const throat=new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points),40,.0078,10,false),graphite);throat.name='connected-racket-throat';g.add(throat);
    const pts=[];for(let i=0;i<=36;i++){const a=-Math.PI/2+i/36*Math.PI*.82;pts.push(new THREE.Vector3(sign*rx*Math.cos(a),cy+ry*Math.sin(a),0));}
    g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts),48,.0069,10,false),graphite));
  }
  const bridge=[];for(let i=0;i<=20;i++){const x=(i/20-.5)*.118;bridge.push(new THREE.Vector3(x,.287+.017*(x/.059)**2,0));}
  g.add(new THREE.Mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(bridge),24,.0055,8,false),graphite));
  const strings=[];
  for(let i=-8;i<=8;i++){const x=i*.0144,dy=ry*Math.sqrt(1-(x/rx)**2);strings.push(x,cy-dy,.001,x,cy+dy,.001);}
  for(let i=-11;i<=11;i++){const y=i*.0158,dx=rx*Math.sqrt(1-(y/ry)**2);strings.push(-dx,cy+y,.0015,dx,cy+y,.0015);}
  const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.Float32BufferAttribute(strings,3));g.add(new THREE.LineSegments(geo,new THREE.LineBasicMaterial({color:variant?0x25272b:0xec8c33})));
  const mark=makeLogo(THREE,variant?'DUNLOP':'HEAD','#ece6dc',.034,.006);if(mark){mark.position.set(0,.205,.0082);g.add(mark);}
  g.userData.dimensions={width:.275,height:.668,depth:.036};return g;
}

export function createCap(THREE) {
  const g=buildProp(THREE,'cap');g.name='Black LA Baseball Cap';
  const stitch=m(THREE,0x33353a,.98,0);
  // Interlocked serif L / A traced as embroidery, projected onto the curved crown.
  // A regular text label on a flat plane would cut into the cloth on either side.
  const thread=m(THREE,0xf1f0e8,.97,0,{side:THREE.DoubleSide});
  const letters=[
    [[-.014,.021],[-.004,.021],[-.004,.017],[-.007,.017],[-.007,-.011],[.007,-.011],[.007,-.005],[.011,-.005],[.010,-.016],[-.017,-.016],[-.017,-.012],[-.013,-.012],[-.010,.017],[-.014,.017]],
    [[.001,.013],[.009,.013],[.007,.009],[.012,-.021],[.017,-.021],[.017,-.025],[.004,-.025],[.004,-.021],[.007,-.021],[.005,-.013],[-.004,-.013],[-.007,-.021],[-.003,-.021],[-.003,-.025],[-.015,-.025],[-.015,-.021],[-.011,-.021]]
  ];
  for(let k=0;k<letters.length;k++){
    const s=new THREE.Shape(letters[k].map(p=>new THREE.Vector2(...p)));s.closePath();
    if(k===1){const hole=new THREE.Path();hole.moveTo(.001,.004);hole.lineTo(-.002,-.009);hole.lineTo(.004,-.009);hole.closePath();s.holes.push(hole);}
    let geometry=new THREE.ShapeGeometry(s).toNonIndexed();
    // Subdivide before wrapping so even the broad letter strokes follow the fabric.
    for(let pass=0;pass<3;pass++){
      const p=geometry.attributes.position,next=[];for(let i=0;i<p.count;i+=3){const a=new THREE.Vector3().fromBufferAttribute(p,i),b=new THREE.Vector3().fromBufferAttribute(p,i+1),c=new THREE.Vector3().fromBufferAttribute(p,i+2),ab=a.clone().add(b).multiplyScalar(.5),bc=b.clone().add(c).multiplyScalar(.5),ca=c.clone().add(a).multiplyScalar(.5);for(const q of [a,ab,ca,ab,b,bc,ca,bc,c,ab,bc,ca])next.push(...q.toArray());}geometry.dispose();geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(next,3));
    }
    const p=geometry.attributes.position;for(let i=0;i<p.count;i++){const x=p.getX(i),y=p.getY(i)+.055,z=.104*Math.sqrt(Math.max(0,1-(x/.093)**2-(y/.108)**2))+.0013;p.setXYZ(i,x,y,z);}geometry.computeVertexNormals();const monogram=new THREE.Mesh(geometry,thread);monogram.name='curved-interlocking-LA-embroidery';g.add(monogram);
  }
  for(let i=0;i<6;i++){const a=i*Math.PI/3+.5,eye=new THREE.Mesh(new THREE.TorusGeometry(.0021,.0006,5,12),stitch);eye.position.set(.071*Math.sin(a),.067,.079*Math.cos(a));eye.lookAt(eye.position.clone().multiplyScalar(2));g.add(eye);}
  g.userData.dimensions={width:.19,height:.115,depth:.292};return g;
}
export default {createHelmet,createRacket,createCap};
