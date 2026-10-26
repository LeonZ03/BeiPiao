// Arrows provide height controls; touch has separate held keys.
const movementCodes=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowLeft','ArrowRight']);
export function movementKey(event){
  if(event.code==='ArrowUp')return 'MoveUp';
  if(event.code==='ArrowDown')return 'MoveDown';
  return movementCodes.has(event.code)?event.code:null;
}
export function releaseMovementKey(event){
  return movementKey(event);
}
export const touchMovementKeys=Object.freeze({forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',up:'TouchMoveUp',down:'TouchMoveDown'});
export function verticalMovement(keys){
  return Number(keys.has('MoveUp')||keys.has('TouchMoveUp'))-Number(keys.has('MoveDown')||keys.has('TouchMoveDown'));
}
export function wheelHeightDelta(event,pageHeight=800){
  if(event.ctrlKey||!Number.isFinite(event.deltaY))return 0;
  const pixels=event.deltaY*(event.deltaMode===1?16:event.deltaMode===2?pageHeight:1);
  return -Math.max(-120,Math.min(120,pixels))*.0005;
}
export function bindWalkWheel({canvas,enabled,move}){
  const onWheel=event=>{
    if(!enabled())return;
    const delta=wheelHeightDelta(event,canvas.clientHeight||800);
    if(!delta)return;
    event.preventDefault();move(delta);
  };
  canvas.addEventListener('wheel',onWheel,{passive:false});
  return ()=>canvas.removeEventListener('wheel',onWheel);
}
