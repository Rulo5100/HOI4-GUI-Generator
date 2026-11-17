"""Sprites for charts and windows.

Sprite mode (default, works in any mod, no shaders):

    FillBar        bar that fills left->right or bottom->top, frames = steps + 1 (no background: chart columns)
    Wedge          pie / donut layer: frame f fills (f-1)/steps of a full turn clockwise from 12 o'clock
    LineSegments   one cell of a line chart; frames = levels^2, frame = start*levels + end + 1
    ChartBackground panel with axes and gridlines
    Marker         a dot / diamond / triangle / bar tick to position with x / y properties
    Gradient       one frame per colour step of a colour ramp (heatmaps, tiers)
    Panel          9-slice window background (corneredTileSpriteType)
    CloseButton    small X button, 3 frames (idle / hover / pressed) like vanilla buttons

Shader mode (optional): ProgressBarSprite writes a `progressbartype`. With the vanilla effect files it
gives smooth bars (progress.lua) and pie slices (progress_radial.lua); with guigen's own line shader
(see shaders.py) it draws anti-aliased line segments.

Pies and stacked bars are built by layering: slice k is drawn filled to the cumulative share of slices
1..k, the largest cumulative layer first, so each slice shows exactly its own share.
"""
import math

from PIL import Image, ImageDraw

from .sprites import Sprite
from .theme import lerp

SS = 4      # supersampling factor for anti-aliased shapes


def _aa(size, draw):
    """Draw at SS x size with draw(d, scale) and downscale (anti-aliasing)."""
    w, h = size
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    draw(ImageDraw.Draw(big), SS)
    return big.resize((w, h), Image.LANCZOS)


class FillBar(Sprite):
    """A bar that fills to (f-1)/steps of its length. direction: 'right' or 'up'.
    bg: draw the theme's bar background and outline (False for chart columns over a chart background)."""

    def __init__(self, name, texture, w, h, colour, steps=20, direction="up", bg=False, highlight=True):
        super().__init__(name, texture, steps + 1)
        self.w, self.h, self.colour, self.steps, self.direction, self.bg, self.highlight = w, h, colour, steps, direction, bg, highlight

    def render(self, t):
        w, h, n = self.w, self.h, self.frames
        col = t.colour(self.colour)
        hi = tuple(min(255, c + t.bar_highlight) for c in col) + (255,)
        img = Image.new("RGBA", (w * n, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pad = 2 if self.bg else 0
        for f in range(n):
            x0 = f * w
            if self.bg:
                d.rectangle([x0, 0, x0 + w - 1, h - 1], fill=t.bar_bg, outline=t.bar_outline)
            frac = f / self.steps
            if self.direction == "right":
                fw = int((w - 2 * pad) * frac)
                if fw > 0:
                    d.rectangle([x0 + pad, pad, x0 + pad + fw - 1, h - 1 - pad], fill=col + (255,))
                    if self.highlight:
                        d.line([x0 + pad, pad, x0 + pad + fw - 1, pad], fill=hi)
            else:
                fh = int((h - 2 * pad) * frac)
                if fh > 0:
                    d.rectangle([x0 + pad, h - pad - fh, x0 + w - 1 - pad, h - 1 - pad], fill=col + (255,))
                    if self.highlight:
                        d.line([x0 + pad, h - pad - fh, x0 + w - 1 - pad, h - pad - fh], fill=hi)
        return img


class Wedge(Sprite):
    """Pie / donut layer. inner: hole radius as a fraction of the radius (0 = pie). Anti-aliased."""

    def __init__(self, name, texture, size, colour, steps=50, inner=0.0, edge=True):
        super().__init__(name, texture, steps + 1)
        self.size, self.colour, self.steps, self.inner, self.edge = size, colour, steps, inner, edge

    def render(self, t):
        s, n = self.size, self.frames
        col = t.colour(self.colour) + (255,)
        img = Image.new("RGBA", (s * n, s), (0, 0, 0, 0))
        for f in range(n):
            frac = f / self.steps
            if frac <= 0:
                continue

            def draw(d, k, frac=frac):
                r = s * k / 2 - k
                c = s * k / 2
                box = [c - r, c - r, c + r, c + r]
                if frac >= 1:
                    d.ellipse(box, fill=col)
                else:
                    d.pieslice(box, -90, -90 + 360 * frac, fill=col)
                    if self.edge:                       # thin dark separators at the slice edges
                        for a in (-90, -90 + 360 * frac):
                            ra = math.radians(a)
                            d.line([c, c, c + r * math.cos(ra), c + r * math.sin(ra)], fill=t.dark_line, width=k)
                if self.inner:
                    ri = r * self.inner
                    d.ellipse([c - ri, c - ri, c + ri, c + ri], fill=(0, 0, 0, 0))
            img.paste(_aa((s, s), draw), (f * s, 0))
        return img


class LineSegments(Sprite):
    """One horizontal cell of a line chart. levels: vertical resolution (0 = bottom).
    frame = start_level * levels + end_level + 1. area: also fill below the line with this alpha (0..255)."""

    def __init__(self, name, texture, w, h, colour, levels=16, width=2.0, area=0, dot=False):
        super().__init__(name, texture, levels * levels)
        self.w, self.h, self.colour, self.levels, self.width, self.area, self.dot = w, h, colour, levels, width, area, dot

    def y(self, level, k=1):
        pad = self.width + 1
        return (self.h - pad - level * (self.h - 2 * pad) / (self.levels - 1)) * k

    def render(self, t):
        w, h, L = self.w, self.h, self.levels
        col = t.colour(self.colour)
        img = Image.new("RGBA", (w * L * L, h), (0, 0, 0, 0))
        for s in range(L):
            for e in range(L):
                def draw(d, k, s=s, e=e):
                    y0, y1 = self.y(s, k), self.y(e, k)
                    if self.area:
                        d.polygon([(0, y0), (w * k, y1), (w * k, h * k), (0, h * k)], fill=col + (self.area,))
                    d.line([(-k, y0 - (y1 - y0) / w), (w * k + k, y1 + (y1 - y0) / w)], fill=col + (255,), width=int(self.width * k))
                    if self.dot:
                        r = self.width * 1.6 * k
                        d.ellipse([-r, y0 - r, r, y0 + r], fill=col + (255,))
                img.paste(_aa((w, h), draw), ((s * L + e) * w, 0))
        return img

    @staticmethod
    def frame_of(start, end, levels):
        return start * levels + end + 1


class ChartBackground(Sprite):
    """Plot area: panel, gridlines every 1/y_div of the height (and x_div of the width), axis lines."""

    def __init__(self, name, texture, w, h, y_div=4, x_div=0, axes=True, zero_line=None):
        super().__init__(name, texture, 1)
        self.w, self.h, self.y_div, self.x_div, self.axes, self.zero_line = w, h, y_div, x_div, axes, zero_line

    def render(self, t):
        w, h = self.w, self.h
        img = Image.new("RGBA", (w, h), t.panel_bg)
        d = ImageDraw.Draw(img)
        grid = t.outline[:3] + (70,)
        for i in range(1, self.y_div):
            y = round(h * i / self.y_div)
            for x in range(0, w, 6):
                d.line([x, y, min(w - 1, x + 2), y], fill=grid)
        for i in range(1, self.x_div):
            x = round(w * i / self.x_div)
            for y in range(0, h, 6):
                d.line([x, y, x, min(h - 1, y + 2)], fill=grid)
        if self.zero_line is not None:
            y = round(h * (1 - self.zero_line))
            d.line([0, y, w - 1, y], fill=t.outline)
        d.rectangle([0, 0, w - 1, h - 1], outline=t.outline)
        if self.axes:
            d.line([0, h - 1, w - 1, h - 1], fill=t.hub_rim)
            d.line([0, 0, 0, h - 1], fill=t.hub_rim)
        return img


class Marker(Sprite):
    """A position marker: shape 'dot', 'diamond', 'triangle' (pointing down) or 'tick' (vertical bar)."""

    def __init__(self, name, texture, size=10, colour="accent", shape="dot", outline=True):
        super().__init__(name, texture, 1)
        self.size, self.colour, self.shape, self.outline = size, colour, shape, outline

    def render(self, t):
        s = self.size
        col = t.colour(self.colour) + (255,)
        edge = t.dark_line if self.outline else None

        def draw(d, k):
            S = s * k
            if self.shape == "diamond":
                d.polygon([(S / 2, k), (S - k, S / 2), (S / 2, S - k), (k, S / 2)], fill=col, outline=edge)
            elif self.shape == "triangle":
                d.polygon([(k, k), (S - k, k), (S / 2, S - k)], fill=col, outline=edge)
            elif self.shape == "tick":
                d.rectangle([S / 2 - k * 1.5, 0, S / 2 + k * 1.5, S], fill=col, outline=edge)
            else:
                d.ellipse([k, k, S - k, S - k], fill=col, outline=edge, width=k)
        return _aa((s, s), draw)


class Gradient(Sprite):
    """Heatmap / tier cells: `steps` frames along a colour ramp (list of stops)."""

    def __init__(self, name, texture, w, h, stops=("bad", "mid", "good"), steps=10, border=True):
        super().__init__(name, texture, steps)
        self.w, self.h, self.stops, self.steps, self.border = w, h, list(stops), steps, border

    def colour_at(self, t, x):
        stops = [t.colour(c) for c in self.stops]
        if len(stops) == 1:
            return stops[0]
        pos = x * (len(stops) - 1)
        i = min(int(pos), len(stops) - 2)
        return lerp(stops[i], stops[i + 1], pos - i)

    def render(self, t):
        w, h, n = self.w, self.h, self.steps
        img = Image.new("RGBA", (w * n, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f in range(n):
            c = self.colour_at(t, f / max(1, n - 1))
            d.rectangle([f * w, 0, f * w + w - 1, h - 1], fill=c + (255,), outline=t.dark_line if self.border else None)
        return img


class Panel(Sprite):
    """9-slice window background for containerWindowType backgrounds (corneredTileSpriteType).
    title_h: height of a darker title band at the top (0 for none)."""

    def __init__(self, name, texture, size=96, border=24, title_h=30):
        super().__init__(name, texture, 1)
        self.size, self.border, self.title_h = size, border, title_h

    def render(self, t):
        s = self.size
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for yy in range(s):
            d.line([2, yy, s - 3, yy], fill=lerp(t.card_top, t.card_bottom, yy / s) + (246,))
        if self.title_h:
            d.rectangle([2, 2, s - 3, min(self.border, self.title_h)], fill=lerp(t.card_top, t.colour("accent"), 0.25) + (250,))
        d.rounded_rectangle([0, 0, s - 1, s - 1], 6, outline=t.outline, width=2)
        d.rounded_rectangle([3, 3, s - 4, s - 4], 4, outline=t.shadow + (255,), width=1)
        return img

    def gfx(self):
        b = self.border
        return (f"\tcorneredTileSpriteType = {{\n\t\tname = \"{self.name}\"\n\t\ttexturefile = \"{self.texture}\"\n"
                f"\t\tsize = {{ x = {self.size} y = {self.size} }}\n\t\tborderSize = {{ x = {b} y = {b} }}\n\t\ttilingCenter = yes\n\t}}\n")


class CloseButton(Sprite):
    """Small X button with idle / hover / pressed frames."""

    def __init__(self, name, texture, size=22):
        super().__init__(name, texture, 3)
        self.size = size

    def render(self, t):
        s = self.size
        img = Image.new("RGBA", (s * 3, s), (0, 0, 0, 0))
        for f in range(3):
            def draw(d, k, f=f):
                S = s * k
                fill = lerp(t.card_top, t.colour("bad"), (0.25, 0.6, 0.8)[f])
                d.rounded_rectangle([k, k, S - k, S - k], 3 * k, fill=fill + (255,), outline=t.outline, width=k)
                m = S * 0.3
                d.line([m, m, S - m, S - m], fill=t.preview_text + (255,), width=int(2 * k))
                d.line([S - m, m, m, S - m], fill=t.preview_text + (255,), width=int(2 * k))
            img.paste(_aa((s, s), draw), (f * s, 0))
        return img


class TextButton(Sprite):
    """Plain button background (idle / hover / pressed / disabled) for buttonText buttons."""

    def __init__(self, name, texture, w=110, h=26):
        super().__init__(name, texture, 4)
        self.w, self.h = w, h

    def render(self, t):
        w, h = self.w, self.h
        img = Image.new("RGBA", (w * 4, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for f, mix in enumerate((0.15, 0.35, 0.05, 0.0)):
            ox = f * w
            top = lerp(t.card_top, t.colour("accent"), mix)
            for yy in range(h):
                d.line([ox + 1, yy, ox + w - 2, yy], fill=lerp(top, t.card_bottom, yy / h) + (245 if f != 3 else 150,))
            d.rounded_rectangle([ox, 0, ox + w - 1, h - 1], 4, outline=t.outline if f != 3 else t.shadow + (255,), width=1)
        return img


class ProgressBarSprite(Sprite):
    """A `progressbartype` (shader mode). Its frame sets the progress: value = frame / steps.

    effect: 'progress' (vanilla bar), 'radial' (vanilla progress_radial: pie slice from 12 o'clock),
    'line' (guigen's line shader, see shaders.py) or a path to any .lua effect file.
    fill / empty: Sprite-like objects (rendered into textureFile1 / textureFile2), or texture paths.
    """
    EFFECTS = {"progress": "gfx/FX/progress.lua", "radial": "gfx/FX/progress_radial.lua"}

    def __init__(self, name, texture, w, h, effect="progress", steps=1000, horizontal=True, fill=None, empty=None,
                 color=None, colortwo=None, texture2=None):
        super().__init__(name, texture, 1)
        self.w, self.h, self.effect, self.steps, self.horizontal = w, h, effect, steps, horizontal
        self.fill, self.empty, self.color, self.colortwo = fill, empty, color, colortwo
        self.texture2 = texture2 or texture.replace(".png", "_empty.png")
        self.progress = True

    @property
    def effect_file(self):
        if self.effect == "line":
            from .shaders import LINE_EFFECT
            return LINE_EFFECT
        return self.EFFECTS.get(self.effect, self.effect)

    def render(self, t):
        if self.fill is None:
            return Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        img = self.fill(t) if callable(self.fill) else self.fill
        return img

    def render_empty(self, t):
        if self.empty is None:
            return Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        return self.empty(t) if callable(self.empty) else self.empty

    @property
    def frame_size(self):
        return self.w, self.h

    @property
    def textured(self):
        """The line shader draws from colours only (the engine then runs its Color effect)."""
        return self.effect != "line"

    def gfx(self):
        s = f"\tprogressbartype = {{\n\t\tname = \"{self.name}\"\n"
        if self.textured:
            s += f"\t\ttextureFile1 = \"{self.texture}\"\n\t\ttextureFile2 = \"{self.texture2}\"\n"
        s += (f"\t\tsize = {{ x = {self.w} y = {self.h} }}\n\t\teffectFile = \"{self.effect_file}\"\n\t\tsteps = {self.steps}\n"
              f"\t\thorizontal = {'yes' if self.horizontal else 'no'}\n")
        if self.color:
            s += "\t\tcolor = { " + " ".join(f"{c:g}" for c in self.color) + " }\n"
        if self.colortwo:
            s += "\t\tcolortwo = { " + " ".join(f"{c:g}" for c in self.colortwo) + " }\n"
        return s + "\t}\n"


def solid_disc(colour, size):
    def draw_fn(t):
        col = t.colour(colour) + (255,)

        def draw(d, k):
            d.ellipse([k, k, size * k - k, size * k - k], fill=col)
        return _aa((size, size), draw)
    return draw_fn


def solid_rect(colour, w, h, alpha=255):
    def draw_fn(t):
        return Image.new("RGBA", (w, h), t.colour(colour) + (alpha,))
    return draw_fn
