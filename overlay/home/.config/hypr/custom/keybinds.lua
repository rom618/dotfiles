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
for i = 1, 9 do
    hl.bind("SUPER + SHIFT + " .. tostring(i), hl.dsp.window.move({ workspace = tostring(i) }),
        { description = "Window: Move to workspace 1" })
end
hl.bind("SUPER + SHIFT + 0", hl.dsp.window.move({ workspace = "10" }))

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
