"""Interactive in-game windows and controls.

PopupWindow: a moveable window (like a big mod's economy screen) that an opener button toggles.

    win = PopupWindow(p, "XYZ_econ", "XYZ_ECON_TITLE", 720, 520, opener="top_bar", opener_xy=(560, 4),
                      opener_sprite="GFX_decision_generic_economy", opener_tooltip="XYZ_ECON_OPEN_TT")
    b = win.board                    # add content below win.top (the title bar)
    tabs = TabSet(p, b, "XYZ_econ_tab", [...], x=12, y=win.top, content_y=win.top + 30, content_h=440)

What gets generated:
* the window board: context player_context (shown over the map), `visible = { has_country_flag = <flag> }`,
  `moveable = yes`, centred on screen, a 9-slice panel background (corneredTileSpriteType), a title
  and a close button (clears the flag);
* the opener board: a button attached to a vanilla panel (`parent_window_token`, e.g. top_bar,
  politics_tab, decision_tab, trade_tab) that toggles the flag and refreshes the charts on open.
  opener="decision_category" makes the opener a decision-category board instead (add
  `scripted_gui = <name>_opener` to your category); opener=None makes no opener.

Controls: stepper (- value +), switch (on / off from a variable).
"""
from .chartsprites import CloseButton, Panel, TextButton
from .sprites import Sprite


class Switch(Sprite):
    """Pill on / off switch: frame 1 off, frame 2 on."""

    def __init__(self, name, texture, w=34, h=18):
        super().__init__(name, texture, 2)
        self.w, self.h = w, h

    def render(self, t):
        from .chartsprites import _aa
        from PIL import Image
        w, h = self.w, self.h
        img = Image.new("RGBA", (w * 2, h), (0, 0, 0, 0))
        for f in range(2):
            def draw(d, k, f=f):
                W, H = w * k, h * k
                d.rounded_rectangle([k, k, W - k, H - k], H // 2, fill=(t.colour("good") if f else t.shadow) + (255,),
                                    outline=t.outline, width=k)
                r = H / 2 - 3 * k
                cx = W - H / 2 if f else H / 2
                d.ellipse([cx - r, H / 2 - r, cx + r, H / 2 + r], fill=t.preview_text + (255,))
            img.paste(_aa((w, h), draw), (f * w, 0))
        return img


class PopupWindow:
    def __init__(self, p, name, title, w, h, opener="top_bar", opener_xy=(0, 0), opener_sprite=None, opener_text=None,
                 opener_tooltip=None, flag=None, moveable=True, close=True, centre=True, x=0, y=0, dirty=None,
                 refresh_on_open=True, title_font="hoi_20bs", panel_border=24):
        self.p, self.name, self.w, self.h = p, name, w, h
        self.flag = flag or f"{name}_open"
        self.top = 40
        panel = p.sprites.get(p.gfx_name("window_panel")) or p.sprite(Panel(p.gfx_name("window_panel"), p.png("window_panel"), 96, panel_border))
        extra = [("background", f'{{ name = "Background" quadTextureSprite = "{panel.name}" }}')]
        if moveable:
            extra.append(("moveable", "yes"))
        if centre:
            extra.append(("orientation", "center"))
            x, y = -w // 2, -h // 2
        self.board = b = p.board(name, context="player_context", width=w, height=h, x=x, y=y,
                                 visible=f"has_country_flag = {self.flag}", dirty=dirty)
        b.window.extra = extra
        b.meta = {"popup": True}
        b.text(f"{name}_title", 16, 9, title, w - 70, 24, title_font)
        if close:
            cb = p.sprites.get(p.gfx_name("close")) or p.sprite(CloseButton(p.gfx_name("close"), p.png("close")))
            b.button(f"{name}_close", w - 34, 9, cb.name, click=f"clr_country_flag = {self.flag}")
        self.opener = None
        if opener:
            refresh = f" {p.refresh_effect} = yes" if refresh_on_open else ""
            p.needs_refresh = p.needs_refresh or refresh_on_open
            toggle = (f"if = {{ limit = {{ has_country_flag = {self.flag} }} clr_country_flag = {self.flag} }} "
                      f"else = {{ set_country_flag = {self.flag}{refresh} }}")
            if opener == "decision_category":
                ob = p.board(f"{name}_opener", context="decision_category", width=200, height=40)
            else:
                ob = p.board(f"{name}_opener", context="player_context", parent_token=opener, width=200, height=40,
                             x=opener_xy[0], y=opener_xy[1])
            if not opener_sprite:
                tb = p.sprites.get(p.gfx_name("button")) or p.sprite(TextButton(p.gfx_name("button"), p.png("button")))
                opener_sprite = tb.name
                opener_text = opener_text or title
            ob.button(f"{name}_open", 0, 0, opener_sprite, opener_tooltip, opener_text, click=toggle)
            sz = p.sprite_size(opener_sprite) or (110, 26)
            ob.window.w, ob.window.h = sz[0] + 4, sz[1] + 4
            self.opener = ob


def stepper(b, p, name, x, y, var, step=1, lo=0, hi=100, label=None, label_w=120, value_fmt="0", refresh=True, cost=None):
    """[-] value [+] buttons that change `var` by `step` within lo..hi. cost: an effect added to each click."""
    tb = p.sprites.get(p.gfx_name("btn_small")) or p.sprite(TextButton(p.gfx_name("btn_small"), p.png("btn_small"), 26, 22))
    N = name.upper()
    x0 = x
    if label:
        b.text(f"{name}_l", x, y + 2, f"{N}_L", label_w, 18)
        p.loc(f"{N}_L", label)
        x0 += label_w
    tail = (f" {p.refresh_effect} = yes" if refresh else "") + (f" {cost}" if cost else "")
    p.needs_refresh = p.needs_refresh or refresh
    b.button(f"{name}_dec", x0, y, tb.name, f"{N}_DEC_TT", f"{N}_MINUS",
             click=f"subtract_from_variable = {{ {var} = {step} }} clamp_variable = {{ var = {var} min = {lo} max = {hi} }}{tail}",
             enabled=f"check_variable = {{ {var} > {lo} }}")
    b.text(f"{name}_v", x0 + 28, y + 2, f"{N}_V", 54, 18, fmt="centre")
    b.button(f"{name}_inc", x0 + 84, y, tb.name, f"{N}_INC_TT", f"{N}_PLUS",
             click=f"add_to_variable = {{ {var} = {step} }} clamp_variable = {{ var = {var} min = {lo} max = {hi} }}{tail}",
             enabled=f"check_variable = {{ {var} < {hi} }}")
    p.loc(f"{N}_MINUS", "-")
    p.loc(f"{N}_PLUS", "+")
    p.loc(f"{N}_V", f"§Y[?{var}|{value_fmt}]§!")
    p.loc(f"{N}_DEC_TT", f"Lower by §Y{step}§! (minimum §Y{lo}§!)")
    p.loc(f"{N}_INC_TT", f"Raise by §Y{step}§! (maximum §Y{hi}§!)")


def switch(b, p, name, x, y, var, label=None, label_w=160, tooltip=None, refresh=True):
    """An on / off switch for a 0 / 1 variable."""
    sw = p.sprites.get(p.gfx_name("switch")) or p.sprite(Switch(p.gfx_name("switch"), p.png("switch")))
    N = name.upper()
    tail = f" {p.refresh_effect} = yes" if refresh else ""
    p.needs_refresh = p.needs_refresh or refresh
    from .frames import Linear
    p.frame(Linear(f"{name}_f", var, 2, 0, 1))
    b.button(f"{name}_sw", x, y, sw.name, tooltip,
             click=f"if = {{ limit = {{ check_variable = {{ {var} > 0.5 }} }} set_variable = {{ {var} = 0 }} }} else = {{ set_variable = {{ {var} = 1 }} }}{tail}")
    b.prop(f"{name}_sw", frame=f"{name}_f")
    if label:
        b.text(f"{name}_l", x + 42, y, f"{N}_L", label_w, 18, tooltip=tooltip)
        p.loc(f"{N}_L", label)
