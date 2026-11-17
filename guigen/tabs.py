"""Tab bars and collapsible sections, driven by one variable each.

    tabs = TabSet(p, board, "XYZ_tab", [("eco", "XYZ_TAB_ECO"), ("pol", "XYZ_TAB_POL")], x=10, y=90, content_y=120, content_h=300)
    with tabs.section("eco"):
        board.text("XYZ_eco_title", 10, 0, "XYZ_ECO_TITLE", 300)     # coordinates relative to the section
    with tabs.section("pol"):
        ...

How it works in game:
* every tab has two buttons at the same place: the idle one (visible when the tab is not selected,
  click sets the variable to the tab's index) and the selected one (visible when it is);
* every section is a child containerWindowType whose `_visible` trigger checks the variable, so the
  whole section shows or hides with one trigger;
* the variable lives in the board's scope (the player country for decision_category and
  player_context), and starts at 0, so the first tab is open by default.

Tab sections share the space below the bar: give the board the height of the tallest section.
"""
from contextlib import contextmanager

from .elements import Window
from .sprites import Tabs as TabSprite


def _tab_sprites(p, w, h):
    idle, on = p.gfx_name(f"tab_{w}x{h}"), p.gfx_name(f"tab_{w}x{h}_on")
    if idle not in p.sprites:
        p.sprite(TabSprite(idle, p.png(f"tab_{w}x{h}"), w, h, selected=False))
        p.sprite(TabSprite(on, p.png(f"tab_{w}x{h}_on"), w, h, selected=True))
    return idle, on


class TabSet:
    def __init__(self, project, board, var, tabs, x, y, content_y, content_h, button_w=110, button_h=24, gap=4,
                 font="hoi_16mbs", refresh=None, tooltips=None):
        """tabs: [(key, label loc key)]. refresh: extra effect run on every tab click (e.g. "XYZ_ui_refresh = yes")."""
        self.p, self.b, self.var = project, board, var
        self.keys = [k for k, _ in tabs]
        self.content_y, self.content_h = content_y, content_h
        idle, on = _tab_sprites(project, button_w, button_h)
        for i, (k, label) in enumerate(tabs):
            bx = x + i * (button_w + gap)
            sel = f"check_variable = {{ {var} = {i} }}"
            tt = (tooltips or {}).get(k)
            board.button(f"{var}_btn_{k}", bx, y, idle, tt, label, font=font, visible=f"NOT = {{ {sel} }}",
                         click=f"set_variable = {{ {var} = {i} }}" + (f" {refresh}" if refresh else ""))
            board.button(f"{var}_btn_{k}_on", bx, y, on, tt, label, font=font, clicksound=None, visible=sel)

    def index(self, key):
        return self.keys.index(key)

    @contextmanager
    def section(self, key):
        i = self.index(key)
        win = Window(f"{self.var}_sec_{key}", 0, self.content_y, "100%%", self.content_h)
        self.b.push(win)
        self.b.visible(win.name, f"check_variable = {{ {self.var} = {i} }}")
        try:
            yield win
        finally:
            self.b.pop()


class Toggle:
    """A collapsible section: one button flips `var` between 0 (open) and 1 (closed)."""

    def __init__(self, project, board, var, x, y, sprite, label, content_y, content_h, tooltip=None, start_open=True):
        self.p, self.b, self.var = project, board, var
        self.content_y, self.content_h = content_y, content_h
        self.open_cond = f"check_variable = {{ {var} = {0 if start_open else 1} }}"
        flip = (f"if = {{ limit = {{ check_variable = {{ {var} = 1 }} }} set_variable = {{ {var} = 0 }} }} "
                f"else = {{ set_variable = {{ {var} = 1 }} }}")
        board.button(f"{var}_toggle", x, y, sprite, tooltip, label, click=flip)

    @contextmanager
    def section(self):
        win = Window(f"{self.var}_sec", 0, self.content_y, "100%%", self.content_h)
        self.b.push(win)
        self.b.visible(win.name, self.open_cond)
        try:
            yield win
        finally:
            self.b.pop()
