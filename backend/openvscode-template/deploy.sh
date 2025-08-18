#!/usr/bin/env bash
set -euo pipefail

if ! command -v coder >/dev/null 2>&1; then
	echo "Error: coder CLI not found. Install it first: curl -fsSL https://dev.fisamy.work/install.sh | sh" >&2
	exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

TEMPLATE_NAME="vscode-ai"

echo "Pushing template: $TEMPLATE_NAME (dir: $(pwd))"
coder templates push "$TEMPLATE_NAME" --directory . --yes

echo "Done. Create a workspace from the '$TEMPLATE_NAME' template in the Coder UI."
