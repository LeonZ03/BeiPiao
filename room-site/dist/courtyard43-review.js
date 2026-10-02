// Developer-only comparison modes. No UI, persistence or model mutation.
export function createCourtyardReview(THREE,world,finish,invalidate){
  const originals=new Map(),greys=new Map();let mode='final';
  world.traverse(o=>{if(o.isMesh)originals.set(o,o.material);});
  function grey(m){
    // Retain glazing and transparent plastic to preserve real occlusion.
    if(m.transparent||m.transmission>0)return m;
    if(!greys.has(m))greys.set(m,new THREE.MeshStandardMaterial({color:0x999999,roughness:.78,metalness:0,side:m.side}));
    return greys.get(m);
  }
  return{get mode(){return mode;},set(next){
    if(!['neutral-grey','no-grade','final'].includes(next))throw Error('Invalid comparison mode');
    mode=next;
    for(const [o,m] of originals)o.material=mode==='neutral-grey'?(Array.isArray(m)?m.map(grey):grey(m)):m;
    finish.setGrading(mode==='final');invalidate(true);return{mode};
  },dispose(){for(const m of greys.values())m.dispose();}};
}
