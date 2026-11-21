import importlib.util
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

SETTINGS = Path.home() / '.local/state/quickshell/user/terminal-toys.json'
SCRIPT = Path(os.environ.get('TERMINAL_TOYS_SCRIPT', Path.home() / '.config/quickshell/ii/scripts/terminal-toys.py'))
AGENT_STATE = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'claude-state'
CLAUDE_SESSIONS = Path.home() / '.claude/sessions'
AGENTS = {'claude': 'claude', 'pi': 'pi', 'codex': 'codex', 'codex.js': 'codex'}
SESSION_STATUS = {'idle': 'done', 'shell': 'done', 'busy': 'running', 'waiting': 'waiting'}
DEFAULTS = {'scene': 'cat', 'startup': True, 'ambient': True, 'commands': True, 'sounds': True, 'size': 6}
PAD = (0, 10, 14, 0)
GREETING, AFTERGLOW, CHECK, LONG = 2, 2, 1, 3
SOUNDS = {'success': 'notification', 'error': 'error', 'waiting': 'notification', 'agentDone': 'agentDone'}
spec = importlib.util.spec_from_file_location('terminal_toys', SCRIPT)
toys = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toys)
entries = {}
preferences = dict(DEFAULTS)
accent = toys.FALLBACK_ACCENT
stamps = {}
checked = 0
players = []
QS = shutil.which('qs')


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
    return f'/terminal-toys/v3/{scene}/{state}/{index}/{size}/{color.lstrip("#")}', data


def warm(scene=None, size=None, color=None):
    for key in [scene] if scene else toys.KEYS:
        for state in toys.STATES:
            for index in range(toys.FRAMES):
                picture(key, state, index, size or scale(), color)


def play(outcome):
    players[:] = [p for p in players if p.poll() is None]
    if not QS or not preferences.get('sounds', True) or len(players) > 4:
        return
    try:
        players.append(subprocess.Popen([QS, '-c', 'ii', 'ipc', 'call', 'themeSounds', 'play', SOUNDS[outcome], '0'],
                                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, start_new_session=True))
    except OSError:
        pass


def agent_of(cmdline):
    for arg in (cmdline or [])[:2]:
        name = AGENTS.get(os.path.basename(arg))
        if name:
            return name
        if 'pi-coding-agent' in arg:
            return 'pi'
        if '@anthropic-ai/claude-code' in arg:
            return 'claude'
        if '@openai/codex' in arg:
            return 'codex'
    return None


def agent_state(window):
    try:
        procs = [p for p in window.child.foreground_processes if agent_of(p.get('cmdline'))]
    except Exception:
        return None
    if not procs:
        return None
    pid = procs[0].get('pid')
    try:
        start = os.stat(f'/proc/{pid}').st_ctime
    except OSError:
        start = None
    found = []
    path = AGENT_STATE / f'{os.getpid()}-{window.id}'
    try:
        mtime = path.stat().st_mtime
        state = path.read_text().strip()
        if state in ('running', 'waiting', 'done') and (start is None or mtime >= start-1):
            found.append((mtime, state))
    except OSError:
        pass
    if agent_of(procs[0].get('cmdline')) == 'claude':
        try:
            data = json.loads((CLAUDE_SESSIONS / f'{pid}.json').read_text())
            if data.get('status') in SESSION_STATUS:
                found.append((float(data.get('updatedAt') or 0)/1000, SESSION_STATUS[data['status']]))
        except (OSError, ValueError, AttributeError, TypeError):
            pass
    return max(found)[1] if found else 'done'


def follow_agent(window, entry, now):
    if now-entry['agent_checked'] < CHECK:
        return
    entry['agent_checked'] = now
    state = agent_state(window)
    previous = entry['agent']
    entry['agent'] = state
    if state == previous or state is None:
        return
    if state == 'running':
        entry['turn'] = now
    elif state == 'done' and previous == 'running':
        entry['agent_done'] = now
        if now-entry['turn'] > LONG:
            play('agentDone')
    elif state == 'waiting' and previous is not None:
        play('waiting')
    if state != 'done':
        entry['agent_since'] = now


def wanted_state(entry, now):
    if preferences['commands'] and entry['agent']:
        agent = entry['agent']
        if agent in ('running', 'waiting'):
            return agent, now-entry['agent_since']
        if now-entry['agent_done'] < AFTERGLOW:
            return 'success', now-entry['agent_done']
        return ('idle', now-entry['born']) if preferences['ambient'] else (None, 0)
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
        if entry['state'] == 'running' or entry['agent']:
            follow_agent(window, entry, now)
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
    now = time.monotonic()
    entries[window.id] = dict(born=now, changed=float('-inf'), started=now, state='idle', logo=None,
                              agent=None, agent_checked=float('-inf'), agent_since=now,
                              agent_done=float('-inf'), turn=now)


def on_cmd_startstop(boss, window, data):
    if window.id not in entries:
        return
    entry = entries[window.id]
    now = time.monotonic()
    if data['is_start']:
        entry['state'] = 'running'
        entry['started'] = now
    else:
        entry['state'] = 'success' if data['exit_status'] == 0 else 'error'
        entry['agent'] = None
        if now-entry['started'] > LONG:
            play(entry['state'])
    entry['changed'] = now


def on_close(boss, window, data):
    entries.pop(window.id, None)
