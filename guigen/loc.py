"""Localisation, scripted localisation and text helpers.

Text rules enforced on every entry (they raise LocError):
* no em-dash (U+2014) and no "--";
* no real line breaks: write a literal backslash-n (use `NL` or the helpers below).

Colour conventions (see `c`): §Y economy, §L politics, §O security, §C places; values §G good, §R bad.
"""
import re

NL = "\\n"                      # literal backslash-n, as the game wants it in .yml
BULLET = NL + "£white_dot "


class LocError(ValueError):
    pass


def check_text(key, text):
    if "—" in text:
        raise LocError(f"{key}: em-dash in loc text")
    if "--" in text:
        raise LocError(f"{key}: '--' in loc text")
    if "\n" in text or "\r" in text:
        raise LocError(f"{key}: real line break in loc text, use a literal \\n")
    if '"' in text.replace('\\"', ""):
        raise LocError(f"{key}: unescaped double quote")


class _Colours:
    """c.econ("Steel") -> "§YSteel§!" and so on."""
    CODES = {"econ": "Y", "pol": "L", "sec": "O", "place": "C", "good": "G", "bad": "R", "grey": "g", "white": "W", "header": "H"}

    def __getattr__(self, name):
        code = self.CODES.get(name)
        if not code:
            raise AttributeError(name)
        return lambda s: f"§{code}{s}§!"

    @staticmethod
    def signed(v, good_if_positive=True, suffix=""):
        """§G+5§! / §R-3§! depending on sign and polarity."""
        good = (v >= 0) == good_if_positive
        return f"§{'G' if good else 'R'}{'+' if v >= 0 else ''}{v}{suffix}§!"


c = _Colours()


def bullets(title, *lines):
    """Title plus £white_dot bullet lines, joined with literal \\n."""
    return title + "".join(BULLET + l for l in lines)


class Loc:
    """Ordered loc entries. Duplicates keep the first text ; a conflicting
    duplicate is recorded in `conflicts` for the validator."""

    def __init__(self):
        self.entries = {}
        self.conflicts = []

    def add(self, key, text):
        check_text(key, text)
        if key in self.entries:
            if self.entries[key] != text:
                self.conflicts.append((key, self.entries[key], text))
            return key
        self.entries[key] = text
        return key

    def __contains__(self, key):
        return key in self.entries

    def items(self):
        return self.entries.items()

    def transform(self, fn):
        """Rewrite every text with fn(key, text) (re-checked)."""
        for k in list(self.entries):
            v = fn(k, self.entries[k])
            check_text(k, v)
            self.entries[k] = v

    def yml(self, language="english"):
        s = f"l_{language}:\n"
        for k, v in self.entries.items():
            s += f" {k}:0 \"{v}\"\n"
        return s

    def merge_into(self, existing_text, language="english"):
        """Update an existing yml (LF text, no BOM): replace the lines of keys we own, append new keys
        at the end, leave everything else untouched."""
        lines = existing_text.split("\n")
        if not lines or not lines[0].startswith("l_"):
            lines = [f"l_{language}:"] + lines
        seen = set()
        for i, l in enumerate(lines):
            m = re.match(r"^(\s*)([\w.\-]+):(\d*)\s*\"", l)
            if m and m.group(2) in self.entries:
                k = m.group(2)
                lines[i] = f"{m.group(1)}{k}:{m.group(3) or '0'} \"{self.entries[k]}\""
                seen.add(k)
        while lines and lines[-1] == "":
            lines.pop()
        for k, v in self.entries.items():
            if k not in seen:
                lines.append(f" {k}:0 \"{v}\"")
        return "\n".join(lines) + "\n"


def parse_yml(text):
    """key -> text from a loc yml (LF text)."""
    out = {}
    for l in text.split("\n"):
        m = re.match(r'^\s*([\w.\-]+):\d*\s*"(.*)"\s*(#.*)?$', l)
        if m:
            out.setdefault(m.group(1), m.group(2))
    return out


class DefinedText:
    """A scripted loc `defined_text`. cases: [(trigger or "", loc_key, text or None)].

    The last case usually has no trigger (the fallback). A text of None means the key is defined
    elsewhere and is not added to the loc.
    """

    def __init__(self, name, cases):
        self.name, self.cases = name, list(cases)

    def emit(self):
        s = f"defined_text = {{\n\tname = {self.name}\n"
        for trg, key, _ in self.cases:
            s += "\ttext = {\n" + (f"\t\ttrigger = {{ {trg} }}\n" if trg else "") + f"\t\tlocalization_key = {key}\n\t}}\n"
        return s + "}\n"
