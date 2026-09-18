import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'..');
const source=fs.readFileSync(path.join(root,'tools/reference-scene.source.js'),'utf8');
const init=source.slice(source.indexOf('const $ ='),source.indexOf('const world=new THREE.Group();'));
const suffix=source.slice(source.indexOf('const orbit=new OrbitControls'));
const main=`import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {createAfternoon} from './afternoon.js?v=blender18';
import {installSoftSunShadows,createSoftDaylight} from './soft-daylight.js?v=blender18';
import {createFlyNavigation,batchStaticGeometry} from './navigation.js?v=blender18';
import {createInteractions} from './interactions.js?v=blender18';
import {loadBlenderRoom} from './blender-room.js?v=blender18';

${init}
let renderSignature='';
const manager=new THREE.LoadingManager();
let roomAsset;
try {roomAsset=await loadBlenderRoom(THREE,manager);}
catch(error){$('loading').hidden=true;$('error').hidden=false;throw error;}
const {world,materials,statistics:assetStatistics}=roomAsset;
const {outside,curtain,curtainPanels,curtainRings,diffuser,cutaway,ceilings}=roomAsset.refs;
scene.add(world);
const indirectMaterials=materials.filter(m=>m.userData.bakedIndirect);
const updateIndirect=amount=>indirectMaterials.forEach(m=>m.lightMapIntensity=.24+.22*amount);
const {windowLight,sun}=createAfternoon({THREE,scene,renderer,world});
const daylight=createSoftDaylight({THREE,renderer,scene,camera,sun});
const lamp=new THREE.PointLight('#ffdca5',0,6,2);lamp.position.set(0,2.35,.05);scene.add(lamp);
const bathLight=new THREE.PointLight('#f0f5ed',3,4,2);bathLight.position.set(-.55,2.30,2.48);scene.add(bathLight);
const navigation=createFlyNavigation(THREE,world,[outside,curtain]);
const batchedMeshes=batchStaticGeometry(THREE,world,[curtain,...cutaway,...ceilings]);
renderer.shadowMap.needsUpdate=true;
$('loading').hidden=true;
${suffix}`;
fs.writeFileSync(path.join(root,'dist/main.js'),main.replace('batchedMeshes,water:interactions.state','batchedMeshes,assetStatistics,water:interactions.state'));
for(const name of fs.readdirSync(path.join(root,'dist'))){if(!/\.(js|html|css)$/.test(name))continue;const file=path.join(root,'dist',name),s=fs.readFileSync(file,'utf8');if(s.includes('detail17'))fs.writeFileSync(file,s.replaceAll('detail17','blender18'));}
console.log('Web entrypoint now loads only the Blender model pack and real-time effects.');
