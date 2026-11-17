"""MAN text passes that the original build ran over the whole loc (man_build.recolour and
man_ui_text.apply), limited to what touches the board keys."""
import re

import data as D

B = "\\n£white_dot "
POL_T = [v[0] for v in D.BK.values()] + D.POL_T_EXTRA
PLACES = list(D.SNAME.values())


def recolour(v):
    """§Y economy is the default; politics terms become §L, security §O, places §C."""
    for terms, c in ((POL_T, "L"), (D.SEC_T, "O"), (PLACES, "C")):
        for t in sorted(terms, key=len, reverse=True):
            v = v.replace(f"§Y{t}§!", f"§{c}{t}§!")
    return re.sub(r"§R(grievance)§!", r"§O\1§!", v)


def court(v):
    parts = v.split("\\n")
    body = [re.sub(r"^(Kwantung Army Staff|General Affairs Board|Ministry of Industry|Mangyo|Mantetsu) favour", r"£influence_texticon §L\1§! favour", p) for p in parts[1:]]
    return parts[0] + "".join(B + p for p in body)


def short_text(k, v):
    """Short, bulleted overrides for the boards (man_ui_text.apply)."""
    if k in D.UI_OVR:
        return D.UI_OVR[k]
    if k.startswith("MAN_PB_COURT_") and k.endswith("_TT") and "£white_dot" not in v:
        return court(v)
    if k.startswith("MAN_PL_N_") and k.endswith("_TT"):
        return D.QI[k[9:-3]] + "\\n" + v
    if k.startswith("MAN_PB_I_") and k.endswith("_TT"):
        return v.replace("\\nFavour: ", B + "£influence_texticon Favour: ").replace(" (neutral 50)", " (neutral §Y50§!)")
    return v


def finish(k, v):
    return short_text(k, recolour(v))


def op_effect(key, gar_days):
    """What each security operation does (tooltip body)."""
    return {
        "gar": f"For §Y{gar_days}§! days: §G-0.08§! £pol_violence §Obanditry§! growth a week from police posts and railway guards\\n£white_dot Renew it when it runs out"
               "\\n£white_dot Garrisons in use: §Y[?MAN_gar_n|0]§! of §Y[?MAN_gar_cap|0]§! (the §OPublic Security§! focuses allow more)",
        "sw": "After §Y30§! days: £pol_violence §Obanditry§! §G-10§! to §G-20§! (more with §LKwantung Army Staff§! favour, ×1.5 with an §OInformant Network§!), local £nato_unit_irregular_infantry_icon_small §ORoute Army§! §G-6§!"
              "\\n£white_dot §R30%§! chance of reprisals: a §Ogrievance§! for 120 days (§R+0.15§! banditry growth a week here)\\n£white_dot Repeatable every §Y60§! days",
        "hm": "After §Y120§! days: £pol_violence §Obanditry§! §G-15§!, §G-0.25§! a week for good, local £nato_unit_irregular_infantry_icon_small §ORoute Army§! §G-10§!\\n£white_dot §R-5%§! local resources, §R-10%§! recruitable population, §R-2%§! stability",
        "bh": "After §Y60§! days: §G-0.10§! £pol_violence §Obanditry§! growth a week for good",
        "inf": "For §Y180§! days: §G-0.15§! £pol_violence §Obanditry§! growth a week, and §OPunitive Sweeps§! here are §G50%§! stronger",
    }[key]
