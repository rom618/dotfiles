#!/bin/bash

set -euo pipefail

DEVICE=$(hyprctl devices -j | jq -r '.keyboards[] | select(.main == true) | .name')

if [ -z "$DEVICE" ]; then
    DEVICE=$(hyprctl devices -j | jq -r '.keyboards[0].name')
fi

CURRENT=$(hyprctl devices -j | jq -r --arg dev "$DEVICE" '.keyboards[] | select(.name == $dev) | .active_keymap')

if echo "$CURRENT" | grep -qi "us"; then
    NEW_LAYOUT="ca"
    NEW_VARIANT="fr-legacy"
    LABEL="Canadian French"
else
    NEW_LAYOUT="us"
    NEW_VARIANT=""
    LABEL="US"
fi

hyprctl keyword input:kb_layout "$NEW_LAYOUT"
hyprctl keyword input:kb_variant "$NEW_VARIANT"

hyprctl switchxkblayout "$DEVICE" next

notify-send "Keyboard Layout" "Switched to $LABEL" -a "Shell" -t 1500
