#!/usr/bin/env python3
import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

RULES = Path(__file__).resolve().parent.parent.parent / "themes" / "auto.json"


def hhmm(text, day):
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", text or "")
    if not m:
        return None
    return day.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)


def phase(now, sunrise, sunset, dusk_minutes):
    if not sunrise or not sunset:
        sunrise, sunset = now.replace(hour=7, minute=30), now.replace(hour=18, minute=30)
    half = timedelta(minutes=dusk_minutes)
    if sunset - half <= now < sunset + half:
        return "dusk"
    if sunrise <= now < sunset - half:
        return "day"
    return "night"


def season(now, starts):
    md = now.strftime("%m-%d")
    order = sorted(starts.items(), key=lambda kv: kv[1])
    current = order[-1][0]
    for name, start in order:
        if md >= start:
            current = name
    return current


def in_range(md, start, end):
    return start <= md <= end if start <= end else (md >= start or md <= end)


def weather_kind(code, codes):
    if code is None:
        return None
    for kind, values in codes.items():
        if code in values:
            return kind
    return "clear"


def pick(rules, now, sunrise=None, sunset=None, temp=None, code=None):
    ph = phase(now, sunrise, sunset, rules.get("dusk_minutes", 60))
    se = season(now, rules["seasons"])
    wk = weather_kind(code, rules.get("weather_codes", {}))
    md = now.strftime("%m-%d")
    facts = {"phase": ph, "season": se, "weather": wk, "temp": temp}
    for r in rules["rules"]:
        if "phase" in r and ph not in r["phase"]:
            continue
        if "season" in r and se not in r["season"]:
            continue
        if "weather" in r and wk not in r["weather"]:
            continue
        if "temp_min" in r and (temp is None or temp < r["temp_min"]):
            continue
        if "temp_max" in r and (temp is None or temp > r["temp_max"]):
            continue
        if "from" in r and not in_range(md, r["from"], r.get("to", "12-31")):
            continue
        return {"theme": r["theme"], "why": r.get("why", ""), **facts}
    return {"theme": "", "why": "no rule matched", **facts}


def number(text):
    m = re.search(r"-?\d+(\.\d+)?", text or "")
    return float(m.group(0)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--now", help="YYYY-MM-DDTHH:MM, default the current time")
    ap.add_argument("--sunrise", default="")
    ap.add_argument("--sunset", default="")
    ap.add_argument("--temp", default="", help="like 12, 12C or 54F")
    ap.add_argument("--code", default="", help="wttr.in weather code")
    ap.add_argument("--rules", default=str(RULES))
    a = ap.parse_args()
    rules = json.loads(Path(a.rules).read_text())
    now = datetime.fromisoformat(a.now) if a.now else datetime.now()
    temp = number(a.temp)
    if temp is not None and a.temp.strip().upper().endswith("F"):
        temp = (temp - 32) * 5 / 9
    code = int(number(a.code)) if number(a.code) is not None and int(number(a.code)) > 0 else None
    print(json.dumps(pick(rules, now, hhmm(a.sunrise, now), hhmm(a.sunset, now), temp, code)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
