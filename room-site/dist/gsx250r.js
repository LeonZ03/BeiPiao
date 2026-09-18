import {buildProp} from './prop-assets.js?v=blender18';

// Native Blender model: Y up, front -Z. Suzuki catalogue wheelbase 1.430 m;
// the owner's blue/white graphics and yellow rim tape are applied below.
export function createMotorcycle(THREE){
  const root=buildProp(THREE,'motorcycle');root.name='Suzuki_GSX250R';
  const screen=root.getObjectByName('curved-windscreen');
  screen.material=new THREE.MeshPhysicalMaterial({color:'#596d7c',roughness:.22,metalness:.15,transparent:true,opacity:.70,side:THREE.DoubleSide});screen.castShadow=false;
  function decal(text,side,at,w,h){
    const c=document.createElement('canvas');c.width=1024;c.height=256;const ctx=c.getContext('2d');
    ctx.fillStyle='#f3f5f3';ctx.font='italic 900 142px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,512,138);
    const map=new THREE.CanvasTexture(c);map.colorSpace=THREE.SRGBColorSpace;
    const mesh=new THREE.Mesh(new THREE.PlaneGeometry(w,h),new THREE.MeshStandardMaterial({map,transparent:true,roughness:.43,polygonOffset:true,polygonOffsetFactor:-2,depthWrite:false,side:THREE.DoubleSide}));
    mesh.name=text+'-painted-side-marking';mesh.position.set(side*at[0],at[1],at[2]);mesh.rotation.y=side*Math.PI/2;root.add(mesh);
  }
  for(const s of [-1,1]){
    decal('SUZUKI',s,[.248,.690,-.355],.32,.098);
    decal('250R',s,[.246,.818,-.60],.16,.044);
  }
  root.userData.dimensions={length:2.085,width:.74,height:1.11,wheelbase:1.43};return root;
}
