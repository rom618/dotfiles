#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

FILE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "quickshell" / "colors.json"
KEEP = 16


def load():
    try:
        d = json.loads(FILE.read_text())
        if isinstance(d, dict):
            return {"current": d.get("current", ""), "history": list(d.get("history", []))}
    except Exception:
        pass
    return {"current": "", "history": []}


def save(d):
    FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d))
    tmp.replace(FILE)


def add(color):
    color = color.strip().upper()
    if not re.fullmatch(r"#[0-9A-F]{6}", color):
        return None
    d = load()
    d["current"] = color
    d["history"] = [color] + [c for c in d["history"] if c.upper() != color][:KEEP - 1]
    save(d)
    return color


def reopen():
    subprocess.run(["qs", "-c", "ii", "ipc", "call", "tools", "open", "color"], capture_output=True, timeout=5)


def pick():
    time.sleep(0.3)
    try:
        r = subprocess.run(["hyprpicker", "-f", "hex", "-b", "-q"], capture_output=True, text=True, timeout=120)
        m = re.search(r"#[0-9A-Fa-f]{6}", r.stdout)
        color = add(m.group(0)) if m else None
        if color:
            subprocess.Popen(["wl-copy", color], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        color = None
    reopen()
    return color


def main():
    args = sys.argv[1:]
    if args == ["--pick"]:
        print(json.dumps({"picked": pick()}))
    elif len(args) == 2 and args[0] == "--add":
        print(json.dumps({"added": add(args[1])}))
    elif args == ["--list"]:
        print(json.dumps(load()))
    else:
        print("usage: colors.py --pick | --add '#RRGGBB' | --list", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
