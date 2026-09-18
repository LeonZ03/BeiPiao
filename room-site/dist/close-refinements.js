import assets from './assets/close-refinements/models.js?v=blender18';
const memo=new Map();
function geometry(THREE,item){
  if(!memo.has(item.name)){const g=new THREE.BufferGeometry();for(const key of ['position','normal','uv'])g.setAttribute(key,new THREE.Float32BufferAttribute(item[key],key==='uv'?2:3));g.setIndex(item.index);g.computeBoundingSphere();memo.set(item.name,g);}
  return memo.get(item.name);
}
function texture(THREE,w,h,paint){const c=document.createElement('canvas');c.width=w;c.height=h;paint(c.getContext('2d'),w,h);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;}
export function createDetailedHelmet(THREE){
  const root=new THREE.Group();root.name='LS2 FF801 Carbon Full-Face Helmet';root.userData.authoring='Blender';
  const carbon=texture(THREE,128,128,p=>{p.fillStyle='#171b1f';p.fillRect(0,0,128,128);for(let y=0;y<128;y+=8)for(let x=0;x<128;x+=8){const v=((x+y)/8)%4<2;p.fillStyle=v?'#30343a':'#191c21';p.fillRect(x,y,8,8);for(let j=1;j<8;j+=2){p.fillStyle=v?'#393d42':'#252930';p.fillRect(x+(v?j:0),y+(v?0:j),v?1:8,v?8:1);}}});carbon.wrapS=carbon.wrapT=THREE.RepeatWrapping;carbon.repeat.set(7,4);
  const mirror=texture(THREE,512,64,(p,w,h)=>{const grad=p.createLinearGradient(0,0,w,0);for(const [s,c]of [[0,'#314d61'],[.14,'#ca6f18'],[.35,'#efb93e'],[.50,'#e6a423'],[.72,'#be3e25'],[.87,'#813343'],[1,'#658756']])grad.addColorStop(s,c);p.fillStyle=grad;p.fillRect(0,0,w,h);});
  const materials={
    carbon:new THREE.MeshPhysicalMaterial({color:'#ffffff',map:carbon,roughness:.27,metalness:.2,clearcoat:1,clearcoatRoughness:.12,side:THREE.DoubleSide}),
    rubber:new THREE.MeshStandardMaterial({color:'#11151a',roughness:.84}),
    vent:new THREE.MeshPhysicalMaterial({color:'#262d32',roughness:.34,metalness:.35,clearcoat:.4,side:THREE.DoubleSide}),
    visor:new THREE.MeshPhysicalMaterial({color:'#ffffff',map:mirror,roughness:.14,metalness:.84,clearcoat:1,clearcoatRoughness:.07,iridescence:.24,iridescenceIOR:1.35,side:THREE.DoubleSide}),
    silver:new THREE.MeshStandardMaterial({color:'#7e878b',roughness:.24,metalness:.85})
  };
  for(const [name,text,size] of [['brand-logo','LS2',78],['model-logo','FF801 CARBON',59]]){
    const map=texture(THREE,512,96,p=>{
      p.clearRect(0,0,512,96);p.fillStyle='#f7f7f2';
      if(name==='brand-logo'){
        // Continuous, low-slung racing wordmark rather than spaced Arial letters.
        p.translate(27,14);p.transform(1,0,-.24,1,18,0);
        const polygon=pts=>{p.beginPath();pts.forEach(([x,y],i)=>i?p.lineTo(x,y):p.moveTo(x,y));p.closePath();p.fill();};
        polygon([[0,0],[42,0],[42,48],[143,48],[143,67],[0,67]]);
        polygon([[157,0],[297,0],[297,18],[188,18],[188,25],[272,25],[297,33],[297,57],[279,67],[151,67],[151,49],[264,49],[264,42],[176,42],[151,33],[151,10]]);
        polygon([[312,0],[440,0],[457,12],[457,32],[440,43],[347,43],[347,49],[457,49],[457,67],[311,67],[311,32],[329,25],[420,25],[420,18],[312,18]]);
      }else{p.font=`italic 800 ${size}px Arial`;p.textAlign='center';p.textBaseline='middle';p.translate(256,48);p.scale(470/p.measureText(text).width,1);p.fillText(text,0,0);}
    });
    materials[name]=new THREE.MeshStandardMaterial({map,transparent:true,roughness:.5,side:THREE.DoubleSide,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-2});
  }
  for(const item of assets.groups.helmet){const mesh=new THREE.Mesh(geometry(THREE,item),materials[item.material]);mesh.name=item.name;mesh.castShadow=!item.material.endsWith('logo');mesh.receiveShadow=true;root.add(mesh);}
  root.userData.dimensions={width:.304,height:.318,depth:.443};return root;
}
export function refineCottonPillow(THREE,pillow){
  const cloth=pillow.children.find(o=>o.name==='pillow-soft-surface').material.clone();cloth.side=THREE.FrontSide;cloth.roughness=.93;
  const seam=pillow.children.find(o=>o.name==='pillow-seam').material;
  for(const child of [...pillow.children]){pillow.remove(child);child.geometry?.dispose();}
  pillow.position.y=.624;pillow.userData.authoring='Blender';
  for(const item of assets.groups.pillow){const mesh=new THREE.Mesh(geometry(THREE,item),item.material==='linen'?cloth:seam);mesh.name=item.name;mesh.castShadow=mesh.receiveShadow=true;pillow.add(mesh);}
}
