"""A mock game state for the preview: evaluates the triggers guigen writes.

Mock YAML (all keys optional):

    vars:          {XYZ_pct_steel: 45, political_power: 120, XYZ_leader: 1}
    arrays:        {XYZ_gdp_hist: [100, 104, 103, 110]}     # line chart history; ARR^num and ARR^i work
    default_var:   50          # value of any variable not listed
    flags:         [XYZ_reform_unlocked]                  # country flags
    state_flags:   {716: [XYZ_surveyed], 328: [XYZ_zone_hi]}
    focuses:       [XYZ_blockhouses]
    not_owned:     [1043]      # states the player does not own / control
    scripted_loc:  {GetXYZPlanTitle: XYZ_PLT_1}         # force a defined_text case by its loc key
    default_trigger: true      # result of a trigger the evaluator does not understand
    show_all:      false       # true: ignore _visible triggers

The evaluator understands check_variable, has_country_flag, has_state_flag, has_completed_focus,
has_political_power, command_power, has_manpower, has_stability, has_war_support, is_owned_by,
is_controlled_by, is_owned_and_controlled_by, always, NOT, OR, AND, and state / ROOT scopes.
"""
import re

from .pdxscript import parse

COUNTRY_VALUES = {"has_political_power": "political_power", "command_power": "command_power",
                  "has_manpower": "manpower", "has_stability": "stability", "has_war_support": "war_support"}


class Mock:
    def __init__(self, data=None):
        d = data or {}
        self.vars = {str(k): float(v) for k, v in (d.get("vars") or {}).items()}
        self.arrays = {str(k): [float(x) for x in (v or [])] for k, v in (d.get("arrays") or {}).items()}
        self.default_var = float(d.get("default_var", 50))
        self.flags = set(d.get("flags") or [])
        self.state_flags = {str(k): set(v or []) for k, v in (d.get("state_flags") or {}).items()}
        self.focuses = set(d.get("focuses") or [])
        self.not_owned = {str(s) for s in (d.get("not_owned") or [])}
        self.sloc = dict(d.get("scripted_loc") or {})
        self.default_trigger = bool(d.get("default_trigger", True))
        self.show_all = bool(d.get("show_all", False))
        self.unknown = set()

    @classmethod
    def load(cls, path):
        if not path:
            return cls()
        import yaml
        with open(path, encoding="utf-8") as f:
            return cls(yaml.safe_load(f) or {})

    # ------------------------------------------------------------------ values
    def var(self, name):
        name = name.split("@")[0]
        for pre in ("ROOT.", "THIS.", "PREV.", "FROM."):
            if name.startswith(pre):
                name = name[len(pre):]
        if "^" in name:                                   # array element / size: ARR^3, ARR^num
            arr, idx = name.split("^", 1)
            a = self.array(arr)
            if idx == "num":
                return float(len(a))
            try:
                i = int(float(idx)) if not idx.isidentifier() else int(self.var(idx))
            except ValueError:
                return 0.0
            return a[i] if 0 <= i < len(a) else 0.0
        return self.vars.get(name, self.default_var)

    def array(self, name):
        return self.arrays.get(name, [])

    def value(self, tok):
        try:
            return float(tok)
        except (TypeError, ValueError):
            return self.var(tok)

    # ------------------------------------------------------------------ triggers
    def test(self, text, scope=None):
        if text is None:
            return True
        return self._all(parse(text), scope)

    def _all(self, items, scope):
        return all(self._one(k, op, v, scope) for k, op, v in items)

    @staticmethod
    def _cmp(a, op, b):
        return {"<": a < b, ">": a > b, "=": a == b, "<=": a <= b, ">=": a >= b, "!=": a != b}.get(op, True)

    def _one(self, k, op, v, scope):
        if k is None:
            return True
        if k == "NOT":
            return not any(self._one(*it, scope) for it in v) if isinstance(v, list) else True
        if k == "OR":
            return any(self._one(*it, scope) for it in v)
        if k == "AND":
            return self._all(v, scope)
        if k in ("custom_trigger_tooltip", "hidden_trigger"):
            return self._all([it for it in v if it[0] != "tooltip"], scope)
        if k in ("ROOT", "THIS", "FROM", "PREV", "owner", "controller"):
            return self._all(v, None) if isinstance(v, list) else True
        if re.fullmatch(r"\d+", k) and isinstance(v, list):
            return self._all(v, k)
        if k == "always":
            return v == "yes"
        if k == "check_variable" and isinstance(v, list):
            if len(v) == 1 and v[0][1] in ("<", ">", "=", "<=", ">="):
                name, cop, val = v[0]
                return self._cmp(self.var(name), cop, self.value(val))
            kv = {a: b for a, _, b in v}
            if "var" in kv:
                return self._cmp(self.var(kv["var"]), {"less_than": "<", "greater_than": ">", "equals": "="}.get(kv.get("compare"), "="),
                                 self.value(kv.get("value", 0)))
            return self.default_trigger
        if k == "has_country_flag":
            return (v if isinstance(v, str) else dict((a, b) for a, _, b in v).get("flag")) in self.flags
        if k == "has_state_flag":
            name = v if isinstance(v, str) else dict((a, b) for a, _, b in v).get("flag")
            return name in self.state_flags.get(scope or "", set())
        if k == "has_completed_focus":
            return v in self.focuses
        if k in COUNTRY_VALUES:
            return self._cmp(self.var(COUNTRY_VALUES[k]), op, self.value(v))
        if k in ("is_owned_by", "is_controlled_by", "is_owned_and_controlled_by"):
            return (scope or "") not in self.not_owned
        self.unknown.add(k)
        return self.default_trigger

    # ------------------------------------------------------------------ effects (for clicks in guigen app)
    VAR_OPS = {"set": lambda a, b: b, "add_to": lambda a, b: a + b, "subtract_from": lambda a, b: a - b,
               "multiply": lambda a, b: a * b, "divide": lambda a, b: a / b if b else a}

    def run(self, text, scope=None, skip=()):
        """Apply a click effect to the mock: variables, flags, if / else_if / else, state scopes,
        add_political_power. Scripted effects named in `skip` (refresh effects) are ignored; any other
        unknown command is recorded in `unknown_effects`."""
        self._run(parse(text), scope, set(skip))

    def _run(self, items, scope, skip):
        last = None                         # result of the previous if / else_if in this block
        for k, op, v in items:
            if k == "if" or (k == "else_if" and last is False):
                lim = [it for it in v if it[0] == "limit"]
                ok = self._all(lim[0][2], scope) if lim else True
                if ok:
                    self._run([it for it in v if it[0] != "limit"], scope, skip)
                last = ok
                continue
            if k == "else_if":
                continue
            if k == "else":
                if last is False:
                    self._run(v, scope, skip)
                last = None
                continue
            last = None
            self._do(k, v, scope, skip)

    def _do(self, k, v, scope, skip):
        m = re.fullmatch(r"(set|add_to|subtract_from|multiply|divide)_(temp_)?variable", k or "")
        if m and isinstance(v, list):
            kv = {a: b for a, _, b in v}
            if "var" in kv:
                name, val = kv["var"], kv.get("value", 0)
            else:
                name, _, val = v[0]
            self.vars[name] = float(self.VAR_OPS[m.group(1)](self.var(name), self.value(val)))
            return
        if k in ("clamp_variable", "clamp_temp_variable"):
            kv = {a: b for a, _, b in v}
            x = self.var(kv["var"])
            if "min" in kv:
                x = max(x, self.value(kv["min"]))
            if "max" in kv:
                x = min(x, self.value(kv["max"]))
            self.vars[kv["var"]] = x
            return
        if k in ("round_variable", "round_temp_variable"):
            self.vars[v] = float(round(self.var(v)))
            return
        if k == "set_country_flag":
            self.flags.add(v if isinstance(v, str) else dict((a, b) for a, _, b in v)["flag"])
            return
        if k == "clr_country_flag":
            self.flags.discard(v)
            return
        if k == "set_state_flag" and scope:
            self.state_flags.setdefault(scope, set()).add(v if isinstance(v, str) else dict((a, b) for a, _, b in v)["flag"])
            return
        if k == "clr_state_flag" and scope:
            self.state_flags.get(scope, set()).discard(v)
            return
        if k == "add_political_power":
            self.vars["political_power"] = self.var("political_power") + self.value(v)
            return
        if k and re.fullmatch(r"\d+", k) and isinstance(v, list):
            self._run(v, k, skip)
            return
        if k in ("ROOT", "THIS", "FROM") and isinstance(v, list):
            self._run(v, None, skip)
            return
        if v == "yes" and k in skip:
            return
        if not hasattr(self, "unknown_effects"):
            self.unknown_effects = set()
        self.unknown_effects.add(k)
