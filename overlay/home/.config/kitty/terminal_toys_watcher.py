import importlib.util
import json
import os
import time
from pathlib import Path

SETTINGS = Path.home() / '.local/state/quickshell/user/terminal-toys.json'
SCRIPT = Path(os.environ.get('TERMINAL_TOYS_SCRIPT', Path.home() / '.config/quickshell/ii/scripts/terminal-toys.py'))
DEFAULTS = {'scene': 'cat', 'startup': True, 'ambient': True, 'commands': True, 'size': 6}
PAD = (0, 10, 14, 0)
GREETING, AFTERGLOW, CHECK = 2, 2, 1
spec = importlib.util.spec_from_file_location('terminal_toys', SCRIPT)
toys = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toys)
entries = {}
preferences = dict(DEFAULTS)
accent = toys.FALLBACK_ACCENT
stamps = {}
checked = 0


def changed(path):
    try:
        current = path.stat().st_mtime_ns
    except OSError:
        current = None
    if stamps.get(path) == current:
        return False
    stamps[path] = current
    return current is not None


def refresh(now):
    global preferences, accent, checked
    if now-checked < CHECK:
        return
    checked = now
    if changed(SETTINGS):
        try:
            loaded = json.loads(SETTINGS.read_text())
            preferences = dict(DEFAULTS, **loaded) if isinstance(loaded, dict) else dict(DEFAULTS)
        except (OSError, ValueError):
            preferences = dict(DEFAULTS)
        if preferences['scene'] not in toys.KEYS:
            preferences['scene'] = DEFAULTS['scene']
    if changed(toys.THEME):
        accent = toys.theme_accent()


def scale():
    try:
        return max(3, min(10, int(preferences.get('size', 6))))
    except (TypeError, ValueError):
        return 6


def picture(scene, state, index, size=6, color=None):
    color = color or accent
    data = toys.frame_png(scene, state, index, size, color, PAD)
    return f'/terminal-toys/v2/{scene}/{state}/{index}/{size}/{color.lstrip("#")}', data


def warm(scene=None, size=None, color=None):
    for key in [scene] if scene else toys.KEYS:
        for state in toys.STATES:
            for index in range(toys.FRAMES):
                picture(key, state, index, size or scale(), color)


def wanted_state(entry, now):
    if preferences['commands'] and (entry['state'] == 'running' or now-entry['changed'] < AFTERGLOW):
        return entry['state'], now-entry['changed']
    if preferences['startup'] and now-entry['born'] < GREETING:
        return 'success', now-entry['born']
    if preferences['ambient']:
        return 'idle', now-entry['born']
    return None, 0


def tick(boss):
    now = time.monotonic()
    refresh(now)
    for wid, entry in list(entries.items()):
        window = boss.window_id_map.get(wid)
        if window is None:
            del entries[wid]
            continue
        state, elapsed = wanted_state(entry, now)
        if state is None:
            if entry['logo']:
                window.set_logo('')
                entry['logo'] = None
            continue
        if not window.is_visible_in_layout:
            continue
        path, data = picture(preferences['scene'], state, toys.frame_index(elapsed, state), scale())
        if path != entry['logo']:
            window.set_logo(path, 'top-right', .9, data)
            entry['logo'] = path


def is_shell(window):
    return Path(window.child.argv[0]).name.lstrip('-') == 'fish'


def on_load(boss, data):
    from kitty.fast_data_types import add_timer
    for window in boss.all_windows:
        if not is_shell(window):
            continue
        for name in ('on_resize', 'on_cmd_startstop', 'on_close'):
            getattr(window.watchers, name).append(globals()[name])
        on_resize(boss, window, {})
        if window.last_cmd_output_start_time:
            entries[window.id]['state'] = 'running'
    refresh(time.monotonic())
    add_timer(lambda timer: tick(boss), .1, True)


def on_resize(boss, window, data):
    if window.id in entries or not is_shell(window):
        return
    entries[window.id] = dict(born=time.monotonic(), changed=float('-inf'), state='idle', logo=None)


def on_cmd_startstop(boss, window, data):
    if window.id not in entries:
        return
    entry = entries[window.id]
    entry['state'] = 'running' if data['is_start'] else 'success' if data['exit_status'] == 0 else 'error'
    entry['changed'] = time.monotonic()


def on_close(boss, window, data):
    entries.pop(window.id, None)
