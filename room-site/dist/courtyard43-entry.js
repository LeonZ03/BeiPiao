// Keep legacy links usable, while normal room navigation shares one archive
// document and its in-memory room cache until an explicit page refresh.
if(window.parent===window){
  location.replace(new URL('./#courtyard43',location.href));
}else{
  await import('./courtyard43.js?v=quality19');
}
