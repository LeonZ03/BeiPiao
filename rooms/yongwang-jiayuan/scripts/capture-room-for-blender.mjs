// Offline migration input. No browser, network access, or WebGL is used.
// After migration, this retained reference is not loaded by the web application.
import * as THREE from '../../../room-site/dist/vendor/three.module.js';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {createCanvas}=require('@napi-rs/canvas');
const site=path.resolve(import.meta.dirname,'../../../room-site'),dist=path.join(site,'dist');
const out=path.resolve(site,'../rooms/yongwang-jiayuan/assets/full-room');fs.mkdirSync(out,{recursive:true});
const paintDir=path.join(out,'textures');fs.mkdirSync(paintDir,{recursive:true});
const noop=()=>{};
const el=()=>({style:{},classList:{add:noop,remove:noop,toggle:noop},dataset:{},addEventListener:noop});
class Renderer{constructor(){this.shadowMap={};this.capabilities={getMaxAnisotropy:()=>8};}setPixelRatio(){}setSize(){}}
class Loader{load(url){const t=new THREE.Texture();t.userData.sourceFile=path.resolve(dist,url);if(!fs.existsSync(t.userData.sourceFile))throw Error(url);return t;}}
const context=vm.createContext({console,performance,setTimeout,clearTimeout,devicePixelRatio:1,innerWidth:1280,innerHeight:900,window:{addEventListener:noop},document:{getElementById:el,createElement:()=>createCanvas(512,512)},matchMedia:()=>({matches:false,addEventListener:noop})});
const values={...THREE,WebGLRenderer:Renderer,TextureLoader:Loader};
const three=new vm.SyntheticModule(Object.keys(values),function(){for(const[k,v]of Object.entries(values))this.setExport(k,v);},{context});
const orbit=new vm.SyntheticModule(['OrbitControls'],function(){this.setExport('OrbitControls',class{});},{context});
const modules=new Map();
const sourceFile=path.join(import.meta.dirname,'reference-scene.source.js');
if(!fs.existsSync(sourceFile))fs.copyFileSync(path.join(dist,'main.js'),sourceFile);
let source=fs.readFileSync(sourceFile,'utf8');
source=source.slice(0,source.indexOf('const navigation=createFlyNavigation'));
source+='\n globalThis.captured={world,outside,curtain,curtainPanels,curtainRings,diffuser,cutaway,ceilings,bed,desk,chair,wardrobe};';
const main=new vm.SourceTextModule(source,{context,identifier:path.join(dist,'main.js')});
function get(file){if(!modules.has(file))modules.set(file,new vm.SourceTextModule(fs.readFileSync(file,'utf8'),{context,identifier:file}));return modules.get(file);}
await main.link((id,ref)=>id==='three'?three:id.endsWith('/OrbitControls.js')?orbit:get(path.resolve(path.dirname(ref.identifier),id.split('?')[0])));
await main.evaluate();
const capture=context.captured;
// Contact-darkening planes are lighting effects, recreated by the lighting module.
for(const o of [...capture.world.children])if(o.renderOrder===2&&o.material?.isMeshBasicMaterial&&o.geometry?.type==='PlaneGeometry')capture.world.remove(o);
capture.world.updateMatrixWorld(true);
const blob=[],geometryIds=new Map(),materialIds=new Map(),textureIds=new Map(),nodeIds=new Map();
const geometries=[],materials=[],textures=[],nodes=[];let offset=0;
function bytes(array){const b=Buffer.from(array.buffer,array.byteOffset,array.byteLength);const item={offset,length:array.length,type:array.constructor.name};blob.push(b);offset+=b.length;const pad=(4-offset%4)%4;if(pad){blob.push(Buffer.alloc(pad));offset+=pad;}return item;}
function tex(t){if(textureIds.has(t))return textureIds.get(t);const id=textures.length;textureIds.set(t,id);
 let file=t.userData.sourceFile;
 if(!file){file=path.join(paintDir,`paint-${String(id).padStart(3,'0')}.png`);if(!t.image?.toBuffer)throw Error('Texture has no bitmap '+t.uuid);fs.writeFileSync(file,t.image.toBuffer('image/png'));}
 const info={id,file:path.relative(path.dirname(site),file).replaceAll('\\','/'),webPath:file.startsWith(dist)?'./'+path.relative(dist,file).replaceAll('\\','/'):null};
 for(const key of ['wrapS','wrapT','magFilter','minFilter','anisotropy','flipY','colorSpace','channel','rotation','premultiplyAlpha','generateMipmaps'])info[key]=t[key];
 for(const key of ['repeat','offset','center'])info[key]=t[key].toArray();textures.push(info);return id;
}
function material(m){if(materialIds.has(m))return materialIds.get(m);const id=materials.length;materialIds.set(m,id);const info={id,type:m.type,props:{},textures:{},colors:{},vectors:{},userData:m.userData};
 for(const[key,v]of Object.entries(m)){
   if(['id','uuid','type','version','name','userData'].includes(key)||key.startsWith('_')||key.startsWith('is'))continue;
   if(v?.isTexture)info.textures[key]=tex(v);
   else if(v?.isColor)info.colors[key]=v.toArray();
   else if(v?.isVector2)info.vectors[key]=v.toArray();
   else if(['number','string','boolean'].includes(typeof v)&&Number.isFinite(typeof v==='number'?v:0))info.props[key]=v;
 }materials.push(info);return id;
}
function geometry(g){if(geometryIds.has(g))return geometryIds.get(g);const id=geometries.length;geometryIds.set(g,id);
 const info={id,type:g.type,parameters:g.parameters||{},attributes:{},groups:g.groups,userData:g.userData};
 for(const[key,a]of Object.entries(g.attributes))info.attributes[key]={...bytes(Float32Array.from(a.array)),itemSize:a.itemSize};
 if(g.index)info.index=bytes(Uint32Array.from(g.index.array));geometries.push(info);return id;
}
function node(o,parent=-1){const id=nodes.length;nodeIds.set(o,id);o.updateMatrix();const info={id,parent,name:o.name,type:o.isInstancedMesh?'InstancedMesh':o.isMesh?'Mesh':'Group',matrix:o.matrix.toArray(),visible:o.visible,castShadow:o.castShadow,receiveShadow:o.receiveShadow,renderOrder:o.renderOrder,frustumCulled:o.frustumCulled,userData:o.userData};nodes.push(info);
 if(o.isMesh){info.geometry=geometry(o.geometry);info.material=Array.isArray(o.material)?o.material.map(material):material(o.material);}
 if(o.isInstancedMesh){info.count=o.count;info.instanceMatrix=bytes(Float32Array.from(o.instanceMatrix.array));if(o.instanceColor)info.instanceColor=bytes(Float32Array.from(o.instanceColor.array));}
 for(const child of o.children)node(child,id);
}
node(capture.world);
const refs={};for(const[key,value]of Object.entries(capture))refs[key]=Array.isArray(value)?value.map(o=>nodeIds.get(o)):nodeIds.get(value);
const manifest={format:'room-blender-source-1',nodes,geometries,materials,textures,refs};
fs.writeFileSync(path.join(out,'source-scene.json'),JSON.stringify(manifest));fs.writeFileSync(path.join(out,'source-geometry.bin'),Buffer.concat(blob));
console.log(JSON.stringify({objects:nodes.length,meshes:nodes.filter(o=>o.geometry!==undefined).length,geometries:geometries.length,materials:materials.length,textures:textures.length,bytes:offset,types:geometries.reduce((a,g)=>(a[g.type]=(a[g.type]||0)+1,a),{})},null,2));
