#!/usr/bin/env python3
import html
import json
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "quickshell" / "dictionary.json"
UA = "desktop-tools/1.0"
TTL = 7 * 86400
HISTORY = 12
MAX_RESULTS = 400
LANGS = {"en": "English", "fr": "French", "es": "Spanish", "ja": "Japanese", "zh": "Chinese"}
MAX_SECTIONS = 3
MAX_POS = 4
MAX_SENSES = 8

KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
KANA_ONLY = re.compile(r"^[\u3040-\u30ff\u31f0-\u31ff\u30fc]+$")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
FR_CHARS = re.compile(r"[\u00e0\u00e2\u00e7\u00e8\u00ea\u00eb\u00ee\u00ef\u00f4\u00fb\u00f9\u0153\u00e6]", re.I)
ES_CHARS = re.compile(r"[\u00f1\u00e1\u00ed\u00f3\u00fa\u00bf\u00a1]", re.I)


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def order(word):
    if KANA.search(word):
        return ["ja", "zh"]
    if HAN.search(word):
        return ["zh", "ja"]
    if FR_CHARS.search(word) and not ES_CHARS.search(word):
        return ["fr", "es", "en"]
    if ES_CHARS.search(word):
        return ["es", "fr", "en"]
    return ["en", "fr", "es"]


def page_url(word, lang, host="en"):
    anchor = "#" + LANGS[lang] if host == "en" and lang in LANGS else ""
    return f"https://{host}.wiktionary.org/wiki/" + urllib.parse.quote(word.replace(" ", "_")) + anchor


def get(url, timeout=8):
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def strip_html(s):
    s = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", s, flags=re.S)
    s = re.sub(r"<sup[^>]*>.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r"\s+([,.;:)])", r"\1", s)


def rest_sections(data, langs):
    out = []
    for lang in langs:
        entries = []
        for block in data.get(lang, []):
            senses = []
            for d in block.get("definitions", []):
                text = strip_html(d.get("definition", ""))
                if not text:
                    continue
                exs = []
                for ex in d.get("parsedExamples", [])[:1]:
                    t = strip_html(ex.get("example", ""))
                    if t and len(t) < 240:
                        exs.append({"text": t, "translation": strip_html(ex.get("translation", ""))})
                senses.append({"text": text, "examples": exs})
            if senses:
                entries.append({"pos": block.get("partOfSpeech", ""), "senses": senses[:MAX_SENSES]})
        if entries:
            out.append({"lang": lang, "language": LANGS[lang], "source": "en.wiktionary", "reading": "", "entries": entries[:MAX_POS]})
    return out


def section_text(raw, header):
    m = re.search(r"^==\s*" + header + r"\s*==\s*$", raw, re.M)
    if not m:
        return ""
    rest = raw[m.end():]
    n = re.search(r"^==[^=].*==\s*$", rest, re.M)
    return rest[:n.start()] if n else rest


def readings(raw, lang):
    found = []
    if lang == "ja":
        sec = section_text(raw, "Japanese")
        for m in re.finditer(r"\{\{ja-(?:pron|noun|verb|adj|pos|phrase|verb-suru)\|([^{}]*)\}\}", sec):
            for arg in m.group(1).split("|"):
                arg = arg.strip()
                if "=" not in arg and KANA_ONLY.match(arg) and arg not in found:
                    found.append(arg)
    elif lang == "zh":
        sec = section_text(raw, "Chinese")
        for m in re.finditer(r"\|m=([^\n|}]+)", sec):
            first = m.group(1).split(",")[0].strip()
            if first and first not in found:
                found.append(first)
    return ", ".join(found[:3])


LABEL_TEMPLATES = {"lexique", "term", "terme", "csem", "uso", "\u00e1mbito", "contexto", "registre", "info lex"}
FR_LINKS = {"w", "lien", "ws", "lien web", "nom w pc"}
EN_LINKS = {"l", "m", "link", "mention", "l-self", "ll"}
EN_LABELS = {"lb", "lbl", "label", "tlb", "lb-lite"}
EN_PAREN = {"gloss", "gl", "q", "qualifier", "i", "qual", "sense", "s"}
EN_PLAIN = {"n-g", "ngd", "non-gloss", "non-gloss definition", "taxfmt", "vern", "taxlink"}
POS_NAMES = {
    "noun", "verb", "adjective", "adverb", "pronoun", "particle", "classifier", "numeral", "conjunction", "preposition",
    "postposition", "interjection", "proper noun", "phrase", "proverb", "idiom", "suffix", "prefix", "determiner", "counter",
    "article", "affix", "contraction", "adnominal", "auxiliary", "symbol", "letter", "infix", "circumfix", "participle",
}


def render_fr(name, pos, named, title):
    if name in ("exemple", "ejemplo"):
        return pos[0] if pos else ""
    if name == "plm":
        word = pos[0] if pos else title
        return word[:1].upper() + word[1:]
    if name in FR_LINKS:
        return pos[0] if pos else ""
    if name in LABEL_TEMPLATES:
        labels = [p for p in pos if p not in ("fr", "es")]
        return "(" + ", ".join(labels) + ")" if labels else ""
    if name in ("e", "er", "re", "ers", "res"):
        return name
    if (not pos or pos == ["fr"] or pos == ["es"]) and not named and re.match(r"^[^\W\d_][\w\s'-]*$", name) and len(name) > 2:
        return "(" + name + ")"
    return ""


def zh_example(text):
    text = re.sub(r"\{[^}]*\}", "", text)
    text = text.replace("^", "").replace("--", "").replace("-", "")
    return re.sub(r"(?<=[^\x00-\x7f]) (?=[^\x00-\x7f])", "", text).strip()


def render_en(name, pos, named, title):
    if name in EN_LINKS:
        return (pos[2] if len(pos) > 2 and pos[2] else pos[1]) if len(pos) > 1 else ""
    if name == "w":
        return (pos[1] if len(pos) > 1 else pos[0]) if pos else ""
    if name in EN_LABELS:
        labels = [p for p in pos[1:] if p not in ("_", "and", "or")]
        return "(" + ", ".join(labels) + ")" if labels else ""
    if name in EN_PAREN:
        return "(" + pos[0] + ")" if pos else ""
    if name in EN_PLAIN:
        return pos[0] if pos else ""
    if name in ("zh-x", "ja-usex", "ux", "uxi", "zh-usex"):
        if name in ("ux", "uxi"):
            pos = pos[1:]
        if not pos:
            return ""
        ex = zh_example(pos[0]) if name.startswith("zh") else pos[0]
        tr = pos[1] if len(pos) > 1 and name != "ja-usex" else (pos[2] if len(pos) > 2 else named.get("t", ""))
        return ex + ("\x1f" + tr if tr else "")
    if name.endswith(" of") or name in ("alt form", "alt sp", "abbr of", "clipping of", "syn of"):
        target = pos[1] if len(pos) > 1 else (pos[0] if pos else "")
        label = {"alt form": "alternative form of", "alt sp": "alternative spelling of", "abbr of": "abbreviation of", "syn of": "synonym of"}.get(name, name)
        return label + " " + target
    return ""


def render_template(body, title, mode):
    parts = [p.strip() for p in body.split("|")]
    name = parts[0].lower()
    pos = [p for p in parts[1:] if "=" not in p]
    named = dict(p.split("=", 1) for p in parts[1:] if "=" in p)
    return render_en(name, pos, named, title) if mode == "en" else render_fr(name, pos, named, title)


def wikitext_clean(s, title, mode):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<[^>]*>", " ", s)
    s = re.sub(r"<[^>]*$", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]|]*)\]\]", r"\1", s)
    for _ in range(6):
        new = re.sub(r"\{\{([^{}]*)\}\}", lambda m: render_template(m.group(1), title, mode), s)
        if new == s:
            break
        s = new
    if "{{" in s or "}}" in s:
        return ""
    s = re.sub(r"\[https?://\S+ ([^\]]*)\]", r"\1", s)
    s = s.replace("'''", "").replace("''", "")
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\r\n]+", " ", s).strip()
    return re.sub(r"\s+([,.;:)])", r"\1", s)


def example_obj(text):
    ex, _, tr = text.partition("\x1f")
    ex, tr = ex.strip(), tr.strip()
    if not ex or len(ex) > 240:
        return None
    return {"text": ex, "translation": tr}


def raw_section(raw, lang, title):
    sec = section_text(raw, LANGS[lang])
    if not sec:
        return None, None
    see = None
    m = re.search(r"\{\{zh-see\|([^|}]+)", sec) if lang == "zh" else None
    if m:
        see = m.group(1).strip()
    entries = []
    cur = None
    last = None
    for line in sec.splitlines():
        h = re.match(r"^(=+)\s*([^=]+?)\s*\1\s*$", line)
        if h:
            name = h.group(2).strip().lower()
            last = None
            if name in POS_NAMES:
                cur = {"pos": h.group(2).strip(), "senses": []}
                entries.append(cur)
            elif name == "definitions":
                cur = {"pos": "", "senses": []}
                entries.append(cur)
            else:
                cur = None
            continue
        if cur is None:
            continue
        hm = re.match(r"^\{\{head\|zh\|([^|}]+)", line)
        if hm and not cur["pos"]:
            p = hm.group(1).strip()
            cur["pos"] = "Character" if p == "hanzi" else p[:1].upper() + p[1:]
            continue
        if re.match(r"^#(?![*:#])", line):
            text = wikitext_clean(line[1:], title, "en").replace("\x1f", " ")
            last = {"text": text, "examples": []} if text and not re.match(r"^\([^()]*\)$", text) else None
            if last:
                cur["senses"].append(last)
        elif line.startswith("#:") and last is not None and not last["examples"]:
            ex = example_obj(wikitext_clean(line[2:], title, "en"))
            if ex:
                last["examples"].append(ex)
    entries = [{"pos": e["pos"] or "Definitions", "senses": e["senses"][:MAX_SENSES]} for e in entries if e["senses"]]
    if not entries:
        return None, see
    return {"lang": lang, "language": LANGS[lang], "source": "en.wiktionary", "reading": "", "entries": entries[:MAX_POS]}, see


def native_section(raw, lang, title):
    if lang == "fr":
        sec = section_text(raw, r"\{\{langue\|fr\}\}")
        pos_re = re.compile(r"^===+\s*\{\{S\|([^|}]+)\|fr[^}]*\}\}\s*===+\s*$")
    else:
        sec = section_text(raw, r"\{\{lengua\|es\}\}")
        pos_re = re.compile(r"^===+\s*\{\{([^|}]+)\|es[^}]*\}\}\s*===+\s*$")
    entries = []
    cur = None
    last = None
    for line in sec.splitlines():
        if line.startswith("=="):
            m = pos_re.match(line)
            cur = None
            last = None
            if m:
                cur = {"pos": m.group(1).strip(), "senses": []}
                entries.append(cur)
            continue
        if cur is None:
            continue
        if lang == "fr":
            if re.match(r"^#(?![*:#])", line):
                text = wikitext_clean(line[1:], title, "fr")
                last = {"text": text, "examples": []} if text else None
                if last:
                    cur["senses"].append(last)
            elif line.startswith("#*") and last is not None and not last["examples"]:
                ex = example_obj(wikitext_clean(line[2:], title, "fr"))
                if ex:
                    last["examples"].append(ex)
        else:
            m = re.match(r"^;\s*\d+([^:]*):\s*(.*)$", line)
            if m:
                prefix = wikitext_clean(m.group(1), title, "es")
                text = wikitext_clean(m.group(2), title, "es")
                if text:
                    last = {"text": (prefix + " " + text).strip(), "examples": []}
                    cur["senses"].append(last)
                else:
                    last = None
            elif last is not None and not last["examples"] and "{{ejemplo" in line:
                ex = example_obj(wikitext_clean(line.lstrip(":* "), title, "es"))
                if ex:
                    last["examples"].append(ex)
    entries = [{"pos": e["pos"], "senses": e["senses"][:MAX_SENSES]} for e in entries if e["senses"]]
    if not entries:
        return None
    return {"lang": lang, "language": LANGS[lang], "source": lang + ".wiktionary", "reading": "", "entries": entries[:MAX_POS], "url": page_url(title, lang, lang)}


def raw_url(word, host="en"):
    return f"https://{host}.wiktionary.org/w/index.php?title=" + urllib.parse.quote(word.replace(" ", "_"), safe="") + "&action=raw"


def fetch_native(word, lang):
    try:
        raw = get(raw_url(word, lang))
    except Exception:
        return None
    return native_section(raw, lang, word)


def fetch_pair(pool, word):
    import urllib.error
    q = urllib.parse.quote(word.replace(" ", "_"), safe="")
    raw_future = pool.submit(get, raw_url(word))
    data = None
    rest_error = None
    try:
        data = json.loads(get("https://en.wiktionary.org/api/rest_v1/page/definition/" + q))
    except urllib.error.HTTPError as e:
        if e.code != 404:
            rest_error = e
    except (urllib.error.URLError, OSError, ValueError) as e:
        rest_error = e
    try:
        raw = raw_future.result()
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise
        raw = ""
    except Exception:
        if rest_error is not None:
            raise rest_error
        raw = ""
    return data, raw


def lookup(word, forced):
    from concurrent.futures import ThreadPoolExecutor
    langs = [forced] if forced else order(word)
    candidates = [word] + ([word.lower()] if word.lower() != word else [])
    data, raw, used = None, "", word
    with ThreadPoolExecutor(max_workers=3) as pool:
        native_future = pool.submit(fetch_native, word, forced) if forced in ("fr", "es") else None
        for cand in candidates:
            data, raw = fetch_pair(pool, cand)
            used = cand
            if data or raw:
                break
        rest = {s["lang"]: s for s in rest_sections(data or {}, langs)}
        sections = []
        for lang in langs:
            sec = rest.get(lang)
            see = None
            reading_raw = raw
            if sec is None and raw:
                sec, see = raw_section(raw, lang, used)
            if sec is None and see:
                try:
                    reading_raw = get(raw_url(see))
                    sec, _ = raw_section(reading_raw, lang, see)
                except Exception:
                    sec = None
                if sec:
                    sec["note"] = "Traditional form: " + see
            if sec is None:
                continue
            sec["url"] = page_url(used, lang)
            if reading_raw and lang in ("ja", "zh"):
                sec["reading"] = readings(reading_raw, lang)
            sections.append(sec)
        thin = [s for s in sections if s["lang"] in ("fr", "es") and sum(len(e["senses"]) for e in s["entries"]) < 3]
        native = None
        if native_future is not None:
            native = native_future.result()
        elif thin:
            native = fetch_native(used, thin[0]["lang"])
        if native:
            at = next((i + 1 for i, s in enumerate(sections) if s["lang"] == native["lang"]), len(sections))
            sections.insert(at, native)
    found = set(k for k in (data or {}) if k in LANGS)
    found |= set(k for k, v in LANGS.items() if raw and re.search(r"^==\s*" + v + r"\s*==\s*$", raw, re.M))
    others = [k for k in LANGS if k in found and k not in langs]
    if not sections:
        msg = "No entry for this word"
        if forced:
            msg += " in " + LANGS[forced]
        if others:
            msg += " (found in " + ", ".join(LANGS[k] for k in others) + ")"
        return {"ok": False, "query": word, "lang": forced or "", "error": msg, "others": others, "url": page_url(word, forced or langs[0])}
    return {"ok": True, "query": word, "lang": forced or "", "sections": sections[:MAX_SECTIONS], "others": others, "url": sections[0]["url"]}


def load_cache():
    try:
        data = json.loads(CACHE.read_text())
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def save_cache(data):
    now = time.time()
    res = {k: v for k, v in data.get("results", {}).items() if now - v.get("time", 0) < TTL}
    if len(res) > MAX_RESULTS:
        res = dict(sorted(res.items(), key=lambda kv: kv[1].get("time", 0))[-MAX_RESULTS:])
    data["results"] = res
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False))
    tmp.replace(CACHE)


def remember(data, word):
    hist = [h for h in data.get("history", []) if h.get("query", "") != word]
    data["history"] = [{"query": word, "time": time.time()}] + hist[:HISTORY - 1]


def define(word, forced):
    data = load_cache()
    key = f"{forced or 'auto'}|{word}"
    hit = data.get("results", {}).get(key)
    if hit and time.time() - hit.get("time", 0) < TTL:
        remember(data, word)
        save_cache(data)
        return dict(hit, cached=True, history=data["history"])
    try:
        out = lookup(word, forced)
    except Exception as e:
        reason = getattr(e, "reason", None) or getattr(e, "code", None) or type(e).__name__
        return {"ok": False, "query": word, "lang": forced or "", "retry": True, "error": f"Could not reach Wiktionary ({reason})",
                "url": page_url(word, forced or order(word)[0])}
    if out["ok"] or not out.get("others"):
        out["time"] = time.time()
        data.setdefault("results", {})[key] = out
    remember(data, word)
    save_cache(data)
    return dict(out, history=data["history"])


def main():
    args = sys.argv[1:]
    if args == ["--history"]:
        emit({"history": load_cache().get("history", [])})
        return
    if args == ["--clear"]:
        save_cache({})
        emit({"history": []})
        return
    forced = None
    if len(args) >= 2 and args[0] == "--lang":
        forced = args[1] if args[1] in LANGS else None
        args = args[2:]
    word = " ".join(args).strip()
    if not word:
        print("usage: dictionary.py [--lang en|fr|es|ja|zh] WORD | --history | --clear", file=sys.stderr)
        sys.exit(2)
    emit(define(word, forced))


if __name__ == "__main__":
    main()
