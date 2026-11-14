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
WALL_FILE = STATE / "theme-wallpaper.json"
CHOICE_FILE = STATE / "theme-choices.json"
PREFS_FILE = STATE / "theme-prefs.json"
SHELL_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "illogical-impulse" / "config.json"
WALLPAPERS = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "quickshell-themes" / "wallpapers"
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

MODES = ("light", "dark")
PALETTE_GROUPS = ("colors", "terminal", "kitty")
BUILTIN = [
    {"key": "default", "name": "Wallpaper", "icon": "wallpaper", "modes": list(MODES),
     "swatch": ["#F4F1F6", "#1C1B1F"], "wallpaper": True},
]
ALIASES = {"dark": ("default", "dark"), "white": ("default", "light")}


def camel(key):
    return re.sub(r"_([a-z])", lambda m: m.group(1).upper(), key)


def load(key):
    path = THEMES / f"{key}.json"
    if not re.fullmatch(r"[a-z0-9-]+", key) or not path.is_file():
        raise SystemExit(f"unknown theme: {key}")
    t = json.loads(path.read_text())
    sources = [("", t)] + [(f"palettes.{m}.", p) for m, p in (t.get("palettes") or {}).items()]
    for prefix, src in sources:
        for group in PALETTE_GROUPS:
            for name, value in src.get(group, {}).items():
                if not HEX.match(value):
                    raise SystemExit(f"{path.name}: {prefix}{group}.{name} is not #RRGGBB: {value}")
    return t


def palette(t, mode):
    pals = t.get("palettes") or {}
    if mode in pals:
        return pals[mode]
    if t.get("mode", "dark") == mode and t.get("colors"):
        return {g: t[g] for g in PALETTE_GROUPS if g in t}
    return None


def native_modes(t):
    return [m for m in MODES if palette(t, m)]


def preferred_mode():
    try:
        mode = json.loads(PREFS_FILE.read_text()).get("mode")
    except (OSError, ValueError, AttributeError):
        mode = None
    if mode in MODES:
        return mode
    r = subprocess.run(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                       capture_output=True, text=True)
    return "dark" if "dark" in r.stdout else "light"


def themes():
    found = []
    for path in sorted(THEMES.glob("*.json")):
        try:
            t = load(path.stem)
        except (SystemExit, ValueError):
            continue
        found.append({"key": path.stem, "name": t.get("name", path.stem), "icon": t.get("icon", "palette"),
                      "modes": native_modes(t), "swatch": t.get("swatch", []), "order": t.get("order", 100),
                      "wallpapers": len(wallpaper_names(t))})
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


def set_wallpaper(path, mode):
    subprocess.run([str(HERE / "switchwall.sh"), "--image", str(path), "--mode", mode], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


_AVAILABLE = None


def available_wallpapers():
    global _AVAILABLE
    if _AVAILABLE is None:
        r = subprocess.run([sys.executable, str(THEMES / "make-wallpapers.py"), "--list"], capture_output=True, text=True)
        _AVAILABLE = set(r.stdout.split()) if r.returncode == 0 else set()
    return _AVAILABLE


def wallpaper_names(t):
    names = t.get("wallpapers") or ([t["wallpaper"]] if t.get("wallpaper") else [])
    known = available_wallpapers()
    return [n for n in names if isinstance(n, str) and n in known]


def load_choices():
    try:
        return json.loads(CHOICE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def theme_wallpaper(name):
    if not name or not re.fullmatch(r"[a-z0-9-]+", name):
        return None
    path = WALLPAPERS / f"{name}.jpg"
    if not path.is_file():
        subprocess.run([sys.executable, str(THEMES / "make-wallpapers.py"), name],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return path if path.is_file() else None


def current_wallpaper():
    try:
        return json.loads(SHELL_CONFIG.read_text()).get("background", {}).get("wallpaperPath") or ""
    except (OSError, ValueError):
        return ""


def is_theme_wallpaper(path):
    try:
        return bool(path) and Path(path).resolve().parent == WALLPAPERS.resolve()
    except OSError:
        return False


def remember_wallpaper():
    current = current_wallpaper()
    if current and not is_theme_wallpaper(current):
        write_atomic(WALL_FILE, json.dumps({"previous": current}) + "\n")


def previous_wallpaper():
    try:
        prev = json.loads(WALL_FILE.read_text()).get("previous") or ""
    except (OSError, ValueError):
        return ""
    return prev if prev and Path(prev).exists() else ""


def write_atomic(path, text):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def current_background():
    try:
        return (json.loads((STATE / "colors.json").read_text()).get("background") or "").lower()
    except (OSError, ValueError, AttributeError):
        return ""


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
    kitty_overrides(t.get("kitty", {}))
    json_path = STATE / "colors.json"
    data = json.loads(json_path.read_text())
    data.update({k: v.lower() for k, v in colors.items()})
    write_atomic(json_path, json.dumps(data, indent=2) + "\n")


def kitty_overrides(values):
    path = STATE / "terminal" / "kitty-theme.conf"
    if not values or not path.exists():
        return
    lines = []
    for line in path.read_text().splitlines():
        key = line.split(None, 1)[0] if line.strip() else ""
        if key in values:
            line = f"{key:<22}{values[key]}"
        lines.append(line)
    write_atomic(path, "\n".join(lines) + "\n")
    pids = subprocess.run(["pidof", "kitty"], capture_output=True, text=True).stdout.split()
    for pid in pids:
        for extra in (["--configured"], []):
            subprocess.run(["kitty", "@", "--to", f"unix:@mykitty-{pid}", "set-colors", "--all", *extra, str(path)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def apply(key, wallpaper_step=None, mode=None):
    if key in ALIASES:
        key, mode = ALIASES[key][0], mode or ALIASES[key][1]
    if mode not in MODES:
        mode = preferred_mode()
    builtin = {b["key"]: b for b in BUILTIN}
    if key in builtin:
        prev = previous_wallpaper()
        STATE_FILE.unlink(missing_ok=True)
        if prev and is_theme_wallpaper(current_wallpaper()):
            set_wallpaper(prev, mode)
        switchwall("--mode", mode, "--type", "auto", "--color", "clear")
        return
    t = load(key)
    pal = palette(t, mode)
    names = wallpaper_names(t)
    choices = load_choices()
    index = int(choices.get(key, 0)) if names else 0
    if names and wallpaper_step == "next":
        index += 1
    elif names and wallpaper_step == "prev":
        index -= 1
    elif names and isinstance(wallpaper_step, int):
        index = wallpaper_step
    index = index % len(names) if names else 0
    if names:
        choices[key] = index
        write_atomic(CHOICE_FILE, json.dumps(choices) + "\n")
    wallpaper = theme_wallpaper(names[index]) if names else None
    if wallpaper:
        remember_wallpaper()
        if Path(current_wallpaper() or "/").resolve() != wallpaper.resolve():
            set_wallpaper(wallpaper, mode)
    switchwall("--mode", mode, "--type", "scheme-tonal-spot", "--color", t["seed"])
    if pal:
        override(pal)
    else:
        wait_applycolor()
    write_atomic(STATE_FILE, json.dumps({"theme": key, "mode": mode, "decor": t.get("decor", ""),
                                         "wallpaper_index": index, "wallpapers": len(names),
                                         "background": current_background()}) + "\n")


def main():
    args = sys.argv[1:]
    if args == ["--list"]:
        print(json.dumps(themes()))
        return 0
    usage = "usage: apply-theme.py --list | THEME [--mode light|dark] [--next-wallpaper | --prev-wallpaper | --wallpaper N]"
    if not args or args[0].startswith("-"):
        print(usage, file=sys.stderr)
        return 2
    key, rest = args[0], args[1:]
    mode = step = None
    while rest:
        opt = rest.pop(0)
        if opt == "--mode" and rest and rest[0] in MODES:
            mode = rest.pop(0)
        elif opt in ("--next-wallpaper", "--prev-wallpaper"):
            step = "next" if opt == "--next-wallpaper" else "prev"
        elif opt == "--wallpaper" and rest and rest[0].isdigit():
            step = int(rest.pop(0))
        else:
            print(usage, file=sys.stderr)
            return 2
    apply(key, step, mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
