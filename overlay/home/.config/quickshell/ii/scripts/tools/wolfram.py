#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KEY_FILE = Path(os.environ.get("WOLFRAM_APPID_FILE", Path.home() / ".config" / "wolfram" / "appid"))
CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "quickshell" / "wolfram.json"
API = "https://api.wolframalpha.com/v1/"
HISTORY = 12


def page(q):
    return "https://www.wolframalpha.com/input?i=" + urllib.parse.quote_plus(q)


def call(endpoint, params, timeout):
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "desktop-tools/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace").strip()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace").strip()


def llm_text(text):
    keep = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("image:", "Wolfram Language code:", "Wolfram|Alpha website result", "Query:")) or s.startswith('"'):
            continue
        keep.append(line.rstrip())
    out = "\n".join(keep).strip()
    while "\n\n\n" in out:
        out = out.replace("\n\n\n", "\n\n")
    return out[:1500]


def load_cache():
    try:
        return json.loads(CACHE.read_text())
    except Exception:
        return {"history": []}


def save_cache(data):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(CACHE)


def remember(data, entry):
    hist = [h for h in data.get("history", []) if h.get("query", "").lower() != entry["query"].lower()]
    data["history"] = [entry] + hist[:HISTORY - 1]
    save_cache(data)


def ask(q):
    data = load_cache()
    for h in data.get("history", []):
        if h.get("query", "").lower() == q.lower() and time.time() - h.get("time", 0) < 86400:
            remember(data, h)
            return dict(h, cached=True)
    if not KEY_FILE.is_file() or not KEY_FILE.read_text().strip():
        return {"ok": False, "query": q, "url": page(q), "error": f"No AppID: put it in {KEY_FILE}"}
    key = KEY_FILE.read_text().strip()
    try:
        code, text = call("result", {"appid": key, "i": q, "units": "metric"}, 10)
        if code == 200 and text:
            entry = {"ok": True, "query": q, "answer": text, "detail": "", "url": page(q), "time": time.time()}
            remember(data, entry)
            return entry
        if code in (403,):
            return {"ok": False, "query": q, "url": page(q), "error": "AppID refused (403)"}
        code, text = call("llm-api", {"appid": key, "input": q, "units": "metric", "maxchars": "3000"}, 20)
        if code == 200 and text:
            body = llm_text(text)
            first = body.split("\n\n")[0].strip()
            entry = {"ok": True, "query": q, "answer": first, "detail": body[len(first):].strip(), "url": page(q), "time": time.time()}
            remember(data, entry)
            return entry
        return {"ok": False, "query": q, "url": page(q), "error": "Wolfram Alpha has no answer for that" if code in (501, 400) else f"Wolfram Alpha error {code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "query": q, "url": page(q), "error": f"No connection ({getattr(e, 'reason', e)})", "retry": True}


def decimal(q):
    data = load_cache()
    entry = next((h for h in data.get("history", []) if h.get("query", "").lower() == q.lower()), None)
    if entry and entry.get("decimal"):
        return {"ok": True, "query": q, "decimal": entry["decimal"]}
    if not KEY_FILE.is_file():
        return {"ok": False, "query": q, "error": "No AppID"}
    try:
        code, text = call("result", {"appid": KEY_FILE.read_text().strip(), "i": f"N[{q}]", "units": "metric"}, 10)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "query": q, "error": f"No connection ({getattr(e, 'reason', e)})", "retry": True}
    if code != 200 or not text:
        return {"ok": False, "query": q, "error": "No decimal form for that"}
    if entry:
        entry["decimal"] = text
        save_cache(data)
    return {"ok": True, "query": q, "decimal": text}


def main():
    args = sys.argv[1:]
    if len(args) > 1 and args[0] == "--decimal":
        print(json.dumps(decimal(" ".join(args[1:]).strip())))
        return
    if args == ["--history"]:
        print(json.dumps(load_cache().get("history", [])))
        return
    if args == ["--clear"]:
        save_cache({"history": []})
        print("[]")
        return
    q = " ".join(args).strip()
    if not q:
        print("usage: wolfram.py QUERY | --history | --clear", file=sys.stderr)
        sys.exit(2)
    print(json.dumps(ask(q)))


if __name__ == "__main__":
    main()
