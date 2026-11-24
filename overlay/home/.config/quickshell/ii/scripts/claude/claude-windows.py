#!/usr/bin/env python3
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
STATE_DIR = RUNTIME / "claude-state"
SUBAGENTS_DIR = STATE_DIR / "agents"
SUBAGENT_MAX_AGE = 6 * 3600
SUBAGENT_SILENT_MAX = 30 * 60
SUBAGENT_REPLY_MAX = 5 * 60
CLAUDE_SESSIONS = Path.home() / ".claude" / "sessions"
SESSION_STATUS = {"idle": "done", "shell": "done", "busy": "running", "waiting": "waiting"}
RANK = {"idle": -1, "done": 0, "running": 1, "waiting": 2}
INTERVAL = 1.0
KITTY_VERSION = [int(n) for n in re.search(r"(\d+)\.(\d+)\.(\d+)", subprocess.run(["kitty", "--version"], capture_output=True, text=True).stdout).groups()]


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
    msg = json.dumps({"cmd": "ls", "version": KITTY_VERSION, "no_response": False}).encode()
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


_last_entries = {}
_transcripts = {}
_last_replies = {}


def last_reply(session_id):
    """Identifiant de la dernière réponse de Claude, et vrai si le fil principal a fini son tour (Claude Code reste « busy » tant que des tâches de fond tournent)."""
    path = _transcripts.get(session_id)
    if path is None or not path.exists():
        path = next(Path.home().glob(f".claude/projects/*/{session_id}.jsonl"), None)
        if path is None:
            return None, False
        _transcripts[session_id] = path
    st = path.stat()
    key = (st.st_mtime, st.st_size)
    cached = _last_replies.get(path)
    if cached and cached[0] == key:
        return cached[1]
    with path.open("rb") as f:
        f.seek(max(0, st.st_size - 2_000_000))
        lines = f.read().splitlines()
    reply = ""
    ended = None
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if entry.get("type") not in ("assistant", "user") or entry.get("isSidechain"):
            continue
        if ended is None:
            ended = entry["type"] == "assistant" and entry["message"].get("stop_reason") == "end_turn"
        if entry["type"] == "assistant":
            reply = entry.get("uuid") or ""
            break
    _last_replies[path] = (key, (reply, bool(ended)))
    return reply, bool(ended)


def transcript_running(path):
    """Vrai si le sous-agent travaille encore : il attend un outil, ou un résultat d'outil récent attend sa suite."""
    st = path.stat()
    key = (st.st_mtime, st.st_size)
    cached = _last_entries.get(path)
    if cached and cached[0] == key:
        last = cached[1]
    else:
        with path.open("rb") as f:
            f.seek(max(0, st.st_size - 2_000_000))
            lines = f.read().splitlines()
        last = ""
        for raw in reversed(lines):
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            if entry.get("type") not in ("user", "assistant"):
                continue
            stop = (entry.get("message") or {}).get("stop_reason")
            last = "tool_use" if stop == "tool_use" else "end_turn" if stop else entry.get("type", "")
            break
        _last_entries[path] = (key, last)
    return last == "tool_use" or (last in ("user", "assistant") and time.time() - st.st_mtime < SUBAGENT_REPLY_MAX)


_log_starts = {}


def log_start(path):
    """Heure du premier message du journal d'un sous-agent."""
    if path not in _log_starts:
        with path.open() as f:
            first = json.loads(f.readline())
        _log_starts[path] = datetime.fromisoformat(first["timestamp"].replace("Z", "+00:00")).timestamp()
    return _log_starts[path]


def running_subagents(session_id, pid):
    """Sous-agents en cours lancés par ce processus claude : signalés par le hook (départ sans fin), sinon d'après leur journal."""
    now = time.time()
    start = started_at(pid)
    try:
        marks = [f for f in (SUBAGENTS_DIR / session_id).iterdir() if f.stat().st_mtime >= now - SUBAGENT_MAX_AGE]
    except OSError:
        marks = []
    done_at = {f.name.removesuffix(".done"): f.stat().st_mtime for f in marks if f.name.endswith(".done")}
    # Un sous-agent relancé (SendMessage) a une marque de départ plus récente que son .done
    ended = {f.name for f in marks if f.name in done_at and done_at[f.name] >= f.stat().st_mtime}
    ended |= done_at.keys() - {f.name for f in marks}
    alive, others = set(), set()
    for f in marks:
        if f.name.endswith(".done") or f.name in ended:
            continue
        owner = f.read_text().strip()
        mine = owner == str(pid) if owner else start is None or f.stat().st_mtime >= start - 1
        (alive if mine else others).add(f.name)
    for f in Path.home().glob(f".claude/projects/*/{session_id}/subagents/agent-*.jsonl"):
        agent = f.stem.removeprefix("agent-")
        if agent in alive or agent in others or agent in ended:
            continue
        try:
            if now - f.stat().st_mtime < SUBAGENT_SILENT_MAX and (start is None or log_start(f) >= start - 1) and transcript_running(f):
                alive.add(agent)
        except OSError:
            pass
    return len(alive)


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
        return (hook[1], agent, 0, None) if hook else ("idle", agent, 0, None)
    subagents = 0
    reply = None
    ended = False
    try:
        data = json.loads((CLAUDE_SESSIONS / f"{procs[0].get('pid')}.json").read_text())
        status = data.get("status")
        if status in SESSION_STATUS:
            session = (float(data.get("updatedAt") or 0) / 1000, SESSION_STATUS[status])
        if data.get("sessionId"):
            subagents = running_subagents(data["sessionId"], procs[0].get("pid"))
            reply, ended = last_reply(data["sessionId"])
    except (OSError, ValueError, AttributeError, TypeError):
        pass
    if session and session[1] == "running" and subagents and ended:
        session = (session[0], "done")
    if hook and session:
        return max(hook, session)[1], agent, subagents, reply
    if hook or session:
        return (hook or session)[1], agent, subagents, reply
    return ("done" if (win.get("title") or "").startswith(chr(0x2733)) else "running"), agent, subagents, reply


def os_window_state(kitty_pid, osw):
    best = None
    subagents = 0
    for tab in osw.get("tabs", []):
        for win in tab.get("windows", []):
            found = window_state(kitty_pid, win)
            if not found:
                continue
            subagents += found[2]
            if best is None or RANK[found[0]] > RANK[best[0]]:
                best = (*found[:2], win.get("cwd") or "", found[3])
    return (*best[:3], subagents, best[3]) if best else None


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
    states, agents, cwds, subagents, replies = {}, {}, {}, {}, {}
    for pid, group in by_pid.items():
        for client, osw in match(group, kitty_ls(pid)):
            found = os_window_state(pid, osw)
            if found:
                address = client["address"]
                states[address], agents[address], cwds[address], n, reply = found
                if n:
                    subagents[address] = n
                if reply is not None:
                    replies[address] = reply
    return {"states": states, "agents": agents, "cwds": cwds, "subagents": subagents, "replies": replies}


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
