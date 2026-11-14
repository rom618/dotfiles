#!/usr/bin/env bash
hyprctl dispatch 'hl.dsp.dpms({ action = "enable" })'
sleep 0.1
if pidof hyprlock >/dev/null; then
    wtype -k Escape
else
    qs -c ii ipc call lock clear >/dev/null 2>&1
fi
