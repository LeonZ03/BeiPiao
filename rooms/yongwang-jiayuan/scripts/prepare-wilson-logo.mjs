// Rasterize the archived official SVG without relying on CSS-class support.
import fs from 'node:fs';
import {createCanvas,loadImage} from '@napi-rs/canvas';
const dir=new URL('../history/inputs/wilson43/',import.meta.url);
const source=fs.readFileSync(new URL('logo.svg',dir),'utf8').replaceAll('class="cls-1"','fill="#ffffff"');
const canvas=createCanvas(1024,242),ctx=canvas.getContext('2d');
ctx.drawImage(await loadImage(Buffer.from(source)),0,0,1024,242);
const pixels=ctx.getImageData(0,0,1024,242).data;
let ink=0,white=0;for(let i=0;i<pixels.length;i+=4){if(pixels[i+3]>128)ink++;if(pixels[i+3]>128&&pixels[i]>128)white++;}
if(ink<1000||white/ink<.99)throw Error('Expected visible white wordmark with transparent background');
fs.writeFileSync(new URL('logo.png',dir),canvas.toBuffer('image/png'));
console.log({ink,white});
