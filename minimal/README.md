Minimal "Coder-lite" (OpenVSCode Server + Caddy)

Overview
- One container per developer running OpenVSCode Server.
- One persistent volume per developer for home/workspace.
- Caddy terminates TLS and proxies per-user subdomains to the right container.
- Optional security: Caddy basic_auth or Cloudflare Zero Trust (recommended in production).

Prerequisites
- Linux host with Docker and Docker Compose v2.
- DNS: wildcard pointing to your host, e.g. `*.devbox.example.com` → server IP.
- Ports 80/443 open to the Internet.

Quick Start
1) Configure domain
- Choose a base domain, e.g. `devbox.example.com`. Create DNS wildcard `*.devbox.example.com` to your host IP.

2) Start Caddy reverse proxy
```bash
cd minimal
docker compose up -d caddy
```

3) Create a developer workspace
```bash
# Syntax: ./scripts/create_dev.sh <user> <domain> [--basic-auth user:pass]
./scripts/create_dev.sh alice alice.devbox.example.com --basic-auth alice:StrongPass123!
```
- This starts container `ovscode-alice` with volume `ovscode_data_alice` and adds a Caddy site entry.
- Visit https://alice.devbox.example.com and sign in with the provided basic auth credentials.

4) Remove a developer workspace
```bash
# Syntax: ./scripts/remove_dev.sh <user> [--delete-volume]
./scripts/remove_dev.sh alice --delete-volume
```

Security Notes
- Prefer Cloudflare Zero Trust or your IdP for SSO in front of Caddy where possible.
- If using `--basic-auth`, the script generates a hashed password (via Caddy) and stores only the hash in the Caddy site file.
- OpenVSCode Server has no built-in auth; never expose containers directly.

Resource Controls
- Each container is isolated and can be constrained. Edit `scripts/create_dev.sh` to set `--cpus` and `--memory` limits if desired.

Structure
- `docker-compose.yml`: Runs Caddy with TLS and loads site configs from `caddy/sites/`.
- `caddy/Caddyfile`: Global config; imports `sites/*.caddy` for per-user domains.
- `scripts/create_dev.sh`: Creates a per-user OpenVSCode container + Caddy site and reloads Caddy.
- `scripts/remove_dev.sh`: Removes the container/site and reloads Caddy.

Troubleshooting
- Check Caddy logs: `docker compose logs -f caddy`
- Reload Caddy manually: `docker compose exec caddy caddy reload --config /etc/caddy/Caddyfile`
- Verify container: `docker ps | grep ovscode-`

