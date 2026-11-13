-- share:begin ssh-agent
local runtime = os.getenv("XDG_RUNTIME_DIR")
if runtime then
    hl.env("SSH_AUTH_SOCK", runtime .. "/ssh-agent.socket")
end
-- share:else
--
-- share:end
