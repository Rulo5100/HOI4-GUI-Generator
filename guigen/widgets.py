"""Reusable composite widgets. Each takes a Board, adds elements + wiring, and returns the new y (or a
height). Their output order is fixed (a regression test pins it): changing it
changes the generated files.
"""
from .layout import Columns


def header(board, pfx, emblem, help_tt, title, subs=(), x=62, w=430, emblem_scale=0.5, title_font="hoi_18mbs",
           emblem_xy=(6, 2), title_y=4, sub_y=27, sub_step=18):
    """Emblem button (with the help tooltip) + title + sub lines. Returns the y below the last sub line."""
    board.button(f"{pfx}_emblem", emblem_xy[0], emblem_xy[1], emblem, help_tt, scale=emblem_scale)
    board.text(f"{pfx}_title", x, title_y, title, w, 22, title_font)
    y = sub_y
    for i, s in enumerate(subs, 1):
        board.text(f"{pfx}_sub{i}", x, y, s, w)
        y += sub_step
    return y


def column_headers(board, names_texts, y, cols, font="hoi_16mbs"):
    """names_texts: [(element name, loc key)], one per column of `cols` (a layout.Columns)."""
    for i, (nm, key) in enumerate(names_texts):
        board.text(nm, cols[i], y, key, cols.width(i), 20, font)


def frame_bar(board, name, x, y, sprite, frame_var, tooltip=None, visible=None):
    """An iconType driven by a frame variable (bars, pips, dials, gauges)."""
    return board.icon(name, x, y, sprite, frame=1, frame_var=frame_var, tooltip=tooltip, visible=visible)


def stat_row(board, y, label, bar, value=None, pct=None, cols=None, bar_dy=3):
    """Label | frame bar | value | percent on one row.

    label: (name, loc key, font, tooltip) / bar: (name, sprite, frame var) / value, pct: (name, loc key) or None.
    cols: layout.Columns with 4 columns (default: label 145, bar 150, value 110, percent 52).
    """
    cols = cols or Columns.at([10, 160, 322, 438], [145, 150, 110, 52])
    ln, lk, lf, ltt = label
    board.text(ln, cols[0], y, lk, cols.width(0), 20, lf, tooltip=ltt)
    frame_bar(board, bar[0], cols[1], y + bar_dy, bar[1], bar[2])
    if value:
        board.text(value[0], cols[2], y, value[1], cols.width(2))
    if pct:
        board.text(pct[0], cols[3], y, pct[1], cols.width(3))


def state_map(board, smap, layer, x0, y0, pfx, frame_var, tooltip, visible, legend=(), legend_top=8,
              legend_w=170, legend_step=22):
    """A StateMap layer on the board: backdrop, one icon per state, legend to the right.

    frame_var / tooltip / visible: functions of the state id returning the variable, the tooltip loc key
    and the visible trigger. legend: loc keys for the legend lines (one per frame).
    Returns the height used.
    """
    W, H = smap.size
    board.icon(f"{pfx}_map_bg", x0, y0, smap.bg_sprite, frame=None)
    for s in smap.states:
        ox, oy = smap.offset(smap.sprite_name(layer, s))
        el = f"{pfx}_map_{s}"
        board.icon(el, x0 + ox, y0 + oy, smap.sprite_name(layer, s), tooltip=tooltip(s), frame_var=frame_var(s))
        board.visible(el, visible(s))
    lx = x0 + W + 16
    for i, key in enumerate(legend):
        y = y0 + legend_top + i * legend_step
        board.icon(f"{pfx}_key_{i}", lx, y + 3, smap.key_sprite(layer), frame=i + 1)
        board.text(f"{pfx}_keyt_{i}", lx + 20, y, key, legend_w, 20, fmt=None)
    return H + 6


def card(board, pfx, k, x0, y0, card_sprite, title, holder, request, title_tt=None,
         emblem=None, gauge=None, vacant=None, value=None, value_label=None, button=None,
         held=None, vacant_cond=None, w=96, h=270):
    """Institution card: background, emblem in the ring, vertical gauge, vacancy overlay, texts, a button.

    emblem: (sprite, scale, dx, dy)        gauge: (sprite, frame var, tooltip)
    value: loc key (big number)            value_label: loc key under it
    button: (sprite, tooltip, text, scale, enabled, effect)
    held / vacant_cond: triggers that show the held parts / the vacancy overlay.
    Element names: {pfx}_card_{k}, _emb_, _col_, _vac_, _i_, _h_, _v_, _vl_, _r_, _court_.
    """
    n = lambda part: f"{pfx}_{part}_{k}"
    board.icon(n("card"), x0, y0, card_sprite, tooltip=title_tt)
    if emblem:
        sp, sc, dx, dy = emblem
        board.icon(n("emb"), x0 + dx, y0 + dy, sp, scale=sc, tooltip=title_tt)
    if gauge:
        board.icon(n("col"), x0 + 14, y0 + 140, gauge[0], tooltip=gauge[2], frame_var=gauge[1])
    if vacant:
        board.icon(n("vac"), x0, y0, vacant)
    board.text(n("i"), x0 + 3, y0 + 68, title, w - 6, 34, "hoi_16mbs", "centre", tooltip=title_tt)
    board.text(n("h"), x0 + 3, y0 + 102, holder, w - 6, 36, "hoi_16mbs", "centre")
    if value:
        board.text(n("v"), x0 + 42, y0 + 168, value, 50, 30, "hoi_24header")
    if value_label:
        board.text(n("vl"), x0 + 42, y0 + 196, value_label, 50, 20, "hoi_16mbs")
    board.text(n("r"), x0 + 3, y0 + 226, request, w - 6, 40, "hoi_16mbs", "centre")
    if button:
        sp, tt, txt, sc, en, eff = button
        board.button(n("court"), x0 + 8, y0 + h + 4, sp, tt, txt, scale=sc)
    if held:
        for part in ("col", "v", "vl", "court", "r"):
            if board.element(n(part)):
                board.visible(n(part), held)
    if vacant and vacant_cond:
        board.visible(n("vac"), vacant_cond)
    if button:
        if button[4]:
            board.enabled(n("court"), button[4])
        if button[5]:
            board.click(n("court"), button[5])


def list_rows(board, items, y, row_h, row):
    """Static rows: row(board, item, y) for each item, advancing by row_h. Returns the y after the list."""
    for it in items:
        row(board, it, y)
        y += row_h
    return y
