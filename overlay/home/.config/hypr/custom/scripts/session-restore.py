#!/usr/bin/env python3
import argparse
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "hypr-session"
STATE_FILE = STATE_DIR / "session.json"
RESTORING = STATE_DIR / "restoring"
KITTY_DIR = STATE_DIR / "kitty"
COVER_FLAG = STATE_DIR / "cover"
COVER_QML = Path(__file__).resolve().parent / "restore-cover" / "shell.qml"
WALLPAPER_CONFIG = Path.home() / ".config" / "illogical-impulse" / "config.json"
SPAWN_DELAY = 0.3
PLACE_SECONDS = 90
COVER_SECONDS = 30
CLASS_WAIT = 15
POLL = 0.5
SETTLE_POLLS = 3

DRY_RUN = False


def lua_string(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"


def dispatch(expr):
    if DRY_RUN:
        print(expr)
        return
    subprocess.run(["hyprctl", "dispatch", expr], capture_output=True, check=False)


def clients():
    try:
        out = subprocess.run(["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=10)
        data = json.loads(out.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    return data if isinstance(data, list) else []


def norm_title(title):
    return re.sub(r"^[^0-9A-Za-z~/.]+", "", title or "").strip()


def rules(win):
    parts = []
    if win.get("workspace"):
        parts.append(f"workspace = {lua_string(win['workspace'])}")
    if win.get("floating"):
        at = win.get("at") or [0, 0]
        size = win.get("size") or [800, 600]
        parts += ["float = true", f"move = {lua_string(f'{at[0]} {at[1]}')}",
                  f"size = {lua_string(f'{size[0]} {size[1]}')}"]
    fs = int(win.get("fullscreen") or 0)
    if fs == 1:
        parts.append("maximize = true")
    elif fs >= 2:
        parts.append("fullscreen = true")
    return "{" + ", ".join(parts) + "}"


def exec_cmd(command, win=None):
    expr = f"hl.dsp.exec_cmd({lua_string(command)}"
    if win:
        expr += f", {rules(win)}"
    dispatch(expr + ")")


def with_cwd(command, cwd):
    if cwd and os.path.isdir(cwd):
        return f"cd {shlex.quote(cwd)} && exec {command}"
    return f"exec {command}"


def shell_wrap(command):
    if shutil.which("fish"):
        return ["fish", "-C", command]
    return ["sh", "-c", f'{command}; exec "${{SHELL:-sh}}"']


def kitty_launch(win):
    cwd = win.get("cwd")
    if win.get("claude"):
        command = f"claude --resume {shlex.quote(win['claude'])}"
        if win.get("name"):
            title = shlex.quote(f"{chr(0x2733)} {win['name']}")
            command = f"printf '\\033]2;%s\\007' {title}; {command}"
        program = shell_wrap(command)
    elif win.get("argv"):
        program = shell_wrap(shlex.join(win["argv"]))
    else:
        program = []
    args = ["launch"]
    if cwd and os.path.isdir(cwd):
        args.append(f"--cwd={cwd}")
    return shlex.join(args + program)


def kitty_session(entry, path):
    lines = []
    active = 0
    for i, tab in enumerate(entry.get("tabs") or []):
        lines.append("new_tab")
        if tab.get("layout"):
            lines.append(f"layout {tab['layout']}")
        for win in tab.get("windows") or [{}]:
            lines.append(kitty_launch(win))
        if tab.get("active"):
            active = i
    if not lines:
        lines = ["new_tab", "launch"]
    lines.append(f"focus_tab {active}")
    path.write_text("\n".join(lines) + "\n")


CHROMIUM = {"chrome", "google-chrome", "google-chrome-stable", "google-chrome-beta", "chromium", "chromium-browser",
            "brave", "brave-browser", "vivaldi", "vivaldi-bin", "microsoft-edge", "microsoft-edge-stable", "thorium-browser"}


def restore_argv(argv):
    if argv and os.path.basename(argv[0]) in CHROMIUM and "--restore-last-session" not in argv:
        return argv + ["--restore-last-session"]
    return argv


def matches(entry, name):
    name = name.lower()
    argv0 = os.path.basename((entry.get("argv") or [""])[0]).lower()
    return entry.get("class", "").lower() == name or argv0 == name


def launch(entries, ensure):
    expected = []
    kitty_dir = KITTY_DIR.with_name("kitty-dry-run") if DRY_RUN else KITTY_DIR
    kitty_dir.mkdir(parents=True, exist_ok=True)
    for old in kitty_dir.glob("*.session"):
        old.unlink()
    pending = list(ensure)
    for i, entry in enumerate(entries):
        if entry.get("kind") == "kitty":
            path = kitty_dir / f"{i}.session"
            kitty_session(entry, path)
            exec_cmd(f"exec kitty --session {shlex.quote(str(path))}", entry)
        else:
            argv = entry.get("argv")
            windows = entry.get("windows") or [{}]
            if not argv:
                continue
            exec_cmd(with_cwd(shlex.join(restore_argv(argv)), entry.get("cwd")), windows[0])
            expected += [{"class": entry.get("class", ""), **w} for w in windows]
            pending = [n for n in pending if not matches(entry, n)]
        time.sleep(SPAWN_DELAY)
    for name in pending:
        exec_cmd(f"exec {shlex.quote(name)}")
    return expected


def wallpaper():
    try:
        path = json.loads(WALLPAPER_CONFIG.read_text()).get("background", {}).get("wallpaperPath") or ""
    except (OSError, ValueError, AttributeError):
        return ""
    return path if path and os.path.isfile(path) else ""


def start_cover(entries):
    if DRY_RUN or not entries or not shutil.which("qs") or not COVER_QML.is_file():
        return None
    COVER_FLAG.touch()
    env = dict(os.environ, RESTORE_COVER_FLAG=str(COVER_FLAG), RESTORE_COVER_WALLPAPER=wallpaper())
    try:
        return subprocess.Popen(["qs", "-p", str(COVER_QML)], env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        COVER_FLAG.unlink(missing_ok=True)
        return None


def page_title(title):
    return re.sub(r"\s+[-\u2014\u2013]\s+[^-\u2014\u2013]+$", "", norm_title(title))


def pair(cands, entries):
    pairs = []
    free = list(entries)
    left = []
    for c in cands:
        title = norm_title(c.get("title"))
        hit = next((e for e in free if norm_title(e.get("title")) == title), None)
        if hit:
            pairs.append((c, hit))
            free.remove(hit)
        else:
            left.append(c)
    scored = sorted(((difflib.SequenceMatcher(None, page_title(c.get("title")), page_title(e.get("title"))).ratio(), i, j)
                     for i, c in enumerate(left) for j, e in enumerate(free)), reverse=True)
    taken_c, taken_e = set(), set()
    for ratio, i, j in scored:
        if ratio < 0.6:
            break
        if i in taken_c or j in taken_e:
            continue
        pairs.append((left[i], free[j]))
        taken_c.add(i)
        taken_e.add(j)
    rest_c = [c for i, c in enumerate(left) if i not in taken_c]
    rest_e = [e for j, e in enumerate(free) if j not in taken_e]
    pairs.extend(zip(rest_c, rest_e))
    return pairs


def move_to(addr, ws, current):
    if ws and current != ws:
        dispatch(f"hl.dsp.window.move({{workspace = {lua_string(ws)}, follow = false, "
                 f"window = {lua_string('address:' + addr)}}})")


def place(expected, before, kitty_count, cover):
    if DRY_RUN:
        return
    start = time.time()
    stable = {}
    done = set(before)
    first_seen = {}
    covered = cover is not None
    last_snap = None
    still = 0
    while True:
        now = time.time()
        cs = clients()
        new = [c for c in cs if c.get("address") and c["address"] not in before]
        for c in new:
            prev = stable.get(c["address"])
            title = c.get("title")
            stable[c["address"]] = (title, prev[1] + 1 if prev and prev[0] == title else 1)
        for cls in {e["class"] for e in expected if not e.get("_used")}:
            free = [e for e in expected if not e.get("_used") and e["class"] == cls]
            open_ = [c for c in new if c.get("class") == cls and c["address"] not in done]
            ready = [c for c in open_ if stable[c["address"]][1] >= SETTLE_POLLS]
            if not ready:
                continue
            first_seen.setdefault(cls, now)
            waiting = len(ready) < len(open_) or len(open_) < len(free)
            if waiting and now - first_seen[cls] < CLASS_WAIT:
                continue
            for c, e in pair(ready, free):
                e["_used"] = True
                done.add(c["address"])
                move_to(c["address"], e.get("workspace"), c.get("workspace", {}).get("name"))
        pending = any(not e.get("_used") for e in expected)
        if covered:
            snap = sorted((c.get("address"), c.get("workspace", {}).get("name"), tuple(c.get("at") or ()),
                           tuple(c.get("size") or ()), c.get("fullscreen")) for c in cs)
            still = still + 1 if snap == last_snap else 0
            last_snap = snap
            kitties = sum(1 for c in new if c.get("class") == "kitty")
            if (not pending and kitties >= kitty_count and still >= SETTLE_POLLS) or now - start > COVER_SECONDS:
                COVER_FLAG.unlink(missing_ok=True)
                covered = False
        if not covered and (not pending or now - start > PLACE_SECONDS):
            return
        time.sleep(POLL)


def main():
    global DRY_RUN
    parser = argparse.ArgumentParser()
    parser.add_argument("state_file", nargs="?", type=Path, default=STATE_FILE)
    parser.add_argument("--ensure", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    DRY_RUN = args.dry_run

    try:
        entries = json.loads(args.state_file.read_text()).get("entries") or []
    except (OSError, ValueError, AttributeError):
        entries = []

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not DRY_RUN:
        RESTORING.touch()
    try:
        before = {c.get("address") for c in clients()}
        cover = start_cover(entries)
        expected = launch(entries, args.ensure)
        kitty_count = sum(1 for e in entries if e.get("kind") == "kitty")
        place(expected, before, kitty_count, cover)
    finally:
        COVER_FLAG.unlink(missing_ok=True)
        if not DRY_RUN:
            RESTORING.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
