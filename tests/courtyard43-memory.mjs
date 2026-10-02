// CPU-only checks for the memory12 exported pack: transparency, fabric finish,
// continuous entrance-wall joins, and the door-frame envelope.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
import * as THREE from '../room-site/dist/vendor/three.module.js';

const root=fileURLToPath(new URL('../',import.meta.url));
const pack=path.join(root,'room-site/dist/assets/rooms/Courtyard43/interior');
const manifest=JSON.parse(fs.readFileSync(path.join(pack,'scene.json'),'utf8'));
const buffer=fs.readFileSync(path.join(pack,'geometry.bin'));
assert.equal(manifest.format,'blender-room-pack-1');
assert.ok(['courtyard43-interior12','courtyard43-interior13','courtyard43-interior14','courtyard43-interior15','courtyard43-interior16','courtyard43-interior17','courtyard43-interior18','courtyard43-interior19','courtyard43-interior20','courtyard43-interior21','courtyard43-interior22'].includes(manifest.revision));
const nodes=new Map(manifest.nodes.map(node=>[node.name,node]));
const byName=name=>{const node=nodes.get(name);assert.ok(node,'Missing '+name);return node;};
const materialFor=node=>manifest.materials[Array.isArray(node.material)?node.material[0]:node.material];
const bounds=node=>{
  const descriptor=manifest.geometries[node.geometry],position=descriptor.attributes.position;
  const values=new Float32Array(buffer.buffer,buffer.byteOffset+position.offset,position.length);
  const matrix=new THREE.Matrix4().fromArray(node.matrix),box=new THREE.Box3();
  for(let i=0;i<position.length;i+=position.itemSize)box.expandByPoint(new THREE.Vector3().fromArray(values,i).applyMatrix4(matrix));
  return box;
};
const overlap=(a,b,axis)=>Math.min(a.max[axis],b.max[axis])-Math.max(a.min[axis],b.min[axis]);
const approx=(actual,expected,tolerance,label)=>assert.ok(Math.abs(actual-expected)<=tolerance,`${label}: ${actual} differs from ${expected}`);

// The privacy panels are opaque rendered surfaces. Their reed texture remains
// in the material while the actual panes populate depth for following objects.
for(const name of ['C43_Partition_Frosted_Plant_Panel_0.465','C43_Partition_Frosted_Plant_Panel_1.225']){
  const panel=byName(name),material=materialFor(panel),props=material.props;
  assert.equal(material.userData.opaquePrivacyScreen,true,`${name} is the exported privacy screen`);
  assert.equal(props.transparent,false,`${name} is not alpha blended`);
  assert.equal(props.opacity,1,`${name} keeps full opacity`);
  assert.equal(props.depthWrite,true,`${name} writes depth to occlude the room correctly`);
}

// Both blackout panels use dense, low-specular cloth rather than gauze.
for(const side of ['Left','Right']){
  const curtain=byName(`C43_Curtain_${side}`),material=materialFor(curtain),props=material.props;
  assert.equal(props.transparent,false,`${side} blackout curtain is opaque`);
  assert.equal(props.depthWrite,true,`${side} curtain writes its depth`);
  assert.ok(props.roughness>=.95,`${side} curtain retains broad matte reflection`);
  assert.ok(props.specularIntensity<=.2,`${side} cloth avoids a bright specular lobe`);
  assert.equal(props.metalness,0,`${side} cloth is not metallic`);
  assert.ok(material.userData.surfaceFinish.includes('matte blackout woven cloth'));
}

// All three wall pieces around the entry use one plaster material. The
// continuous jamb/header overlap that wall slightly, so no edge opens into a
// bright bevel seam from a grazing view.
const entryNames=['C43_Wall_Entry_Header','C43_Wall_Entry_Left','C43_Wall_Entry_Right'];
const entryNodes=entryNames.map(name=>manifest.nodes.find(node=>node.name===name));
assert.ok(entryNodes.every(Boolean),'All three doorway wall pieces are exported');
assert.equal(new Set(entryNodes.map(node=>node.material)).size,1,'Entry header and side walls share one plaster material');

const leftBounds=bounds(byName('C43_Door_Jamb')),rightBounds=bounds(byName('C43_Door_Jamb.001')),headerBounds=bounds(byName('C43_Door_Jamb_Header'));
const size=box=>box.getSize(new THREE.Vector3());
const leftSize=size(leftBounds),rightSize=size(rightBounds),headerSize=size(headerBounds);
approx(leftSize.x,.044,.006,'Left door-frame jamb width');
approx(rightSize.x,.044,.006,'Right door-frame jamb width');
approx(leftSize.y,2.091,.02,'Left door-frame jamb height');
approx(rightSize.y,2.091,.02,'Right door-frame jamb height');
approx(headerSize.x,.926,.015,'Door-frame header span');
approx(headerSize.y,.04,.01,'Door-frame header thickness');
approx(headerSize.z,.142,.012,'Door-frame depth');
assert.ok(leftBounds.min.y>=-.002&&leftBounds.max.y<2.11,'Jambs sit on the floor and stay below the header');
assert.ok(headerBounds.min.y>2.08&&headerBounds.max.y<2.15,'Frame header fits the doorway head');

const leftWall=bounds(byName('C43_Wall_Entry_Left'));
const rightWall=bounds(byName('C43_Wall_Entry_Right'));
const entryHeader=bounds(byName('C43_Wall_Entry_Header'));
assert.ok(overlap(leftBounds,leftWall,'x')>.025,'Left jamb overlaps the side wall, leaving no edge seam');
assert.ok(overlap(rightBounds,rightWall,'x')>.025,'Right jamb overlaps the side wall, leaving no edge seam');
assert.ok(overlap(headerBounds,entryHeader,'y')>.025,'Frame header overlaps the entry wall header, leaving no chamfer gap');
for(const [frame,wall,label] of [[leftBounds,leftWall,'left jamb'],[rightBounds,rightWall,'right jamb'],[headerBounds,entryHeader,'frame header']])
  assert.ok(overlap(frame,wall,'z')>.1,`${label} shares the wall thickness`);

// Sample the complete hinge stroke. Compose the hinge's ancestor transform,
// animated hinge rotation and leaf-local transform before testing triangles;
// using only the leaf's local matrix would miss its 1.885 m pivot offset.
const entryDoor=manifest.interactions.find(item=>item.id==='entry-door');
assert.ok(entryDoor,'Entry door hinge interaction is exported');
const leaf=byName('C43_Door_Leaf'),hinge=manifest.nodes[entryDoor.node];
assert.equal(leaf.parent,hinge.id,'Door leaf is a child of its hinge pivot');
const localMatrix=node=>new THREE.Matrix4().fromArray(node.matrix);
const parentWorldMatrix=index=>{
  const node=manifest.nodes[index],local=localMatrix(node);
  return node.parent<0?local:parentWorldMatrix(node.parent).multiply(local);
};
const hingeBase=new THREE.Object3D();hingeBase.matrix.copy(localMatrix(hinge));hingeBase.matrix.decompose(hingeBase.position,hingeBase.quaternion,hingeBase.scale);
const hingeParentWorld=hinge.parent<0?new THREE.Matrix4():parentWorldMatrix(hinge.parent);
const blockers=['C43_Door_Jamb','C43_Door_Jamb.001','C43_Door_Jamb_Header','C43_Wall_Entry_Header','C43_Wall_Entry_Left','C43_Wall_Entry_Right'].map(name=>({name,node:byName(name),box:bounds(byName(name))}));
const leafGeometry=manifest.geometries[leaf.geometry],leafPosition=leafGeometry.attributes.position;
const leafVertices=new Float32Array(buffer.buffer,buffer.byteOffset+leafPosition.offset,leafPosition.length);
const leafIndex=new Uint32Array(buffer.buffer,buffer.byteOffset+leafGeometry.index.offset,leafGeometry.index.length);
const leafLocal=localMatrix(leaf),axis=new THREE.Vector3(0,1,0),triangle=new THREE.Triangle();
for(let step=0;step<=40;step++){
  const amount=step/40;
  localMatrix(hinge).decompose(hingeBase.position,hingeBase.quaternion,hingeBase.scale);
  hingeBase.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(axis,entryDoor.openAngle*amount));
  hingeBase.updateMatrix();
  const leafWorld=hingeParentWorld.clone().multiply(hingeBase.matrix).multiply(leafLocal);
  for(let i=0;i<leafIndex.length;i+=3){
    const point=index=>new THREE.Vector3().fromArray(leafVertices,index*leafPosition.itemSize).applyMatrix4(leafWorld);
    triangle.set(point(leafIndex[i]),point(leafIndex[i+1]),point(leafIndex[i+2]));
    for(const blocker of blockers)
      assert.ok(!triangle.intersectsBox(blocker.box),`Door leaf clears ${blocker.name} at opening amount ${amount.toFixed(2)}`);
  }
}

console.log('Courtyard43 memory12 screen depth, matte curtains, entry-wall joins and frame bounds passed.');
