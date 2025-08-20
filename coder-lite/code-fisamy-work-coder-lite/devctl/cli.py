import os
import sys
import shutil
import socket
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

import typer
from rich import print
from rich.console import Console
from rich.table import Table

try:
    from ruamel.yaml import YAML
except Exception as e:  # pragma: no cover
    YAML = None  # type: ignore

app = typer.Typer(add_completion=False, help="Manage per-user OpenVSCode services (Compose + Caddy)")
console = Console()

DEFAULTS: Dict[str, Any] = {
    "data_root": "/srv/devdata",
    "domain_base": None,
    "image_version": "latest",
    "tz": "Asia/Kuala_Lumpur",
    "caddy_file": "Caddyfile",
    "network": "devnet",
    "defaults": {
        "cpu": "2",
        "ram": "4g",
        "disk": 20,
        "healthcheck": False,
        "gpu": False,
        "start_port": 13001,
    },
}

def load_yaml_cfg(path: Path) -> Dict[str, Any]:
    if not path.exists() or YAML is None:
        return {}
    y = YAML()
    try:
        data = y.load(path.read_text()) or {}
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}

def load_kv_conf(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    out: Dict[str, Any] = {}
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" in s:
            k, v = s.split("=", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out

def merge_cfg(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    res = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(res.get(k), dict):
            res[k] = merge_cfg(res[k], v)  # type: ignore[index]
        else:
            res[k] = v
    return res

def effective_config(cli_config: Optional[Path]) -> Dict[str, Any]:
    cfg = dict(DEFAULTS)
    etc = Path("/etc/devctl.conf")
    if etc.exists():
        cfg = merge_cfg(cfg, load_yaml_cfg(etc) if etc.suffix in (".yml", ".yaml", ".json") else load_kv_conf(etc))
    user = Path.home() / ".config/devctl/config.yml"
    if user.exists():
        cfg = merge_cfg(cfg, load_yaml_cfg(user))
    if cli_config:
        cfg = merge_cfg(cfg, load_yaml_cfg(cli_config) if cli_config.suffix in (".yml", ".yaml", ".json") else load_kv_conf(cli_config))
    return cfg

@app.callback()
def _main(ctx: typer.Context, config: Optional[Path] = typer.Option(None, help="Config file (YAML or KEY=VALUE)")):
    ctx.obj = effective_config(config)


def load_yaml(path: Path):
    if YAML is None:
        raise RuntimeError("ruamel.yaml is required. Install with: pip install -r devctl/requirements.txt")
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.load(f) or {}
    return yaml, data


def save_yaml(yaml, data, path: Path):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)
    tmp.replace(path)


def ensure_override(path: Path):
    if not path.exists():
        if YAML is None:
            raise RuntimeError("ruamel.yaml required to create compose override")
        yaml = YAML()
        data = {"version": "3.9", "services": {}}
        save_yaml(yaml, data, path)
        return yaml, data
    return load_yaml(path)


def ensure_network(name: str):
    try:
        subprocess.run(["docker", "network", "inspect", name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        subprocess.run(["docker", "network", "create", name], check=True)
        return True


def resolve_host(host: str) -> Optional[str]:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def caddy_backup(caddy_file: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup = caddy_file.with_name(caddy_file.name + f".bak.{ts}")
    shutil.copy2(caddy_file, backup)
    return backup


def caddy_validate(caddy_file: Path) -> bool:
    cmd = shutil.which("caddy")
    if not cmd:
        console.print("[yellow]caddy binary not found; skipping validation[/yellow]")
        return True
    res = subprocess.run([cmd, "validate", "--config", str(caddy_file)])
    return res.returncode == 0


def caddy_reload() -> bool:
    # Prefer systemctl reload caddy; fallback to caddy reload if running in container
    if shutil.which("systemctl"):
        res = subprocess.run(["sudo", "systemctl", "reload", "caddy"])  # may prompt for sudo
        if res.returncode == 0:
            return True
    cmd = shutil.which("caddy")
    if cmd:
        res = subprocess.run([cmd, "reload"])  # expects Caddyfile in default path
        return res.returncode == 0
    console.print("[yellow]Could not reload caddy (no systemctl or caddy). Please reload manually.[/yellow]")
    return False


def service_block(
    user: str,
    image: str,
    port: int,
    data_root: Path,
    cpu: str,
    ram: str,
    tz: str,
    network: Optional[str],
    health: bool,
    gpu: bool,
):
    svc = {
        "image": image,
        "container_name": f"dev-{user}",
        "environment": [f"TZ={tz}"],
        "ports": [f"127.0.0.1:{port}:3000"],
        "volumes": [f"{data_root}/{user}:/home/openvscode"],
        "restart": "unless-stopped",
        "mem_limit": ram,
        "memswap_limit": ram,
        "cpus": cpu,
        "pids_limit": 512,
        "ulimits": {"nofile": {"soft": 8192, "hard": 8192}, "nproc": 1024},
        "labels": ["fisamy.role=ovscode", f"fisamy.user={user}"],
    }
    if network:
        svc["networks"] = [network]
    if health:
        svc["healthcheck"] = {
            "test": ["CMD-SHELL", "bash -c ': </dev/tcp/127.0.0.1/3000' || exit 1"],
            "interval": "15s",
            "timeout": "3s",
            "retries": 10,
            "start_period": "10s",
        }
    if gpu:
        svc["device_requests"] = [
            {
                "driver": "nvidia",
                "count": 1,
                "capabilities": [["gpu"]],
            }
        ]
    return svc


def caddy_site_block(host: str, port: int, user: str, basic_auth: Optional[str]) -> str:
    basicauth_block = ""
    if basic_auth:
        try:
            auth_user, auth_hash = basic_auth.split(":", 1)
            basicauth_block = f"  basicauth /* {{\n    {auth_user} {auth_hash}\n  }}\n"
        except ValueError:
            # If parsing fails, leave commented instruction instead
            basicauth_block = f"  # basicauth /* {{\n  #   {user} $2y$05$replace_me_with_a_real_bcrypt_hash\n  # }}\n"
    else:
        basicauth_block = f"  # basicauth /* {{\n  #   {user} $2y$05$replace_me_with_a_real_bcrypt_hash\n  # }}\n"

    return (
        f"{host} {{\n"
        f"  encode gzip\n"
        f"{basicauth_block}"
        f"  reverse_proxy 127.0.0.1:{port}\n"
        f"  header {{\n"
        f"    Strict-Transport-Security \"max-age=31536000; includeSubDomains; preload\"\n"
        f"    X-Content-Type-Options \"nosniff\"\n"
        f"    X-Frame-Options \"SAMEORIGIN\"\n"
        f"    Referrer-Policy \"strict-origin-when-cross-origin\"\n"
        f"  }}\n"
        f"}}"
    )


@app.command()
def create(
    user: str = typer.Argument(..., help="Username/service name"),
    cpu: Optional[str] = typer.Option(None, help="CPU cores (e.g., 2 or 2.5)"),
    ram: Optional[str] = typer.Option(None, help="Memory limit (e.g., 4g)"),
    disk: Optional[int] = typer.Option(None, help="Disk quota GiB (XFS project quota)"),
    port: Optional[int] = typer.Option(None, help="Host port to map to 3000"),
    image_version: Optional[str] = typer.Option(None, help="OpenVSCode image tag"),
    domain_base: Optional[str] = typer.Option(None, help="Base domain for subdomain generation"),
    domain: Optional[str] = typer.Option(None, help="Explicit domain to use"),
    network: Optional[str] = typer.Option(None, help="Docker network name"),
    healthcheck_enable: Optional[bool] = typer.Option(None, help="Enable container healthcheck"),
    gpu: Optional[bool] = typer.Option(None, help="Request 1 NVIDIA GPU for the container"),
    caddy_file: Optional[Path] = typer.Option(None, help="Path to Caddyfile"),
    basic_auth_hash: Optional[str] = typer.Option(None, help="Enable basicauth with 'user:bcrypt_hash'"),
    reload_caddy: bool = typer.Option(False, help="Reload Caddy after writing site"),
    data_root: Optional[Path] = typer.Option(None, help="Root for user data"),
    compose_override: Path = typer.Option(Path("docker-compose.override.yml"), help="Compose override path"),
    tz: Optional[str] = typer.Option(None, help="Timezone env"),
):
    """Create a per-user service and optional Caddy site."""

    cfg = typer.get_current_context().obj or DEFAULTS
    # Defaults from config
    cpu = cpu or cfg["defaults"]["cpu"]
    ram = ram or cfg["defaults"]["ram"]
    disk = int(disk if disk is not None else cfg["defaults"]["disk"])
    image_version = image_version or cfg["image_version"]
    network = network or cfg["network"]
    healthcheck_enable = cfg["defaults"]["healthcheck"] if healthcheck_enable is None else healthcheck_enable
    gpu = cfg["defaults"]["gpu"] if gpu is None else gpu
    data_root = Path(data_root) if data_root else Path(cfg["data_root"])  # type: ignore
    tz = tz or cfg["tz"]
    caddy_file = Path(caddy_file) if caddy_file else Path(cfg["caddy_file"])  # type: ignore
    if domain_base is None:
        domain_base = cfg.get("domain_base")

    # Pick port
    if port is None:
        # find free port starting at configured start_port
        p = int(cfg.get("defaults", {}).get("start_port", 13001))
        used = subprocess.run(["ss", "-ltn"], capture_output=True, text=True)
        used_ports = used.stdout
        while f":{p}\n" in used_ports or f":{p} " in used_ports:
            p += 1
        port = p

    # Ensure network
    ensure_network(network)

    # Ensure data root and user dir
    data_user = data_root / user
    data_user.mkdir(parents=True, exist_ok=True)

    # Compose override update
    yaml, data = ensure_override(compose_override)
    services = data.setdefault("services", {})
    image = f"ghcr.io/coder/openvscode-server:{image_version}"
    if user in services:
        console.print(f"[yellow]Service {user} already exists in {compose_override}. Updating values...[/yellow]")
    services[user] = service_block(user, image, port, data_root, cpu, ram, tz, network, healthcheck_enable, gpu)
    save_yaml(yaml, data, compose_override)
    console.print(f"[green]Compose updated:[/green] {compose_override}")

    # Optional XFS quota
    if shutil.which("xfs_quota") and data_root.exists():
        pid = 2000 + (abs(hash(user)) % 50000)
        projects = Path("/etc/projects")
        projid = Path("/etc/projid")
        try:
            if projects.exists():
                content = projects.read_text()
                if f"{pid}:{data_user}" not in content:
                    with projects.open("a") as f:
                        f.write(f"\n{pid}:{data_user}")
            if projid.exists():
                content = projid.read_text()
                if f"{user}:{pid}" not in content:
                    with projid.open("a") as f:
                        f.write(f"\n{user}:{pid}")
            subprocess.run(["sudo", "xfs_quota", "-x", "-c", f"project -s {user}", str(data_root)], check=False)
            subprocess.run(["sudo", "xfs_quota", "-x", "-c", f"limit -p bhard={disk}g {user}", str(data_root)], check=False)
            console.print(f"[green]Applied XFS quota[/green]: {disk}GiB for {user}")
        except PermissionError:
            console.print("[yellow]Insufficient permissions to set XFS quota; skipped[/yellow]")

    # Domain determination
    if not domain and domain_base:
        domain = f"{user}.{domain_base}"

    # Caddy management
    if domain:
        if not caddy_file.exists():
            caddy_file.write_text("{\n  email admin@example.com\n}\n")
        backup = caddy_backup(caddy_file)
        with caddy_file.open("a", encoding="utf-8") as f:
            f.write("\n\n" + caddy_site_block(domain, port, user, basic_auth_hash) + "\n")
        if not caddy_validate(caddy_file):
            console.print("[red]Caddy validation failed. Rolling back.[/red]")
            shutil.move(str(backup), str(caddy_file))
            raise typer.Exit(1)
        else:
            console.print("[green]Caddy config valid[/green]")
            if reload_caddy:
                if caddy_reload():
                    console.print("[green]Caddy reloaded[/green]")
                else:
                    console.print("[yellow]Caddy reload failed; please reload manually[/yellow]")

    # DNS check
    if domain:
        ip = resolve_host(domain)
        if ip:
            console.print(f"[green]DNS resolves[/green]: {domain} -> {ip}")
        else:
            console.print(f"[yellow]DNS not resolving yet for {domain}[/yellow]")

    console.print(f"[bold]Done.[/bold] Start with: [cyan]docker compose up -d {user}[/cyan]")


@app.command()
def wizard(user: Optional[str] = typer.Option(None, help="Username/service name"), compose_override: Path = typer.Option(Path("docker-compose.override.yml"), help="Compose override path")):
    """Interactive guided setup with preview and confirmation."""
    cfg = typer.get_current_context().obj or DEFAULTS
    if not user:
        user = typer.prompt("Username", default="alice")
    cpu = typer.prompt("CPU cores", default=str(cfg["defaults"]["cpu"]))
    ram = typer.prompt("Memory (e.g., 4g)", default=str(cfg["defaults"]["ram"]))
    disk = int(typer.prompt("Disk quota (GiB)", default=str(cfg["defaults"]["disk"])) )
    start_port = int(cfg.get("defaults", {}).get("start_port", 13001))
    port = int(typer.prompt("Port (host -> 3000)", default=str(start_port)))
    image_version = typer.prompt("Image version tag", default=str(cfg["image_version"]))
    network = typer.prompt("Docker network", default=str(cfg["network"]))
    health = typer.confirm("Enable healthcheck?", default=bool(cfg["defaults"]["healthcheck"]))
    gpu = typer.confirm("Request 1 NVIDIA GPU?", default=bool(cfg["defaults"]["gpu"]))
    domain_base = typer.prompt("Base domain (blank to skip Caddy)", default=str(cfg.get("domain_base") or "")) or None
    domain = f"{user}.{domain_base}" if domain_base else None
    caddy_file = Path(typer.prompt("Caddyfile path", default=str(cfg["caddy_file"]))) if domain else None
    basic_auth_hash = None
    if domain and typer.confirm("Add basic_auth (bcrypt hash)?", default=False):
        basic_auth_hash = typer.prompt("Enter 'user:bcrypt_hash'", default=f"{user}:$2y$05$replace_hash")

    # Preview
    console.rule("Preview")
    table = Table()
    table.add_column("Key")
    table.add_column("Value")
    for k, v in [
        ("user", user), ("cpu", cpu), ("ram", ram), ("disk", str(disk)), ("port", str(port)),
        ("image_version", image_version), ("network", network), ("healthcheck", str(health)), ("gpu", str(gpu)),
        ("domain", domain or "(none)")
    ]:
        table.add_row(k, v)
    console.print(table)
    if not typer.confirm("Apply?", default=True):
        console.print("[yellow]Aborted[/yellow]")
        raise typer.Exit(0)

    # Invoke create with gathered values
    create(
        user=user,
        cpu=cpu,
        ram=ram,
        disk=disk,
        port=port,
        image_version=image_version,
        domain_base=domain_base,
        domain=domain,
        network=network,
        healthcheck_enable=health,
        gpu=gpu,
        caddy_file=caddy_file,
        basic_auth_hash=basic_auth_hash,
        reload_caddy=True if domain else False,
        data_root=None,
        compose_override=compose_override,
        tz=None,
    )


@app.command()
def list(compose_override: Path = typer.Option(Path("docker-compose.override.yml"))):
    """List managed services (from compose override)."""
    yaml, data = ensure_override(compose_override)
    services = data.get("services", {})
    table = Table(title=f"Services in {compose_override}")
    table.add_column("Service")
    table.add_column("Container")
    table.add_column("Port")
    table.add_column("Image")
    for name, svc in services.items():
        container = svc.get("container_name", "")
        ports = ",".join(svc.get("ports", []))
        image = svc.get("image", "")
        table.add_row(name, container, ports, image)
    console.print(table)


@app.command()
def status(user: str, compose_project: Optional[str] = typer.Option(None, help="Compose project name (optional)")):
    """Show container status for a user."""
    svc = f"dev-{user}"
    cmd = ["docker", "ps", "--filter", f"name={svc}", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"]
    subprocess.run(cmd)


@app.command()
def delete(
    user: str,
    compose_override: Path = typer.Option(Path("docker-compose.override.yml")),
    purge: bool = typer.Option(False, help="Also remove /srv/devdata/<user> directory"),
    data_root: Path = typer.Option(Path("/srv/devdata")),
):
    """Remove service from compose override; optionally purge data dir."""
    yaml, data = ensure_override(compose_override)
    services = data.get("services", {})
    if user in services:
        services.pop(user)
        save_yaml(yaml, data, compose_override)
        console.print(f"[green]Removed {user} from {compose_override}[/green]")
    else:
        console.print(f"[yellow]{user} not found in {compose_override}[/yellow]")
    if purge:
        target = data_root / user
        if target.exists():
            shutil.rmtree(target)
            console.print(f"[green]Purged data dir[/green]: {target}")
        else:
            console.print(f"[yellow]Data dir not found[/yellow]: {target}")


@app.command()
def backup(user: str, output: Optional[Path] = typer.Option(None, help="Output tar.gz path"), data_root: Path = typer.Option(Path("/srv/devdata"))):
    """Create a tar.gz backup of the user's data directory."""
    target = data_root / user
    if not target.exists():
        console.print(f"[red]Data dir not found[/red]: {target}")
        raise typer.Exit(1)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    if output is None:
        output = Path.cwd() / f"{user}-backup-{ts}.tar.gz"
    subprocess.run(["tar", "-czf", str(output), "-C", str(data_root), user], check=True)
    console.print(f"[green]Backup created[/green]: {output}")
