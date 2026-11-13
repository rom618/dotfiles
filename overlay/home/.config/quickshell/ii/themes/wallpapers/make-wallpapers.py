#!/usr/bin/env python3
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

W, H = 2560, 1600
OUT_SIZE = (3840, 2400)
OUT = Path(__file__).resolve().parent


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


MAKERS = {"midnight": midnight, "forest": forest, "arctic": arctic, "mint": mint}

if __name__ == "__main__":
    names = sys.argv[1:] or list(MAKERS)
    for name in names:
        MAKERS[name]().resize(OUT_SIZE, Image.LANCZOS).save(OUT / f"{name}.jpg", quality=90, optimize=True,
                                                               progressive=True)
        print(f"{name}.jpg {(OUT / f'{name}.jpg').stat().st_size // 1024} KB")
