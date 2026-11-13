#!/usr/bin/env bash
hyprctl dispatch 'hl.dsp.dpms({ action = "enable" })'
if pidof hyprlock >/dev/null; then
    sleep 0.1
    wtype -k Escape
fi
