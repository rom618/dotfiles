#!/usr/bin/env python3
import fcntl
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "ambiance-playlist" / "config.json"
DATA = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "quickshell-themes"
OUT = DATA / "playlist"
INDEX = OUT / "index.json"


def load_config():
    try:
        cfg = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return None
    if not cfg.get("server") or not cfg.get("playlist"):
        return None
    key_file = Path(os.path.expanduser(cfg.get("keyFile") or str(CONFIG.parent / "key")))
    try:
        cfg["key"] = key_file.read_text().strip()
    except OSError:
        return None
    return cfg


def call(cfg, method, params=(), raw=False):
    q = [("apiKey", cfg["key"]), ("c", cfg.get("client") or "ambiance"), ("v", "1.16.1"), ("f", "json")] + list(params)
    url = cfg["server"].rstrip("/") + "/rest/" + method + "?" + urllib.parse.urlencode(q)
    r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "ambiance-playlist"}), timeout=60)
    if raw:
        return r
    with r:
        v = json.load(r)["subsonic-response"]
    if v.get("status") != "ok":
        raise RuntimeError(f"{method}: error {v.get('error', {}).get('code')}")
    return v


def fetch(cfg, song, dest):
    raw = dest.with_suffix(".download")
    part = dest.with_suffix(".part.ogg")
    try:
        with call(cfg, "download", [("id", song["id"])], raw=True) as r, open(raw, "wb") as f:
            while chunk := r.read(1 << 16):
                f.write(chunk)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", str(raw), "-map", "0:a:0",
                        "-af", "loudnorm=I=-26:TP=-3:LRA=11", "-ac", "2", "-ar", "48000",
                        "-c:a", "libopus", "-b:a", "128k", str(part)], check=True)
        part.replace(dest)
    finally:
        raw.unlink(missing_ok=True)
        part.unlink(missing_ok=True)


def local_name(song_id):
    return re.sub(r"[^A-Za-z0-9_-]", "_", str(song_id)) + ".ogg"


def sync(cfg):
    playlists = call(cfg, "getPlaylists").get("playlists", {}).get("playlist", [])
    match = next((p for p in playlists if p.get("name") == cfg["playlist"]), None)
    if not match:
        raise RuntimeError("playlist not found")
    entries = call(cfg, "getPlaylist", [("id", match["id"])])["playlist"].get("entry", [])
    OUT.mkdir(parents=True, exist_ok=True)
    os.chmod(OUT, 0o700)
    tracks, downloaded, failed, seen = [], 0, 0, set()
    for song in entries:
        name = local_name(song["id"])
        if name in seen:
            continue
        seen.add(name)
        dest = OUT / name
        if not dest.is_file():
            try:
                fetch(cfg, song, dest)
                downloaded += 1
            except Exception as e:
                failed += 1
                print(f"download failed: {type(e).__name__}", file=sys.stderr)
                continue
        tracks.append({"file": str(dest), "id": song["id"], "title": song.get("title") or "",
                       "artist": song.get("artist") or "", "album": song.get("album") or ""})
    removed = 0
    for f in OUT.glob("*.ogg"):
        if f.name not in seen:
            f.unlink(missing_ok=True)
            removed += 1
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps({"playlist": cfg["playlist"], "tracks": tracks}, ensure_ascii=False, indent=1) + "\n")
    tmp.replace(INDEX)
    return {"tracks": len(tracks), "downloaded": downloaded, "removed": removed, "failed": failed}


def main():
    cfg = load_config()
    if cfg is None:
        print(json.dumps({"configured": False}))
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / ".lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            result = sync(cfg)
        except Exception as e:
            print(json.dumps({"configured": True, "offline": True, "error": type(e).__name__}))
            return 1
    print(json.dumps(dict(configured=True, **result)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
