#!/usr/bin/env python3
import json
import math
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
    if not re.fullmatch(r"[a-z0-9-]+", key) or key == "photos" or not path.is_file():
        raise SystemExit(f"unknown theme: {key}")
    t = json.loads(path.read_text())
    sources = [("", t)] + [(f"palettes.{m}.", p) for m, p in (t.get("palettes") or {}).items()]
    for prefix, src in sources:
        for group in PALETTE_GROUPS:
            for name, value in src.get(group, {}).items():
                if not HEX.match(value):
                    raise SystemExit(f"{path.name}: {prefix}{group}.{name} is not #RRGGBB: {value}")
    return t


def to_oklch(hexcolor):
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(int(hexcolor[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l_ = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m_ = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s_ = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    return L, math.hypot(a, b), math.atan2(b, a)


def from_oklch(L, C, h):
    def rgb(c):
        a, b = c * math.cos(h), c * math.sin(h)
        l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
        m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
        s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
        return (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
                -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
                -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)

    def inside(c):
        return all(-1e-4 <= v <= 1 + 1e-4 for v in rgb(c))

    if not inside(C):
        lo, hi = 0.0, C
        for _ in range(24):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if inside(mid) else (lo, mid)
        C = lo

    def enc(c):
        c = min(max(c, 0.0), 1.0)
        return round(255 * (c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055))
    return "#{:02X}{:02X}{:02X}".format(*(enc(v) for v in rgb(C)))


def flip_lightness(L, to, bg):
    if to == "light":
        return 0.95 - (L - bg) if L < 0.5 else 1.15 - L
    return 0.2 + (bg - L) if L > 0.72 else 1.15 - L


def flip_palette(pal, to):
    """The theme's own palette in the other mode: OKLCH lightness flipped around its background, hue and chroma
    kept, light surfaces tinted; the terminal keeps its designed colors."""
    colors = pal.get("colors", {})
    bg = to_oklch(colors["background"])[0]
    theme_hue = to_oklch(colors["primary"])[2]
    out = {g: dict(v) for g, v in pal.items() if g != "colors"}
    out["colors"] = {}
    for name, value in colors.items():
        L, C, h = to_oklch(value)
        L = min(max(flip_lightness(L, to, bg), 0.0), 1.0)
        if to == "light" and L > 0.8:
            h = h if C >= 0.01 else theme_hue
            C = max(C, 0.045)
        out["colors"][name] = from_oklch(L, C, h)
    return out


def palette(t, mode):
    pals = t.get("palettes") or {}
    if mode in pals:
        return pals[mode]
    if t.get("colors"):
        native = {g: t[g] for g in PALETTE_GROUPS if g in t}
        return native if t.get("mode", "dark") == mode else flip_palette(native, mode)
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
        if path.stem == "photos":
            continue
        try:
            t = load(path.stem)
        except (SystemExit, ValueError):
            continue
        found.append({"key": path.stem, "name": t.get("name", path.stem), "icon": t.get("icon", "palette"),
                      "modes": native_modes(t), "swatch": t.get("swatch", []), "order": t.get("order", 100),
                      "wallpapers": len(wallpaper_names(t))})
    found.sort(key=lambda t: (t["order"], t["name"]))
    return BUILTIN + found


def switchwall(*args, skip_applycolor=False):
    env = dict(os.environ, II_SKIP_APPLYCOLOR="1") if skip_applycolor else None
    subprocess.run([str(HERE / "switchwall.sh"), "--noswitch", *args], check=True, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_applycolor(timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        r = subprocess.run(["pgrep", "-u", str(os.getuid()), "-f", "scripts/colors/applycolor\\.sh"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            return
        time.sleep(0.05)


VIDEO_EXT = (".mp4", ".webm", ".mkv", ".avi", ".mov")


def set_wallpaper(path, mode):
    subprocess.run([str(HERE / "switchwall.sh"), "--image", str(path), "--mode", mode], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def set_wallpaper_path(path):
    if str(path).lower().endswith(VIDEO_EXT) or current_wallpaper().lower().endswith(VIDEO_EXT):
        return False
    r = subprocess.run(["jq", "--arg", "path", str(path), ".background.wallpaperPath = $path", str(SHELL_CONFIG)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return False
    write_atomic(SHELL_CONFIG, r.stdout)
    return True


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


def shell_hold(on):
    try:
        subprocess.run(["qs", "-c", "ii", "ipc", "call", "theme", "hold" if on else "release"], timeout=3,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        pass


def apply(key, wallpaper_step=None, mode=None):
    shell_hold(True)
    try:
        apply_held(key, wallpaper_step, mode)
    finally:
        shell_hold(False)


def apply_held(key, wallpaper_step=None, mode=None):
    if key in ALIASES:
        key, mode = ALIASES[key][0], mode or ALIASES[key][1]
    if mode not in MODES:
        mode = preferred_mode()
    builtin = {b["key"]: b for b in BUILTIN}
    if key in builtin:
        prev = previous_wallpaper()
        STATE_FILE.unlink(missing_ok=True)
        if prev and is_theme_wallpaper(current_wallpaper()) and not set_wallpaper_path(prev):
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
        if Path(current_wallpaper() or "/").resolve() != wallpaper.resolve() and not set_wallpaper_path(wallpaper):
            set_wallpaper(wallpaper, mode)
    switchwall("--mode", mode, "--type", "scheme-tonal-spot", "--color", t["seed"], skip_applycolor=bool(pal))
    if pal:
        override(pal)
    else:
        wait_applycolor()
    missing = [n for n in names if not (WALLPAPERS / f"{n}.jpg").is_file()]
    if missing:
        subprocess.Popen([sys.executable, str(THEMES / "make-wallpapers.py"), *missing], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
