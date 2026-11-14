#!/usr/bin/env python3
import json
import os
import re
import socket
import sys
import time
from pathlib import Path

RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATE_DIR = RUNTIME / "claude-state"
CLAUDE_SESSIONS = Path.home() / ".claude" / "sessions"
SESSION_STATUS = {"idle": "done", "busy": "running", "waiting": "waiting"}
RANK = {"idle": -1, "done": 0, "running": 1, "waiting": 2}
INTERVAL = 1.0


def hypr_socket():
    sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")
    if sig:
        return RUNTIME / "hypr" / sig / ".socket.sock"
    socks = sorted((RUNTIME / "hypr").glob("*/.socket.sock"), key=lambda p: p.stat().st_mtime, reverse=True)
    return socks[0] if socks else None


def hypr_clients():
    path = hypr_socket()
    if not path:
        return []
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(str(path))
            s.sendall(b"j/clients")
            chunks = []
            while True:
                data = s.recv(65536)
                if not data:
                    break
                chunks.append(data)
        return json.loads(b"".join(chunks))
    except (OSError, ValueError):
        return []


def kitty_ls(pid):
    msg = json.dumps({"cmd": "ls", "version": [0, 14, 2], "no_response": False}).encode()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect(f"\0mykitty-{pid}")
            s.sendall(b"\x1bP@kitty-cmd" + msg + b"\x1b\\")
            buf = b""
            while not buf.endswith(b"\x1b\\"):
                data = s.recv(65536)
                if not data:
                    break
                buf += data
        start = buf.index(b"{")
        reply = json.loads(buf[start:buf.rindex(b"}") + 1])
        if not reply.get("ok"):
            return []
        return json.loads(reply.get("data") or "[]")
    except (OSError, ValueError):
        return []


def norm_title(title):
    return re.sub(r"^[^0-9A-Za-z~/.]+", "", title or "").strip()


AGENTS = {"claude": "claude", "pi": "pi", "codex": "codex", "codex.js": "codex"}


def agent_of(cmdline):
    for a in (cmdline or [])[:2]:
        name = AGENTS.get(os.path.basename(a))
        if name:
            return name
        if "pi-coding-agent" in a:
            return "pi"
        if "@anthropic-ai/claude-code" in a:
            return "claude"
        if "@openai/codex" in a:
            return "codex"
    return None


def started_at(pid):
    try:
        return os.stat(f"/proc/{pid}").st_ctime
    except OSError:
        return None


def window_state(kitty_pid, win):
    procs = [p for p in win.get("foreground_processes") or [] if agent_of(p.get("cmdline"))]
    if not procs:
        return None
    agent = agent_of(procs[0].get("cmdline"))
    hook = session = None
    path = STATE_DIR / f"{kitty_pid}-{win.get('id')}"
    try:
        st = path.stat()
        state = path.read_text().strip()
        start = started_at(procs[0].get("pid"))
        if state in RANK and (start is None or st.st_mtime >= start - 1):
            hook = (st.st_mtime, state)
    except OSError:
        pass
    if agent != "claude":
        return (hook[1], agent) if hook else ("idle", agent)
    try:
        data = json.loads((CLAUDE_SESSIONS / f"{procs[0].get('pid')}.json").read_text())
        status = data.get("status")
        if status in SESSION_STATUS:
            session = (float(data.get("updatedAt") or 0) / 1000, SESSION_STATUS[status])
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    if hook and session:
        return max(hook, session)[1], agent
    if hook or session:
        return (hook or session)[1], agent
    return ("done" if (win.get("title") or "").startswith(chr(0x2733)) else "running"), agent


def os_window_state(kitty_pid, osw):
    best = None
    for tab in osw.get("tabs", []):
        for win in tab.get("windows", []):
            found = window_state(kitty_pid, win)
            if found and (best is None or RANK[found[0]] > RANK[best[0]]):
                best = found
    return best


def os_window_title(osw):
    title = ""
    for tab in osw.get("tabs", []):
        if tab.get("is_active") or not title:
            title = tab.get("title", "")
    return title


def match(clients, os_windows):
    remaining = list(clients)
    pairs = []
    unmatched = []
    for key in (lambda t: t, norm_title):
        unmatched = []
        for osw in os_windows:
            hit = next((c for c in remaining if key(c.get("title")) == key(os_window_title(osw))), None)
            if hit:
                remaining.remove(hit)
                pairs.append((hit, osw))
            else:
                unmatched.append(osw)
        os_windows = unmatched
    pairs.extend(zip(remaining, unmatched))
    return pairs


def snapshot():
    by_pid = {}
    for c in hypr_clients():
        if c.get("class") == "kitty" and c.get("pid", 0) > 0:
            by_pid.setdefault(c["pid"], []).append(c)
    states, agents = {}, {}
    for pid, group in by_pid.items():
        for client, osw in match(group, kitty_ls(pid)):
            found = os_window_state(pid, osw)
            if found:
                states[client["address"]], agents[client["address"]] = found
    return {"states": states, "agents": agents}


def main():
    last = None
    parent = os.getppid()
    while os.getppid() == parent:
        current = snapshot()
        if current != last:
            print(json.dumps(current, sort_keys=True), flush=True)
            last = current
        time.sleep(INTERVAL)


if __name__ == "__main__":
    sys.exit(main())
