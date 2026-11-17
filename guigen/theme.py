"""Colour themes for generated sprites and the preview.

`Theme.get(name)` returns a copy you can tweak. The default "parchment" theme (dark parchment, brass
outlines) is pinned by a regression test: change its colours and that test will fail.

A country theme usually only needs `accent`, `bars` and perhaps the panel tints, e.g.

    t = Theme.get("steel").derive(accent=(160, 30, 30), bars={"main": (190, 50, 40)})
"""
from dataclasses import dataclass, field, replace


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


@dataclass
class Theme:
    name: str = "parchment"
    # frame bars
    bar_bg: tuple = (28, 26, 22, 235)
    bar_outline: tuple = (120, 110, 90, 255)
    bar_highlight: int = 50                     # added to the fill colour for the top line
    # panels (dial, gauge, card, map frame)
    panel_bg: tuple = (30, 28, 24, 235)
    gauge_bg: tuple = (26, 24, 21, 240)
    outline: tuple = (125, 112, 88, 255)
    card_top: tuple = (44, 40, 34)
    card_bottom: tuple = (26, 24, 21)
    card_alpha: int = 240
    shadow: tuple = (20, 18, 16)
    dark_line: tuple = (22, 20, 18, 255)
    vacant: tuple = (12, 11, 10, 165)
    # needle
    needle_glow: tuple = (235, 228, 205, 255)
    needle: tuple = (150, 30, 25, 255)
    hub: tuple = (60, 55, 48, 255)
    hub_rim: tuple = (200, 185, 150, 255)
    # pips (figures)
    pip_lit: tuple = (176, 158, 92, 255)
    pip_lit_edge: tuple = (60, 50, 30, 255)
    pip_off: tuple = (70, 66, 56, 200)
    pip_off_edge: tuple = (40, 38, 34, 200)
    pip_off_rifle: tuple = (55, 52, 46, 200)
    # state map
    map_sea: tuple = (34, 48, 66, 255)
    map_land: tuple = (70, 66, 58, 255)
    # named fill colours for bars and accents
    bars: dict = field(default_factory=lambda: {"gold": (205, 160, 55), "blue": (85, 140, 215), "red": (190, 55, 45), "green": (85, 170, 80)})
    good: tuple = (85, 170, 82)
    bad: tuple = (175, 50, 42)
    mid: tuple = (205, 160, 55)
    accent: tuple = (205, 160, 55)
    # preview
    preview_bg: tuple = (38, 36, 32, 255)
    preview_text: tuple = (225, 220, 205)

    def colour(self, c):
        """A colour value from a spec: an RGB tuple, a bars name, or 'accent' / 'good' / 'bad' / 'mid'."""
        if isinstance(c, str):
            if c in self.bars:
                return tuple(self.bars[c])
            if c in ("accent", "good", "bad", "mid"):
                return tuple(getattr(self, c))
            if isinstance(getattr(self, c, None), tuple):          # any theme colour: outline, panel_bg, shadow ...
                return tuple(getattr(self, c)[:3])
            if c.startswith("#") and len(c) == 7:
                return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
            raise KeyError(f"unknown colour {c!r} in theme {self.name}")
        return tuple(c)

    def derive(self, **kw):
        if "bars" in kw:
            kw["bars"] = {**self.bars, **kw["bars"]}
        return replace(self, **kw)

    @classmethod
    def get(cls, name="parchment"):
        if isinstance(name, Theme):
            return name
        if name not in THEMES:
            raise KeyError(f"unknown theme {name!r}; known: {', '.join(THEMES)}")
        return replace(THEMES[name], bars=dict(THEMES[name].bars))


THEMES = {
    # dark parchment, brass outlines (the default)
    "parchment": Theme(),
    # cool grey-blue, e.g. Germany, Sweden
    "steel": Theme(name="steel", bar_bg=(22, 25, 30, 235), bar_outline=(105, 115, 130, 255), panel_bg=(24, 27, 32, 235),
                   gauge_bg=(20, 23, 28, 240), outline=(120, 130, 145, 255), card_top=(40, 44, 52), card_bottom=(22, 25, 30),
                   shadow=(14, 16, 20), dark_line=(14, 16, 20, 255), hub_rim=(170, 180, 195, 255), needle=(40, 90, 170, 255),
                   pip_lit=(160, 170, 185, 255), accent=(95, 135, 190), preview_bg=(30, 33, 38, 255), preview_text=(215, 220, 228)),
    # deep red with gold trim, e.g. the Soviet Union, China
    "crimson": Theme(name="crimson", bar_bg=(32, 18, 18, 235), bar_outline=(150, 105, 60, 255), panel_bg=(36, 20, 20, 235),
                     gauge_bg=(30, 16, 16, 240), outline=(170, 125, 70, 255), card_top=(58, 30, 28), card_bottom=(30, 16, 16),
                     shadow=(20, 10, 10), dark_line=(20, 10, 10, 255), hub_rim=(215, 175, 90, 255), needle=(230, 190, 60, 255),
                     pip_lit=(205, 165, 80, 255), accent=(190, 45, 40), preview_bg=(42, 24, 24, 255), preview_text=(235, 215, 195)),
    # muted green with bronze, e.g. Britain's colonies, Brazil
    "jade": Theme(name="jade", bar_bg=(20, 28, 24, 235), bar_outline=(110, 125, 95, 255), panel_bg=(22, 30, 26, 235),
                  gauge_bg=(18, 26, 22, 240), outline=(130, 140, 105, 255), card_top=(36, 48, 40), card_bottom=(18, 26, 22),
                  shadow=(12, 18, 14), dark_line=(12, 18, 14, 255), hub_rim=(185, 180, 140, 255),
                  pip_lit=(165, 175, 120, 255), accent=(70, 150, 110), preview_bg=(26, 34, 30, 255), preview_text=(215, 225, 210)),
}
