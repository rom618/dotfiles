#!/usr/bin/env bash
set -euo pipefail
rm -f "${XDG_CACHE_HOME:-$HOME/.cache}/cliphist/db"
echo "clipboard history wiped"
qs -c "${qsConfig:-ii}" ipc call cliphistService update >/dev/null 2>&1 || true
