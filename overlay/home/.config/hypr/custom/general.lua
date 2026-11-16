
hl.config({
    input = {
kb_layout = "us",
kb_variant = "",
        repeat_delay = 400,
        touchpad = {
            natural_scroll = false,
        },
    },
})

local screenOutputs = { "eDP-1", "DP-1", "DP-2", "HDMI-A-1", "HDMI-A-2", "DP-3", "DP-4", "DP-5", "DP-6", "DP-7", "DP-8" }
for k, output in ipairs(screenOutputs) do
    for i = 1, 10 do
        hl.workspace_rule({ workspace = tostring((k - 1) * 10 + i), monitor = output, default = i == 1 })
    end
end
