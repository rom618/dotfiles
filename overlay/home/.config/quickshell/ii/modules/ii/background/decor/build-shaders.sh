#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
QSB="$(command -v qsb || echo /usr/lib/qt6/bin/qsb)"
for s in particles.vert particles.frag; do
    "$QSB" --qt6 --qsbversion 65 -o "$s.qsb" "$s"
    echo "built $s.qsb"
done
