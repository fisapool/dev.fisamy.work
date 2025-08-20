devctl (Python CLI)

Overview
- Enhanced CLI to manage per-user OpenVSCode services, Compose, and Caddy.
- Implements the Phase 1A + 2A plan: config, validation, image pinning, healthchecks, domain auto-gen, and Caddy backup/validate/reload.

Install
1) Python 3.10+
2) Optional virtualenv
3) Install deps:
   pip install -r requirements.txt

Usage
- Create user:
  python -m devctl create USER \
    --cpu 2 --ram 4g --disk 20 \
    --port 13001 \
    --domain-base code.fisamy.work \
    --image-version latest \
    --healthcheck-enable \
    --gpu \
    --basic-auth-hash USER:'$2y$05$YourBcryptHashHere' \
    --network devnet \
    --caddy-file Caddyfile \
    --reload-caddy

- Delete user:
  python -m devctl delete USER [--purge]

- List users:
  python -m devctl list

- Status:
  python -m devctl status USER

- Interactive wizard:
  python -m devctl wizard

Config
- Precedence: --config FILE > ~/.config/devctl/config.yml > /etc/devctl.conf
- Example keys: data_root, domain_base, image, tz, caddy_file, network, defaults.{cpu,ram,disk}, xfs.enable

Example ~/.config/devctl/config.yml
  data_root: /srv/devdata
  domain_base: code.fisamy.work
  image_version: "1.92.3"
  tz: Asia/Kuala_Lumpur
  caddy_file: /opt/coder-lite/Caddyfile
  network: devnet
  defaults:
    cpu: "2"
    ram: "4g"
    disk: 20
    healthcheck: true
    gpu: false
    start_port: 13001

Notes
- Requires ruamel.yaml for safe Compose edits; install via requirements.
- Caddy validation/reload is attempted if the binary/systemd is present; otherwise it prints instructions.
