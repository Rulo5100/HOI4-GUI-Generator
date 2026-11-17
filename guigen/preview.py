"""Preview renderer: mock a board to a PNG without launching the game.

What it draws:
* every element in .gui order, at its real position, with its real sprite (generated sprites from the
  build, existing ones from the mod / vanilla .gfx, DDS included) and frame;
* frames from the scripted GUI properties, computed from mock variables through the project's frame
  rules (Linear / Thresholds / Flags), so a mock `XYZ_pct_steel: 45` lights the bar the way the game will;
* `_visible` triggers (hidden elements are skipped) and `_click_enabled` (disabled buttons are dimmed);
* text with loc resolved: keys, [Scope.GetX] scripted loc (first true case, or a forced pick),
  [?var|fmt] values, £texticons (real vanilla icons when found), §colour codes with the game's own
  colour table, \\n breaks, word wrap, maxWidth / maxHeight clipping and left / centre / right format.

It also writes <board>_tooltips.png with every tooltip rendered, to check wording and colours, and
all_boards.png with the boards side by side. --debug outlines elements and prints their names.

Fonts are approximations of the game's bitmap fonts (a serif TTF at a similar size).
"""
import os
import re

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

from .elements import Button, Icon, Text, Window
from .frames import Flags, Linear, Thresholds
from .loc import parse_yml
from .mock import Mock
from .sprites import GfxIndex

TEXT_COLOURS = {  # interface/core.gfx textcolors
    "C": (35, 206, 255), "L": (195, 176, 145), "W": (255, 255, 255), "B": (0, 0, 255), "G": (0, 159, 3),
    "R": (255, 50, 50), "b": (0, 0, 0), "g": (176, 176, 176), "Y": (255, 189, 0), "H": (255, 189, 0),
    "T": (255, 255, 255), "O": (255, 112, 25), "0": (203, 0, 203), "1": (128, 120, 211), "2": (81, 112, 243),
    "3": (81, 143, 220), "4": (90, 190, 231), "5": (63, 181, 194), "6": (119, 204, 186), "7": (153, 209, 153),
    "8": (204, 163, 51), "9": (252, 169, 125), "t": (255, 76, 77),
}
FONT_SIZES = {"hoi_16mbs": 13, "hoi_18mbs": 15, "hoi_20bs": 16, "hoi_22bs": 18, "hoi_24header": 20, "hoi_30header": 25, "hoi_36header": 30}
FONT_FILES = ["C:/Windows/Fonts/georgia.ttf", "C:/Windows/Fonts/times.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
              "/Library/Fonts/Georgia.ttf", "/System/Library/Fonts/Supplemental/Georgia.ttf"]
KEY_RE = re.compile(r"^[A-Za-z][\w.\-]*$")
_font_cache = {}


class BitmapFont:
    """The game's own BMFont (gfx/fonts/<name>.fnt + .dds): exact advances, kerning and glyphs."""

    def __init__(self, fnt_path):
        self.chars, self.kern = {}, {}
        page = None
        with open(fnt_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                kind, _, rest = line.strip().partition(" ")
                kv = dict(re.findall(r'(\w+)=("[^"]*"|\S+)', rest))
                if kind == "common":
                    self.size, self.base = int(kv["lineHeight"]), int(kv["base"])
                elif kind == "page" and kv.get("id") == "0":
                    page = kv["file"].strip('"')
                elif kind == "char":
                    self.chars[int(kv["id"])] = tuple(int(kv[k]) for k in ("x", "y", "width", "height", "xoffset", "yoffset", "xadvance"))
                elif kind == "kerning":
                    self.kern[(int(kv["first"]), int(kv["second"]))] = int(kv["amount"])
        self.page = Image.open(os.path.join(os.path.dirname(fnt_path), page)).convert("RGBA")
        self.lineheight = self.size
        self._glyphs = {}

    def _char(self, c):
        return self.chars.get(ord(c)) or self.chars.get(ord("?"))

    def getlength(self, s):
        w, prev = 0, None
        for c in s:
            ch = self._char(c)
            if ch:
                w += ch[6] + (self.kern.get((prev, ord(c)), 0) if prev else 0)
            prev = ord(c)
        return w

    def draw(self, img, xy, s, fill):
        x, y = xy
        prev = None
        for c in s:
            ch = self._char(c)
            if not ch:
                continue
            if prev:
                x += self.kern.get((prev, ord(c)), 0)
            gx, gy, gw, gh, xo, yo, adv = ch
            if gw and gh:
                key = (gx, gy, gw, gh)
                if key not in self._glyphs:
                    self._glyphs[key] = self.page.crop((gx, gy, gx + gw, gy + gh)).getchannel("A")
                mask = self._glyphs[key]
                glyph = Image.new("RGBA", (gw, gh), tuple(fill) + (255,))
                glyph.putalpha(mask)
                px, py = int(x + xo), int(y + yo)
                if px >= 0 and py >= 0 and px + gw <= img.width and py + gh <= img.height:
                    img.alpha_composite(glyph, (px, py))
            x += adv
            prev = ord(c)


class TTFont:
    """Fallback when the game fonts are not available."""

    def __init__(self, size):
        f = None
        for path in FONT_FILES:
            if os.path.exists(path):
                f = ImageFont.truetype(path, size)
                break
        self.f = f or ImageFont.load_default(size)
        self.size = size
        self.lineheight = int(size * 1.25)

    def getlength(self, s):
        return self.f.getlength(s)

    def draw(self, img, xy, s, fill):
        ImageDraw.Draw(img).text(xy, s, font=self.f, fill=tuple(fill))


def font(name, vanilla=None):
    key = (name, vanilla)
    if key not in _font_cache:
        f = None
        if vanilla:
            path = os.path.join(vanilla, "gfx", "fonts", f"{name}.fnt")
            if os.path.exists(path):
                try:
                    f = BitmapFont(path)
                except Exception:
                    f = None
        _font_cache[key] = f or TTFont(FONT_SIZES.get(name, 13))
    return _font_cache[key]


class Renderer:
    def __init__(self, p, fs, mock=None, debug=False, width=520):
        self.p, self.fs, self.mock, self.debug, self.width = p, fs, mock or Mock(), debug, width
        self.gidx = GfxIndex(fs, extra_text=p.gfx_text())
        self.frames = p.frames.by_var()
        self.dts = {dt.name: dt for dt in p.defined_texts}
        self.loc = self._load_loc()
        self.notes = []
        self.clipped = []
        self._sprite_cache = {}
        self.refresh_charts()

    def refresh_charts(self):
        """Charts compute their frame / label variables from the mock (call again after the mock changes)."""
        for ch in getattr(self.p, "charts", []):
            self.mock.vars.update(ch.mock_vars(self.mock))

    def click(self, board, x, y):
        """Simulate a left click at (x, y) on the last render of `board`: run the button's effect on the mock
        if its click_enabled trigger allows it. Returns a short description, or None if nothing was hit."""
        trig, eff = dict(board.triggers), dict(board.effects)
        for el, bb in reversed(getattr(self, "last_boxes", [])):
            if bb[0] <= x < bb[2] and bb[1] <= y < bb[3]:
                if not isinstance(el, Button):
                    tt = self.resolve(el.tooltip) if el.tooltip else ""
                    return f"{el.name} ({el.kind})" + (f": {tt[:160]}" if tt else "")
                body = eff.get(f"{el.name}_click")
                if body is None:
                    return f"{el.name}: button without a click effect"
                if not self.mock.test(trig.get(f"{el.name}_click_enabled")):
                    return f"{el.name}: disabled ({trig.get(f'{el.name}_click_enabled')})"
                self.mock.run(body, skip={self.p.refresh_effect, self.p.frame_effect} | {ch.update for ch in self.p.charts})
                self.refresh_charts()
                return f"{el.name}: clicked"
        return None

    # ------------------------------------------------------------------ data
    def _load_loc(self):
        import glob
        loc = {}
        files = glob.glob(os.path.join(self.fs.root, "localisation", "**", "*english*.yml"), recursive=True)
        if self.fs.vanilla:
            files += glob.glob(os.path.join(self.fs.vanilla, "localisation", "english", "state_names*.yml"))
        for f in files:
            with open(f, encoding="utf-8-sig", errors="ignore") as fh:
                for k, v in parse_yml(fh.read().replace("\r\n", "\n")).items():
                    loc.setdefault(k, v)
        loc.update(self.p.locs.entries)
        return loc

    def sprite_strip(self, name):
        """(PIL strip, frames) or (None, 1)."""
        if name in self._sprite_cache:
            return self._sprite_cache[name]
        s = self.p.sprites.get(name)
        if s:
            out = (s.image(self.p.theme), s.frames)
        else:
            im = self.gidx.open(name)
            out = (im, self.gidx.frames(name) or 1) if im is not None else (None, 1)
            if im is None:
                self.notes.append(f"sprite {name} not found or not readable")
        self._sprite_cache[name] = out
        return out

    def progress_frame(self, s, frame):
        """Emulate a progressbartype (shader mode) for the given frame value."""
        from PIL import ImageDraw as D
        w, h = s.w, s.h
        frac = max(0.0, min(1.0, (frame or 0) / s.steps))
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        if s.effect == "line":
            v = int(frame or 0)
            a, b = v // 1000, v % 1000
            rgba = tuple(int(c * 255) for c in s.colortwo)
            lw = max(1, round(s.color[2] * 10))
            big = Image.new("RGBA", (w * 4, h * 4), (0, 0, 0, 0))
            d = D.Draw(big)
            y0, y1 = (h - a) * 4, (h - b) * 4
            if s.color[3]:
                d.polygon([(0, y0), (w * 4, y1), (w * 4, h * 4), (0, h * 4)], fill=rgba[:3] + (int(255 * s.color[3]),))
            slope = (y1 - y0) / (w * 4)
            d.line([(-4, y0 - 4 * slope), (w * 4 + 4, y1 + 4 * slope)], fill=rgba, width=lw * 4)
            return big.resize((w, h), Image.LANCZOS)
        fill = s.image(self.p.theme).convert("RGBA").resize((w, h))
        empty = s.render_empty(self.p.theme).convert("RGBA").resize((w, h))
        mask = Image.new("L", (w, h), 0)
        md = D.Draw(mask)
        if s.effect == "radial":
            if frac >= 1:
                md.rectangle([0, 0, w, h], fill=255)
            elif frac > 0:
                md.pieslice([-w, -h, 2 * w, 2 * h], -90, -90 + 360 * frac, fill=255)
        elif s.horizontal:
            md.rectangle([0, 0, int(w * frac) - 1, h], fill=255)
        else:
            md.rectangle([0, h - int(h * frac), w, h], fill=255)
        out.alpha_composite(empty)
        out.paste(fill, (0, 0), Image.composite(fill.getchannel("A"), Image.new("L", (w, h), 0), mask))
        return out

    def sprite_frame(self, name, frame, scale=None):
        s = self.p.sprites.get(name)
        if s is not None and getattr(s, "progress", False):
            cell = self.progress_frame(s, frame)
            if scale and scale != 1:
                cell = cell.resize((max(1, int(cell.width * scale)), max(1, int(cell.height * scale))), Image.LANCZOS)
            return cell
        strip, n = self.sprite_strip(name)
        if strip is None:
            return None
        w = strip.width // max(1, n)
        f = max(1, min(n, frame or 1))
        cell = strip.crop(((f - 1) * w, 0, f * w, strip.height))
        if scale and scale != 1:
            cell = cell.resize((max(1, int(cell.width * scale)), max(1, int(cell.height * scale))), Image.LANCZOS)
        return cell

    # ------------------------------------------------------------------ text
    def fmt_value(self, v, fmt):
        pct = "%" in fmt
        sign = "+" in fmt
        digits = re.search(r"\d", fmt)
        d = int(digits.group(0)) if digits else 0
        if pct:
            v *= 100
        s = f"{v:.{d}f}"
        if sign and v >= 0:
            s = "+" + s
        return s + ("%" if pct else "")

    def resolve(self, text, depth=0):
        if depth > 4 or text is None:
            return text or ""
        if KEY_RE.match(text) and text in self.loc:
            text = self.loc[text]

        def sloc(m):
            scope, name = m.group(1), m.group(2)
            if name in self.dts:
                key = self.mock.sloc.get(name)
                if not key:
                    for trg, k, _ in self.dts[name].cases:
                        if not trg or self.mock.test(trg):
                            key = k
                            break
                return self.resolve(key or "", depth + 1)
            if name == "GetName" and scope and scope.isdigit():
                return self.loc.get(f"STATE_{scope}", f"State {scope}")
            return f"<{name}>"

        text = re.sub(r"\[(?:([\w.@]+)\.)?(Get\w+)\]", sloc, text)
        text = re.sub(r"\[\?([\w.@:]+)(?:\|([^\]]*))?\]", lambda m: self.fmt_value(self.mock.var(m.group(1)), m.group(2) or ""), text)
        return text

    def runs(self, text, base_colour):
        """[(kind, value, colour)] kind: word | space | icon | nl."""
        out, stack, i = [], [base_colour], 0
        buf = ""

        def flush():
            nonlocal buf
            for part in re.split(r"( +)", buf):
                if part:
                    out.append(("space" if part.startswith(" ") else "word", part, stack[-1]))
            buf = ""
        while i < len(text):
            ch = text[i]
            if ch == "§" and i + 1 < len(text):
                flush()
                code = text[i + 1]
                if code == "!":
                    if len(stack) > 1:
                        stack.pop()
                else:
                    stack.append(TEXT_COLOURS.get(code, stack[-1]))
                i += 2
                continue
            if ch == "\\" and text[i + 1:i + 2] == "n":
                flush()
                out.append(("nl", None, None))
                i += 2
                continue
            if ch == "£":
                flush()
                m = re.match(r"£([\w]+)(?:\|(\d+))?", text[i:])
                if m:
                    out.append(("icon", (m.group(1), int(m.group(2) or 1)), None))
                    i += m.end()
                    continue
            buf += ch
            i += 1
        flush()
        return out

    def text_icon(self, name, frame, h):
        for cand in (f"GFX_{name}", name, f"GFX_{name}_icon"):
            if cand in self.gidx:
                cell = self.sprite_frame(cand, frame)
                if cell is not None:
                    s = h / max(1, cell.height)
                    return cell.resize((max(1, int(cell.width * s)), h), Image.LANCZOS)
        return None

    def draw_text(self, img, box, text, font_name, fmt="left", colour=None):
        x0, y0, w, h = box
        f = font(font_name, self.fs.vanilla)
        lh = f.lineheight
        colour = colour or self.p.theme.preview_text
        lines, line, lw = [], [], 0
        for kind, val, col in self.runs(self.resolve(text), colour):
            if kind == "nl":
                lines.append((line, lw))
                line, lw = [], 0
                continue
            if kind == "icon":
                ic = self.text_icon(val[0], val[1], f.size)
                piece = ("icon", ic, None)
                pw = ic.width if ic is not None else f.size
            else:
                piece = (kind, val, col)
                pw = f.getlength(val)
            if kind != "space" and lw + pw > w and line:
                while line and line[-1][0] == "space":
                    lw -= f.getlength(line[-1][1])
                    line.pop()
                lines.append((line, lw))
                line, lw = [], 0
            if kind == "space" and not line:
                continue
            line.append(piece)
            lw += pw
        lines.append((line, lw))
        d = ImageDraw.Draw(img)
        y = y0
        self.last_clipped = False
        for n, (line, lw) in enumerate(lines):
            if y + lh > y0 + h + 2 and y > y0:
                self.last_clipped = any(k != "space" for ln, _ in lines[n:] for k, _, _ in ln)
                break                                    # clipped by maxHeight, like the game
            x = x0 + {"centre": (w - lw) / 2, "center": (w - lw) / 2, "right": w - lw}.get(fmt or "left", 0)
            for kind, val, col in line:
                if kind == "icon":
                    if val is not None:
                        if x >= 0 and y >= 0:
                            img.alpha_composite(val, (int(x), int(y + 1)))
                        x += val.width
                    else:
                        d.rectangle([x + 1, y + 2, x + f.size - 2, y + f.size - 1], outline=(150, 150, 150))
                        x += f.size
                    continue
                f.draw(img, (x, y), val, col)
                x += f.getlength(val)
            y += lh
        return self.last_clipped

    # ------------------------------------------------------------------ boards
    def frame_for(self, board, el):
        for name, kv in board.props:
            if name == el.name and "frame" in kv:
                var = kv["frame"]
                rule = self.frames.get(var)
                if isinstance(rule, (Linear, Thresholds)):
                    return rule.value_to_frame(self.mock.var(rule.source))
                if isinstance(rule, Flags):
                    have = self.mock.flags if rule.kind == "country" else self.mock.state_flags.get(str(rule.scope), set())
                    return rule.flags_to_frame(have)
                if var in self.mock.vars:
                    return int(self.mock.vars[var])
        return el.frame if isinstance(el, Icon) else 1

    def nine_slice(self, sprite_name, w, h):
        """A corneredTileSpriteType stretched to w x h (corners kept, edges and centre stretched)."""
        s = self.p.sprites.get(sprite_name)
        src = s.image(self.p.theme) if s is not None else self.gidx.open(sprite_name)
        if src is None:
            return None
        b = getattr(s, "border", None) or min(src.width, src.height) // 4
        b = min(b, w // 2, h // 2)
        sw, sh = src.size
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        xs = [(0, b, 0, b), (b, sw - b, b, w - b), (sw - b, sw, w - b, w)]
        ys = [(0, b, 0, b), (b, sh - b, b, h - b), (sh - b, sh, h - b, h)]
        for sx0, sx1, dx0, dx1 in xs:
            for sy0, sy1, dy0, dy1 in ys:
                if dx1 > dx0 and dy1 > dy0 and sx1 > sx0 and sy1 > sy0:
                    out.paste(src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0)), (dx0, dy0))
        return out

    def render_board(self, b, respect_visible=False):
        """Draw a board. respect_visible: when the board's own `visible` trigger is false under the mock,
        draw a placeholder instead (used by guigen app, where a click can close a window)."""
        trig = dict(b.triggers)
        W = b.window.w if isinstance(b.window.w, int) else self.width
        H = max(40, b.window.h or b.auto_height())
        self.last_boxes = []
        if respect_visible and b.visible_trigger and not self.mock.test(b.visible_trigger):
            img = Image.new("RGBA", (min(W, 420), 60), self.p.theme.preview_bg)
            ImageDraw.Draw(img).text((10, 10), f"{b.name} is hidden:\n{b.visible_trigger}", fill=self.p.theme.preview_text,
                                     font=TTFont(12).f)
            return img
        bg = dict(b.window.extra).get("background")
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0) if bg else self.p.theme.preview_bg)
        if bg:
            import re as _re
            m = _re.search(r'quadTextureSprite\s*=\s*"?([\w.\-]+)', bg)
            panel = self.nine_slice(m.group(1), W, H) if m else None
            if panel is not None:
                img.alpha_composite(panel)
        pos = {}
        for name, kv in b.props:
            if "x" in kv or "y" in kv:
                pos[name] = kv
        dbg = []

        def visible(name):
            return self.mock.show_all or self.mock.test(trig.get(f"{name}_visible"))

        def rec(win, ox, oy):
            for el in win.children:
                if not visible(el.name):
                    continue
                x, y = ox + el.x, oy + el.y
                if el.name in pos:
                    kv = pos[el.name]
                    if "x" in kv:
                        x = ox + int(self.mock.var(kv["x"]))
                    if "y" in kv:
                        y = oy + int(self.mock.var(kv["y"]))
                if isinstance(el, Window):
                    rec(el, x, y)
                    continue
                if isinstance(el, (Icon, Button)):
                    cell = self.sprite_frame(el.sprite, self.frame_for(b, el), el.scale)
                    if cell is not None:
                        if isinstance(el, Button) and not self.mock.test(trig.get(f"{el.name}_click_enabled")):
                            cell = ImageEnhance.Brightness(ImageEnhance.Color(cell).enhance(0.2)).enhance(0.6)
                        img.alpha_composite(cell, (max(0, x), max(0, y)) if x >= 0 and y >= 0 else (0, 0))
                        bw, bh = cell.size
                    else:
                        bw, bh = el.w or 24, el.h or 24
                        ImageDraw.Draw(img).rectangle([x, y, x + bw, y + bh], outline=(255, 0, 255))
                    if isinstance(el, Button) and el.text:
                        self.draw_text(img, (x, y + max(0, (bh - 16) // 2), bw, bh), el.text, el.font, "centre")
                    dbg.append((el, (x, y, x + bw, y + bh)))
                elif isinstance(el, Text):
                    if self.draw_text(img, (x, y, el.w, el.h), el.text, el.font, el.fmt):
                        self.clipped.append(f"{b.name}/{el.name}: text does not fit {el.w}x{el.h} ({self.resolve(el.text)[:60]!r})")
                    dbg.append((el, (x, y, x + el.w, y + el.h)))
        rec(b.window, 0, 0)
        self.last_boxes = dbg
        if self.debug:
            d = ImageDraw.Draw(img)
            small = TTFont(9).f
            col = {"text": (90, 160, 255), "icon": (90, 220, 120), "button": (255, 160, 60)}
            for el, bb in dbg:
                d.rectangle(bb, outline=col.get(el.kind, (255, 255, 255)))
                d.text((bb[0] + 1, bb[1]), el.name.replace(self.p.prefix + "_", ""), font=small, fill=col.get(el.kind))
        return img

    def render_tooltips(self, b, width=380, limit=80):
        keys = []
        for el in b.elements():
            if el.tooltip and el.tooltip not in keys:
                keys.append(el.tooltip)
        keys = keys[:limit]
        pieces = []
        small = TTFont(10).f
        for k in keys:
            tmp = Image.new("RGBA", (width, 600), (24, 22, 20, 255))
            self.draw_text(tmp, (8, 18, width - 16, 580), k, "hoi_16mbs")
            ImageDraw.Draw(tmp).text((8, 2), k, font=small, fill=(140, 140, 140))
            bbox = tmp.getchannel("R").point(lambda v: 255 if v > 40 else 0).getbbox() or (0, 0, width, 30)
            pieces.append(tmp.crop((0, 0, width, min(600, bbox[3] + 8))))
        if not pieces:
            return None
        cols = 2
        rows = [pieces[i::cols] for i in range(cols)]
        colh = [sum(p.height + 6 for p in r) for r in rows]
        out = Image.new("RGBA", (cols * (width + 8), max(colh) + 6), (12, 11, 10, 255))
        for c, r in enumerate(rows):
            y = 6
            for pce in r:
                out.alpha_composite(pce, (c * (width + 8) + 4, y))
                y += pce.height + 6
        return out


def apply_overrides(m, overrides):
    """--set VAR=VALUE, VAR=[1,2,3] (array), flag:NAME, -flag:NAME."""
    for o in overrides or []:
        if o.startswith("flag:"):
            m.flags.add(o[5:])
            continue
        if o.startswith("-flag:"):
            m.flags.discard(o[6:])
            continue
        k, _, v = o.partition("=")
        v = v.strip()
        if v.startswith("["):
            m.arrays[k.strip()] = [float(x) for x in v.strip("[]").split(",") if x.strip()]
        else:
            m.vars[k.strip()] = float(v)


def preview_project(p, fs, out_dir, mock=None, debug=False, width=520, boards=None, overrides=None, suffix=""):
    m = mock if isinstance(mock, Mock) else Mock.load(mock)
    apply_overrides(m, overrides)
    r = Renderer(p, fs, m, debug, width)
    os.makedirs(out_dir, exist_ok=True)
    files, imgs = [], []
    for b in p.boards:
        if boards and b.name not in boards:
            continue
        img = r.render_board(b)
        path = os.path.join(out_dir, f"{b.name}{suffix}.png")
        img.save(path)
        files.append(path)
        imgs.append(img)
        tt = r.render_tooltips(b)
        if tt is not None:
            path = os.path.join(out_dir, f"{b.name}{suffix}_tooltips.png")
            tt.save(path)
            files.append(path)
    if len(imgs) > 1:
        sheet = Image.new("RGBA", (sum(i.width for i in imgs) + 12 * (len(imgs) + 1), max(i.height for i in imgs) + 24), (10, 10, 10, 255))
        x = 12
        for i in imgs:
            sheet.alpha_composite(i, (x, 12))
            x += i.width + 12
        path = os.path.join(out_dir, f"all_boards{suffix}.png")
        sheet.save(path)
        files.append(path)
    notes = sorted(set(r.notes)) + [f"clipped: {c}" for c in r.clipped]
    if m.unknown:
        notes.append("triggers assumed true: " + ", ".join(sorted(m.unknown)))
    return files, notes
