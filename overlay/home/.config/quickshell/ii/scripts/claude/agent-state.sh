#!/bin/sh
# Note l'état d'un agent (running, done, waiting) pour la fenêtre kitty qui le porte ; la barre le lit.
cat >/dev/null
pid=$$
while [ "$pid" -gt 1 ] && [ -z "$fenetre" ]; do
    fenetre=$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | awk -F= '$1=="KITTY_PID"{p=$2} $1=="KITTY_WINDOW_ID"{w=$2} END{if (p != "" && w != "") print p "-" w}')
    pid=$(awk '{print $4}' "/proc/$pid/stat" 2>/dev/null || echo 1)
done
d="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/claude-state"
[ -n "$fenetre" ] && mkdir -p "$d" && printf '%s\n' "$1" > "$d/$fenetre"
echo '{}'
