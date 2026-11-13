#!/usr/bin/env bash
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/quickshell/states.json"
SOUND=/usr/share/sounds/freedesktop/stereo/dialog-warning.oga
STEPS=15
STEP_DELAY=0.04

[ "$(jq -r '.idle.inhibit // false' "$STATE" 2>/dev/null)" = "true" ] || exit 0

mapfile -t STREAMS < <(LC_ALL=C pactl list sink-inputs 2>/dev/null | awk '
    /^Sink Input #/ { idx = substr($3, 2) }
    /^\tVolume:/ && idx != "" {
        out = idx
        for (i = 3; i <= NF; i++) if ($(i + 1) == "/" && $i ~ /^[0-9]+$/) out = out " " $i
        print out
        idx = ""
    }')

set_streams() {
    local num=$1 line idx vols v out
    for line in "${STREAMS[@]}"; do
        read -r idx vols <<< "$line"
        out=()
        for v in $vols; do
            out+=($((v * num / STEPS)))
        done
        pactl set-sink-input-volume "$idx" "${out[@]}" 2>/dev/null
    done
}

fade() {
    local from=$1 to=$2 dir=1 i
    [ "$from" -gt "$to" ] && dir=-1
    for ((i = from; i != to + dir; i += dir)); do
        set_streams "$i"
        sleep "$STEP_DELAY"
    done
}

SINK=@DEFAULT_AUDIO_SINK@
read -r _ VOL MUTED < <(wpctl get-volume "$SINK")
MUTE=0
[ -n "$MUTED" ] && MUTE=1
restore_sink() {
    wpctl set-volume "$SINK" "$VOL"
    wpctl set-mute "$SINK" "$MUTE"
}
trap 'restore_sink; set_streams "$STEPS"' EXIT

fade "$STEPS" 0
wpctl set-mute "$SINK" 0
wpctl set-volume "$SINK" 0.8

for _ in 1 2 3; do
    pw-play "$SOUND" 2>/dev/null || paplay "$SOUND"
done

restore_sink
fade 0 "$STEPS"
