import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {loadRoomBinary} from '../room-site/dist/room-binary.js';

const root=fileURLToPath(new URL('../',import.meta.url));
execFileSync(process.execPath,['tools/build-pages.mjs'],{cwd:root,stdio:'inherit'});
const deployed=path.join(root,'.pages-dist');
const readScene=dir=>fs.readFile(path.join(dir,'assets/full-room/scene.json'),'utf8').then(JSON.parse);
const local=await readScene(path.join(root,'room-site/dist')),remote=await readScene(deployed);
assert.deepEqual(remote.nodes,local.nodes);assert.deepEqual(remote.materials,local.materials);
const expected=await fs.readFile(path.join(root,'room-site/dist',local.binary));
const originalFetch=globalThis.fetch,originalDecompress=globalThis.DecompressionStream;
try{
  for(const compressed of [true,false]){
    globalThis.DecompressionStream=compressed?originalDecompress:undefined;
    for(const [dir,manifest]of [[deployed,remote],[path.join(root,'room-site/dist'),local]]){
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
}finally{globalThis.fetch=originalFetch;globalThis.DecompressionStream=originalDecompress;}
const clean={...remote};delete clean.binaryParts;delete clean.compressedBinaryParts;
assert.deepEqual(clean,local,'Deployment must not alter model descriptors');
console.log('PASS Pages: raw/gzip chunks and local fallback are byte-identical; progress, failed and truncated downloads checked.');
