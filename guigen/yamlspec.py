"""YAML board specs: a short file per country board.

    project:
      prefix: SWE                 # tag-like prefix; $P$ in any string becomes this
      theme: steel                # or {base: steel, accent: [40, 90, 170], bars: {ore: [150, 110, 70]}}
      files: {}                   # optional overrides (see Project)
      loc_mode: own
      frame_effect: SWE_ui_refresh

    sprites:                      # name -> GFX_<P>_<name>, texture <png_dir>/<P>_<name>.png
      - {type: bar, name: bar_ore, w: 150, h: 14, colour: ore}
      - {type: pips, name: ships, n: 8}
      - {type: dial, name: neutrality}
      - {type: gauge, name: column}
      - {type: card, name: card_lkab, accent: [150, 110, 70]}
      - {type: solid, name: vacant, w: 96, h: 200}

    frames:                       # variable -> frame wiring (written to the frames scripted effect)
      - {var: $P$_f_ore, source: $P$_ore_pct}                    # linear 0..100 -> 1..11
      - {var: $P$_f_neutral, source: $P$_neutral, frames: 21}
      - {var: $P$_f_risk, source: $P$_risk, thresholds: [25, 50, 75]}
      - {var: $P$_f_zone_716, scope: 716, flags: [a, b]}

    boards:
      - name: $P$_ore_board
        context: decision_category          # any HOI4 context_type
        parent_token: null                  # e.g. top_bar, selected_state_view
        visible: null                       # scripted gui visible trigger
        dirty: null
        x: 10                               # default x for elements without one
        gap: 4                              # space added after every element / row
        elements: [...]                     # see below
    loc: {KEY: "text"}
    scripted_loc:
      - name: Get$P$Mood
        cases:
          - {trigger: "check_variable = { $P$_x < 30 }", key: $P$_MOOD_0, text: "Calm"}
          - {key: $P$_MOOD_1, text: "Tense"}

Elements are laid out top to bottom. Each one is a one-key mapping:

    text:   {name, text, w, h: 20, x, y, font, format: left, tooltip, visible}
    icon:   {name, sprite, x, y, frame: 1, frame_var, scale, tooltip, visible}
    bar:    same as icon (a frame-driven sprite: bars, pips, dials, gauges)
    button: {name, sprite, x, y, text, tooltip, scale, click, enabled, visible, right_click}
    header: {emblem, help, title, subs: [...], name: $P$_hd}
    row:    {height, items: [<elements>]}   items share one y (use dy for a nudge)
    space:  10
    repeat: {for: [a, b] or {a: x, b: y}, as: k, elements: [...]}    $k$ (and $k_value$) substituted
    tabs:   {var, tabs: [{key, label, tooltip, elements: [...]}], height, button_w: 110, refresh}
    toggle: {var, sprite, label, height, elements: [...]}
    chart:  {type: bar|hbar|stacked|pie|donut|line|area|ring|scale|scatter|heatmap, name, x, y, ...}
            the keyword arguments of the chart classes in charts.py (w, h, size, bars, slices, parts,
            series, points, var, lo, hi, mode, ...); heatmap var is a pattern with {row} and {col}
    legend: {name, x, y, items: [[label, colour], ...], w, row}
    stepper: {name, var, step, lo, hi, label, label_w, cost}
    switch: {name, var, label, tooltip}

A board with `window: {title, w, h, opener, opener_xy, opener_sprite, opener_text, opener_tooltip, flag,
moveable, close}` becomes an interactive popup window (see windows.PopupWindow); its elements start
below the title bar.

`y` on an element moves the cursor there; `h` overrides the measured height.
"""
import copy
import re

import yaml

from .frames import Flags, Linear, Thresholds
from .project import Project
from .sprites import Bar, Card, Dial, Gauge, Pips, Solid
from .tabs import TabSet, Toggle
from .theme import Theme
from . import widgets as W

SPRITES = {"bar": Bar, "pips": Pips, "dial": Dial, "gauge": Gauge, "card": Card, "solid": Solid}


def _subst(obj, mapping):
    if isinstance(obj, str):
        for k, v in mapping.items():
            obj = obj.replace(f"${k}$", str(v))
        return obj
    if isinstance(obj, list):
        return [_subst(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return {_subst(k, mapping): _subst(v, mapping) for k, v in obj.items()}
    return obj


def _theme(spec):
    if isinstance(spec, dict):
        t = Theme.get(spec.get("base", "parchment"))
        kw = {k: (tuple(v) if isinstance(v, list) else v) for k, v in spec.items() if k != "base"}
        if "bars" in kw:
            kw["bars"] = {k: tuple(v) for k, v in kw["bars"].items()}
        return t.derive(**kw)
    return Theme.get(spec or "parchment")


class _Layout:
    def __init__(self, p, board, x, gap):
        self.p, self.b, self.x, self.gap = p, board, x, gap
        self.y = 0
        self.bottom = 0

    def height_of(self, kind, a):
        if "h" in a and kind != "text":
            return a["h"]
        if kind == "text":
            return a.get("h", 20)
        sz = self.p.sprite_size(a["sprite"])
        return int(sz[1] * (a.get("scale") or 1)) if sz else 24

    def place(self, item, y=None, advance=True):
        (kind, a), = item.items()
        if kind == "space":
            self.y += int(a)
            return 0
        if kind == "repeat":
            self.repeat(a)
            return 0
        if kind == "row":
            if "y" in a:
                self.y = a["y"]
            hs = [self.place(it, self.y, advance=False) for it in a["items"]]
            h = a.get("height", max(hs or [0]))
            self.y += h + self.gap
            return h
        if kind == "tabs":
            self.tabs(a)
            return 0
        if kind == "toggle":
            self.toggle(a)
            return 0
        if kind == "header":
            y = W.header(self.b, a.get("name", f"{self.p.prefix}_hd"), a["emblem"], a.get("help"), a["title"], a.get("subs", []))
            self.y = max(self.y, y + 4)
            return 0
        if kind in ("chart", "legend", "stepper", "switch"):
            a = dict(a)
            if "y" in a and y is None:
                self.y = a["y"]
            yy = (a.pop("y", self.y) if y is None else y) + a.pop("dy", 0)
            xx = a.pop("x", self.x)
            h = build_control(self.p, self.b, kind, xx, yy, a)
            self.bottom = max(self.bottom, yy + h)
            if advance:
                self.y = yy + h + self.gap
            return h
        a = dict(a)
        if "y" in a and y is None:
            self.y = a["y"]
        yy = (a.get("y", self.y) if y is None else y) + a.get("dy", 0)
        x = a.get("x", self.x)
        h = self.height_of(kind, a)
        b = self.b
        if kind == "text":
            b.text(a["name"], x, yy, a["text"], a["w"], a.get("h", 20), a.get("font", "hoi_16mbs"), a.get("format", "left"),
                   a.get("tooltip"), a.get("visible"))
        elif kind in ("icon", "bar"):
            b.icon(a["name"], x, yy, a["sprite"], a.get("frame", 1), a.get("frame_var"), a.get("scale"), a.get("tooltip"), a.get("visible"))
        elif kind == "button":
            b.button(a["name"], x, yy, a["sprite"], a.get("tooltip"), a.get("text"), a.get("scale"), a.get("font", "hoi_16mbs"),
                     a.get("click"), a.get("enabled"), a.get("visible"))
            if a.get("right_click"):
                b.click(a["name"], a["right_click"], modifier="right")
        else:
            raise ValueError(f"unknown element type {kind!r}")
        self.bottom = max(self.bottom, yy + h)
        if advance:
            self.y = yy + h + self.gap
        return h

    def run(self, items):
        for it in items:
            self.place(it)
        self.bottom = max(self.bottom, self.y)

    def repeat(self, a):
        name = a.get("as", "item")
        seq = a["for"]
        pairs = list(seq.items()) if isinstance(seq, dict) else [(v, v) for v in seq]
        for i, (k, v) in enumerate(pairs):
            self.run(_subst(copy.deepcopy(a["elements"]), {name: k, f"{name}_value": v, f"{name}_index": i}))

    def tabs(self, a):
        y = self.y
        bw = a.get("button_w", 110)
        ts = TabSet(self.p, self.b, a["var"], [(t["key"], t["label"]) for t in a["tabs"]], self.x, y, y + 30, a["height"],
                    button_w=bw, refresh=a.get("refresh"), tooltips={t["key"]: t.get("tooltip") for t in a["tabs"]})
        for t in a["tabs"]:
            with ts.section(t["key"]):
                sub = _Layout(self.p, self.b, self.x, self.gap)
                sub.run(t.get("elements", []))
        self.y = y + 30 + a["height"] + self.gap
        self.bottom = max(self.bottom, self.y)

    def toggle(self, a):
        y = self.y
        tg = Toggle(self.p, self.b, a["var"], self.x, y, a["sprite"], a["label"], y + 30, a["height"], a.get("tooltip"),
                    a.get("start_open", True))
        with tg.section():
            sub = _Layout(self.p, self.b, self.x, self.gap)
            sub.run(a.get("elements", []))
        self.y = y + 30 + a["height"] + self.gap
        self.bottom = max(self.bottom, self.y)


def _tuples(v):
    if isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v):
        return tuple(v)
    if isinstance(v, list):
        return [_tuples(x) for x in v]
    if isinstance(v, dict):
        return {k: _tuples(x) for k, x in v.items()}
    return v


def build_control(p, b, kind, x, y, a):
    """chart / legend / stepper / switch elements. Returns the height used."""
    from . import charts as C
    from .windows import stepper, switch
    a = _tuples(a)
    if kind == "legend":
        return C.legend(b, p, a["name"], x, y, [tuple(i) for i in a["items"]], a.get("row", 20), a.get("w", 160))
    if kind == "stepper":
        stepper(b, p, a.pop("name"), x, y, a.pop("var"), **a)
        return 24
    if kind == "switch":
        switch(b, p, a.pop("name"), x, y, a.pop("var"), **a)
        return 20
    t = a.pop("type")
    name = a.pop("name")
    if t in ("bar", "column", "hbar"):
        w, h = a.pop("w"), a.pop("h")
        horizontal = (t == "hbar") or a.pop("horizontal", False)
        C.BarChart(p, b, name, x, y, w, h, a.pop("bars"), horizontal=horizontal, **a)
        return h if horizontal else h + (36 if a.get("show_values", True) else 20)
    if t in ("pie", "donut"):
        size = a.pop("size")
        if t == "donut":
            a.setdefault("inner", 0.55)
        C.PieChart(p, b, name, x, y, size, a.pop("slices"), **a)
        return size
    if t == "stacked":
        h = a.pop("h")
        C.StackedBar(p, b, name, x, y, a.pop("w"), h, a.pop("parts"), **a)
        return h + (22 if a.get("legend", True) else 0)
    if t in ("line", "area"):
        h = a.pop("h")
        if t == "area":
            a.setdefault("area", True)
        C.LineChart(p, b, name, x, y, a.pop("w"), h, a.pop("series"), **a)
        return h
    if t == "ring":
        size = a.pop("size")
        C.RingGauge(p, b, name, x, y, size, a.pop("var"), **a)
        return size + (20 if a.get("label") else 0)
    if t == "scale":
        C.ScaleMarker(p, b, name, x, y, a.pop("w"), a.pop("var"), **a)
        return a.get("marker", 14) + a.get("h", 10) + (18 if a.get("left") or a.get("right") else 0)
    if t == "scatter":
        h = a.pop("h")
        quads = [tuple(q) for q in a.pop("quadrants", [])] or None
        C.Scatter(p, b, name, x, y, a.pop("w"), h, a.pop("points"), quadrants=quads, **a)
        return h
    if t == "heatmap":
        pattern = a.pop("var")
        rows, cols = a.pop("rows"), a.pop("cols")
        cell = tuple(a.pop("cell", (34, 22)))
        C.Heatmap(p, b, name, x, y, rows, cols, lambda r, c: pattern.replace("{row}", str(r)).replace("{col}", str(c)), cell=cell, **a)
        return 20 + len(rows) * cell[1]
    raise ValueError(f"unknown chart type {t!r} (bar, hbar, stacked, pie, donut, line, area, ring, scale, scatter, heatmap)")


def load_yaml(fs, path):
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    pj = raw.get("project", {})
    P = pj["prefix"]
    d = _subst(raw, {"P": P})
    pj = d["project"]
    p = Project(fs, P, theme=_theme(pj.get("theme")), files=pj.get("files"), loc_mode=pj.get("loc_mode", "own"),
                frame_effect=pj.get("frame_effect", "{P}_guigen_refresh_frames"))
    for s in d.get("sprites", []):
        s = dict(s)
        cls = SPRITES[s.pop("type")]
        stem = s.pop("name")
        if "colour" in s and isinstance(s["colour"], list):
            s["colour"] = tuple(s["colour"])
        if "accent" in s and isinstance(s["accent"], list):
            s["accent"] = tuple(s["accent"])
        p.sprite(cls(p.gfx_name(stem), p.png(stem), **s))
    for fr in d.get("frames", []):
        if "thresholds" in fr:
            p.frame(Thresholds(fr["var"], fr["source"], fr["thresholds"]))
        elif "flags" in fr:
            p.frame(Flags(fr["var"], fr.get("scope"), fr["flags"], fr.get("kind", "state")))
        else:
            p.frame(Linear(fr["var"], fr["source"], fr.get("frames", 11), fr.get("lo", 0), fr.get("hi", 100)))
    for k, v in (d.get("loc") or {}).items():
        p.loc(k, v)
    for dt in d.get("scripted_loc", []):
        p.defined_text(dt["name"], [(c.get("trigger", ""), c["key"], c.get("text")) for c in dt["cases"]])
    for bd in d.get("boards", []):
        popup = bd.get("window")
        if isinstance(popup, dict):
            from .windows import PopupWindow
            wd = _tuples(dict(popup))
            win = PopupWindow(p, bd["name"], wd.pop("title"), wd.pop("w"), wd.pop("h"), **wd)
            b = win.board
            lay = _Layout(p, b, bd.get("x", 16), bd.get("gap", 4))
            lay.y = win.top + 4
            lay.run(bd.get("elements", []))
            continue
        b = p.board(bd["name"], context=bd.get("context", "decision_category"), window_name=popup,
                    width=bd.get("width", "100%%"), parent_token=bd.get("parent_token"), parent_gui=bd.get("parent_gui"),
                    visible=bd.get("visible"), dirty=bd.get("dirty"), map_mode=bd.get("map_mode"),
                    x=bd.get("window_x", 0), y=bd.get("window_y", 0))
        lay = _Layout(p, b, bd.get("x", 10), bd.get("gap", 4))
        lay.run(bd.get("elements", []))
        b.window.h = bd["height"] if isinstance(bd.get("height"), int) else lay.bottom + bd.get("pad", 6)
    return p
