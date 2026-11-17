#!/usr/bin/env python3
import argparse
import html
import json
import math
import select
import signal
import sys
import termios
import time
import tty

NAMES = ['Terminal cat', 'Growing garden', 'Sleepy robot', 'Little baker',
         'Pocket wizard', 'Little planet']
KEYS = ['cat', 'garden', 'robot', 'baker', 'wizard', 'planet']
COLORS = ['#536482', '#8bd5ff', '#b7a2ff', '#a6ed9e', '#ffd580', '#ff92bd', '#edf3ff']
W, H = 76, 20


class Canvas:
    def __init__(self):
        self.cells = [[(' ', 0) for _ in range(W)] for _ in range(H)]

    def put(self, x, y, text, color=1):
        x, y = round(x), round(y)
        for dy, line in enumerate(text.split('\n')):
            for dx, ch in enumerate(line):
                if 0 <= x + dx < W and 0 <= y + dy < H and ch != ' ':
                    self.cells[y + dy][x + dx] = (ch, color)

    def line(self, x, y, x2, y2, ch='.', color=0):
        steps = max(1, round(max(abs(x2-x), abs(y2-y))))
        for k in range(steps + 1):
            self.put(x+(x2-x)*k/steps, y+(y2-y)*k/steps, ch, color)

    def encode(self, rich=False):
        rows = []
        for row in self.cells:
            parts, last = [], None
            for ch, color in row:
                if color != last:
                    if rich:
                        parts.append(('</span>' if last is not None else '') +
                                     f'<span style="color:{COLORS[color]}">')
                    else:
                        rgb = tuple(int(COLORS[color][i:i+2], 16) for i in (1, 3, 5))
                        parts.append('\x1b[38;2;%d;%d;%dm' % rgb)
                    last = color
                parts.append(html.escape(ch) if rich else ch)
            parts.append('</span>' if rich else '\x1b[0m')
            rows.append(''.join(parts))
        return '<pre>' + '\n'.join(rows) + '</pre>' if rich else '\r\n'.join(rows)


def frame(scene, t, state='running'):
    c = Canvas()
    beat = int(t*4) % 2
    color = {'idle': 2, 'running': 1, 'success': 3, 'error': 5}[state]
    label = {'idle': 'IDLE', 'running': 'WORKING', 'success': 'SUCCESS', 'error': 'ERROR'}[state]
    c.put((W-len(label)-4)//2, 1, '[ '+label+' ]', color)
    if scene == 'cat':
        x = 31+math.sin(t if state == 'running' else t*.15)*2
        eyes = {'idle': '-.-', 'running': 'o.o', 'success': '^.^', 'error': 'O.O'}[state]
        c.put(x, 7, ' /\\_/\\\n( '+eyes+' )\n > ^ <\n/|   |\\\n (_|_)', 4)
        if state == 'idle':
            c.put(x+10, 5-int(t)%2, 'z Z', 2)
        elif state == 'running':
            c.put(x+9, 10, '/-\\|'[int(t*8)%4], 5)
            c.put(x+7, 10+math.sin(t*9), '_/', 4)
        elif state == 'success':
            c.put(x+10, 7-beat, '<3', 5)
        else:
            c.put(x+10, 5, '!?', 5)
            c.put(x+9, 12, '/___/ . .', 1)
        caption = {'idle': 'nap time', 'running': 'spinner hunting',
                   'success': 'purr. well done.', 'error': 'who knocked that over?'}[state]
    elif scene == 'garden':
        c.put(31, 12, '\\__________/\n \\________/\n  \\______/', 2)
        if state == 'idle':
            c.put(33, 9, '\\  /\n \\ /\n  |', 3)
            c.put(41, 7-int(t)%2, 'z z', 2)
        elif state == 'running':
            top = 9-int(t*1.5)%3
            c.put(32, top, '\\ | /\n \\|/', 3)
            c.line(34, top+2, 34, 11, '|', 3)
            c.put(42, 5, ' ___\n|___|_\n \\___/\\', 1)
            c.put(38+beat, 8+beat, '. .\n .', 1)
        elif state == 'success':
            c.put(31, 4, '  .-.-.\n ( ^ ^ )\n(   v   )\n (_____)\n    |\n \\  |  /\n  \\ | /\n    |', 4)
            c.put(27, 6+beat, '+', 5)
            c.put(44, 5+beat, '*', 5)
        else:
            c.put(34, 6, '   ___\n  /   \\__\n  |  (x_x)\n  |   `-\'\n /|\n  |', 4)
            c.put(45, 11+beat, '.', 1)
            c.put(28, 5, '!', 5)
        caption = {'idle': 'a seed with big dreams', 'running': 'sip, sprout, repeat',
                   'success': 'look who bloomed!', 'error': 'oops. too thirsty.'}[state]
    elif scene == 'robot':
        x = 32+beat if state == 'running' else 32
        eyes = {'idle': '- -', 'running': 'o o', 'success': '^ ^', 'error': 'x x'}[state]
        c.put(x, 5, '   o\n   |', 1)
        c.put(x, 6, ' .---.\n |'+eyes+'|\n |_'+('v' if state == 'success' else '_')+'_|', color)
        c.put(x, 10, '[|'+('###' if state == 'success' else '.  ' if state == 'idle' else '=  ' if beat else '== ')+'|]\n  |_|\n _/ \\_', 1)
        if state == 'idle':
            c.put(43, 5-int(t)%2, 'z Z', 2)
            c.put(28, 13, '==', 0)
        elif state == 'running':
            c.put(x+8, 8+beat, 'o--{', 4)
            c.put(x+10, 11, '/-\\|'[int(t*8)%4], 4)
        elif state == 'success':
            c.put(x-4, 8-beat, '\\o/', 4)
            c.put(x+8, 8-beat, '\\o/', 4)
            c.put(46, 5, '+', 3)
        else:
            c.put(x+8, 5+beat, '* !', 5)
            c.put(x+9, 12, 'o--{', 4)
        caption = {'idle': 'battery saver: snooze', 'running': 'tiny bot, big job',
                   'success': 'beep boop. nailed it!', 'error': 'a screw went on vacation'}[state]
    elif scene == 'baker':
        c.put(29, 5, ' .-~~-.\n(______)', 6)
        eyes = {'idle': '- -', 'running': 'o o', 'success': '^ ^', 'error': 'O O'}[state]
        c.put(30, 7, '('+eyes+')\n /'+('v' if state == 'success' else '_')+'\\\n |:|', 4)
        c.put(26, 14, '==========================', 0)
        if state == 'idle':
            c.put(41, 11, '____\n\\__/', 2)
            c.put(38, 5-int(t)%2, 'z z', 2)
        elif state == 'running':
            c.put(35, 9+beat, '--o', 4)
            c.put(40+beat, 9, '/\n/', 6)
            c.put(38, 11, '\\~~~~~~/\n \\____/', 2)
            c.put(44, 8+beat, '.', 6)
        elif state == 'success':
            c.put(41, 7-beat, '*', 4)
            c.put(36, 10, '   i i i\n .-------.\n |~o~o~o~|\n [_______]', 5)
        else:
            c.put(41+beat, 6, '( (\n ) )', 0)
            c.put(38, 10, '  .---.\n /xxxxx\\\n[_______]', 5)
            c.put(37, 5, '!?', 5)
        caption = {'idle': 'resting the dough (and me)', 'running': 'whisking up something good',
                   'success': 'freshly baked. take a slice!', 'error': 'well... extra crispy.'}[state]
    elif scene == 'wizard':
        c.put(30, 4, '    /\\\n   / *\\\n  /____\\', 2)
        eyes = {'idle': '- -', 'running': 'o o', 'success': '^ ^', 'error': '@ @'}[state]
        c.put(32, 7, '('+eyes+')\n /v\\\n/ * \\\n|___|', 2)
        if state == 'idle':
            c.put(41, 5-int(t)%2, 'z Z', 2)
            c.put(41, 12, '___\n\\_/', 0)
        elif state == 'running':
            c.put(38, 8-beat, '--/', 4)
            c.put(43, 6+beat, '*', 4)
            c.put(44, 9, 'o' if beat else '.', 3)
            c.put(40, 12, '\\~~~/\n \\_/', 3)
        elif state == 'success':
            c.put(44, 6-beat, '*', 4)
            c.put(42, 8-beat, '(\\ /)\n(o.o)\n(___)', 6)
            c.put(40, 12, '======\n|____|', 2)
        else:
            c.put(41, 7+beat, 'p o o f', 5)
            c.put(41, 11, ' @ @\n( - )\n/|_|\\', 3)
            c.put(29, 8, '!', 5)
        caption = {'idle': 'out of office. in a spell.', 'running': 'a pinch of hocus pocus',
                   'success': 'ta-da! one bonus bunny.', 'error': 'that was NOT a frog spell'}[state]
    elif scene == 'planet':
        x = 31+beat if state == 'error' else 31
        c.put(x, 6, '   .----.\n /        \\\n|          |\n|          |\n \\        /\n   `----\'', 1)
        eyes = {'idle': '-  -', 'running': 'o  o', 'success': '^  ^', 'error': 'x  x'}[state]
        c.put(x+4, 8, eyes, color)
        c.put(x+5, 9, 'v' if state == 'success' else '~' if state == 'error' else '-', color)
        if state == 'idle':
            c.put(44, 5-int(t)%2, 'z Z', 2)
            c.put(28, 13, '.', 0)
        elif state == 'running':
            a = t*2
            c.put(36+math.cos(a)*12, 9+math.sin(a)*5, '(o)', 4)
            c.put(x+2+int(t*3)%6, 7, '~', 3)
            c.put(x+3+int(t*3)%5, 10, '~', 3)
        elif state == 'success':
            for sx, sy in ((27, 5), (46, 6), (29, 13), (45, 12)):
                c.put(sx, sy-beat, '*', 4)
            c.put(35, 4, '\\|/\n===', 4)
        else:
            c.put(43, 4+beat, '\\\\\n (@)', 4)
            c.put(40, 6, '#', 5)
            c.put(28, 6+beat, '!', 5)
        caption = {'idle': 'do not disturb this world', 'running': 'a world of work to do',
                   'success': 'you are out of this world!', 'error': 'ow. who ordered a meteor?'}[state]
    else:
        raise ValueError(f'Unknown scene: {scene}')
    c.put(4, 17, '_'*68, 0)
    c.put((W-len(caption))//2, 19, caption, color)
    return c


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('scene', choices=KEYS, nargs='?', default='cat')
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--state', choices=['idle', 'running', 'success', 'error'], default='running')
    args = parser.parse_args()
    input_stream = sys.stdin.buffer.raw
    scene, state = args.scene, args.state
    paused, elapsed, previous = False, 0, time.monotonic()
    saved = None
    if not args.stream:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            parser.error('Open in a terminal, or use --stream for JSON frames.')
        saved = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)
        sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[48;2;13;18;32m\x1b[2J')
    def stop(signum, _):
        raise SystemExit(128+signum)
    signal.signal(signal.SIGTERM, stop)
    try:
        while True:
            now = time.monotonic()
            if not paused:
                elapsed += now-previous
            previous = now
            if args.stream:
                if select.select([sys.stdin], [], [], 0)[0]:
                    line = input_stream.readline()
                    if not line:
                        break
                    settings = json.loads(line)
                    if scene != settings['scene'] or state != settings['state']:
                        elapsed = 0
                    scene, state = settings['scene'], settings['state']
                    paused = settings['paused']
                    if settings['restart']:
                        elapsed = 0
                print(json.dumps({'html': frame(scene, elapsed, state).encode(True)}), flush=True)
            else:
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = input_stream.read(1).decode('latin1')
                    if key in ('q', '\x1b'):
                        break
                    if key in '1234567890'[:len(KEYS)]:
                        scene, elapsed = KEYS['1234567890'.index(key)], 0
                    elif key == ' ':
                        paused = not paused
                    elif key == 'r':
                        elapsed = 0
                    elif key in 'iswe':
                        state = dict(i='idle', s='success', w='running', e='error')[key]
                        elapsed = 0
                title = f'  {NAMES[KEYS.index(scene)]}  /  {state}  /  {"paused" if paused else "playing"}'
                sys.stdout.write('\x1b[H\x1b[38;2;237;243;255m'+title.ljust(W)+'\r\n\r\n'+frame(scene, elapsed, state).encode()+
                                 '\r\n\r\n\x1b[38;2;139;213;255m  1-6 scene   Space pause   R replay   Q quit'.ljust(W)+
                                 '\r\n  I idle   W working   S success   E error'.ljust(W))
                sys.stdout.flush()
            time.sleep(1/12)
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        if saved is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, saved)
            sys.stdout.write('\x1b[0m\x1b[?25h\x1b[?1049l')
            sys.stdout.flush()



if __name__ == '__main__':
    main()
