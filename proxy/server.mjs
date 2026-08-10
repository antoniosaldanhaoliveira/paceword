/**
 * Pace fetch proxy — bare Node.js HTTP server, no npm dependencies.
 * Accepts GET /fetch?url=<encoded> and returns the raw HTML body.
 *
 * Security guards:
 *   - Blocks private/loopback IP ranges (SSRF protection)
 *   - 20-second upstream timeout
 *   - 5 MB response size cap
 *   - Enforces text/html content-type
 */

import http from 'node:http';
import https from 'node:https';
import { URL } from 'node:url';

const PORT = 3001;
const MAX_BYTES = 5 * 1024 * 1024;
const TIMEOUT_MS = 20_000;

const BLOCKED_PREFIXES = [
  'localhost', '127.', '0.', '10.', '169.254.', '192.168.', '::1', '[::1]',
];

function isBlockedHost(hostname) {
  const lower = hostname.toLowerCase();
  return BLOCKED_PREFIXES.some((p) => lower === p.replace('.', '') || lower.startsWith(p));
}

function respond(res, status, body) {
  res.writeHead(status, { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' });
  res.end(JSON.stringify({ error: body }));
}

function respondHtml(res, html) {
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Access-Control-Allow-Origin': '*' });
  res.end(html);
}

http.createServer((req, res) => {
  if (req.method === 'OPTIONS') {
    res.writeHead(204, { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET' });
    res.end();
    return;
  }

  const reqUrl = new URL(req.url ?? '/', `http://localhost:${PORT}`);
  if (reqUrl.pathname !== '/fetch') {
    respond(res, 404, 'not found');
    return;
  }

  const raw = reqUrl.searchParams.get('url');
  if (!raw) {
    respond(res, 400, 'missing url param');
    return;
  }

  let target;
  try {
    target = new URL(decodeURIComponent(raw));
  } catch {
    respond(res, 400, 'invalid url');
    return;
  }

  if (!['http:', 'https:'].includes(target.protocol)) {
    respond(res, 400, 'blocked');
    return;
  }

  if (isBlockedHost(target.hostname)) {
    respond(res, 400, 'blocked');
    return;
  }

  const client = target.protocol === 'https:' ? https : http;
  const options = {
    hostname: target.hostname,
    port: target.port || (target.protocol === 'https:' ? 443 : 80),
    path: target.pathname + target.search,
    method: 'GET',
    headers: {
      'User-Agent': 'Mozilla/5.0 (compatible; PaceReader/1.0)',
      Accept: 'text/html,application/xhtml+xml',
    },
    timeout: TIMEOUT_MS,
  };

  const upstream = client.request(options, (upRes) => {
    const ct = upRes.headers['content-type'] ?? '';
    if (!ct.includes('text/html') && !ct.includes('application/xhtml')) {
      upRes.destroy();
      respond(res, 422, 'not-html');
      return;
    }

    if (upRes.statusCode && upRes.statusCode >= 400) {
      upRes.destroy();
      respond(res, upRes.statusCode, `upstream ${upRes.statusCode}`);
      return;
    }

    const chunks = [];
    let total = 0;

    upRes.on('data', (chunk) => {
      total += chunk.length;
      if (total > MAX_BYTES) {
        upRes.destroy();
        respond(res, 413, 'too large');
        return;
      }
      chunks.push(chunk);
    });

    upRes.on('end', () => {
      respondHtml(res, Buffer.concat(chunks).toString('utf8'));
    });

    upRes.on('error', () => {
      respond(res, 502, 'upstream error');
    });
  });

  upstream.on('timeout', () => {
    upstream.destroy();
    respond(res, 504, 'timeout');
  });

  upstream.on('error', (err) => {
    if (err.message?.includes('ECONNREFUSED') || err.message?.includes('ENOTFOUND')) {
      respond(res, 502, 'network');
    } else {
      respond(res, 502, 'upstream error');
    }
  });

  upstream.end();
}).listen(PORT, () => {
  console.log(`pace-proxy listening on :${PORT}`);
});
