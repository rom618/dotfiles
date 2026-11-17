import hashlib
import importlib.util
import json
import time
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SETTINGS = Path.home() / '.local/state/quickshell/user/terminal-toys.json'
SCRIPT = Path.home() / '.config/quickshell/ii/scripts/terminal-toys.py'
spec = importlib.util.spec_from_file_location('terminal_toys', SCRIPT)
toys = importlib.util.module_from_spec(spec)
spec.loader.exec_module(toys)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 12)
entries = {}
preferences = {}
stamp = None


@lru_cache(maxsize=512)
def glyph(ch, color):
    image = Image.new('RGBA', (8, 14))
    ImageDraw.Draw(image).text((0, 0), ch, font=font, fill=toys.COLORS[color],
                               stroke_width=1, stroke_fill='#0d1220')
    return image


@lru_cache(maxsize=640)
def picture(scene, state, step):
    canvas = toys.frame(scene, step/10, state)
    rows = [row[24:56] for row in canvas.cells[4:16]]
    image = Image.new('RGBA', (len(rows[0])*8, len(rows)*14))
    for y, row in enumerate(rows):
        for x, (ch, color) in enumerate(row):
            if ch != ' ':
                image.alpha_composite(glyph(ch, color), (x*8, y*14))
    image = image.crop(image.getbbox())
    image.thumbnail((180, 80), Image.Resampling.LANCZOS)
    padded = Image.new('RGBA', (image.width+16, image.height+12))
    padded.paste(image, (0, 12))
    output = BytesIO()
    padded.save(output, format='PNG', compress_level=1)
    data = output.getvalue()
    return '/terminal-toys/'+hashlib.sha256(data).hexdigest(), data


def tick(boss):
    global preferences, stamp
    current = SETTINGS.stat().st_mtime_ns
    if current != stamp:
        preferences = json.loads(SETTINGS.read_text())
        stamp = current
    now = time.monotonic()
    for wid, entry in list(entries.items()):
        window = boss.window_id_map.get(wid)
        if window is None:
            del entries[wid]
            continue
        startup = preferences['startup'] and now-entry['born'] < 2.5
        command = preferences['commands'] and (entry['state'] == 'running' or now-entry['changed'] < 2)
        wanted = preferences['ambient'] or startup or command
        if not wanted:
            if entry['shown']:
                window.set_logo('')
                entry['shown'] = False
            continue
        if not window.is_visible_in_layout:
            continue
        state = entry['state'] if command else 'running' if startup else 'idle'
        step = int((now-entry['born'])*10)%160
        path, data = picture(preferences['scene'], state, step)
        window.set_logo(path, 'top-right', .85, data)
        entry['shown'] = True


def on_load(boss, data):
    from kitty.fast_data_types import add_timer
    for window in boss.all_windows:
        if Path(window.child.argv[0]).name.lstrip('-') != 'fish':
            continue
        for name in ('on_resize', 'on_cmd_startstop', 'on_close'):
            getattr(window.watchers, name).append(globals()[name])
        on_resize(boss, window, {})
        if window.last_cmd_output_start_time:
            entries[window.id]['state'] = 'running'
    add_timer(lambda timer: tick(boss), .1, True)


def on_resize(boss, window, data):
    if window.id in entries or Path(window.child.argv[0]).name.lstrip('-') != 'fish':
        return
    entries[window.id] = dict(born=time.monotonic(), changed=0, state='idle', shown=False)


def on_cmd_startstop(boss, window, data):
    if window.id not in entries:
        return
    entry = entries[window.id]
    entry['state'] = 'running' if data['is_start'] else 'success' if data['exit_status'] == 0 else 'error'
    entry['changed'] = time.monotonic()


def on_close(boss, window, data):
    entries.pop(window.id, None)
