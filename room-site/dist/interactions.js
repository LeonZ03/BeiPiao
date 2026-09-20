export function createInteractions({THREE,world,camera,canvas,curtain,toggleCurtain,toggleLight,wardrobe,toast,hint,onSound=()=>{}}){
  const ray=new THREE.Raycaster(),pointer=new THREE.Vector2(),targets=[],water={shower:false,faucet:false};
  const thumbturn=world.getObjectByName('clickable-privacy-thumbturn');
  let doorLocked=false,turnTarget=0,lastUpdate=0;
  ray.params.Line.threshold=.002;ray.params.Points.threshold=.002;
  const labels={light:()=> '点击墙壁开关 · 开 / 关灯',curtain:()=> '点击窗帘 · 拉开 / 合上',shower:()=>water.shower?'点击花洒 · 关闭水流':'点击花洒 · 打开水流',faucet:()=>water.faucet?'点击水龙头 · 关闭水流':'点击水龙头 · 打开水流'};
  labels.doorLock=()=>doorLocked?'点击旋钮 · 解除反锁':'点击旋钮 · 反锁';
  if(wardrobe)for(const id of ['wardrobeLeft','wardrobeMiddle','wardrobeRight'])labels[id]=()=>wardrobe.label(id);
  curtain.userData.interactive='curtain';
  world.traverse(o=>{if(o.userData.interactive)targets.push(o);});
  const effects=new THREE.Group();effects.name='running-water';effects.userData.noCollision=true;effects.userData.dynamic=true;world.add(effects);
  const faucet=new THREE.Group();faucet.visible=false;effects.add(faucet);
  const stream=new THREE.Mesh(new THREE.CylinderGeometry(.004,.003,.224,10),new THREE.MeshPhysicalMaterial({color:'#c0e5e9',transparent:true,opacity:.48,roughness:.13,metalness:.1,depthWrite:false}));
  stream.position.set(-.065,.892,2.986);faucet.add(stream);
  const shower=new THREE.Group();shower.visible=false;effects.add(shower);
  world.updateMatrixWorld(true);
  const showerHead=world.getObjectByName('wall-normal-shower-head');
  const showerOrigin=showerHead.localToWorld(new THREE.Vector3(0,.0138,0));
  const showerRotation=showerHead.getWorldQuaternion(new THREE.Quaternion()),sprayNormal=new THREE.Vector3(0,1,0).applyQuaternion(showerRotation),sprayX=new THREE.Vector3(1,0,0).applyQuaternion(showerRotation),sprayZ=new THREE.Vector3(0,0,1).applyQuaternion(showerRotation);
  const drops=180,positions=new Float32Array(drops*6),geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(positions,3).setUsage(THREE.DynamicDrawUsage));
  const spray=new THREE.LineSegments(geo,new THREE.LineBasicMaterial({color:'#789ca7',transparent:true,opacity:.76,depthWrite:false}));spray.frustumCulled=false;shower.add(spray);
  for(let j=0;j<4;j++){
    const ripple=new THREE.Mesh(new THREE.RingGeometry(.028,.031,32),new THREE.MeshBasicMaterial({color:'#c5dfe0',transparent:true,opacity:.25,side:THREE.DoubleSide,depthWrite:false}));ripple.rotation.x=-Math.PI/2;ripple.position.set(showerOrigin.x,.112,showerOrigin.z+.30);ripple.userData.phase=j/4;shower.add(ripple);
  }
  const splash=new THREE.Mesh(new THREE.RingGeometry(.012,.014,24),new THREE.MeshBasicMaterial({color:'#d1e8e9',transparent:true,opacity:.4,side:THREE.DoubleSide,depthWrite:false}));splash.rotation.x=-Math.PI/2;splash.position.set(-.065,.783,2.986);faucet.add(splash);
  function update(t){
    const dt=Math.min(.05,lastUpdate?t-lastUpdate:.016);lastUpdate=t;
    if(thumbturn){const d=turnTarget-thumbturn.rotation.z;thumbturn.rotation.z=Math.abs(d)<.001?turnTarget:thumbturn.rotation.z+d*(1-Math.exp(-dt*12));}
    if(water.shower){
      for(let i=0;i<drops;i++){
        const phase=(t*1.48+i*.6180339)%1,age=phase*.615,angle=i*2.39996,r=.036*Math.sqrt((i%29)/29),sx=Math.sin(angle),sz=Math.cos(angle);
        for(let k=0;k<2;k++){const a=Math.min(.617,age+k*.011),p=i*6+k*3;for(let axis=0;axis<3;axis++){const key=['x','y','z'][axis];positions[p+axis]=showerOrigin[key]+(sprayX[key]*sx+sprayZ[key]*sz)*(r+.07*a)+sprayNormal[key]*.55*a-(axis===1?4.78*a*a:0);}}
      }geo.attributes.position.needsUpdate=true;
      shower.children.slice(1).forEach(o=>{const p=(t*1.4+o.userData.phase)%1;o.scale.setScalar(.5+p*3.2);o.material.opacity=(1-p)*.2;});
    }
    if(water.faucet){const p=(t*2.4)%1;splash.scale.setScalar(.7+p*2);splash.material.opacity=(1-p)*.5;stream.material.opacity=.45+Math.sin(t*21)*.045;}
  }
  function perform(id){if(id==='light')toggleLight();else if(id==='curtain')toggleCurtain();else if(id.startsWith('wardrobe'))wardrobe?.toggle(id);else if(id==='doorLock'&&thumbturn){doorLocked=!doorLocked;turnTarget=doorLocked?Math.PI/2:0;thumbturn.userData.locked=doorLocked;toast(doorLocked?'门已反锁':'已解除反锁');}else if(id in water){water[id]=!water[id];(id==='shower'?shower:faucet).visible=water[id];world.userData.waterActive=water.shower||water.faucet;toast((id==='shower'?'花洒':'水龙头')+(water[id]?'已打开':'已关闭'));}if(labels[id]){hint.textContent=labels[id]();onSound(id);}return {...water,doorLocked};}
  const ownerOf=o=>{while(o&&!o.userData.interactive)o=o.parent;return o;};
  const visible=o=>{while(o){if(!o.visible)return false;o=o.parent;}return true;};
  function pick(x,y,locked=false){
    if(locked)pointer.set(0,0);else{const r=canvas.getBoundingClientRect();pointer.set((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1);}
    camera.updateMatrixWorld();world.updateMatrixWorld(true);ray.setFromCamera(pointer,camera);ray.far=4;
    const candidates=ray.intersectObjects(targets,true).filter(h=>visible(h.object));
    if(!candidates.length)return null;
    const first=candidates[0],owner=ownerOf(first.object);
    // Opaque intervening geometry prevents operating fixtures through a wall.
    const obstruction=ray.intersectObject(world,true).find(h=>h.object.isMesh&&visible(h.object)&&h.distance<first.distance-.006&&!(Array.isArray(h.object.material)?h.object.material:[h.object.material]).every(m=>m.transparent)&&ownerOf(h.object)!==owner);
    if(obstruction)return null;return owner?.userData.interactive;
  }
  function hover(x,y,locked){const id=pick(x,y,locked);canvas.style.cursor=id?'pointer':'grab';hint.textContent=id?(labels[id]?.()||'点击互动'):'';hint.hidden=!id;return id;}
  return {update,perform,pick,hover,get state(){return {...water,doorLocked,thumbturnAngle:thumbturn?.rotation.z||0};},get active(){return water.shower||water.faucet||(thumbturn&&Math.abs(turnTarget-thumbturn.rotation.z)>.00001);}};
}
