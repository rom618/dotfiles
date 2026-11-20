#!/usr/bin/env python3
import argparse
import base64
import colorsys
import json
import math
import os
import select
import signal
import sys
import termios
import time
import tty
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from PIL import Image

NAMES = ['Cat', 'Sprout', 'Robot', 'Toast']
KEYS = ['cat', 'garden', 'robot', 'baker']
ICONS = {'cat': 'pets', 'garden': 'local_florist', 'robot': 'smart_toy', 'baker': 'bakery_dining'}
GAMES = Path(__file__).resolve().with_name('terminal_toys_games.py')
PRIVATE = Path(os.environ.get('TERMINAL_TOYS_PRIVATE', Path.home() / '.local/share/terminal-toys/private_scenes.py'))
STATES = ['idle', 'running', 'success', 'error', 'waiting']
FPS = {'idle': 4, 'running': 10, 'success': 8, 'error': 8, 'waiting': 8}
FRAMES = 8
W = H = 32
THEME = Path.home() / '.local/state/quickshell/user/generated/colors.json'
FALLBACK_ACCENT = '#e8789a'
INK = (43, 32, 56)
WHITE = (255, 251, 242)
WARM = (255, 244, 222)
COOL = (60, 40, 96)
UPPER, LOWER = chr(0x2580), chr(0x2584)


def rgb(value):
    if isinstance(value, tuple):
        return value
    value = value.lstrip('#')
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[k]+(b[k]-a[k])*t) for k in range(3))


def shades(color, hi=.38, lo=.36):
    c = rgb(color)
    return mix(c, WARM, hi), c, mix(c, COOL, lo)


def theme_accent(path=THEME):
    try:
        value = rgb(json.loads(Path(path).read_text())['primary'])
    except (OSError, ValueError, KeyError, TypeError):
        return FALLBACK_ACCENT
    h, s, v = colorsys.rgb_to_hsv(*(k/255 for k in value))
    s = min(.8, max(.6, s*2.4))
    v = min(.95, max(.88, v))
    return '#%02x%02x%02x' % tuple(round(k*255) for k in colorsys.hsv_to_rgb(h, s, v))


def ellipse(cx, cy, rx, ry):
    return lambda x, y: ((x-cx)/rx)**2+((y-cy)/ry)**2 <= 1


def rrect(x0, y0, x1, y1, r):
    def test(x, y):
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return False
        dx = max(x0+r-x, 0, x-(x1-r))
        dy = max(y0+r-y, 0, y-(y1-r))
        return dx*dx+dy*dy <= r*r
    return test


def triangle(a, b, c):
    def side(p, q, r):
        return (p[0]-r[0])*(q[1]-r[1])-(q[0]-r[0])*(p[1]-r[1])
    def test(x, y):
        d1, d2, d3 = side((x, y), a, b), side((x, y), b, c), side((x, y), c, a)
        return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))
    return test


class Sprite:
    def __init__(self):
        self.layers = {'light': {}, 'body': {}, 'fx': {}}
        self.shadow = None
        self.bands = []

    def band(self, y0, y1, color, alpha=.6):
        self.bands.append((y0, y1, rgb(color), alpha))

    def dot(self, x, y, color, layer='body'):
        x, y = round(x), round(y)
        if 0 <= x < W and 0 <= y < H:
            self.layers[layer][(x, y)] = rgb(color) if color is not None else None

    def fill(self, test, colors, light=(1, 1.5), rim=True, layer='body', edge=None, edge_from=-1):
        hi, base, lo = colors
        drawn = set()
        for y in range(H):
            for x in range(W):
                cx, cy = x+.5, y+.5
                if not test(cx, cy):
                    continue
                if light and not test(cx+light[0], cy+light[1]):
                    color = lo
                elif rim and not test(cx-1, cy-1):
                    color = hi
                else:
                    color = base
                self.layers[layer][(x, y)] = color
                drawn.add((x, y))
        if edge:
            target = self.layers[layer]
            for (x, y) in drawn:
                for n in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if n not in drawn and n[1] >= edge_from and target.get(n) is not None:
                        target[n] = rgb(edge)

    def paint(self, test, color, layer='body'):
        color = rgb(color)
        for (x, y) in list(self.layers[layer]):
            if test(x+.5, y+.5):
                self.layers[layer][(x, y)] = color

    def stamp(self, rows, x, y, palette, layer='body'):
        x, y = math.floor(x+.5), math.floor(y+.5)
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch != '.':
                    self.dot(x+dx, y+dy, palette[ch], layer)

    def line(self, x0, y0, x1, y1, color, layer='body'):
        steps = max(1, round(max(abs(x1-x0), abs(y1-y0))))
        for k in range(steps+1):
            self.dot(x0+(x1-x0)*k/steps, y0+(y1-y0)*k/steps, color, layer)

    def blob(self, points, radius, colors, layer='body'):
        tests = [ellipse(px, py, radius, radius) for px, py in points]
        self.fill(lambda x, y: any(t(x, y) for t in tests), colors, layer=layer)

    def image(self):
        out = Image.new('RGBA', (W, H))
        pixels = out.load()
        if self.shadow:
            cx, cy, rx = self.shadow
            for y in range(H):
                for x in range(W):
                    if ((x+.5-cx)/rx)**2+((y+.5-cy)/1.4)**2 <= 1:
                        pixels[x, y] = (20, 14, 30, 70)
        for (x, y), color in self.layers['light'].items():
            if color is not None:
                pixels[x, y] = color+(255,)
        for name in ('body', 'fx'):
            layer = {k: v for k, v in self.layers[name].items() if v is not None}
            edge = set()
            for (x, y) in layer:
                for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
                    if (nx, ny) not in layer and 0 <= nx < W and 0 <= ny < H:
                        edge.add((nx, ny))
            for (x, y) in edge:
                pixels[x, y] = INK+(255,)
            for (x, y), color in layer.items():
                pixels[x, y] = color+(255,)
        for y0, y1, color, alpha in self.bands:
            for y in range(max(0, round(y0)), min(H, round(y1))):
                edge = min(y-y0+1, y1-y, 2)/2
                for x in range(W):
                    pixels[x, y] = blend(pixels[x, y], color, round(255*alpha*edge))
        return out


def blend(under, color, alpha):
    if not alpha:
        return under
    a = alpha/255
    total = a+under[3]/255*(1-a)
    if total <= 0:
        return (0, 0, 0, 0)
    mixed = tuple(round((color[k]*a+under[k]*under[3]/255*(1-a))/total) for k in range(3))
    return mixed+(round(total*255),)


Z3 = ['zzzz', '..z.', '.z..', 'zzzz']
Z4 = ['zzzzz', '...z.', '..z..', '.z...', 'zzzzz']
HEART = ['.rr.rr.', 'rhrrrrr', 'rrrrrrr', '.rrrrr.', '..rrr..', '...r...']
HEART_S = ['rr.rr', 'rhrrr', '.rrr.', '..r..']
STAR = ['..y..', '..y..', 'yyhyy', '..y..', '..y..']
STAR_S = ['.y.', 'yhy', '.y.']
DROP = ['.b.', 'bhb', 'bbb', '.b.']
BANG = ['yy', 'yy', 'yy', 'yy', '..', 'yy']
FX = {'z': (226, 220, 255), 'r': (255, 106, 140), 'h': WHITE, 'y': (255, 214, 92),
      'b': (130, 200, 255)}


def zzz(s, i, x, y):
    for k in range(2):
        phase = (i/FRAMES+k/2) % 1
        if phase > .92:
            continue
        rows = Z3 if phase < .45 else Z4
        s.stamp(rows, min(x+phase*6, W-len(rows[0])), max(0, y+3-phase*8), FX, 'fx')


def hearts(s, i, spots):
    for k, (x, y) in enumerate(spots):
        phase = (i/FRAMES+k/len(spots)) % 1
        rows = HEART if phase < .55 else HEART_S
        s.stamp(rows, x+round(math.sin(phase*6.3)), y-phase*6, FX, 'fx')


def sparkles(s, i, spots):
    for k, (x, y) in enumerate(spots):
        phase = (i+k*3) % FRAMES
        if phase in (0, 1, 2):
            s.stamp(STAR if phase == 1 else STAR_S, x-(2 if phase == 1 else 1), y-(2 if phase == 1 else 1), FX, 'fx')


def puff(s, i, x, y, color=(206, 200, 214)):
    phase = i % FRAMES
    if phase > 5:
        return
    grow = [1.2, 1.9, 2.4, 2.4, 1.8, 1.1][phase]
    rise = phase*.8
    pts = [(x, y-rise), (x+2.6, y-1-rise), (x-2.4, y-.6-rise), (x+.6, y-2.4-rise)]
    tests = [ellipse(px, py, grow, grow) for px, py in pts]
    s.fill(lambda a, b: any(t(a, b) for t in tests), shades(color, .55, .18), light=(.6, 1.2), layer='fx')


def bang(s, x, y):
    s.stamp(BANG, x, y, FX, 'fx')


BUBBLE = ['.wwwww.', 'wwwrwww', 'wwwrwww', 'wwwrwww', 'wwwwwww', 'wwwrwww', '.wwwww.', '.ww....', 'w......']
HOP = [0, -1, -2, -1, 0, 0, 0, 0]


def attention(s, i, x=23, y=1):
    s.stamp(BUBBLE, x, y+(1 if i % 4 >= 2 else 0), {'w': WHITE, 'r': (240, 84, 84)}, 'fx')


def shift(s, dx, dy, layer='body'):
    s.layers[layer] = {(x+dx, y+dy): c for (x, y), c in s.layers[layer].items() if 0 <= x+dx < W and 0 <= y+dy < H}


def drop(s, x, y):
    s.stamp(DROP, x, y, FX, 'fx')


def face(s, x, y, mood, gap=7, eye='open', look=0, blush=True, mouth=True):
    k, w, p = INK, WHITE, (255, 138, 160)
    pal = {'k': k, 'w': w, 'p': p}
    for ex in (x, x+gap):
        if mood == 'sleep':
            s.stamp(['kkk'], ex-1, y+1, pal)
        elif mood == 'happy':
            s.stamp(['.kk.', 'k..k'], ex-1, y, pal)
        elif mood == 'shock':
            s.stamp(['kkk', 'kwk', 'kkk'], ex-1, y-1, pal)
        elif mood == 'dizzy':
            s.stamp(['k.k', '.k.', 'k.k'], ex-1, y-1, pal)
        else:
            s.stamp(['kw', 'kk', 'kk'] if look >= 0 else ['wk', 'kk', 'kk'], ex+look, y-1, pal)
    if blush:
        s.stamp(['pp'], x-3, y+2, pal)
        s.stamp(['pp'], x+gap+2, y+2, pal)
    if not mouth:
        return
    mx = x+gap//2
    if mood == 'happy':
        s.stamp(['kkkk', '.pp.'], mx-1, y+2, pal)
    elif mood in ('shock', 'dizzy'):
        s.stamp(['.k.', 'k.k', '.k.'], mx, y+2, pal)
    elif mood == 'sleep':
        s.stamp(['.k'], mx, y+3, pal)
    else:
        s.stamp(['k.k', '.k.'], mx, y+2, pal)


def apart(accent, avoid, fallback):
    hue = colorsys.rgb_to_hsv(*(k/255 for k in rgb(accent)))[0]*360
    gap = abs((hue-avoid+180) % 360-180)
    return accent if gap > 45 else fallback


def draw_cat(s, state, i, accent):
    fur, pink = shades('#f4a259'), shades('#ff9fb4')
    cream = ((255, 251, 240), (255, 236, 206), (238, 194, 158))
    bob, shake = 0, 0
    wave = math.sin(i/FRAMES*2*math.pi)
    tail = wave*.5
    if state == 'idle':
        bob = 1 if i >= 4 else 0
    elif state == 'running':
        bob = -(i % 2)
        tail = math.sin(i/FRAMES*4*math.pi)*1.6
    elif state == 'success':
        bob = [0, -2, -3, -2, 0, -1, 0, 0][i]
        tail = wave*1.2
    elif state == 'error':
        shake = [0, -1, 1, -1, 1, 0, 0, 0][i]
    cx = 15+shake
    s.shadow = (16, 30.6, 10)
    pts = [(cx+6+t, 29) for t in range(5)] + [(cx+11.2, 27.6+tail*.3), (cx+12+tail*.4, 25.8-max(tail, 0)), (cx+11.6+tail, 24.2-max(tail, 0)*1.2)]
    s.blob(pts, 1.5, fur)
    s.fill(ellipse(cx, 24.4, 8.2+(1 if state == 'error' else 0), 6.2-bob*.3), fur)
    s.fill(ellipse(cx, 26.2, 4.2, 3.6), cream, light=None)
    hy = 15+bob
    ear = 2 if state == 'error' else 0
    for side in (-1, 1):
        ex = cx+side*6.2
        s.fill(triangle((ex-side*3.6, hy-2), (ex+side*1+side*ear, hy-9.6+ear*1.6), (ex+side*3.8, hy-2.4+ear)), fur)
        s.fill(triangle((ex-side*1.6, hy-3), (ex+side*.9+side*ear, hy-7.6+ear*1.6), (ex+side*2.4, hy-3.4+ear)), pink, light=None, rim=False)
    acc = shades(apart(accent, 28, '#5fb4d9'))
    s.fill(ellipse(cx, hy+.4, 9.2, 6.9), fur, edge=acc[1], edge_from=hy+4)
    s.fill(ellipse(cx, hy+3.6, 3.2, 1.9), cream, light=None)
    for px, py in ((0, -6), (0, -5), (-3, -5), (3, -5)):
        s.dot(cx+px, hy+py, fur[2])
    paw = (1 if i % 4 < 2 else -1) if state == 'running' else 0
    for side, lift in ((-1, max(paw, 0)), (1, max(-paw, 0))):
        s.fill(ellipse(cx+side*3.6, 29.7-lift*1.5, 2.3, 1.5), cream)
    s.fill(ellipse(cx, hy+8.6, 1.2, 1.2), shades('#ffd65c'), rim=False)
    mood = {'idle': 'sleep', 'running': 'open', 'success': 'happy', 'error': 'shock'}.get(state, 'open')
    look = -1 if state == 'running' and i % 4 >= 2 else 0
    face(s, cx-4, hy+1, mood, gap=8, look=look)
    if state == 'idle':
        zzz(s, i, 21, 6)
    elif state == 'running':
        ball = shades(apart(accent, 28, '#7aa7ff'))
        bx = [3, 3.6, 4.4, 5, 5.4, 5, 4.4, 3.6][i]
        by = 27.6-[0, 1.4, 2.2, 1.4, 0, .8, 1, .4][i]
        s.fill(ellipse(bx, by, 2.7, 2.7), ball, layer='fx')
        s.dot(bx-1+(i % 2), by-1, ball[2], 'fx')
        s.dot(bx+(i % 2), by, ball[2], 'fx')
    elif state == 'success':
        hearts(s, i, [(24, 8), (1, 11)])
    elif state == 'error':
        drop(s, cx+9, hy-5)
        bang(s, 3, 5+(i % 2))


def leaf(s, x, y, dx, dy, length, colors, layer='body'):
    pts = [(x+dx*t, y+dy*t) for t in (k*length/4 for k in range(5))]
    tests = [ellipse(px, py, r, r) for (px, py), r in zip(pts, (1, 1.5, 1.7, 1.4, .9))]
    s.fill(lambda a, b: any(t(a, b) for t in tests), colors, layer=layer)


def flower(s, x, y, size, petal, layer='body'):
    hue = colorsys.rgb_to_hsv(*(k/255 for k in petal[1]))[0]*360
    middle = shades('#e0784e' if 25 < hue < 75 else '#ffd65c')
    if size == 0:
        s.fill(ellipse(x, y, 1.4, 1.8), petal, layer=layer)
        return
    d, r = (1.5, 1.3) if size == 1 else (2.5, 1.8)
    for a in range(5):
        ang = a*2*math.pi/5-math.pi/2
        s.fill(ellipse(x+math.cos(ang)*d, y+math.sin(ang)*d, r, r), petal, light=None, edge=petal[2], layer=layer)
    s.fill(ellipse(x, y, 1.2, 1.2), middle, rim=False, light=None, layer=layer)


def draw_garden(s, state, i, accent):
    clay, green = shades('#e0784e'), shades('#6cc96a')
    hop = [0, -1, -2, -1, 0, -1, 0, 0][i] if state == 'success' else 0
    shake = [0, -1, 1, -1, 1, 0, 0, 0][i] if state == 'error' else 0
    cx, top = 16+shake, 19+hop
    s.shadow = (16, 30.6, 8.5)
    sway = math.sin(i/FRAMES*2*math.pi)
    if state == 'error':
        green = shades('#a7b85a')
        path = [(cx, top), (cx, top-6), (cx+1, top-8), (cx+3, top-9), (cx+5, top-8), (cx+6, top-6)]
        for a, b in zip(path, path[1:]):
            s.line(a[0], a[1], b[0], b[1], green[2])
            s.line(a[0]+1, a[1]+1, b[0]+1, b[1]+1, green[1])
        leaf(s, cx, top-4, -1.2, 1, 3.8, green)
        leaf(s, cx+1, top-4, 1.2, 1.1, 3.8, green)
        s.fill(ellipse(cx+6.8, top-4.5, 1.4, 1.8), shades('#c9a26a'))
        if i < 7:
            fx, fy = 25+round(math.sin(i*1.3)*1.5), 7+i*1.8
            s.stamp(['.d', 'dd', 'd.'] if i % 2 else ['d.', 'dd', '.d'], fx, fy, {'d': (201, 162, 106)}, 'fx')
    else:
        if state == 'idle':
            stem, lean, droop = 5, sway*.4, .45
        elif state == 'running':
            stem, lean, droop = 7, sway*.8, -.5 if i % 2 else .1
        elif state == 'waiting':
            stem, lean, droop = 6, 0, -.6
        else:
            stem, lean, droop = 9, sway*.4, -.25
        tip = (cx+lean, top-stem)
        s.line(cx, top, tip[0], tip[1], green[2])
        s.line(cx+1, top, tip[0]+1, tip[1], green[1])
        mid = (cx+lean*.5, top-stem*.5)
        leaf(s, mid[0], mid[1], -1.2, -.3+droop, 4.6, green)
        leaf(s, mid[0]+1, mid[1]-1, 1.2, -.5+droop, 4.6, green)
        if state == 'success':
            flower(s, tip[0]+.5, tip[1]-1, min(i, 2), shades(apart(accent, 110, '#ff8fb8'), .3, .3))
            sparkles(s, i, [(5, 8), (27, 6), (26, 16)])
        else:
            s.fill(ellipse(tip[0]+.5, tip[1]-.5, 1.3, 1.7), green)
    s.fill(rrect(cx-8.5, top-.5, cx+8.5, top+3.5, 1.2), clay)
    s.fill(ellipse(cx, top+.4, 6.6, .9), shades('#6e4634'), rim=False, light=None)
    s.fill(lambda x, y: top+3 <= y <= 30.5 and abs(x-cx) <= 7.2-(y-top-3)*.18, clay, edge=clay[2], edge_from=top+3)
    band = shades(apart(accent, 16, '#6fb6e8'))
    s.paint(lambda x, y: top+9 <= y < top+10 and abs(x-cx) < 8, band[1])
    mood = {'idle': 'sleep', 'running': 'open', 'success': 'happy', 'error': 'shock'}.get(state, 'open')
    face(s, cx-4, top+5, mood, gap=8, look=0)
    if state == 'idle':
        zzz(s, i, 21, 7)
    elif state == 'running':
        for k in range(3):
            phase = (i/FRAMES+k/3) % 1
            drop(s, cx-6+k*5, 1+phase*(top-stem-2))
    elif state == 'error':
        bang(s, 4, 6+(i % 2))


def draw_robot(s, state, i, accent):
    metal, dark, screen = shades('#a9bbd6'), shades('#6c7a96'), shades('#23304a', .15, .2)
    glow = (126, 245, 214) if state != 'error' else (255, 110, 120)
    bob = (1 if i >= 4 else 0) if state == 'idle' else 0
    if state == 'success':
        bob = [0, -1, -2, -1, 0, -1, 0, 0][i]
    shake = [0, -1, 1, -1, 1, 0, 0, 0][i] if state == 'error' else 0
    cx = 16+shake
    s.shadow = (16, 30.6, 8)
    s.fill(rrect(cx-5, 27.5, cx+5, 30.5, 1.5), dark)
    for k in (-3, 0, 3):
        s.dot(cx+k+(i % 2 if state == 'running' else 0), 29, dark[2])
    s.fill(rrect(cx-5.5, 20+bob*.5, cx+5.5, 28, 2), metal)
    arm = 0
    if state == 'running':
        arm = 1 if i % 4 < 2 else -1
    for side in (-1, 1):
        up = state == 'success' and i % 4 < 3
        ay = 21.5 if up else 23.5+arm*side
        s.fill(rrect(cx+side*7.4-1.4, ay-(4 if up else 0), cx+side*7.4+1.4, ay+3, 1.4), metal)
    acc = shades(apart(accent, 215, '#ff9a5c'))
    lights = 3
    for k in range(lights):
        on = (k <= i % 4) if state == 'running' else (state == 'success') or (state == 'idle' and k == 0 and i < 4)
        s.dot(cx-2+k*2, 24+bob*.5, acc[0] if on else dark[2])
        s.dot(cx-2+k*2, 25+bob*.5, acc[1] if on else dark[2])
    hy = 7+bob
    s.line(cx, hy-4, cx, hy, dark[1])
    blink = state == 'running' and i % 2 or state == 'success' or state == 'idle' and i < 2
    s.fill(ellipse(cx+.5, hy-4.5, 1.8, 1.8), shades('#ff6b7a' if state == 'error' else apart(accent, 215, '#ff9a5c')) if blink or state == 'error' else dark, light=None)
    for side in (-1, 1):
        s.fill(rrect(cx+side*9.6-1.5, hy+4, cx+side*9.6+1.5, hy+9, 1), dark)
    s.fill(rrect(cx-8.5, hy, cx+8.5, hy+13, 3), metal)
    s.fill(rrect(cx-6.5, hy+2, cx+6.5, hy+11, 2), screen, rim=False, light=None)
    g = {'g': glow, 'p': (255, 138, 160)}
    ex, ey = cx-4, hy+5
    if state == 'idle':
        for e in (ex, ex+6):
            s.stamp(['ggg'], e-1, ey+1, g)
    elif state == 'running':
        look = [0, 1, 1, 0, 0, -1, -1, 0][i]
        for e in (ex, ex+6):
            s.stamp(['gg', 'gg'], e+look, ey, g)
    elif state == 'success':
        for e in (ex, ex+6):
            s.stamp(['.g.', 'g.g'], e-1, ey, g)
        s.stamp(['g..g', '.gg.'], cx-2, ey+3, g)
    elif state == 'waiting':
        for e in (ex, ex+6):
            s.stamp(['gg', 'gg', 'gg'], e, ey-1, g)
        s.stamp(['gg'], cx-1, ey+3, g)
    else:
        for e in (ex, ex+6):
            s.stamp(['g.g', '.g.', 'g.g'], e-1, ey-1, g)
        s.stamp(['.gg.', 'g..g'], cx-2, ey+3, g)
    if state != 'success':
        s.stamp(['pp'], ex-2, ey+3, g)
        s.stamp(['pp'], ex+7, ey+3, g)
    if state == 'idle':
        zzz(s, i, 21, 5)
    elif state == 'running':
        if i % 2:
            s.stamp(['y.', '.y'], cx+10, hy-3, {'y': (255, 214, 92)}, 'fx')
    elif state == 'success':
        sparkles(s, i, [(4, 6), (27, 4), (28, 18), (3, 18)])
    elif state == 'error':
        puff(s, i, cx+10, hy+2, (214, 210, 224))
        if i % 2:
            s.stamp(['y.y', '.y.', 'y.y'], cx-1, hy-8, {'y': (255, 214, 92)}, 'fx')


def draw_baker(s, state, i, accent):
    crust = shades('#c9813f' if state != 'error' else '#5e3f31')
    crumb = shades('#f8d9a0' if state != 'error' else '#93654a', .45, .25)
    if state == 'success':
        crumb = shades('#fbcf72', .45, .25)
    hop = 0
    if state == 'running':
        hop = [0, -1, -2, -1, 0, -1, -2, -1][i]
    elif state == 'success':
        hop = [0, -1, -2, -1, 0, -1, 0, 0][i]
    elif state == 'idle':
        hop = 1 if i >= 4 else 0
    shake = [0, -1, 1, -1, 1, 0, 0, 0][i] if state == 'error' else 0
    cx = 16+shake
    s.shadow = (16, 30.6, 8.5)
    for side in (-1, 1):
        s.fill(rrect(cx+side*3.5-1.2, 27+hop, cx+side*3.5+1.2, 30.4, .8), shades('#6b4a3a'))
    top = 17+hop
    body = lambda x, y: ellipse(cx, top, 10, 5)(x, y) or rrect(cx-8.4, top, cx+8.4, 28.6+hop, 2.5)(x, y)
    s.fill(body, crust)
    inner = lambda x, y: ellipse(cx, top+.6, 8.4, 3.7)(x, y) or rrect(cx-6.9, top+.6, cx+6.9, 27.2+hop, 2)(x, y)
    s.fill(inner, crumb, light=(1, 1))
    arm = (1 if i % 2 else -1) if state == 'running' else 0
    for side in (-1, 1):
        ay = 22+hop-(3 if state == 'success' and i % 4 < 3 else 0)+arm*side
        s.fill(ellipse(cx+side*9.4, ay, 1.6, 1.6), crust)
    if state == 'running':
        wx = cx+10.6
        s.line(wx, 22+hop+arm, wx, 18+hop+arm, (150, 156, 176))
        s.fill(ellipse(wx+.5, 15.6+hop+arm, 1.6, 2.4), ((250, 250, 255), (214, 220, 234), (150, 156, 176)), rim=False)
    hat = ((255, 255, 255), (246, 242, 236), (200, 194, 212))
    tilt = 1 if state == 'idle' else -1 if state == 'error' else 0
    hy = 10+hop
    s.fill(rrect(cx-4.2+tilt, hy-1, cx+4.2+tilt, hy+2.6, .8), hat, light=(1, 0))
    for k, (dx, dy, r) in enumerate(((-3.4, -2.6, 2.8), (3.4, -2.6, 2.8), (0, -3.8, 3.2))):
        s.fill(ellipse(cx+dx+tilt*1.6, hy+dy, r, r*.95), hat, edge=hat[2], edge_from=hy-8)
    mood = {'idle': 'sleep', 'running': 'open', 'success': 'happy', 'error': 'shock'}.get(state, 'open')
    face(s, cx-4, 21+hop, mood, gap=8)
    if state == 'idle':
        zzz(s, i, 21, 6)
    elif state == 'running':
        for k in range(2):
            phase = (i/FRAMES+k/2) % 1
            if phase < .75:
                s.fill(ellipse(4+k*24+phase*2*(1-2*k), 26-phase*8, 1.7-phase, 1.7-phase), shades('#fff6e6'), layer='fx')
    elif state == 'success':
        sparkles(s, i, [(4, 12), (28, 9), (27, 24)])
        hearts(s, i, [(0, 22)])
    elif state == 'error':
        puff(s, i, cx+8, hy-1, (110, 104, 118))
        puff(s, (i+3) % FRAMES, cx-8, hy+2, (130, 124, 138))
        bang(s, 3, 14+(i % 2))


DRAW = {'cat': draw_cat, 'garden': draw_garden, 'robot': draw_robot, 'baker': draw_baker}
BUILTIN = set(DRAW)


def load_private(path=PRIVATE):
    if not Path(path).is_file():
        return
    import importlib.util
    import types
    try:
        spec = importlib.util.spec_from_file_location('terminal_toys_private', path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for key, name, icon, draw in mod.scenes(types.SimpleNamespace(**globals())):
            if key not in DRAW:
                KEYS.append(key)
                NAMES.append(name)
                ICONS[key] = icon
                DRAW[key] = draw
    except Exception as error:
        print(f'terminal-toys: scenes in {path} skipped: {error!r}', file=sys.stderr)


load_private(GAMES)
load_private()


def render(scene, state, i, accent=FALLBACK_ACCENT):
    s = Sprite()
    DRAW[scene](s, state, i % FRAMES, accent)
    if state == 'waiting' and scene in BUILTIN:
        shift(s, 0, HOP[i % FRAMES])
        attention(s, i % FRAMES)
    return s.image()


@lru_cache(maxsize=1024)
def frame_png(scene, state, i, scale=6, accent=FALLBACK_ACCENT, pad=(0, 0, 0, 0)):
    image = render(scene, state, i, accent).resize((W*scale, H*scale), Image.Resampling.NEAREST)
    if any(pad):
        left, top, right, bottom = pad
        padded = Image.new('RGBA', (image.width+left+right, image.height+top+bottom))
        padded.paste(image, (left, top))
        image = padded
    output = BytesIO()
    image.save(output, format='PNG', optimize=False, compress_level=6)
    return output.getvalue()


def frame_index(elapsed, state):
    return int(elapsed*FPS[state]) % FRAMES


def data_uri(png):
    return 'data:image/png;base64,'+base64.b64encode(png).decode()


def kitty_upload(image_id, png):
    data = base64.b64encode(png).decode()
    chunks = [data[k:k+4096] for k in range(0, len(data), 4096)]
    out = []
    for n, chunk in enumerate(chunks):
        more = 1 if n < len(chunks)-1 else 0
        head = f'a=t,f=100,i={image_id},q=2,m={more}' if n == 0 else f'm={more}'
        out.append(f'\x1b_G{head};{chunk}\x1b\\')
    return ''.join(out)


def halfblocks(image):
    pixels = image.load()
    rows = []
    for y in range(0, image.height, 2):
        parts = []
        for x in range(image.width):
            top = pixels[x, y]
            bottom = pixels[x, y+1] if y+1 < image.height else (0, 0, 0, 0)
            if top[3] < 128 and bottom[3] < 128:
                parts.append('\x1b[0m ')
            elif top[3] < 128:
                parts.append('\x1b[0m\x1b[38;2;%d;%d;%dm' % bottom[:3] + LOWER)
            elif bottom[3] < 128:
                parts.append('\x1b[0m\x1b[38;2;%d;%d;%dm' % top[:3] + UPPER)
            else:
                parts.append('\x1b[38;2;%d;%d;%dm\x1b[48;2;%d;%d;%dm' % (top[:3]+bottom[:3]) + UPPER)
        rows.append(''.join(parts)+'\x1b[0m')
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('scene', choices=KEYS, nargs='?', default='cat')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--stream', action='store_true')
    parser.add_argument('--state', choices=STATES, default='running')
    parser.add_argument('--scale', type=int, default=8)
    args = parser.parse_args()
    if args.list:
        print(json.dumps([{'key': k, 'name': n, 'icon': ICONS.get(k, 'animation')} for k, n in zip(KEYS, NAMES)]))
        return
    input_stream = sys.stdin.buffer.raw
    scene, state = args.scene, args.state
    accent = theme_accent()
    paused, elapsed, previous = False, 0, time.monotonic()
    saved = None
    kitty = not args.stream and (os.environ.get('KITTY_WINDOW_ID') or os.environ.get('TERM') == 'xterm-kitty')
    uploaded = set()
    shown = None
    if not args.stream:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            parser.error('Open in a terminal, or use --stream for JSON frames.')
        saved = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin)
        sys.stdout.write('\x1b[?1049h\x1b[?25l\x1b[2J')
    def stop(signum, _):
        raise SystemExit(128+signum)
    signal.signal(signal.SIGTERM, stop)
    try:
        while True:
            now = time.monotonic()
            if not paused:
                elapsed += now-previous
            previous = now
            index = frame_index(elapsed, state)
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
                    accent = theme_accent()
                    index = frame_index(elapsed, state)
                key = (scene, state, index, accent)
                if key != shown:
                    png = frame_png(scene, state, index, args.scale, accent)
                    print(json.dumps({'scene': scene, 'state': state, 'frame': index,
                                      'size': W*args.scale, 'image': data_uri(png)}), flush=True)
                    shown = key
            else:
                if select.select([sys.stdin], [], [], 0)[0]:
                    key = input_stream.read(1).decode('latin1')
                    if key in ('q', '\x1b'):
                        break
                    if key in '1234567890'[:len(KEYS)]:
                        scene, elapsed = KEYS['1234567890'.index(key)], 0
                    elif key in 'np':
                        scene, elapsed = KEYS[(KEYS.index(scene)+(1 if key == 'n' else -1)) % len(KEYS)], 0
                    elif key == ' ':
                        paused = not paused
                    elif key == 'r':
                        elapsed = 0
                    elif key in 'iswea':
                        state = dict(i='idle', s='success', w='running', e='error', a='waiting')[key]
                        elapsed = 0
                    sys.stdout.write('\x1b[2J')
                    shown = None
                    index = frame_index(elapsed, state)
                title = f'  {NAMES[KEYS.index(scene)]}  /  {state}  /  {"paused" if paused else "playing"}'
                help_text = ['  1-0 or N/P scene   Space pause   R replay   Q quit',
                             '  I idle   W working   S success   E error   A attention']
                key = (scene, state, index)
                if key != shown:
                    out = ['\x1b[H\x1b[0m\x1b[1m'+title+'\x1b[0m\x1b[K\r\n\r\n']
                    if kitty:
                        image_id = 1+KEYS.index(scene)*64+STATES.index(state)*FRAMES+index
                        if image_id not in uploaded:
                            out.append(kitty_upload(image_id, frame_png(scene, state, index, args.scale, accent)))
                            uploaded.add(image_id)
                        out.append('\x1b_Ga=d,d=a,q=2\x1b\\\x1b[3;3H')
                        out.append(f'\x1b_Ga=p,i={image_id},q=2,C=1\x1b\\')
                        rows = os.get_terminal_size().lines
                        out.append(f'\x1b[{rows-2};1H\x1b[2m'+help_text[0]+'\x1b[K\r\n'+help_text[1]+'\x1b[K\x1b[0m')
                    else:
                        image = render(scene, state, index, accent)
                        cols = os.get_terminal_size().columns
                        if cols >= W*2+4:
                            image = image.resize((W*2, H*2), Image.Resampling.NEAREST)
                        for row in halfblocks(image):
                            out.append('  '+row+'\x1b[K\r\n')
                        out.append('\r\n\x1b[2m'+help_text[0]+'\x1b[K\r\n'+help_text[1]+'\x1b[K\x1b[0m')
                    sys.stdout.write(''.join(out))
                    sys.stdout.flush()
                    shown = key
            time.sleep(1/30)
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        if saved is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, saved)
            if kitty:
                sys.stdout.write('\x1b_Ga=d,d=A,q=2\x1b\\')
            sys.stdout.write('\x1b[0m\x1b[?25h\x1b[?1049l')
            sys.stdout.flush()


if __name__ == '__main__':
    main()
