import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {loadRoomBinary} from '../room-site/dist/room-binary.js';

const root=fileURLToPath(new URL('../',import.meta.url));
execFileSync(process.execPath,['tools/build-pages.mjs'],{cwd:root,stdio:'inherit'});
const deployed=path.join(root,'.pages-dist');
const source=path.join(root,'room-site/dist');
const scenes=['assets/full-room/scene.json'];
async function discover(directory){
  for(const entry of await fs.readdir(directory,{withFileTypes:true}).catch(error=>{if(error.code==='ENOENT')return [];throw error;})){
    const file=path.join(directory,entry.name);
    if(entry.isDirectory())await discover(file);
    else if(entry.isFile()&&entry.name==='scene.json'){
      const manifest=JSON.parse(await fs.readFile(file,'utf8'));
      if(manifest.format==='blender-room-pack-1')scenes.push(path.relative(source,file).split(path.sep).join('/'));
    }
  }
}
await discover(path.join(source,'assets','rooms'));
const headers=await fs.readFile(path.join(deployed,'_headers'),'utf8');
assert.ok(headers.includes('max-age=0, must-revalidate'));
const originalFetch=globalThis.fetch,originalDecompress=globalThis.DecompressionStream;
try{
 for(const scenePath of scenes){
  const local=JSON.parse(await fs.readFile(path.join(source,scenePath),'utf8'));
  const remote=JSON.parse(await fs.readFile(path.join(deployed,scenePath),'utf8'));
  const expected=await fs.readFile(path.join(source,local.binary));
  for(const [key,property] of [['binary','binaryParts'],['compressedBinary','compressedBinaryParts']]){
    const bytes=await fs.readFile(path.join(source,local[key]));
    const digest=createHash('sha256').update(bytes).digest('hex').slice(0,16);
    assert.ok(remote[property].length>0,`${scenePath} ${property}`);
    assert.ok(headers.includes(`/${path.posix.dirname(scenePath)}/chunks/*\n  Cache-Control: public, max-age=31536000, immutable`));
    assert.equal(await fs.stat(path.join(deployed,local[key])).then(()=>true,error=>{if(error.code==='ENOENT')return false;throw error;}),false,'Unchunked binary must not be deployed');
    const chunks=[];
    for(const [index,part] of remote[property].entries()){
      assert.equal(part.url,`${path.posix.dirname(scenePath)}/chunks/${key}-${digest}-${index}.part`);
      assert.ok(part.bytes>0&&part.bytes<=8*1024*1024);
      const chunk=await fs.readFile(path.join(deployed,part.url));
      assert.equal(chunk.length,part.bytes);
      chunks.push(chunk);
    }
    assert.deepEqual(Buffer.concat(chunks),bytes,`${scenePath} ${key} chunks preserve every byte`);
  }
  for(const compressed of [true,false]){
    globalThis.DecompressionStream=compressed?originalDecompress:undefined;
    for(const [dir,manifest]of [[deployed,remote],[source,local]]){
      globalThis.fetch=async url=>{
        const bytes=await fs.readFile(path.join(dir,url.split('?')[0]));
        return new Response(bytes,{headers:{'Content-Length':String(bytes.length)}});
      };
      const progress=[];
      const actual=await loadRoomBinary(manifest,value=>progress.push(value));
      assert.deepEqual(Buffer.from(actual),expected,'Delivery must preserve every Blender byte');
      assert.equal(progress.at(-1),1);
      assert.ok(progress.every((v,i)=>v>=0&&v<=1&&(i===0||v>=progress[i-1])));
    }
  }
  globalThis.DecompressionStream=originalDecompress;
  globalThis.fetch=async()=>new Response('missing',{status:404});
  await assert.rejects(()=>loadRoomBinary(remote),/Room geometry 404/);
  globalThis.fetch=async()=>new Response(new Uint8Array(3));
  await assert.rejects(()=>loadRoomBinary(remote),/Incomplete room geometry/);
  const clean={...remote};delete clean.binaryParts;delete clean.compressedBinaryParts;
  assert.deepEqual(clean,local,`${scenePath}: deployment must not alter model descriptors`);
 }
}finally{globalThis.fetch=originalFetch;globalThis.DecompressionStream=originalDecompress;}
console.log(`PASS Pages: ${scenes.length} independent scene packs; raw/gzip chunks and local fallback are byte-identical; progress, failed and truncated downloads checked.`);
