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
DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "quickshell-themes"
OUT = DATA / "sounds"
PRIVATE = DATA / "private"
SKIP = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "quickshell" / "user" / "generated" / "theme-ambiance-skip.json"
EVENTS = ("popupOpen", "popupClose", "notification", "lock", "unlock", "windowOpen", "windowClose", "workspace",
          "launcherOpen", "launcherClose", "screenshot")
UA = "Mozilla/5.0 (X11; Linux x86_64) quickshell-themes"


def tracks(theme):
    try:
        return json.loads(SOUNDS.read_text()).get(theme, [])
    except (OSError, ValueError):
        return []


def private(theme):
    if not theme.replace("-", "").isalnum():
        return {}
    try:
        return json.loads((PRIVATE / f"{theme}.json").read_text())
    except (OSError, ValueError):
        return {}


def skipped(theme):
    try:
        return set(json.loads(SKIP.read_text()).get(theme, []))
    except (OSError, ValueError):
        return set()


def skip(theme, path):
    try:
        data = json.loads(SKIP.read_text())
    except (OSError, ValueError):
        data = {}
    data[theme] = sorted(set(data.get(theme, [])) | {path})
    SKIP.parent.mkdir(parents=True, exist_ok=True)
    tmp = SKIP.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1) + "\n")
    tmp.replace(SKIP)


def music_entries(theme):
    out = []
    for m in private(theme).get("music", []):
        f, name = (m, "") if isinstance(m, str) else ((m.get("file"), m.get("name") or "") if isinstance(m, dict) else (None, ""))
        if isinstance(f, str):
            out.append((str(Path(os.path.expanduser(f))), name))
    return out


def local_music(theme):
    return [f for f, _ in music_entries(theme) if Path(f).is_file()]


def names(theme):
    found = {}
    for t in tracks(theme):
        if t.get("title"):
            found[str(local(theme, t))] = t["title"]
    for f, name in music_entries(theme):
        if name:
            found[f] = name
    return found


def effects(theme):
    found = {}
    out = DATA / "effects"
    def convert(event, f):
        path = Path(os.path.expanduser(f)) if isinstance(f, str) else None
        if not path or not path.is_file():
            return None
        dest = out / f"{theme}-{event}-{hashlib.sha1(str(path).encode()).hexdigest()[:10]}.wav"
        if not dest.is_file():
            out.mkdir(parents=True, exist_ok=True)
            part = dest.with_suffix(".part.wav")
            r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(path), "-ac", "2", "-ar", "48000",
                                "-af", "silenceremove=start_periods=1:start_threshold=-50dB,loudnorm=I=-20:TP=-2",
                                "-c:a", "pcm_s16le", str(part)])
            if r.returncode != 0:
                part.unlink(missing_ok=True)
                return None
            part.replace(dest)
        return str(dest)

    for event, f in (private(theme).get("sounds") or {}).items():
        if event not in EVENTS:
            continue
        if isinstance(f, list):
            files = [convert(event, x) for x in f]
            if any(files):
                found[event] = [x or "" for x in files]
        else:
            one = convert(event, f)
            if one:
                found[event] = one
    return found


def local(theme, track):
    h = hashlib.sha1(track['url'].encode()).hexdigest()[:10]
    own = OUT / f"{theme}-{h}.ogg"
    if own.is_file():
        return own
    shared = sorted(OUT.glob(f"*-{h}.ogg"))
    return shared[0] if shared else own


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
    skip_set = skipped(theme)
    files = [str(local(theme, t)) for t in tracks(theme) if local(theme, t).is_file()] + local_music(theme)
    return [f for f in files if f not in skip_set]


def main():
    args = sys.argv[1:]
    if args == ["--list"]:
        try:
            data = json.loads(SOUNDS.read_text())
        except (OSError, ValueError):
            data = {}
        counts = {k: len(v) for k, v in data.items() if v}
        for path in sorted(PRIVATE.glob("*.json")):
            n = len(local_music(path.stem))
            if n:
                counts[path.stem] = counts.get(path.stem, 0) + n
        print(json.dumps(counts))
        return 0
    if len(args) == 2 and args[0] == "--effects":
        print(json.dumps(effects(args[1])))
        return 0
    if len(args) == 3 and args[0] == "--skip":
        skip(args[1], args[2])
        print(json.dumps(ready(args[1])))
        return 0
    if len(args) == 2 and args[0] == "--names":
        print(json.dumps(names(args[1])))
        return 0
    if len(args) == 2 and args[0] == "--ready":
        print(json.dumps(ready(args[1])))
        return 0
    if len(args) == 1 and not args[0].startswith("-"):
        ensure(args[0])
        print(json.dumps(ready(args[0])))
        return 0
    print("usage: ambiance.py --list | --ready THEME | --names THEME | --effects THEME | --skip THEME FILE | THEME (download missing tracks, print ready files)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
