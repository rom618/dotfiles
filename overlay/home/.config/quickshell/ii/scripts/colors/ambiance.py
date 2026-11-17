#!/usr/bin/env python3
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOUNDS = Path(os.environ.get("AMBIANCE_SOUNDS") or HERE.parent.parent / "themes" / "sounds.json")
OUT = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "quickshell-themes" / "sounds"
UA = "Mozilla/5.0 (X11; Linux x86_64) quickshell-themes"


def tracks(theme):
    try:
        return json.loads(SOUNDS.read_text()).get(theme, [])
    except (OSError, ValueError):
        return []


def local(theme, track):
    return OUT / f"{theme}-{hashlib.sha1(track['url'].encode()).hexdigest()[:10]}.ogg"


def fetch(theme, track):
    dest = local(theme, track)
    raw = dest.with_suffix(".download")
    part = dest.with_suffix(".part.ogg")
    req = urllib.request.Request(track["url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r, open(raw, "wb") as f:
        while chunk := r.read(1 << 16):
            f.write(chunk)
    fade = float(track.get("fade", 4))
    start = float(track.get("start", 0))
    end = float(track.get("end", 0))
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(raw)],
                           capture_output=True, text=True)
    total = float(probe.stdout.strip() or 0)
    stop = end if end > 0 else total
    length = max(stop - start, fade * 2 + 1)
    filters = f"loudnorm=I=-26:TP=-3:LRA=11,afade=t=in:d={fade},afade=t=out:st={length - fade:.2f}:d={fade}"
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", str(start), "-i", str(raw), "-t", f"{length:.2f}",
           "-af", filters, "-ac", "2", "-ar", "48000", "-c:a", "libopus", "-b:a", "96k", str(part)]
    try:
        subprocess.run(cmd, check=True)
        part.replace(dest)
    finally:
        raw.unlink(missing_ok=True)
        part.unlink(missing_ok=True)


def ensure(theme):
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for t in tracks(theme):
            if not local(theme, t).is_file():
                try:
                    fetch(theme, t)
                except Exception as e:
                    print(f"{theme}: {t.get('title', t['url'])}: {e}", file=sys.stderr)


def ready(theme):
    return [str(local(theme, t)) for t in tracks(theme) if local(theme, t).is_file()]


def main():
    args = sys.argv[1:]
    if args == ["--list"]:
        try:
            data = json.loads(SOUNDS.read_text())
        except (OSError, ValueError):
            data = {}
        print(json.dumps({k: len(v) for k, v in data.items() if v}))
        return 0
    if len(args) == 2 and args[0] == "--ready":
        print(json.dumps(ready(args[1])))
        return 0
    if len(args) == 1 and not args[0].startswith("-"):
        ensure(args[0])
        print(json.dumps(ready(args[0])))
        return 0
    print("usage: ambiance.py --list | --ready THEME | THEME (download missing tracks, print ready files)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
