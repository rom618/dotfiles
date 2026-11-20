#!/usr/bin/env python3
import json
import os
import re
import select
import subprocess
import sys
import threading
import time
from pathlib import Path

HOME = Path.home()
CACHE = Path(os.environ.get("XDG_CACHE_HOME", HOME / ".cache")) / "quickshell"
QCONF = CACHE / "qalc"
DATA = Path(os.environ.get("XDG_DATA_HOME", HOME / ".local" / "share")) / "qalculate"
STAMP = CACHE / "qalc-rates-try"
ANSI = re.compile(r"\x1b\[[0-9;]*m")
NUM = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?:E([\u2212\-+]?\d+))?")

KINDS = {
    "length": ["m", "cm", "mm", "km", "ft", "in", "mi"],
    "mass": ["kg", "g", "mg", "t", "lb", "oz"],
    "temperature": ["\u00b0C", "\u00b0F", "K"],
    "volume": ["L", "mL", "cL", "m^3", "cup", "floz", "gal"],
    "area": ["m^2", "cm^2", "km^2", "ha", "ft^2", "acre"],
    "speed": ["km/h", "m/s", "mph", "knot"],
    "time": ["s", "min", "h", "d", "week", "yr"],
    "data": ["B", "kB", "MB", "GB", "TB", "MiB", "GiB"],
    "energy": ["J", "kJ", "kcal", "kWh", "Wh", "eV"],
    "power": ["W", "kW", "hp"],
    "pressure": ["Pa", "kPa", "bar", "atm", "psi", "mmHg"],
    "currency": ["EUR", "USD", "JPY", "GBP", "CNY", "CHF"],
}
BASE = {
    "m": "length", "kg": "mass", "K": "temperature", "m\u00b3": "volume", "m\u00b2": "area",
    "m/s": "speed", "bits": "data", "bit": "data", "kg\u00b7m\u00b2/s\u00b2": "energy",
    "kg\u00b7m\u00b2/s\u00b3": "power", "kg/(m\u00b7s\u00b2)": "pressure",
}
METRIC = {"m", "cm", "mm", "km", "kg", "g", "mg", "t", "\u00b0C", "K", "L", "mL", "cL", "m^3", "m^2", "cm^2",
          "km^2", "ha", "km/h", "m/s", "J", "kJ", "Wh", "kWh", "W", "kW", "Pa", "kPa", "bar"}
TIME_UNITS ={"s", "ms", "min", "h", "d", "wk", "yr", "mo"}
CURRENCY_SIGNS = "\u20ac$\u00a3\u00a5"


class Qalc:
    def __init__(self, prefixes=True):
        self.prefixes = prefixes
        self.p = None

    def start(self):
        env = dict(os.environ, XDG_CONFIG_HOME=str(QCONF), LANG="C.UTF-8", LC_ALL="C.UTF-8")
        self.p = subprocess.Popen(["qalc", "-i", "-t"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, env=env)
        os.set_blocking(self.p.stdout.fileno(), False)
        self.buf = b""
        self.read_prompt(3)
        for cmd in ["set autoconversion optimal", "set max decimals off", "set prefixes " + ("on" if self.prefixes else "off")]:
            self.ask(cmd)

    def read_prompt(self, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            r, _, _ = select.select([self.p.stdout], [], [], max(0, end - time.monotonic()))
            if r:
                chunk = self.p.stdout.read()
                if not chunk:
                    raise RuntimeError("qalc exited")
                self.buf += chunk
                if self.buf.endswith(b"> "):
                    out = self.buf[:-2]
                    self.buf = b""
                    return ANSI.sub("", out.decode("utf-8", "replace"))
        raise TimeoutError("qalc timed out")

    def ask(self, expr):
        if self.p is None or self.p.poll() is not None:
            self.start()
        expr = expr.replace("\n", " ")
        self.p.stdin.write((expr + "\n").encode())
        self.p.stdin.flush()
        try:
            out = self.read_prompt(2)
        except TimeoutError:
            self.stop()
            return "", "Took too long"
        lines = [l.strip() for l in out.splitlines()]
        if lines and lines[0] == expr.strip():
            lines = lines[1:]
        errs = [l for l in lines if l.lower().startswith(("error:", "warning:"))]
        res = [l for l in lines if l and l not in errs]
        err = next((e.split(":", 1)[1].strip() for e in errs if e.lower().startswith("error")), "")
        return (res[-1] if res else ""), err

    def stop(self):
        if self.p and self.p.poll() is None:
            try:
                self.p.stdin.write(b"quit\n")
                self.p.stdin.flush()
                self.p.wait(1)
            except Exception:
                self.p.kill()
        self.p = None


def setup_conf():
    cfg = QCONF / "qalculate" / "qalc.cfg"
    if not cfg.exists():
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text("\n[General]\nsave_config=0\nsave_mode_on_exit=0\nsave_definitions_on_exit=0\n"
                       "auto_update_exchange_rates=0\ncolorize=0\nuse_unicode_signs=1\n\n[Mode]\nprecision=10\n")


def normalize(q):
    q = q.strip()
    q = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", q)
    q = re.sub(r"(?<=\d),(?=\d)", ".", q)
    q = re.sub(r"\s*(->|=>|\u2192)\s*", " to ", q)
    if not re.search(r"\sto\s", q, re.I):
        m = re.match(r"^(.*\S)\s+(?:in|into|as)\s+(\S[^\s]*(?:\s+\S+)?)$", q, re.I)
        if m and re.search(r"\d", m.group(1)):
            q = m.group(1) + " to " + m.group(2)
    q = re.sub(r"(?<=\d)\s*\u00b0?\s*([CcFf])\b(?!\w)", lambda m: " \u00b0" + m.group(1).upper(), q)
    q = re.sub(r"(\bto\s+)\u00b0?([CcFf])$", lambda m: m.group(1) + "\u00b0" + m.group(2).upper(), q)
    q = re.sub(r"(?i)\b(celsius|centigrade)\b", "\u00b0C", q)
    q = re.sub(r"(?i)\bfahrenheit\b", "\u00b0F", q)
    q = re.sub(r"(?i)\bkelvin\b", "K", q)
    q = re.sub(r"(?i)\bcups?\b", "cup", q)
    return q


def split_target(q):
    m = re.match(r"^(.*\S)\s+to\s+(\S.*)$", q, re.I)
    return (m.group(1), m.group(2)) if m else (q, "")


def fnum(s, currency):
    def rep(m):
        mant, exp = m.group(1), m.group(2)
        if "." not in mant:
            return m.group(0)
        x = float(mant)
        if currency and not exp:
            v = f"{x:.2f}"
        elif x >= 1:
            v = f"{x:.{max(0, min(4, 6 - len(str(int(x)))))}f}"
        else:
            v = f"{x:.4g}" if x else "0"
            if "e" in v:
                v = mant
        if "." in v:
            v = v.rstrip("0").rstrip(".")
            if currency and not exp and "." in f"{x:.2f}" and x != int(x):
                v = f"{x:.2f}"
        return v + ("E" + exp if exp else "")
    return NUM.sub(rep, s)


def tidy(s):
    s = s.replace("kcal_th", "kcal").replace("fl_oz", "fl oz")
    return re.sub(r"(?<=\w)_(?=\w)", " ", s)


def value_of(s):
    m = NUM.search(s.replace(",", ""))
    if not m:
        return None
    v = float(m.group(1)) * (10 ** int(m.group(2).replace("\u2212", "-")) if m.group(2) else 1)
    return -v if re.match(r"^\s*[\u2212-]", s) else v


def classify(base_q, src):
    out, err = base_q.ask(src + " to base")
    if err or not out:
        return None
    if any(c in out for c in CURRENCY_SIGNS) or re.search(r"\bEUR\b", out):
        return "currency"
    unit = NUM.sub("", out).replace("\u2248", "").strip()
    if unit in BASE:
        return BASE[unit]
    toks = set(re.findall(r"[A-Za-z]+", unit))
    if toks and toks <= TIME_UNITS and "/" not in unit and "\u00b7" not in unit:
        return "time"
    return None


def convert(q, disp, base_q):
    t0 = time.monotonic()
    raw = q
    q = normalize(q)
    res = {"query": raw, "ok": False}
    if not q or not re.search(r"\d", q):
        res["error"] = "Type a value and a unit, like 5 ft to cm"
        return res
    src, target = split_target(q)
    kind = classify(base_q, src)
    cur = kind == "currency"
    src_val = value_of(src)
    cands = []
    source_unit = ""
    for u in KINDS.get(kind, []):
        out, err = disp.ask(f"{src} to {u}")
        if err or not out or "(" in out:
            continue
        v = value_of(out)
        if v is not None and src_val is not None and "+" not in out and abs(v - src_val) <= 1e-9 * max(1, abs(v)):
            source_unit = source_unit or u
            continue
        if kind not in ("temperature", "currency") and v and not (0.01 <= abs(v) < 1e6):
            continue
        cands.append({"text": tidy(fnum(out, cur)), "unit": u, "nice": v is None or v == 0 or 0.1 <= abs(v) < 10000})
    main = ""
    if target:
        out, err = disp.ask(q)
        if err or not out:
            res["error"] = err or "No result"
            return res
        main = tidy(fnum(out, cur))
    else:
        pick = None
        if source_unit and source_unit in METRIC:
            pick = next((c for c in cands if c["nice"] and c["unit"] not in METRIC), None)
        pick = pick or next((c for c in cands if c["nice"]), None) or (cands[0] if cands else None)
        if pick:
            main = pick["text"]
    if not main:
        out, err = disp.ask(src)
        if err or not out:
            res["error"] = err or "No result"
            return res
        main = tidy(fnum(out, cur))
    related = [{"text": c["text"], "unit": c["unit"]} for c in cands if c["text"] != main]
    res.update(ok=True, expr=q, kind=kind or "", source=source_unit, main=main, related=related[:5],
               ms=round((time.monotonic() - t0) * 1000, 1))
    return res


def rates_file():
    for d in (DATA, Path("/usr/share/qalculate")):
        f = d / "eurofxref-daily.xml"
        if f.exists():
            return f
    return None


def rates_date():
    f = rates_file()
    if not f:
        return ""
    m = re.search(r"time=['\"](\d{4}-\d\d-\d\d)", f.read_text(errors="replace"))
    return m.group(1) if m else ""


def update_rates(force=False):
    f = DATA / "eurofxref-daily.xml"
    now = time.time()
    if not force:
        if f.exists() and now - f.stat().st_mtime < 86400:
            return False
        try:
            if now - float(STAMP.read_text()) < 86400:
                return False
        except Exception:
            pass
    STAMP.parent.mkdir(parents=True, exist_ok=True)
    STAMP.write_text(str(now))
    env = dict(os.environ, XDG_CONFIG_HOME=str(QCONF))
    try:
        subprocess.run(["qalc", "-e"], env=env, capture_output=True, timeout=60)
    except Exception:
        return False
    return f.exists() and f.stat().st_mtime >= now - 5


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def serve():
    setup_conf()
    lock = threading.Condition()
    state = {"next": None, "eof": False, "restart": False}

    def reader():
        for line in sys.stdin:
            line = line.rstrip("\n")
            if not line:
                continue
            with lock:
                state["next"] = line
                lock.notify()
        with lock:
            state["eof"] = True
            lock.notify()

    def rates():
        if update_rates():
            with lock:
                state["restart"] = True
                lock.notify()

    threading.Thread(target=reader, daemon=True).start()
    threading.Thread(target=rates, daemon=True).start()
    disp, base_q = Qalc(True), Qalc(False)
    disp.start()
    base_q.start()
    emit({"type": "ready", "rates": rates_date()})
    while True:
        with lock:
            while state["next"] is None and not state["eof"] and not state["restart"]:
                lock.wait()
            if state["restart"]:
                state["restart"] = False
                disp.stop()
                base_q.stop()
                emit({"type": "rates", "rates": rates_date()})
                continue
            if state["next"] is None and state["eof"]:
                break
            line, state["next"] = state["next"], None
        rid, _, q = line.partition("\t")
        try:
            r = convert(q, disp, base_q)
        except Exception as e:
            disp.stop()
            base_q.stop()
            r = {"query": q, "ok": False, "error": f"Converter error: {e}"}
        r["id"] = rid
        r["type"] = "result"
        emit(r)
    disp.stop()
    base_q.stop()


def main():
    args = sys.argv[1:]
    if args == ["--serve"]:
        serve()
        return
    if args == ["--update-rates"]:
        setup_conf()
        print(json.dumps({"updated": update_rates(force=True), "rates": rates_date()}))
        return
    if args == ["--rates"]:
        print(json.dumps({"rates": rates_date()}))
        return
    if not args:
        print("usage: convert.py QUERY | --serve | --update-rates | --rates", file=sys.stderr)
        sys.exit(2)
    setup_conf()
    disp, base_q = Qalc(True), Qalc(False)
    print(json.dumps(convert(" ".join(args), disp, base_q), ensure_ascii=False))
    disp.stop()
    base_q.stop()


if __name__ == "__main__":
    main()
