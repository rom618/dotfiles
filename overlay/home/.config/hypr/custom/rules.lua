
-- share:begin window-rules
hl.on("window.move_to_workspace", function(_, ws)
    if not ws or ws.special then
        return
    end
    local name = ws.name
    hl.timer(function()
        local list = hl.get_workspace_windows(name)
        if #list < 2 then
            return
        end
        for _, w in ipairs(list) do
            if w.fullscreen == 1 then
                hl.dispatch(hl.dsp.window.fullscreen({ mode = "maximized", action = "unset", window = "address:" .. w.address }))
            end
        end
    end, { timeout = 50, type = "oneshot" })
end)
-- share:end
