// Targeted checks for the two authored laptops and props24. No browser mocks.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {gunzipSync} from 'node:zlib';
import * as THREE from '../room-site/dist/vendor/three.module.js';
import {parseBlenderRoom} from '../room-site/dist/blender-room.js';
import {createLaptop} from '../room-site/dist/laptop.js';
const web=new URL('../room-site/dist/',import.meta.url);
for(const [path,revision] of [['assets/full-room/','laptop40'],['assets/rooms/Courtyard43/interior/','courtyard43-props24']]){
  const dir=new URL(path,web),m=JSON.parse(fs.readFileSync(new URL('scene.json',dir))),b=fs.readFileSync(new URL('geometry.bin',dir));
  assert.equal(m.revision,revision);
  assert.deepEqual(gunzipSync(fs.readFileSync(new URL('geometry.bin.gz',dir))),b);
  for(const t of m.textures)assert.ok(fs.statSync(new URL(t.webPath,web)).size>0,'Texture exists: '+t.webPath);
  const {world}=parseBlenderRoom(THREE,m,b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),[]);
  let lid,base;world.traverse(o=>{if(o.userData.laptopLid)lid=o;if(o.userData.laptopRoot)base=o;});
  assert.ok(lid&&base);assert.equal(lid.parent,base);
  base.updateWorldMatrix(true,true);
  const all=[];base.traverse(o=>{if(o.isMesh&&o.visible)all.push(o);});
  for(const mesh of all){
    const g=mesh.geometry,n=g.attributes.position.count;
    for(const a of Object.values(g.attributes))for(const v of a.array)assert.ok(Number.isFinite(v));
    for(const i of g.index.array)assert.ok(i<n);
  }
  // Sweep all 21 hinge states and ensure the screen never reaches the desk.
  const inv=base.matrixWorld.clone().invert(),p=new THREE.Vector3();let min=Infinity;
  for(let k=0;k<=20;k++){
    lid.rotation.x=Math.PI/2+(-.21-Math.PI/2)*k/20;world.updateMatrixWorld(true);
    lid.traverse(o=>{if(!o.isMesh||!o.visible)return;const a=o.geometry.attributes.position;
      for(let i=0;i<a.count;i++){p.fromBufferAttribute(a,i).applyMatrix4(o.matrixWorld).applyMatrix4(inv);min=Math.min(min,p.y);}
    });
  }
  assert.ok(min>.001,'Lid sweep stays above desk: '+min);
  if(revision==='laptop40'){
    const controller=createLaptop(world);assert.equal(controller.state.amount,1);
    controller.toggle();for(let i=0;i<80;i++)controller.update(.05);assert.equal(controller.state.amount,0);
    controller.toggle();controller.update(.05);const mid=controller.state.amount;controller.toggle();controller.update(.05);assert.ok(controller.state.amount<mid);
    for(let i=0;i<80;i++)controller.update(.05);const r=controller.revision;controller.update(.05);assert.equal(controller.revision,r,'Settled state does not invalidate cache');
  }else{
    assert.ok(m.nodes.some(n=>n.name==='C43_Bag24_new_roll'&&n.visible));
    assert.ok(m.nodes.some(n=>n.name.includes('softpack')&&n.visible));
    assert.ok(m.interactions.find(x=>x.id==='laptop'&&!x.defaultOpen&&x.kind==='laptop'));
    for(const name of ['C43_Curtain_Left','C43_Curtain_Right']){
      const node=m.nodes.find(n=>n.name===name),g=m.geometries[node.geometry],mat=m.materials[node.material];
      assert.ok(g.morphTargets?.position?.length);assert.equal(mat.props.metalness,0);assert.ok(mat.props.roughness>=.95);
    }
  }
  console.log(revision+': pack consistency, textures, laptop sweep and targeted state checks passed');
}
