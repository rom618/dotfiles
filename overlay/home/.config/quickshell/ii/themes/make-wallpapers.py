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


def sakura_fuji():
    rng = random.Random(1002)
    img = vgradient([(0, "#A9C8E8"), (0.55, "#F6E1EA"), (0.75, "#FBE4EC"), (1, "#E9B0C4")])
    cx, base, top = W * 0.48, H * 0.78, H * 0.28
    mt = [(cx - 900, base), (cx - 160, top + 40), (cx - 90, top), (cx + 90, top), (cx + 170, top + 40), (cx + 950, base)]
    img = fill_below(img, [(0, base)] + mt + [(W, base)], "#7A8FB5", 2)
    snow = Image.new("L", img.size, 0)
    sd = ImageDraw.Draw(snow)
    cap = [(cx - 160, top + 40), (cx - 90, top), (cx + 90, top), (cx + 170, top + 40)]
    jag = [(cx + 260, top + 190), (cx + 170, top + 150), (cx + 110, top + 220), (cx + 30, top + 160), (cx - 50, top + 230),
           (cx - 130, top + 160), (cx - 230, top + 200)]
    sd.polygon(cap + jag, fill=255)
    img = Image.composite(Image.new("RGB", img.size, hexrgb("#F7F9FF")), img, snow.filter(ImageFilter.GaussianBlur(2)))
    img = fill_below(img, ridge(rng, H * 0.82, 30, 2.0), "#C9A3C0", 3)
    img = fill_below(img, ridge(rng, H * 0.9, 25, 3.0, 0.3), "#B07A9E", 1)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tips = []
    branch(d, rng, W + 30, -20, math.pi * 0.72, 600, 36, 6, "#4A2E32", tips)
    img.paste(layer, (0, 0), layer)
    img = blossoms(img, rng, tips, ["#F8B7CD", "#FBD3E0", "#E07A9E"], 24, 14)
    img = baked_petals(img, rng, 160, ["#F8B7CD", "#FBD3E0"])
    return grain(img, 25, rng)


def sakura_dusk():
    rng = random.Random(1003)
    img = vgradient([(0, "#3A2450"), (0.45, "#9A5A8A"), (0.7, "#F2A6B8"), (1, "#5A2E4A")])
    img = glow(img, (W * 0.3, H * 0.62), 300, "#FFD6C2", 0.6)
    img = fill_below(img, ridge(rng, H * 0.78, 50, 1.6), "#4A2A48", 3)
    d = ImageDraw.Draw(img)
    px, pb = W * 0.7, H * 0.8
    for k in range(5):
        w = 190 - k * 30
        y = pb - 60 - k * 95
        d.rectangle([px - w * 0.55, y, px + w * 0.55, y + 60], fill=hexrgb("#2A1426"))
        d.polygon([(px - w, y + 8), (px + w, y + 8), (px + w * 0.7, y - 22), (px - w * 0.7, y - 22)], fill=hexrgb("#2A1426"))
    d.line([(px, pb - 60 - 4 * 95 - 22), (px, pb - 60 - 4 * 95 - 120)], fill=hexrgb("#2A1426"), width=8)
    img = fill_below(img, ridge(rng, H * 0.9, 20, 2.0), "#2A1426", 1)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tips = []
    branch(d, rng, W * 0.18, H * 0.92, -math.pi / 2 - 0.05, 300, 30, 6, "#2A1426", tips)
    img.paste(layer, (0, 0), layer)
    img = blossoms(img, rng, tips, ["#F8B7CD", "#F09AB8", "#FBD3E0"], 30, 18)
    return grain(img, 30, rng)


def seaweed(d, rng, x, base, h, color):
    pts = [(x + 18 * math.sin(t / 5 + rng.random()) * t / 20, base - h * t / 20) for t in range(21)]
    d.line(pts, fill=hexrgb(color), width=10)
    for t in range(3, 20, 3):
        px, py = pts[t]
        d.ellipse([px - 14, py - 6, px + 14, py + 6], fill=hexrgb(color))


def ocean_floor(img, rng, colors):
    img = fill_below(img, ridge(rng, H * 0.9, 30, 1.8), colors[0], 2)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(24):
        seaweed(d, rng, rng.random() * W, H + 10, 140 + rng.random() * 300, rng.choice(colors[1:]))
    img.paste(layer, (0, 0), layer)
    return img


def ocean():
    rng = random.Random(1101)
    img = vgradient([(0, "#2E9AB5"), (0.25, "#0E5A73"), (0.7, "#04263A"), (1, "#021B2A")])
    rays = Image.new("RGB", img.size, (0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for _ in range(12):
        x = rng.random() * W
        w = 30 + rng.random() * 90
        rd.polygon([(x - w, -10), (x + w, -10), (x + w * 3 + 200, H), (x - w * 2 + 200, H)], fill=(30, 70, 80))
    img = ImageChops.screen(img, rays.filter(ImageFilter.GaussianBlur(50)))
    d = ImageDraw.Draw(img)
    for _ in range(260):
        x, y, r = rng.random() * W, rng.random() * H, 1 + rng.random() * 5
        d.ellipse([x - r, y - r, x + r, y + r], outline=(200, 240, 250), width=1)
    img = ocean_floor(img, rng, ["#0A2E3E", "#0E4A3A", "#1B5A4A", "#0B3A48"])
    return grain(img, 30, rng)


def fish(d, x, y, s, color, flip):
    k = -1 if flip else 1
    d.ellipse([x - 22 * s, y - 9 * s, x + 22 * s, y + 9 * s], fill=hexrgb(color))
    d.polygon([(x - 18 * s * k, y), (x - 36 * s * k, y - 12 * s), (x - 36 * s * k, y + 12 * s)], fill=hexrgb(color))
    d.ellipse([x + 12 * s * k - 2 * s, y - 3 * s, x + 12 * s * k + 2 * s, y + 1 * s], fill=(20, 20, 30))


def ocean_reef():
    rng = random.Random(1102)
    img = vgradient([(0, "#4FB3C9"), (0.4, "#1B7A93"), (1, "#0C3D57")])
    img = glow(img, (W * 0.5, -200), 900, "#BFF0F7", 0.5)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(9):
        cx, cy = rng.random() * W, H * (0.25 + rng.random() * 0.4)
        color = rng.choice(["#F2B880", "#FFD27A", "#8FD3E6", "#F28B9A"])
        flip = rng.random() < 0.5
        for _ in range(8 + rng.randint(0, 10)):
            fish(d, cx + rng.gauss(0, 130), cy + rng.gauss(0, 60), 1.3 + rng.random() * 0.8, color, flip)
    img.paste(layer, (0, 0), layer)
    img = fill_below(img, ridge(rng, H * 0.82, 40, 2.0), "#0E4A5A", 2)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(26):
        x, base = rng.random() * W, H * (0.86 + rng.random() * 0.12)
        kind = rng.random()
        col = rng.choice(["#F28B74", "#FF9E7A", "#E86A8A", "#F2B880", "#C7A6FF", "#FFD27A"])
        if kind < 0.4:
            tips = []
            branch(d, rng, x, base, -math.pi / 2 + (rng.random() - 0.5) * 0.4, 110 + rng.random() * 80, 14, 4, col, tips)
            for tx, ty in tips:
                d.ellipse([tx - 7, ty - 7, tx + 7, ty + 7], fill=hexrgb(col))
        elif kind < 0.7:
            r = 90 + rng.random() * 90
            d.pieslice([x - r, base - r, x + r, base + r], 200, 340, fill=hexrgb(col))
            for k in range(10):
                a = math.radians(200 + k * 14)
                d.line([(x, base), (x + r * math.cos(a), base + r * math.sin(a))], fill=hexrgb("#7A2A3A"), width=2)
        else:
            r = 50 + rng.random() * 60
            d.ellipse([x - r, base - r * 0.8, x + r, base + r * 0.4], fill=hexrgb(col))
            for _ in range(30):
                a, rr = rng.random() * math.tau, rng.random() * r * 0.8
                d.ellipse([x + rr * math.cos(a) - 3, base - r * 0.2 + rr * 0.5 * math.sin(a) - 3,
                           x + rr * math.cos(a) + 3, base - r * 0.2 + rr * 0.5 * math.sin(a) + 3], fill=hexrgb("#FFFFFF"))
    img.paste(layer, (0, 0), layer)
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


def ember():
    rng = random.Random(1201)
    img = vgradient([(0, "#0A0606"), (0.5, "#2A0E0A"), (0.8, "#6A1E10"), (1, "#1A0A08")])
    cx, top, base = W * 0.5, H * 0.38, H * 0.9
    img = glow(img, (cx, top), 420, "#FF6A1A", 0.6)
    plume = [([cx - 160 + rng.random() * 120 + k * 30 - 300, top - 120 - k * 70 - 120, cx + 160 + k * 30 - 300 + rng.random() * 160,
               top - 120 - k * 70 + 120], (40, 26, 24)) for k in range(9)]
    img = ImageChops.subtract(img, blob_layer(plume, 40))
    img = fill_below(img, [(0, base), (cx - 760, base - 40), (cx - 130, top), (cx + 130, top), (cx + 780, base - 30), (W, base)],
                     "#1E100C", 1)
    lava = Image.new("RGB", img.size, (0, 0, 0))
    ld = ImageDraw.Draw(lava)
    for k in range(6):
        x, y = cx - 100 + k * 40, top + 5
        pts = [(x, y)]
        for t in range(40):
            x += (rng.random() - 0.5) * 24 + (k - 2.5) * 6
            y += 14
            pts.append((x, y))
        ld.line(pts, fill=(255, 110, 30), width=10)
    ld.ellipse([cx - 130, top - 20, cx + 130, top + 20], fill=(255, 170, 60))
    img = ImageChops.screen(img, lava.filter(ImageFilter.GaussianBlur(14)))
    img = ImageChops.screen(img, lava.filter(ImageFilter.GaussianBlur(2)))
    d = ImageDraw.Draw(img)
    for _ in range(300):
        x, y = cx + rng.gauss(0, 260), top - rng.random() * H * 0.35
        r = 1 + rng.random() * 2.5
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, rng.randint(140, 220), 80))
    img = fill_below(img, ridge(rng, H * 0.94, 20, 2.5), "#0A0606", 1)
    return grain(img, 35, rng)


def ember_campfire():
    rng = random.Random(1202)
    img = vgradient([(0, "#06080C"), (0.6, "#120C0A"), (1, "#2A140C")])
    fx, fy = W * 0.5, H * 0.86
    img = glow(img, (fx, fy - 60), 700, "#FF7A2A", 0.55)
    for base, color, count, blur in [(H * 0.7, "#1A120E", 26, 3), (H * 0.82, "#0E0906", 16, 0)]:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i in range(count):
            x = (i + rng.random()) * W / count
            if abs(x - fx) < 260:
                continue
            pine(d, x, base, 260 + rng.random() * 260, color)
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.paste(layer, (0, 0), layer)
    img = fill_below(img, ridge(rng, H * 0.88, 10, 2.0), "#24140C", 2)
    d = ImageDraw.Draw(img)
    for a in (-0.35, 0.35, 0):
        d.line([(fx - 120 * math.cos(a), fy + 20 + 40 * math.sin(a)), (fx + 120 * math.cos(a), fy + 20 - 40 * math.sin(a))],
               fill=hexrgb("#4A2A18"), width=26)
    flame = Image.new("RGB", img.size, (0, 0, 0))
    fd = ImageDraw.Draw(flame)
    for w, h, c in ((110, 260, (200, 60, 10)), (80, 210, (255, 120, 20)), (52, 150, (255, 190, 60)), (26, 90, (255, 240, 170))):
        for k in range(3):
            ox = (k - 1) * w * 0.35
            fd.polygon([(fx + ox - w * 0.5, fy + 10), (fx + ox + w * 0.5, fy + 10), (fx + ox + w * 0.2, fy - h * 0.5),
                        (fx + ox, fy - h * (0.8 + 0.2 * (k == 1))), (fx + ox - w * 0.2, fy - h * 0.5)], fill=c)
    img = ImageChops.screen(img, flame.filter(ImageFilter.GaussianBlur(8)))
    img = ImageChops.screen(img, flame.filter(ImageFilter.GaussianBlur(1)))
    d = ImageDraw.Draw(img)
    for _ in range(140):
        x, y = fx + rng.gauss(0, 120), fy - 120 - rng.random() * H * 0.6
        r = 1 + rng.random() * 2.2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, rng.randint(150, 230), 90))
    return grain(img, 35, rng)


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


def lavender_moon():
    rng = random.Random(1302)
    img = vgradient([(0, "#140F24"), (0.6, "#2C2348"), (1, "#403466")])
    d = ImageDraw.Draw(img)
    for _ in range(700):
        x, y, r = rng.random() * W, rng.random() * H * 0.6, rng.choice([0.6, 0.9, 1.3])
        d.ellipse([x - r, y - r, x + r, y + r], fill=(230, 220, 255))
    img = glow(img, (W * 0.7, H * 0.28), 380, "#E8DDFF", 0.35)
    d = ImageDraw.Draw(img)
    d.ellipse([W * 0.7 - 130, H * 0.28 - 130, W * 0.7 + 130, H * 0.28 + 130], fill=hexrgb("#F2ECFF"))
    for cx, cy, r in ((W * 0.7 - 40, H * 0.28 - 30, 26), (W * 0.7 + 50, H * 0.28 + 40, 18), (W * 0.7 - 10, H * 0.28 + 60, 12)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hexrgb("#DCD2F2"))
    for base, amp, color in ((H * 0.66, 70, "#352B56"), (H * 0.76, 90, "#2A2246"), (H * 0.88, 70, "#1F1836")):
        img = fill_below(img, ridge(rng, base, amp, 1.8, rng.random()), color, 2)
    glows = []
    d = ImageDraw.Draw(img)
    for _ in range(70):
        x, y = rng.random() * W, H * (0.55 + rng.random() * 0.4)
        glows.append(([x - 22, y - 22, x + 22, y + 22], "#D8F27A"))
    img = ImageChops.screen(img, ImageEnhance.Brightness(blob_layer(glows, 10)).enhance(0.7))
    d = ImageDraw.Draw(img)
    for (box, _) in glows:
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        d.ellipse([cx - 2.5, cy - 2.5, cx + 2.5, cy + 2.5], fill=(255, 252, 210))
    return grain(img, 30, rng)


def lavender_waves():
    rng = random.Random(1303)
    img = vgradient([(0, "#2C2348"), (0.5, "#4E3A8A"), (1, "#1C1630")])
    img = glow(img, (W * 0.25, H * 0.2), 600, "#C7A6FF", 0.35)
    bands = [("#4A3F70", 0.4, 90), ("#6B4FB8", 0.52, 110), ("#8E80BF", 0.63, 100), ("#A7C79A", 0.74, 70), ("#352B56", 0.86, 120)]
    for i, (color, base, amp) in enumerate(bands):
        ph = rng.random() * 6.28
        pts = [(x, H * base + amp * math.sin(x / W * math.pi * (1.3 + i * 0.3) + ph)
                + amp * 0.3 * math.sin(x / W * math.pi * 4.1 + ph * 2)) for x in range(-40, W + 41, 20)]
        shade = Image.new("L", img.size, 0)
        ImageDraw.Draw(shade).polygon([(x, y - 16) for x, y in pts] + [(W + 40, H), (-40, H)], fill=80)
        img = Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, shade.filter(ImageFilter.GaussianBlur(26)))
        img = fill_below(img, pts, color, 2)
    d = ImageDraw.Draw(img)
    for _ in range(40):
        x, y, r = rng.random() * W, rng.random() * H * 0.5, 1 + rng.random() * 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=hexrgb("#F2C46B"))
    return grain(img, 25, rng)


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


def neon_grid():
    rng = random.Random(1402)
    horizon = int(H * 0.6)
    img = vgradient([(0, "#0B0A12"), (0.35, "#2A0E4A"), (0.6, "#B0168C"), (0.61, "#0B0A12"), (1, "#14082A")])
    sun = Image.new("RGB", (700, 700), (0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for y in range(700):
        t = y / 700
        sd.line([(0, y), (700, y)], fill=mix(hexrgb("#FFE45E"), hexrgb("#FF4FD8"), t))
    mask = Image.new("L", (700, 700), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, 700, 700], fill=255)
    for k in range(7):
        y = 380 + k * 45
        md.rectangle([0, y, 700, y + 6 + k * 3], fill=0)
    img = glow(img, (W / 2, horizon - 200), 520, "#FF4FD8", 0.45)
    img.paste(sun, (int(W / 2 - 350), int(horizon - 560)), mask)
    img = fill_below(img, ridge(rng, horizon, 90, 1.6), "#14082A", 1)
    d = ImageDraw.Draw(img)
    d.rectangle([0, horizon, W, H], fill=hexrgb("#0E0620"))
    grid = Image.new("RGB", img.size, (0, 0, 0))
    gd = ImageDraw.Draw(grid)
    vx = W / 2
    for k in range(-30, 31):
        gd.line([(vx + k * 8, horizon), (vx + k * 220, H)], fill=(255, 79, 216), width=2)
    for k in range(1, 22):
        y = horizon + (H - horizon) * (k / 21) ** 2.2
        gd.line([(0, y), (W, y)], fill=(255, 79, 216), width=2)
    img = ImageChops.screen(img, grid.filter(ImageFilter.GaussianBlur(4)))
    img = ImageChops.screen(img, grid)
    return grain(img, 25, rng)


def neon_street():
    rng = random.Random(1403)
    horizon = int(H * 0.62)
    img = vgradient([(0, "#07060C"), (0.6, "#1A1030"), (1, "#0B0A12")])
    vx = W * 0.5
    d = ImageDraw.Draw(img)
    left = [(0, 0), (vx - 260, horizon - 330), (vx - 260, horizon + 20), (0, H)]
    right = [(W, 0), (vx + 260, horizon - 330), (vx + 260, horizon + 20), (W, H)]
    d.polygon(left, fill=hexrgb("#262040"))
    d.polygon(right, fill=hexrgb("#1E1934"))
    d.rectangle([vx - 260, horizon - 330, vx + 260, horizon + 20], fill=hexrgb("#120F22"))
    for k in range(1, 9):
        t = k / 9
        for side, poly in ((-1, left), (1, right)):
            x0 = poly[0][0] + (poly[1][0] - poly[0][0]) * t
            y_top = poly[0][1] + (poly[1][1] - poly[0][1]) * t
            y_bot = poly[3][1] + (poly[2][1] - poly[3][1]) * t
            d.line([(x0, y_top), (x0, y_bot)], fill=hexrgb("#3A3260"), width=max(1, int(4 * (1 - t))))
            for j in range(4):
                if rng.random() < 0.5:
                    wy = y_top + (y_bot - y_top) * (0.15 + j * 0.18)
                    ww = 30 * (1 - t) + 4
                    d.rectangle([x0 + 6 * -side, wy, x0 + (6 + ww) * -side if side < 0 else x0 - 6, wy + ww * 0.7],
                                fill=hexrgb(rng.choice(["#FFE45E", "#3EE6FF", "#2B2642"])))
    d.line([left[1], left[2]], fill=hexrgb("#4A4080"), width=3)
    d.line([right[1], right[2]], fill=hexrgb("#4A4080"), width=3)
    glow_l = Image.new("RGB", img.size, (0, 0, 0))
    g = ImageDraw.Draw(glow_l)
    for side in (-1, 1):
        for k in range(7):
            t = k / 7
            x = vx + side * (260 + (W / 2 - 260) * (1 - t) ** 1.5 * 0.9)
            y = horizon - 330 * (1 - t) * 0.3 - 250 - t * 300
            s = 0.35 + (1 - t) * 0.9
            c = hexrgb(rng.choice(["#FF4FD8", "#3EE6FF", "#FFE45E", "#FF5F87", "#5FFFB0"]))
            box = [x - 70 * s, y, x + 70 * s, y + 34 * s] if rng.random() < 0.5 else [x - 12 * s, y - 60 * s, x + 12 * s, y + 90 * s]
            g.rectangle(box, fill=c)
            d.rectangle(box, fill=c)
    img = ImageChops.screen(img, glow_l.filter(ImageFilter.GaussianBlur(30)))
    img = glow(img, (vx, horizon - 100), 300, "#3A1450", 0.5)
    img = reflect(img, horizon, 0.8, "#13111E", rng, 5)
    img = rain_streaks(img, rng, 2200, 80)
    return grain(img, 30, rng)


def crowns(d, rng, x, base, h, colors):
    d.rectangle([x - h * 0.04, base - h * 0.45, x + h * 0.04, base], fill=hexrgb("#4A2E1A"))
    for _ in range(9):
        cx = x + rng.gauss(0, h * 0.16)
        cy = base - h * 0.6 + rng.gauss(0, h * 0.13)
        r = h * (0.16 + rng.random() * 0.1)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=hexrgb(rng.choice(colors)))


FALL = ["#C2411C", "#D9692E", "#E89A3A", "#F2C46B", "#A8441A", "#8A2E10", "#E2B85A"]


def autumn():
    rng = random.Random(1501)
    img = vgradient([(0, "#9EC3DA"), (0.5, "#F4E3CF"), (1, "#E8C9A6")])
    for base, size, count, blur, dim in ((H * 0.62, 90, 40, 3, 0.55), (H * 0.76, 150, 26, 1, 0.8), (H * 0.94, 260, 14, 0, 1)):
        img = fill_below(img, ridge(rng, base, 50, 1.8, rng.random()), "#8A6A3A", blur)
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        for i in range(count):
            crowns(d, rng, (i + rng.random()) * W / count, base + 20, size * (0.8 + rng.random() * 0.5), FALL)
        if blur:
            layer = layer.filter(ImageFilter.GaussianBlur(blur))
        img.paste(layer, (0, 0), layer)
        if dim < 1:
            haze = Image.new("L", img.size, 0)
            ImageDraw.Draw(haze).rectangle([0, 0, W, base + 40], fill=int(60 * (1 - dim) * 2))
            img = Image.composite(Image.new("RGB", img.size, hexrgb("#F4E3CF")), img, haze)
    return grain(img, 30, rng)


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


def autumn_lake():
    rng = random.Random(1503)
    horizon = int(H * 0.56)
    img = vgradient([(0, "#8FB8D0"), (0.4, "#F2DCC0"), (0.56, "#F4E3CF"), (1, "#5A6A7A")])
    img = fill_below(img, ridge(rng, horizon - 160, 80, 1.5), "#B5A0A0", 4)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rectangle([0, horizon - 40, W, horizon], fill=hexrgb("#6A4A2A"))
    x = -40.0
    while x < W + 60:
        crowns(d, rng, x, horizon, 160 + rng.random() * 140, FALL)
        x += 50 + rng.random() * 50
    img.paste(layer, (0, 0), layer)
    img = img.crop((0, 0, W, horizon)).resize((W, horizon))
    full = Image.new("RGB", (W, H))
    full.paste(img, (0, 0))
    full = reflect(full, horizon, 0.75, "#5A6A7A", rng, 3)
    return grain(full, 30, rng)


MAKERS = {"midnight": midnight, "midnight-galaxy": midnight_galaxy, "midnight-city": midnight_city,
          "forest": forest, "forest-rays": forest_rays, "forest-lake": forest_lake,
          "arctic": arctic, "arctic-icebergs": arctic_icebergs, "arctic-pines": arctic_pines,
          "mint": mint, "mint-bokeh": mint_bokeh, "mint-lowpoly": mint_lowpoly,
          "desert": desert, "desert-night": desert_night, "desert-mesa": desert_mesa,
          "sakura": sakura, "sakura-fuji": sakura_fuji, "sakura-dusk": sakura_dusk,
          "ocean": ocean, "ocean-reef": ocean_reef, "ocean-abyss": ocean_abyss,
          "ember": ember, "ember-campfire": ember_campfire, "ember-lava": ember_lava,
          "lavender": lavender, "lavender-moon": lavender_moon, "lavender-waves": lavender_waves,
          "neon": neon, "neon-grid": neon_grid, "neon-street": neon_street,
          "autumn": autumn, "autumn-road": autumn_road, "autumn-lake": autumn_lake}

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
