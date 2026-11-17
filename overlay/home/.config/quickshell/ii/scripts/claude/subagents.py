#!/usr/bin/env python3
"""Hook Claude Code SubagentStart/SubagentStop : un fichier par sous-agent en cours, lu par la barre."""
import json
import os
import sys
from pathlib import Path

entree = json.load(sys.stdin)
dossier = Path(os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}") / "claude-state" / "agents" / entree["session_id"]
agent = entree.get("agent_id")
if agent:
    fichier = dossier / agent
    dossier.mkdir(parents=True, exist_ok=True)
    if entree["hook_event_name"] == "SubagentStart":
        fichier.touch()
    else:
        fichier.unlink(missing_ok=True)
        (dossier / f"{agent}.done").touch()
