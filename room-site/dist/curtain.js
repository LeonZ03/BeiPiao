// The geometry and endpoint positions are authored in the Blender scene.
// This controller interpolates the fabric shapes and attached rings only.
export function createCurtainController(panels,rings){
  for(const p of panels){
    if(!p.userData.curtainShapeKey||!p.morphTargetInfluences?.length)throw new Error('Missing Blender curtain shape keys');
  }
  return function updateCurtain(openness){
    const a=Math.max(0,Math.min(1,openness));
    for(const p of panels){
      p.morphTargetInfluences[0]=a;
      p.material.emissiveIntensity=3.0-2.945*a;
    }
    for(const r of rings){
      const {fixedRight,closedWidth,openWidth,slideU}=r.userData;
      const width=closedWidth+(openWidth-closedWidth)*a;
      r.position.x=fixedRight-width+width*slideU;
    }
  };
}
