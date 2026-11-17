"""A mock game state for the preview: evaluates the triggers guigen writes.

Mock YAML (all keys optional):

    vars:          {MAN_pct_steel: 45, political_power: 120, MAN_h_kw: 1}
    default_var:   50          # value of any variable not listed
    flags:         [MAN_zone_unl_hi]                    # country flags
    state_flags:   {716: [MAN_surveyed], 328: [MAN_zone_hi]}
    focuses:       [MAN_sec_blockhouses]
    not_owned:     [1043]      # states the player does not own / control
    scripted_loc:  {GetMANPlanTitle: MAN_PLT_1}         # force a defined_text case by its loc key
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
        return self.vars.get(name, self.default_var)

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
