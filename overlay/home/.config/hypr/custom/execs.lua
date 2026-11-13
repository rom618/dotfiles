local scripts = os.getenv("HOME") .. "/.config/hypr/custom/scripts"

hl.on("hyprland.start", function()
    -- share:begin ssh-agent
    hl.exec_cmd(scripts .. "/ssh-keys-load.sh")
    -- share:end
    -- share:begin session-restore
    hl.exec_cmd(scripts .. "/session-restore.py")
    -- share:end
end)
