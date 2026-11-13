#!/usr/bin/env python3
import json
import sys


def lum(h):
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


PAIRS = [
    ("on_background", "background", 7),
    ("on_surface", "surface", 7),
    ("on_surface_variant", "surface_container_low", 4.5),
    ("on_surface_variant", "surface_container", 4.5),
    ("on_surface_variant", "surface_container_high", 4.5),
    ("outline", "background", 3),
    ("outline", "surface_container_low", 3),
    ("primary", "background", 3),
    ("primary", "surface_container_low", 3),
    ("on_primary", "primary", 4.5),
    ("on_primary_container", "primary_container", 4.5),
    ("on_secondary_container", "secondary_container", 4.5),
    ("on_tertiary_container", "tertiary_container", 4.5),
    ("on_secondary", "secondary", 4.5),
    ("on_tertiary", "tertiary", 4.5),
    ("inverse_on_surface", "inverse_surface", 4.5),
]

failed = 0
for path in sys.argv[1:]:
    t = json.load(open(path))
    c, term = t["colors"], t["terminal"]
    print(f"== {t['name']}")
    for fg, bg, need in PAIRS:
        if fg in c and bg in c:
            r = ratio(c[fg], c[bg])
            mark = "ok " if r >= need else "LOW"
            failed += r < need
            print(f"  {mark} {r:5.2f} (>= {need}) {fg} {c[fg]} on {bg} {c[bg]}")
    bg = term["term0"]
    for k in [f"term{i}" for i in range(1, 16)]:
        need = 3.5 if k == "term8" else 4.5
        r = ratio(term[k], bg)
        mark = "ok " if r >= need else "LOW"
        failed += r < need
        print(f"  {mark} {r:5.2f} (>= {need}) {k} {term[k]} on term0 {bg}")
    for k, v in t.get("kitty", {}).items():
        print(f"  kitty {k} = {v}")
    if "kitty" in t:
        r = ratio(t["kitty"]["selection_foreground"], t["kitty"]["selection_background"])
        failed += r < 4.5
        print(f"  {'ok ' if r >= 4.5 else 'LOW'} {r:5.2f} (>= 4.5) selection")
print("FAILED" if failed else "ALL OK", failed)
sys.exit(1 if failed else 0)
