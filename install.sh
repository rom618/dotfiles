#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is needed first (Arch: sudo pacman -S python, Ubuntu: sudo apt install python3)" >&2
    exit 1
fi
exec python3 "$here/lib/dotfiles.py" "$@"
