// Only animate the authored hinge; all persistent geometry remains in Blender.
export function createLaptop(world){
  let root,lid;
  world.traverse(o=>{if(o.userData.laptopRoot)root=o;if(o.userData.laptopLid)lid=o;});
  if(!root||!lid)throw Error('Missing authored laptop hinge');
  root.userData.interactive='laptop';root.userData.dynamic=true;
  root.traverse(o=>{o.userData.dynamic=true;});
  const {openAngle=-.21,closedAngle=Math.PI/2,defaultOpen=true}=lid.userData;
  let amount=defaultOpen?1:0,target=amount,revision=0;
  const apply=()=>{lid.rotation.x=closedAngle+(openAngle-closedAngle)*amount;};apply();
  return {
    toggle(){target=target>.5?0:1;return !!target;},
    update(dt){if(amount===target)return false;amount+=(target-amount)*(1-Math.exp(-Math.min(dt,.05)*4.5));if(Math.abs(target-amount)<.0001)amount=target;apply();revision++;return true;},
    get revision(){return revision;},
    get state(){return {amount,target,open:target===1,angle:lid.rotation.x};}
  };
}
