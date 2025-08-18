#!/usr/bin/env bash
# monitor_extras.sh — JSON/Prometheus/Alerts wrapper for your OpenVSCode monitor
set -Eeuo pipefail

# ---------- Defaults (override via env or flags) ----------
CPU_WARN="${CPU_WARN:-85}"      CPU_CRIT="${CPU_CRIT:-95}"
MEM_WARN="${MEM_WARN:-85}"      MEM_CRIT="${MEM_CRIT:-95}"
DISK_WARN="${DISK_WARN:-90}"    DISK_CRIT="${DISK_CRIT:-95}"
GPU_TEMP_WARN="${GPU_TEMP_WARN:-82}"  GPU_TEMP_CRIT="${GPU_TEMP_CRIT:-88}"
GPU_PWR_WARN="${GPU_PWR_WARN:-350}"   GPU_PWR_CRIT="${GPU_PWR_CRIT:-420}"
ALERT_HOOK="${ALERT_HOOK:-}"    # e.g. https://hooks.slack.com/services/...
MODE="human"                    # human|json|prometheus
INTERVAL=0                      # >0 = loop every N seconds
TIMEOUT=3                       # seconds for docker/nvidia-smi calls

has(){ command -v "$1" >/dev/null 2>&1; }

usage(){ cat <<'USAGE'
monitor_extras.sh [--json|--prometheus] [--interval N] [--alert-hook URL]
Env thresholds: CPU_WARN/CRIT, MEM_WARN/CRIT, DISK_WARN/CRIT, GPU_TEMP_WARN/CRIT, GPU_PWR_WARN/CRIT
Exit codes: 0=OK, 1=WARN, 2=CRIT, 3=error
USAGE
}

# ---------- Parsing ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) MODE="json"; shift;;
    --prometheus) MODE="prometheus"; shift;;
    -c|--interval) INTERVAL="${2:?}"; shift 2;;
    --alert-hook) ALERT_HOOK="${2:?}"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 3;;
  esac
done

HOST="$(hostname)"
ts() { date -u +%FT%TZ; }

with_timeout(){ command timeout --preserve-status "$TIMEOUT" "$@" 2>/dev/null || true; }

# ---------- Samplers ----------
cpu_percent() {
  # calc CPU usage from /proc/stat (2 samples)
  read -r cpu a b c d rest < /proc/stat
  idle1=$((d)); total1=$((a+b+c+d))
  sleep 0.2
  read -r cpu a b c d rest < /proc/stat
  idle2=$((d)); total2=$((a+b+c+d))
  idle=$((idle2-idle1)); total=$((total2-total1))
  awk -v i="$idle" -v t="$total" 'BEGIN{ if(t==0)print 0; else printf "%.1f", (1 - i/t)*100 }'
}

mem_percent() {
  awk '
    /^MemTotal:/ {t=$2}
    /^MemAvailable:/ {a=$2}
    END { if(t==0) print 0; else printf "%.1f", (1- a/t)*100 }
  ' /proc/meminfo
}

disk_percent_root() {
  df -P / | awk 'NR==2 {print $5}' | tr -d '%'
}

gpu_csv() {
  has nvidia-smi || return 0
  with_timeout nvidia-smi \
    --query-gpu=index,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,power.limit,fan.speed \
    --format=csv,noheader,nounits
}

docker_list() {
  has docker || return 0
  with_timeout docker ps --format '{{.ID}} {{.Names}}'
}

docker_health() {
  has docker || return 0
  with_timeout docker inspect -f '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$1"
}

docker_stats_row() {
  has docker || return 0
  with_timeout docker stats --no-stream --format '{{.CPUPerc}} {{.MemUsage}} {{.NetIO}} {{.BlockIO}}' "$1"
}

# ---------- Collect ----------
collect() {
  local CPU MEM DISK
  CPU="$(cpu_percent)"
  MEM="$(mem_percent)"
  DISK="$(disk_percent_root)"

  # containers
  local rows cont id name state health stats
  rows="$(docker_list || true)"
  local containers_json="[]"
  local docker_bad=0
  if [[ -n "${rows:-}" ]]; then
    containers_json="["
    while read -r id name; do
      [[ -z "$id" ]] && continue
      read -r state health <<<"$(docker_health "$id")"
      stats="$(docker_stats_row "$id")"
      # keep stats as strings; parsing units is messy and not needed for alerts
      containers_json+='{"id":"'"$id"'","name":"'"$name"'","state":"'"${state:-unknown}"'","health":"'"${health:-none}"'","stats":"'"${stats//\"/\\\"}"'"},'
      if [[ "$state" != "running" || "$health" == "unhealthy" ]]; then docker_bad=1; fi
    done <<< "$rows"
    containers_json="${containers_json%,}]"
  fi

  # gpu
  local gpu_lines gpu_json="[]"
  gpu_lines="$(gpu_csv || true)"
  if [[ -n "${gpu_lines:-}" ]]; then
    gpu_json="["
    while IFS=',' read -r idx t util mu mt p pcap fan; do
      gpu_json+='{"index":'"${idx:-0}"',"temp":'"${t:-0}"',"util":'"${util:-0}"',"mem_used":'"${mu:-0}"',"mem_total":'"${mt:-0}"',"power":'"${p:-0}"',"power_cap":'"${pcap:-0}"',"fan":'"${fan:-0}"'},'
    done <<< "$gpu_lines"
    gpu_json="${gpu_json%,}]"
  fi

  echo "$CPU|$MEM|$DISK|$containers_json|$gpu_json|$docker_bad"
}

# ---------- Evaluate thresholds ----------
level=0; msgs=()

bump_level(){ 
  (( $1 > level )) && level=$1; 
}

assess() {
  local CPU="$1" MEM="$2" DISK="$3" docker_bad="$4" gjson="$5"
  # CPU/MEM/DISK
  (( ${CPU%.*} >= CPU_CRIT )) && { bump_level 2; msgs+=("CPU ${CPU}% ≥ ${CPU_CRIT}%"); } \
  || (( ${CPU%.*} >= CPU_WARN )) && { bump_level 1; msgs+=("CPU ${CPU}% ≥ ${CPU_WARN}%"); }

  (( ${MEM%.*} >= MEM_CRIT )) && { bump_level 2; msgs+=("MEM ${MEM}% ≥ ${MEM_CRIT}%"); } \
  || (( ${MEM%.*} >= MEM_WARN )) && { bump_level 1; msgs+=("MEM ${MEM}% ≥ ${MEM_WARN}%"); }

  (( DISK >= DISK_CRIT )) && { bump_level 2; msgs+=("DISK ${DISK}% ≥ ${DISK_CRIT}%"); } \
  || (( DISK >= DISK_WARN )) && { bump_level 1; msgs+=("DISK ${DISK}% ≥ ${DISK_WARN}%"); }

  # Docker
  if (( docker_bad == 1 )); then bump_level 2; msgs+=("Container not running or unhealthy"); fi

  # GPU thresholds
  if [[ "$gjson" != "[]" ]]; then
    # check max across GPUs
    local gtemp gpwr
    gtemp=$(printf '%s\n' "$gjson" | awk -F'[: ,}]' '/"temp":/{print $(NF-1)}' | sort -nr | head -1)
    gpwr=$(printf '%s\n' "$gjson" | awk -F'[: ,}]' '/"power":/{print $(NF-1)}' | sort -nr | head -1)
    [[ -n "$gtemp" ]] && {
      (( gtemp >= GPU_TEMP_CRIT )) && { bump_level 2; msgs+=("GPU temp ${gtemp}°C ≥ ${GPU_TEMP_CRIT}°C"); } \
      || (( gtemp >= GPU_TEMP_WARN )) && { bump_level 1; msgs+=("GPU temp ${gtemp}°C ≥ ${GPU_TEMP_WARN}°C"); }
    }
    [[ -n "$gpwr" ]] && {
      (( gpwr >= GPU_PWR_CRIT )) && { bump_level 2; msgs+=("GPU power ${gpwr}W ≥ ${GPU_PWR_CRIT}W"); } \
      || (( gpwr >= GPU_PWR_WARN )) && { bump_level 1; msgs+=("GPU power ${gpwr}W ≥ ${GPU_PWR_WARN}W"); }
    }
  fi
}

send_alert() {
  [[ -z "$ALERT_HOOK" ]] && return 0
  local payload
  payload=$(cat <<JSON
{"host":"$HOST","ts":"$(ts)","level":$level,"messages":$(printf '%s\n' "${msgs[@]}" | awk 'BEGIN{s="["} {gsub(/"/,"\\\""); s=s (NR>1?",":"") "\"" $0 "\""} END{s=s "]"; print s}'),"summary":"$(IFS='; '; echo "${msgs[*]:-OK}")"}
JSON
)
  with_timeout curl -sS -X POST -H "Content-Type: application/json" -d "$payload" "$ALERT_HOOK" >/dev/null || true
}

print_human() {
  local CPU="$1" MEM="$2" DISK="$3" cjson="$4" gjson="$5"
  echo "[$(ts)] $HOST  CPU:${CPU}%  MEM:${MEM}%  DISK:${DISK}%  LEVEL:$level"
  [[ "$cjson" != "[]" ]] && echo "Containers: $(echo "$cjson" | wc -c) bytes (use --json for details)"
  [[ "$gjson" != "[]" ]] && echo "GPU: $(echo "$gjson" | wc -c) bytes (use --json or --prometheus for details)"
  ((${#msgs[@]})) && echo "Alerts: ${msgs[*]}"
}

print_json() {
  local CPU="$1" MEM="$2" DISK="$3" cjson="$4" gjson="$5"
  printf '{'
  printf '"host":"%s","ts":"%s","level":%d,' "$HOST" "$(ts)" "$level"
  printf '"cpu":%s,"mem":%s,"disk":%s,' "$CPU" "$MEM" "$DISK"
  printf '"containers":%s,"gpus":%s' "$cjson" "$gjson"
  printf '}\n'
}

print_prom() {
  local CPU="$1" MEM="$2" DISK="$3" _cjson="$4" gjson="$5"
  echo "# HELP monitor_cpu_percent CPU usage percent"
  echo "# TYPE monitor_cpu_percent gauge"
  echo "monitor_cpu_percent{host=\"$HOST\"} $CPU"
  echo "# HELP monitor_mem_percent Memory usage percent"
  echo "# TYPE monitor_mem_percent gauge"
  echo "monitor_mem_percent{host=\"$HOST\"} $MEM"
  echo "# HELP monitor_disk_percent_root Disk usage percent of /"
  echo "# TYPE monitor_disk_percent_root gauge"
  echo "monitor_disk_percent_root{host=\"$HOST\",mount=\"/\"} $DISK"
  # GPUs
  if [[ "$gjson" != "[]" ]]; then
    # cheap JSON-ish parse (we controlled format)
    echo "$gjson" | tr '{,}' '\n ' | awk -v H="$HOST" '
      /"index":/ {idx=$0; sub(/.*:/,"",idx)}
      /"temp":/ {t=$0; sub(/.*:/,"",t); print "monitor_gpu_temp_celsius{host=\"" H "\",gpu=\"" idx "\"} " t}
      /"util":/ {u=$0; sub(/.*:/,"",u); print "monitor_gpu_util_percent{host=\"" H "\",gpu=\"" idx "\"} " u}
      /"mem_used":/ {mu=$0; sub(/.*:/,"",mu); getline; mt=$0; sub(/.*:/,"",mt);
                      print "monitor_gpu_mem_used_mib{host=\"" H "\",gpu=\"" idx "\"} " mu
                      print "monitor_gpu_mem_total_mib{host=\"" H "\",gpu=\"" idx "\"} " mt}
      /"power":/ {p=$0; sub(/.*:/,"",p); getline; pc=$0; sub(/.*:/,"",pc);
                  print "monitor_gpu_power_watts{host=\"" H "\",gpu=\"" idx "\"} " p
                  print "monitor_gpu_power_cap_watts{host=\"" H "\",gpu=\"" idx "\"} " pc}
      /"fan":/ {f=$0; sub(/.*:/,"",f); print "monitor_gpu_fan_percent{host=\"" H "\",gpu=\"" idx "\"} " f}
    '
  fi
  echo "monitor_overall_level{host=\"$HOST\"} $level"
}

# ---------- Main loop ----------
run_once() {
  local line CPU MEM DISK cjson gjson docker_bad
  line="$(collect)"
  IFS='|' read -r CPU MEM DISK cjson gjson docker_bad <<<"$line"
  assess "$CPU" "$MEM" "$DISK" "$docker_bad" "$gjson"
  case "$MODE" in
    human)      print_human "$CPU" "$MEM" "$DISK" "$cjson" "$gjson" ;;
    json)       print_json  "$CPU" "$MEM" "$DISK" "$cjson" "$gjson" ;;
    prometheus) print_prom  "$CPU" "$MEM" "$DISK" "$cjson" "$gjson" ;;
  esac
  send_alert
  return $(( level==2 ? 2 : level==1 ? 1 : 0 ))
}

if (( INTERVAL > 0 )); then
  while true; do
    run_once || true
    sleep "$INTERVAL"
  done
else
  run_once
fi
