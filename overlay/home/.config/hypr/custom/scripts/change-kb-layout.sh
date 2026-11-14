#!/bin/bash

set -euo pipefail

DEVICE=$(hyprctl devices -j | jq -r '.keyboards[] | select(.main == true) | .name')

if [ -z "$DEVICE" ]; then
    DEVICE=$(hyprctl devices -j | jq -r '.keyboards[0].name')
fi

hyprctl switchxkblayout "$DEVICE" next >/dev/null

LABEL=$(hyprctl devices -j | jq -r --arg dev "$DEVICE" '.keyboards[] | select(.name == $dev) | .active_keymap')

notify-send "Keyboard Layout" "Switched to $LABEL" -a "Shell" -t 1500
