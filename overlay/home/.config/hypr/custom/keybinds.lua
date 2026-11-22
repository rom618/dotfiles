-- share:begin keybinds
hl.bind("CTRL+SUPER+ALT+Slash", hl.dsp.exec_cmd("xdg-open ~/.config/hypr/custom/keybinds.lua"), {description = "Config: Edit user keybinds"} )
-- share:else
-- hl.bind("CTRL+SUPER+ALT+Slash", hl.dsp.exec_cmd("xdg-open ~/.config/hypr/custom/keybinds.lua"), {description = "Edit user keybinds"} )
-- share:end
-- share:begin keybinds

-- Unbind default SUPER + ALT + [0-9] move-to-workspace binds
hl.unbind("SUPER + ALT + 1")
hl.unbind("SUPER + ALT + 2")
hl.unbind("SUPER + ALT + 3")
hl.unbind("SUPER + ALT + 4")
hl.unbind("SUPER + ALT + 5")
hl.unbind("SUPER + ALT + 6")
hl.unbind("SUPER + ALT + 7")
hl.unbind("SUPER + ALT + 8")
hl.unbind("SUPER + ALT + 9")
hl.unbind("SUPER + ALT + 0")
hl.unbind("Print")

-- share:end
-- share:begin keybinds
-- Rebind move-to-workspace to SUPER + SHIFT + [0-9]
for i = 1, 10 do
    hl.bind("SUPER + SHIFT + " .. (i % 10), function()
        hl.dispatch(hl.dsp.window.move({ workspace = workspace_in_group(i) }))
    end, { description = "Window: Move to workspace " .. i .. " of this screen" })
end

local function move_to_screen(step)
    local mons = {}
    for _, m in ipairs(hl.get_monitors()) do
        if m.enabled and not m.is_mirror then
            table.insert(mons, m)
        end
    end
    table.sort(mons, function(a, b) return a.x < b.x end)
    for i, m in ipairs(mons) do
        if m.focused then
            local target = mons[i + step]
            if target and target.active_workspace then
                hl.dispatch(hl.dsp.window.move({ workspace = target.active_workspace.id }))
            end
            return
        end
    end
end
hl.bind("SUPER + SHIFT + ALT + Left", function() move_to_screen(-1) end,
    { description = "Window: Send to the screen on the left" })
hl.bind("SUPER + SHIFT + ALT + Right", function() move_to_screen(1) end,
    { description = "Window: Send to the screen on the right" })

-- share:end
-- share:begin session-restore
hl.unbind("CTRL + SHIFT + ALT + SUPER + Delete")
hl.bind("CTRL + SHIFT + ALT + SUPER + Delete",
    hl.dsp.exec_cmd("qs -c ii ipc call session poweroff || systemctl poweroff || loginctl poweroff"),
    { description = "Session: Shut down" })

-- share:end
-- share:begin display-input
hl.bind("SUPER + Space", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/custom/scripts/change-kb-layout.sh"),
    { description = "Input: Switch keyboard layout" })
-- share:end
-- share:begin keybinds
-- hl.bind("Pause", hl.dsp.exec_cmd("loginctl lock-session"))
--##! Media
local mediaNextCommand =
"playerctl next || playerctl position bc <<< \"100 * $(playerctl metadata mpris:length) / 1000000 / 100\""
hl.bind("SUPER + ALT + Right", hl.dsp.exec_cmd(mediaNextCommand), { description = "Media: Next track" })
hl.bind("SUPER + ALT + Left", hl.dsp.exec_cmd("playerctl previous"), { description = "Media: Previous track" })

local function media_or_ide(key, cmd)
    return function()
        local w = hl.get_active_window()
        if w and w.class and w.class:find("^jetbrains%-") then
            hl.dispatch(hl.dsp.send_shortcut({ mods = "", key = key, window = "address:" .. w.address }))
        else
            hl.exec_cmd(cmd)
        end
    end
end
hl.bind("F7", media_or_ide("F7", "playerctl previous"), { description = "Media: Previous track (F7 stays F7 in JetBrains IDEs)" })
hl.bind("F8", media_or_ide("F8", "playerctl play-pause"), { description = "Media: Play/pause (F8 stays F8 in JetBrains IDEs)" })
hl.bind("F9", media_or_ide("F9", mediaNextCommand), { description = "Media: Next track (F9 stays F9 in JetBrains IDEs)" })
hl.bind("Print", hl.dsp.exec_cmd("grim -g \"$(slurp)\" - | wl-copy"),
    { description = "Utilities: Screenshot region to clipboard" })

-- share:end
-- share:begin kitty
hl.unbind("SUPER + SHIFT + T")
hl.bind("SUPER + SHIFT + T", hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/custom/scripts/kitty-reopen.sh"),
    { description = "App: Reopen the last closed terminal" })
hl.bind("SUPER + ALT + T", hl.dsp.global("quickshell:screenTranslate"),
    { description = "Utilities: Translate screen content" })
hl.unbind("SUPER + Return")
hl.unbind("SUPER + T")
hl.bind("SUPER + Return", hl.dsp.exec_cmd("kitty -1"), { description = "App: Terminal (kitty)" })
hl.bind("SUPER + T", hl.dsp.exec_cmd("kitty -1"))

-- share:end
-- share:begin idle-lid
hl.bind("switch:on:Lid Switch",
    hl.dsp.exec_cmd(os.getenv("HOME") .. "/.config/hypr/custom/scripts/lid-keepawake-alert.sh"),
    { locked = true, description = "Session: Warn on lid close while Keep awake is on" })
-- share:end
