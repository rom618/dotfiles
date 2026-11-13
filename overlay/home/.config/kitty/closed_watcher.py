import json
import os
import shlex
import time
from pathlib import Path

KEEP = 20
MAX_LINES = 5000
SNAPSHOT_EVERY = 15.0

_running = {}
_mod = None


def _store():
    base = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    d = Path(base) / "kitty-closed"
    d.mkdir(mode=0o700, exist_ok=True)
    return d


def _cwd(window):
    try:
        from kitty.utils import path_from_osc7_url
        url = window.screen.last_reported_cwd
        if url:
            p = path_from_osc7_url(url)
            if p and os.path.isdir(p):
                return p
    except Exception:
        pass
    try:
        p = window.child.current_cwd
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return None


def _session_save():
    global _mod
    if _mod is None:
        import importlib.util
        src = Path.home() / ".config/hypr/custom/scripts/session-save.py"
        spec = importlib.util.spec_from_file_location("hypr_session_save", src)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _mod = mod
    return _mod


def _program(window):
    try:
        found = _session_save().window_program({"foreground_processes": window.child.foreground_processes})
    except Exception:
        return None
    if not found:
        return None
    if found.get("claude"):
        return {"cmd": f"claude --resume {shlex.quote(found['claude'])}", "cwd": found.get("cwd")}
    return {"cmd": shlex.join(found["argv"]), "cwd": found.get("cwd")}


def _stop(window_id):
    entry = _running.pop(window_id, None)
    if entry and entry.get("timer"):
        try:
            from kitty.fast_data_types import remove_timer
            remove_timer(entry["timer"])
        except Exception:
            pass


def _snapshot(boss, window_id):
    entry = _running.get(window_id)
    window = boss.window_id_map.get(window_id)
    if entry is None or window is None:
        _stop(window_id)
        return
    entry["program"] = _program(window)


def on_cmd_startstop(boss, window, data):
    _stop(window.id)
    if not data.get("is_start"):
        return
    try:
        from kitty.fast_data_types import add_timer
    except Exception:
        return
    wid = window.id
    _running[wid] = {"program": None}
    add_timer(lambda _t: _snapshot(boss, wid), 1.0, False)
    _running[wid]["timer"] = add_timer(lambda _t: _snapshot(boss, wid), SNAPSHOT_EVERY, True)


def on_close(boss, window, data):
    entry = _running.get(window.id) or {}
    program = entry.get("program")
    _stop(window.id)
    try:
        if window.overlay_parent is not None:
            return
    except Exception:
        pass
    cwd = _cwd(window)
    if program and program.get("cwd") and os.path.isdir(program["cwd"]):
        cwd = program["cwd"]
    if not cwd:
        return
    try:
        text = window.as_text(as_ansi=True, add_history=True)
    except Exception:
        text = ""
    lines = text.rstrip("\n").split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and not program:
        lines.pop()
    text = "\n".join(lines[-MAX_LINES:])
    d = _store()
    stem = f"{time.time_ns()}"
    (d / f"{stem}.txt").write_text(text + "\n" if text else "")
    (d / f"{stem}.json").write_text(json.dumps({"cwd": cwd, "title": window.title, "cmd": program["cmd"] if program else None}))
    entries = sorted(d.glob("*.json"))
    for old in entries[:-KEEP]:
        old.unlink(missing_ok=True)
        old.with_suffix(".txt").unlink(missing_ok=True)
