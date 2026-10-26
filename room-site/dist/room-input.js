// Fn is only available when the keyboard/OS forwards it to the browser.
// Arrow keys provide ordinary-key height controls; touch has separate held keys.
const movementCodes=new Set(['KeyW','KeyA','KeyS','KeyD','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight']);
export function movementKey(event){
  if(event.key==='Fn'||event.code==='Fn')return 'Fn';
  if(event.code==='ArrowUp')return 'MoveUp';
  if(event.code==='ArrowDown')return 'MoveDown';
  return movementCodes.has(event.code)?event.code:null;
}
export function releaseMovementKey(event){
  return movementKey(event);
}
export const touchMovementKeys=Object.freeze({forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD',up:'TouchMoveUp',down:'TouchMoveDown'});
export function verticalMovement(keys){
  return Number(keys.has('ShiftLeft')||keys.has('ShiftRight')||keys.has('MoveUp')||keys.has('TouchMoveUp'))-Number(keys.has('Fn')||keys.has('MoveDown')||keys.has('TouchMoveDown'));
}
