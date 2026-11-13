#!/usr/bin/env python3
import math
import os
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

W, H = 2560, 1600
OUT_SIZE = (3840, 2400)
OUT = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "quickshell-themes" / "wallpapers"


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def vgradient(stops):
    col = Image.new("RGB", (1, H))
    px = col.load()
    stops = [(p, hexrgb(c)) for p, c in stops]
    for y in range(H):
        t = y / (H - 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                f = (t - p0) / (p1 - p0) if p1 > p0 else 0
                f = f * f * (3 - 2 * f)
                px[0, y] = tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
                break
    return col.resize((W, H))


def glow(img, center, radius, color, strength):
    layer = Image.new("RGB", img.size, hexrgb(color))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse([center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
                                 fill=int(255 * strength))
    mask = mask.filter(ImageFilter.GaussianBlur(radius * 0.6))
    return Image.composite(layer, img, mask)


def ridge(rng, base, amp, rough, seed_shift=0.0):
    pts = []
    phases = [rng.random() * 6.28 for _ in range(4)]
    for x in range(0, W + 41, 40):
        y = base
        for i, ph in enumerate(phases):
            f = (i + 1) * rough
            y -= amp / (i + 1) * math.sin(x / W * math.pi * f + ph + seed_shift)
        pts.append((x, y))
    return pts


def fill_below(img, pts, color, blur=0):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(pts + [(W + 40, H), (-40, H)], fill=255)
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return Image.composite(Image.new("RGB", img.size, hexrgb(color)), img, mask)


def grain(img, amount, rng):
    noise = Image.effect_noise(img.size, amount).convert("RGB")
    return Image.blend(img, noise, 0.035)


def pine(d, x, base, h, color):
    w = h * 0.36
    for i in range(4):
        top = base - h + i * h * 0.2
        bot = base - h * 0.15 + i * h * 0.05 - (3 - i) * h * 0.12
        ww = w * (0.45 + i * 0.2)
        d.polygon([(x, top), (x - ww, bot), (x + ww, bot)], fill=color)
    d.rectangle([x - h * 0.025, base - h * 0.18, x + h * 0.025, base], fill=color)


def forest():
    rng = random.Random(11)
    img = vgradient([(0, "#0B2219"), (0.45, "#1B4332"), (0.7, "#40916C"), (0.78, "#B7C98A"), (1, "#0E2A1F")])
    img = glow(img, (W * 0.32, H * 0.7), 380, "#E9C46A", 0.5)
    layers = [(H * 0.74, 160, "#2D6A4F", 6, 70), (H * 0.82, 230, "#1B4332", 3, 55), (H * 0.92, 330, "#0E2A1F", 1, 42),
              (H * 1.02, 470, "#081C15", 0, 34)]
    for base, size, color, blur, count in layers:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rectangle([0, min(base - size * 0.05, H - 1), W, H], fill=color)
        for i in range(count):
            x = (i + rng.random() * 0.8) * W / count
            pine(d, x, base + rng.random() * size * 0.08, size * (0.7 + rng.random() * 0.6), color)
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.paste(layer, (0, 0), layer)
        fog = Image.new("RGB", img.size, hexrgb("#95D5B2"))
        mask = Image.new("L", img.size, 0)
        ImageDraw.Draw(mask).rectangle([0, base - size * 0.2, W, base + size * 0.05], fill=28)
        img = Image.composite(fog, img, mask.filter(ImageFilter.GaussianBlur(60)))
    return grain(img, 40, rng)


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def palette_at(colors, t):
    t = max(0.0, min(1.0, t)) * (len(colors) - 1)
    i = min(int(t), len(colors) - 2)
    return mix(hexrgb(colors[i]), hexrgb(colors[i + 1]), t - i)


def blob_layer(shapes, blur):
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for box, color in shapes:
        d.ellipse(box, fill=hexrgb(color) if isinstance(color, str) else color)
    return layer.filter(ImageFilter.GaussianBlur(blur))


def midnight_galaxy():
    rng = random.Random(101)
    img = vgradient([(0, "#04061A"), (0.55, "#0A1033"), (1, "#18143F")])
    ang = math.radians(-24)
    cx, cy = W * 0.52, H * 0.42

    def on_band(t, spread):
        x = cx + t * math.cos(ang) - spread * math.sin(ang)
        y = cy + t * math.sin(ang) + spread * math.cos(ang)
        return x, y

    shapes = []
    for _ in range(70):
        t = (rng.random() - 0.5) * W * 1.5
        x, y = on_band(t, rng.gauss(0, 90))
        r = 120 + rng.random() * 340
        c = rng.choice(["#3B2A6E", "#5B4A9E", "#2E3A80", "#7A4FA0", "#9C5FA8", "#3E5BA8"])
        shapes.append(([x - r, y - r * 0.55, x + r, y + r * 0.55], c))
    img = ImageChops.screen(img, ImageEnhance.Brightness(blob_layer(shapes, 110)).enhance(0.8))
    dust = [([x - r, y - r * 0.3, x + r, y + r * 0.3], (60, 60, 70)) for x, y, r in
            [(*on_band((rng.random() - 0.5) * W * 1.4, rng.gauss(0, 30)), 60 + rng.random() * 160) for _ in range(40)]]
    img = ImageChops.subtract(img, blob_layer(dust, 40))
    d = ImageDraw.Draw(img)
    for i in range(11000):
        if i < 7000:
            x, y = on_band((rng.random() - 0.5) * W * 1.6, rng.gauss(0, 150))
        else:
            x, y = rng.random() * W, rng.random() * H * 0.85
        r = rng.choice([0.5, 0.7, 0.9, 1.1, 1.4]) * (2.2 if rng.random() < 0.01 else 1)
        b = rng.randint(140, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rng.choice([(b, b, b), (b, b, 255), (255, int(b * 0.9), int(b * 0.75))]))
    img = Image.blend(img, img.filter(ImageFilter.GaussianBlur(1.6)), 0.3)
    img = glow(img, (W * 0.15, H * 1.0), 700, "#3B2A6E", 0.5)
    img = fill_below(img, ridge(rng, H * 0.84, 60, 1.8), "#0D0B26", 3)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    pd = ImageDraw.Draw(layer)
    base = ridge(rng, H * 0.92, 30, 2.6, 0.7)
    for x, y in base[::3]:
        if rng.random() < 0.55:
            pine(pd, x + rng.random() * 30, y + 10, 90 + rng.random() * 120, "#05040F")
    img.paste(layer, (0, 0), layer)
    img = fill_below(img, base, "#05040F", 1)
    return grain(img, 40, rng)


def snowy_pine(d, x, base, h, color, snow):
    w = h * 0.38
    for i in range(5):
        top = base - h + i * h * 0.17
        bot = top + h * 0.3
        ww = w * (0.35 + i * 0.17)
        d.polygon([(x, top), (x - ww, bot), (x + ww, bot)], fill=color)
        k = 0.3 + 0.25 * ((i * 7919) % 5) / 4
        d.polygon([(x, top), (x - ww * 0.55 * k * 2, top + (bot - top) * k * 1.1), (x - ww * 0.1, top + (bot - top) * k * 0.8),
                   (x + ww * 0.45 * k * 2, top + (bot - top) * k)], fill=snow)
    d.rectangle([x - h * 0.03, base - h * 0.1, x + h * 0.03, base], fill=color)


def arctic_pines():
    rng = random.Random(606)
    img = vgradient([(0, "#89C2D9"), (0.4, "#CAE9F5"), (0.75, "#E6F5FB"), (1, "#F4FBFE")])
    img = fill_below(img, ridge(rng, H * 0.52, 140, 1.7), "#B8E1F1", 5)
    img = fill_below(img, ridge(rng, H * 0.58, 90, 2.3, 0.4), "#A9D6E5", 3)
    for base, size, color, snow, count, blur in [(H * 0.68, 150, "#61A5C2", "#E6F5FB", 60, 3),
                                                 (H * 0.8, 240, "#2A6F97", "#F4FBFE", 34, 1),
                                                 (H * 0.98, 420, "#013A63", "#FFFFFF", 14, 0)]:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i in range(count):
            x = (i + rng.random() * 0.8) * W / count
            snowy_pine(d, x, base + rng.random() * size * 0.06, size * (0.7 + rng.random() * 0.5), hexrgb(color), hexrgb(snow))
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.paste(layer, (0, 0), layer)
        img = fill_below(img, ridge(rng, base + size * 0.04, 12, 3.5), "#F4FBFE", 2)
    flakes = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(flakes)
    for _ in range(1800):
        x, y = rng.random() * W, rng.random() * H
        r = 0.8 + rng.random() * 2.6
        fd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, rng.randint(120, 230)))
    img.paste(flakes, (0, 0), flakes.filter(ImageFilter.GaussianBlur(0.6)))
    return grain(img, 20, rng)


def mint_lowpoly():
    rng = random.Random(808)
    colors = ["#C7F9CC", "#80ED99", "#57CC99", "#38A3A5", "#22577A"]
    cols, rows = 26, 17
    pts = [[(x * W / (cols - 1) + (rng.random() - 0.5) * W / cols * (0 < x < cols - 1),
             y * H / (rows - 1) + (rng.random() - 0.5) * H / rows * (0 < y < rows - 1)) for x in range(cols)] for y in range(rows)]
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(rows - 1):
        for x in range(cols - 1):
            a, b, c, e = pts[y][x], pts[y][x + 1], pts[y + 1][x], pts[y + 1][x + 1]
            tris = [(a, b, e), (a, e, c)] if rng.random() < 0.5 else [(a, b, c), (b, e, c)]
            for tri in tris:
                mx = sum(p[0] for p in tri) / 3
                my = sum(p[1] for p in tri) / 3
                t = (mx / W * 0.45 + my / H * 0.75) / 1.2
                t += 0.08 * math.sin(mx / W * 5.0 + my / H * 3.0)
                base = palette_at(colors, t)
                v = (tri[1][0] - tri[0][0]) * (tri[2][1] - tri[0][1]) - (tri[1][1] - tri[0][1]) * (tri[2][0] - tri[0][0])
                shade = 0.06 if v > 0 else -0.04
                shade += (rng.random() - 0.5) * 0.06
                col = mix(base, (255, 255, 255), shade) if shade > 0 else mix(base, (0, 0, 0), -shade)
                d.polygon(tri, fill=col, outline=mix(col, (255, 255, 255), 0.12))
    img = glow(img, (W * 0.15, H * 0.1), 600, "#FFFFFF", 0.3)
    return grain(img, 20, rng)

def dune(img, rng, base, amp, color, shadow, crest, blur=0):
    ph = rng.random() * 6.28
    f1, f2 = 1.2 + rng.random() * 1.2, 3.1 + rng.random() * 1.5
    pts = [(x, base - amp * (0.6 * math.sin(x / W * math.pi * f1 + ph) + 0.4 * math.sin(x / W * math.pi * f2 + ph * 1.7)))
           for x in range(-40, W + 41, 16)]
    img = fill_below(img, pts, color, blur)
    sh = Image.new("L", img.size, 0)
    sd = ImageDraw.Draw(sh)
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]
        if y1 > y0:
            sd.polygon([(x0, y0), (x1, y1), (x1 + 60, y1 + amp * 1.2), (x0 + 60, y0 + amp * 1.2)], fill=110)
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(pts + [(W + 40, H), (-40, H)], fill=255)
    sh = ImageChops.multiply(sh.filter(ImageFilter.GaussianBlur(24)), mask)
    img = Image.composite(Image.new("RGB", img.size, hexrgb(shadow)), img, sh)
    ImageDraw.Draw(img).line(pts, fill=hexrgb(crest), width=2)
    return img


def saguaro(d, x, base, h, color):
    w = h * 0.12
    d.rounded_rectangle([x - w / 2, base - h, x + w / 2, base], radius=w / 2, fill=color)
    for side, at, arm in ((-1, 0.55, 0.32), (1, 0.4, 0.26)):
        ax = x + side * w / 2
        ay = base - h * at
        d.rounded_rectangle([min(ax, ax + side * h * 0.16), ay - w * 0.4, max(ax, ax + side * h * 0.16), ay + w * 0.4],
                            radius=w * 0.4, fill=color)
        ex = ax + side * h * 0.16
        d.rounded_rectangle([ex - w * 0.4, ay - h * arm, ex + w * 0.4, ay + w * 0.4], radius=w * 0.4, fill=color)


def desert_night():
    rng = random.Random(910)
    img = vgradient([(0, "#0B1026"), (0.5, "#1F2050"), (0.7, "#4A3060"), (1, "#2A1B14")])
    d = ImageDraw.Draw(img)
    for _ in range(1600):
        x, y = rng.random() * W, (rng.random() ** 1.3) * H * 0.7
        r = rng.choice([0.6, 0.8, 1.1, 1.5]) * (1.8 if rng.random() < 0.02 else 1)
        b = rng.randint(150, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=rng.choice([(b, b, b), (255, int(b * 0.9), int(b * 0.75))]))
    img = glow(img, (W * 0.22, H * 0.2), 200, "#F5E6C8", 0.3)
    d = ImageDraw.Draw(img)
    d.ellipse([W * 0.22 - 60, H * 0.2 - 60, W * 0.22 + 60, H * 0.2 + 60], fill=hexrgb("#F5E6C8"))
    for base, amp, color, shadow, crest in [(H * 0.7, 50, "#4A3A5A", "#2E2440", "#7A6A8A"),
                                            (H * 0.82, 80, "#3A2A44", "#22182E", "#6A5A7A"),
                                            (H * 0.96, 100, "#2A1E32", "#170F1E", "#5A4A6A")]:
        img = dune(img, rng, base, amp, color, shadow, crest)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(layer)
    for x, h in ((W * 0.12, 300), (W * 0.83, 380), (W * 0.9, 220), (W * 0.55, 160)):
        saguaro(cd, x, H * 0.93, h, hexrgb("#120A16"))
    img.paste(layer, (0, 0), layer)
    return grain(img, 35, rng)


def branch(d, rng, x, y, ang, length, width, depth, color, tips):
    ex, ey = x + math.cos(ang) * length, y + math.sin(ang) * length
    d.line([(x, y), (ex, ey)], fill=hexrgb(color), width=max(1, int(width)))
    if depth == 0 or length < 18:
        tips.append((ex, ey))
        return
    for da in (-0.45 - rng.random() * 0.3, 0.3 + rng.random() * 0.35):
        branch(d, rng, ex, ey, ang + da, length * (0.62 + rng.random() * 0.18), width * 0.68, depth - 1, color, tips)
    if rng.random() < 0.5:
        tips.append((ex, ey))


def blossoms(img, rng, tips, colors, spread, count):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for tx, ty in tips:
        for _ in range(count):
            x, y = tx + rng.gauss(0, spread), ty + rng.gauss(0, spread)
            r = 4 + rng.random() * 9
            c = hexrgb(rng.choice(colors))
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (rng.randint(170, 245),))
            if rng.random() < 0.3:
                d.ellipse([x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35], fill=(255, 245, 250, 230))
    img.paste(layer, (0, 0), layer)
    return img


def baked_petals(img, rng, n, colors):
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y, r = rng.random() * W, rng.random() * H, 3 + rng.random() * 6
        a = rng.random() * math.pi
        pts = [(x + r * math.cos(a + t) * (1 if k % 2 else 0.45), y + r * math.sin(a + t) * (1 if k % 2 else 0.45))
               for k, t in enumerate([i * math.pi / 2 for i in range(4)])]
        d.polygon(pts, fill=hexrgb(rng.choice(colors)))
    return img


def sakura():
    rng = random.Random(1001)
    img = vgradient([(0, "#DCEBF7"), (0.5, "#FBE4EC"), (1, "#F6D3DF")])
    img = fill_below(img, ridge(rng, H * 0.75, 60, 1.5), "#EFC6D5", 6)
    img = fill_below(img, ridge(rng, H * 0.86, 50, 2.2, 0.5), "#E9B0C4", 3)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tips = []
    branch(d, rng, -40, H * 0.05, 0.35, 520, 34, 6, "#5A3A3A", tips)
    branch(d, rng, W + 40, H * 0.15, math.pi - 0.3, 380, 26, 5, "#5A3A3A", tips)
    img.paste(layer, (0, 0), layer)
    img = blossoms(img, rng, tips, ["#F8B7CD", "#FBD3E0", "#E07A9E", "#FFF0F5"], 26, 14)
    img = baked_petals(img, rng, 220, ["#F8B7CD", "#FBD3E0", "#FFFFFF"])
    return grain(img, 25, rng)


def ocean_abyss():
    rng = random.Random(1103)
    img = vgradient([(0, "#06243A"), (0.4, "#031726"), (1, "#010A12")])
    d = ImageDraw.Draw(img)
    for _ in range(500):
        x, y, r = rng.random() * W, rng.random() * H, 0.7 + rng.random() * 1.6
        c = rng.choice([(120, 230, 240), (200, 160, 255), (150, 255, 210)])
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    glows = []
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    jd = ImageDraw.Draw(layer)
    for _ in range(7):
        x, y = rng.random() * W, H * (0.15 + rng.random() * 0.65)
        s = 0.6 + rng.random() * 1.2
        col = rng.choice(["#6FD3E6", "#C7A6FF", "#F7A8D8", "#7FE0B5"])
        glows.append(([x - 160 * s, y - 120 * s, x + 160 * s, y + 160 * s], col))
        jd.chord([x - 70 * s, y - 60 * s, x + 70 * s, y + 60 * s], 180, 360, fill=hexrgb(col) + (200,))
        jd.chord([x - 50 * s, y - 40 * s, x + 50 * s, y + 30 * s], 180, 360, fill=(255, 255, 255, 120))
        for k in range(7):
            tx = x - 55 * s + k * 18 * s
            pts = [(tx + 14 * s * math.sin(t / 3 + k), y + t * 14 * s) for t in range(18)]
            jd.line(pts, fill=hexrgb(col) + (170,), width=max(2, int(3 * s)))
    img = ImageChops.screen(img, ImageEnhance.Brightness(blob_layer(glows, 70)).enhance(0.45))
    img.paste(layer, (0, 0), layer)
    return grain(img, 30, rng)


def ember_lava():
    rng = random.Random(1203)
    img = vgradient([(0, "#1A1110"), (1, "#0E0807")])
    rock = Image.effect_noise((W // 8, H // 8), 60).convert("RGB").resize((W, H), Image.BICUBIC)
    img = Image.blend(img, ImageChops.multiply(rock, Image.new("RGB", (W, H), (60, 40, 34))), 0.6)
    cracks = Image.new("RGB", img.size, (0, 0, 0))
    cd = ImageDraw.Draw(cracks)
    for _ in range(26):
        x, y = rng.random() * W, rng.random() * H
        a = rng.random() * math.tau
        pts = [(x, y)]
        for _ in range(60):
            a += (rng.random() - 0.5) * 0.9
            x += math.cos(a) * 26
            y += math.sin(a) * 26
            pts.append((x, y))
            if rng.random() < 0.05:
                bx, by, ba = x, y, a + (rng.random() - 0.5) * 2
                bp = [(bx, by)]
                for _ in range(15):
                    ba += (rng.random() - 0.5) * 0.8
                    bx += math.cos(ba) * 22
                    by += math.sin(ba) * 22
                    bp.append((bx, by))
                cd.line(bp, fill=(255, 90, 20), width=4)
        cd.line(pts, fill=(255, 110, 25), width=7)
    img = ImageChops.screen(img, cracks.filter(ImageFilter.GaussianBlur(18)))
    img = ImageChops.screen(img, cracks.filter(ImageFilter.GaussianBlur(5)))
    core = ImageEnhance.Brightness(cracks).enhance(1.0).point(lambda v: min(255, int(v * 1.2)))
    img = ImageChops.screen(img, core.filter(ImageFilter.GaussianBlur(1)).point(lambda v: v // 2))
    return grain(img, 30, rng)


def lavender():
    rng = random.Random(1301)
    horizon = int(H * 0.55)
    img = vgradient([(0, "#2C2348"), (0.35, "#7A5AA8"), (0.5, "#F2B8A0"), (0.55, "#FFD9B0"), (1, "#3A2A5A")])
    img = glow(img, (W * 0.62, horizon), 220, "#FFF0D0", 0.8)
    img = fill_below(img, ridge(rng, horizon, 18, 1.4), "#5A4A78", 3)
    vx = W * 0.6
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, horizon + 4, W, H], fill=hexrgb("#4A5A3A"))
    rows = 26
    for k in range(-rows, rows + 1):
        x_bottom = vx + k * 240
        d.polygon([(vx + k * 6 - 1, horizon + 6), (vx + k * 6 + 1, horizon + 6), (x_bottom + 90, H + 40), (x_bottom - 90, H + 40)],
                  fill=hexrgb("#7A5AB8" if k % 2 == 0 else "#8E6AC8"))
    img.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(img)
    for _ in range(2200):
        y = horizon + (rng.random() ** 2) * (H - horizon)
        t = (y - horizon) / (H - horizon)
        x = rng.random() * W
        r = 1 + t * 4
        d.ellipse([x - r, y - r * 1.6, x + r, y + r * 1.6], fill=hexrgb(rng.choice(["#B89AF0", "#9A7AD8", "#D2BFF7"])))
    tx = W * 0.25
    d.line([(tx, horizon + 8), (tx, horizon - 110)], fill=hexrgb("#1C1630"), width=12)
    for _ in range(18):
        x, y, r = tx + rng.gauss(0, 60), horizon - 150 + rng.gauss(0, 35), 30 + rng.random() * 30
        d.ellipse([x - r, y - r, x + r, y + r], fill=hexrgb("#1C1630"))
    return grain(img, 30, rng)


def neon_buildings(img, rng, horizon, layers):
    for color, hmin, hmax, wmin, wmax, signs in layers:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        glow_l = Image.new("RGB", img.size, (0, 0, 0))
        g = ImageDraw.Draw(glow_l)
        x = -rng.random() * 60
        while x < W:
            bw = wmin + rng.random() * (wmax - wmin)
            bh = hmin + rng.random() * (hmax - hmin)
            top = horizon - bh
            d.rectangle([x, top, x + bw, horizon], fill=hexrgb(color))
            for wy in range(int(top + 16), int(horizon - 10), 20):
                for wx in range(int(x + 8), int(x + bw - 10), 14):
                    if rng.random() < 0.12:
                        d.rectangle([wx, wy, wx + 6, wy + 9], fill=hexrgb(rng.choice(["#3EE6FF", "#FF4FD8", "#FFE45E", "#8A80B0"])))
            if signs and rng.random() < 0.6:
                c = hexrgb(rng.choice(["#FF4FD8", "#3EE6FF", "#FFE45E", "#FF5F87", "#5FFFB0"]))
                sx = x + bw * (0.2 + rng.random() * 0.6)
                sy = top + 30 + rng.random() * bh * 0.4
                if rng.random() < 0.5:
                    g.rectangle([sx - 8, sy, sx + 8, sy + 120], fill=c)
                    d.rectangle([sx - 5, sy + 3, sx + 5, sy + 117], fill=c)
                else:
                    g.rectangle([sx - 60, sy, sx + 60, sy + 26], fill=c)
                    d.rectangle([sx - 57, sy + 3, sx + 57, sy + 23], fill=c)
            x += bw + rng.random() * 8
        img.paste(layer, (0, 0), layer)
        img = ImageChops.screen(img, glow_l.filter(ImageFilter.GaussianBlur(24)))
    return img


def rain_streaks(img, rng, n, alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y, L = rng.random() * W, rng.random() * H, 20 + rng.random() * 50
        d.line([(x, y), (x - L * 0.45, y + L)], fill=(200, 220, 255, alpha), width=1)
    img.paste(layer, (0, 0), layer)
    return img


def neon():
    rng = random.Random(1401)
    horizon = int(H * 0.86)
    img = vgradient([(0, "#07060C"), (0.6, "#1A1030"), (0.86, "#3A1450"), (1, "#0B0A12")])
    img = glow(img, (W * 0.5, horizon), W * 0.5, "#7A1A66", 0.4)
    img = neon_buildings(img, rng, horizon, [("#1A1728", 300, 700, 90, 200, False), ("#0F0D18", 380, 980, 120, 260, True)])
    fog = Image.new("L", img.size, 0)
    ImageDraw.Draw(fog).rectangle([0, horizon - 160, W, horizon + 40], fill=70)
    img = Image.composite(Image.new("RGB", img.size, hexrgb("#3A1450")), img, fog.filter(ImageFilter.GaussianBlur(80)))
    img = fill_below(img, [(0, horizon), (W, horizon)], "#07060C")
    img = rain_streaks(img, rng, 1800, 70)
    return grain(img, 30, rng)


def crowns(d, rng, x, base, h, colors):
    d.rectangle([x - h * 0.04, base - h * 0.45, x + h * 0.04, base], fill=hexrgb("#4A2E1A"))
    for _ in range(9):
        cx = x + rng.gauss(0, h * 0.16)
        cy = base - h * 0.6 + rng.gauss(0, h * 0.13)
        r = h * (0.16 + rng.random() * 0.1)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hexrgb(rng.choice(colors)))


FALL = ["#C2411C", "#D9692E", "#E89A3A", "#F2C46B", "#A8441A", "#8A2E10", "#E2B85A"]


def autumn_road():
    rng = random.Random(1502)
    horizon = int(H * 0.5)
    img = vgradient([(0, "#A9C8DA"), (0.5, "#F6E4C8"), (0.51, "#B5893A"), (1, "#8A6A3A")])
    vx = W * 0.5
    d = ImageDraw.Draw(img)
    d.polygon([(vx - 14, horizon), (vx + 14, horizon), (vx + 620, H), (vx - 620, H)], fill=hexrgb("#5A4A40"))
    for k in range(14):
        t0, t1 = (k / 14) ** 1.8, ((k + 0.5) / 14) ** 1.8
        y0, y1 = horizon + (H - horizon) * t0, horizon + (H - horizon) * t1
        d.polygon([(vx - 2 - 12 * t0, y0), (vx + 2 + 12 * t0, y0), (vx + 2 + 12 * t1, y1), (vx - 2 - 12 * t1, y1)], fill=hexrgb("#E8D8B0"))
    trees = []
    for side in (-1, 1):
        for k in range(14):
            t = (k / 14) ** 1.6
            x = vx + side * (40 + 900 * t) + rng.gauss(0, 20)
            base = horizon + (H - horizon) * t * 0.9 + 10
            trees.append((base, x, 60 + 700 * t))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for base, x, h in sorted(trees):
        crowns(ld, rng, x, base, h, FALL)
    img.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(img)
    for _ in range(900):
        y = horizon + (rng.random() ** 0.7) * (H - horizon)
        t = (y - horizon) / (H - horizon)
        x = vx + (rng.random() - 0.5) * 1300 * t
        r = 1.5 + t * 6
        d.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.6], fill=hexrgb(rng.choice(FALL)))
    return grain(img, 30, rng)


MAKERS = {"arctic-pines": arctic_pines, "autumn-road": autumn_road, "desert-night": desert_night, "ember-lava": ember_lava, "forest": forest, "lavender": lavender, "midnight-galaxy": midnight_galaxy, "mint-lowpoly": mint_lowpoly, "neon": neon, "ocean-abyss": ocean_abyss, "sakura": sakura}

def load_private():
    path = Path(__file__).resolve().parent / "private_wallpapers.py"
    if not path.is_file():
        return
    import importlib.util
    spec = importlib.util.spec_from_file_location("private_wallpapers", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    this = sys.modules[__name__]
    for name, fn in getattr(mod, "MAKERS", {}).items():
        MAKERS[name] = lambda fn=fn: fn(this)


if __name__ == "__main__":
    load_private()
    if sys.argv[1:] == ["--list"]:
        print("\n".join(MAKERS))
        sys.exit(0)
    names = sys.argv[1:] or list(MAKERS)
    OUT.mkdir(parents=True, exist_ok=True)
    for name in names:
        tmp = OUT / f".{name}.jpg.tmp"
        MAKERS[name]().resize(OUT_SIZE, Image.LANCZOS).save(tmp, "JPEG", quality=90, optimize=True, progressive=True)
        tmp.replace(OUT / f"{name}.jpg")
        print(f"{name}.jpg {(OUT / f'{name}.jpg').stat().st_size // 1024} KB")
