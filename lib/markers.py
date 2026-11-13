import re

MARK = re.compile(r"^(?P<indent>\s*)(?P<token>\S+?)\s*share:(?P<kind>begin|else|end)(?:\s+(?P<name>[a-z0-9-]+))?\s*$")
PRIVATE = "private"


class MarkerError(ValueError):
    pass


def _uncomment(line, token, where):
    stripped = line.lstrip()
    if not stripped.startswith(token):
        raise MarkerError(f"{where}: else line is not commented with {token!r}: {line!r}")
    rest = stripped[len(token):]
    if rest.startswith(" "):
        rest = rest[1:]
    return rest


def parse(text, where="?"):
    lines = text.split("\n")
    blocks = []
    region = None
    for no, line in enumerate(lines, 1):
        m = MARK.match(line)
        if not m:
            if region is None:
                blocks.append(("text", line))
            elif region["in_else"]:
                region["else"].append(_uncomment(line, region["token"], f"{where}:{no}") if line.strip() else "")
                region["else_raw"].append(line)
            else:
                region["body"].append(line)
            continue
        kind = m.group("kind")
        if kind == "begin":
            if region is not None:
                raise MarkerError(f"{where}:{no}: nested share:begin")
            if not m.group("name"):
                raise MarkerError(f"{where}:{no}: share:begin without a name")
            region = {"name": m.group("name"), "token": m.group("token"), "body": [], "else": [], "else_raw": [],
                      "in_else": False, "begin": line, "else_line": None, "line": no}
        elif kind == "else":
            if region is None or region["in_else"]:
                raise MarkerError(f"{where}:{no}: share:else outside a region")
            region["in_else"] = True
            region["else_line"] = line
        else:
            if region is None:
                raise MarkerError(f"{where}:{no}: share:end without share:begin")
            region["end"] = line
            blocks.append(("region", region))
            region = None
    if region is not None:
        raise MarkerError(f"{where}:{region['line']}: share:begin {region['name']} never closed")
    return blocks


def names(text, where="?"):
    return sorted({b[1]["name"] for b in parse(text, where) if b[0] == "region"})


def resolve_private(text, where="?"):
    out = []
    for kind, value in parse(text, where):
        if kind == "text":
            out.append(value)
        elif value["name"] == PRIVATE:
            out.extend(value["else"])
        else:
            out.append(value["begin"])
            out.extend(value["body"])
            if value["else_line"] is not None:
                out.append(value["else_line"])
                out.extend(value["else_raw"])
            out.append(value["end"])
    return "\n".join(out)


def render(text, selected, where="?"):
    out = []
    for kind, value in parse(text, where):
        if kind == "text":
            out.append(value)
        elif value["name"] != PRIVATE and value["name"] in selected:
            out.extend(value["body"])
        else:
            out.extend(value["else"])
    return "\n".join(out)


def live(text, where="?"):
    out = []
    for kind, value in parse(text, where):
        if kind == "text":
            out.append(value)
        else:
            out.extend(value["body"])
    return "\n".join(out)
