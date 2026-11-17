"""Static validation of a built project against the mod and vanilla.

Errors (the game would show missing textures, raw keys or do nothing):
  * a spriteType used by an element is not defined (generated, mod or vanilla .gfx)
  * a generated texture file is missing, or an existing sprite's texture file is missing
  * a text / tooltip / buttonText loc key is not defined anywhere
  * a [Scope.GetX] scripted loc reference has no defined_text (and is not an engine getter)
  * a scripted GUI property / trigger / effect names an element that is not in the board's window
  * a frame variable maps to more frames than its sprite has
  * a scripted effect called with `X = yes` from a click is not defined
  * a written text file has the wrong line endings or unbalanced braces

Warnings (likely mistakes):
  * frame variable not set by the generated frame effect nor anywhere in the mod
  * sprite has more frames than the variable can reach
  * unbalanced or unknown § colour codes in loc
  * elements outside the window, text boxes that overlap a lot
  * duplicate element names in one window, window names already used by another .gui file
  * a decision_category board that no decision category references with `scripted_gui = NAME`
  * the same loc key generated twice with different text
"""
import glob
import os
import re

from .elements import Button, Icon, Text, Window
from .modfs import detect_eol
from .pdxscript import top_level_names
from .sprites import GfxIndex

ENGINE_GETTERS = {
    "GetName", "GetNameDef", "GetNameDefCap", "GetNameCap", "GetNameWithFlag", "GetAdjective", "GetAdjectiveCap",
    "GetNonIdeologyName", "GetNonIdeologyNameDef", "GetLeader", "GetFlag", "GetTag", "GetRulingParty",
    "GetRulingIdeology", "GetPartySupport", "GetCapitalVictoryPointName", "GetManpower", "GetFactionName",
    "GetDateText", "GetDate", "GetYear", "GetID", "GetHerHim", "GetSheHe", "GetHerHis", "GetFullName",
    "GetLastName", "GetFirstName", "GetCallsign", "GetRank", "GetOwner", "GetController",
}
COLOUR_CODES = set("CLWBGRbgYHTOt0123456789!")
TRIGGER_SUFFIXES = ["_visible", "_click_enabled"] + [f"_{m}_click_enabled" for m in
                    ("right", "shift", "alt", "control", "shift_right", "alt_right", "control_right")]
EFFECT_SUFFIXES = ["_click"] + [f"_{m}_click" for m in ("right", "shift", "alt", "control", "shift_right", "alt_right", "control_right")]
KEY_RE = re.compile(r"^[A-Za-z][\w.\-]*$")
REF_RE = re.compile(r"\[([\w.@?]+)\.(Get\w+)\]|\[(Get\w+)\]")


def _read_all(pattern_list):
    out = []
    for pat in pattern_list:
        for f in glob.glob(pat, recursive=True):
            try:
                with open(f, encoding="utf-8-sig", errors="ignore") as fh:
                    out.append((f, fh.read()))
            except OSError:
                pass
    return out


def _known_loc(p, fs):
    keys = set(p.locs.entries)
    pats = [os.path.join(fs.root, "localisation", "**", "*.yml")]
    if fs.vanilla:
        pats.append(os.path.join(fs.vanilla, "localisation", "english", "**", "*.yml"))
    for _, t in _read_all(pats):
        keys.update(re.findall(r"(?m)^\s*([\w.\-]+):\d*\s*\"", t))
    return keys


def _known_sloc(p, fs):
    names = {dt.name for dt in p.defined_texts}
    pats = [os.path.join(fs.root, "common", "scripted_localisation", "*.txt")]
    if fs.vanilla:
        pats.append(os.path.join(fs.vanilla, "common", "scripted_localisation", "*.txt"))
    for _, t in _read_all(pats):
        names.update(re.findall(r"\bname\s*=\s*(\w+)", t))
    return names


def _known_effects(p, fs):
    names = {p.frame_effect} if p.frames.rules and p.files.get("frames") else set()
    pats = [os.path.join(fs.root, "common", "scripted_effects", "*.txt")]
    if fs.vanilla:
        pats.append(os.path.join(fs.vanilla, "common", "scripted_effects", "*.txt"))
    for _, t in _read_all(pats):
        names |= top_level_names(t)
    return names


def _strip_suffix(key, suffixes):
    for s in sorted(suffixes, key=len, reverse=True):
        if key.endswith(s):
            return key[: -len(s)]
    return None


def _overlap(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    if x1 <= x0 or y1 <= y0:
        return 0
    return (x1 - x0) * (y1 - y0)


def validate(p, fs, width=520):
    errors, warnings = [], []
    gidx = GfxIndex(fs, extra_text=p.gfx_text())
    locs = _known_loc(p, fs)
    slocs = _known_sloc(p, fs)
    effects = _known_effects(p, fs)
    frame_rules = p.frames.by_var()
    mod_script = None

    def ref_check(where, text):
        for scope, getter, bare in REF_RE.findall(text or ""):
            name = getter or bare
            if name not in slocs and name not in ENGINE_GETTERS:
                (errors if name.startswith(f"Get{p.prefix}") else warnings).append(
                    f"{where}: scripted loc [{scope + '.' if scope else ''}{name}] is not defined")

    def key_check(where, key):
        if not key or "[" in key or not KEY_RE.match(key):
            ref_check(where, key)
            return
        if key not in locs:
            errors.append(f"{where}: loc key {key} is not defined")

    # ------------------------------------------------------------------ boards
    window_names = {}
    for b in p.boards:
        win = b.window
        names = {}
        for el, (ox, oy) in b.absolute():
            where = f"{b.name}/{el.name}"
            if el.name in names:
                warnings.append(f"{where}: duplicate element name in window {win.name}")
            names[el.name] = el
            if isinstance(el, (Icon, Button)):
                if el.sprite not in gidx:
                    errors.append(f"{where}: spriteType {el.sprite} is not defined")
                elif el.sprite not in p.sprites:
                    tex = gidx.texture(el.sprite)
                    if tex and not fs.find(tex) and not any(fs.find(os.path.splitext(tex)[0] + e) for e in (".dds", ".png", ".tga")):
                        warnings.append(f"{where}: texture {tex} of {el.sprite} not found")
                if isinstance(el, Icon) and el.frame is not None and gidx.frames(el.sprite) and el.frame > gidx.frames(el.sprite):
                    errors.append(f"{where}: frame {el.frame} but {el.sprite} has {gidx.frames(el.sprite)} frames")
            if isinstance(el, Text):
                key_check(where, el.text)
            if isinstance(el, Button) and el.text:
                key_check(where, el.text)
            if el.tooltip:
                key_check(where + " tooltip", el.tooltip)
            # geometry
            if not isinstance(el, Window):
                x1, y1 = ox + el.x + (el.w or 0), oy + el.y + (el.h or 0)
                if win.h and y1 > win.h + 2:
                    warnings.append(f"{where}: bottom {y1} is below the window height {win.h}")
                wmax = win.w if isinstance(win.w, int) else width
                if x1 > wmax + 2:
                    warnings.append(f"{where}: right edge {x1} is beyond the window width {wmax}")
        texts = [(e, (ox + e.x, oy + e.y, ox + e.x + e.w, oy + e.y + e.h), par) for e, (ox, oy), par in b.absolute(True) if isinstance(e, Text)]
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, bb = texts[i], texts[j]
                if a[2] is not bb[2] and a[2] is not win and bb[2] is not win:
                    continue                         # different tab / toggle sections never show together
                ov = _overlap(a[1], bb[1])
                small = min((a[1][2] - a[1][0]) * (a[1][3] - a[1][1]), (bb[1][2] - bb[1][0]) * (bb[1][3] - bb[1][1])) or 1
                if ov > 0.25 * small:
                    warnings.append(f"{b.name}: text boxes {a[0].name} and {bb[0].name} overlap")
        # wiring
        for el, kv in b.props:
            if el not in names:
                errors.append(f"{b.name}: property for unknown element {el}")
                continue
            var = kv.get("frame")
            if var is None:
                continue
            spr = getattr(names[el], "sprite", None)
            nf = gidx.frames(spr) if spr else None
            rule = frame_rules.get(var)
            if rule is not None and rule.frames and nf:
                if rule.frames > nf:
                    errors.append(f"{b.name}/{el}: {var} reaches frame {rule.frames} but {spr} has {nf} frames")
                elif rule.frames < nf:
                    warnings.append(f"{b.name}/{el}: {spr} has {nf} frames but {var} only reaches {rule.frames}")
            elif rule is None:
                if mod_script is None:
                    mod_script = "".join(t for _, t in _read_all([os.path.join(fs.root, d, "**", "*.txt") for d in ("common", "events", "history")]))
                if not re.search(rf"\b{re.escape(var)}\s*=", mod_script):
                    warnings.append(f"{b.name}/{el}: frame variable {var} is not set by guigen nor anywhere in the mod")
        for key, body in b.triggers:
            el = _strip_suffix(key, TRIGGER_SUFFIXES)
            if el is None:
                warnings.append(f"{b.name}: trigger {key} has no known suffix (_visible, _click_enabled)")
            elif el not in names:
                errors.append(f"{b.name}: trigger {key} for unknown element {el}")
        for key, body in b.effects:
            el = _strip_suffix(key, EFFECT_SUFFIXES)
            if el is None:
                warnings.append(f"{b.name}: effect {key} has no known suffix (_click ...)")
            elif el not in names:
                errors.append(f"{b.name}: effect {key} for unknown element {el}")
            for call in re.findall(r"\b([A-Za-z]\w+) = yes\b", body):
                if call not in effects and "_" in call and call[:3].isupper():
                    errors.append(f"{b.name}: {key} calls undefined scripted effect {call}")
        for d in b.dynamic_lists:
            if d["name"] not in names:
                errors.append(f"{b.name}: dynamic list {d['name']} has no gridbox of that name")
        if win.name in window_names:
            errors.append(f"window name {win.name} used by two boards")
        window_names[win.name] = b.name
        if b.context == "decision_category":
            cats = _read_all([os.path.join(fs.root, "common", "decisions", "categories", "*.txt")])
            if not any(re.search(rf"\bscripted_gui\s*=\s*\"?{re.escape(b.name)}\b", t) for _, t in cats):
                warnings.append(f"{b.name}: no decision category has scripted_gui = {b.name}")
    own_gui = os.path.normcase(os.path.abspath(fs.path(p.files["gui"])))
    for f, t in _read_all([os.path.join(fs.root, "interface", "*.gui")]):
        if os.path.normcase(os.path.abspath(f)) == own_gui:
            continue
        for wn in window_names:
            if re.search(rf'name\s*=\s*"{re.escape(wn)}"', t):
                warnings.append(f"window {wn} is also defined in {os.path.relpath(f, fs.root)}")

    # ------------------------------------------------------------------ loc + scripted loc
    for k, v in p.locs.items():
        ref_check(f"loc {k}", v)
        opens, closes = len(re.findall(r"§[^!]", v)), v.count("§!")
        if opens != closes:
            warnings.append(f"loc {k}: {opens} colour codes opened, {closes} closed")
        for code in re.findall(r"§(.)", v):
            if code not in COLOUR_CODES:
                warnings.append(f"loc {k}: unknown colour code §{code}")
    for dt in p.defined_texts:
        for _, key, txt in dt.cases:
            if txt is None and key not in locs:
                errors.append(f"defined_text {dt.name}: loc key {key} is not defined")
    for k, a, b2 in p.locs.conflicts:
        warnings.append(f"loc {k} generated twice with different text (kept the first)")

    # ------------------------------------------------------------------ written files
    for rel, kind in fs.written:
        path = fs.out_path(rel)
        if kind == "image":
            continue
        with open(path, "rb") as fh:
            data = fh.read()
        want = fs.eol_for(rel)
        got = detect_eol(data)
        if got and got != want:
            errors.append(f"{rel}: written with {got} line endings, expected {want}")
        if rel.endswith((".txt", ".gui", ".gfx")):
            t = data.decode("utf-8-sig")
            if t.count("{") != t.count("}"):
                errors.append(f"{rel}: unbalanced braces")
    for s in p.sprites:
        if not os.path.exists(fs.out_path(s.texture)) and not fs.find(s.texture):
            errors.append(f"generated texture {s.texture} missing")
    warnings += text_fit_warnings(p, fs)
    return errors, warnings


def text_fit_warnings(p, fs):
    """Measure every text box with the game's bitmap fonts (needs the HOI4 install). Scripted loc picks
    its first true case and variables are 50, so dynamic text is only an estimate."""
    if not fs.vanilla or not os.path.exists(os.path.join(fs.vanilla, "gfx", "fonts", "hoi_16mbs.fnt")):
        return []
    from PIL import Image
    from .preview import Renderer
    r = Renderer(p, fs)
    out = []
    scratch = Image.new("RGBA", (1200, 1200))
    for b in p.boards:
        for el in b.elements():
            if isinstance(el, Text) and el.w and el.h:
                if r.draw_text(scratch, (0, 0, el.w, el.h), el.text, el.font, el.fmt):
                    out.append(f"{b.name}/{el.name}: text may not fit {el.w}x{el.h} with {el.font}: {r.resolve(el.text)[:70]!r}")
    return out
