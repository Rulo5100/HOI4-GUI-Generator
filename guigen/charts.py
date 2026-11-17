"""Charts: bar, horizontal bar, stacked bar, pie, donut, line, area, ring gauge, scale marker, scatter /
compass, heatmap, legend.

Every chart:
* registers its sprites (sprite mode: pre-rendered frame sheets; shader mode: progressbartype),
* adds its elements to the board (at x, y in the board or the current tab section),
* writes a scripted effect `<name>_update` that turns your variables / arrays into frame variables
  (and helper values such as maxima and percentages for the labels), collected in the project's
  frames file; call `<P>_guigen_refresh = yes` (or the chart's own update) after the data changes,
* knows the same maths in Python, so the preview draws it from a mock state.

Data comes from plain variables (`var`) or, for line charts, arrays of history (`array`), e.g.

    LineChart(p, b, "XYZ_gdp", 10, 40, 360, 120, series=[{"array": "XYZ_gdp_hist", "source": "XYZ_gdp", "label": "GDP"}], points=24)

and `XYZ_gdp_record = yes` monthly appends XYZ_gdp to the history and drops the oldest entry.
"""
from .chartsprites import (ChartBackground, FillBar, Gradient, LineSegments, Marker, ProgressBarSprite, Wedge,
                           solid_disc, solid_rect)
from .elements import num
from .frames import Linear
from .shaders import line_frame
from .sprites import Static, Swatches


def _v(x):
    """A number or a variable name, as a value in script."""
    return num(x) if isinstance(x, (int, float)) else str(x)


class Chart:
    kind = "chart"

    def __init__(self, p, b, name, x, y, mode="sprite"):
        if mode not in ("sprite", "shader"):
            raise ValueError("mode must be 'sprite' or 'shader'")
        self.p, self.b, self.name, self.x, self.y, self.mode = p, b, name, x, y, mode
        self.N = name.upper()
        self._frame_vars = {}
        p.charts.append(self)

    # ------------------------------------------------------------------ helpers
    def gfx(self, stem):
        return f"GFX_{self.name}_{stem}"

    def png(self, stem):
        return f"{self.p.files['png_dir']}/{self.name}_{stem}.png"

    def sprite(self, s):
        return self.p.sprites.get(s.name) or self.p.sprite(s)

    def loc(self, key, text):
        return self.p.loc(key, text)

    def frame_var(self, var, frames):
        self._frame_vars[var] = frames
        return var

    @property
    def update(self):
        return f"{self.name}_update"

    def frame_vars(self):
        return dict(self._frame_vars)

    def effects(self):
        """[(effect name, body)] written to the frames file."""
        return [(self.update, self.update_body())]

    def update_body(self):
        raise NotImplementedError

    def mock_vars(self, mock):
        return {}

    @staticmethod
    def _frame_calc(var, src, steps, maxvar, base=1):
        """var = round(src * steps / max) + base, clamped."""
        return (f"set_variable = {{ {var} = {src} }}\nmultiply_variable = {{ {var} = {steps} }}\n"
                f"divide_variable = {{ {var} = {maxvar} }}\nround_variable = {var}\n"
                + (f"add_to_variable = {{ {var} = {base} }}\n" if base else "")
                + f"clamp_variable = {{ var = {var} min = {base} max = {steps + base} }}\n")


def _items(seq, keys):
    out = []
    for it in seq:
        if isinstance(it, dict):
            out.append(dict(it))
        else:
            out.append(dict(zip(keys, it)))
    return out


# ====================================================================== bar charts
class BarChart(Chart):
    """Vertical columns (or horizontal bars with horizontal=True), one per entry of `bars`:
    bars = [{"var": "XYZ_steel", "label": "Steel", "colour": "gold"}, ...]   (or tuples var, label, colour)

    max: a number, a variable, or None to scale to the largest bar. Values below 0 draw as empty.
    The chart sets <name>_max (shown on the axis) and the bar frames <name>_f_<i>.
    """

    def __init__(self, p, b, name, x, y, w, h, bars, max=None, steps=20, gap=None, horizontal=False, label_w=110,
                 value_fmt="0", y_div=4, show_values=True, mode="auto"):
        """mode (horizontal bars): 'sprite' frame sheets, 'shader' vanilla progress.lua bars, 'auto' = sprite
        unless the sheet would exceed 8192 px. Vertical columns are always frame sheets."""
        super().__init__(p, b, name, x, y, "sprite")
        self.bars = _items(bars, ("var", "label", "colour"))
        self.w, self.h, self.max, self.steps, self.horizontal, self.value_fmt = w, h, max, steps, horizontal, value_fmt
        self.base = 1
        n = len(self.bars)
        N = self.N
        if horizontal:
            row = h // n
            bh = max_(6, row - (gap if gap is not None else max_(4, row // 4)))
            bw = w - label_w - (46 if show_values else 6)
            self.shader = mode == "shader" or (mode == "auto" and bw * (steps + 1) > 8192)
            if self.shader:
                self.steps, self.base = 1000, 0
            for i, bar in enumerate(self.bars):
                col = bar.get("colour", "accent")
                if self.shader:
                    spr = self.sprite(ProgressBarSprite(self.gfx(f"pbar_{_cname(col)}_{bw}x{bh}"), self.png(f"pbar_{_cname(col)}_{bw}x{bh}"),
                                                        bw, bh, "progress", 1000, fill=solid_rect(col, bw, bh), empty=_bar_bg(bw, bh)))
                else:
                    spr = self.sprite(FillBar(self.gfx(f"hbar_{_cname(col)}_{bw}x{bh}"), self.png(f"hbar_{_cname(col)}_{bw}x{bh}"),
                                              bw, bh, col, steps, "right", bg=True))
                yy = y + i * row
                tt = f"{N}_TT{i}"
                b.text(f"{name}_l{i}", x, yy + (bh - 16) // 2, f"{N}_L{i}", label_w - 6, 18, tooltip=tt)
                b.icon(f"{name}_b{i}", x + label_w, yy, spr.name, frame=self.base,
                       frame_var=self.frame_var(f"{name}_f_{i}", self.steps + self.base), tooltip=tt, w=bw, h=bh)
                if show_values:
                    b.text(f"{name}_v{i}", x + label_w + bw + 6, yy + (bh - 16) // 2, f"{N}_V{i}", 40, 18)
                self._labels(i, bar)
        else:
            self.sprite(ChartBackground(self.gfx(f"bg_{w}x{h}"), self.png(f"bg_{w}x{h}"), w, h, y_div))
            b.icon(f"{name}_bg", x, y, self.gfx(f"bg_{w}x{h}"), frame=None)
            g = gap if gap is not None else max_(4, w // (n * 5))
            bw = (w - g * (n + 1)) // n
            for i, bar in enumerate(self.bars):
                col = bar.get("colour", "accent")
                spr = self.sprite(FillBar(self.gfx(f"col_{_cname(col)}_{bw}x{h - 2}"), self.png(f"col_{_cname(col)}_{bw}x{h - 2}"),
                                          bw, h - 2, col, steps, "up"))
                bx = x + g + i * (bw + g)
                tt = f"{N}_TT{i}"
                b.icon(f"{name}_b{i}", bx, y + 1, spr.name, frame_var=self.frame_var(f"{name}_f_{i}", steps + 1), tooltip=tt)
                b.text(f"{name}_l{i}", bx - g // 2, y + h + 2, f"{N}_L{i}", bw + g, 18, fmt="centre", tooltip=tt)
                if show_values:
                    b.text(f"{name}_v{i}", bx - g // 2, y + h + 18, f"{N}_V{i}", bw + g, 18, fmt="centre")
                self._labels(i, bar)
            b.text(f"{name}_ymax", x + 3, y + 2, f"{N}_YMAX", 60, 16)
            self.loc(f"{N}_YMAX", f"§g[?{name}_max|{value_fmt}]§!")

    def _labels(self, i, bar):
        N = self.N
        self.loc(f"{N}_L{i}", bar.get("label", bar["var"]))
        self.loc(f"{N}_V{i}", f"§Y[?{bar['var']}|{self.value_fmt}]§!")
        self.loc(f"{N}_TT{i}", bar.get("tooltip") or f"§Y{bar.get('label', bar['var'])}§!: §Y[?{bar['var']}|{self.value_fmt}]§!")

    def update_body(self):
        n, mv = self.name, f"{self.name}_max"
        if self.max is None:
            s = f"set_variable = {{ {mv} = 1 }}\n"
            for bar in self.bars:
                s += f"if = {{ limit = {{ check_variable = {{ {bar['var']} > {mv} }} }} set_variable = {{ {mv} = {bar['var']} }} }}\n"
        else:
            s = f"set_variable = {{ {mv} = {_v(self.max)} }}\n"
        for i, bar in enumerate(self.bars):
            s += self._frame_calc(f"{n}_f_{i}", bar["var"], self.steps, mv, self.base)
        return s

    def mock_vars(self, mock):
        vals = [mock.var(bar["var"]) for bar in self.bars]
        mx = max([1.0] + vals) if self.max is None else (float(self.max) if isinstance(self.max, (int, float)) else mock.var(self.max))
        out = {f"{self.name}_max": mx}
        for i, v in enumerate(vals):
            out[f"{self.name}_f_{i}"] = max(self.base, min(self.steps + self.base, round(v * self.steps / (mx or 1)) + self.base))
        return out


def max_(a, b):
    return a if a > b else b


def _bar_bg(w, h):
    """Empty part of a shader-mode bar: the theme's bar background and outline."""
    def draw(t):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (w, h), t.bar_bg)
        ImageDraw.Draw(img).rectangle([0, 0, w - 1, h - 1], outline=t.bar_outline)
        return img
    return draw


def _cname(c):
    return c if isinstance(c, str) else "c%02x%02x%02x" % tuple(c[:3])


# ====================================================================== cumulative layers (pie, donut, stacked)
class _Layered(Chart):
    def _cum_body(self, steps, base):
        n, tot = self.name, f"{self.name}_total"
        if self.total is None:
            s = f"set_variable = {{ {tot} = 0 }}\n" + "".join(f"add_to_variable = {{ {tot} = {it['var']} }}\n" for it in self.items)
        else:
            s = f"set_variable = {{ {tot} = {_v(self.total)} }}\n"
        inner = "set_temp_variable = { gg_cum = 0 }\n"
        zero = ""
        for k, it in enumerate(self.items):
            fv, pv = f"{n}_f_{k}", f"{n}_p_{k}"
            inner += f"add_to_temp_variable = {{ gg_cum = {it['var']} }}\n" + self._frame_calc(fv, "gg_cum", steps, tot, base)
            inner += f"set_variable = {{ {pv} = {it['var']} }}\nmultiply_variable = {{ {pv} = 100 }}\ndivide_variable = {{ {pv} = {tot} }}\n"
            zero += f"set_variable = {{ {fv} = {base} }}\nset_variable = {{ {pv} = 0 }}\n"
        from .pdxscript import indent
        return s + f"if = {{\n\tlimit = {{ check_variable = {{ {tot} > 0 }} }}\n{indent(inner, 1)}}}\nelse = {{\n{indent(zero, 1)}}}\n"

    def _cum_mock(self, mock, steps, base):
        vals = [mock.var(it["var"]) for it in self.items]
        tot = sum(vals) if self.total is None else (float(self.total) if isinstance(self.total, (int, float)) else mock.var(self.total))
        out = {f"{self.name}_total": tot}
        cum = 0
        for k, v in enumerate(vals):
            cum += v
            out[f"{self.name}_f_{k}"] = max(base, min(steps + base, round(cum * steps / tot) + base)) if tot > 0 else base
            out[f"{self.name}_p_{k}"] = v * 100 / tot if tot > 0 else 0
        return out

    def _legend(self, x, y, w, row=20, value=True):
        b, n, N = self.b, self.name, self.N
        key = self.sprite(Swatches(self.gfx("key"), self.png("key"), [it.get("colour", "accent") for it in self.items], 12))
        for k, it in enumerate(self.items):
            yy = y + k * row
            b.icon(f"{n}_key{k}", x, yy + 3, key.name, frame=k + 1)
            b.text(f"{n}_kl{k}", x + 18, yy, f"{N}_L{k}", w - 18 - (48 if value else 0), 18, tooltip=f"{N}_TT{k}")
            if value:
                b.text(f"{n}_kv{k}", x + w - 46, yy, f"{N}_P{k}", 46, 18, fmt="right")
        return len(self.items) * row


class PieChart(_Layered):
    """Pie (inner=0) or donut (inner=0.55) with slices = [{"var", "label", "colour"}].
    total: None (sum of the slices), a number or a variable. Sets <name>_p_<k> (percent of each slice).
    legend: draw a legend to the right (legend_w wide). center: loc key shown in the hole of a donut."""

    def __init__(self, p, b, name, x, y, size, slices, inner=0.0, steps=50, total=None, legend=True, legend_w=170,
                 center=None, mode="sprite"):
        super().__init__(p, b, name, x, y, mode)
        self.items = _items(slices, ("var", "label", "colour"))
        self.size, self.inner, self.steps, self.total = size, inner, steps, total
        n, N = self.name, self.N
        st = steps if mode == "sprite" else 1000
        self.layer_steps = st
        base = 1 if mode == "sprite" else 0
        self.base = base
        tt = f"{N}_TT"
        self.loc(tt, self._summary())
        for k in reversed(range(len(self.items))):
            it = self.items[k]
            col = it.get("colour", "accent")
            if mode == "sprite":
                spr = self.sprite(Wedge(self.gfx(f"w{k}"), self.png(f"w{k}"), size, col, steps, inner))
            else:
                spr = self.sprite(ProgressBarSprite(self.gfx(f"r{k}"), self.png(f"r{k}"), size, size, "radial", 1000,
                                                    fill=solid_disc(col, size)))
            b.icon(f"{n}_s{k}", x, y, spr.name, frame=base, frame_var=self.frame_var(f"{n}_f_{k}", st + base),
                   tooltip=tt, w=size, h=size)
            self.loc(f"{N}_L{k}", it.get("label", it["var"]))
            self.loc(f"{N}_P{k}", f"§Y[?{n}_p_{k}|0]%§!")
            self.loc(f"{N}_TT{k}", it.get("tooltip") or f"§Y{it.get('label', it['var'])}§!: §Y[?{it['var']}|1]§! (§Y[?{n}_p_{k}|0]%§!)")
        if mode == "shader" and inner:
            hole = int(size * inner)
            spr = self.sprite(Static(self.gfx(f"hole{hole}"), self.png(f"hole{hole}"), _hole(hole)))
            b.icon(f"{n}_hole", x + (size - hole) // 2, y + (size - hole) // 2, spr.name, frame=None)
        if center:
            b.text(f"{n}_c", x + size // 4, y + size // 2 - 10, center, size // 2, 20, "hoi_18mbs", "centre")
        if legend:
            self._legend(x + size + 14, y + max_(0, (size - 20 * len(self.items)) // 2), legend_w)

    def _summary(self):
        lines = [f"£white_dot §Y{it.get('label', it['var'])}§!: §Y[?{self.name}_p_{k}|0]%§!" for k, it in enumerate(self.items)]
        return "\\n".join(lines)

    def update_body(self):
        return self._cum_body(self.layer_steps, self.base)

    def mock_vars(self, mock):
        return self._cum_mock(mock, self.layer_steps, self.base)


def _hole(d):
    return lambda t: _disc(t, d)


def _disc(t, d):
    from .chartsprites import _aa
    col = t.panel_bg[:3] + (255,)

    def draw(dr, k):
        dr.ellipse([k, k, d * k - k, d * k - k], fill=col)
    return _aa((d, d), draw)


class StackedBar(_Layered):
    """One bar split into parts = [{"var", "label", "colour"}] (horizontal by default).
    total: None (sum of the parts), a number or a variable (then the bar shows the parts' share of it)."""

    def __init__(self, p, b, name, x, y, w, h, parts, steps=50, total=None, horizontal=True, legend=True, legend_w=200, mode="auto"):
        """mode: 'sprite' frame sheets, 'shader' vanilla progress.lua layers, 'auto' = sprite unless the sheet
        would exceed 8192 px (wide bars)."""
        super().__init__(p, b, name, x, y, "sprite")
        self.items = _items(parts, ("var", "label", "colour"))
        length = w if horizontal else h
        self.shader = mode == "shader" or (mode == "auto" and (w if horizontal else w) * (steps + 1) > 8192)
        self.w, self.h, self.total = w, h, total
        self.steps, self.base = (1000, 0) if self.shader else (steps, 1)
        n, N = self.name, self.N
        direction = "right" if horizontal else "up"
        last = len(self.items) - 1
        for k in reversed(range(len(self.items))):
            it = self.items[k]
            col = it.get("colour", "accent")
            if self.shader:
                spr = self.sprite(ProgressBarSprite(self.gfx(f"pseg{k}_{w}x{h}"), self.png(f"pseg{k}_{w}x{h}"), w, h, "progress", 1000,
                                                    horizontal=horizontal, fill=solid_rect(col, w, h),
                                                    empty=_bar_bg(w, h) if k == last else None))
            else:
                spr = self.sprite(FillBar(self.gfx(f"seg{k}_{w}x{h}"), self.png(f"seg{k}_{w}x{h}"), w, h, col, steps, direction,
                                          bg=(k == last)))
            b.icon(f"{n}_s{k}", x, y, spr.name, frame=self.base, frame_var=self.frame_var(f"{n}_f_{k}", self.steps + self.base),
                   tooltip=f"{N}_TT{k}", w=w, h=h)
            self.loc(f"{N}_L{k}", it.get("label", it["var"]))
            self.loc(f"{N}_P{k}", f"§Y[?{n}_p_{k}|0]%§!")
            self.loc(f"{N}_TT{k}", it.get("tooltip") or f"§Y{it.get('label', it['var'])}§!: §Y[?{it['var']}|1]§! (§Y[?{n}_p_{k}|0]%§!)")
        if legend:
            if horizontal:
                self._legend_row(x, y + h + 4, w)
            else:
                self._legend(x + w + 12, y, legend_w)

    def _legend_row(self, x, y, w):
        b, n, N = self.b, self.name, self.N
        key = self.sprite(Swatches(self.gfx("key"), self.png("key"), [it.get("colour", "accent") for it in self.items], 12))
        cw = w // len(self.items)
        for k in range(len(self.items)):
            b.icon(f"{n}_key{k}", x + k * cw, y + 3, key.name, frame=k + 1)
            b.text(f"{n}_kl{k}", x + k * cw + 16, y, f"{N}_KL{k}", cw - 18, 18, tooltip=f"{N}_TT{k}")
            self.loc(f"{N}_KL{k}", f"{self.items[k].get('label', self.items[k]['var'])} [?{n}_p_{k}|0]%")

    def update_body(self):
        return self._cum_body(self.steps, self.base)

    def mock_vars(self, mock):
        return self._cum_mock(mock, self.steps, self.base)


# ====================================================================== line chart
class LineChart(Chart):
    """Line (or area) chart of one or more history arrays.

    series = [{"array": "XYZ_gdp_hist", "label": "GDP", "colour": "green", "source": "XYZ_gdp"}, ...]
    points: how many values are shown (the newest `points` entries; the record effect keeps the array at this size).
    lo / hi: numbers, variables, or None to scale to the data. Sets <name>_lo, <name>_hi, <name>_mid.
    Sprite mode: each segment is one cell, a frame sheet of `levels` x `levels` start / end heights
    (cell_width x levels^2 pixels, kept within max_sheet; levels is picked automatically, at most 40).
    sub=2..4 splits each segment into narrower cells, which allows more levels, but on gentle slopes the
    cells round to flat-then-step and the line looks like a staircase, so one cell is the default.
    For smooth lines use shader mode: pixel-exact, anti-aliased lines via gfx/FX/guigen_line.shader
    (experimental).
    """

    def __init__(self, p, b, name, x, y, w, h, series, points=12, lo=None, hi=None, levels=None, width=2.0, area=False,
                 dots=False, y_div=4, labels=True, value_fmt="1", mode="sprite", max_sheet=8192, sub=None):
        super().__init__(p, b, name, x, y, mode)
        self.series = _items(series, ("array", "label", "colour"))
        seg_w = w // (points - 1)
        fit = lambda cell: int((max_sheet / cell) ** 0.5)          # most levels a cell width allows
        if mode == "shader" or sub is None:
            sub = 1
        if levels is None:
            levels = max(8, min(40, fit(seg_w // sub), h // 3))
        self.sub = sub
        self.cw = cw = seg_w // sub                              # one cell (a segment is `sub` cells)
        self.points, self.lo, self.hi, self.levels, self.value_fmt = points, lo, hi, levels, value_fmt
        n, N = self.name, self.N
        self.w, self.h = cw * sub * (points - 1), h
        self.pad = int(width) + 1
        self.sprite(ChartBackground(self.gfx(f"bg_{self.w}x{h}"), self.png(f"bg_{self.w}x{h}"), self.w, h, y_div, points - 1 if points <= 13 else 0))
        b.icon(f"{n}_bg", x, y, self.gfx(f"bg_{self.w}x{h}"), frame=None)
        alpha = 70 if area else 0
        for s, se in enumerate(self.series):
            col = se.get("colour", "accent")
            if mode == "sprite":
                spr = self.sprite(LineSegments(self.gfx(f"seg{s}_{cw}x{h}"), self.png(f"seg{s}_{cw}x{h}"), cw, h, col, levels, width, alpha, dots))
                fmax = levels * levels
            else:
                rgb = p.theme.colour(col)
                spr = self.sprite(ProgressBarSprite(self.gfx(f"line{s}_{cw}x{h}"), self.png(f"line{s}_{cw}x{h}"), cw, h, "line", 1000000,
                                                    color=(cw / 1000, h / 1000, width / 10, alpha / 255),
                                                    colortwo=tuple(round(c / 255, 3) for c in rgb) + (1,)))
                fmax = 1000000
            for i in range(points - 1):
                for j in range(self.sub):
                    b.icon(self.cell_name(s, i, j), x + (i * self.sub + j) * cw, y, spr.name, frame=1 if mode == "sprite" else 0,
                           frame_var=self.frame_var(self.cell_var(s, i, j), fmax), tooltip=f"{N}_PT{s}_{i}",
                           visible=f"check_variable = {{ {se['array']}^num > {i + 1} }}", w=cw, h=h)
                self.loc(f"{N}_PT{s}_{i}", f"§Y{se.get('label', se['array'])}§!: §Y[?{n}_v{s}_{i}|{value_fmt}]§!")
        if labels:
            b.text(f"{n}_hi", x + 3, y + 2, f"{N}_HI", 70, 16)
            b.text(f"{n}_mid", x + 3, y + h // 2 - 8, f"{N}_MID", 70, 16)
            b.text(f"{n}_lo", x + 3, y + h - 18, f"{N}_LO", 70, 16)
            self.loc(f"{N}_HI", f"§g[?{n}_hi|{value_fmt}]§!")
            self.loc(f"{N}_MID", f"§g[?{n}_mid|{value_fmt}]§!")
            self.loc(f"{N}_LO", f"§g[?{n}_lo|{value_fmt}]§!")

    def cell_name(self, s, i, j):
        return f"{self.name}_s{s}_{i}" if self.sub == 1 else f"{self.name}_s{s}_{i}_{j}"

    def cell_var(self, s, i, j):
        return f"{self.name}_f{s}_{i}" if self.sub == 1 else f"{self.name}_f{s}_{i}_{j}"

    @property
    def record(self):
        return f"{self.name}_record"

    def effects(self):
        out = [(self.update, self.update_body())]
        rec = ""
        for se in self.series:
            if se.get("source"):
                a = se["array"]
                rec += (f"add_to_array = {{ array = {a} value = {se['source']} }}\n"
                        f"while_loop_effect = {{\n\tlimit = {{ check_variable = {{ {a}^num > {self.points} }} }}\n"
                        f"\tremove_from_array = {{ array = {a} index = 0 }}\n}}\n")
        if rec:
            out.append((self.record, rec + f"{self.update} = yes\n"))
        return out

    def update_body(self):
        n = self.name
        lo, hi, mid, rng = f"{n}_lo", f"{n}_hi", f"{n}_mid", f"{n}_rng"
        s = ""
        a0 = self.series[0]["array"]
        if self.hi is None or self.lo is None:
            s += f"set_variable = {{ {hi} = 0 }}\nset_variable = {{ {lo} = 0 }}\n"
            s += f"if = {{ limit = {{ check_variable = {{ {a0}^num > 0 }} }} set_variable = {{ {hi} = {a0}^0 }} set_variable = {{ {lo} = {a0}^0 }} }}\n"
            for se in self.series:
                s += (f"for_each_loop = {{\n\tarray = {se['array']}\n\tvalue = gg_v\n"
                      f"\tif = {{ limit = {{ check_variable = {{ gg_v > {hi} }} }} set_variable = {{ {hi} = gg_v }} }}\n"
                      f"\tif = {{ limit = {{ check_variable = {{ gg_v < {lo} }} }} set_variable = {{ {lo} = gg_v }} }}\n}}\n")
        if self.hi is not None:
            s += f"set_variable = {{ {hi} = {_v(self.hi)} }}\n"
        if self.lo is not None:
            s += f"set_variable = {{ {lo} = {_v(self.lo)} }}\n"
        s += (f"set_variable = {{ {rng} = {hi} }}\nsubtract_from_variable = {{ {rng} = {lo} }}\n"
              f"if = {{ limit = {{ check_variable = {{ {rng} < 0.0001 }} }} set_variable = {{ {rng} = 1 }} }}\n"
              f"set_variable = {{ {mid} = {rng} }}\ndivide_variable = {{ {mid} = 2 }}\nadd_to_variable = {{ {mid} = {lo} }}\n")
        scale = self.levels - 1 if self.mode == "sprite" else self.h - 2 * self.pad
        mult = self.levels if self.mode == "sprite" else 1000
        off = 0 if self.mode == "sprite" else self.pad
        from .pdxscript import indent

        def level(tv):
            return (f"subtract_from_temp_variable = {{ {tv} = {lo} }}\n"
                    f"multiply_temp_variable = {{ {tv} = {scale} }}\ndivide_temp_variable = {{ {tv} = {rng} }}\n"
                    f"round_temp_variable = {tv}\nclamp_temp_variable = {{ var = {tv} min = 0 max = {scale} }}\n"
                    + (f"add_to_temp_variable = {{ {tv} = {off} }}\n" if off else ""))

        def point(tv, frac):
            """tv = the value at `frac` (0..1) along the segment (gg_r0 + gg_rd * frac)."""
            if frac == 0:
                return f"set_temp_variable = {{ {tv} = gg_r0 }}\n"
            if frac == 1:
                return f"set_temp_variable = {{ {tv} = gg_r1 }}\n"
            return (f"set_temp_variable = {{ {tv} = gg_rd }}\nmultiply_temp_variable = {{ {tv} = {num(round(frac, 4))} }}\n"
                    f"add_to_temp_variable = {{ {tv} = gg_r0 }}\n")

        for si, se in enumerate(self.series):
            a = se["array"]
            for i in range(self.points - 1):
                body = ""
                if self.sub == 1:
                    for tv, idx in (("gg_a", i), ("gg_b", i + 1)):
                        body += f"set_temp_variable = {{ {tv} = {a}^{idx} }}\n" + level(tv)
                else:
                    body += (f"set_temp_variable = {{ gg_r0 = {a}^{i} }}\nset_temp_variable = {{ gg_r1 = {a}^{i + 1} }}\n"
                             f"set_temp_variable = {{ gg_rd = gg_r1 }}\nsubtract_from_temp_variable = {{ gg_rd = gg_r0 }}\n")
                for j in range(self.sub):
                    f = self.cell_var(si, i, j)
                    if self.sub > 1:
                        body += point("gg_a", j / self.sub) + level("gg_a") + point("gg_b", (j + 1) / self.sub) + level("gg_b")
                    body += (f"set_variable = {{ {f} = gg_a }}\nmultiply_variable = {{ {f} = {mult} }}\nadd_to_variable = {{ {f} = gg_b }}\n"
                             + ("add_to_variable = { %s = 1 }\n" % f if self.mode == "sprite" else ""))
                body += f"set_variable = {{ {n}_v{si}_{i} = {a}^{i} }}\n"
                s += f"if = {{\n\tlimit = {{ check_variable = {{ {a}^num > {i + 1} }} }}\n{indent(body, 1)}}}\n"
        return s

    def mock_vars(self, mock):
        n = self.name
        arrays = [mock.array(se["array"]) for se in self.series]
        allv = [v for arr in arrays for v in arr]
        hi = max(allv) if allv else 0
        lo = min(allv) if allv else 0
        if self.hi is not None:
            hi = float(self.hi) if isinstance(self.hi, (int, float)) else mock.var(self.hi)
        if self.lo is not None:
            lo = float(self.lo) if isinstance(self.lo, (int, float)) else mock.var(self.lo)
        rng = hi - lo if hi - lo >= 0.0001 else 1
        out = {f"{n}_lo": lo, f"{n}_hi": hi, f"{n}_mid": lo + rng / 2, f"{n}_rng": rng}
        scale = self.levels - 1 if self.mode == "sprite" else self.h - 2 * self.pad
        off = 0 if self.mode == "sprite" else self.pad

        def lvl(v):
            return max(0, min(scale, round((v - lo) * scale / rng))) + off
        for si, arr in enumerate(arrays):
            for i in range(self.points - 1):
                if len(arr) > i + 1:
                    r0, r1 = arr[i], arr[i + 1]
                    for j in range(self.sub):
                        v0 = r0 + (r1 - r0) * round(j / self.sub, 4) if 0 < j else r0
                        v1 = r1 if j + 1 == self.sub else r0 + (r1 - r0) * round((j + 1) / self.sub, 4)
                        a, b_ = lvl(v0), lvl(v1)
                        out[self.cell_var(si, i, j)] = LineSegments.frame_of(a, b_, self.levels) if self.mode == "sprite" else line_frame(a, b_)
                    out[f"{n}_v{si}_{i}"] = arr[i]
        return out


# ====================================================================== single-value widgets
class RingGauge(Chart):
    """A ring (donut) filled to var between lo and hi, with the value in the middle."""

    def __init__(self, p, b, name, x, y, size, var, lo=0, hi=100, colour="accent", steps=50, inner=0.62, label=None, value_fmt="0"):
        super().__init__(p, b, name, x, y, "sprite")
        self.var, self.lo, self.hi, self.steps = var, lo, hi, steps
        n, N = self.name, self.N
        track = self.sprite(Wedge(self.gfx(f"track{size}"), self.png(f"track{size}"), size, "card_top", 1, inner, edge=False))
        fill = self.sprite(Wedge(self.gfx(f"ring_{_cname(colour)}{size}"), self.png(f"ring_{_cname(colour)}{size}"), size, colour, steps, inner))
        b.icon(f"{n}_track", x, y, track.name, frame=2)
        p.frame(Linear(f"{n}_f", var, steps + 1, lo, hi))
        b.icon(f"{n}_ring", x, y, fill.name, frame_var=f"{n}_f", tooltip=f"{N}_TT")
        b.text(f"{n}_v", x, y + size // 2 - 11, f"{N}_V", size, 22, "hoi_18mbs", "centre")
        self.loc(f"{N}_V", f"§Y[?{var}|{value_fmt}]§!")
        self.loc(f"{N}_TT", label or f"§Y[?{var}|{value_fmt}]§! (range {num(lo)} to {num(hi)})")
        if label:
            b.text(f"{n}_l", x - 20, y + size + 2, f"{N}_L", size + 40, 18, fmt="centre")
            self.loc(f"{N}_L", label)

    def effects(self):
        return []


class ScaleMarker(Chart):
    """A marker sliding along a gradient scale, like an index between two poles.
    Sets <name>_x (the marker's x position property)."""

    def __init__(self, p, b, name, x, y, w, var, lo=0, hi=100, stops=("bad", "mid", "good"), h=10, marker=14,
                 shape="triangle", left=None, right=None, colour="accent"):
        super().__init__(p, b, name, x, y, "sprite")
        self.var, self.lo, self.hi, self.w, self.ms = var, lo, hi, w, marker
        n, N = self.name, self.N
        g = Gradient("_", "_", 1, 1, stops, 2)

        def strip(t, w=w, h=h, g=g):
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(img)
            for xx in range(w):
                d.line([xx, 0, xx, h - 1], fill=g.colour_at(t, xx / max(1, w - 1)) + (255,))
            d.rectangle([0, 0, w - 1, h - 1], outline=t.outline)
            return img
        bar = self.sprite(Static(self.gfx(f"scale_{w}x{h}"), self.png(f"scale_{w}x{h}"), strip))
        mk = self.sprite(Marker(self.gfx(f"marker_{shape}{marker}"), self.png(f"marker_{shape}{marker}"), marker,
                                colour, shape))
        b.icon(f"{n}_bar", x, y + marker - 2, bar.name, frame=None, tooltip=f"{N}_TT")
        b.icon(f"{n}_mk", x - marker // 2, y, mk.name, frame=None, tooltip=f"{N}_TT")
        b.prop(f"{n}_mk", x=f"{n}_x")
        self.loc(f"{N}_TT", f"§Y[?{var}|0]§! on a scale of {num(lo)} to {num(hi)}")
        if left:
            b.text(f"{n}_left", x, y + marker + h, f"{N}_LEFT", w // 2, 18)
            self.loc(f"{N}_LEFT", left)
        if right:
            b.text(f"{n}_right", x + w // 2, y + marker + h, f"{N}_RIGHT", w // 2, 18, fmt="right")
            self.loc(f"{N}_RIGHT", right)

    def update_body(self):
        xv = f"{self.name}_x"
        return (f"set_variable = {{ {xv} = {self.var} }}\nsubtract_from_variable = {{ {xv} = {_v(self.lo)} }}\n"
                f"multiply_variable = {{ {xv} = {self.w} }}\ndivide_variable = {{ {xv} = {num(self.hi - self.lo) if isinstance(self.hi, (int, float)) else self.hi} }}\n"
                f"round_variable = {xv}\nclamp_variable = {{ var = {xv} min = 0 max = {self.w} }}\n"
                f"add_to_variable = {{ {xv} = {self.x - self.ms // 2} }}\n")

    def mock_vars(self, mock):
        v = mock.var(self.var)
        px = max(0, min(self.w, round((v - self.lo) * self.w / (self.hi - self.lo))))
        return {f"{self.name}_x": px + self.x - self.ms // 2}


class Scatter(Chart):
    """Points positioned in a plot by two variables each (a political compass, a risk map...).
    points = [{"x": var, "y": var, "label": "...", "colour": ..., "shape": "dot"}]."""

    def __init__(self, p, b, name, x, y, w, h, points, xlo=-100, xhi=100, ylo=-100, yhi=100, marker=12, quadrants=None, x_div=2, y_div=2):
        super().__init__(p, b, name, x, y, "sprite")
        self.items = _items(points, ("x", "y", "label", "colour"))
        self.w, self.h, self.xlo, self.xhi, self.ylo, self.yhi, self.ms = w, h, xlo, xhi, ylo, yhi, marker
        n, N = self.name, self.N
        self.sprite(ChartBackground(self.gfx(f"plane_{w}x{h}"), self.png(f"plane_{w}x{h}"), w, h, y_div, x_div, axes=False))
        b.icon(f"{n}_bg", x, y, self.gfx(f"plane_{w}x{h}"), frame=None)
        for i, (qx, qy, key) in enumerate(quadrants or []):
            b.text(f"{n}_q{i}", x + qx, y + qy, f"{N}_Q{i}", w // 2 - 8, 18, fmt="centre")
            self.loc(f"{N}_Q{i}", key)
        for i, it in enumerate(self.items):
            col = it.get("colour", "accent")
            mk = self.sprite(Marker(self.gfx(f"pt_{_cname(col)}_{it.get('shape', 'dot')}{marker}"),
                                    self.png(f"pt_{_cname(col)}_{it.get('shape', 'dot')}{marker}"), marker, col, it.get("shape", "dot")))
            b.icon(f"{n}_p{i}", x, y, mk.name, frame=None, tooltip=f"{N}_TT{i}")
            b.prop(f"{n}_p{i}", x=f"{n}_x{i}", y=f"{n}_y{i}")
            self.loc(f"{N}_TT{i}", f"§Y{it.get('label', '')}§!: [?{it['x']}|0], [?{it['y']}|0]")

    def update_body(self):
        n, s = self.name, ""
        for i, it in enumerate(self.items):
            for axis, var, lo, hi, size, org, flip in (("x", it["x"], self.xlo, self.xhi, self.w, self.x, False),
                                                       ("y", it["y"], self.ylo, self.yhi, self.h, self.y, True)):
                v = f"{n}_{axis}{i}"
                s += (f"set_variable = {{ {v} = {var} }}\nsubtract_from_variable = {{ {v} = {num(lo)} }}\n"
                      f"multiply_variable = {{ {v} = {size} }}\ndivide_variable = {{ {v} = {num(hi - lo)} }}\n"
                      f"round_variable = {v}\nclamp_variable = {{ var = {v} min = 0 max = {size} }}\n")
                if flip:
                    s += f"multiply_variable = {{ {v} = -1 }}\nadd_to_variable = {{ {v} = {size} }}\n"
                s += f"add_to_variable = {{ {v} = {org - self.ms // 2} }}\n"
        return s

    def mock_vars(self, mock):
        out = {}
        for i, it in enumerate(self.items):
            px = max(0, min(self.w, round((mock.var(it["x"]) - self.xlo) * self.w / (self.xhi - self.xlo))))
            py = max(0, min(self.h, round((mock.var(it["y"]) - self.ylo) * self.h / (self.yhi - self.ylo))))
            out[f"{self.name}_x{i}"] = px + self.x - self.ms // 2
            out[f"{self.name}_y{i}"] = self.h - py + self.y - self.ms // 2
        return out


class Heatmap(Chart):
    """A grid of coloured cells: rows x cols, each cell's value from var(row_key, col_key).
    lo / hi map onto `steps` colours along `stops`. Row / column headers from the labels."""

    def __init__(self, p, b, name, x, y, rows, cols, var, cell=(34, 22), lo=0, hi=100, steps=10, stops=("good", "mid", "bad"),
                 row_w=90, value_fmt="0"):
        super().__init__(p, b, name, x, y, "sprite")
        n, N = self.name, self.N
        cw, ch = cell
        grad = self.sprite(Gradient(self.gfx(f"cells_{cw}x{ch}"), self.png(f"cells_{cw}x{ch}"), cw, ch, stops, steps))
        rows, cols = _items(rows, ("key", "label")), _items(cols, ("key", "label"))
        for j, c in enumerate(cols):
            b.text(f"{n}_ch{j}", x + row_w + j * cw, y, f"{N}_C{j}", cw, 18, fmt="centre")
            self.loc(f"{N}_C{j}", c.get("label", c["key"]))
        for i, r in enumerate(rows):
            yy = y + 20 + i * ch
            b.text(f"{n}_rh{i}", x, yy + (ch - 16) // 2, f"{N}_R{i}", row_w - 4, 18)
            self.loc(f"{N}_R{i}", r.get("label", r["key"]))
            for j, c in enumerate(cols):
                v = var(r["key"], c["key"])
                fv = f"{n}_f_{r['key']}_{c['key']}"
                p.frame(Linear(fv, v, steps, lo, hi))
                b.icon(f"{n}_c_{r['key']}_{c['key']}", x + row_w + j * cw, yy, grad.name, frame_var=fv, tooltip=f"{N}_TT_{i}_{j}")
                b.text(f"{n}_t_{r['key']}_{c['key']}", x + row_w + j * cw, yy + (ch - 16) // 2, f"{N}_T_{i}_{j}", cw, 18, fmt="centre")
                self.loc(f"{N}_TT_{i}_{j}", f"§Y{r.get('label', r['key'])}§!, §Y{c.get('label', c['key'])}§!: §Y[?{v}|{value_fmt}]§!")
                self.loc(f"{N}_T_{i}_{j}", f"[?{v}|{value_fmt}]")

    def effects(self):
        return []


def legend(b, p, name, x, y, items, row=20, w=160):
    """A free-standing legend: items = [(label, colour)]."""
    key = p.sprites.get(f"GFX_{name}_key") or p.sprite(Swatches(f"GFX_{name}_key", f"{p.files['png_dir']}/{name}_key.png",
                                                                [c for _, c in items], 12))
    for k, (label, _) in enumerate(items):
        b.icon(f"{name}_key{k}", x, y + k * row + 3, key.name, frame=k + 1)
        b.text(f"{name}_kl{k}", x + 18, y + k * row, f"{name.upper()}_KL{k}", w - 18, 18)
        p.loc(f"{name.upper()}_KL{k}", label)
    return len(items) * row
