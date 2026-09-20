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
const scenePath='assets/full-room/scene.json';
const sourceManifest=await fs.readFile(path.join(source,scenePath),'utf8');
const manifest=JSON.parse(sourceManifest);
const binaries=new Set([manifest.binary,manifest.compressedBinary].map(p=>path.resolve(source,p)));
await fs.cp(source,output,{recursive:true,filter:src=>!binaries.has(path.resolve(src))});
for(const [key,property] of [['binary','binaryParts'],['compressedBinary','compressedBinaryParts']]){
  const bytes=await fs.readFile(path.join(source,manifest[key]));
  const hash=createHash('sha256').update(bytes).digest('hex').slice(0,16);
  const parts=[];
  for(let offset=0,index=0;offset<bytes.length;offset+=8*1024*1024,index++){
    const part=bytes.subarray(offset,Math.min(offset+8*1024*1024,bytes.length));
    const url=`assets/full-room/chunks/${key}-${hash}-${index}.part`;
    await fs.mkdir(path.dirname(path.join(output,url)),{recursive:true});
    await fs.writeFile(path.join(output,url),part);parts.push({url,bytes:part.length});
  }
  manifest[property]=parts;
}
const delivery=JSON.stringify({binaryParts:manifest.binaryParts,compressedBinaryParts:manifest.compressedBinaryParts});
await fs.writeFile(path.join(output,scenePath),sourceManifest.trimEnd().slice(0,-1)+','+delivery.slice(1));
await fs.writeFile(path.join(output,'_headers'),`/*
  Cache-Control: public, max-age=0, must-revalidate
  X-Content-Type-Options: nosniff
/assets/full-room/chunks/*
  Cache-Control: public, max-age=31536000, immutable
  Content-Type: application/octet-stream
`);
let count=0,max=0;
async function check(dir){for(const entry of await fs.readdir(dir,{withFileTypes:true})){
  const file=path.join(dir,entry.name);if(entry.isDirectory()){await check(file);continue;}
  const {size}=await fs.stat(file);if(size>25*1024*1024)throw new Error('Pages file limit: '+file);count++;max=Math.max(max,size);
}}
await check(output);
console.log(`Pages ready: ${count} files; largest ${(max/1024/1024).toFixed(2)} MiB; scene ${manifest.revision}; output .pages-dist`);
