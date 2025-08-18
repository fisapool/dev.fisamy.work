# VSCode Hosting Provider — Backend Stacks (MVP & Provider‑grade)

You said: run it like a *real* provider. Done. Two stacks:

- **MVP:** per‑user OpenVSCode containers + Caddy + Basic Auth (simple, <10 users).
- **Provider‑grade (recommended):** Coder OSS + Postgres + Caddy with wildcard dev‑URLs, quotas, idle autosuspend, and Docker workspaces.

---

## 0) DNS & TLS (required)

Create two A records to your server IP:

- `dev.fisamy.work`
- `*.dev.fisamy.work`

If you're using Cloudflare, set **DNS‑only (grey cloud)** for first boot so Caddy can issue Let's Encrypt certs. You can flip to orange later with an origin cert or keep DNS‑only.

---

## 1) Host prerequisites

```bash
# Ubuntu 22.04+
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# re-login or: newgrp docker
```

Recommended: open only 80/443 on your firewall, everything else stays inside Docker.

---

## 2) MVP Track (fastest way to ship)

**Files:** `vscode-hosting-mvp/docker-compose.yml` and `vscode-hosting-mvp/Caddyfile`

1. Generate a bcrypt hash for the Basic Auth password:
   ```bash
   docker run --rm caddy caddy hash-password --plaintext 'SuperPass'
   ```
2. Put that hash in the Caddyfile (replace `REPLACE_WITH_HASHED_PASSWORD`).  
3. Boot:
   ```bash
   cd vscode-hosting-mvp
   docker compose up -d
   ```
4. Test: `https://alice.dev.fisamy.work` → enter user/pass → OpenVSCode loads.

**Add users:** duplicate the `alice-openvscode` service in compose, e.g. `bob-openvscode`, then add a new site block in Caddyfile for `bob.dev.fisamy.work` pointing to `bob-openvscode:3000` with its own `basicauth` user+hash.

**Pros:** dead simple. **Cons:** manual user mgmt, no quotas, no billing hooks.

---

## 3) Provider‑grade Track (recommended)

**Files:** `coder-provider/docker-compose.yml` and `coder-provider/Caddyfile`

What you get:
- Coder UI at `https://dev.fisamy.work`
- Wildcard dev‑URLs `*.dev.fisamy.work` for workspace apps (VSCode, Jupyter, web servers) routed through Coder
- Postgres for user & workspace metadata
- Idle autosuspend (default 30m, change via env), max CPU/RAM/disk caps

### Boot

```bash
cd coder-provider
export CODER_PG_PASSWORD="$(openssl rand -base64 24 | tr -d '=+/')"
export CODER_ACCESS_URL="https://dev.fisamy.work"
# Optional policy caps and idle timeout
export CODER_MAX_WORKSPACE_CPUS=6
export CODER_MAX_WORKSPACE_MEMORY=16Gi
export CODER_MAX_WORKSPACE_DISK=100Gi
export CODER_DEFAULT_WORKSPACE_IDLE_TIMEOUT=30m

docker compose up -d

# Create the first admin
docker exec -it coder coder users create   --email admin@fisamy.work --username admin   --password 'ChangeMe$trong' --site-admin
```

Open `https://dev.fisamy.work` → sign in.

### Create a template (OpenVSCode)

Inside Coder UI → **Templates → Create** → use a Docker‑based workspace with this image:

```
ghcr.io/gitpod-io/openvscode-server:latest
```

Add these **startup commands** (IDE on 3000):
```bash
export OPENVSCODE_SERVER_CONNECTION_TOKEN="$CODER_TOKEN"
/openvscode-server/bin/openvscode-server --host 0.0.0.0 --port 3000
```

Expose **port 3000** as a **Dev URL** (public or authenticated). Users will get IDE at something like:
```
vscode--myworkspace--username.dev.fisamy.work
```

### Plans / quotas

Use **Policies** and **Parameters** in the template:

- CPU: `2 / 4 / 6`
- RAM: `4Gi / 8Gi / 16Gi`
- Disk: `20Gi / 40Gi / 100Gi`
- Idle timeout: default 30–60 min
- Max caps are set via compose env (`CODER_MAX_*`).

### SSO (OIDC)

Coder supports GitHub, Google, and generic OIDC. In **Admin → Authentication**, add a provider and set:
- Callback URL: `https://dev.fisamy.work/oidc/callback`
- Allowed redirect origins: `https://dev.fisamy.work`

(If you want Cloudflare Access instead, terminate Access at the edge and pass email headers to Coder—ping me for the exact policy.)

### Backups

- Postgres: schedule `pg_dump` to S3‑compatible storage (e.g., Backblaze) daily.
- `coder_data`: snapshot weekly if you store templates locally.

### Monitoring

- Add `caddy` and `coder` logs to Loki/Promtail or vector → Grafana.
- UptimeKuma checks for `https://dev.fisamy.work/healthz` (Coder exposes health endpoints).

---

## 4) Pricing (starter)

- **Solo** (2 vCPU / 4GB / 20GB): RM 30/mo
- **Pro** (4 vCPU / 8GB / 40GB): RM 60/mo
- **Team** (4 seats): RM 199/mo

Auto‑stop idle workspaces, wipe after 30 days inactive. Stripe webhooks → small worker calls Coder API to create/disable users and set policy group.

---

## 5) Security notes

- Keep **only** ports 80/443 open.
- Use **DNS‑01** if you later want orange‑cloud/CF proxy; for now HTTP‑01 is fine.
- Rotate admin password, enable SSO quickly.
- Set per‑template non‑root user and mount a dedicated volume for `/home` if you need persistence.

---

## FAQ

**Q: Do I need wildcard DNS?**  
Yes, for Coder dev‑URLs. Both `dev.fisamy.work` and `*.dev.fisamy.work` should resolve to your server.

**Q: Can I mix GPU workspaces?**  
Yes if the host has NVIDIA drivers + `nvidia-container-toolkit`; add `"deploy.resources.reservations.devices"` in the template. Start CPU‑only first.

**Q: Where do I add custom CLIs/dotfiles?**  
Bake your own image (FROM `ghcr.io/gitpod-io/openvscode-server`) with Node/Python/Go, then reference it in the template.

---

## OpenVSCode Template (Terraform CLI)

If you prefer managing the template via Terraform + Coder CLI (rather than creating it in the UI), use the `openvscode-template/` directory.

1) Update Coder CLI to match server

```bash
curl -fsSL https://dev.fisamy.work/install.sh | sh
coder version  # should match your server (e.g., v2.25.1+3bf6a00)
```

2) Initialize Terraform (generates `.terraform.lock.hcl`)

```bash
cd openvscode-template
./init.sh        # or: terraform init
```

Commit the generated `.terraform.lock.hcl` so providers are cached.

3) Push the template

From repo root:

```bash
coder templates push vscode-ai --directory backend/openvscode-template
```

Or run inside the folder:

```bash
cd openvscode-template
coder templates push vscode-ai
```

Notes
- Expects Docker on the provisioner; provisions OpenVSCode image `ghcr.io/gitpod-io/openvscode-server:latest`.
- Template parameters include `workspace_name`, `cpu`, `ram`, `disk`, and optional AI vars: `openai_api_key`, `openai_base_url`, `codeium_api_key`, `tabby_endpoint`.
- IDE runs on port 3000 and is exposed as a Dev URL via `coder_app`.
