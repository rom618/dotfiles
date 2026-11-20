#!/usr/bin/env python3
"""Hook Claude Code SubagentStart/SubagentStop : un fichier par sous-agent en cours, lu par la barre."""
import json
import os
import sys
from pathlib import Path


def processus_claude():
    """PID du processus claude qui lance le hook : la même conversation peut être ouverte dans deux fenêtres."""
    pid = os.getppid()
    while pid > 1:
        if Path(f"/proc/{pid}/comm").read_text().strip() == "claude":
            return pid
        pid = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
    return None


entree = json.load(sys.stdin)
dossier = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "claude-state" / "agents" / entree["session_id"]
agent = entree.get("agent_id")
if agent:
    fichier = dossier / agent
    dossier.mkdir(parents=True, exist_ok=True)
    if entree["hook_event_name"] == "SubagentStart":
        pid = processus_claude()
        fichier.write_text(f"{pid}\n" if pid else "")
    else:
        fichier.unlink(missing_ok=True)
        (dossier / f"{agent}.done").touch()
