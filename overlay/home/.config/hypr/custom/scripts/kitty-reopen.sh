#!/usr/bin/env bash
store="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/kitty-closed"
last=$(ls -1 "$store"/*.json 2>/dev/null | sort | tail -n 1)
if [ -z "$last" ]; then
    notify-send -a Terminal "No closed terminal to reopen"
    exit 0
fi
cwd=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["cwd"])' "$last")
cmd=$(python3 -I -c 'import json,sys; print(json.load(open(sys.argv[1])).get("cmd") or "")' "$last")
txt="${last%.json}.txt"
rm -f "$last"
[ -d "$cwd" ] || cwd="$HOME"
if [ -s "$txt" ]; then
    export KITTY_RESTORE_FILE="$txt"
else
    rm -f "$txt"
fi
if [ -n "$cmd" ]; then
    exec kitty -1 -d "$cwd" fish -C "$cmd"
fi
exec kitty -1 -d "$cwd"
