import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root=fileURLToPath(new URL('../',import.meta.url));
const source=path.join(root,'room-site','dist');
const output=path.resolve(root,'.pages-dist');
// This disposable publication directory is the only path this builder removes.
if(path.dirname(output)!==path.resolve(root)||path.basename(output)!=='.pages-dist')throw new Error('Unsafe output directory');
const existing=await fs.lstat(output).catch(e=>{if(e.code!=='ENOENT')throw e;});
if(existing?.isSymbolicLink())throw new Error('Output must not be a symlink');
await fs.rm(output,{recursive:true,force:true});
// Each room keeps its own descriptor and delivery directory. Nested room stages
// (for example a preserved whitebox plus an interior) are discovered as well.
const scenePaths=['assets/full-room/scene.json'];
async function discoverScenes(directory){
  for(const entry of await fs.readdir(directory,{withFileTypes:true}).catch(error=>{if(error.code==='ENOENT')return [];throw error;})){
    const file=path.join(directory,entry.name);
    if(entry.isDirectory())await discoverScenes(file);
    else if(entry.isFile()&&entry.name==='scene.json')scenePaths.push(path.relative(source,file).split(path.sep).join('/'));
  }
}
await discoverScenes(path.join(source,'assets','rooms'));
const manifests=[];
const insideSource=url=>{
  if(typeof url!=='string'||/^[a-z][a-z\d+.-]*:/i.test(url))throw new Error('Expected a local room binary URL');
  const file=path.resolve(source,url);
  if(!file.startsWith(path.resolve(source)+path.sep))throw new Error('Room binary outside deployment source: '+url);
  return file;
};
for(const scenePath of scenePaths.sort()){
  const sourceManifest=await fs.readFile(path.join(source,scenePath),'utf8');
  const manifest=JSON.parse(sourceManifest);
  if(manifest.format!=='blender-room-pack-1')continue;
  for(const key of ['binary','compressedBinary'])insideSource(manifest[key]);
  manifests.push({scenePath,sourceManifest,manifest});
}
if(!manifests.some(entry=>entry.scenePath==='assets/full-room/scene.json'))throw new Error('Missing primary room pack');
const binaries=new Set(manifests.flatMap(({manifest})=>[manifest.binary,manifest.compressedBinary].map(insideSource)));
await fs.cp(source,output,{recursive:true,filter:src=>!binaries.has(path.resolve(src))});
for(const {scenePath,sourceManifest,manifest} of manifests){
 for(const [key,property] of [['binary','binaryParts'],['compressedBinary','compressedBinaryParts']]){
  const bytes=await fs.readFile(insideSource(manifest[key]));
  const hash=createHash('sha256').update(bytes).digest('hex').slice(0,16);
  const parts=[];
  for(let offset=0,index=0;offset<bytes.length;offset+=8*1024*1024,index++){
    const part=bytes.subarray(offset,Math.min(offset+8*1024*1024,bytes.length));
    const url=`${path.posix.dirname(scenePath)}/chunks/${key}-${hash}-${index}.part`;
    await fs.mkdir(path.dirname(path.join(output,url)),{recursive:true});
    await fs.writeFile(path.join(output,url),part);parts.push({url,bytes:part.length});
  }
  manifest[property]=parts;
 }
 const delivery=JSON.stringify({binaryParts:manifest.binaryParts,compressedBinaryParts:manifest.compressedBinaryParts});
 await fs.writeFile(path.join(output,scenePath),sourceManifest.trimEnd().slice(0,-1)+','+delivery.slice(1));
}
await fs.writeFile(path.join(output,'_headers'),`/*
  Cache-Control: public, max-age=0, must-revalidate
  X-Content-Type-Options: nosniff
${manifests.map(({scenePath})=>`/${path.posix.dirname(scenePath)}/chunks/*
  Cache-Control: public, max-age=31536000, immutable
  Content-Type: application/octet-stream
`).join('')}`);
let count=0,max=0;
async function check(dir){for(const entry of await fs.readdir(dir,{withFileTypes:true})){
  const file=path.join(dir,entry.name);if(entry.isDirectory()){await check(file);continue;}
  const {size}=await fs.stat(file);if(size>25*1024*1024)throw new Error('Pages file limit: '+file);count++;max=Math.max(max,size);
}}
await check(output);
console.log(`Pages ready: ${count} files; largest ${(max/1024/1024).toFixed(2)} MiB; scenes ${manifests.map(({manifest})=>manifest.revision).join(', ')}; output .pages-dist`);
