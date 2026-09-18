// Public BOSC wordmark, sourced from the XiangShan team's APPT 2025 slides.
// UVs select the original emblem only; the user's full photograph is not served.
export function addBoscPaperCup({THREE,desk,texture}){
  const cup=new THREE.Group();cup.name='bosc-printed-paper-cup';cup.position.set(.12,1.662,-.13);cup.rotation.y=-Math.PI/2;desk.add(cup);
  const paper=new THREE.MeshStandardMaterial({color:'#fff9e9',roughness:.88});
  const profile=[[0,.001],[.023,.001],[.024,.006],[.031,.079],[.032,.081],[.031,.083],[.029,.082],[.0285,.077],[.022,.006],[0,.006]].map(p=>new THREE.Vector2(...p));
  const shell=new THREE.Mesh(new THREE.LatheGeometry(profile,72),paper);shell.name='rolled-rim-hollow-paper-cup';shell.castShadow=shell.receiveShadow=true;cup.add(shell);
  function wrap(name,width,y0,height,material,uv=(u,v)=>[u,v]){
    const p=[],t=[],ix=[],N=80;
    for(let row=0;row<=8;row++)for(let i=0;i<=N;i++){
      const u=i/N,v=row/8,y=y0+height*v,a=(u-.5)*width,r=.024+(y-.006)/.073*.007+.00007;
      p.push(Math.sin(a)*r,y,Math.cos(a)*r);t.push(...uv(u,v));
    }
    for(let row=0;row<8;row++)for(let i=0;i<N;i++){const a=row*(N+1)+i;ix.push(a,a+1,a+N+2,a,a+N+2,a+N+1);}
    const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(t,2));g.setIndex(ix);g.computeVertexNormals();
    const m=new THREE.Mesh(g,material);m.name=name;m.receiveShadow=true;cup.add(m);return m;
  }
  const logo=texture('bosc-public-logo.png');logo.anisotropy=8;
  wrap('original-bosc-emblem',.87,.033,.027,new THREE.MeshStandardMaterial({map:logo,transparent:true,roughness:.9,depthWrite:false}), (u,v)=>[u*83/632,v]);
  wrap('teal-bottom-band',Math.PI*2,.009,.007,new THREE.MeshStandardMaterial({color:'#398c98',roughness:.94}));
  const c=document.createElement('canvas');c.width=1024;c.height=112;const p=c.getContext('2d');p.clearRect(0,0,c.width,c.height);
  p.fillStyle='#fffaf0';p.font='54px "Microsoft YaHei", sans-serif';p.textAlign='center';p.textBaseline='middle';p.fillText('北京开源芯片研究院',512,58,970);
  const text=new THREE.CanvasTexture(c);text.colorSpace=THREE.SRGBColorSpace;text.anisotropy=8;
  const letters=wrap('bosc-institute-ring-lettering',2.09,.010,.0046,new THREE.MeshStandardMaterial({map:text,transparent:true,roughness:1,depthWrite:false,polygonOffset:true,polygonOffsetFactor:-1}));
  letters.scale.set(1.001,1,1.001);
  cup.userData.logoSource='https://tutorial.xiangshan.cc/appt25/slides/20250714-4-APPT25-4-Dev-Tools.pdf';
  return cup;
}
