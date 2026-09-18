import http from 'node:http';
import { readFile, stat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzip } from 'node:zlib';
import { promisify } from 'node:util';

const root = await realpath(fileURLToPath(new URL('../room-site/dist/', import.meta.url)));
const portArgument = process.argv.indexOf('--port');
const port = portArgument >= 0 ? Number(process.argv[portArgument + 1]) : 48173;
if (!Number.isInteger(port) || port < 1024 || port > 65535) {
  throw new Error('Invalid --port value');
}
const compress = promisify(gzip);
const cache = new Map();
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.woff2': 'font/woff2', '.wasm': 'application/wasm', '.mp4': 'video/mp4' };
const inside = file => file.startsWith(root + path.sep);
const server = http.createServer(async (req, res) => {
  try {
    if (!['GET', 'HEAD'].includes(req.method)) { res.writeHead(405, { Allow: 'GET, HEAD' }); return res.end(); }
    const requested = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (requested.includes('\\') || requested.includes('\0') || requested.split('/').some(p => p.startsWith('.'))) { res.writeHead(404); return res.end(); }
    const candidate = path.resolve(root, '.' + (requested === '/' ? '/index.html' : requested));
    if (!inside(candidate)) { res.writeHead(404); return res.end(); }
    const file = await realpath(candidate);
    if (!inside(file)) { res.writeHead(404); return res.end(); }
    const info = await stat(file);
    if (!info.isFile()) { res.writeHead(404); return res.end(); }
    let entry = cache.get(file);
    if (!entry || entry.mtime !== info.mtimeMs) {
      const body = await readFile(file);
      const text = /\.(html|js|css|json|svg|gltf)$/.test(file);
      entry = { mtime: info.mtimeMs, body, zipped: text ? await compress(body) : null };
      cache.set(file, entry);
    }
    const zipped = entry.zipped && /\bgzip\b/.test(req.headers['accept-encoding'] || '');
    const body = zipped ? entry.zipped : entry.body;
    res.writeHead(200, {
      'Content-Type': types[path.extname(file)] || 'application/octet-stream',
      'Content-Length': body.length,
      'Cache-Control': 'public, max-age=0, must-revalidate',
      'X-Content-Type-Options': 'nosniff',
      'Vary': 'Accept-Encoding',
      ...(zipped ? { 'Content-Encoding': 'gzip' } : {})
    });
    res.end(req.method === 'HEAD' ? undefined : body);
  } catch (error) {
    res.writeHead(error instanceof URIError ? 400 : 404);
    res.end('Not found');
  }
});
server.listen(port, '127.0.0.1', () => console.log(`Room website: http://127.0.0.1:${port}`));
