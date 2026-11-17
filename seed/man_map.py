"""Generated map of Manchukuo for the Public Security board: one sprite per province, 5 frames = banditry tier."""
import re, glob, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from man_common import ROOT, P, STATES, SNAME

Image.MAX_IMAGE_PIXELS = None
MAP_W = 270                      # target width on the board
PAD = 18                          # map pixels of context around Manchukuo
TIER_COL = [(96, 128, 92), (196, 170, 70), (214, 122, 48), (186, 52, 40), (110, 24, 26)]   # pacified .. lost to the mountains
# Plan map: unsurveyed, survey under way, surveyed, Heavy Industry, Mining, Power and Water, Settlement and Grain
PLAN_COL = [(88, 84, 76), (150, 138, 104), (196, 186, 152), (182, 76, 52), (150, 112, 64), (72, 124, 182), (104, 152, 78)]
PLAN_NAMES = ["Unsurveyed", "Survey under way", "Surveyed", "Heavy Industry Zone", "Mining District", "Power and Water District", "Settlement and Grain Zone"]
PLAN_FLAGS = [None, "MAN_svy_on", "MAN_surveyed", "MAN_zone_hi", "MAN_zone_min", "MAN_zone_pow", "MAN_zone_set"]
_cache = {}

def _data():
    if _cache: return _cache
    im = np.array(Image.open(os.path.join(ROOT, "map/provinces.bmp")).convert("RGB"))
    key = (im[:, :, 0].astype(np.int32) << 16) | (im[:, :, 1].astype(np.int32) << 8) | im[:, :, 2]
    col, typ = {}, {}
    for l in open(os.path.join(ROOT, "map/definition.csv"), encoding="utf-8", errors="ignore"):
        p = l.strip().split(";")
        if len(p) >= 5 and p[0].isdigit():
            col[int(p[0])] = (int(p[1]) << 16) | (int(p[2]) << 8) | int(p[3]); typ[int(p[0])] = p[4]
    prov = {}
    for s in STATES:
        f = [x for x in glob.glob(os.path.join(ROOT, "history/states/*.txt")) if re.match(rf"{s}\s*-", os.path.basename(x))][0]
        t = open(f, encoding="utf-8-sig", errors="ignore").read()
        prov[s] = [int(x) for x in re.search(r"provinces\s*=\s*\{([^}]*)\}", t).group(1).split()]
    masks = {s: np.isin(key, np.array([col[p] for p in prov[s]])) for s in STATES}
    allm = np.zeros_like(masks[STATES[0]])
    for s in STATES: allm |= masks[s]
    ys, xs = np.nonzero(allm)
    x0, x1, y0, y1 = max(xs.min() - PAD, 0), xs.max() + PAD, max(ys.min() - PAD, 0), ys.max() + PAD
    sea_keys = np.array([c for i, c in col.items() if typ[i] in ("sea", "lake")])
    crop = key[y0:y1, x0:x1]
    sea = np.isin(crop, sea_keys)
    sc = MAP_W / (x1 - x0)
    _cache.update(dict(masks={s: m[y0:y1, x0:x1] for s, m in masks.items()}, sea=sea, crop=crop, sc=sc, size=(int((x1 - x0) * sc), int((y1 - y0) * sc))))
    return _cache

def _down(mask, size):
    return Image.fromarray((mask * 255).astype(np.uint8)).resize(size, Image.LANCZOS)

def make_sprites():
    D = _data(); W, H = D["size"]
    out = []
    # backdrop: sea, foreign land, province borders of everything in view
    crop = D["crop"]
    edge = np.zeros(crop.shape, bool)
    edge[1:, :] |= crop[1:, :] != crop[:-1, :]; edge[:, 1:] |= crop[:, 1:] != crop[:, :-1]
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    land = _down(~D["sea"], (W, H))
    bg = Image.new("RGBA", (W, H), (34, 48, 66, 255))                     # sea
    bg.paste(Image.new("RGBA", (W, H), (70, 66, 58, 255)), (0, 0), land)  # foreign land
    frame = Image.new("RGBA", (W + 6, H + 6), (0, 0, 0, 0)); fd = ImageDraw.Draw(frame)
    fd.rounded_rectangle([0, 0, W + 5, H + 5], 6, fill=(125, 112, 88, 255))
    frame.paste(bg, (3, 3))
    tex = "gfx/interface/MAN/MAN_map_bg.png"; frame.save(P(tex)); out.append(("GFX_MAN_map_bg", tex, 1, 0, 0))
    # one sprite per province, cropped to its own box, 5 tier frames, dark outline
    pos = {}
    for s in STATES:
        m = _down(D["masks"][s], (W, H))
        a = np.array(m)
        ys, xs = np.nonzero(a > 40)
        bx0, bx1, by0, by1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        mc = m.crop((bx0, by0, bx1, by1))
        ring = mc.filter(ImageFilter.MaxFilter(3))
        w, h = mc.size
        for prefix, cols in (("map", TIER_COL), ("pmap", PLAN_COL)):
            strip = Image.new("RGBA", (w * len(cols), h), (0, 0, 0, 0))
            for f, c in enumerate(cols):
                fill = Image.new("RGBA", (w, h), c + (255,))
                outline = Image.new("RGBA", (w, h), (22, 20, 18, 255))
                cell = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                cell.paste(outline, (0, 0), ring)
                cell.paste(fill, (0, 0), mc.point(lambda v: 255 if v > 150 else 0))
                strip.paste(cell, (f * w, 0))
            tex = f"gfx/interface/MAN/MAN_{prefix}_{s}.png"; strip.save(P(tex))
            out.append((f"GFX_MAN_{prefix}_{s}", tex, len(cols), bx0 + 3, by0 + 3))
        cy, cx = np.nonzero(a > 150); pos[s] = (int(cx.mean()) + 3, int(cy.mean()) + 3)
    gfx = "".join(f"\tspriteType = {{\n\t\tname = \"{n}\"\n\t\ttexturefile = \"{t}\"\n" + (f"\t\tnoOfFrames = {fr}\n" if fr > 1 else "") + "\t}\n" for n, t, fr, _, _ in out)
    for kname, cols in (("map_key", TIER_COL), ("pmap_key", PLAN_COL)):
        sw = Image.new("RGBA", (14 * len(cols), 14), (0, 0, 0, 0)); d = ImageDraw.Draw(sw)
        for f, c in enumerate(cols): d.rectangle([f * 14, 0, f * 14 + 13, 13], fill=c + (255,), outline=(22, 20, 18, 255))
        tex = f"gfx/interface/MAN/MAN_{kname}.png"; sw.save(P(tex))
        gfx += f"\tspriteType = {{\n\t\tname = \"GFX_MAN_{kname}\"\n\t\ttexturefile = \"{tex}\"\n\t\tnoOfFrames = {len(cols)}\n\t}}\n"
    offs = {n: (ox, oy) for n, _, _, ox, oy in out}
    _cache["offs"] = offs; _cache["centre"] = pos
    return gfx

def gui(props, trig, loc, x0, y0, NL):
    """iconTypes for the board; frames from MAN_f_bt_<state>. Returns (text, height)."""
    D = _data(); W, H = D["size"]
    s_ = f"\t\ticonType = {{\n\t\t\tname = \"MAN_sb_map_bg\"\n\t\t\tposition = {{ x = {x0} y = {y0} }}\n\t\t\tspriteType = \"GFX_MAN_map_bg\"\n\t\t}}\n"
    for s in STATES:
        ox, oy = _cache["offs"][f"GFX_MAN_map_{s}"]
        el = f"MAN_sb_map_{s}"
        s_ += (f"\t\ticonType = {{\n\t\t\tname = \"{el}\"\n\t\t\tposition = {{ x = {x0 + ox} y = {y0 + oy} }}\n\t\t\tspriteType = \"GFX_MAN_map_{s}\"\n"
               f"\t\t\tframe = 1\n\t\t\tpdx_tooltip = \"MAN_SB_MAP_{s}_TT\"\n\t\t}}\n")
        props.append((el, f"MAN_f_bt_{s}"))
        trig.append(f"{el}_visible = {{ {s} = {{ is_owned_by = ROOT }} }}")
        loc(f"MAN_SB_MAP_{s}_TT", f"§C{SNAME[s]}§!" + NL + f"£pol_violence §OBanditry§!: §Y[?MAN_bl_{s}|0]§!")
    # legend to the right of the map
    lx = x0 + W + 16
    names = ["Pacified (under 25)", "Bandit Raids (25+)", "Bandit Country (45+)", "Partisan Base Area (65+)", "Lost to the Mountains (85+)"]
    for i, nm in enumerate(names):
        y = y0 + 8 + i * 22
        s_ += f"\t\ticonType = {{\n\t\t\tname = \"MAN_sb_key_{i}\"\n\t\t\tposition = {{ x = {lx} y = {y + 3} }}\n\t\t\tspriteType = \"GFX_MAN_map_key\"\n\t\t\tframe = {i + 1}\n\t\t}}\n"
        s_ += (f"\t\tinstantTextBoxType = {{\n\t\t\tname = \"MAN_sb_keyt_{i}\"\n\t\t\tposition = {{ x = {lx + 20} y = {y} }}\n\t\t\tfont = \"hoi_16mbs\"\n"
               f"\t\t\ttext = \"MAN_SB_KEY_{i}\"\n\t\t\tmaxWidth = 170\n\t\t\tmaxHeight = 20\n\t\t\tfixedsize = yes\n\t\t}}\n")
        loc(f"MAN_SB_KEY_{i}", nm)
    return s_, H + 6

def frame_effect():
    s = ""
    for st in STATES:
        s += f"set_variable = {{ MAN_f_bt_{st} = 1 }}\n"
        for i, t in enumerate((25, 45, 65, 85), 2):
            s += f"if = {{ limit = {{ check_variable = {{ MAN_bl_{st} > {t - 0.01} }} }} set_variable = {{ MAN_f_bt_{st} = {i} }} }}\n"
        # plan map: later flags in the list win (zone beats surveyed beats survey under way)
        s += f"set_variable = {{ MAN_f_pz_{st} = 1 }}\n"
        for i, fl in enumerate(PLAN_FLAGS[1:], 2):
            s += f"if = {{ limit = {{ {st} = {{ has_state_flag = {fl} }} }} set_variable = {{ MAN_f_pz_{st} = {i} }} }}\n"
    return s

def gui_plan(props, trig, loc, x0, y0, NL):
    """Plan board map: provinces coloured by survey state and designation. Returns (text, height)."""
    D = _data(); W, H = D["size"]
    s_ = f"\t\ticonType = {{\n\t\t\tname = \"MAN_pl_map_bg\"\n\t\t\tposition = {{ x = {x0} y = {y0} }}\n\t\t\tspriteType = \"GFX_MAN_map_bg\"\n\t\t}}\n"
    for s in STATES:
        ox, oy = _cache["offs"][f"GFX_MAN_pmap_{s}"]
        el = f"MAN_pl_map_{s}"
        s_ += (f"\t\ticonType = {{\n\t\t\tname = \"{el}\"\n\t\t\tposition = {{ x = {x0 + ox} y = {y0 + oy} }}\n\t\t\tspriteType = \"GFX_MAN_pmap_{s}\"\n"
               f"\t\t\tframe = 1\n\t\t\tpdx_tooltip = \"MAN_PL_MAP_{s}_TT\"\n\t\t}}\n")
        props.append((el, f"MAN_f_pz_{s}"))
        trig.append(f"{el}_visible = {{ {s} = {{ is_owned_by = ROOT }} }}")
        loc(f"MAN_PL_MAP_{s}_TT", f"§C{SNAME[s]}§!" + NL + f"[ROOT.GetMANProv_{s}]")
    lx = x0 + W + 16
    for i, nm in enumerate(PLAN_NAMES):
        y = y0 + 4 + i * 22
        s_ += f"\t\ticonType = {{\n\t\t\tname = \"MAN_pl_key_{i}\"\n\t\t\tposition = {{ x = {lx} y = {y + 3} }}\n\t\t\tspriteType = \"GFX_MAN_pmap_key\"\n\t\t\tframe = {i + 1}\n\t\t}}\n"
        s_ += (f"\t\tinstantTextBoxType = {{\n\t\t\tname = \"MAN_pl_keyt_{i}\"\n\t\t\tposition = {{ x = {lx + 20} y = {y} }}\n\t\t\tfont = \"hoi_16mbs\"\n"
               f"\t\t\ttext = \"MAN_PL_KEY_{i}\"\n\t\t\tmaxWidth = 180\n\t\t\tmaxHeight = 20\n\t\t\tfixedsize = yes\n\t\t}}\n")
        loc(f"MAN_PL_KEY_{i}", nm)
    return s_, H + 6

if __name__ == "__main__":   # preview
    g = make_sprites()
    D = _data(); W, H = D["size"]
    prev = Image.open(P("gfx/interface/MAN/MAN_map_bg.png")).convert("RGBA")
    import random
    for s in STATES:
        st = Image.open(P(f"gfx/interface/MAN/MAN_map_{s}.png")).convert("RGBA")
        w = st.width // 5; f = random.randint(0, 4)
        ox, oy = _cache["offs"][f"GFX_MAN_map_{s}"]
        prev.alpha_composite(st.crop((f * w, 0, f * w + w, st.height)), (ox, oy))
    prev = prev.resize((prev.width * 2, prev.height * 2), Image.NEAREST)
    prev.save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map_preview.png"))
    print(W, H)
