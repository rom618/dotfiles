if status is-interactive; and set -q KITTY_RESTORE_FILE
    if test -f "$KITTY_RESTORE_FILE"
        cat "$KITTY_RESTORE_FILE"
        rm -f "$KITTY_RESTORE_FILE"
        set_color brblack
        echo "-- restored from a closed terminal --"
        set_color normal
    end
    set -e KITTY_RESTORE_FILE
end
