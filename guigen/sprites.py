"""Sprite-sheet generation with Pillow, and the .gfx spriteTypes block.

Every generated sprite is a horizontal strip of `frames` cells. HOI4 picks a cell with `frame = N`
(1-based) on the iconType or through a scripted GUI property, so a variable mapped to 1..frames
(see frames.py) animates the sprite.

Drawing is deterministic (same parameters and theme -> same pixels), so rebuilds are pixel-identical
and `guigen diff` stays quiet unless something really changed.
"""
import math
import os
import re

from PIL import Image, ImageDraw

from .theme import Theme, lerp


class Sprite:
    """A generated sprite. `texture` is the mod-relative PNG path."""
    generated = True

    def __init__(self, name, texture, frames=1):
        self.name, self.texture, self.frames = name, texture, frames
        self.theme = None
        self._img = self._img_key = None

    def render(self, theme):
        raise NotImplementedError

    def _fingerprint(self, theme):
        params = tuple(sorted((k, repr(v)) for k, v in vars(self).items() if not k.startswith("_") and k != "theme"))
        return params, repr(theme)

    def image(self, theme=None):
        """Rendered strip; re-rendered whenever a parameter or the theme changes."""
        t = Theme.get(theme or self.theme or "parchment")
        key = self._fingerprint(t)
        if self._img is None or self._img_key != key:
            self._img, self._img_key = self.render(t), key
        return self._img

    @property
    def frame_size(self):
        im = self.image()
        return im.width // self.frames, im.height

    def gfx(self):
        s = f"\tspriteType = {{\n\t\tname = \"{self.name}\"\n\t\ttexturefile = \"{self.texture}\"\n"
        if self.frames > 1:
            s += f"\t\tnoOfFrames = {self.frames}\n"
        return s + "\t}\n"


class Bar(Sprite):
    """Horizontal progress bar; frame f fills f-1 tenths (11 frames = 0%..100%)."""

    def __init__(self, name, texture, w, h, colour, frames=11):
        super().__init__(name, texture, frames)
        self.w, self.h, self.colour = w, h, colour

    def render(self, t):
        w, h, n = self.w, self.h, self.frames
        col = t.colour(self.colour)
        img = Image.new("RGBA", (w * n, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f in range(n):
            x0 = f * w
            d.rectangle([x0, 0, x0 + w - 1, h - 1], fill=t.bar_bg, outline=t.bar_outline)
            fw = int((w - 4) * f / (n - 1))
            if fw > 0:
                d.rectangle([x0 + 2, 2, x0 + 1 + fw, h - 3], fill=col + (255,))
                d.line([x0 + 2, 2, x0 + 1 + fw, 2], fill=tuple(min(255, c + t.bar_highlight) for c in col) + (255,))
        return img


class Pips(Sprite):
    """A row of `n` figures; frame f lights f-1 of them. figure: 'soldier' (default) or 'dot'."""

    def __init__(self, name, texture, n=10, pw=15, h=16, frames=11, figure="soldier"):
        super().__init__(name, texture, frames)
        self.n, self.pw, self.h, self.figure = n, pw, h, figure

    def render(self, t):
        n, pw, h = self.n, self.pw, self.h
        w = n * pw
        img = Image.new("RGBA", (w * self.frames, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f in range(self.frames):
            for i in range(n):
                x0 = f * w + i * pw + 2
                lit = i < f
                body = t.pip_lit if lit else t.pip_off
                edge = t.pip_lit_edge if lit else t.pip_off_edge
                if self.figure == "dot":
                    r = min(pw, h) // 2 - 2
                    cx, cy = x0 + pw // 2 - 2, h // 2
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=body, outline=edge)
                    continue
                d.ellipse([x0 + 3, 1, x0 + 7, 5], fill=body, outline=edge)                              # head
                d.polygon([(x0 + 2, 6), (x0 + 8, 6), (x0 + 9, 11), (x0 + 1, 11)], fill=body, outline=edge)  # torso
                d.rectangle([x0 + 2, 11, x0 + 4, h - 1], fill=body)                                      # legs
                d.rectangle([x0 + 6, 11, x0 + 8, h - 1], fill=body)
                d.line([x0 + 9, 2, x0 + 11, 12], fill=edge if lit else t.pip_off_rifle, width=1)         # rifle
        return img


DIAL_BANDS = [(0, 15, (175, 45, 40)), (15, 35, (205, 115, 40)), (35, 65, (170, 160, 120)), (65, 85, (80, 160, 75)), (85, 100, (215, 175, 60))]


class Dial(Sprite):
    """Semicircular dial over 0..100 with coloured bands and a needle; frame f points at f * 100/(frames-1)."""

    def __init__(self, name, texture, w=180, h=100, frames=21, bands=None, r=78, band_width=14, ticks=None):
        super().__init__(name, texture, frames)
        self.w, self.h, self.r, self.band_width = w, h, r, band_width
        self.bands = bands or DIAL_BANDS
        self.ticks = ticks if ticks is not None else [b[0] for b in self.bands[1:]]

    def render(self, t):
        W, H, n = self.w, self.h, self.frames
        step = 100 / (n - 1)
        img = Image.new("RGBA", (W * n, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f in range(n):
            ox = f * W
            cx, cy, r = ox + W // 2, H - 10, self.r
            d.rounded_rectangle([ox + 1, 1, ox + W - 2, H - 2], 10, fill=t.panel_bg, outline=t.outline, width=2)
            for lo, hi, col in self.bands:   # angle 180 (left, 0) to 360 (right, 100), PIL measures clockwise from east
                d.arc([cx - r, cy - r, cx + r, cy + r], 180 + lo * 1.8, 180 + hi * 1.8, fill=t.colour(col) + (255,), width=self.band_width)
            for v in self.ticks:
                a = math.radians(180 + v * 1.8)
                d.line([cx + (r - 16) * math.cos(a), cy + (r - 16) * math.sin(a), cx + (r + 1) * math.cos(a), cy + (r + 1) * math.sin(a)],
                       fill=t.shadow + (255,), width=2)
            a = math.radians(180 + f * step * 1.8)
            tip = (cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a))
            d.line([cx, cy, tip[0], tip[1]], fill=t.needle_glow, width=4)
            d.line([cx, cy, tip[0], tip[1]], fill=t.needle, width=2)
            d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=t.hub, outline=t.hub_rim, width=2)
        return img


class Gauge(Sprite):
    """Vertical column 0..100 with threshold ticks.

    Fill colour: `low` at or below `low_t`, a blend from `mid_from` to `mid_to` up to `high_t`, then `high`.
    """

    def __init__(self, name, texture, w=22, h=84, frames=11, low_t=0.3, high_t=0.6, low=(175, 50, 42),
                 mid_from=(205, 160, 55), mid_to=(85, 165, 80), high=(85, 170, 82), ticks=None):
        super().__init__(name, texture, frames)
        self.w, self.h = w, h
        self.low_t, self.high_t, self.low, self.mid_from, self.mid_to, self.high = low_t, high_t, low, mid_from, mid_to, high
        self.ticks = ticks if ticks is not None else [(low_t, (215, 70, 60)), (high_t, (110, 205, 100))]

    def fill(self, t, v):
        if v <= self.low_t:
            return t.colour(self.low)
        if v < self.high_t:
            return lerp(t.colour(self.mid_from), t.colour(self.mid_to), min(1, (v - self.low_t) / (self.high_t - self.low_t)))
        return t.colour(self.high)

    def render(self, t):
        W, H, n = self.w, self.h, self.frames
        img = Image.new("RGBA", (W * n, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f in range(n):
            ox = f * W
            d.rectangle([ox, 0, ox + W - 1, H - 1], fill=t.gauge_bg, outline=t.outline)
            v = f / (n - 1)
            col = self.fill(t, v)
            fh = int((H - 4) * v)
            if fh > 0:
                d.rectangle([ox + 3, H - 2 - fh, ox + W - 4, H - 3], fill=col + (255,))
                d.line([ox + 3, H - 2 - fh, ox + W - 4, H - 2 - fh], fill=lerp(col, (255, 255, 255), 0.35) + (255,))
            for tv, tc in self.ticks:
                y = H - 2 - int((H - 4) * tv)
                d.line([ox, y, ox + 5, y], fill=t.colour(tc) + (255,), width=2)
                d.line([ox + W - 6, y, ox + W - 1, y], fill=t.colour(tc) + (255,), width=2)
        return img


class Card(Sprite):
    """Card background: vertical gradient, outline, accent strip on top and an emblem ring."""

    def __init__(self, name, texture, w=96, h=270, accent="accent", ring=None):
        super().__init__(name, texture, 1)
        self.w, self.h, self.accent = w, h, accent
        self.ring = ring or (w // 2 - 29, 9, w // 2 + 29, 63)

    @property
    def ring_centre(self):
        x0, y0, x1, y1 = self.ring
        return (x0 + x1) // 2, (y0 + y1) // 2

    def render(self, t):
        W, H = self.w, self.h
        acc = t.colour(self.accent)
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for yy in range(H):
            c = lerp(t.card_top, t.card_bottom, yy / H)
            d.line([2, yy, W - 3, yy], fill=c + (t.card_alpha,))
        d.rectangle([0, 0, W - 1, H - 1], outline=t.outline, width=2)
        d.rectangle([2, 2, W - 3, 7], fill=acc + (255,))
        d.ellipse(list(self.ring), fill=lerp(acc, t.shadow, 0.65) + (255,), outline=acc + (255,), width=2)
        return img


class Solid(Sprite):
    """Flat rectangle, e.g. a translucent 'vacant' overlay. colour: RGBA, or None for theme.vacant."""

    def __init__(self, name, texture, w, h, colour=None):
        super().__init__(name, texture, 1)
        self.w, self.h, self.colour = w, h, colour

    def render(self, t):
        return Image.new("RGBA", (self.w, self.h), tuple(self.colour) if self.colour else t.vacant)


class Swatches(Sprite):
    """Legend key: one square per frame."""

    def __init__(self, name, texture, colours, size=14):
        super().__init__(name, texture, len(colours))
        self.colours, self.size = colours, size

    def render(self, t):
        s = self.size
        img = Image.new("RGBA", (s * len(self.colours), s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f, c in enumerate(self.colours):
            d.rectangle([f * s, 0, f * s + s - 1, s - 1], fill=t.colour(c) + (255,), outline=t.dark_line)
        return img


class Tabs(Sprite):
    """Tab button background, idle or selected (accent strip, brighter top). Used by tabs.TabSet."""

    def __init__(self, name, texture, w=110, h=24, selected=False):
        super().__init__(name, texture, 1)
        self.w, self.h, self.selected = w, h, selected

    def render(self, t):
        W, H = self.w, self.h
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        top = lerp(t.card_top, t.colour("accent"), 0.55) if self.selected else t.card_top
        for yy in range(H):
            d.line([1, yy, W - 2, yy], fill=lerp(top, t.card_bottom, yy / H) + (240,))
        d.rounded_rectangle([0, 0, W - 1, H + 4], 5, outline=t.outline, width=2 if self.selected else 1)
        if self.selected:
            d.rectangle([3, 2, W - 4, 4], fill=t.colour("accent") + (255,))
        return img


class Static(Sprite):
    """A sprite drawn by your own function: draw(theme) -> PIL.Image (a strip of `frames` cells)."""

    def __init__(self, name, texture, draw, frames=1):
        super().__init__(name, texture, frames)
        self.draw = draw

    def render(self, t):
        return self.draw(t)


class SpriteSet:
    """Ordered generated sprites. gfx() prints them in insertion order."""

    def __init__(self):
        self.items = []
        self.by_name = {}

    def add(self, sprite):
        if sprite.name in self.by_name:
            raise ValueError(f"duplicate sprite {sprite.name}")
        self.items.append(sprite)
        self.by_name[sprite.name] = sprite
        return sprite

    def __iter__(self):
        return iter(self.items)

    def __contains__(self, name):
        return name in self.by_name

    def get(self, name):
        return self.by_name.get(name)

    def gfx(self):
        return "spriteTypes = {\n" + "".join(s.gfx() for s in self.items) + "}\n"


# ------------------------------------------------------------------ existing sprites (mod + vanilla .gfx)
_SPRITE_RE = re.compile(r'(?:spriteType|frameAnimatedSpriteType|corneredTileSpriteType|textSpriteType|progressbartype|maskedShieldType)\s*=\s*\{(.*?)\n\s*\}', re.S | re.I)


class GfxIndex:
    """name -> (texturefile, noOfFrames, source file) over the mod's and vanilla's interface/*.gfx."""

    def __init__(self, fs, extra_text=""):
        import glob
        self.fs = fs
        self.sprites = {}
        self.order = []
        roots = [fs.root] + ([fs.vanilla] if fs.vanilla else [])
        if extra_text:
            self._parse(extra_text, "<generated>")
        for r in roots:
            for f in sorted(glob.glob(os.path.join(r, "interface", "**", "*.gfx"), recursive=True)):
                with open(f, encoding="utf-8-sig", errors="ignore") as fh:
                    self._parse(fh.read(), f)

    def _parse(self, text, src):
        for m in _SPRITE_RE.finditer(text):
            body = m.group(1)
            n = re.search(r'\bname\s*=\s*"?([^"\s}]+)"?', body)
            if not n or n.group(1) in self.sprites:
                continue
            tf = re.search(r'texture[fF]ile1?\s*=\s*"([^"]+)"', body)
            fr = re.search(r'noOfFrames\s*=\s*(\d+)', body)
            self.sprites[n.group(1)] = (tf.group(1) if tf else None, int(fr.group(1)) if fr else 1, src)
            self.order.append(n.group(1))

    def __contains__(self, name):
        return name in self.sprites

    def texture(self, name):
        v = self.sprites.get(name)
        return v[0] if v else None

    def frames(self, name):
        v = self.sprites.get(name)
        return v[1] if v else None

    def open(self, name):
        """PIL image of a sprite's whole texture, or None."""
        tex = self.texture(name)
        if not tex:
            return None
        p = self.fs.find(tex)
        if not p:
            alt = os.path.splitext(tex)[0]
            for ext in (".dds", ".png", ".tga"):
                p = self.fs.find(alt + ext)
                if p:
                    break
        if not p:
            return None
        try:
            return Image.open(p).convert("RGBA")
        except Exception:
            return None


def fit_into(img, centre, fit, alpha_cut=60):
    """(scale, dx, dy) that centres the visible part of `img` on `centre` at `fit` pixels across.

    Used to drop focus icons into a card's emblem ring regardless of their padding.
    """
    a = img.split()[3].point(lambda v: 255 if v > alpha_cut else 0)
    x0, y0, x1, y1 = a.getbbox()
    s = round(fit / max(x1 - x0, y1 - y0), 3)
    cx, cy = (x0 + x1) / 2 * s, (y0 + y1) / 2 * s
    return s, int(round(centre[0] - cx)), int(round(centre[1] - cy))
