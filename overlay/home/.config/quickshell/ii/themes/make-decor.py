#!/usr/bin/env python3
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "decor"


def f(v):
    return f"{v:.2f}"


def rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def snowflake(branches, tip, side_len, side_at, hexcore):
    c = 50
    lines = []
    for k in range(6):
        a = k * math.pi / 3
        x, y = rot(0, -tip, a)
        lines.append((0, 0, x, y))
        for pos, length in zip(side_at, side_len):
            bx, by = rot(0, -pos, a)
            for sgn in (-1, 1):
                ex, ey = rot(sgn * length * math.sin(math.pi / 3), -pos - length * math.cos(math.pi / 3), a)
                lines.append((bx, by, ex, ey))
        for pos in branches:
            bx, by = rot(0, -pos, a)
            for sgn in (-1, 1):
                ex, ey = rot(sgn * 5, -pos - 5, a)
                lines.append((bx, by, ex, ey))
    path = " ".join(f"M{f(c + x1)} {f(c + y1)}L{f(c + x2)} {f(c + y2)}" for x1, y1, x2, y2 in lines)
    hexpts = " ".join(f"{f(c + rot(0, -hexcore, k * math.pi / 3 + math.pi / 6)[0])},"
                      f"{f(c + rot(0, -hexcore, k * math.pi / 3 + math.pi / 6)[1])}" for k in range(6))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<path d="{path}" fill="none" stroke="#BFE6FF" stroke-opacity="0.45" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="{path}" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round"/>'
            f'<polygon points="{hexpts}" fill="#FFFFFF" fill-opacity="0.9" stroke="#DDF2FF" stroke-width="1.5"/>'
            f'</svg>\n')


def leaf_ovate(light, dark):
    veins = ""
    for i, t in enumerate((0.25, 0.4, 0.55, 0.7)):
        y = 85 - t * 70
        w = 22 * math.sin(math.pi * t)
        veins += f"M50 {f(y)}Q{f(50 - w * 0.6)} {f(y - 6)} {f(50 - w)} {f(y - 12)}"
        veins += f"M50 {f(y)}Q{f(50 + w * 0.6)} {f(y - 6)} {f(50 + w)} {f(y - 12)}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
            f'<stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></linearGradient></defs>'
            f'<path d="M50 8C72 24 80 50 66 72C60 82 54 86 50 92C46 86 40 82 34 72C20 50 28 24 50 8Z" fill="url(#g)"/>'
            f'<path d="M50 14L50 97" stroke="{dark}" stroke-width="2.4" stroke-linecap="round" fill="none"/>'
            f'<path d="{veins}" stroke="{dark}" stroke-opacity="0.7" stroke-width="1.4" fill="none" stroke-linecap="round"/>'
            f'</svg>\n')


def leaf_maple(light, dark):
    pts = []
    lobes = [(0, 44), (35, 20), (60, 40), (95, 22), (125, 38), (150, 16), (180, 8)]
    full = lobes + [(360 - a, r) for a, r in reversed(lobes[:-1])]
    for a, r in full:
        rad = math.radians(a - 90)
        pts.append((50 + r * math.cos(rad), 52 + r * math.sin(rad)))
    poly = " ".join(f"{f(x)},{f(y)}" for x, y in pts)
    veins = "".join(f"M50 56L{f(50 + 38 * math.cos(math.radians(a - 90)))} {f(56 + 38 * math.sin(math.radians(a - 90)))}"
                    for a in (0, 60, 300, 120, 240))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><radialGradient id="g" cx="0.5" cy="0.45" r="0.6">'
            f'<stop offset="0" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></radialGradient></defs>'
            f'<polygon points="{poly}" fill="url(#g)" stroke="{dark}" stroke-width="1.2" stroke-linejoin="round"/>'
            f'<path d="{veins}M50 56L50 96" stroke="{dark}" stroke-opacity="0.75" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
            f'</svg>\n')


def bubble(rim, tint):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><radialGradient id="b" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0.62" stop-color="{tint}" stop-opacity="0.04"/>'
            f'<stop offset="0.9" stop-color="{tint}" stop-opacity="0.28"/>'
            f'<stop offset="1" stop-color="{rim}" stop-opacity="0.85"/></radialGradient>'
            f'<radialGradient id="h" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.95"/><stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="50" cy="50" r="46" fill="url(#b)"/>'
            f'<path d="M24 40A28 28 0 0 1 46 20" stroke="#FFFFFF" stroke-opacity="0.85" stroke-width="5" stroke-linecap="round" fill="none"/>'
            f'<ellipse cx="34" cy="31" rx="7" ry="4.5" transform="rotate(-35 34 31)" fill="url(#h)"/>'
            f'<path d="M66 82A34 34 0 0 0 80 66" stroke="{rim}" stroke-opacity="0.6" stroke-width="3" stroke-linecap="round" fill="none"/>'
            f'</svg>\n')


def sparkle(color, glow):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><radialGradient id="g" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0" stop-color="{glow}" stop-opacity="0.55"/><stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="50" cy="50" r="30" fill="url(#g)"/>'
            f'<path d="M50 4C52 40 60 48 96 50C60 52 52 60 50 96C48 60 40 52 4 50C40 48 48 40 50 4Z" fill="{color}"/>'
            f'<path d="M50 30C51 46 54 49 70 50C54 51 51 54 50 70C49 54 46 51 30 50C46 49 49 46 50 30Z" fill="#FFFFFF" transform="rotate(45 50 50)" opacity="0.8"/>'
            f'</svg>\n')


def tumbleweed():
    import random
    rng = random.Random(5)
    paths = []
    for _ in range(46):
        a0 = rng.random() * math.tau
        r0 = 8 + rng.random() * 34
        r1 = 8 + rng.random() * 34
        a1 = a0 + (rng.random() - 0.5) * 2.4
        x0, y0 = 50 + r0 * math.cos(a0), 50 + r0 * math.sin(a0)
        x1, y1 = 50 + r1 * math.cos(a1), 50 + r1 * math.sin(a1)
        cx, cy = 50 + (rng.random() - 0.5) * 60, 50 + (rng.random() - 0.5) * 60
        paths.append(f"M{f(x0)} {f(y0)}Q{f(cx)} {f(cy)} {f(x1)} {f(y1)}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<circle cx="50" cy="50" r="40" fill="#8A6A3A" fill-opacity="0.12"/>'
            f'<path d="{"".join(paths)}" fill="none" stroke="#6E5230" stroke-width="2.2" stroke-linecap="round"/>'
            f'<path d="{"".join(paths[::3])}" fill="none" stroke="#B08A52" stroke-width="1.4" stroke-linecap="round"/>'
            f'</svg>\n')


def petal(light, dark):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><radialGradient id="g" cx="0.5" cy="0.75" r="0.75">'
            f'<stop offset="0" stop-color="#FFFFFF"/><stop offset="0.45" stop-color="{light}"/><stop offset="1" stop-color="{dark}"/></radialGradient></defs>'
            f'<path d="M50 94C24 80 14 52 22 30C28 14 40 8 46 18L50 26L54 18C60 8 72 14 78 30C86 52 76 80 50 94Z" fill="url(#g)"/>'
            f'<path d="M50 90L50 40" stroke="{dark}" stroke-opacity="0.35" stroke-width="1.5" fill="none"/>'
            f'</svg>\n')


def jellyfish(body, glow_color):
    tentacles = "".join(f'<path d="M{x} 54C{x - 6} 66 {x + 6} 76 {x} 96" stroke="{body}" stroke-opacity="0.6" '
                        f'stroke-width="2" fill="none" stroke-linecap="round"/>' for x in (32, 42, 50, 58, 68))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><radialGradient id="g" cx="0.5" cy="0.3" r="0.6">'
            f'<stop offset="0" stop-color="#FFFFFF" stop-opacity="0.9"/><stop offset="0.5" stop-color="{body}" stop-opacity="0.65"/>'
            f'<stop offset="1" stop-color="{glow_color}" stop-opacity="0.25"/></radialGradient></defs>'
            f'<circle cx="50" cy="40" r="34" fill="{glow_color}" fill-opacity="0.12"/>'
            f'{tentacles}'
            f'<path d="M20 52C20 26 34 14 50 14C66 14 80 26 80 52C74 48 70 56 64 52C58 48 56 56 50 52C44 48 42 56 36 52C30 48 26 56 20 52Z" fill="url(#g)"/>'
            f'</svg>\n')


def glow_dot(core, glow_color, ring=0.5):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
            f'<defs><radialGradient id="g" cx="0.5" cy="0.5" r="0.5">'
            f'<stop offset="0" stop-color="{core}"/><stop offset="0.18" stop-color="{core}"/>'
            f'<stop offset="0.4" stop-color="{glow_color}" stop-opacity="{ring}"/>'
            f'<stop offset="1" stop-color="{glow_color}" stop-opacity="0"/></radialGradient></defs>'
            f'<circle cx="50" cy="50" r="50" fill="url(#g)"/></svg>\n')


ASSETS = {
    "snowflake-1.svg": snowflake([], 40, [12, 9, 6], [14, 24, 32], 7),
    "snowflake-2.svg": snowflake([20, 30], 42, [16], [12], 9),
    "snowflake-3.svg": snowflake([12], 38, [8, 14, 8], [10, 20, 30], 6),
    "leaf-green.svg": leaf_ovate("#95D5B2", "#2D6A4F"),
    "leaf-lime.svg": leaf_ovate("#B7E4A0", "#52794A"),
    "leaf-gold.svg": leaf_maple("#F6E3B0", "#C9932E"),
    "leaf-amber.svg": leaf_maple("#F4C27A", "#B5651D"),
    "leaf-moss.svg": leaf_maple("#A7D7A0", "#40916C"),
    "bubble-white.svg": bubble("#FFFFFF", "#E3FCE6"),
    "bubble-mint.svg": bubble("#80ED99", "#C7F9CC"),
    "bubble-teal.svg": bubble("#38A3A5", "#80ED99"),
    "sparkle-white.svg": sparkle("#F2F4FF", "#A6B1FF"),
    "sparkle-gold.svg": sparkle("#FBEBC2", "#F5D687"),
    "tumbleweed.svg": tumbleweed(),
    "petal-pink.svg": petal("#F8B7CD", "#E07A9E"),
    "petal-blush.svg": petal("#FBD3E0", "#F09AB8"),
    "petal-white.svg": petal("#FFF0F5", "#F4C2D4"),
    "jellyfish-cyan.svg": jellyfish("#6FD3E6", "#3EE6FF"),
    "jellyfish-violet.svg": jellyfish("#C7A6FF", "#9A6BFF"),
    "jellyfish-pink.svg": jellyfish("#F7A8D8", "#FF6FC8"),
    "ember.svg": glow_dot("#FFF2C2", "#FF6A1A", 0.7),
    "ember-red.svg": glow_dot("#FFD0A0", "#E8341C", 0.6),
    "firefly.svg": glow_dot("#FFFBD0", "#D8F27A", 0.55),
    "leaf-red.svg": leaf_maple("#F28B5A", "#A8241A"),
    "leaf-rust.svg": leaf_maple("#E89A5A", "#8A3A10"),
    "leaf-orange.svg": leaf_ovate("#F7B860", "#B5551A"),
    "leaf-yellow.svg": leaf_ovate("#F8DC7A", "#B88A1A"),
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for name, svg in ASSETS.items():
        (OUT / name).write_text(svg)
    print(f"{len(ASSETS)} decor SVGs in {OUT}")
