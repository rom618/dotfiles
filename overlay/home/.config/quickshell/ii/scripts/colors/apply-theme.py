#!/usr/bin/env python3
import contextlib
import fcntl
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tomllib
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
CACHE = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "quickshell" / "theme-cache"
MATUGEN_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "matugen" / "config.toml"
TERMINAL = HERE / "terminal"
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


def switchwall(*args):
    subprocess.run([str(HERE / "switchwall.sh"), "--noswitch", *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


VIDEO_EXT = (".mp4", ".webm", ".mkv", ".avi", ".mov")


def set_wallpaper(path, mode):
    subprocess.run([str(HERE / "switchwall.sh"), "--image", str(path), "--mode", mode], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def set_wallpaper_path(path, accent=None):
    if str(path).lower().endswith(VIDEO_EXT) or current_wallpaper().lower().endswith(VIDEO_EXT):
        return False
    return edit_shell_config(path=path, accent=accent)


def edit_shell_config(path=None, accent=None):
    filters = [".background.wallpaperPath = $path"] if path is not None else []
    filters += [".appearance.palette.accentColor = $accent"] if accent is not None else []
    r = subprocess.run(["jq", "--arg", "path", str(path), "--arg", "accent", str(accent), " | ".join(filters),
                        str(SHELL_CONFIG)], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip():
        return False
    if r.stdout != SHELL_CONFIG.read_text():
        write_atomic(SHELL_CONFIG, r.stdout)
    return True


_AVAILABLE = None


def wallpaper_listing():
    sources = [THEMES / n for n in ("make-wallpapers.py", "photos.json", "private_wallpapers.py")]
    return CACHE / f"wallpapers-{digest(*(p.read_bytes() if p.is_file() else b'' for p in sources))}.txt"


def available_wallpapers():
    global _AVAILABLE
    if _AVAILABLE is None:
        listing = wallpaper_listing()
        if not listing.is_file():
            r = subprocess.run([sys.executable, str(THEMES / "make-wallpapers.py"), "--list"], capture_output=True, text=True)
            if r.returncode != 0:
                return set()
            CACHE.mkdir(parents=True, exist_ok=True)
            write_atomic(listing, r.stdout)
        _AVAILABLE = set(listing.read_text().split())
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


def shell_config():
    return json.loads(SHELL_CONFIG.read_text()) if SHELL_CONFIG.is_file() else {}


def wallpaper_theming():
    return shell_config().get("appearance", {}).get("wallpaperTheming", {})


def digest(*parts):
    h = hashlib.sha256()
    for part in parts:
        h.update(part if isinstance(part, bytes) else str(part).encode())
        h.update(b"\0")
    return h.hexdigest()[:20]


def matugen_templates():
    cfg = tomllib.loads(MATUGEN_CONFIG.read_text())
    return cfg.get("config", {}), {name: (Path(t["input_path"]).expanduser(), Path(t["output_path"]).expanduser())
                                   for name, t in cfg.get("templates", {}).items()}


def venv():
    return Path(os.path.expandvars(os.environ["ILLOGICAL_IMPULSE_VIRTUAL_ENV"])).expanduser()


_INPUTS = None


def inputs_digest():
    """Everything a prepared theme depends on apart from the theme file and the mode."""
    global _INPUTS
    if _INPUTS is None:
        _, templates = matugen_templates()
        files = [Path(__file__).resolve(), HERE / "generate_colors_material.py", HERE / "applycolor.sh",
                 TERMINAL / "kitty-theme.conf", TERMINAL / "sequences.txt", TERMINAL / "scheme-base.json",
                 MATUGEN_CONFIG, *(src for src, _ in templates.values())]
        matugen = Path(shutil.which("matugen")).stat()
        packages = [p.stat().st_mtime_ns for p in sorted((venv() / "lib").glob("python*/site-packages"))]
        theming = wallpaper_theming()
        live = []
        if theming.get("enableAppsAndShell") is False:
            live = [(STATE / "material_colors.scss").read_bytes(), (STATE / "colors.json").read_bytes()]
        _INPUTS = digest(*(f.read_bytes() for f in files), matugen.st_mtime_ns, matugen.st_size, *packages,
                         json.dumps(theming, sort_keys=True), *live)
    return _INPUTS


def entry_dir(key, mode):
    return CACHE / f"{key}-{mode}-{digest(inputs_digest(), (THEMES / f'{key}.json').read_bytes(), mode)}"


def override_scss(scss, pal):
    wanted = {camel(k): v for k, v in pal.get("colors", {}).items()}
    wanted.update(pal.get("terminal", {}))
    lines = []
    for line in scss.splitlines():
        m = re.match(r"^\$([A-Za-z0-9_]+):\s*([^;]*);", line)
        if m and m.group(1) in wanted:
            line = f"${m.group(1)}: {wanted[m.group(1)]};"
        lines.append(line)
    return "\n".join(lines) + "\n"


def fill_template(text, scss):
    """What applycolor.sh's sed loop does: each `$name #` becomes the color without its #."""
    for line in scss.splitlines():
        m = re.match(r"^(\$[A-Za-z0-9_]+):\s*([^;]*);", line)
        if m:
            text = text.replace(f"{m.group(1)} #", m.group(2).removeprefix("#"))
    return text


def kitty_overrides(conf, values):
    lines = []
    for line in conf.splitlines():
        key = line.split(None, 1)[0] if line.strip() else ""
        if key in values:
            line = f"{key:<22}{values[key]}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def run_matugen(build, seed, mode):
    settings, templates = matugen_templates()
    toml = ["[config]"] + [f"{k} = {json.dumps(v)}" for k, v in settings.items()]
    for name, (src, _) in templates.items():
        toml += ["", f"[templates.{name}]", f"input_path = {json.dumps(str(src))}",
                 f"output_path = {json.dumps(str(build / ('matugen-' + name)))}"]
    (build / "matugen.toml").write_text("\n".join(toml) + "\n")
    subprocess.run(["matugen", "-c", str(build / "matugen.toml"), "--source-color-index", "0", "color", "hex", seed,
                    "--mode", mode, "--type", "scheme-tonal-spot"], check=True, cwd=build,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {str(dst): f"matugen-{name}" for name, (_, dst) in templates.items()}


def generate_scss(build, seed, mode):
    props = wallpaper_theming().get("terminalGenerationProps", {})
    args = ["--color", seed, "--mode", "dark" if props.get("forceDarkMode") is True else mode,
            "--scheme", "scheme-tonal-spot", "--termscheme", str(TERMINAL / "scheme-base.json"), "--blend_bg_fg",
            "--cache", str(build / "color.txt")]
    for prop, flag in (("harmony", "--harmony"), ("harmonizeThreshold", "--harmonize_threshold"),
                       ("termFgBoost", "--term_fg_boost")):
        if props.get(prop) is not None:
            args += [flag, str(props[prop])]
    return subprocess.run([str(venv() / "bin" / "python3"), str(HERE / "generate_colors_material.py"), *args],
                          check=True, capture_output=True, text=True).stdout


def prepare(key, mode):
    """Every file a switch to this theme and mode writes, built in the cache without touching the desktop."""
    entry = entry_dir(key, mode)
    if (entry / "manifest.json").is_file():
        return entry
    t = load(key)
    CACHE.mkdir(parents=True, exist_ok=True)
    build = CACHE / f".prep-{os.getpid()}-{key}-{mode}"
    shutil.rmtree(build, ignore_errors=True)
    build.mkdir()
    if wallpaper_theming().get("enableAppsAndShell") is False:
        files = {}
        scss = (STATE / "material_colors.scss").read_text()
        colors_text = (STATE / "colors.json").read_text()
    else:
        files = run_matugen(build, t["seed"], mode)
        scss = generate_scss(build, t["seed"], mode)
        colors_text = (build / files.pop(str(STATE / "colors.json"))).read_text()
    pal = palette(t, mode)
    if pal:
        scss = override_scss(scss, pal)
        colors = json.loads(colors_text)
        colors.update({k: v.lower() for k, v in pal.get("colors", {}).items()})
        colors_text = json.dumps(colors, indent=2) + "\n"
    kitty = fill_template((TERMINAL / "kitty-theme.conf").read_text(), scss)
    if pal and pal.get("kitty"):
        kitty = kitty_overrides(kitty, pal["kitty"])
    alpha = re.search(r"^term_alpha=(\d+)", (HERE / "applycolor.sh").read_text(), re.M).group(1)
    sequences = fill_template((TERMINAL / "sequences.txt").read_text(), scss).replace("$alpha", alpha)
    for name, text in (("material_colors.scss", scss), ("kitty-theme.conf", kitty), ("sequences.txt", sequences),
                       ("colors.json", colors_text)):
        (build / name).write_text(text)
    manifest = {"files": files | {str(STATE / "material_colors.scss"): "material_colors.scss"},
                "terminal": {str(STATE / "terminal" / "kitty-theme.conf"): "kitty-theme.conf",
                             str(STATE / "terminal" / "sequences.txt"): "sequences.txt"},
                "colors": {str(STATE / "colors.json"): "colors.json"}}
    (build / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    try:
        build.rename(entry)
    except OSError:
        if not (entry / "manifest.json").is_file():
            raise
        shutil.rmtree(build)
    return entry


def install(entry, group):
    for dst, name in json.loads((entry / "manifest.json").read_text())[group].items():
        dst = Path(dst).resolve()
        data = (entry / name).read_bytes()
        if dst.is_file() and dst.read_bytes() == data:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        tmp = dst.with_name(dst.name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(dst)


def recolor_terminals():
    """kitty windows in parallel, one set-colors each (--configured also sets the current colors); other
    terminals get the escape sequences on their pty, as applycolor.sh does."""
    conf = STATE / "terminal" / "kitty-theme.conf"
    pids = subprocess.run(["pidof", "kitty"], capture_output=True, text=True).stdout.split()
    procs = [subprocess.Popen(["kitten", "@", "--to", f"unix:@mykitty-{pid}", "set-colors", "--all", "--configured",
                               str(conf)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for pid in pids]
    sequences = (STATE / "terminal" / "sequences.txt").read_bytes()
    for pts in Path("/dev/pts").iterdir():
        if pts.name.isdigit():
            with contextlib.suppress(OSError):
                fd = os.open(pts, os.O_WRONLY | os.O_NOCTTY | os.O_NONBLOCK)
                try:
                    os.write(fd, sequences)
                finally:
                    os.close(fd)
    return procs


def background(*cmd, stdout=subprocess.DEVNULL, niceness=10):
    subprocess.Popen(["nice", "-n", str(niceness), *cmd], start_new_session=True, stdin=subprocess.DEVNULL,
                     stdout=stdout, stderr=subprocess.DEVNULL)


def post_process():
    """What switchwall.sh starts after the colors, off the critical path."""
    cfg = shell_config()
    if cfg.get("appearance", {}).get("wallpaperTheming", {}).get("enableQtApps") is not False:
        background(str(MATUGEN_CONFIG.parent / "templates" / "kde" / "kde-material-you-colors-wrapper.sh"),
                   "--scheme-variant", "scheme-tonal-spot")
    background(str(HERE / "code" / "material-code-set-color.sh"))
    if cfg.get("background", {}).get("widgets", {}).get("clock", {}).get("cookie", {}).get("aiStyling") is True:
        category = STATE / "wallpaper" / "category.txt"
        with category.open("w") as out:
            background(str(HERE.parent / "ai" / "gemini-categorize-wallpaper.sh"), current_wallpaper(), stdout=out)


def prepare_in_background():
    background("ionice", "-c3", sys.executable, str(Path(__file__).resolve()), "--prepare", niceness=19)


def prepare_all():
    CACHE.mkdir(parents=True, exist_ok=True)
    with (CACHE / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        try:
            current = json.loads(STATE_FILE.read_text())
        except (OSError, ValueError):
            current = {}
        keys = [t["key"] for t in themes() if t["key"] not in {b["key"] for b in BUILTIN}]
        mode = current.get("mode") if current.get("mode") in MODES else preferred_mode()
        other = "dark" if mode == "light" else "light"
        first = [(current["theme"], other)] if current.get("theme") in keys else []
        wanted = {".lock", wallpaper_listing().name}
        for key, m in first + [(k, mode) for k in keys] + [(k, other) for k in keys]:
            wanted.add(prepare(key, m).name)
        for path in CACHE.iterdir():
            pid = path.name.split("-")[1] if path.name.startswith(".prep-") else None
            if pid and Path(f"/proc/{pid}").exists():
                continue
            if path.name not in wanted:
                shutil.rmtree(path) if path.is_dir() else path.unlink()
        missing = sorted({n for k in keys for n in wallpaper_names(load(k)) if not (WALLPAPERS / f"{n}.jpg").is_file()})
        if missing:
            subprocess.run([sys.executable, str(THEMES / "make-wallpapers.py"), *missing],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def shell_hold(on):
    try:
        subprocess.run(["qs", "-c", "ii", "ipc", "call", "theme", "hold" if on else "release"], timeout=3,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        pass


def apply(key, wallpaper_step=None, mode=None):
    if key in ALIASES:
        key, mode = ALIASES[key][0], mode or ALIASES[key][1]
    if mode not in MODES:
        mode = preferred_mode()
    if key in {b["key"] for b in BUILTIN}:
        shell_hold(True)
        try:
            apply_wallpaper_colors(mode)
        finally:
            shell_hold(False)
    else:
        apply_theme(key, wallpaper_step, mode)


def apply_wallpaper_colors(mode):
    prev = previous_wallpaper()
    STATE_FILE.unlink(missing_ok=True)
    if prev and is_theme_wallpaper(current_wallpaper()) and not set_wallpaper_path(prev):
        set_wallpaper(prev, mode)
    switchwall("--mode", mode, "--type", "auto", "--color", "clear")


def apply_theme(key, wallpaper_step, mode):
    """Installs the prepared files; no shell hold needed since colors.json is written once, atomically."""
    t = load(key)
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
    entry = prepare(key, mode)
    running = []
    if not SHELL_CONFIG.is_file() or wallpaper_theming().get("enableTerminal") is True:
        install(entry, "terminal")
        running = recolor_terminals()
    wallpaper = theme_wallpaper(names[index]) if names else None
    if wallpaper:
        remember_wallpaper()
    moved = bool(wallpaper) and Path(current_wallpaper() or "/").resolve() != wallpaper.resolve()
    if not (moved and set_wallpaper_path(wallpaper, accent=t["seed"])):
        if moved:
            set_wallpaper(wallpaper, mode)
        edit_shell_config(accent=t["seed"])
    install(entry, "files")
    install(entry, "colors")
    write_atomic(STATE_FILE, json.dumps({"theme": key, "mode": mode, "decor": t.get("decor", ""),
                                         "wallpaper_index": index, "wallpapers": len(names),
                                         "background": current_background()}) + "\n")
    scheme = "prefer-dark" if mode == "dark" else "prefer-light"
    gtk = "adw-gtk3-dark" if mode == "dark" else "adw-gtk3"
    running += [subprocess.Popen(["gsettings", "set", "org.gnome.desktop.interface", k, v])
                for k, v in (("color-scheme", scheme), ("gtk-theme", gtk))]
    missing = [n for n in names if not (WALLPAPERS / f"{n}.jpg").is_file()]
    if missing:
        subprocess.Popen([sys.executable, str(THEMES / "make-wallpapers.py"), *missing], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    post_process()
    for p in running:
        p.wait()


def main():
    args = sys.argv[1:]
    if args == ["--list"]:
        print(json.dumps(themes()))
        prepare_in_background()
        return 0
    if args == ["--prepare"]:
        prepare_all()
        return 0
    usage = "usage: apply-theme.py --list | --prepare | THEME [--mode light|dark] [--next-wallpaper | --prev-wallpaper | --wallpaper N]"
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
    prepare_in_background()
    return 0


if __name__ == "__main__":
    sys.exit(main())
