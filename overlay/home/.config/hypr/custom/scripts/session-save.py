#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "hypr-session"
STATE_FILE = STATE_DIR / "session.json"
RESTORING = STATE_DIR / "restoring"
RESTORING_MAX_AGE = 300
CLAUDE_SESSIONS = Path.home() / ".claude" / "sessions"
RERUN = {"nvim", "vim", "btop", "htop", "yazi", "less", "man"}


def hyprland_env():
    env = dict(os.environ)
    if env.get("HYPRLAND_INSTANCE_SIGNATURE"):
        return env
    runtime = Path(env.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "hypr"
    dirs = sorted(runtime.glob("*/.socket.sock"), key=lambda p: p.stat().st_mtime, reverse=True)
    if dirs:
        env["HYPRLAND_INSTANCE_SIGNATURE"] = dirs[0].parent.name
    return env


def run_json(argv, env=None):
    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=10, env=env)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except ValueError:
        return None


def shutting_down():
    try:
        out = subprocess.run(["systemctl", "--user", "is-system-running"],
                             capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return out.stdout.strip() == "stopping"


def norm_title(title):
    return re.sub(r"^[^0-9A-Za-z~/.]+", "", title or "").strip()


def read_argv(pid):
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return None
    return [p.decode(errors="replace") for p in raw.split(b"\x00") if p] or None


def read_cwd(pid):
    try:
        return str(Path(f"/proc/{pid}/cwd").resolve())
    except OSError:
        return None


def placement(client):
    return {
        "title": client.get("title", ""),
        "workspace": client.get("workspace", {}).get("name", ""),
        "floating": bool(client.get("floating", False)),
        "fullscreen": int(client.get("fullscreen", 0) or 0),
        "at": client.get("at", [0, 0]),
        "size": client.get("size", [800, 600]),
    }


def claude_sessions_dir(pid):
    try:
        env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\x00")
    except OSError:
        return CLAUDE_SESSIONS
    for item in env:
        if item.startswith(b"CLAUDE_CONFIG_DIR=") and len(item) > 18:
            return Path(item[18:].decode(errors="replace")) / "sessions"
    return CLAUDE_SESSIONS


def claude_session(pid):
    try:
        data = json.loads((claude_sessions_dir(pid) / f"{pid}.json").read_text())
    except (OSError, ValueError):
        return None
    sid = data.get("sessionId")
    if not sid:
        return None
    found = {"claude": sid, "cwd": data.get("cwd")}
    if data.get("name"):
        found["name"] = data["name"]
    return found


def is_claude(cmdline):
    return any(os.path.basename(a) == "claude" for a in cmdline[:2])


def window_program(win):
    procs = win.get("foreground_processes") or []
    for p in procs:
        if is_claude(p.get("cmdline") or []):
            found = claude_session(p.get("pid"))
            if found:
                return found
    for p in procs:
        cmdline = p.get("cmdline") or []
        if cmdline and os.path.basename(cmdline[0]) in RERUN:
            return {"argv": cmdline, "cwd": p.get("cwd")}
    return None


def kitty_os_windows(pid):
    data = run_json(["kitty", "@", "--to", f"unix:@mykitty-{pid}", "ls"])
    if not isinstance(data, list):
        return []
    result = []
    for osw in data:
        tabs = []
        title = ""
        for tab in osw.get("tabs", []):
            windows = []
            for win in tab.get("windows", []):
                entry = {"cwd": win.get("cwd")}
                program = window_program(win)
                if program:
                    entry.update(program)
                windows.append(entry)
            tabs.append({"layout": tab.get("layout", ""), "active": bool(tab.get("is_active")),
                         "windows": windows})
            if tab.get("is_active") or not title:
                title = tab.get("title", "")
        result.append({"title": title, "tabs": tabs})
    return result


def match_kitty(clients, os_windows):
    remaining = list(clients)
    pairs = []
    unmatched = []
    for osw in os_windows:
        hit = next((c for c in remaining if norm_title(c.get("title")) == norm_title(osw["title"])), None)
        if hit:
            remaining.remove(hit)
            pairs.append((hit, osw))
        else:
            unmatched.append(osw)
    for osw, client in zip(unmatched, remaining):
        pairs.append((client, osw))
    return pairs


def main():
    if RESTORING.exists() and time.time() - RESTORING.stat().st_mtime < RESTORING_MAX_AGE:
        return
    if shutting_down():
        return
    clients = run_json(["hyprctl", "clients", "-j"], env=hyprland_env())
    if not isinstance(clients, list):
        return

    by_pid = {}
    for c in clients:
        pid = c.get("pid")
        if c.get("class") and pid and pid > 0:
            by_pid.setdefault(pid, []).append(c)

    entries = []
    for pid, group in by_pid.items():
        cls = group[0].get("class", "")
        if cls == "kitty":
            for client, osw in match_kitty(group, kitty_os_windows(pid)):
                entries.append({"kind": "kitty", "class": cls, **placement(client), "tabs": osw["tabs"]})
            continue
        argv = read_argv(pid)
        if not argv:
            continue
        entries.append({"kind": "app", "class": cls, "argv": argv, "cwd": read_cwd(pid),
                        "windows": [placement(c) for c in group]})

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps({"saved_at": int(time.time()), "entries": entries}, indent=2))
    tmp.replace(STATE_FILE)


if __name__ == "__main__":
    sys.exit(main())
