"""Hsinking Bureaucracy board: patience dial + five institution cards with vertical favour columns."""
import math, os
from PIL import Image, ImageDraw
from man_common import P, BROKERS

CARD_W, CARD_H, GAP = 96, 270, 2
GAUGE_W, GAUGE_H = 22, 84
DIAL_W, DIAL_H = 180, 100
ACCENT = {"kw": (170, 52, 42), "gab": (70, 110, 175), "ind": (195, 152, 60), "mgy": (55, 140, 128), "smr": (150, 40, 62)}
EMBLEM = {"kw": "GFX_MAN_an_army_with_a_state-905635", "gab": "GFX_focus_MAN_pol_gab_state", "ind": "GFX_focus_MAN_eco_kishi_arrives",
          "mgy": "GFX_focus_MAN_eco_found_mangyo", "smr": "GFX_MAN_manetsu_research_department-905555"}

RING_C = (CARD_W // 2, 36)   # centre of the emblem ring on the card
RING_FIT = 52                 # visible emblem size inside the ring

def _emblem_place(sprite):
    """scale and top-left offset that centre the sprite's visible content on the ring."""
    import glob, re
    tex = None
    for f in glob.glob(P("interface/*.gfx")):
        m = re.search(r'name\s*=\s*"' + re.escape(sprite) + r'"\s*\n\s*texture[fF]ile\s*=\s*"([^"]+)"', open(f, encoding="utf-8-sig", errors="ignore").read())
        if m: tex = m.group(1); break
    im = Image.open(P(tex)).convert("RGBA")
    a = im.split()[3].point(lambda v: 255 if v > 60 else 0)
    x0, y0, x1, y1 = a.getbbox()
    s = round(RING_FIT / max(x1 - x0, y1 - y0), 3)
    cx, cy = (x0 + x1) / 2 * s, (y0 + y1) / 2 * s
    return s, int(round(RING_C[0] - cx)), int(round(RING_C[1] - cy))

def _save(img, name):
    p = P(f"gfx/interface/MAN/{name}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)
    return f"gfx/interface/MAN/{name}.png"

def _lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def make_sprites():
    out = []
    # patience dial: 21 frames (0, 5, ... 100)
    img = Image.new("RGBA", (DIAL_W * 21, DIAL_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bands = [(0, 15, (175, 45, 40)), (15, 35, (205, 115, 40)), (35, 65, (170, 160, 120)), (65, 85, (80, 160, 75)), (85, 100, (215, 175, 60))]
    for f in range(21):
        ox = f * DIAL_W; cx, cy, r = ox + DIAL_W // 2, DIAL_H - 10, 78
        d.rounded_rectangle([ox + 1, 1, ox + DIAL_W - 2, DIAL_H - 2], 10, fill=(30, 28, 24, 235), outline=(125, 112, 88, 255), width=2)
        for lo, hi, col in bands:   # angle 180 (left, 0) to 360 (right, 100) in PIL's clockwise-from-east convention
            d.arc([cx - r, cy - r, cx + r, cy + r], 180 + lo * 1.8, 180 + hi * 1.8, fill=col + (255,), width=14)
        for v in (15, 35, 65, 85):
            a = math.radians(180 + v * 1.8)
            d.line([cx + (r - 16) * math.cos(a), cy + (r - 16) * math.sin(a), cx + (r + 1) * math.cos(a), cy + (r + 1) * math.sin(a)], fill=(20, 18, 16, 255), width=2)
        a = math.radians(180 + f * 5 * 1.8)
        tip = (cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a))
        d.line([cx, cy, tip[0], tip[1]], fill=(235, 228, 205, 255), width=4)
        d.line([cx, cy, tip[0], tip[1]], fill=(150, 30, 25, 255), width=2)
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=(60, 55, 48, 255), outline=(200, 185, 150, 255), width=2)
    out.append(("GFX_MAN_pat_dial", _save(img, "MAN_pat_dial"), 21))
    # vertical favour column: 11 frames, ticks at 30 (enemy) and 60 (patron)
    img = Image.new("RGBA", (GAUGE_W * 11, GAUGE_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for f in range(11):
        ox = f * GAUGE_W
        d.rectangle([ox, 0, ox + GAUGE_W - 1, GAUGE_H - 1], fill=(26, 24, 21, 240), outline=(125, 112, 88, 255))
        v = f / 10
        col = (175, 50, 42) if v <= 0.3 else _lerp((205, 160, 55), (85, 165, 80), min(1, (v - 0.3) / 0.3)) if v < 0.6 else (85, 170, 82)
        fh = int((GAUGE_H - 4) * v)
        if fh > 0:
            d.rectangle([ox + 3, GAUGE_H - 2 - fh, ox + GAUGE_W - 4, GAUGE_H - 3], fill=col + (255,))
            d.line([ox + 3, GAUGE_H - 2 - fh, ox + GAUGE_W - 4, GAUGE_H - 2 - fh], fill=_lerp(col, (255, 255, 255), 0.35) + (255,))
        for t, tc in ((0.3, (215, 70, 60)), (0.6, (110, 205, 100))):
            y = GAUGE_H - 2 - int((GAUGE_H - 4) * t)
            d.line([ox, y, ox + 5, y], fill=tc + (255,), width=2); d.line([ox + GAUGE_W - 6, y, ox + GAUGE_W - 1, y], fill=tc + (255,), width=2)
    out.append(("GFX_MAN_fav_column", _save(img, "MAN_fav_column"), 11))
    # cards
    for k, acc in ACCENT.items():
        img = Image.new("RGBA", (CARD_W, CARD_H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for yy in range(CARD_H):
            c = _lerp((44, 40, 34), (26, 24, 21), yy / CARD_H)
            d.line([2, yy, CARD_W - 3, yy], fill=c + (240,))
        d.rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=(125, 112, 88, 255), width=2)
        d.rectangle([2, 2, CARD_W - 3, 7], fill=acc + (255,))
        d.ellipse([CARD_W // 2 - 29, 9, CARD_W // 2 + 29, 63], fill=_lerp(acc, (20, 18, 16), 0.65) + (255,), outline=acc + (255,), width=2)
        out.append((f"GFX_MAN_card_{k}", _save(img, f"MAN_card_{k}"), 1))
    img = Image.new("RGBA", (CARD_W, CARD_H), (12, 11, 10, 165))
    out.append(("GFX_MAN_card_vacant", _save(img, "MAN_card_vacant"), 1))
    return "".join(f"\tspriteType = {{\n\t\tname = \"{n}\"\n\t\ttexturefile = \"{t}\"\n" + (f"\t\tnoOfFrames = {fr}\n" if fr > 1 else "") + "\t}\n" for n, t, fr in out)

def icon(name, x, y, sprite, scale=None, tt=None):
    s = f"\t\ticonType = {{\n\t\t\tname = \"{name}\"\n\t\t\tposition = {{ x = {x} y = {y} }}\n\t\t\tspriteType = \"{sprite}\"\n\t\t\tframe = 1\n"
    if scale: s += f"\t\t\tscale = {scale}\n"
    if tt: s += f"\t\t\tpdx_tooltip = \"{tt}\"\n"
    return s + "\t\t}\n"

def board(T, B, props, trig, eff, loc, BK, COURT_COST, NL):
    b = T("MAN_pb_title", 196, 4, "MAN_PB_TITLE", 300, 22, "hoi_18mbs", tt="MAN_PB_HELP_TT")
    b += icon("MAN_pb_dial", 6, 4, "GFX_MAN_pat_dial", tt="MAN_PB_PAT_TT")
    props.append(("MAN_pb_dial", "MAN_f_pat21"))
    b += T("MAN_pb_pat_l", 196, 32, "MAN_PB_PAT_L", 300, tt="MAN_PB_PAT_TT")
    b += T("MAN_pb_pat_v", 196, 52, "MAN_PB_PAT_V", 120, 30, "hoi_24header")
    b += T("MAN_pb_pat_s", 196, 82, "[ROOT.GetMANPatience]", 300, 40)
    y0 = 112
    for i, k in enumerate(BROKERS):
        x0 = 6 + i * (CARD_W + GAP)
        inst = BK[k][0]
        vac = f"check_variable = {{ MAN_h_{k} < 0.5 }}"
        held = f"check_variable = {{ MAN_h_{k} > 0.5 }}"
        b += icon(f"MAN_pb_card_{k}", x0, y0, f"GFX_MAN_card_{k}", tt=f"MAN_PB_I_{k.upper()}_TT")
        es, ex, ey = _emblem_place(EMBLEM[k])
        b += icon(f"MAN_pb_emb_{k}", x0 + ex, y0 + ey, EMBLEM[k], scale=es, tt=f"MAN_PB_I_{k.upper()}_TT")
        b += icon(f"MAN_pb_col_{k}", x0 + 14, y0 + 140, "GFX_MAN_fav_column", tt=f"MAN_PB_G_{k.upper()}_TT")
        props.append((f"MAN_pb_col_{k}", f"MAN_f_fav_{k}"))
        b += icon(f"MAN_pb_vac_{k}", x0, y0, "GFX_MAN_card_vacant")
        b += T(f"MAN_pb_i_{k}", x0 + 3, y0 + 68, f"MAN_PB_I_{k.upper()}", CARD_W - 6, 34, "hoi_16mbs", "centre", tt=f"MAN_PB_I_{k.upper()}_TT")
        b += T(f"MAN_pb_h_{k}", x0 + 3, y0 + 102, f"[ROOT.GetMANHolder_{k}]", CARD_W - 6, 36, "hoi_16mbs", "centre")
        b += T(f"MAN_pb_v_{k}", x0 + 42, y0 + 168, f"MAN_PB_V_{k.upper()}", 50, 30, "hoi_24header")
        b += T(f"MAN_pb_vl_{k}", x0 + 42, y0 + 196, "MAN_PB_FAVOUR", 50, 20, "hoi_16mbs")
        b += T(f"MAN_pb_r_{k}", x0 + 3, y0 + 226, f"[ROOT.GetMANReq_{k}]", CARD_W - 6, 40, "hoi_16mbs", "centre")
        b += B(f"MAN_pb_court_{k}", x0 + 8, y0 + CARD_H + 4, "GFX_button_94x31", f"MAN_PB_COURT_{k.upper()}_TT", "MAN_PB_COURT", scale=0.85)
        for el in (f"MAN_pb_col_{k}", f"MAN_pb_v_{k}", f"MAN_pb_vl_{k}", f"MAN_pb_court_{k}", f"MAN_pb_r_{k}"):
            trig.append(f"{el}_visible = {{ {held} }}")
        trig.append(f"MAN_pb_vac_{k}_visible = {{ {vac} }}")
        trig.append(f"MAN_pb_court_{k}_click_enabled = {{ has_political_power > {COURT_COST[k] - 0.01:.2f} NOT = {{ has_country_flag = MAN_court_cd_{k} }} {held} }}")
        eff.append(f"MAN_pb_court_{k}_click = {{ MAN_court_{k} = yes }}")
        loc(f"MAN_PB_I_{k.upper()}", f"§L{inst}§!")
        loc(f"MAN_PB_V_{k.upper()}", f"[?MAN_fav_{k}|0]")
        loc(f"MAN_PB_G_{k.upper()}_TT", f"£influence_texticon §L{inst}§! favour: §Y[?MAN_fav_{k}|0]§!" + NL + "£white_dot Drifts back to its §Lresting level§! over time" +
            NL + "£white_dot §G60§! or more: the holder leaves for Tokyo as a §Gpatron§!" + NL + "£white_dot §R30§! or less: he leaves as an §Renemy§!")
        riv = BK[k][1]
        loc(f"MAN_PB_COURT_{k.upper()}_TT", f"§YCourt the {inst}§!" + NL + f"£white_dot Cost: §Y{COURT_COST[k]}§! £pol_power" + NL + f"£white_dot £influence_texticon §L{inst}§! favour: §G+12§!" +
            (NL + f"£white_dot £influence_texticon §L{BK[riv][0]}§! favour: §R-6§!" if riv else "") + NL + "£white_dot Can be repeated every §Y60§! days")
    loc("MAN_PB_FAVOUR", "§gfavour§!")
    return b, y0 + CARD_H + 36
