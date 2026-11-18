#!/usr/bin/env python3
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import markers  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
HOME = Path.home()
STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", HOME / ".local" / "state")) / "dotfiles"
DATA_DIR = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share")) / "dotfiles"
STATE_FILE = STATE_DIR / "state.json"
END4_URL = "https://github.com/end-4/dots-hyprland.git"
END4_DIR = DATA_DIR / "end-4"
SILENT_URL = "https://github.com/uiriansan/SilentSDDM.git"
SILENT_COMMIT = "0dc4386ef570659537b480f4b226b3b6f2699948"
SILENT_DIR = DATA_DIR / "SilentSDDM"
UNIT_DIR = HOME / ".config" / "systemd" / "user"
NEW_SUFFIX = ".dotfiles-new"
PROTECTED = [
    ".claude", ".claude.json", ".codex", ".agents",
    ".config/environment.d", ".ssh/config", ".ssh/config.d", ".local/share/gnome-shell/extensions",
    ".local/bin/claude", ".local/bin/codex",
]


class Plan:
    def __init__(self, dry_run):
        self.dry_run = dry_run
        self.notes = []

    def say(self, text):
        print(("would: " if self.dry_run else "") + text, flush=True)

    def sudo_ok(self):
        if os.geteuid() == 0 or sys.stdin.isatty():
            return True
        if not hasattr(self, "_sudo_ok"):
            self._sudo_ok = subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0
        return self._sudo_ok

    def note(self, text):
        self.notes.append(text)

    def run(self, cmd, check=True, sudo=False, cwd=None, label=None):
        prefix = []
        if sudo and os.geteuid() != 0:
            if not self.sudo_ok():
                self.note("needs your password, run ./install.sh update in a terminal: " + (label or " ".join(str(c) for c in cmd)))
                return 1
            prefix = ["sudo"] if sys.stdin.isatty() else ["sudo", "-n"]
        cmd = prefix + [str(c) for c in cmd]
        self.say("run " + (label or " ".join(cmd)))
        if self.dry_run:
            return 0
        rc = subprocess.run(cmd, check=False, cwd=cwd).returncode
        if rc != 0 and check:
            raise subprocess.CalledProcessError(rc, cmd)
        if rc != 0:
            self.note(f"failed (exit {rc}): " + (label or " ".join(cmd)))
        return rc


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    try:
        return sha(Path(path).read_bytes())
    except (FileNotFoundError, IsADirectoryError):
        return None


def load_manifest():
    return tomllib.loads((REPO / "modules.toml").read_text())


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except FileNotFoundError:
        return {"modules": None, "end4_commit": None, "files": {}, "system_files": {}}


def save_state(state, plan):
    if plan.dry_run:
        return
    try:
        if json.loads(STATE_FILE.read_text()) == state:
            return
    except (FileNotFoundError, ValueError):
        pass
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(STATE_FILE)


def os_release():
    info = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                info[k] = v.strip('"')
    except FileNotFoundError:
        pass
    ids = [info.get("ID", "")] + info.get("ID_LIKE", "").split()
    if "arch" in ids:
        return "arch", info.get("VERSION_ID", "")
    if "ubuntu" in ids or "debian" in ids:
        return "ubuntu", info.get("VERSION_ID", "")
    return info.get("ID", "unknown"), info.get("VERSION_ID", "")


def desktop_supported(distro, version):
    if distro == "arch":
        return True
    if distro == "ubuntu":
        try:
            return tuple(int(x) for x in version.split(".")[:2]) >= (26, 4)
        except ValueError:
            return False
    return False


def protected(dest):
    try:
        rel = Path(dest).relative_to(HOME)
    except ValueError:
        return False
    return any(str(rel) == p or str(rel).startswith(p + "/") for p in PROTECTED)


def choose_modules(manifest, state, args, distro, version):
    modules = manifest["module"]
    retired_notes = []
    if args.all:
        chosen = {n for n, m in modules.items() if not m.get("retired")}
    elif args.modules is not None:
        chosen = {m for m in args.modules.split(",") if m}
    elif state.get("modules") is not None:
        chosen = set(state["modules"])
        gone = {n for n in chosen if n not in modules or modules[n].get("retired")}
        chosen -= gone
        retired_notes = [f"{n} (no longer offered: its files and units are removed)" for n in sorted(gone)]
    else:
        chosen = {name for name, meta in modules.items() if meta.get("default")}
    chosen |= {m for m in (args.add or "").split(",") if m}
    chosen -= {m for m in (args.remove or "").split(",") if m}
    chosen.add("base")
    unknown = chosen - set(modules)
    if unknown:
        raise SystemExit("unknown modules: " + ", ".join(sorted(unknown)))
    retired = {n for n in chosen if modules[n].get("retired")}
    if retired:
        raise SystemExit("modules no longer offered: " + ", ".join(sorted(retired)))
    dropped = list(retired_notes)
    for name in sorted(chosen):
        meta = modules[name]
        if meta.get("os") and distro not in meta["os"]:
            dropped.append(f"{name} (only on {', '.join(meta['os'])})")
        elif meta.get("desktop") and not desktop_supported(distro, version):
            dropped.append(f"{name} (needs the desktop: Arch, or Ubuntu 26.04 or newer)")
        elif meta.get("needs_command") and shutil.which(meta["needs_command"]) is None:
            dropped.append(f"{name} (needs {meta['needs_command']}, which is not installed)")
    for d in dropped:
        chosen.discard(d.split(" ")[0])
    return chosen, dropped


def group_of(meta):
    if meta.get("sudo"):
        return "System (asks for your password)"
    if meta.get("desktop"):
        return "Desktop"
    return "Terminal"


def pick_modules(manifest, preselected, distro, version):
    import curses
    modules = manifest["module"]
    order = ["Desktop", "Terminal", "System (asks for your password)"]
    rows = []
    for g in order:
        names = [n for n, m in modules.items() if n != "base" and not m.get("retired") and group_of(m) == g]
        if names:
            rows.append(("header", g))
            rows.extend(("module", n) for n in names)

    def available(name):
        meta = modules[name]
        if meta.get("os") and distro not in meta["os"]:
            return False
        if meta.get("desktop") and not desktop_supported(distro, version):
            return False
        return True

    chosen = {n for n in preselected if n != "base" and available(n)}
    defaults = {n for n, m in modules.items() if m.get("default") and n != "base" and available(n)}
    rows.append(("install", ""))
    items = [i for i, r in enumerate(rows) if r[0] in ("module", "install")]
    help_text = "Space/Enter: tick, i: install, a: all, n: none, d: defaults, q: quit"

    def details(name, width):
        meta = modules[name]
        text = meta["description"]
        if not available(name):
            text = "Not available on this system. " + text
        elif meta.get("default"):
            text += " (on by default)"
        if meta.get("sudo") or group_of(meta).startswith("System"):
            text += " Changes system files: asks for your password."
        return textwrap.wrap(f"{name}: {text}", max(20, width - 1))

    def ui(scr):
        curses.curs_set(0)
        curses.use_default_colors()
        pos, top = 0, 0
        while True:
            scr.erase()
            h, w = scr.getmaxyx()
            scr.addnstr(0, 0, "Choose modules", w - 1, curses.A_BOLD)
            for i, line in enumerate(textwrap.wrap(help_text, max(20, w - 1))[:2]):
                scr.addnstr(1 + i, 0, line, w - 1, curses.A_DIM)
            cur = items[pos]
            kind_cur, name = rows[cur]
            info = details(name, w) if kind_cur == "module" else textwrap.wrap(
                f"Installs end-4's base and the {len(chosen)} ticked modules.", max(20, w - 1))
            info = info[:max(1, h // 3)]
            first = 4
            body = h - first - len(info) - 1
            if body < 1:
                body = 1
            if cur < top:
                top = cur
            if cur >= top + body:
                top = cur - body + 1
            if top > 0 and rows[top - 1][0] == "header" and cur - (top - 1) < body:
                top -= 1
            for y, idx in enumerate(range(top, min(len(rows), top + body))):
                kind, value = rows[idx]
                if kind == "header":
                    scr.addnstr(first + y, 0, value, w - 1, curses.A_UNDERLINE)
                    continue
                if kind == "install":
                    line = f"  [ Install {len(chosen)} modules ]"
                    scr.addnstr(first + y, 0, line, w - 1, curses.A_BOLD | (curses.A_REVERSE if idx == cur else 0))
                    continue
                ok = available(value)
                box = "[x]" if value in chosen else ("[-]" if not ok else "[ ]")
                mark = "  (default)" if modules[value].get("default") and ok else ""
                attr = curses.A_REVERSE if idx == cur else (curses.A_DIM if not ok else 0)
                scr.addnstr(first + y, 0, f"  {box} {value}{mark}", w - 1, attr)
            for i, line in enumerate(info):
                scr.addnstr(h - len(info) + i, 0, line, w - 1)
            key = scr.getch()
            if key in (curses.KEY_UP, ord("k")):
                pos = max(0, pos - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                pos = min(len(items) - 1, pos + 1)
            elif key in (ord(" "), 10, 13, curses.KEY_ENTER):
                if kind_cur == "install":
                    if key != ord(" "):
                        return True
                elif available(name):
                    chosen.symmetric_difference_update({name})
            elif key == ord("i"):
                return True
            elif key == ord("a"):
                chosen.update(n for n in modules if n != "base" and not modules[n].get("retired") and available(n))
            elif key == ord("n"):
                chosen.clear()
            elif key == ord("d"):
                chosen.clear()
                chosen.update(defaults)
            elif key in (ord("q"), 27):
                return False

    if not curses.wrapper(ui):
        return None
    return chosen | {"base"}


def end4_commit(manifest):
    return manifest["end4_commit"]


def git_head(path):
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def fetch_end4(commit, plan):
    if git_head(END4_DIR) == commit:
        return
    if not (END4_DIR / ".git").exists():
        plan.run(["git", "clone", "--filter=blob:none", END4_URL, END4_DIR])
    plan.run(["git", "-C", END4_DIR, "fetch", "-q", "origin", commit])
    plan.run(["git", "-C", END4_DIR, "checkout", "-q", "--detach", commit])
    plan.run(["git", "-C", END4_DIR, "submodule", "update", "--init", "--recursive", "-q"])


def run_end4_setup(distro, plan, skip_deps, unattended):
    if distro == "ubuntu":
        if not skip_deps:
            plan.run([REPO / "distro" / "ubuntu" / "deps.sh"])
        plan.say(f"write {END4_DIR / 'os-release'} (end-4 then takes its Arch path, without its Arch packages)")
        if not plan.dry_run:
            (END4_DIR / "os-release").write_text("ID=ubuntu\nID_LIKE=arch\n")
    if distro == "arch" and not skip_deps and shutil.which("qs") is None:
        plan.run(["pacman", "-S", "--needed", "--noconfirm", "quickshell"], sudo=True)
    flags = ["install", "--skip-sysupdate", "--skip-plasmaintg", "--skip-allgreeting"]
    if distro != "arch" or skip_deps:
        flags.append("--skip-alldeps")
    if unattended:
        flags.append("-f")
    cmd = [str(END4_DIR / "setup"), *flags]
    plan.say("run " + " ".join(cmd) + (" (failed steps answered with ignore)" if unattended else ""))
    if plan.dry_run:
        return
    if unattended:
        yes = subprocess.Popen(["yes", "i"], stdout=subprocess.PIPE)
        try:
            subprocess.run(cmd, cwd=END4_DIR, stdin=yes.stdout, check=True)
        finally:
            yes.kill()
    else:
        subprocess.run(cmd, cwd=END4_DIR, check=True)
    if distro == "arch" and shutil.which("qs") is None:
        plan.run(["pacman", "-S", "--needed", "--noconfirm", "quickshell"], sudo=True)
    if plan.dry_run:
        return
    missing = [b for b in ("Hyprland", "qs") if shutil.which(b) is None]
    if missing:
        raise SystemExit("end-4's setup finished but " + " and ".join(missing) + " are not installed; "
                         "scroll up for the step that failed, fix it, then run ./install.sh install --reinstall-end4")


def install_packages(manifest, chosen, distro, plan):
    pkgs = sorted({p for m in chosen for p in manifest["module"][m].get("packages", {}).get(distro, [])})
    if not pkgs:
        return
    if distro == "arch":
        missing = [p for p in pkgs if subprocess.run(["pacman", "-Q", p], capture_output=True).returncode != 0]
        if missing:
            plan.run(["pacman", "-S", "--needed", "--noconfirm", *missing], sudo=True)
    elif distro == "ubuntu":
        missing = [p for p in pkgs if subprocess.run(["dpkg", "-s", p], capture_output=True).returncode != 0]
        if missing:
            plan.run(["apt-get", "update", "-q"], sudo=True)
            plan.run(["env", "DEBIAN_FRONTEND=noninteractive", "apt-get", "install", "-y", *missing], sudo=True)


def target_of(dest):
    if dest.startswith("home/"):
        return HOME / dest[len("home/"):], False
    if dest.startswith("root/"):
        return Path("/") / dest[len("root/"):], True
    raise SystemExit(f"bad destination {dest}")


def render_bytes(raw, chosen, dest):
    try:
        return markers.render(raw.decode(), chosen, dest).encode()
    except UnicodeDecodeError:
        return raw


def published_shas(dest, chosen):
    """Hashes of every version of dest this repo ever committed: a target equal to one of them holds no change of the user's."""
    if not (REPO / ".git").exists():
        return set()
    path = f"overlay/{dest}"
    revs = subprocess.run(["git", "-C", str(REPO), "log", "--format=%H", "--", path],
                          capture_output=True, text=True, check=True).stdout.split()
    shas = set()
    for rev in revs:
        shown = subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{path}"], capture_output=True)
        if shown.returncode == 0:
            shas.add(sha(render_bytes(shown.stdout, chosen, dest)))
    return shas


def end4_original(target):
    try:
        rel = target.relative_to(HOME)
    except ValueError:
        return None
    candidate = END4_DIR / "dots" / rel
    return candidate if candidate.is_file() else None


def write_user_file(target, data, mode, plan):
    plan.say(f"write {target}")
    if plan.dry_run:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        target.unlink()
    tmp = target.with_name(target.name + ".dotfiles-tmp")
    tmp.write_bytes(data)
    tmp.chmod(mode)
    tmp.replace(target)


def write_system_file(target, data, mode, plan):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(data)
        tmp = f.name
    try:
        return plan.run(["install", "-D", "-m", oct(mode)[2:], tmp, target], sudo=True, check=False,
                        label=f"update {target}") == 0
    finally:
        os.unlink(tmp)


def apply_files(manifest, chosen, state, plan):
    files = manifest["files"]
    recorded = state.setdefault("files", {})
    recorded_sys = state.setdefault("system_files", {})
    backup_root = STATE_DIR / "backup" / datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    wanted = {}
    for dest, module in files.items():
        if module not in chosen:
            continue
        src = REPO / "overlay" / dest
        data = render_bytes(src.read_bytes(), chosen, dest)
        mode = 0o755 if os.access(src, os.X_OK) else 0o644
        wanted[dest] = (data, mode)
    for dest, (data, mode) in sorted(wanted.items()):
        target, system = target_of(dest)
        key = str(target)
        if protected(target):
            plan.note(f"skipped {target}: agent and ssh config is left to the tools that manage it")
            continue
        new = sha(data)
        if system:
            if file_sha(target) == new:
                recorded_sys[key] = new
                continue
            if write_system_file(target, data, 0o644 if str(target).startswith("/etc/") else mode, plan):
                recorded_sys[key] = new
                plan.system_changed = True
            continue
        current = file_sha(target) if not target.is_symlink() else None
        before = recorded.get(key)
        side = target.with_name(target.name + NEW_SUFFIX)
        if current == new:
            recorded[key] = new
            if side.exists() and not plan.dry_run:
                side.unlink()
            continue
        if current is None or current == before or current in published_shas(dest, chosen):
            write_user_file(target, data, mode, plan)
            recorded[key] = new
            if side.exists() and not plan.dry_run:
                side.unlink()
            continue
        if before is None:
            original = end4_original(target)
            if original is not None and file_sha(original) == current:
                write_user_file(target, data, mode, plan)
                recorded[key] = new
                continue
            plan.say(f"back up {target} to {backup_root}")
            if not plan.dry_run:
                b = backup_root / target.relative_to(HOME)
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, b)
            write_user_file(target, data, mode, plan)
            recorded[key] = new
            plan.note(f"replaced {target}; your previous version is in {backup_root}")
            continue
        if file_sha(side) == new:
            continue
        write_user_file(side, data, mode, plan)
        plan.note(f"kept your changes in {target}; the new version is next to it as {side.name}")
    wanted_targets = {str(target_of(d)[0]) for d in wanted}
    for key in sorted(set(recorded) - wanted_targets):
        target = Path(key)
        current = file_sha(target)
        if current is None:
            del recorded[key]
            continue
        if current != recorded[key]:
            plan.note(f"left {target}: its module is no longer chosen but you changed it")
            del recorded[key]
            continue
        original = end4_original(target)
        side = target.with_name(target.name + NEW_SUFFIX)
        if original is not None:
            plan.say(f"restore end-4's {target}")
            if not plan.dry_run:
                shutil.copy2(original, target)
        else:
            plan.say(f"remove {target}")
            if not plan.dry_run:
                target.unlink()
                prune_empty(target.parent)
        if side.exists():
            plan.say(f"remove {side}")
            if not plan.dry_run:
                side.unlink()
        del recorded[key]
    for key in sorted(set(recorded_sys) - wanted_targets):
        target = Path(key)
        if file_sha(target) == recorded_sys[key]:
            if plan.run(["rm", "-f", target], sudo=True, check=False) == 0:
                parent, keep = target.parent, {Path("/etc"), Path("/etc/systemd"), Path("/etc/systemd/system"), Path("/usr/share/sddm/themes")}
                while parent not in keep and parent != parent.parent:
                    if not parent.is_dir() or any(parent.iterdir()):
                        break
                    plan.run(["rmdir", parent], sudo=True, check=False)
                    parent = parent.parent
            else:
                continue
        else:
            plan.note(f"left {target}: its module is no longer chosen but it was changed")
        del recorded_sys[key]


def prune_empty(folder):
    stop = {HOME, HOME / ".config", HOME / ".local", HOME / ".local" / "share"}
    while folder not in stop and folder != folder.parent:
        try:
            folder.rmdir()
        except OSError:
            return
        folder = folder.parent


def apply_removals(manifest, chosen, plan):
    for name in sorted(chosen):
        for rel in manifest["module"][name].get("remove", []):
            target = HOME / rel
            if target.is_dir() and not target.is_symlink():
                plan.say(f"remove {target}/")
                if not plan.dry_run:
                    shutil.rmtree(target)
            elif target.exists() or target.is_symlink():
                plan.say(f"remove {target}")
                if not plan.dry_run:
                    target.unlink()


SHELL_CONFIG = HOME / ".config" / "illogical-impulse" / "config.json"
MISSING = object()


def config_get(cfg, key):
    node = cfg
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return MISSING
        node = node[part]
    return node


def config_set(cfg, key, value):
    parts = key.split(".")
    node = cfg
    for part in parts[:-1]:
        if not isinstance(node.get(part), dict):
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value


def apply_settings(manifest, chosen, state, plan):
    recorded = state.setdefault("settings", {})
    wanted = {}
    for name in sorted(chosen):
        for key, pair in manifest["module"][name].get("settings", {}).items():
            if not isinstance(pair, list) or len(pair) != 2:
                plan.note(f"skipped setting {key} of {name}: not an [end-4 default, value] pair")
                continue
            wanted[key] = {"default": pair[0], "value": pair[1]}
    if not wanted and not recorded:
        return
    try:
        cfg = json.loads(SHELL_CONFIG.read_text()) if SHELL_CONFIG.exists() else {}
    except ValueError:
        plan.note(f"skipped settings: {SHELL_CONFIG} is not valid JSON")
        return
    changed = False
    for key, want in sorted(wanted.items()):
        current = config_get(cfg, key)
        if current == want["value"]:
            recorded[key] = want
            continue
        if recorded.get(key, {}).get("yours"):
            continue
        before = recorded.get(key, {}).get("value", MISSING)
        ours = current is MISSING or (current == before if before is not MISSING else current == want["default"])
        if ours:
            plan.say(f"set {key} = {json.dumps(want['value'])}")
            config_set(cfg, key, want["value"])
            recorded[key] = want
            changed = True
            continue
        plan.note(f"kept your {key} = {json.dumps(current)} (this config sets {json.dumps(want['value'])})")
        recorded[key] = dict(want, yours=True)
    for key in sorted(set(recorded) - set(wanted)):
        old = recorded.pop(key)
        if not old.get("yours") and config_get(cfg, key) == old["value"]:
            plan.say(f"set {key} back to end-4's {json.dumps(old['default'])}")
            config_set(cfg, key, old["default"])
            changed = True
    if changed and not plan.dry_run:
        SHELL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        tmp = SHELL_CONFIG.with_name(SHELL_CONFIG.name + ".tmp")
        tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(SHELL_CONFIG)


AGENT_SCRIPTS = HOME / ".config" / "quickshell" / "ii" / "scripts" / "claude"
AGENT_HOOKS = {
    HOME / ".claude" / "settings.json": {"SubagentStart": "subagents.py", "SubagentStop": "subagents.py"},
    HOME / ".codex" / "hooks.json": {"UserPromptSubmit": "agent-state.sh running", "Stop": "agent-state.sh done"},
}


def apply_agent_hooks(chosen, previous, plan):
    """Adds or removes exactly the agent-hooks entries, leaving every other hook and setting as it is."""
    on = "agent-hooks" in chosen
    if not on and "agent-hooks" not in (previous or []):
        return
    for path, events in AGENT_HOOKS.items():
        if not path.parent.is_dir():
            continue
        try:
            cfg = json.loads(path.read_text()) if path.exists() else {}
        except ValueError:
            plan.note(f"agent-hooks: skipped {path}, it is not valid JSON")
            continue
        hooks = cfg.get("hooks", {})
        changed = False
        for event, script in events.items():
            command = f"{AGENT_SCRIPTS}/{script}"
            groups = hooks.get(event, [])
            present = any(h.get("command") == command for g in groups for h in g.get("hooks", []))
            if on and not present:
                hooks[event] = groups + [{"hooks": [{"type": "command", "command": command}]}]
                changed = True
            elif not on and present:
                kept = [dict(g, hooks=[h for h in g["hooks"] if h.get("command") != command]) for g in groups]
                kept = [g for g in kept if g["hooks"]]
                if kept:
                    hooks[event] = kept
                else:
                    del hooks[event]
                changed = True
        if not changed:
            continue
        plan.say(("add" if on else "remove") + f" the bar's agent hooks in {path}")
        if on and path.parent.name == ".codex":
            plan.note(f"agent-hooks: in Codex, open /hooks and trust the new hooks of {path}; Codex skips them until then")
        if plan.dry_run:
            continue
        if hooks:
            cfg["hooks"] = hooks
        else:
            cfg.pop("hooks", None)
        real = path.resolve()
        tmp = real.with_name(real.name + ".dotfiles-tmp")
        tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
        if real.exists():
            shutil.copymode(real, tmp)
        tmp.replace(real)


def user_bus():
    if shutil.which("systemctl") is None:
        return False
    return subprocess.run(["systemctl", "--user", "show-environment"], capture_output=True).returncode == 0


def apply_units(manifest, chosen, previous, plan):
    modules = manifest["module"]
    bus = user_bus()
    for name in sorted(chosen):
        meta = modules[name]
        for unit in meta.get("user_units", []):
            link = UNIT_DIR / unit
            source = HOME / ".config/hypr/custom/systemd" / unit
            if link.is_symlink() and Path(os.readlink(link)) == source:
                continue
            plan.say(f"link {link} -> {source}")
            if not plan.dry_run:
                UNIT_DIR.mkdir(parents=True, exist_ok=True)
                if link.is_symlink() or link.exists():
                    link.unlink()
                link.symlink_to(source)
        units = meta.get("enable", []) + meta.get("enable_system_user_units", [])
        if units:
            if bus:
                todo = [u for u in units if subprocess.run(["systemctl", "--user", "is-enabled", "-q", u]).returncode != 0]
                if todo:
                    plan.run(["systemctl", "--user", "daemon-reload"], check=False)
                for unit in todo:
                    plan.run(["systemctl", "--user", "enable", "--now", unit], check=False)
            else:
                plan.note(f"{name}: no user session bus; enable later with: systemctl --user enable --now {' '.join(units)}")
        for unit in meta.get("system_enable", []):
            if shutil.which("systemctl") is None:
                plan.note(f"{name}: no systemd; {unit} not enabled")
                continue
            if getattr(plan, "system_changed", False) and not getattr(plan, "reloaded", False):
                plan.run(["systemctl", "daemon-reload"], sudo=True, check=False)
                plan.reloaded = True
            if subprocess.run(["systemctl", "is-enabled", "-q", unit]).returncode != 0:
                plan.run(["systemctl", "enable", "--now", unit], sudo=True, check=False)
    for name in sorted(set(previous or []) - chosen):
        meta = modules.get(name, {})
        for unit in meta.get("enable", []):
            if bus:
                plan.run(["systemctl", "--user", "disable", "--now", unit], check=False)
        for unit in meta.get("user_units", []):
            link = UNIT_DIR / unit
            if link.is_symlink():
                plan.say(f"remove {link}")
                if not plan.dry_run:
                    link.unlink()
                    prune_empty(UNIT_DIR)
        for unit in meta.get("system_enable", []):
            if shutil.which("systemctl"):
                plan.run(["systemctl", "disable", "--now", unit], sudo=True, check=False)


def apply_sddm(chosen, previous, plan):
    if "sddm-theme" not in chosen:
        if "sddm-theme" in (previous or []):
            theme = Path("/usr/share/sddm/themes/silent")
            if theme.exists():
                plan.run(["rm", "-rf", theme], sudo=True, check=False)
            if SILENT_DIR.exists() and not plan.dry_run:
                shutil.rmtree(SILENT_DIR)
            (STATE_DIR / "sddm-theme.commit").unlink(missing_ok=True)
            plan.note("sddm-theme removed; its fonts stay in /usr/share/fonts and SDDM falls back to its default theme")
        return
    theme = Path("/usr/share/sddm/themes/silent")
    stamp = STATE_DIR / "sddm-theme.commit"
    if git_head(SILENT_DIR) == SILENT_COMMIT and (theme / "Main.qml").exists() and stamp.exists() and stamp.read_text().strip() == SILENT_COMMIT:
        return
    if not (SILENT_DIR / ".git").exists():
        plan.run(["git", "clone", "--filter=blob:none", SILENT_URL, SILENT_DIR])
    plan.run(["git", "-C", SILENT_DIR, "fetch", "-q", "origin", SILENT_COMMIT])
    plan.run(["git", "-C", SILENT_DIR, "checkout", "-q", "--detach", SILENT_COMMIT])
    plan.run(["mkdir", "-p", theme], sudo=True)
    plan.run(["rsync", "-a", "--exclude", ".git", "--exclude", "configs/default.conf", f"{SILENT_DIR}/", f"{theme}/"], sudo=True)
    plan.run(["rsync", "-a", f"{SILENT_DIR}/fonts/", "/usr/share/fonts/"], sudo=True)
    if not plan.dry_run:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        stamp.write_text(SILENT_COMMIT + "\n")


def apply_multi_user(chosen, args, plan):
    if "multi-user" not in chosen or not args.group:
        if "multi-user" in chosen:
            plan.note("multi-user: run once with --group NAME (and every account in that group) to share this checkout")
        return
    group = args.group
    if subprocess.run(["getent", "group", group], capture_output=True).returncode != 0:
        plan.run(["groupadd", group], sudo=True)
    user = os.environ.get("USER") or ""
    plan.run(["usermod", "-aG", group, user], sudo=True)
    plan.run(["chgrp", "-R", group, REPO], sudo=True)
    plan.run(["chmod", "-R", "g+rwX", REPO], sudo=True)
    plan.run(["find", REPO, "-type", "d", "-exec", "chmod", "g+s", "{}", "+"], sudo=True)
    if shutil.which("setfacl"):
        plan.run(["setfacl", "-R", "-d", "-m", f"g:{group}:rwX", REPO], sudo=True)
    if (REPO / ".git").exists():
        plan.run(["git", "-C", REPO, "config", "core.sharedRepository", "group"])
    plan.note(f"multi-user: add each other account with `sudo usermod -aG {group} NAME`, then that account runs {REPO}/install.sh")


def cmd_install(args):
    manifest = load_manifest()
    state = load_state()
    distro, version = os_release()
    if distro not in ("arch", "ubuntu"):
        raise SystemExit(f"unsupported system: {distro} (Arch and Ubuntu are supported)")
    plan = Plan(args.dry_run)
    chosen, dropped = choose_modules(manifest, state, args, distro, version)
    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not args.yes
    if interactive and args.modules is None and not args.all and not args.add and not args.remove:
        picked = pick_modules(manifest, chosen, distro, version)
        if picked is None:
            print("nothing changed")
            return 1
        chosen = picked
        args.picked = True
    for d in dropped:
        plan.note(f"left out {d}")
    print(f"system: {distro} {version}")
    print("modules: " + ", ".join(sorted(chosen)))
    if not args.yes and not getattr(args, "picked", False) and not args.dry_run and sys.stdin.isatty():
        if input("continue? [y/N] ").strip().lower() not in ("y", "yes"):
            return 1
    desktop = desktop_supported(distro, version)
    commit = end4_commit(manifest)
    if desktop and not args.skip_end4:
        fetch_end4(commit, plan)
        if state.get("end4_commit") != commit or args.reinstall_end4:
            run_end4_setup(distro, plan, args.skip_deps, args.yes or not sys.stdin.isatty())
            state["end4_commit"] = commit
    if not args.skip_deps:
        install_packages(manifest, chosen, distro, plan)
    previous = state.get("modules")
    apply_removals(manifest, chosen, plan)
    apply_files(manifest, chosen, state, plan)
    apply_settings(manifest, chosen, state, plan)
    apply_agent_hooks(chosen, previous, plan)
    apply_units(manifest, chosen, previous, plan)
    apply_sddm(chosen, previous, plan)
    apply_multi_user(chosen, args, plan)
    state["modules"] = sorted(chosen)
    save_state(state, plan)
    for n in plan.notes:
        print("note: " + n)
    print("dry run, nothing changed" if plan.dry_run else "done")
    return 0


def cmd_update(args):
    if (REPO / ".git").exists():
        cmd = ["git", "-C", str(REPO), "pull", "--ff-only", "-q"]
        print(("would: run " if args.dry_run else "run ") + " ".join(cmd))
        if not args.dry_run:
            subprocess.run(cmd, check=True)
            os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve()), "install", "--yes",
                                      *(["--skip-deps"] if args.skip_deps else [])])
    args.modules = args.add = args.remove = None
    args.all = False
    args.yes = True
    return cmd_install(args)


def cmd_list(args):
    manifest = load_manifest()
    state = load_state()
    installed = set(state.get("modules") or [])
    for name, meta in manifest["module"].items():
        if name == "base" or meta.get("retired"):
            continue
        mark = "*" if name in installed else " "
        flags = []
        if meta.get("default"):
            flags.append("default")
        if meta.get("sudo"):
            flags.append("sudo")
        if meta.get("os"):
            flags.append("/".join(meta["os"]) + " only")
        print(f"{mark} {name:22} {meta['description']}" + (f"  [{', '.join(flags)}]" if flags else ""))
    return 0


def cmd_status(args):
    state = load_state()
    if state.get("modules") is None:
        print("not installed yet")
        return 0
    print("modules: " + ", ".join(state["modules"]))
    print("end-4: " + str(state.get("end4_commit")))
    dests = {str(target_of(d)[0]): d for d in load_manifest()["files"]}
    chosen = set(state["modules"])
    changed = [k for k, v in state.get("files", {}).items()
               if file_sha(k) not in (v, None) and file_sha(k) not in published_shas(dests.get(k, ""), chosen)]
    pending = [k for k in state.get("files", {}) if Path(k + NEW_SUFFIX).exists() and file_sha(k + NEW_SUFFIX) != file_sha(k)]
    for k in changed:
        print("changed by you: " + k)
    for k in pending:
        print("new version waiting: " + k + NEW_SUFFIX)
    timer = UNIT_DIR / "dotfiles-update.timer"
    print("automatic updates: " + ("on" if timer.exists() else "off"))
    return 0


def cmd_timer(args):
    plan = Plan(args.dry_run)
    service = UNIT_DIR / "dotfiles-update.service"
    timer = UNIT_DIR / "dotfiles-update.timer"
    if args.state == "on":
        plan.say(f"write {service} and {timer}")
        if not plan.dry_run:
            UNIT_DIR.mkdir(parents=True, exist_ok=True)
            service.write_text("[Unit]\nDescription=Update the dotfiles\n\n[Service]\nType=oneshot\n"
                               f"ExecStart={REPO}/install.sh update --skip-deps\n")
            timer.write_text("[Unit]\nDescription=Update the dotfiles daily\n\n[Timer]\nOnCalendar=daily\n"
                             "RandomizedDelaySec=1h\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n")
        plan.run(["systemctl", "--user", "daemon-reload"], check=False)
        plan.run(["systemctl", "--user", "enable", "--now", "dotfiles-update.timer"], check=False)
    else:
        plan.run(["systemctl", "--user", "disable", "--now", "dotfiles-update.timer"], check=False)
        for f in (service, timer):
            if f.exists():
                plan.say(f"remove {f}")
                if not plan.dry_run:
                    f.unlink()
        plan.run(["systemctl", "--user", "daemon-reload"], check=False)
    return 0


def main():
    ap = argparse.ArgumentParser(prog="install.sh", description="Modular dotfiles on top of end-4's dots-hyprland")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("install", "update"):
        p = sub.add_parser(name)
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--skip-deps", action="store_true")
        p.add_argument("--skip-end4", action="store_true")
        p.add_argument("--reinstall-end4", action="store_true")
        p.add_argument("--group")
        if name == "install":
            p.add_argument("--modules")
            p.add_argument("--add")
            p.add_argument("--remove")
            p.add_argument("--all", action="store_true")
            p.add_argument("--yes", "-y", action="store_true")
    sub.add_parser("list")
    sub.add_parser("status")
    t = sub.add_parser("timer")
    t.add_argument("state", choices=["on", "off"])
    t.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.cmd in (None, "install"):
        if args.cmd is None:
            args = ap.parse_args(["install", *sys.argv[1:]])
        return cmd_install(args)
    return {"update": cmd_update, "list": cmd_list, "status": cmd_status, "timer": cmd_timer}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
