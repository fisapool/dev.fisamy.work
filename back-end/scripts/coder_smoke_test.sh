#!/usr/bin/env bash
set -euo pipefail

# Smoke test: list Coder workspaces via API.
# Sources /etc/fisamy/coder.env if env vars are not already set.

if [[ -z "${CODER_HOST:-}" || -z "${CODER_API_TOKEN:-}" ]]; then
  if [[ -f /etc/fisamy/coder.env ]]; then
    # shellcheck disable=SC1091
    source /etc/fisamy/coder.env
  fi
fi

if [[ -z "${CODER_HOST:-}" || -z "${CODER_API_TOKEN:-}" ]]; then
  echo "Missing CODER_HOST or CODER_API_TOKEN. Export them or create /etc/fisamy/coder.env" >&2
  exit 1
fi

curl -s -H "Authorization: Bearer ${CODER_API_TOKEN}" \
  "${CODER_HOST%/}/api/v2/workspaces" | jq '.[].name'

