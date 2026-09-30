// CPU-only validation of the published Blender pack. No temporary analysis file,
// Blender installation, browser or original private photograph is required.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {gunzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';

const root=fileURLToPath(new URL('../',import.meta.url));
const web=path.join(root,'room-site/dist');
const pack=path.join(web,'assets/rooms/Courtyard43/interior');
const manifest=JSON.parse(fs.readFileSync(path.join(pack,'scene.json'),'utf8'));
const approved=JSON.parse(fs.readFileSync(path.join(root,'rooms/Courtyard43/history/inputs/approved-layout.json'),'utf8'));
assert.equal(manifest.format,'blender-room-pack-1');
assert.equal(manifest.roomId,'Courtyard43');
assert.equal(manifest.stage,'interior');
assert.equal(manifest.structureApproved,true);
assert.equal(manifest.parentRevision,approved.parentRevision);
assert.match(manifest.revision,/^courtyard43-interior\d+$/);
assert.deepEqual(manifest.review,approved,'The final pack must retain approved layout provenance');
assert.match(approved.approval.baselineCommit,/^[a-f\d]{40}$/);
assert.ok(fs.existsSync(path.join(root,'rooms/Courtyard43/assets/full-room/Courtyard43-interior.blend')));
for(const component of ['architecture','furniture','props']){
  const directory=path.join(root,'rooms/Courtyard43/assets',component);
  assert.ok(fs.statSync(path.join(directory,`Courtyard43-${component}.blend`)).size>1000);
  assert.ok(fs.existsSync(path.join(root,`rooms/Courtyard43/scripts/build-${component}.py`)),`${component} remains reproducible`);
}
const localFile=url=>{
  assert.equal(typeof url,'string');
  assert.ok(url.startsWith('./assets/rooms/Courtyard43/interior/'),'Interior asset must remain isolated: '+url);
  const file=path.resolve(web,url);
  assert.ok(file.startsWith(pack+path.sep),'Asset path traversal: '+url);
  assert.ok(fs.existsSync(file),'Missing '+url);
  return file;
};
const bytes=fs.readFileSync(localFile(manifest.binary));
assert.deepEqual(gunzipSync(fs.readFileSync(localFile(manifest.compressedBinary))),bytes,'Raw and gzip belong to the same export');
const buffer=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const constructors={Float32Array,Uint32Array,Uint16Array,Int16Array};
function read(desc,label){
  assert.ok(desc&&constructors[desc.type],`Unknown binary attribute ${label}`);
  const Constructor=constructors[desc.type];
  assert.ok(Number.isInteger(desc.offset)&&desc.offset>=0&&desc.offset%Constructor.BYTES_PER_ELEMENT===0,`${label} aligned offset`);
  assert.ok(Number.isInteger(desc.length)&&desc.length>=0&&desc.offset+desc.length*Constructor.BYTES_PER_ELEMENT<=buffer.byteLength,`${label} buffer bounds`);
  assert.ok(Number.isInteger(desc.itemSize)&&desc.itemSize>0&&desc.length%desc.itemSize===0,`${label} item size`);
  const values=new Constructor(buffer,desc.offset,desc.length);
  for(const value of values)assert.ok(Number.isFinite(value),`${label} finite`);
  return values;
}
let triangles=0,vertices=0,morphMeshes=0,uv1Meshes=0;
const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
for(const [id,geometry] of manifest.geometries.entries()){
  assert.equal(geometry.id,id);
  const data={};
  for(const [name,desc] of Object.entries(geometry.attributes))data[name]=read(desc,`geometry ${id} ${name}`);
  for(const name of ['position','normal','uv'])assert.ok(data[name],`Missing ${name} on geometry ${id}`);
  const count=data.position.length/3;
  assert.equal(geometry.attributes.position.itemSize,3);
  assert.equal(data.normal.length,count*3);
  assert.equal(data.uv.length,count*2);
  if(data.uv1){assert.equal(data.uv1.length,count*2);uv1Meshes++;}
  for(let index=0;index<data.normal.length;index+=3)assert.ok(Math.abs(Math.hypot(...data.normal.subarray(index,index+3))-1)<.001,`Unit normal ${id}`);
  const indices=read(geometry.index,`geometry ${id} index`);
  assert.equal(indices.length%3,0);
  for(const index of indices)assert.ok(Number.isInteger(index)&&index>=0&&index<count,`Index range ${id}`);
  for(let index=0;index<indices.length;index+=3){
    a.fromArray(data.position,indices[index]*3);b.fromArray(data.position,indices[index+1]*3);c.fromArray(data.position,indices[index+2]*3);
    assert.ok(b.sub(a).cross(c.sub(a)).lengthSq()>1e-24,`Degenerate triangle ${id}:${index/3}`);
  }
  for(const group of geometry.groups){
    assert.ok(Number.isInteger(group.start)&&group.start>=0&&group.start%3===0);
    assert.ok(Number.isInteger(group.count)&&group.count>0&&group.count%3===0&&group.start+group.count<=indices.length);
  }
  if(geometry.morphTargets){
    morphMeshes++;
    assert.equal(geometry.morphTargets.position.length,geometry.morphTargets.normal.length);
    for(const [name,targets] of Object.entries(geometry.morphTargets))for(const [target,desc] of targets.entries()){
      const values=read(desc,`morph ${id}/${name}/${target}`);
      assert.equal(values.length,count*3,'Morph keeps evaluated topology');
      if(name==='normal')for(let i=0;i<values.length;i+=3)assert.ok(Math.abs(Math.hypot(...values.subarray(i,i+3))-1)<.001);
    }
  }
  vertices+=count;triangles+=indices.length/3;
}
assert.equal(triangles,manifest.statistics.triangles);
assert.equal(vertices,manifest.statistics.vertices);
assert.equal(manifest.geometries.length,manifest.statistics.meshes);
assert.ok(morphMeshes>=2,'Both curtain leaves must retain authored open/closed shapes');
assert.ok(uv1Meshes>0,'Secondary UV data must survive export');

const names=new Set();
for(const [id,node] of manifest.nodes.entries()){
  assert.equal(node.id,id);
  assert.ok(!names.has(node.name),'Stable unique node names: '+node.name);names.add(node.name);
  assert.equal(node.matrix.length,16);assert.ok(node.matrix.every(Number.isFinite));
  assert.ok(node.parent===-1||Number.isInteger(node.parent)&&node.parent>=0&&node.parent<manifest.nodes.length&&node.parent!==id,'Valid parent');
  const ancestors=new Set([id]);let parent=node.parent;
  while(parent>=0){assert.ok(!ancestors.has(parent),'No hierarchy cycles');ancestors.add(parent);parent=manifest.nodes[parent].parent;}
  if(node.type==='Mesh'){
    assert.ok(manifest.geometries[node.geometry]);
    const materials=Array.isArray(node.material)?node.material:[node.material];
    for(const material of materials)assert.ok(manifest.materials[material]);
    for(const group of manifest.geometries[node.geometry].groups)assert.ok(group.materialIndex<materials.length);
  }
}
for(const [id,texture] of manifest.textures.entries()){
  assert.equal(texture.id,id);localFile(texture.webPath);
  assert.ok(!/references|微信图片/.test(texture.webPath),'Do not publish private reference photographs');
  assert.ok([0,1].includes(texture.channel));
}
for(const [id,material] of manifest.materials.entries()){
  assert.equal(material.id,id);assert.ok(THREE[material.type]);
  for(const texture of Object.values(material.textures))assert.ok(manifest.textures[texture]);
  for(const values of Object.values(material.colors))assert.ok(values.every(Number.isFinite));
}
for(const [key,value] of Object.entries(manifest.refs))for(const id of Array.isArray(value)?value:[value])assert.ok(manifest.nodes[id],`Missing ${key} ref`);
const interactionIds=new Set();
for(const interaction of manifest.interactions){
  assert.ok(!interactionIds.has(interaction.id),'Interaction ids are unique');interactionIds.add(interaction.id);
  assert.ok(manifest.nodes[interaction.node]);
  assert.ok(['hinge','curtain','switch','lock'].includes(interaction.kind));
  assert.ok(['x','y','z'].includes(interaction.axis));
  if(interaction.kind==='hinge')assert.ok(Number.isFinite(interaction.openAngle)&&Math.abs(interaction.openAngle)>0&&Math.abs(interaction.openAngle)<=Math.PI);
}
for(const id of ['wardrobeFar','wardrobeNear','curtain-left','curtain-right','entry-door','entry-lock','ceiling-switch'])assert.ok(interactionIds.has(id),`Missing ${id}`);
assert.ok(!interactionIds.has('curtain'),'Actual curtain picking must have separate owners');
for(const m of manifest.materials.filter(m=>m.props.sheen>0))assert.ok(m.colors.sheenColor?.some(v=>v>0),'Nonzero cloth sheen must export a nonblack tint: '+m.name);
assert.equal(manifest.nodes.filter(n=>n.name==='C43_CeilingLamp_Diffuser').length,1,'Exactly one ceiling light');
assert.ok(!manifest.nodes.some(n=>n.name.startsWith('C43_Downlight_')),'No assumed perimeter lights');
for(const m of manifest.materials.filter(m=>m.textures.aoMap!==undefined))assert.equal(manifest.textures[m.textures.aoMap].channel,1,'Static contact map keeps a separate UV channel');
assert.ok(manifest.materials.filter(m=>m.textures.aoMap!==undefined).length>=3,'Large room surfaces have local occlusion');

const textures=manifest.textures.map(descriptor=>Object.assign(new THREE.Texture(),{channel:descriptor.channel}));
const {world,refs}=parseBlenderRoom(THREE,manifest,buffer,textures);
const byName=name=>{const object=world.getObjectByName(name);assert.ok(object,'Missing '+name);return object;};
const bounds=name=>new THREE.Box3().setFromObject(byName(name),true);
// The doorway backdrop must stay a closed, noninteractive background. Its
// floor meets the approved threshold and it must not seal the door aperture.
const corridor=byName('C43_ZCorridor');
assert.ok(refs.cutaway.includes(corridor),'Corridor hides in the existing room overview');
assert.equal(corridor.userData.explorable,false);
const secondary=manifest.nodes.filter(n=>n.userData.secondaryBedroom);
assert.equal(secondary.length,2);
for(const node of secondary){
  assert.equal(node.userData.openable,false);
  assert.ok(!manifest.interactions.some(i=>i.node===node.id),'Secondary bedrooms cannot open');
}
const corridorFloor=bounds('C43_ZCorridor_Floor');
assert.ok(Math.abs(corridorFloor.max.y)<.0001,'Corridor floor meets bedroom floor height');
assert.ok(Math.abs(corridorFloor.min.z-approved.room.depth)<.002,'No gap at the threshold');
const corridorRay=new THREE.Raycaster(new THREE.Vector3(1.48,1.4,approved.room.depth),new THREE.Vector3(0,0,1));
const corridorHits=corridorRay.intersectObject(corridor,true);
assert.ok(corridorHits.length&&corridorHits[0].distance>.9&&corridorHits[0].distance<2,'Door opens onto visible depth, not a near wall or void');
for(const material of manifest.materials.filter(m=>m.name?.startsWith('C43_ZCorridor'))){
  assert.equal(material.textures.aoMap,undefined,'Old bedroom contact AO must not be projected onto the corridor');
}
const fullCap=bounds('C43_Radiator_Cap_Front'),endPanel=bounds('C43_Radiator_Solid_Body');
assert.ok(fullCap.max.z-fullCap.min.z>.39,'Counter bridges the internal partition depth');
assert.ok(Math.abs(endPanel.min.y)<.0001&&Math.abs(endPanel.max.y-fullCap.min.y)<.0001,'Solid body joins floor and counter');
assert.ok(endPanel.max.x-endPanel.min.x>1.09&&endPanel.max.z-endPanel.min.z>.365,'Full-width, full-depth solid counter');
assert.ok(!world.getObjectByName('C43_Radiator_Inner_Shadow'),'No inferred black interior proxy');
const counterBody=byName('C43_Radiator_Solid_Body'),bodyRay=new THREE.Raycaster();
for(const x of [.34,.84,1.34])for(const y of [.06,.45,.90])for(const [z,direction,expected] of [[-.6,1,-.12],[.6,-1,y<.125?.246:.221]]){
  bodyRay.set(new THREE.Vector3(x,y,z),new THREE.Vector3(0,0,direction));
  const hits=bodyRay.intersectObject(counterBody,false);
  assert.ok(hits.length&&Math.abs(hits[0].point.z-expected)<.0002,'Solid counter has continuous front and balcony faces');
}
assert.ok(fullCap.max.y-fullCap.min.y<.027,'Counter cap has a thin manufactured edge');
const facadeTargets=['C43_Radiator_Solid_Body','C43_Radiator_White_Vertical_Grille'].map(byName);
for(const y of [.20,.56,.91]){
  const frontAt=x=>{bodyRay.set(new THREE.Vector3(x,y,.6),new THREE.Vector3(0,0,-1));return bodyRay.intersectObjects(facadeTargets,false)[0]?.point.z;};
  assert.ok(frontAt(.84)-frontAt(.852925)>.04,'Each grille field has real recessed slots between distinct ribs');
}
for(const id of [0,1]){
  const band=bounds(`C43_Radiator_Teal_Crossbar_${id}`);
  assert.ok(band.min.x>endPanel.min.x+.02&&band.max.x<endPanel.max.x-.02,'Blue band sits within side frame');
  assert.ok(band.max.z<.268&&band.max.y-band.min.y>.15,'Wide blue panel is inset, not a projecting bar');
}
for(const side of ['Left','Right']){
  const root=byName(`C43_Curtain_${side}_Pivot`);
  for(const suffix of ['','_Rings'])assert.equal(byName(`C43_Curtain_${side}${suffix}`).parent,root,'Panel and rings have independent correct owner');
}
assert.ok(bounds('C43_Curtain_Right').min.y>=fullCap.max.y,'Right hem clears complete counter');
assert.ok(bounds('C43_Curtain_Left').max.x<endPanel.min.x,'Long left panel clears counter side');
const near=(actual,expected,label,tolerance=.00002)=>assert.ok(Math.abs(actual-expected)<=tolerance,`${label}: ${actual} != ${expected}`);
const left=(approved.room.centerX??0)-approved.room.width/2,right=(approved.room.centerX??0)+approved.room.width/2;
const bed=bounds('C43_BedPlatform'),mattress=bounds('C43_Mattress'),desk=bounds('C43_DeskTop');
near(bed.min.x,left+.06,'Bed head anchor');near(bed.max.x,left+.06+approved.bed.length,'Bed foot anchor');
near(bed.min.z,approved.bed.centerZ-approved.bed.width/2,'Bed near edge');near(bed.max.z,approved.bed.centerZ+approved.bed.width/2,'Bed far edge');
near(mattress.min.y,bed.max.y,'Mattress contacts supporting platform');
near(desk.min.x,left+.025,'Desk left anchor');near(desk.max.x,left+.025+approved.desk.width,'Desk right anchor');
near(desk.max.y,approved.desk.height,'Desk top height');near(desk.max.z-desk.min.z,approved.desk.depth,'Desk depth');
assert.ok(desk.max.x<approved.balcony.openingLeft,'Desk stays clear of balcony passage');
// User-marked working edge is concave at the chair, not a convex board.
const deskObject=byName('C43_DeskTop'),deskPosition=deskObject.geometry.attributes.position;
const deskPoints=Array.from({length:deskPosition.count},(_,i)=>new THREE.Vector3().fromBufferAttribute(deskPosition,i).applyMatrix4(deskObject.matrixWorld));
const frontAt=x=>Math.max(...deskPoints.filter(p=>Math.abs(p.x-x)<.004&&p.y>.735).map(p=>p.z));
near(frontAt(-1.35),.50,'Concave working edge at seated center',.003);
near(frontAt(-1.965),.58,'Left shoulder retains desk depth',.003);
near(frontAt(-.735),.58,'Right shoulder retains desk depth',.003);
// Dark plinth caps must be enclosed by the white returns. Previously both
// colours occupied x=.29 and z=.262, producing camera-dependent flicker.
const grille=byName('C43_Radiator_White_Vertical_Grille'),gg=grille.geometry;
const grilleNode=manifest.nodes.find(n=>n.name===grille.name);
const darkSlots=grilleNode.material.map((id,i)=>manifest.materials[id].name.includes('Dark_red_brown_skirt')?i:-1).filter(i=>i>=0);
assert.equal(darkSlots.length,1,'The grille keeps its original dark plinth material');
const plinthPoints=[];
for(const group of gg.groups.filter(g=>darkSlots.includes(g.materialIndex)))for(let i=group.start;i<group.start+group.count;i++)plinthPoints.push(new THREE.Vector3().fromBufferAttribute(gg.attributes.position,gg.index.getX(i)).applyMatrix4(grille.matrixWorld));
assert.ok(plinthPoints.length>0,'Audited plinth geometry exists');
const plinthBounds=new THREE.Box3().setFromPoints(plinthPoints);
assert.ok(plinthBounds.min.x>.311&&plinthBounds.max.x<1.369,'Plinth end faces lie inside both side boards');
assert.ok(plinthBounds.max.z<.257,'Plinth front has a real reveal from the white return');
const nearSide=bounds('C43_WardrobeNearSide'),farSide=bounds('C43_WardrobeFarSide');
near(nearSide.max.x,right,'Wardrobe right anchor');near(nearSide.min.x,right-approved.wardrobe.depth,'Wardrobe front anchor');
near(nearSide.max.z,approved.wardrobe.centerZ+approved.wardrobe.width/2,'Wardrobe near end');
near(farSide.min.z,approved.wardrobe.centerZ-approved.wardrobe.width/2,'Wardrobe far end');
near(nearSide.max.y,approved.wardrobe.height,'Wardrobe height');
const chair=bounds('C43_ChairBlackCushion'),chairBack=bounds('C43_ChairWhiteCurvedBack');
assert.ok(chair.getCenter(new THREE.Vector3()).z>desk.max.z&&chairBack.getCenter(new THREE.Vector3()).z>chair.getCenter(new THREE.Vector3()).z,'Chair faces the desk, its back faces the bed');
assert.ok(chairBack.max.z<bed.min.z,'Chair clears bed');
assert.equal(manifest.nodes.filter(node=>node.name==='C43_DeskChair').length,1);
assert.ok(!manifest.nodes.some(node=>/spare.?chair/i.test(node.name)),'Keep the entrance free of a spare chair');
for(const name of [...names].filter(name=>/^C43_(BedFootCap|DeskFoot|ChairRubberFoot)/.test(name)))near(bounds(name).min.y,0,'Ground contact '+name);
const pillow=bounds('C43_CottonPillow'),sheet=bounds('C43_DrapedWhiteSheet'),duvet=bounds('C43_FloralDuvet');
// Small objects must share actual world-space support after source transforms.
const bottle=bounds('C43_Ribbed_water_bottle'),bottleCap=bounds('C43_Bottle_cap'),cup=bounds('C43_Plastic_cup'),packet=bounds('C43_Tissue_packet');
for(const [name,box] of [['bottle',bottle],['cup',cup],['tissue packet',packet]])near(box.min.y,fullCap.max.y,name+' rests on the counter',.0005);
near(bottle.getCenter(new THREE.Vector3()).x,bottleCap.getCenter(new THREE.Vector3()).x,'Bottle cap remains concentric after relocation',.001);
assert.ok(bottleCap.min.y<bottle.max.y&&bottleCap.max.y>bottle.max.y,'Cap physically overlaps the bottle neck');
assert.ok(bottle.max.x<cup.min.x&&cup.max.x<packet.min.x,'Photo-supported bottle, cup, packet order');
for(const name of ['C43_Tissue_0','C43_Tissue_1'])near(bounds(name).min.y,packet.max.y,'Paper emerges from packet opening',.001);
assert.ok(byName('C43_Plastic_cup').material.opacity>=.15&&byName('C43_Plastic_cup').material.opacity<.35&&!byName('C43_Plastic_cup').material.depthWrite,'Cup has readable translucent walls without opaque depth occlusion');
assert.ok(byName('C43_Floor_RedBrown_Boards').material.roughnessMap,'Timber finish has restrained spatial roughness');
assert.ok(byName('C43_Floor_RedBrown_Boards').geometry.attributes.uv1,'Floor contact bake UV1 survives finish changes');
assert.ok(!names.has('C43_Bottle_label_band'),'Label colours share one surface, without near-coplanar overlay');
assert.ok(pillow.min.y>=sheet.max.y-.001&&pillow.min.y-sheet.max.y<.003,'Pillow rests on the sheet');
assert.ok(sheet.min.y>0&&duvet.min.y>0,'Bed linen remains above the floor');
// Local quilt accumulations may be as high as the pillow; judge the pillow's
// own loft/support instead of forcing every quilt fold below its top.
assert.ok(pillow.max.y-pillow.min.y>.10&&pillow.max.y-pillow.min.y<.18,'Pillow keeps a soft, bounded loft');
assert.ok(duvet.max.y-sheet.max.y>.09,'Quilt has a visible local accumulation above its supporting sheet');
for(const name of ['C43_FloralDuvet','C43_DrapedWhiteSheet','C43_CottonPillow']){
  const object=byName(name);assert.ok(object.geometry.attributes.uv1,`Cotton UV1 preserved: ${name}`);
  assert.ok(object.material.bumpMap?.isTexture,'Cotton thread relief retained');
}

// Exercise exact authored door triangles against the fixed carcass and enlarged
// radiator cap. AABB-of-door tests would falsely reject ordinary angled doors.
const cap=bounds('C43_Radiator_Cap_Front').expandByScalar(.02);
const wardrobeObstacles=['C43_WardrobeFarSide','C43_WardrobeNearSide','C43_WardrobeBase','C43_WardrobeTop','C43_WardrobeShelf','C43_WardrobeBack'].map(bounds);
const hinges=['wardrobeFar','wardrobeNear'].map(id=>manifest.interactions.find(item=>item.id===id));
const pivots=hinges.map(item=>byName(manifest.nodes[item.node].name));
const doors=['C43_WardrobeDoorFar','C43_WardrobeDoorNear'].map(byName);
const triangle=new THREE.Triangle();
for(let step=0;step<=24;step++){
  hinges.forEach((hinge,index)=>{pivots[index].rotation[hinge.axis]=hinge.openAngle*step/24;});world.updateMatrixWorld(true);
  for(const door of doors){
    const position=door.geometry.attributes.position,index=door.geometry.index;
    for(let i=0;i<index.count;i+=3){
      triangle.a.fromBufferAttribute(position,index.getX(i)).applyMatrix4(door.matrixWorld);
      triangle.b.fromBufferAttribute(position,index.getX(i+1)).applyMatrix4(door.matrixWorld);
      triangle.c.fromBufferAttribute(position,index.getX(i+2)).applyMatrix4(door.matrixWorld);
      assert.ok(!cap.intersectsTriangle(triangle),`Door retains 20 mm cap margin: ${door.name} amount ${step}/24`);
      for(const obstacle of wardrobeObstacles)assert.ok(!obstacle.intersectsTriangle(triangle),`Door clears carcass: ${door.name} amount ${step}/24`);
    }
  }
}
pivots.forEach(pivot=>pivot.rotation.y=0);world.updateMatrixWorld(true);
for(const object of refs.curtainPanels){
  assert.ok(object.morphTargetInfluences?.length,'Curtain panel/ring retains its authored morph');
  const initialWidth=new THREE.Box3().setFromObject(object,true).getSize(new THREE.Vector3()).x;
  for(const amount of Array.from({length:21},(_,i)=>i/20)){
    object.morphTargetInfluences[0]=amount;
    const box=new THREE.Box3().setFromObject(object,true);
    assert.ok([...box.min,...box.max].every(Number.isFinite),'Finite intermediate curtain state');
    assert.ok(box.min.y>=0&&box.max.z<.12,'Curtain clears floor and radiator cover');
    if(!object.userData.curtainRings){
      const support=object.name.includes('Left')?.044:fullCap.max.y;
      assert.ok(box.min.y>=support&&box.min.y-support<.01,'Hem stays close to its support throughout opening');
      assert.ok(object.geometry.attributes.uv1,'Sewn transmission mask uses normalized secondary UVs');
      assert.ok(!object.material.emissiveMap,'Blackout cloth does not use a transmission mask');assert.equal(object.material.emissiveIntensity,0);
      assert.equal(object.material.transparent,false,'Heavy grey curtain does not become transparent gauze');
    }
  }
  const openWidth=new THREE.Box3().setFromObject(object,true).getSize(new THREE.Vector3()).x;
  assert.ok(openWidth<initialWidth*.5,'Curtain gathers without disappearing');
  object.morphTargetInfluences[0]=0;
}
console.log(`PASS Courtyard43 interior: ${manifest.statistics.meshes} meshes, ${triangles} triangles; finite PBR/UV/UV1/morph/index/gzip, fixed approved anchors, furniture contact, 25-state door clearance and 21-state curtain support checks.`);
