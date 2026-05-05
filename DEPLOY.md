# Pace — Deploy Guide

## Target
- Host: 76.13.192.55 (solay.cloud VPS)
- Domain: https://pace.solay.cloud
- Stack: Docker + Traefik (Let's Encrypt) shared with crea.solay.cloud and ai-salon.solay.cloud

## Services

| Container    | Role                                                      |
|--------------|-----------------------------------------------------------|
| `pace`       | nginx serving the built PWA                               |
| `pace-proxy` | Internal Node.js fetch proxy for URL article extraction   |

`pace-proxy` is NOT Traefik-exposed. Only `pace` (nginx) can reach it, via the `proxy_pass` in nginx.conf. No external traffic touches it.

## First-time setup on the VPS

```bash
ssh root@76.13.192.55
mkdir -p /opt/pace
```

Copy `compose.yml` and the `proxy/` directory to `/opt/pace/` on the VPS:

```bash
scp compose.yml root@76.13.192.55:/opt/pace/
scp -r proxy/ root@76.13.192.55:/opt/pace/
```

## Deploy from local

```bash
cd /Users/philippsolay/Library/CloudStorage/Dropbox/Projects/Pace

# Build the pace image locally
docker build -t pace:latest .

# Transfer to VPS
docker save pace:latest | ssh root@76.13.192.55 "docker load"

# Bring up (or restart) both services
ssh root@76.13.192.55 "cd /opt/pace && docker compose up -d"
```

`pace-proxy` uses the official `node:20-alpine` image pulled directly by Docker on the VPS — no separate build step needed.

## Local development

To use URL extraction locally, run the proxy alongside the Vite dev server:

```bash
# Terminal 1
node proxy/server.mjs

# Terminal 2
npm run dev
```

The Vite dev server proxies `/api/fetch` → `localhost:3001` automatically.

## DNS

Add an A record in your DNS provider pointing `pace.solay.cloud` → `76.13.192.55`. Traefik handles the cert issuance on first request.

## Verify

```bash
curl -I https://pace.solay.cloud/
# HTTP/2 200 — you should see cache-control headers

# Test the fetch proxy (from inside the pace container):
docker exec pace wget -qO- 'http://pace-proxy:3001/fetch?url=https%3A%2F%2Fexample.com' | head -5
```

## Rollback

```bash
ssh root@76.13.192.55 "cd /opt/pace && docker compose down"
# Build the previous tag locally, docker save | ssh | docker load, up -d
```

## Notes
- `pace-proxy` logs no URLs (privacy); only errors and the startup message are printed
- PWA service worker handles offline; add-to-home-screen gives the installed experience
- Web Share Target GET shares land on /share — routed to paste or URL import flow
- URL extraction works best on text-heavy articles; JS-rendered pages and paywalls will fail gracefully with a user-facing error message
