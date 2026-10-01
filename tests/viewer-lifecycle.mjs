// Route races and fullscreen ownership, without a browser or WebGL.
import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const source=fs.readFileSync(new URL('../room-site/dist/archive.js',import.meta.url),'utf8');
const elements=new Map(),events=new Map(),entered=[];
let imports=0,starts=0,pauses=0,exits=0,finishImport,finishExit;
const messages=[],frameEvents=new Map();let frameLoads=0;
const el=id=>{if(!elements.has(id))elements.set(id,{hidden:id==='app'||id==='courtyardRoom',addEventListener(n,f){if(id==='courtyardRoom')frameEvents.set(n,f);},contentWindow:{postMessage:(...args)=>messages.push(args)},set src(v){this.source=v;if(id==='courtyardRoom')frameLoads++;},get src(){return this.source;},close(){},focus(){},showModal(){}});return elements.get(id);};
const roomChoices=['yongwang-jiayuan','Courtyard43','yongwang-jiayuan','Courtyard43'].map(id=>({dataset:{roomSelect:id},setAttribute(name,value){this[name]=value;},addEventListener(){},closest(){return {classList:{toggle(){}}};}}));
const doc={getElementById:el,querySelectorAll:()=>roomChoices,fullscreenElement:null,title:'',exitFullscreen:()=>{exits++;return new Promise(resolve=>finishExit=()=>{doc.fullscreenElement=null;resolve();});}};
const location={hash:'',origin:'https://room.example'};
const context=vm.createContext({document:doc,location,window:{addEventListener:(n,f)=>events.set(n,f)},console});
const loader=new vm.SyntheticModule(['startRoomLoading','failRoomLoading'],function(){this.setExport('startRoomLoading',()=>starts++);this.setExport('failRoomLoading',()=>{throw Error('Unexpected load error');});},{context});
const room=new vm.SyntheticModule(['enterRoom','pauseRoom'],function(){this.setExport('enterRoom',v=>entered.push(v));this.setExport('pauseRoom',()=>pauses++);},{context});
await room.link(()=>{});await room.evaluate();
const archive=new vm.SourceTextModule(source,{context,importModuleDynamically:()=>{imports++;return new Promise(resolve=>finishImport=()=>resolve(room));}});
await archive.link(()=>loader);await archive.evaluate();
const navigate=hash=>{location.hash=hash;return events.get('hashchange')();};
assert.equal(el('app').hidden,true);
const first=navigate('#room');assert.equal(starts,1);assert.equal(el('archive').hidden,true);
await navigate('#');finishImport();await first;
assert.deepEqual(entered,[],'Canceled first load must not re-enter the room');
assert.equal(el('archive').hidden,false);
await navigate('#room');assert.deepEqual(entered,['walk']);assert.equal(imports,1);
// Document-wide fullscreen survives a round trip and doesn't cover the archive.
doc.fullscreenElement={tagName:'HTML'};
await navigate('#');assert.equal(el('app').hidden,true);assert.equal(el('archive').hidden,false);assert.equal(exits,0);
await navigate('#room');assert.equal(el('app').hidden,false);assert.equal(entered.length,2);assert.equal(starts,1);
// Previously app-owned fullscreen must exit before that app can be hidden.
doc.fullscreenElement=el('app');const home=navigate('#');
assert.equal(el('app').hidden,false);assert.equal(exits,1);finishExit();await home;
assert.equal(el('app').hidden,true);assert.equal(el('archive').hidden,false);
await navigate('#overview');assert.equal(entered.at(-1),'overview');
// A later route wins if fullscreen exit finishes after a new entry.
doc.fullscreenElement=el('app');const oldHome=navigate('#');
await navigate('#room');finishExit();await oldHome;
assert.equal(el('app').hidden,false);assert.equal(el('archive').hidden,true);
assert.ok(pauses>=3);
await navigate('#courtyard43');assert.equal(frameLoads,1);assert.equal(el('app').hidden,true);assert.equal(doc.title,'43号院 · 北漂');
const cachedFrame=el('courtyardRoom');assert.equal(cachedFrame.src,'./courtyard43.html?embedded=1&v=photo17','Courtyard iframe requests the current homepage cache version');frameEvents.get('load')();assert.equal(messages.at(-1)[0].active,true);
await navigate('#');assert.equal(cachedFrame.hidden,true);assert.equal(messages.at(-1)[0].active,false);
await navigate('#courtyard43');assert.equal(frameLoads,1,'Re-entry never resets the cached frame src');assert.equal(messages.at(-1)[0].active,true);
await navigate('#room');assert.equal(imports,1,'Returning from another room reuses Yongwang module and GPU scene');assert.equal(starts,1);
await navigate('#courtyard43');
events.get('message')({origin:'https://evil.example',source:cachedFrame.contentWindow,data:{type:'beipiao-room-home'}});assert.equal(location.hash,'#courtyard43');
events.get('message')({origin:location.origin,source:{},data:{type:'beipiao-room-home'}});assert.equal(location.hash,'#courtyard43');
events.get('message')({origin:location.origin,source:cachedFrame.contentWindow,data:{type:'beipiao-room-home'}});assert.equal(location.hash,'#');
doc.fullscreenElement=cachedFrame;const childHome=navigate('#');assert.equal(cachedFrame.hidden,false);finishExit();await childHome;assert.equal(cachedFrame.hidden,true);
await navigate('#courtyard43');assert.equal(frameLoads,1);assert.equal(el('archive').hidden,true);
// Loading completes after leaving: the onload handshake must stay paused.
await navigate('#');frameEvents.get('load')();assert.equal(messages.at(-1)[0].active,false);
console.log('First-load cancellation, cached re-entry, fullscreen round trip, legacy fullscreen exit and route races passed.');
