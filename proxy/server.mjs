/**
 * Pace fetch proxy — internal Docker sidecar.
 *
 * Accepts: GET /fetch?url=<encoded>
 * Returns: the raw HTML of the target page, or an error status.
 *
 * Only reachable from the pace nginx container (not Traefik-exposed).
 * Blocks private/loopback addresses so the container can't be used as
 * an SSRF vector against internal VPS services.
 */

import { createServer } from 'node:http';
import { URL } from 'node:url';

const PORT = 3001;
const TIMEOUT_MS = 20_000;
const MAX_BYTES = 5 * 1024 * 1024; // 5 MB

// Private / loopback CIDR blocks to block (simple prefix checks).
const BLOCKED_HOSTS = [
  'localhost', '127.', '0.', '10.', '169.254.',
  '192.168.', '::1', '[::1]',
];

function isBlockedHost(hostname) {
  const h = hostname.toLowerCase();
  return BLOCKED_HOSTS.some((prefix) => h === prefix.slice(0, -1) || h.startsWith(prefix));
}

createServer(async (req, res) => {
  if (req.method !== 'GET') {
    res.writeHead(405); res.end('Method not allowed'); return;
  }

  const reqUrl = new URL(req.url, `http://localhost:${PORT}`);
  if (reqUrl.pathname !== '/fetch') {
    res.writeHead(404); res.end('Not found'); return;
  }

  const target = reqUrl.searchParams.get('url');
  if (!target) {
    res.writeHead(400); res.end('Missing url parameter'); return;
  }

  let parsed;
  try { parsed = new URL(target); } catch {
    res.writeHead(400); res.end('Invalid URL'); return;
  }

  if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
    res.writeHead(400); res.end('Only http and https URLs are supported'); return;
  }

  if (isBlockedHost(parsed.hostname)) {
    res.writeHead(403); res.end('Blocked host'); return;
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const upstream = await fetch(target, {
      signal: controller.signal,
      redirect: 'follow',
      headers: {
        'User-Agent':
          'Mozilla/5.0 (compatible; Pace-Reader/1.0; +https://pace.solay.cloud)',
        Accept: 'text/html,application/xhtml+xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
    });

    clearTimeout(timer);

    const ct = upstream.headers.get('content-type') ?? '';
    if (!ct.includes('text/html') && !ct.includes('application/xhtml')) {
      res.writeHead(422); res.end('URL does not return HTML'); return;
    }

    // Stream with size cap.
    const reader = upstream.body?.getReader();
    if (!reader) { res.writeHead(502); res.end('Empty body'); return; }

    const chunks = [];
    let total = 0;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.length;
      if (total > MAX_BYTES) { reader.cancel(); break; }
      chunks.push(value);
    }

    const html = Buffer.concat(chunks).toString('utf-8');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);

  } catch (err) {
    clearTimeout(timer);
    if (err.name === 'AbortError') {
      res.writeHead(504); res.end('Request timed out');
    } else {
      res.writeHead(502); res.end('Failed to fetch URL');
    }
  }
}).listen(PORT, () => {
  console.log(`[pace-proxy] listening on port ${PORT}`);
});
