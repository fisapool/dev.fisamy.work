#!/usr/bin/env bash
set -euo pipefail

# Stop idle OpenVSCode containers based on low CPU and low network throughput.
# Tunables via environment or systemd unit Environment=…
THRESHOLD_MINUTES="${THRESHOLD_MINUTES:-45}"
CPU_PCT_MAX="${CPU_PCT_MAX:-1.0}"
RX_TX_BPS_MAX="${RX_TX_BPS_MAX:-2048}"  # ~2KB/s

now() { date +%s; }

# List ovscode containers by label
containers=$(docker ps --format '{{.Names}}' --filter "label=fisamy.role=ovscode" || true)
[[ -z "$containers" ]] && exit 0

for cname in $containers; do
  # CPU%
  raw=$(docker stats --no-stream --format '{{.CPUPerc}}' "$cname" 2>/dev/null || echo "0")
  cpu="${raw//%/}"
  # net BPS (approx): sample /sys counters inside container if present
  n1=$(docker exec "$cname" sh -lc "test -r /sys/class/net/eth0/statistics/rx_bytes && cat /sys/class/net/eth0/statistics/rx_bytes /sys/class/net/eth0/statistics/tx_bytes || echo 0 0" 2>/dev/null | awk '{s+=$1}END{print s+0}')
  t1=$(now); sleep 2
  n2=$(docker exec "$cname" sh -lc "test -r /sys/class/net/eth0/statistics/rx_bytes && cat /sys/class/net/eth0/statistics/rx_bytes /sys/class/net/eth0/statistics/tx_bytes || echo 0 0" 2>/dev/null | awk '{s+=$1}END{print s+0}')
  t2=$(now)
  bps=$(( (n2 - n1) / (t2 - t1 + 1) ))

  # Track last active timestamp per container in /var/run (tmpfs) or /tmp
  stamp_dir="/var/run/dev-idle-stamps"
  mkdir -p "$stamp_dir"
  stamp_file="${stamp_dir}/${cname}.stamp"
  [[ -f "$stamp_file" ]] || touch "$stamp_file"
  last=$(stat -c %Y "$stamp_file" 2>/dev/null || echo "$t1")

  # active if either CPU or net exceeds thresholds
  awk "BEGIN{exit !(${cpu}>${CPU_PCT_MAX} || ${bps}>${RX_TX_BPS_MAX})}" >/dev/null 2>&1 && touch "$stamp_file"

  elapsed=$(( t2 - last ))
  if [[ "$elapsed" -gt $(( THRESHOLD_MINUTES * 60 )) ]]; then
    echo "Stopping idle container: $cname (cpu=${cpu}%, bps=${bps})"
    docker stop "$cname" >/dev/null 2>&1 || true
    rm -f "$stamp_file"
  fi
done
