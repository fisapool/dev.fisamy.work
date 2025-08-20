# Coder Hardening & Templates (Ops Runbook)

This runbook captures the exact steps to secure Coder, validate DNS, create no‑GPU and GPU templates, wire tokens, add DB backups, and smoke test the whole flow. All commands are copy‑ready for a Ubuntu host with Docker and Caddy.

## 0) Lock It Down

### UI Method (Original)

- Disable self‑sign up: Admin → Admin settings → Access → turn off public signup.
- Restrict domains: Admin → Admin settings → Access → Allowed email domains → your org domains only.
- Turn on 2FA for your user: User menu → Account → Security → enable 2FA.
- Create a bot user (e.g., `bff-bot`) and mint a PAT with the minimal scopes needed for workspace management.

### CLI Method (Recommended for Repeatability)

```bash
# Authenticate coder CLI first (ensure CODER_HOST/CODER_URL and token are set)

# List organizations to find your ORG_ID
coder organizations list

# Disable public signup
coder admin org-settings update --org-id <ORG_ID> --allow-user-signup=false

# Restrict to your domains only
coder admin org-settings update --org-id <ORG_ID> --allowed-domains="fisamy.work"

# Enforce MFA requirement
coder admin org-settings update --org-id <ORG_ID> --require-mfa=true

# Create a bot user (adjust email/username as needed)
coder users create --email bff-bot@fisamy.work --username bff-bot

# Create a Personal Access Token for automation (scope as needed)
# Run as the bot user context; store securely in /etc/fisamy/coder.env
coder tokens create --name "deployment-bot" --scope "admin"
```

## 1) DNS / Wildcard Check

Ensure both records exist and resolve to your server IP:

```
A coder.fisamy.work → <server IP>
A *.coder.fisamy.work → <server IP>
```

### Manual DNS Verification
Quick checks from any shell:

```bash
dig +short coder.fisamy.work A
dig +short '*.coder.fisamy.work' A
```

### Cloudflare API Automation
If using Cloudflare, automate DNS record creation:

```bash
# Set your Cloudflare credentials and zone ID
export CLOUDFLARE_API_TOKEN="your_api_token_here"
export ZONE_ID="your_zone_id_here"
export SERVER_IP="your_server_ip_here"

# Create A record for coder.fisamy.work
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "coder.fisamy.work",
    "content": "'$SERVER_IP'",
    "ttl": 1,
    "proxied": true
  }'

# Create wildcard A record for *.coder.fisamy.work
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "*.coder.fisamy.work",
    "content": "'$SERVER_IP'",
    "ttl": 1,
    "proxied": true
  }'

# Verify records were created
curl -s "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | jq '.result[] | {name, type, content}'
```

If either is missing, workspace apps and forwarded ports will fail to open.

## 2) No‑GPU Template (fast sanity check)

UI: Templates → New → Create from scratch → Provider: Docker

- Default image: `ubuntu:22.04`
- Startup script (one‑time):

```bash
apt-get update
apt-get install -y curl git sudo ca-certificates
curl -fsSL https://code-server.dev/install.sh | sh
useradd -m coder || true
sudo -u coder bash -lc 'code-server --bind-addr 0.0.0.0:13337 --auth none &'
```

- App:
  - Name: VS Code
  - URL: `http://localhost:13337`
  - Icon: `vscode`
- Autostop: 30–60 min idle.

Create a workspace from this template and open the app. If it loads, Docker wiring is good.

## 3) GPU Template (for AI workloads)

- Base image: `nvidia/cuda:12.4.1-runtime-ubuntu22.04`
- Docker options → Device requests → GPU: `1` (or `all`).
- Environment:

```
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=all
```

- Startup script (example Python toolchain):

```bash
apt-get update
apt-get install -y python3 python3-venv python3-pip curl git sudo ca-certificates
python3 -m venv /opt/venv
source /opt/venv/bin/activate
pip install --upgrade pip wheel
# Choose your stack – examples:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install jupyter jupyterlab numpy pandas matplotlib
```

- Apps to add:
  - Jupyter: `http://localhost:8888`
  - Open WebUI (if you install it): `http://localhost:3000`

Test inside the workspace:

```bash
nvidia-smi
python3 -c "import torch; print(torch.cuda.is_available())"
```

## 4) Wire Tokens into Services (host)

Create secure env files on the host and reference them in Docker Compose.

```bash
sudo mkdir -p /etc/fisamy && sudo chmod 700 /etc/fisamy

sudo tee /etc/fisamy/coder.env >/dev/null <<'EOF'
CODER_HOST=https://coder.fisamy.work
CODER_API_TOKEN=PASTE_CODER_PAT
EOF

sudo tee /etc/fisamy/cloudflare.env >/dev/null <<'EOF'
DOMAIN_MANAGER_PROVIDER=cloudflare
DOMAIN_MANAGER_TOKEN=PASTE_CF_API_TOKEN
DOMAIN_MANAGER_ZONE=fisamy.work
EOF

sudo chmod 600 /etc/fisamy/*.env
```

This repo’s `back-end/docker-compose.yml` is already set to read both files via `env_file`.

## 5) Postgres Backups (nightly)

If your Coder deployment uses Postgres, add a nightly dump on the host (adjust the container name if needed):

```bash
sudo tee /usr/local/sbin/backup_coder_db.sh >/dev/null <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ts=$(date +%F-%H%M)
docker exec -i coder-postgres pg_dump -U coder coder | gzip > /var/backups/coder-$ts.sql.gz
find /var/backups -name 'coder-*.sql.gz' -mtime +14 -delete
SH

sudo chmod +x /usr/local/sbin/backup_coder_db.sh
echo '0 3 * * * root /usr/local/sbin/backup_coder_db.sh' | sudo tee /etc/cron.d/coder-backup >/dev/null
sudo mkdir -p /var/backups
```

## 6) Monitoring & Uptime

- Put Coder behind Caddy (you likely already did).
- Add Uptime Kuma checks for:
  - `https://coder.fisamy.work`
  - A sample workspace app URL (to catch wildcard/DNS issues)
- Optional: Cloudflare Firewall – restrict admin routes to your IP.

## 7) Quotas / Plans

Create resource presets via templates/variables:

- Lite: 2 vCPU / 4GB / 0 GPU / autostop 30m
- Pro: 8 vCPU / 16GB / 1 GPU / autostop 60m

Your BFF maps user plan → allowed template/vars.

## 8) SSO

Admin → Authentication → configure Google/GitHub/Auth0. Force SSO for normal users; keep local login for admin/bot only.

## 9) Golden Images

Once a stack is stable, bake a custom Docker image with all deps (OpenVINO, PyTorch, FFmpeg, SDXL weights mount path, etc.). Point templates to the image to cut cold‑start from minutes to seconds.

## 10) Smoke Test

- Create one non‑GPU and one GPU workspace.
- Open VS Code app, Jupyter app.
- Stop/start; confirm autostop works.
- From any host with the env set (or from `/etc/fisamy/coder.env`):

```bash
curl -s -H "Authorization: Bearer $CODER_API_TOKEN" \
  "$CODER_HOST/api/v2/workspaces" | jq '.[].name'
```

---

### Appendix: Caddy Tips

- Ensure `coder.fisamy.work` is proxied to your Coder service with TLS.
- If hosting both dashboard and BFF, keep `/api/*` proxy first in the site block to avoid conflicts with SPA routing.
