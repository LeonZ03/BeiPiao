// Pages delivery may split the exact Blender binary into bounded-size files.
// Local playback keeps using the original single file and the same scene pack.
export async function loadRoomBinary(manifest,onProgress=()=>{}){
  const compressed=typeof DecompressionStream!=='undefined';
  const parts=compressed?manifest.compressedBinaryParts:manifest.binaryParts;
  const files=parts||[{url:compressed?manifest.compressedBinary:manifest.binary}];
  const received=files.map(()=>0),totals=files.map(f=>f.bytes||0);
  const report=()=>{const total=totals.reduce((a,b)=>a+b,0);if(total>0)onProgress(Math.min(.99,received.reduce((a,b)=>a+b,0)/total));};
  const data=await Promise.all(files.map(async(file,i)=>{
    const response=await fetch(file.url+'?v='+manifest.revision);
    if(!response.ok)throw new Error('Room geometry '+response.status);
    if(!totals[i])totals[i]=Number(response.headers.get('Content-Length'))||0;
    let bytes;
    if(response.body){
      const reader=response.body.getReader(),chunks=[];
      while(true){const {done,value}=await reader.read();if(done)break;chunks.push(value);received[i]+=value.length;report();}
      bytes=new Uint8Array(received[i]);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
    }else{bytes=new Uint8Array(await response.arrayBuffer());received[i]=bytes.length;report();}
    if(file.bytes!==undefined&&bytes.length!==file.bytes)throw new Error('Incomplete room geometry');
    return bytes;
  }));
  const blob=new Blob(data);
  const buffer=compressed?await new Response(blob.stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer():await blob.arrayBuffer();
  onProgress(1);return buffer;
}
