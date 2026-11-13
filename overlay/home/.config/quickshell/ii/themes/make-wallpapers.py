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


def midnight():
    rng = random.Random(7)
    img = vgradient([(0, "#060A1C"), (0.55, "#141B45"), (0.82, "#2E2766"), (1, "#3B2A6E")])
    img = glow(img, (W * 0.5, H * 1.05), W * 0.55, "#5B4A9E", 0.55)
    d = ImageDraw.Draw(img)
    for _ in range(900):
        x, y = rng.random() * W, (rng.random() ** 1.6) * H * 0.78
        r = rng.choice([0.6, 0.8, 1.0, 1.2, 1.6, 2.2]) * (1.3 if rng.random() < 0.05 else 1)
        b = rng.randint(150, 255)
        tint = rng.choice([(b, b, b), (b, b, 255), (255, b, int(b * 0.8))])
        d.ellipse([x - r, y - r, x + r, y + r], fill=tint)
    stars = img.filter(ImageFilter.GaussianBlur(2.2))
    img = Image.blend(img, stars, 0.35)
    img = glow(img, (W * 0.78, H * 0.2), 220, "#F5E6B0", 0.18)
    moon = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(moon)
    cx, cy, r = W * 0.78, H * 0.2, 70
    md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    md.ellipse([cx - r + 34, cy - r - 18, cx + r + 34, cy + r - 18], fill=0)
    img = Image.composite(Image.new("RGB", img.size, hexrgb("#F7EBC4")), img, moon.filter(ImageFilter.GaussianBlur(1)))
    img = fill_below(img, ridge(rng, H * 0.86, 70, 2.2), "#120F33", 2)
    img = fill_below(img, ridge(rng, H * 0.93, 45, 3.1, 1.3), "#08071C", 1)
    return grain(img, 40, rng)


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


def arctic():
    rng = random.Random(23)
    img = vgradient([(0, "#89C2D9"), (0.4, "#CAE9F5"), (0.62, "#E6F5FB"), (1, "#CAE9F5")])
    aurora = Image.new("L", img.size, 0)
    ad = ImageDraw.Draw(aurora)
    for i in range(6):
        pts = [(x, H * 0.18 + 60 * math.sin(x / 260 + i * 0.7) + i * 22) for x in range(-40, W + 41, 40)]
        ad.line(pts, fill=60, width=40)
    img = Image.composite(Image.new("RGB", img.size, hexrgb("#9A9CF0")), img, aurora.filter(ImageFilter.GaussianBlur(45)))
    for base, amp, rough, color, cap, blur in [(H * 0.62, 190, 2.6, "#A9D6E5", "#F4FBFE", 3),
                                               (H * 0.75, 230, 3.3, "#61A5C2", "#E6F5FB", 1),
                                               (H * 0.9, 160, 4.1, "#2A6F97", "#CAE9F5", 0)]:
        pts = ridge(rng, base, amp, rough, rng.random())
        img = fill_below(img, pts, color, blur)
        capmask = Image.new("L", img.size, 0)
        cm = ImageDraw.Draw(capmask)
        cm.polygon(pts + [(W + 40, H), (-40, H)], fill=255)
        shifted = [(x, y + amp * 0.45) for x, y in pts]
        cm.polygon(shifted + [(W + 40, H), (-40, H)], fill=0)
        img = Image.composite(Image.new("RGB", img.size, hexrgb(cap)), img,
                              capmask.filter(ImageFilter.GaussianBlur(4 + blur)).point(lambda v: int(v * 0.85)))
    img = fill_below(img, ridge(rng, H * 0.97, 25, 2.0), "#E6F5FB", 2)
    return grain(img, 30, rng)


def mint():
    rng = random.Random(31)
    img = vgradient([(0, "#C7F9CC"), (0.5, "#A8F0B8"), (1, "#80ED99")])
    img = glow(img, (W * 0.2, H * 0.15), 600, "#F2FFF4", 0.6)
    bands = [("#80ED99", 0.42, 90), ("#57CC99", 0.55, 110), ("#38A3A5", 0.68, 120), ("#22577A", 0.82, 130)]
    for i, (color, base, amp) in enumerate(bands):
        ph = rng.random() * 6.28
        pts = [(x, H * base + amp * math.sin(x / W * math.pi * (1.4 + i * 0.35) + ph)
                + amp * 0.35 * math.sin(x / W * math.pi * 4.3 + ph * 2)) for x in range(-40, W + 41, 20)]
        shade = Image.new("L", img.size, 0)
        ImageDraw.Draw(shade).polygon([(x, y - 18) for x, y in pts] + [(W + 40, H), (-40, H)], fill=70)
        img = Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, shade.filter(ImageFilter.GaussianBlur(28)))
        img = fill_below(img, pts, color, 2)
    return grain(img, 30, rng)



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


def reflect(img, horizon, darken, tint, rng, ripple=3.0):
    h = H - horizon
    src = img.crop((0, max(0, horizon - h), W, horizon)).transpose(Image.FLIP_TOP_BOTTOM)
    src = ImageEnhance.Brightness(src.filter(ImageFilter.GaussianBlur(2))).enhance(darken)
    out = Image.new("RGB", (W, h))
    for y in range(0, h, 2):
        shift = int(ripple * (1 + y / h * 3) * math.sin(y * 0.35 + rng.random() * 0.6))
        out.paste(src.crop((0, y, W, min(h, y + 2))), (shift, y))
    out = Image.blend(out, Image.new("RGB", out.size, hexrgb(tint)), 0.25)
    img.paste(out, (0, horizon))
    d = ImageDraw.Draw(img)
    for _ in range(140):
        y = horizon + int((rng.random() ** 1.6) * h)
        x = rng.random() * W
        w = 40 + rng.random() * 220 * (1 + (y - horizon) / h)
        c = mix(hexrgb(tint), (255, 255, 255), 0.35)
        d.line([(x, y), (x + w, y)], fill=c, width=1)
    return img


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


def midnight_city():
    rng = random.Random(202)
    horizon = int(H * 0.74)
    img = vgradient([(0, "#060A1C"), (0.5, "#141B45"), (0.74, "#3B2F72"), (1, "#141B45")])
    img = glow(img, (W * 0.5, horizon), W * 0.5, "#6B4FA0", 0.45)
    d = ImageDraw.Draw(img)
    for _ in range(500):
        x, y = rng.random() * W, (rng.random() ** 1.5) * horizon * 0.7
        r = rng.choice([0.6, 0.9, 1.2, 1.6])
        b = rng.randint(150, 240)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, 255))
    img = glow(img, (W * 0.2, H * 0.18), 160, "#F7EBC4", 0.25)
    d = ImageDraw.Draw(img)
    d.ellipse([W * 0.2 - 55, H * 0.18 - 55, W * 0.2 + 55, H * 0.18 + 55], fill=hexrgb("#F2E6C2"))
    for layer_i, (color, hmin, hmax, wmin, wmax, lit) in enumerate([
            ("#252C5C", 180, 420, 60, 140, 0.0), ("#161C42", 240, 560, 70, 170, 0.18), ("#0B0F26", 120, 360, 90, 210, 0.3)]):
        x = -rng.random() * 80
        while x < W:
            bw = wmin + rng.random() * (wmax - wmin)
            bh = hmin + rng.random() * (hmax - hmin)
            top = horizon - bh
            d.rectangle([x, top, x + bw, horizon], fill=hexrgb(color))
            if rng.random() < 0.25:
                d.rectangle([x + bw * 0.45, top - 40, x + bw * 0.5, top], fill=hexrgb(color))
                d.ellipse([x + bw * 0.47 - 3, top - 44, x + bw * 0.47 + 3, top - 38], fill=(255, 90, 90))
            if lit:
                for wy in range(int(top + 14), horizon - 10, 22):
                    for wx in range(int(x + 10), int(x + bw - 14), 18):
                        if rng.random() < lit:
                            warm = mix(hexrgb("#F5D687"), hexrgb("#FFF4D6"), rng.random())
                            dim = 0.55 + rng.random() * 0.45
                            d.rectangle([wx, wy, wx + 8, wy + 11], fill=mix((20, 24, 60), warm, dim))
            x += bw + rng.random() * 12
    img = reflect(img, horizon, 0.55, "#141B45", rng, 4)
    return grain(img, 35, rng)


def forest_rays():
    rng = random.Random(303)
    img = vgradient([(0, "#1B4332"), (0.5, "#2D6A4F"), (0.8, "#1B4332"), (1, "#081C15")])
    img = glow(img, (W * 0.78, -100), 900, "#B7E4A0", 0.55)
    for color, count, wmin, wmax, blur in [("#4F8A6B", 26, 18, 40, 6), ("#2D6A4F", 16, 40, 80, 2), ("#0E2A1F", 9, 90, 170, 0)]:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i in range(count):
            x = (i + rng.random()) * W / count
            w = wmin + rng.random() * (wmax - wmin)
            lean = (rng.random() - 0.5) * 60
            d.polygon([(x - w * 0.4 + lean, -20), (x + w * 0.4 + lean, -20), (x + w * 0.6, H), (x - w * 0.6, H)], fill=hexrgb(color))
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.paste(layer, (0, 0), layer)
        fog = Image.new("L", img.size, 0)
        ImageDraw.Draw(fog).rectangle([0, H * 0.55, W, H], fill=40)
        img = Image.composite(Image.new("RGB", img.size, hexrgb("#95D5B2")), img, fog.filter(ImageFilter.GaussianBlur(160)))
    rays = Image.new("RGB", img.size, (0, 0, 0))
    rd = ImageDraw.Draw(rays)
    sx, sy = W * 0.8, -250
    for _ in range(9):
        a = math.radians(100 + rng.random() * 55)
        spread = math.radians(1.2 + rng.random() * 2.4)
        L = H * 2
        rd.polygon([(sx, sy), (sx + L * math.cos(a - spread), sy + L * math.sin(a - spread)),
                    (sx + L * math.cos(a + spread), sy + L * math.sin(a + spread))], fill=(52 + rng.randint(0, 20), 70, 34))
    img = ImageChops.screen(img, rays.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(img)
    for _ in range(500):
        x, y = rng.random() * W, rng.random() * H * 0.9
        r = 0.8 + rng.random() * 1.6
        d.ellipse([x - r, y - r, x + r, y + r], fill=(246, 236, 190))
    img = fill_below(img, ridge(rng, H * 0.9, 25, 3.0), "#081C15", 2)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fd = ImageDraw.Draw(layer)
    for _ in range(26):
        bx, by = rng.random() * W, H - rng.random() * 40
        length = 160 + rng.random() * 220
        a0 = math.radians(-90 + (rng.random() - 0.5) * 100)
        bend = (rng.random() - 0.5) * 0.9
        pts = []
        for k in range(24):
            t = k / 23
            a = a0 + bend * t
            pts.append((bx + math.cos(a) * length * t, by + math.sin(a) * length * t))
        col = rng.choice(["#1B4332", "#2D6A4F", "#40916C"])
        fd.line(pts, fill=hexrgb(col), width=4)
        for k in range(2, 23):
            x, y = pts[k]
            a = a0 + bend * k / 23
            leaf = length * 0.16 * (1 - k / 26)
            for sgn in (-1, 1):
                ex = x + math.cos(a + sgn * 1.1) * leaf
                ey = y + math.sin(a + sgn * 1.1) * leaf
                fd.line([(x, y), (ex, ey)], fill=hexrgb(col), width=3)
    img.paste(layer, (0, 0), layer)
    return grain(img, 40, rng)


def forest_lake():
    rng = random.Random(404)
    horizon = int(H * 0.58)
    img = vgradient([(0, "#1B4332"), (0.35, "#52B788"), (0.52, "#F4C27A"), (0.58, "#E9C46A"), (1, "#1B4332")])
    img = glow(img, (W * 0.62, horizon - 30), 260, "#FFF4D6", 0.7)
    img = fill_below(img, ridge(rng, horizon - 150, 90, 1.6), "#4F8A6B", 4)
    img = fill_below(img, ridge(rng, horizon - 70, 60, 2.4, 1.1), "#2D6A4F", 2)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, horizon - 20, W, horizon], fill=hexrgb("#0E2A1F"))
    x = -20.0
    while x < W + 40:
        h = 90 + rng.random() * 160
        pine(d, x, horizon, h, "#0E2A1F")
        x += 18 + rng.random() * 34
    img.paste(layer, (0, 0), layer)
    mist = Image.new("L", img.size, 0)
    ImageDraw.Draw(mist).rectangle([0, horizon - 40, W, horizon + 30], fill=90)
    img = Image.composite(Image.new("RGB", img.size, hexrgb("#E8F5E0")), img, mist.filter(ImageFilter.GaussianBlur(50)))
    img = img.crop((0, 0, W, horizon)).resize((W, horizon))
    full = Image.new("RGB", (W, H))
    full.paste(img, (0, 0))
    full = reflect(full, horizon, 0.7, "#1B4332", rng, 3)
    return grain(full, 35, rng)


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


def arctic_icebergs():
    rng = random.Random(505)
    horizon = int(H * 0.6)
    img = vgradient([(0, "#B8E1F1"), (0.45, "#E6F5FB"), (0.6, "#F4FBFE"), (0.62, "#89C2D9"), (1, "#2A6F97")])
    img = glow(img, (W * 0.3, horizon - 40), 300, "#FFFFFF", 0.6)
    img = fill_below(img, ridge(rng, horizon - 40, 30, 1.4), "#CAE9F5", 6)
    img = img.crop((0, 0, W, horizon)).resize((W, horizon))
    sky = img
    full = Image.new("RGB", (W, H))
    full.paste(sky, (0, 0))
    bergs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bergs)
    for i in range(6):
        cx = (i + 0.3 + rng.random() * 0.5) * W / 6
        bw = 160 + rng.random() * 360
        bh = 80 + rng.random() * 260
        n = 7
        pts = [(cx - bw / 2, horizon)]
        for k in range(1, n):
            t = k / n
            pts.append((cx - bw / 2 + bw * t + (rng.random() - 0.5) * bw * 0.08,
                        horizon - bh * math.sin(math.pi * t) ** 0.6 * (0.7 + rng.random() * 0.35)))
        pts.append((cx + bw / 2, horizon))
        bd.polygon(pts, fill=hexrgb("#F4FBFE"))
        peak = max(range(1, n), key=lambda k: horizon - pts[k][1])
        shade = [pts[peak]] + pts[peak + 1:] + [(pts[peak][0] + bw * 0.05, horizon)]
        bd.polygon(shade, fill=hexrgb("#A9D6E5"))
        bd.line(pts, fill=hexrgb("#DDF2FF"), width=2)
    full.paste(bergs, (0, 0), bergs)
    sea = vgradient([(0, "#61A5C2"), (0.6, "#2A6F97"), (1, "#014F86")]).crop((0, horizon, W, H))
    refl = bergs.crop((0, max(0, horizon - (H - horizon)), W, horizon)).transpose(Image.FLIP_TOP_BOTTOM)
    sea_img = sea.copy()
    sea_img.paste(Image.new("RGB", refl.size, hexrgb("#CAE9F5")), (0, 0), refl.split()[3].point(lambda v: int(v * 0.55)))
    rows = Image.new("RGB", sea_img.size)
    for y in range(0, sea_img.size[1], 2):
        shift = int(3 * (1 + y / sea_img.size[1] * 3) * math.sin(y * 0.4))
        rows.paste(sea_img.crop((0, y, W, y + 2)), (shift, y))
    full.paste(rows.filter(ImageFilter.GaussianBlur(1.2)), (0, horizon))
    d = ImageDraw.Draw(full)
    for _ in range(40):
        x, y = rng.random() * W, horizon + 30 + rng.random() * (H - horizon - 40)
        w = 10 + rng.random() * 50 * (y - horizon) / (H - horizon)
        d.polygon([(x, y), (x + w, y), (x + w * 0.7, y - w * 0.25), (x + w * 0.2, y - w * 0.3)], fill=hexrgb("#F4FBFE"))
    for _ in range(160):
        y = horizon + int((rng.random() ** 1.5) * (H - horizon))
        x = rng.random() * W
        d.line([(x, y), (x + 40 + rng.random() * 200, y)], fill=hexrgb("#B8E1F1"), width=1)
    return grain(full, 25, rng)


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


def mint_bokeh():
    rng = random.Random(707)
    img = vgradient([(0, "#E3FCE6"), (0.45, "#C7F9CC"), (0.8, "#80ED99"), (1, "#57CC99")])
    img = glow(img, (W * 0.8, H * 0.2), 700, "#FFFFFF", 0.5)
    for count, rmin, rmax, blur, amin, amax, colors in [
            (26, 120, 260, 40, 40, 90, ["#FFFFFF", "#E3FCE6", "#C7F9CC", "#80ED99"]),
            (60, 40, 110, 8, 50, 120, ["#FFFFFF", "#C7F9CC", "#80ED99", "#57CC99"]),
            (90, 10, 34, 1.5, 90, 180, ["#FFFFFF", "#80ED99", "#57CC99", "#38A3A5"])]:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for _ in range(count):
            x, y = rng.random() * W, rng.random() * H
            r = rmin + rng.random() * (rmax - rmin)
            c = hexrgb(rng.choice(colors))
            a = rng.randint(amin, amax)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (a,), outline=c + (min(255, a + 50),), width=max(1, int(r * 0.06)))
        img.paste(layer.filter(ImageFilter.GaussianBlur(blur)), (0, 0), layer.filter(ImageFilter.GaussianBlur(blur)))
    return grain(img, 25, rng)


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


def desert():
    rng = random.Random(909)
    img = vgradient([(0, "#3E6E7A"), (0.35, "#C98B6B"), (0.55, "#F2C46B"), (0.62, "#F5DDB0"), (1, "#C9693F")])
    img = glow(img, (W * 0.7, H * 0.56), 260, "#FFF4D6", 0.8)
    for base, amp, color, shadow, crest, blur in [(H * 0.62, 40, "#E0B07A", "#C48A5A", "#F2CE96", 3),
                                                  (H * 0.72, 70, "#D9A066", "#B5713F", "#F2C690", 1),
                                                  (H * 0.84, 90, "#C9824E", "#9E5A2E", "#E8B078", 0),
                                                  (H * 0.97, 110, "#B5693A", "#874420", "#D99A62", 0)]:
        img = dune(img, rng, base, amp, color, shadow, crest, blur)
    return grain(img, 35, rng)


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


def desert_mesa():
    rng = random.Random(911)
    horizon = H * 0.7
    img = vgradient([(0, "#6FA3B0"), (0.45, "#E8C39A"), (0.7, "#F2D3A8"), (1, "#C9693F")])
    img = glow(img, (W * 0.25, H * 0.3), 300, "#FFF4D6", 0.5)
    plan = [(0, "#D9A07A", "#C4865E", [(0.18, 0.34, 210), (0.62, 0.22, 170), (0.88, 0.14, 230)]),
            (1, "#C9693F", "#A34A28", [(0.3, 0.2, 360), (0.74, 0.3, 300)])]
    for depth, color, shade, mesas in plan:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for fx, fw, bh in mesas:
            cx, topw = fx * W, fw * W
            top = horizon - bh
            cliff = top + bh * 0.62
            l, r = cx - topw / 2, cx + topw / 2
            jag = [(l + (r - l) * k / 12, top + (rng.random() - 0.5) * 6) for k in range(13)]
            body = [(l - bh * 0.03, cliff)] + jag + [(r + bh * 0.04, cliff)]
            d.polygon(body + [(r + bh * 0.04, horizon), (l - bh * 0.03, horizon)], fill=hexrgb(color))
            d.polygon([(l - bh * 0.03, cliff), (l - bh * 0.5, horizon), (r + bh * 0.55, horizon), (r + bh * 0.04, cliff)],
                      fill=hexrgb(color))
            d.polygon([(r - topw * 0.18, top), (r, top), (r + bh * 0.04, cliff), (r + bh * 0.55, horizon), (r - topw * 0.1, horizon)],
                      fill=hexrgb(shade))
            for k in range(1, 6):
                y = top + (cliff - top) * k / 6
                d.line([(l - bh * 0.03 * k / 6, y), (r + bh * 0.04 * k / 6, y)], fill=hexrgb(shade), width=2)
            for _ in range(18):
                x = l - bh * 0.4 + rng.random() * (topw + bh * 0.9)
                y = cliff + rng.random() * (horizon - cliff)
                rr = 3 + rng.random() * 7
                d.ellipse([x - rr, y - rr * 0.6, x + rr, y + rr * 0.6], fill=hexrgb(shade))
        if depth == 0:
            layer = layer.filter(ImageFilter.GaussianBlur(2))
        img.paste(layer, (0, 0), layer)
    img = fill_below(img, ridge(rng, horizon + 10, 10, 2.2), "#D9A066", 1)
    img = dune(img, rng, H * 0.9, 60, "#C9824E", "#9E5A2E", "#E8B078")
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(layer)
    for x, h in ((W * 0.08, 240), (W * 0.93, 280)):
        saguaro(cd, x, H * 0.98, h, hexrgb("#4A5A2A"))
    for _ in range(60):
        x, y = rng.random() * W, H * 0.92 + rng.random() * H * 0.08
        r = 6 + rng.random() * 16
        cd.ellipse([x - r, y - r * 0.6, x + r, y + r * 0.4], fill=hexrgb(rng.choice(["#6E7A3A", "#8A8A4A", "#5A6A30"])))
    img.paste(layer, (0, 0), layer)
    return grain(img, 30, rng)


MAKERS = {"midnight": midnight, "midnight-galaxy": midnight_galaxy, "midnight-city": midnight_city,
          "forest": forest, "forest-rays": forest_rays, "forest-lake": forest_lake,
          "arctic": arctic, "arctic-icebergs": arctic_icebergs, "arctic-pines": arctic_pines,
          "mint": mint, "mint-bokeh": mint_bokeh, "mint-lowpoly": mint_lowpoly,
          "desert": desert, "desert-night": desert_night, "desert-mesa": desert_mesa}

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
