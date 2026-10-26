// Focused exported-asset checks: hanging rackets, cabinet plinth and 86 rockers.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
const web=new URL('../room-site/dist/',import.meta.url);
function load(path){
  const dir=new URL(path,web),m=JSON.parse(fs.readFileSync(new URL('scene.json',dir))),b=fs.readFileSync(new URL('geometry.bin',dir));
  assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',dir))),b,'Same-export compressed and raw binary');
  const textures=m.textures.map(t=>{assert.ok(fs.existsSync(new URL(t.webPath,web)));return new THREE.Texture();});
  const parsed=parseBlenderRoom(THREE,m,b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),textures);
  return {m,...parsed};
}
const yw=load('assets/full-room/'),c43=load('assets/rooms/Courtyard43/interior/');
const targets=[];
for(const [prefix,parent] of [['Clash44',824],['Radical44',811]]){
  const nodes=yw.m.nodes.filter(n=>n.name.startsWith(prefix));assert.ok(nodes.length>=10);
  for(const n of nodes){assert.equal(n.parent,parent);assert.equal(n.visible,true);targets.push(yw.world.getObjectByName(n.name));}
}
for(const id of [823,836])assert.equal(yw.m.nodes[id].visible,false,'Old block hook retired');
assert.equal(yw.m.nodes[781].material,yw.m.nodes[773].material,'Visible cabinet base uses same veneer as fixed side');
if(yw.m.statistics.exteriorRefinement?.props45){
  const report=yw.m.statistics.exteriorRefinement.props45;
  assert.ok(report.frameFrontWidthM<.015,'Slim frontal frame section');
  assert.ok(report.surfacePrint.length>=6,'Visible frame prints follow their source surface');
  assert.equal(yw.m.nodes[1483].matrix[12],Math.fround(yw.m.statistics.exteriorRefinement?.switch31?.rockerCenterX??1.387),'Export matches the current authored switch origin');
  const a=yw.world.getObjectByName('light-switch-rocker'),b=c43.world.getObjectByName('C43_Switch_Rocker');
  const bounds=o=>new THREE.Box3().setFromBufferAttribute(o.geometry.attributes.position).getSize(new THREE.Vector3());
  assert.ok(bounds(a).distanceTo(bounds(b))<1e-7,'Reused switch has the same geometry size');
  assert.ok(a.material.color.toArray().every((v,i)=>Math.abs(v-b.material.color.toArray()[i])<1e-7),'Reused switch base color');
  for(let id=1070;id<=1077;id++)yw.world.traverse(o=>{if(o.isMesh&&o.geometry.userData.blenderGeometry===yw.m.nodes[id].geometry)targets.push(o);});
  for(let id=1078;id<1096;id++)assert.equal(yw.m.nodes[id].visible,false,'Old disconnected tuft pieces retired');
  for(const name of ['C43_WardrobeFarMirror_Reflection','C43_WardrobeFarMirror_Edge']){
    const n=c43.m.nodes.find(n=>n.name===name);assert.ok(n);assert.equal(c43.m.nodes[n.parent].name,'C43_WardrobeDoorFarPivot');
    assert.equal(n.userData.noCollision,true);assert.equal(n.castShadow,false);targets.push(c43.world.getObjectByName(name));
  }
}
for(const root of [yw.world,c43.world]){
  const rocker=root.getObjectByName(root===yw.world?'light-switch-rocker':'C43_Switch_Rocker');assert.ok(rocker);targets.push(rocker);
  const box=new THREE.Box3().setFromBufferAttribute(rocker.geometry.attributes.position),size=box.getSize(new THREE.Vector3());
  assert.ok(size.x<.008&&size.y>.060&&size.z>.060,'Broad rocker with a closed rear skirt');
  const travel=yw.m.statistics.exteriorRefinement?.switch31?.angle??.13;
  for(let i=0;i<=20;i++){const angle=travel*i/20,q=new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),angle);const points=[];for(let x of [box.min.x,box.max.x])for(let y of [box.min.y,box.max.y])for(let z of [box.min.z,box.max.z])points.push(new THREE.Vector3(x,y,z).applyQuaternion(q));assert.ok(points.every(p=>Math.abs(p.x)<.007),'Rocker travel remains inside shallow housing');}
}
if(yw.m.statistics.exteriorRefinement?.switch31){
  const closed=o=>{
    const p=o.geometry.attributes.position,idx=o.geometry.index.array,edges=new Map();
    const key=i=>[p.getX(i),p.getY(i),p.getZ(i)].map(v=>Math.round(v*1e9)).join(',');
    for(let i=0;i<idx.length;i+=3)for(const [a,b]of [[idx[i],idx[i+1]],[idx[i+1],idx[i+2]],[idx[i+2],idx[i]]]){
      const ka=key(a),kb=key(b);assert.notEqual(ka,kb,'No collapsed exported triangle edge');
      const edge=ka<kb?ka+'|'+kb:kb+'|'+ka;edges.set(edge,(edges.get(edge)||0)+1);
    }
    assert.ok([...edges.values()].every(n=>n===2),'Every welded edge has exactly two faces: no open shell');
  };
  for(const [root,plateName,rockerName,wall]of [[yw.world,'wall-switch-86-frame','light-switch-rocker',1.4],[c43.world,'C43_Switch_Backplate','C43_Switch_Rocker',2.225]]){
    const plate=root.getObjectByName(plateName),rocker=root.getObjectByName(rockerName);closed(plate);closed(rocker);
    const box=new THREE.Box3().setFromObject(plate);assert.ok(box.max.x>wall&&box.max.x-wall<.0006,'Closed rear seats into wall without a visible air gap');
    const center=new THREE.Vector3();plate.getWorldPosition(center);
    const ray=new THREE.Raycaster(new THREE.Vector3(wall-.02,center.y+.0332,center.z),new THREE.Vector3(1,0,0),0,.03);
    const floor=ray.intersectObject(plate,false)[0];assert.ok(floor,'Narrow seam is backed by a real recess floor');
    assert.ok(Math.abs(floor.point.x-(wall-.0002))<.0001,'No overlapping dark plane on the front face');
    const pos=rocker.geometry.attributes.position,pivot=rocker.parent;
    const animated=root===yw.world?rocker:pivot,base=animated.quaternion.clone();
    for(let i=0;i<=20;i++){
      animated.quaternion.copy(base).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1),.045*i/20));root.updateMatrixWorld(true);
      for(let v=0;v<pos.count;v++){
        const p=new THREE.Vector3().fromBufferAttribute(pos,v).applyMatrix4(rocker.matrixWorld);
        assert.ok(p.x<wall-.0009,'Button skirt never cuts through the closed floor during switching');
        assert.ok(Math.abs(p.y-center.y)<.034&&Math.abs(p.z-center.z)<.0335,'Button stays within the well side walls');
      }
    }
    animated.quaternion.copy(base);root.updateMatrixWorld(true);targets.push(plate);
  }
  assert.equal(yw.m.nodes[2033].visible,false,'Coplanar old dark reveal is retired');
  assert.ok(!c43.m.nodes.some(n=>n.name==='C43_Switch28_reveal'),'Coplanar C43 reveal is absent from the pack');
}
let triangles=0;
for(const mesh of targets){assert.ok(mesh?.isMesh);const g=mesh.geometry,n=g.attributes.position.count;for(const a of Object.values(g.attributes))for(const v of a.array)assert.ok(Number.isFinite(v));for(const i of g.index.array)assert.ok(i>=0&&i<n);triangles+=g.index.count/3;
 const ns=g.attributes.normal;for(let i=0;i<ns.count;i++){const length=Math.hypot(ns.getX(i),ns.getY(i),ns.getZ(i));assert.ok(length>.9&&length<1.1,'Finite normalized surface normals');}}
assert.ok(triangles<110000,'Rackets, switch, toothbrush and mirror remain bounded');
console.log(JSON.stringify({result:'PASS',targetMeshes:targets.length,targetTriangles:triangles,revisions:[yw.m.revision,c43.m.revision]}));
