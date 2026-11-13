#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
THEMES = HERE.parent.parent / "themes"
STATE = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "quickshell" / "user" / "generated"
STATE_FILE = STATE / "theme.json"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

BUILTIN = [
    {"key": "dark", "name": "Dark", "icon": "dark_mode", "mode": "dark", "swatch": ["#1C1B1F"], "wallpaper": True},
    {"key": "white", "name": "White", "icon": "light_mode", "mode": "light", "swatch": ["#F4F1F6"], "wallpaper": True},
]


def camel(key):
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), key)


def load(key):
    path = THEMES / f"{key}.json"
    if not re.fullmatch(r"[a-z0-9-]+", key) or not path.is_file():
        raise SystemExit(f"unknown theme: {key}")
    t = json.loads(path.read_text())
    for group in ("colors", "terminal"):
        for name, value in t.get(group, {}).items():
            if not HEX.match(value):
                raise SystemExit(f"{path.name}: {group}.{name} is not #RRGGBB: {value}")
    return t


def themes():
    found = []
    for path in sorted(THEMES.glob("*.json")):
        try:
            t = load(path.stem)
        except (SystemExit, ValueError):
            continue
        found.append({"key": path.stem, "name": t.get("name", path.stem), "icon": t.get("icon", "palette"),
                      "mode": t.get("mode", "dark"), "swatch": t.get("swatch", []), "order": t.get("order", 100),
                      "background": t.get("colors", {}).get("background", "")})
    found.sort(key=lambda t: (t["order"], t["name"]))
    return BUILTIN + found


def switchwall(*args):
    subprocess.run([str(HERE / "switchwall.sh"), "--noswitch", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_applycolor(timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        r = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f", "scripts/colors/applycolor\\.sh"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            return
        time.sleep(0.05)


def write_atomic(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def override(t):
    colors = t.get("colors", {})
    terminal = t.get("terminal", {})
    scss_path = STATE / "material_colors.scss"
    wanted = {camel(k): v for k, v in colors.items()}
    wanted.update(terminal)
    lines = []
    for line in scss_path.read_text().splitlines():
        m = re.match(r"^\$([A-Za-z0-9_]+):\s*([^;]*);", line)
        if m and m.group(1) in wanted:
            line = f"${m.group(1)}: {wanted[m.group(1)]};"
        lines.append(line)
    wait_applycolor()
    write_atomic(scss_path, "\n".join(lines) + "\n")
    subprocess.run([str(HERE / "applycolor.sh")], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    wait_applycolor()
    json_path = STATE / "colors.json"
    data = json.loads(json_path.read_text())
    data.update({k: v.lower() for k, v in colors.items()})
    write_atomic(json_path, json.dumps(data, indent=2) + "\n")


def apply(key):
    builtin = {b["key"]: b for b in BUILTIN}
    if key in builtin:
        switchwall("--mode", builtin[key]["mode"], "--type", "auto", "--color", "clear")
        STATE_FILE.unlink(missing_ok=True)
        return
    t = load(key)
    switchwall("--mode", t.get("mode", "dark"), "--type", "scheme-tonal-spot", "--color", t["seed"])
    override(t)
    write_atomic(STATE_FILE, json.dumps({"theme": key, "background": t.get("colors", {}).get("background", "").lower()}) + "\n")


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--list":
        print(json.dumps(themes()))
        return 0
    if len(sys.argv) == 2:
        apply(sys.argv[1])
        return 0
    print("usage: apply-theme.py --list | THEME", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
