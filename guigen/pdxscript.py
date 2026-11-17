"""Small Paradox-script helpers: indentation, a tokenizer/parser, and block extraction."""
import re


def indent(s, n):
    """Indent every non-empty line by n tabs."""
    pad = "\t" * n
    return "".join(pad + l + "\n" if l.strip() else "\n" for l in s.strip("\n").split("\n"))


_TOK = re.compile(r'"[^"]*"|[{}]|[<>!]=|[=<>]|[^\s{}=<>"]+')


def tokenize(text):
    text = re.sub(r"#[^\n]*", "", text)
    return _TOK.findall(text)


def parse(text):
    """Parse script into a list of (key, op, value) where value is a str or a nested list."""
    toks = tokenize(text)
    pos = 0

    def block():
        nonlocal pos
        out = []
        while pos < len(toks):
            t = toks[pos]
            if t == "}":
                pos += 1
                return out
            if t == "{":                       # bare list item block
                pos += 1
                out.append((None, None, block()))
                continue
            pos += 1
            if pos < len(toks) and toks[pos] in ("=", "<", ">", "<=", ">=", "!="):
                op = toks[pos]
                pos += 1
                if pos < len(toks) and toks[pos] == "{":
                    pos += 1
                    out.append((t, op, block()))
                else:
                    v = toks[pos] if pos < len(toks) else ""
                    pos += 1
                    out.append((t, op, v.strip('"')))
            else:
                out.append((t.strip('"'), None, None))  # bare value (e.g. list of numbers)
        return out

    return block()


def find_block(text, name):
    """Return the full `name = { ... }` block at top level of `text` (LF text), or None."""
    m = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if not m:
        return None
    depth, i = 0, m.end() - 1
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(text) and text[end] == "\n":
                    end += 1
                return text[m.start():end]
        i += 1
    return None


def top_level_names(text):
    """Names defined at column 0 as `name = {` (scripted effects / triggers files)."""
    return set(re.findall(r"(?m)^([A-Za-z_][\w.\-]*)\s*=\s*\{", text))
