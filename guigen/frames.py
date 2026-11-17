"""Variable -> frame wiring.

A scripted GUI property `elem = { frame = VAR }` needs VAR to hold 1..noOfFrames. These classes write
the scripted effect lines that compute VAR from a game value; `FrameSet.effect(name)` wraps them all
in one scripted effect (call it from your weekly / on-click refresh).

    Linear("XYZ_f_steel", "XYZ_pct_steel")              # 0..100 -> frames 1..11
    Linear("XYZ_f_mood", "XYZ_mood", frames=21)         # 0..100 -> 1..21
    Linear("X_f_lvl", "X_level", lo=-50, hi=50)         # shifts before dividing
    Thresholds("X_f_tier", "X_bandits", [25, 45, 65])   # frame 1, 2 above 25, 3 above 45 ...
    Flags("X_f_zone", "716", ["X_svy_on", "X_surveyed"])  # later flags win
"""
from .elements import num


def _step(lo, hi, frames):
    return (hi - lo) / (frames - 1)


class FrameRule:
    var = None
    frames = None

    def text(self):
        raise NotImplementedError


class Linear(FrameRule):
    """frame = round((source - lo) / step) + 1, clamped to 1..frames, step = (hi - lo) / (frames - 1)."""

    def __init__(self, var, source, frames=11, lo=0, hi=100):
        self.var, self.source, self.frames, self.lo, self.hi = var, source, frames, lo, hi

    def text(self):
        v = self.var
        s = f"set_variable = {{ {v} = {self.source} }}\n"
        if self.lo:
            s += f"subtract_from_variable = {{ {v} = {num(self.lo)} }}\n"
        s += (f"divide_variable = {{ {v} = {num(_step(self.lo, self.hi, self.frames))} }}\nround_variable = {v}\n"
              f"add_to_variable = {{ {v} = 1 }}\nclamp_variable = {{ var = {v} min = 1 max = {self.frames} }}\n")
        return s

    def value_to_frame(self, value):
        f = round((value - self.lo) / _step(self.lo, self.hi, self.frames)) + 1
        return max(1, min(self.frames, f))


class Thresholds(FrameRule):
    """frame 1 by default, frame i+2 once source exceeds thresholds[i] (ascending)."""

    def __init__(self, var, source, thresholds, eps=0.01):
        self.var, self.source, self.thresholds, self.eps = var, source, list(thresholds), eps
        self.frames = len(self.thresholds) + 1

    def text(self):
        s = f"set_variable = {{ {self.var} = 1 }}\n"
        for i, t in enumerate(self.thresholds, 2):
            s += f"if = {{ limit = {{ check_variable = {{ {self.source} > {t - self.eps} }} }} set_variable = {{ {self.var} = {i} }} }}\n"
        return s

    def value_to_frame(self, value):
        f = 1
        for i, t in enumerate(self.thresholds, 2):
            if value > t - self.eps:
                f = i
        return f


class Flags(FrameRule):
    """frame 1 by default, frame i+2 if `scope` has flags[i]; later flags win.

    scope: a state id / scope name, or None for the current scope. kind: 'state' or 'country'.
    """

    def __init__(self, var, scope, flags, kind="state"):
        self.var, self.scope, self.flags, self.kind = var, scope, list(flags), kind
        self.frames = len(self.flags) + 1

    def text(self):
        s = f"set_variable = {{ {self.var} = 1 }}\n"
        for i, fl in enumerate(self.flags, 2):
            cond = f"has_{self.kind}_flag = {fl}"
            if self.scope is not None:
                cond = f"{self.scope} = {{ {cond} }}"
            s += f"if = {{ limit = {{ {cond} }} set_variable = {{ {self.var} = {i} }} }}\n"
        return s

    def flags_to_frame(self, flags):
        f = 1
        for i, fl in enumerate(self.flags, 2):
            if fl in flags:
                f = i
        return f


class Raw(FrameRule):
    """Hand-written effect lines (kept in order with the others)."""

    def __init__(self, text, var=None, frames=None):
        self._t, self.var, self.frames = text if text.endswith("\n") else text + "\n", var, frames

    def text(self):
        return self._t


class FrameSet:
    def __init__(self):
        self.rules = []

    def add(self, rule):
        self.rules.append(rule)
        return rule

    def by_var(self):
        return {r.var: r for r in self.rules if r.var}

    def body(self):
        return "".join(r.text() for r in self.rules)

    def effect(self, name):
        from .pdxscript import indent
        return f"{name} = {{\n" + indent(self.body(), 1) + "}\n"
