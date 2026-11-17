"""Boards (one scripted GUI + its window) and the Project that collects everything a spec builds.

A Board keeps three ordered lists, exactly as they end up in common/scripted_guis:

* props    -> properties = { elem = { frame = VAR } }  (also x / y / image)
* triggers -> triggers   = { elem_visible = {...} elem_click_enabled = {...} }
* effects  -> effects    = { elem_click = {...} }

Element helpers (`text`, `icon`, `button`) append to these lists at call time when you pass
`frame=`, `visible=`, `enabled=` or `click=`; you can also call `visible()` / `enabled()` / `click()`
later to control the order.
"""
from .elements import Button, GridBox, Icon, Text, Window

CONTEXT_TYPES = {
    "player_context", "selected_country_context", "selected_state_context", "diplomacy_target_context",
    "decision_category", "diplomatic_action", "national_focus_context", "country_mapicon", "state_mapicon",
}
PARENT_TOKENS = {
    "top_bar", "decision_tab", "technology_tab", "trade_tab", "construction_tab", "production_tab", "deployment_tab",
    "logistics_tab", "diplomacy_tab", "national_focus", "politics_tab", "selected_country_view", "selected_state_view",
    "selected_country_view_info", "selected_country_view_diplomacy", "army_ledger", "navy_ledger", "civilian_ledger",
    "air_ledger", "tech_infantry_folder", "tech_support_folder", "tech_armor_folder", "tech_artillery_folder",
    "tech_land_doctrine_folder", "tech_naval_folder", "tech_naval_doctrine_folder", "tech_air_techs_folder",
    "tech_air_doctrine_folder", "tech_electronics_folder", "tech_industry_folder",
}
CLICK_MODIFIERS = ("", "right", "shift", "alt", "control", "shift_right", "alt_right", "control_right")


class Board:
    def __init__(self, project, name, context="decision_category", window_name=None, height=0, width="100%%",
                 x=0, y=0, parent_token=None, parent_window=None, parent_gui=None, visible=None, dirty=None,
                 map_mode=None, mapicon_targets=None, extra_keys=None):
        if context not in CONTEXT_TYPES:
            raise ValueError(f"{name}: unknown context_type {context!r}")
        if parent_token and parent_token not in PARENT_TOKENS:
            raise ValueError(f"{name}: unknown parent_window_token {parent_token!r}")
        self.project, self.name, self.context = project, name, context
        self.window = Window(window_name or name, x, y, width, height)
        self.parent_token, self.parent_window, self.parent_gui = parent_token, parent_window, parent_gui
        self.visible_trigger, self.dirty, self.map_mode, self.mapicon_targets = visible, dirty, map_mode, mapicon_targets
        self.extra_keys = list((extra_keys or {}).items())
        self.props, self.triggers, self.effects, self.dynamic_lists = [], [], [], []
        self.ai_weights = []
        self._target = [self.window]            # window stack (tab sections push child windows)

    # ------------------------------------------------------------------ elements
    @property
    def container(self):
        return self._target[-1]

    def add(self, el):
        el.board = self
        self.container.add(el)
        return el

    def text(self, name, x, y, text, w, h=20, font="hoi_16mbs", fmt="left", tooltip=None, visible=None, extra=None):
        el = self.add(Text(name, x, y, text, w, h, font, fmt, tooltip, extra))
        if visible:
            self.visible(name, visible)
        return el

    def icon(self, name, x, y, sprite, frame=1, frame_var=None, scale=None, tooltip=None, visible=None, w=None, h=None, extra=None):
        """frame_var: wire a scripted GUI frame property (the icon keeps `frame` as its static frame)."""
        fw, fh = self._sprite_size(sprite, scale)
        el = self.add(Icon(name, x, y, sprite, frame, scale, tooltip, w or fw, h or fh, extra))
        if frame_var:
            self.prop(name, frame=frame_var)
        if visible:
            self.visible(name, visible)
        return el

    def button(self, name, x, y, sprite, tooltip=None, text=None, scale=None, font="hoi_16mbs", click=None,
               enabled=None, visible=None, clicksound="click_default", w=None, h=None, extra=None):
        fw, fh = self._sprite_size(sprite, scale)
        el = self.add(Button(name, x, y, sprite, tooltip, text, font, scale, clicksound, w or fw, h or fh, extra))
        if visible:
            self.visible(name, visible)
        if enabled:
            self.enabled(name, enabled)
        if click:
            self.click(name, click)
        return el

    def gridbox(self, name, x, y, w, h, slot_w, slot_h, **kw):
        return self.add(GridBox(name, x, y, w, h, slot_w, slot_h, **kw))

    def _sprite_size(self, sprite, scale):
        sz = self.project.sprite_size(sprite) if self.project else None
        if not sz:
            return 0, 0
        s = scale or 1
        return int(sz[0] * s), int(sz[1] * s)

    # ------------------------------------------------------------------ scripted gui wiring
    def prop(self, elem, frame=None, x=None, y=None, image=None):
        self.props.append((elem, dict((k, v) for k, v in (("image", image), ("frame", frame), ("x", x), ("y", y)) if v is not None)))

    def trigger(self, key, body):
        self.triggers.append((key, body))

    def effect(self, key, body):
        self.effects.append((key, body))

    def visible(self, elem, cond):
        self.trigger(f"{elem}_visible", cond)

    def enabled(self, elem, cond, modifier=""):
        self.trigger(f"{elem}_{modifier + '_' if modifier else ''}click_enabled", cond)

    def click(self, elem, body, modifier=""):
        if modifier not in CLICK_MODIFIERS:
            raise ValueError(f"unknown click modifier {modifier!r}")
        self.effect(f"{elem}_{modifier + '_' if modifier else ''}click", body)

    def dynamic_list(self, gridbox, array, entry_container=None, country_entry=None, state_entry=None,
                     value=None, index=None, change_scope=None):
        self.dynamic_lists.append(dict(name=gridbox, array=array, entry_container=entry_container,
                                       country_scope_entry_container=country_entry, state_scope_entry_container=state_entry,
                                       value=value, index=index, change_scope=change_scope))

    # ------------------------------------------------------------------ sections (used by tabs.py)
    def push(self, window):
        self.container.add(window)
        window.board = self
        self._target.append(window)
        return window

    def pop(self):
        if len(self._target) == 1:
            raise RuntimeError("pop() without push()")
        return self._target.pop()

    # ------------------------------------------------------------------ layout
    def elements(self):
        return list(self.window.walk())

    def element(self, name):
        for e in self.window.walk():
            if e.name == name:
                return e
        return None

    def auto_height(self, pad=6):
        bottom = 0
        for e, (ox, oy) in self.absolute():
            bottom = max(bottom, oy + e.y + (e.h or 20))
        self.window.h = bottom + pad
        return self.window.h

    def absolute(self, with_parent=False):
        """(element, (offset_x, offset_y)) with the offset of the element's parent window
        (and the parent window itself when with_parent)."""
        out = []

        def rec(win, ox, oy):
            for c in win.children:
                out.append((c, (ox, oy), win) if with_parent else (c, (ox, oy)))
                if isinstance(c, Window):
                    rec(c, ox + c.x, oy + c.y)
        rec(self.window, 0, 0)
        return out

    # ------------------------------------------------------------------ output
    def scripted_gui(self):
        s = f"\t{self.name} = {{\n\t\tcontext_type = {self.context}\n\t\twindow_name = \"{self.window.name}\"\n"
        if self.parent_token:
            s += f"\t\tparent_window_token = {self.parent_token}\n"
        if self.parent_window:
            s += f"\t\tparent_window_name = \"{self.parent_window}\"\n"
        if self.parent_gui:
            s += f"\t\tparent_scripted_gui = \"{self.parent_gui}\"\n"
        if self.map_mode:
            s += f"\t\tmap_mode = {self.map_mode}\n"
        if self.mapicon_targets:
            s += f"\t\tmapicon_targets = {{ {self.mapicon_targets} }}\n"
        if self.visible_trigger:
            s += f"\t\tvisible = {{ {self.visible_trigger} }}\n"
        if self.dirty:
            s += f"\t\tdirty = {self.dirty}\n"
        for k, v in self.extra_keys:
            s += f"\t\t{k} = {v}\n"
        if self.dynamic_lists:
            s += "\t\tdynamic_lists = {\n"
            for d in self.dynamic_lists:
                s += f"\t\t\t{d['name']} = {{\n\t\t\t\tarray = {d['array']}\n"
                for k in ("value", "index"):
                    if d[k]:
                        s += f"\t\t\t\t{k} = {d[k]}\n"
                if d["change_scope"] is not None:
                    s += f"\t\t\t\tchange_scope = {'yes' if d['change_scope'] else 'no'}\n"
                for k in ("entry_container", "country_scope_entry_container", "state_scope_entry_container"):
                    if d[k]:
                        s += f"\t\t\t\t{k} = \"{d[k]}\"\n"
                s += "\t\t\t}\n"
            s += "\t\t}\n"
        if self.props or not (self.triggers or self.effects):
            s += "\t\tproperties = {\n"
            for e, kv in self.props:
                inner = " ".join(f"{k} = \"{v}\"" if k == "image" else f"{k} = {v}" for k, v in kv.items())
                s += f"\t\t\t{e} = {{ {inner} }}\n"
            s += "\t\t}\n"
        if self.triggers:
            s += "\t\ttriggers = {\n" + "".join(f"\t\t\t{k} = {{ {b} }}\n" for k, b in self.triggers) + "\t\t}\n"
        if self.effects:
            s += "\t\teffects = {\n" + "".join(f"\t\t\t{k} = {{ {b} }}\n" for k, b in self.effects) + "\t\t}\n"
        if self.ai_weights:
            s += "\t\tai_weights = {\n" + "".join(f"\t\t\t{k} = {{ {b} }}\n" for k, b in self.ai_weights) + "\t\t}\n"
        return s + "\t}\n"
