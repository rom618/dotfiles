#!/usr/bin/env python3
import html
import json
import os
import re
import sys
import time
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "quickshell" / "translate.json"
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "quickshell-tools" / "translate.json"
UA = "Mozilla/5.0 (X11; Linux x86_64; rv:140.0) Gecko/20100101 Firefox/140.0"
TTL = 7 * 86400
HISTORY = 12
MAX_RESULTS = 400
LANGS = {"en": "English", "fr": "French", "es": "Spanish", "ja": "Japanese", "zh": "Chinese"}
LINGUEE = {"en": "english", "fr": "french", "es": "spanish", "ja": "japanese", "zh": "chinese"}
LINGUEE_PAIRS = {frozenset(p) for p in (("en", "fr"), ("en", "es"), ("en", "ja"), ("en", "zh"), ("fr", "es"))}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}

KANA = re.compile(r"[\u3040-\u30ff\u31f0-\u31ff]")
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
FR_CHARS = re.compile(r"[\u00e0\u00e2\u00e7\u00e8\u00ea\u00eb\u00ee\u00ef\u00f4\u00fb\u00f9\u0153\u00e6]", re.I)
ES_CHARS = re.compile(r"[\u00f1\u00e1\u00ed\u00f3\u00fa\u00bf\u00a1]", re.I)
FR_WORDS = {"le", "la", "les", "un", "une", "des", "je", "tu", "il", "elle", "est", "et", "du", "de", "ce", "pas", "nous", "vous", "avec", "pour", "dans", "sur", "qui", "au", "aux", "mon", "ma", "mes", "ne", "suis", "c'est", "j'ai", "on"}
ES_WORDS = {"el", "los", "las", "una", "es", "y", "del", "que", "por", "con", "para", "yo", "pero", "muy", "esta", "este", "como", "mi", "su", "lo", "al", "se", "estoy", "hay", "no"}
EN_WORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "i", "you", "it", "in", "on", "with", "for", "this", "that", "be", "was", "my", "your", "we", "not", "do", "what", "how"}


def emit(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def guess_source(text):
    if KANA.search(text):
        return "ja"
    if HAN.search(text):
        return "han"
    if FR_CHARS.search(text) and not ES_CHARS.search(text):
        return "fr"
    if ES_CHARS.search(text):
        return "es"
    words = re.findall(r"[a-z']+", text.lower())
    if len(words) < 2:
        return None
    score = {"en": 0, "fr": 0, "es": 0}
    for w in words:
        score["en"] += w in EN_WORDS
        score["fr"] += w in FR_WORDS
        score["es"] += w in ES_WORDS
    best = max(score, key=score.get)
    ranked = sorted(score.values(), reverse=True)
    return best if ranked[0] > ranked[1] else None


def is_short(text):
    if HAN.search(text) or KANA.search(text):
        return len(text) <= 8 and not re.search(r"[\u3002\uff01\uff1f\uff0c\u3001.!?,]", text)
    return len(text.split()) <= 4 and not re.search(r"[.!?;]\s*$", text) and len(text) <= 60


def linguee_url(src, dst, text):
    a, b = (src, dst) if src and src != dst else ("en", dst if dst != "en" else "fr")
    if frozenset((a, b)) not in LINGUEE_PAIRS:
        a, b = ("en", b) if b != "en" else (a, "en")
    return f"https://www.linguee.com/{LINGUEE[a]}-{LINGUEE[b]}/search?source=auto&query=" + urllib.parse.quote_plus(text)


def deepl_url(src, dst, text):
    return f"https://www.deepl.com/translator#{src or 'en'}/{dst}/" + urllib.parse.quote(text, safe="")


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


class LingueeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.src_lang = None
        self.section = None
        self.lemmas = {"exact": [], "inexact": []}
        self.lemma = None
        self.trans = None
        self.example = None
        self.corpus = []
        self.row = None
        self.cell = None

    def has(self, cls):
        return any(cls in c for _, c, _ in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        classes = set((a.get("class") or "").split())
        ident = a.get("id") or ""
        if tag not in VOID:
            self.stack.append((tag, classes, ident))
        if "isMainTerm" in classes or "isForeignTerm" in classes:
            self.src_lang = (a.get("data-source-lang") or "").lower() or self.src_lang
        if tag == "div" and classes & {"exact", "inexact"} and self.has_id("dictionary"):
            self.section = "exact" if "exact" in classes else "inexact"
        if tag == "div" and "lemma" in classes and self.section:
            self.lemma = {"word": "", "pos": "", "main": [], "less": [], "examples": []}
            self.lemmas[self.section].append(self.lemma)
        if tag == "div" and "translation" in classes and self.lemma is not None:
            self.trans = {"text": "", "type": "", "examples": []}
            (self.lemma["less"] if self.has("translation_group") else self.lemma["main"]).append(self.trans)
        if tag == "span" and "tag_type" in classes and self.trans is not None and a.get("title"):
            self.trans["type"] = clean(a["title"])
        if tag == "div" and "example" in classes and self.trans is not None:
            self.example = {"s": "", "t": ""}
            self.trans["examples"].append(self.example)
        if tag == "tr" and self.has_id("result_table"):
            self.row = {"s": "", "t": "", "cut": False}
            self.corpus.append(self.row)
        if tag == "td" and self.row is not None and "sentence" in classes:
            self.cell = "s" if "left" in classes else "t"
        if self.row is not None and any(k.startswith(("placeholder", "shortened")) for k in classes):
            self.row["cut"] = True

    def has_id(self, ident):
        return any(i == ident for _, _, i in self.stack)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        while self.stack:
            t, classes, _ = self.stack.pop()
            if "lemma" in classes:
                self.lemma = None
            if "translation" in classes:
                self.trans = None
            if "example" in classes:
                self.example = None
            if t == "td":
                self.cell = None
            if t == "tr":
                self.row = None
            if t == tag:
                break

    def handle_data(self, data):
        if not self.stack:
            return
        if self.lemma is not None and self.trans is None:
            if self.has("tag_wordtype"):
                self.lemma["pos"] += data
            elif self.has("tag_lemma") and not self.has("tag_lemma_context") and not self.has("tag_forms") and self.inside_link():
                self.lemma["word"] += data
        if self.trans is not None:
            if self.example is not None:
                if self.has("tag_s"):
                    self.example["s"] += data
                elif self.has("tag_t"):
                    self.example["t"] += data
            elif self.has("tag_trans") and self.inside_link() and not self.has("tag_type"):
                self.trans["text"] += data
        if self.row is not None and self.cell:
            if any(k.startswith(("source_url", "placeholder", "shortened", "behindLinkDiv")) for _, c, _ in self.stack for k in c):
                return
            self.row[self.cell] += data

    def inside_link(self):
        return any(t == "a" and "dictLink" in c for t, c, _ in self.stack)


def fetch_linguee(src, dst, text):
    import urllib.request
    url = f"https://www.linguee.com/{LINGUEE[src]}-{LINGUEE[dst]}/search?source=auto&query=" + urllib.parse.quote_plus(text)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.7"})
    with urllib.request.urlopen(req, timeout=8) as r:
        raw = r.read()
        charset = r.headers.get_content_charset() or "utf-8"
    m = re.search(rb"charset=['\"]?([A-Za-z0-9_-]+)", raw[:2000])
    if m:
        charset = m.group(1).decode()
    if charset.lower() in ("iso-8859-1", "iso-8859-15", "latin-1", "latin1"):
        charset = "cp1252" if charset.lower() in ("iso-8859-1", "latin-1", "latin1") else charset
    p = LingueeParser()
    p.feed(raw.decode(charset, "replace"))
    p.close()
    return url, p


def lemma_out(lem):
    def tr(t):
        return {"text": clean(t["text"]), "type": t["type"].replace("\u00a0", " ")}
    return {
        "word": clean(lem["word"]),
        "pos": clean(lem["pos"]),
        "main": [tr(t) for t in lem["main"] if clean(t["text"])][:6],
        "less": [tr(t) for t in lem["less"] if clean(t["text"])][:10],
    }


def linguee_result(src, dst, text, single):
    url, p = fetch_linguee(src, dst, text)
    lemmas = p.lemmas["exact"] or (p.lemmas["inexact"] if single else [])
    entries = [lemma_out(l) for l in lemmas]
    entries = [e for e in entries if e["main"] or e["less"]][:4]
    examples = []
    for lem in lemmas:
        for t in lem["main"]:
            for ex in t["examples"]:
                s, tt = clean(ex["s"]), clean(ex["t"])
                if s and tt and len(examples) < 3:
                    examples.append({"s": s, "t": tt})
    corpus = []
    for row in p.corpus:
        s, t = clean(row["s"]), clean(row["t"])
        if s and t and len(s) < 200 and len(t) < 200:
            if row["cut"]:
                s, t = s + " ...", t + " ..."
            corpus.append({"s": s, "t": t})
    detected = p.src_lang if p.src_lang in LANGS else None
    if not detected:
        corpus = []
    corpus.sort(key=lambda x: len(x["s"]))
    if detected and detected == dst:
        dst = src
    real_src = detected or src
    if not entries:
        return {"found": False, "url": url, "src": real_src, "corpus": corpus[:3]}
    while len(examples) < 3 and corpus:
        examples.append(corpus.pop(0))
    return {
        "found": True, "ok": True, "engine": "linguee", "src": real_src, "dst": dst,
        "entries": entries, "examples": examples, "url": url,
    }


def system_prompt(dst):
    name = LANGS[dst]
    reading = ""
    fmt = '{"source": "<ISO 639-1 code of the input language>", "meaning": "...", "translation": "..."}'
    if dst == "ja":
        reading = ' Field "reading": the translation written fully in hiragana.'
        fmt = fmt[:-1] + ', "reading": "..."}'
    elif dst == "zh":
        reading = ' Write simplified Chinese. Field "reading": the translation in Hanyu Pinyin with tone marks, words separated by spaces.'
        fmt = fmt[:-1] + ', "reading": "..."}'
    return (
        f"You translate text into {name}.\n"
        'Step 1, field "meaning": in simple ENGLISH, say what the text really means, replacing every idiom or figure of speech by its plain sense '
        '(example: "it is raining cats and dogs" -> "it is raining very hard").\n'
        f'Step 2, field "translation": write how a native {name} speaker would naturally say that meaning. Translate the meaning from step 1, '
        "not the original words: never keep the imagery of an idiom unless " + name + " uses the very same image. "
        "Keep the register (casual stays casual, polite stays polite), names, numbers and line breaks. "
        "If the input is a single word or short phrase, give its most common translation." + reading + "\n"
        "Answer with JSON only: " + fmt
    )


def parse_llm(content):
    s = content.strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            if isinstance(d, dict) and str(d.get("translation", "")).strip():
                return d
        except ValueError:
            pass
    return {"translation": s}


def llm_config():
    try:
        c = json.loads(CONFIG.read_text())
    except (OSError, ValueError):
        return None
    if not isinstance(c, dict) or not c.get("url") or not c.get("model"):
        return None
    c.setdefault("name", c["model"])
    return c


def llm(text, dst, c):
    import urllib.request
    headers = {"Content-Type": "application/json", "User-Agent": "desktop-tools/1.0"}
    if c.get("keyFile"):
        key_file = Path(os.path.expanduser(c["keyFile"]))
        if not key_file.is_file():
            raise RuntimeError("nokey")
        key = key_file.read_text().strip()
        headers.update({"Authorization": "Bearer " + key, "x-api-key": key})
    body = dict(c.get("extra", {}))
    body.update({
        "model": c["model"], "temperature": 0.2,
        "messages": [{"role": "system", "content": system_prompt(dst)}, {"role": "user", "content": text}],
    })
    req = urllib.request.Request(c["url"], data=json.dumps(body).encode(), headers=headers)
    with urllib.request.urlopen(req, timeout=c.get("timeout", 40)) as r:
        d = json.loads(r.read())
    return parse_llm(d["choices"][0]["message"]["content"])


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


def remember(data, text, dst):
    hist = [h for h in data.get("history", []) if h.get("query", "").lower() != text.lower()]
    data["history"] = [{"query": text, "time": time.time()}] + hist[:HISTORY - 1]
    data["target"] = dst


def plan(text, dst, src):
    if src == "han":
        if dst == "zh":
            src = "ja"
        elif dst == "ja":
            src = "zh"
    if src in LANGS and src == dst:
        dst = "en" if src != "en" else "fr"
    if src in LANGS:
        return src, dst, [src] if frozenset((src, dst)) in LINGUEE_PAIRS else []
    if src == "han":
        return None, dst, ["zh", "ja"] if dst == "en" else []
    if dst == "en":
        return None, dst, ["fr", "es"]
    if dst in ("fr", "es"):
        return None, dst, ["en", "es" if dst == "fr" else "fr"]
    return None, dst, ["en"]


def translate(text, dst, forced_src=None):
    data = load_cache()
    key = f"{forced_src or 'auto'}|{dst}|{text.lower()}"
    hit = data.get("results", {}).get(key)
    if hit and time.time() - hit.get("time", 0) < TTL:
        remember(data, text, dst)
        save_cache(data)
        return dict(hit, cached=True, query=text, history=data["history"])
    import socket
    import urllib.error
    src, dst, tries = plan(text, dst, forced_src or guess_source(text))
    short = is_short(text)
    single = len(text.split()) == 1
    out = None
    corpus = []
    link = None
    net_error = None
    if short:
        for i, s in enumerate(tries[:2]):
            try:
                r = linguee_result(s, dst, text, single)
            except (urllib.error.URLError, TimeoutError, OSError, socket.timeout) as e:
                net_error = e
                break
            link = link or r["url"]
            corpus = corpus or r.get("corpus", [])
            if r["found"]:
                out = r
                break
            if r.get("src") and r["src"] != s:
                break
    if out is None:
        guessed = src if src in LANGS else None
        fallback = link or (linguee_url(guessed, dst, text) if short else deepl_url(guessed, dst, text))
        label = "Open in Linguee" if short else "Open in DeepL"
        c = llm_config()
        if c is None:
            return {"ok": False, "query": text, "dst": dst, "url": fallback, "urlLabel": label,
                    "error": "Not found in Linguee. Sentences need a translation model: see " + str(CONFIG)}
        name = c["name"]
        emit({"stage": "llm", "query": text, "name": name})
        t0 = time.time()
        try:
            d = llm(text, dst, c)
        except RuntimeError:
            return {"ok": False, "query": text, "dst": dst, "error": f"No key file for {name}: {c.get('keyFile')}", "url": fallback, "urlLabel": label}
        except (socket.timeout, TimeoutError):
            return {"ok": False, "query": text, "dst": dst, "retry": True, "url": fallback, "urlLabel": label,
                    "error": f"{name} did not answer in time."}
        except urllib.error.HTTPError as e:
            return {"ok": False, "query": text, "dst": dst, "retry": True, "url": fallback, "urlLabel": label,
                    "error": f"{name} is not available right now (HTTP {e.code})."}
        except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
            reason = getattr(e, "reason", None)
            offline = net_error is not None or isinstance(reason, socket.gaierror)
            if isinstance(reason, (socket.timeout, TimeoutError)):
                msg = f"{name} did not answer in time."
            else:
                msg = "No connection." if offline else f"Could not reach {name}."
            return {"ok": False, "query": text, "dst": dst, "retry": True, "url": fallback, "urlLabel": label, "error": msg}
        s = str(d.get("source", "")).lower()[:2]
        out = {
            "ok": True, "engine": "llm", "engineName": name, "src": s if s in LANGS else (guessed or ""), "dst": dst,
            "translation": str(d.get("translation", "")).strip(),
            "reading": str(d.get("reading", "") or "").strip() if dst in ("ja", "zh") else "",
            "meaning": str(d.get("meaning", "") or "").strip() if dst != "en" else "",
            "examples": corpus[:3], "url": fallback, "urlLabel": label, "seconds": round(time.time() - t0, 1),
        }
    else:
        out["urlLabel"] = "Open in Linguee"
    out["time"] = time.time()
    out["query"] = text
    data.setdefault("results", {})[key] = out
    remember(data, text, dst)
    save_cache(data)
    return dict(out, history=data["history"])


def main():
    args = sys.argv[1:]
    if args == ["--state"]:
        data = load_cache()
        emit({"target": data.get("target", "fr"), "history": data.get("history", [])})
        return
    if args == ["--clear"]:
        save_cache({})
        emit({"target": "fr", "history": []})
        return
    dst = "fr"
    src = None
    while args and args[0] in ("--to", "--from"):
        if len(args) < 2:
            break
        if args[0] == "--to":
            dst = args[1]
        else:
            src = args[1] if args[1] in LANGS else None
        args = args[2:]
    text = " ".join(args).strip()
    if not text or dst not in LANGS:
        print("usage: translate.py [--to en|fr|es|ja|zh] [--from LANG] TEXT | --state | --clear", file=sys.stderr)
        sys.exit(2)
    try:
        emit(translate(text, dst, src))
    except Exception as e:
        emit({"ok": False, "query": text, "dst": dst, "retry": True, "error": f"Translate failed ({type(e).__name__})",
              "url": linguee_url(None, dst, text) if is_short(text) else deepl_url(None, dst, text)})


if __name__ == "__main__":
    main()
