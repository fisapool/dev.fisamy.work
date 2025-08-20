# code.fisamy.work — Coder‑lite (OpenVSCode + Caddy)

Minimal, OSS replacement for Coder using **one container per user** with **OpenVSCode Server**,
reverse‑proxied by **Caddy**. Includes per‑user **CPU/RAM/PID limits**, optional **disk quotas** (XFS),
and an **idle reaper** (systemd timer) to stop inactive containers.

> TL;DR: Each user gets their own container at `USER.code.fisamy.work`, protected by Caddy basic_auth or Cloudflare Access.
> Storage lives at `/srv/devdata/USER`. You control limits in Compose; quotas via XFS; idle autostop via systemd.

---

## Requirements

- Ubuntu 22.04+ (recommended), root/sudo
- Docker Engine + Docker Compose v2 (`docker compose`)
- Caddy (host‑installed) or Cloudflare Tunnel (if you prefer)
- DNS: `A` records for each subdomain (e.g. `aria.code.fisamy.work`) pointing to this server
- Optional: XFS **project quotas** enabled on the disk that backs `/srv/devdata`

---

## Quick start (no quotas)

```bash
# 1) Get files
sudo mkdir -p /opt/coder-lite && cd /opt/coder-lite
sudo tar -xzf /path/to/code-fisamy-work-coder-lite.tgz || true  # if you downloaded the .tgz

# OR if you downloaded the zip:
#   unzip code-fisamy-work-coder-lite.zip -d /opt && mv /opt/code-fisamy-work-coder-lite /opt/coder-lite
#   cd /opt/coder-lite

# 2) Prepare data root
sudo mkdir -p /srv/devdata
sudo chown -R root:root /srv/devdata
sudo chmod 755 /srv/devdata

# 3) Provision a user (creates /srv/devdata/aria and appends to docker-compose.override.yml)
# Option A: Bash helper (simple)
sudo ./scripts/devctl aria --cpu 2 --ram 4g --disk 20 --port 13001

# Option B: Python CLI (enhanced features: config, caddy integration, healthcheck)
cd devctl && sudo pip install -r requirements.txt && cd ..
sudo python -m devctl create aria \
  --cpu 2 --ram 4g --disk 20 \
  --port 13001 \
  --domain-base code.fisamy.work \
  --healthcheck-enable --gpu \
  --network devnet \
  --caddy-file Caddyfile \
  --basic-auth-hash aria:'$2y$05$replace_me_with_bcrypt' \
  --reload-caddy

# 4) Start only that user’s workspace
docker compose up -d aria

# 5) Caddy
# Edit Caddyfile -> duplicate block per user; set basicauth hash; then:
sudo cp Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy || sudo systemctl restart caddy
```

Open: https://aria.code.fisamy.work (log in with the basic auth user you configured in Caddy).

---

## Enable XFS disk quotas (recommended)

> Only if your data filesystem is **XFS**.

1) Ensure the data mount (e.g. `/srv/devdata`) is XFS with `pquota`:
```bash
sudo apt-get update && sudo apt-get install -y xfsprogs
grep /srv/devdata /etc/fstab
# Example fstab line:
# UUID=... /srv/devdata xfs defaults,pquota 0 2
sudo mount -o remount,pquota /srv/devdata
```

2) Now when you run `devctl USER --disk 20`, it will assign a project quota of 20GiB.

> If you’re on btrfs, you can manually create subvolumes and set qgroup limits; the repo doesn’t automate that.

---

## Idle autostop (cost control)

Install the systemd unit + timer and script:

```bash
sudo cp scripts/dev-idle-reaper.sh /usr/local/sbin/
sudo chmod +x /usr/local/sbin/dev-idle-reaper.sh
sudo cp systemd/dev-idle-reaper.service /etc/systemd/system/
sudo cp systemd/dev-idle-reaper.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dev-idle-reaper.timer
```

Defaults: stop containers idle for **45 min** with CPU ≤ **1%** and traffic ≤ **2KB/s**.
Tune via `Environment=` in the service or edit the timer unit.

---

## Auth

- **Basic auth** (in this repo via Caddyfile) – quick and fine for small teams.
- **Cloudflare Zero Trust** – stronger SSO/mfa/device checks, no password storage in Caddy.
- You can run both: keep basic auth as fallback; put CF Access in front.

Generate a bcrypt hash (store in Caddyfile):
```bash
sudo apt-get install -y apache2-utils
htpasswd -nbB USER 'StrongPassword' | sed 's/\$/\$\$/g'
```

---

## File layout

```
.
├── Caddyfile
├── README.md
├── docker-compose.override.sample.yml
├── docker-compose.yml
├── devctl
│   ├── README.md
│   ├── requirements.txt
│   └── (Python package: devctl)
├── scripts
│   ├── dev-idle-reaper.sh
│   └── devctl
└── systemd
    ├── dev-idle-reaper.service
    └── dev-idle-reaper.timer
```

---

## Multi‑user flow

1) Create DNS `A` records: `USER.code.fisamy.work → server IP`.
2) `sudo ./scripts/devctl USER --cpu 2 --ram 4g --disk 20 --port 13001`
3) Duplicate the Caddyfile block for that user; set basicauth line.
4) `docker compose up -d USER` + `sudo systemctl reload caddy`
5) Done.

Repeat per user.

---

## Notes / knobs

- **CPU/RAM**: set per‑service in `docker-compose.override.yml` via `cpus`, `mem_limit`, `memswap_limit`, `pids_limit`, `ulimits`.
- **PID/file‑desc caps**: stop fork/file storms (`pids_limit`, `ulimits.nofile`, `ulimits.nproc`).
- **GPU**: uncomment `device_requests` block and set `count: 1` + `device_ids` if you want to pin cards. Needs NVIDIA Container Toolkit.
- **Security headers**: already in Caddyfile. CSP blocks framing; tighten as needed.
- **Backups**: `tar` or `rsync` `/srv/devdata/*` per user dir.
- **Logs**: `docker logs dev-USER`, `journalctl -u dev-idle-reaper.timer -u dev-idle-reaper.service`.
- **TZ**: default `Asia/Kuala_Lumpur`; change in compose or per‑service env.

---

## Remove a user

```bash
docker compose stop USER && docker compose rm -f USER
sudo rm -rf /srv/devdata/USER
sudo sed -i '/^USER:$/,/^\S/ d' docker-compose.override.yml  # remove block; verify after
# Also remove the user block in Caddyfile; then:
sudo systemctl reload caddy
```

> Keep backups. Deleting data is permanent.

---

## Why this beats Coder (for you)

- Zero vendor coupling, OSS, fast to ship.
- Every user is isolated at the container boundary with hard caps.
- You add SSO later (CF Access) without changing the stack.
