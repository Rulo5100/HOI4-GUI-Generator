"""Manchukuo: Industrial Development Plan, Hsinking Bureaucracy and Public Security boards.

The reference port of the original one-off generator (seed/man_systems2.py, man_polgui.py, man_map.py,
man_sites.py). It writes the same files with the same bytes:

    interface/MAN_systems.gui / .gfx, common/scripted_guis/MAN_systems_guis.txt,
    common/scripted_localisation/MAN_systems_loc.txt, gfx/interface/MAN/*.png

The loc yml and common/scripted_effects/MAN_systems_effects.txt belong to the wider MAN build, so this
spec only merges its own loc keys into the yml and checks its MAN_ui_refresh block (embed) against the
effects file.

    python -m guigen diff specs/MAN/spec.py --mod "<path to the mod>"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from guigen import (Bar, Card, Dial, Flags, Gauge, Linear, Pips, Project, Solid, StateMap, Thresholds,
                    fit_into, widgets as W)
from guigen.loc import NL
from guigen.pdxscript import indent

import data as D
import text as TX

PNG = "gfx/interface/MAN"
CARD_W, CARD_H, GAP = 96, 270, 2


def build(fs):
    p = Project(fs, "MAN", theme="parchment", loc_mode="merge", files={
        "gui": "interface/MAN_systems.gui",
        "gfx": "interface/MAN_systems.gfx",
        "scripted_gui": "common/scripted_guis/MAN_systems_guis.txt",
        "scripted_loc": "common/scripted_localisation/MAN_systems_loc.txt",
        "loc": "localisation/english/MAN_systems_l_english.yml",
        "frames": None,                      # MAN_ui_refresh lives in MAN_systems_effects.txt (see embed below)
        "png_dir": PNG,
    }, sloc_header="# Manchukuo systems scripted loc\n")
    loc = p.loc

    # ------------------------------------------------------------------ sprites (.gfx order matters)
    p.sprite(Pips("GFX_MAN_pips_strength", f"{PNG}/MAN_pips_strength.png"))
    for nm in D.BARS:
        for sz, (w, h) in (("", (150, 14)), ("_small", (80, 10))):
            p.sprite(Bar(f"GFX_MAN_bar_{nm}{sz}", f"{PNG}/MAN_bar_{nm}{sz}.png", w, h, nm))
    p.sprite(Dial("GFX_MAN_pat_dial", f"{PNG}/MAN_pat_dial.png"))
    p.sprite(Gauge("GFX_MAN_fav_column", f"{PNG}/MAN_fav_column.png"))
    cards = {k: p.sprite(Card(f"GFX_MAN_card_{k}", f"{PNG}/MAN_card_{k}.png", CARD_W, CARD_H, acc)) for k, acc in D.ACCENT.items()}
    p.sprite(Solid("GFX_MAN_card_vacant", f"{PNG}/MAN_card_vacant.png", CARD_W, CARD_H))
    smap = p.statemap(StateMap(fs, D.STATES, "GFX_MAN_", "MAN_", PNG, [("map", D.TIER_COL), ("pmap", D.PLAN_COL)]))

    # ------------------------------------------------------------------ frame variables (MAN_ui_refresh)
    for k, _ in D.QUOTAS:
        p.frame(Linear(f"MAN_f_{k}", f"MAN_pct_{k}"))
    p.frame(Linear("MAN_f_plan", "MAN_plan_pct"))
    p.frame(Linear("MAN_f_pat", "MAN_kw_pat"))
    p.frame(Linear("MAN_f_pat21", "MAN_kw_pat", frames=21))
    for k in D.BROKERS:
        p.frame(Linear(f"MAN_f_fav_{k}", f"MAN_fav_{k}"))
    p.frame(Linear("MAN_f_bavg", "MAN_bandit_avg"))
    for n in D.BANDS:
        p.frame(Linear(f"MAN_f_band{n}", f"MAN_band{n}"))
    for s in D.STATES:
        p.frame(Linear(f"MAN_f_bl_{s}", f"MAN_bl_{s}"))
    for s in D.STATES:
        p.frame(Thresholds(f"MAN_f_bt_{s}", f"MAN_bl_{s}", [25, 45, 65, 85]))
        p.frame(Flags(f"MAN_f_pz_{s}", s, D.PLAN_FLAGS[1:]))
    p.embed("common/scripted_effects/MAN_systems_effects.txt", "MAN_ui_refresh",
            "MAN_ui_refresh = {\n" + indent(p.frames.body(), 1) + "}\n")

    plan_board(p, loc, smap)
    politics_board(p, loc, cards)
    security_board(p, loc, smap)
    scripted_loc(p)
    p.locs.transform(TX.finish)        # the MAN build's colour pass and short bulleted overrides
    return p


# ====================================================================== Plan
def plan_board(p, loc, smap):
    b = p.board("MAN_plan_board")
    W.header(b, "MAN_pl", "GFX_MAN_first_five_year_plan-905539", "MAN_PL_HELP_TT", "[ROOT.GetMANPlanTitle]",
             ["MAN_PL_SUB1", "MAN_PL_SUB2", "[ROOT.GetMANPlanReview]"])
    for i, (key, x, w) in enumerate([("MAN_PL_H_QUOTA", 10, 140), ("MAN_PL_H_PROGRESS", 160, 150), ("MAN_PL_H_DELIV", 322, 110), ("MAN_PL_H_PCT", 438, 52)], 1):
        b.text(f"MAN_pl_h{i}", x, 88, key, w)
    y = 110
    tts = {"steel": "Pig iron, steel ingots and rolled plate from Anshan, Benxihu and the new furnaces.",
           "coal": "Coal from Fushun and the open pits, plus shale oil and synthetic fuel.",
           "power": "Generating capacity from thermal stations and the great dams.",
           "mach": "Machine tools, vehicles, aircraft and munitions.",
           "plan": "The average of the four quota tracks. The Annual Review judges this number."}
    for k, nm in D.QUOTAS + [("plan", "Total plan fulfilment")]:
        K = k.upper()
        src = "MAN_plan_pct" if k == "plan" else f"MAN_pct_{k}"
        W.stat_row(b, y, (f"MAN_pl_n_{k}", f"MAN_PL_N_{K}", "hoi_18mbs" if k == "plan" else "hoi_16mbs", f"MAN_PL_N_{K}_TT"),
                   (f"MAN_pl_bar_{k}", "GFX_MAN_bar_gold", f"MAN_f_{k}"),
                   None if k == "plan" else (f"MAN_pl_v_{k}", f"MAN_PL_V_{K}"), (f"MAN_pl_p_{k}", f"MAN_PL_P_{K}"))
        loc(f"MAN_PL_N_{K}", nm if k != "plan" else "§YTotal plan fulfilment§!")
        loc(f"MAN_PL_N_{K}_TT", tts[k])
        if k != "plan":
            loc(f"MAN_PL_V_{K}", f"[?MAN_q_{k}|0] / [?MAN_qt_{k}|0]")
        loc(f"MAN_PL_P_{K}", f"[?{src}|0]%")
        y += 26 if k != "mach" else 32
    mh = W.state_map(b, smap, "pmap", 10, y + 8, "MAN_pl", lambda s: f"MAN_f_pz_{s}", lambda s: f"MAN_PL_MAP_{s}_TT",
                     lambda s: f"{s} = {{ is_owned_by = ROOT }}", [f"MAN_PL_KEY_{i}" for i in range(len(D.PLAN_NAMES))],
                     legend_top=4, legend_w=180)
    for s in D.STATES:
        loc(f"MAN_PL_MAP_{s}_TT", f"§C{D.SNAME[s]}§!" + NL + f"[ROOT.GetMANProv_{s}]")
    for i, nm in enumerate(D.PLAN_NAMES):
        loc(f"MAN_PL_KEY_{i}", nm)
    y += mh + 10
    y = provinces_panel(b, loc, y + 6)
    b.window.h = y + 6
    loc("MAN_PL_SUB1", "Labour pool §Y[?MAN_labour|0]k§! workers (§G+[?MAN_labour_income|1]k§! a week)")
    loc("MAN_PL_SUB2", "Zones §Y[?MAN_zones_used|0]/[?MAN_zone_cap|0]§!   Projects §Y[?MAN_proj_active|0]/[?MAN_proj_slots|0]§!   Planning efficiency §Y[?MAN_quota_mult|%0]§!")
    loc("MAN_PL_H_QUOTA", "§gQuota track§!")
    loc("MAN_PL_H_PROGRESS", "§gFulfilment§!")
    loc("MAN_PL_H_DELIV", "§gDelivered§!")
    loc("MAN_PL_H_PCT", "§g%§!")
    loc("MAN_PL_HELP_TT", "§YHow the Plan works§!" + NL + "1. §YZone§! provinces (Heavy Industry, Mining, Power, Settlement, Railway) with the map decisions." + NL +
        "2. Start §Yprojects§! in zoned provinces. They cost political power and §Ylabour§!, tie up civilian factories, and add to the quota tracks when finished." + NL +
        "3. Output is scaled by the province's §Ysecurity§! (Public Security tab) and by §Yplanning efficiency§! (Ministry of Industry favour in the Hsinking Bureaucracy tab)." + NL +
        "4. Each plan year the §YAnnual Review§! needs total fulfilment of 20% per year. Passing pleases the Kwantung Army; failing angers it." + NL +
        "5. §YMegaprojects§! unlocked by the focus tree give large, fixed quota deliveries.")


def provinces_panel(b, loc, y):
    """Survey / designate / lift buttons, one row per province."""
    b.text("MAN_pv_h", 10, y, "MAN_PV_H", 300, tooltip="MAN_PV_H_TT")
    loc("MAN_PV_H", "§gProvinces§! (survey and designate here)")
    loc("MAN_PV_H_TT", "§YProvinces§!\\n£white_dot §YSurvey§! a province (§Y" + str(D.SDAYS) + "§! days, one at a time)\\n£white_dot Then §Ydesignate§! it with one of the zone buttons\\n"
        "£white_dot Its §Ysites§! then appear as decisions\\n£white_dot Lifting a designation costs §Y" + str(D.LIFT) + "§! £pol_power; built works stay")
    y += 22
    for s in D.STATES:
        own = f"{s} = {{ is_owned_by = ROOT }}"
        b.text(f"MAN_pv_n_{s}", 10, y + 3, f"[{s}.GetName]", 110, visible=own)
        b.text(f"MAN_pv_s_{s}", 122, y + 3, f"[ROOT.GetMANProv_{s}]", 220, visible=own)
        el = f"MAN_pv_svy_{s}"
        b.button(el, 345, y, "GFX_decision_generic_research", f"MAN_PV_SVY_{s}_TT", scale=0.75,
                 visible=f"{s} = {{ is_owned_by = ROOT NOT = {{ has_state_flag = MAN_surveyed }} NOT = {{ has_state_flag = MAN_svy_on }} }}",
                 enabled=f"NOT = {{ has_country_flag = MAN_surveying }} has_political_power > {D.SCOST_PP - 0.01} check_variable = {{ MAN_labour > {D.SCOST_LAB - 0.01} }} {s} = {{ is_controlled_by = ROOT }}",
                 click=f"{s} = {{ MAN_survey_begin = yes }} MAN_ui_refresh = yes")
        loc(f"MAN_PV_SVY_{s}_TT", f"§YMantetsu Geological Survey§!: §C{D.SNAME[s]}§!\\n£white_dot Cost: §Y{D.SCOST_PP}§! £pol_power, §Y{D.SCOST_LAB}k§! £manpower_texticon §Ylabour§!"
            f"\\n£white_dot Takes §Y{D.SDAYS}§! days; only one survey party at a time\\n£white_dot Expected finds: §Y{D.FOUND[s]}§!\\n£white_dot §G30%§! chance of a rich find: §G+15§! of the main resource"
            "\\n£white_dot Surveyed provinces gain §G+5%§! local resources and can be designated")
        for i, z in enumerate(D.ZNAME_S):
            if s not in D.ZONES[z]:
                continue
            el = f"MAN_pv_z{z}_{s}"
            b.button(el, 345 + i * 28, y, D.ZICON[z], f"MAN_PV_Z_{z}_{s}_TT", scale=0.75,
                     visible=f"has_country_flag = MAN_zone_unl_{z} {s} = {{ is_owned_by = ROOT has_state_flag = MAN_surveyed NOT = {{ has_state_flag = MAN_zoned }} }}",
                     enabled=f"has_political_power > {D.ZCOST - 0.01} check_variable = {{ MAN_zones_used < MAN_zone_cap }} {s} = {{ is_controlled_by = ROOT }}",
                     click=f"add_political_power = -{D.ZCOST} add_to_variable = {{ MAN_zones_used = 1 }} {s} = {{ MAN_zone_apply_{z} = yes }} MAN_ui_refresh = yes")
            sites = [st[2] for st in D.SITES if st[0] == s and st[1] == z]
            extra = {"pow": ["Thermal Power Station", "Transmission Grid"], "set": ["Pioneer Colony", "Soybean Export Season"], "hi": ["Production Run for the Empire"]}.get(z, [])
            opens = ", ".join(sites + extra) or "no special sites"
            loc(f"MAN_PV_Z_{z}_{s}_TT", f"§YDesignate {D.ZNAME_S[z]}§!: §C{D.SNAME[s]}§!\\n£white_dot Cost: §Y{D.ZCOST}§! £pol_power and one £state §Yzone§! (§Y[?MAN_zones_used|0]§! of §Y[?MAN_zone_cap|0]§! used)"
                f"\\n£white_dot Opens: §Y{opens}§!\\n£white_dot A province holds one designation")
        el = f"MAN_pv_lift_{s}"
        b.button(el, 460, y, "GFX_decision_generic_break_treaty", f"MAN_PV_LIFT_{s}_TT", scale=0.75,
                 visible=f"{s} = {{ is_owned_by = ROOT has_state_flag = MAN_zoned }}",
                 enabled=f"has_political_power > {D.LIFT - 0.01} {s} = {{ NOT = {{ has_state_flag = MAN_busy }} }}",
                 click=f"add_political_power = -{D.LIFT} subtract_from_variable = {{ MAN_zones_used = 1 }} {s} = {{ MAN_zone_lift = yes }} MAN_ui_refresh = yes")
        loc(f"MAN_PV_LIFT_{s}_TT", f"§YLift the designation§!: §C{D.SNAME[s]}§!\\n£white_dot Cost: §Y{D.LIFT}§! £pol_power\\n£white_dot Frees a £state §Yzone§!; built works stay\\n£white_dot Not while a project is under way here")
        y += 26
    return y


# ====================================================================== Hsinking Bureaucracy
def politics_board(p, loc, cards):
    b = p.board("MAN_politics_board")
    b.text("MAN_pb_title", 196, 4, "MAN_PB_TITLE", 300, 22, "hoi_18mbs", tooltip="MAN_PB_HELP_TT")
    W.frame_bar(b, "MAN_pb_dial", 6, 4, "GFX_MAN_pat_dial", "MAN_f_pat21", tooltip="MAN_PB_PAT_TT")
    b.text("MAN_pb_pat_l", 196, 32, "MAN_PB_PAT_L", 300, tooltip="MAN_PB_PAT_TT")
    b.text("MAN_pb_pat_v", 196, 52, "MAN_PB_PAT_V", 120, 30, "hoi_24header")
    b.text("MAN_pb_pat_s", 196, 82, "[ROOT.GetMANPatience]", 300, 40)
    y0 = 112
    for i, k in enumerate(D.BROKERS):
        K = k.upper()
        x0 = 6 + i * (CARD_W + GAP)
        inst = D.BK[k][0]
        held = f"check_variable = {{ MAN_h_{k} > 0.5 }}"
        emb = p.gfx_index.open(D.EMBLEM[k])
        es, ex, ey = fit_into(emb, cards[k].ring_centre, 52)
        W.card(b, "MAN_pb", k, x0, y0, f"GFX_MAN_card_{k}", f"MAN_PB_I_{K}", f"[ROOT.GetMANHolder_{k}]", f"[ROOT.GetMANReq_{k}]",
               title_tt=f"MAN_PB_I_{K}_TT", emblem=(D.EMBLEM[k], es, ex, ey),
               gauge=("GFX_MAN_fav_column", f"MAN_f_fav_{k}", f"MAN_PB_G_{K}_TT"), vacant="GFX_MAN_card_vacant",
               value=f"MAN_PB_V_{K}", value_label="MAN_PB_FAVOUR",
               button=("GFX_button_94x31", f"MAN_PB_COURT_{K}_TT", "MAN_PB_COURT", 0.85,
                       f"has_political_power > {D.COURT_COST[k] - 0.01:.2f} NOT = {{ has_country_flag = MAN_court_cd_{k} }} {held}",
                       f"MAN_court_{k} = yes"),
               held=held, vacant_cond=f"check_variable = {{ MAN_h_{k} < 0.5 }}", w=CARD_W, h=CARD_H)
        loc(f"MAN_PB_I_{K}", f"§L{inst}§!")
        loc(f"MAN_PB_V_{K}", f"[?MAN_fav_{k}|0]")
        loc(f"MAN_PB_G_{K}_TT", f"£influence_texticon §L{inst}§! favour: §Y[?MAN_fav_{k}|0]§!" + NL + "£white_dot Drifts back to its §Lresting level§! over time" +
            NL + "£white_dot §G60§! or more: the holder leaves for Tokyo as a §Gpatron§!" + NL + "£white_dot §R30§! or less: he leaves as an §Renemy§!")
        riv = D.BK[k][1]
        loc(f"MAN_PB_COURT_{K}_TT", f"§YCourt the {inst}§!" + NL + f"£white_dot Cost: §Y{D.COURT_COST[k]}§! £pol_power" + NL + f"£white_dot £influence_texticon §L{inst}§! favour: §G+12§!" +
            (NL + f"£white_dot £influence_texticon §L{D.BK[riv][0]}§! favour: §R-6§!" if riv else "") + NL + "£white_dot Can be repeated every §Y60§! days")
    loc("MAN_PB_FAVOUR", "§gfavour§!")
    b.window.h = y0 + CARD_H + 36
    loc("MAN_PB_TITLE", "The Hsinking Bureaucracy")
    loc("MAN_PB_COURT", "Court")
    loc("MAN_PB_PAT_L", "Kwantung Army patience")
    loc("MAN_PB_PAT_V", "[?MAN_kw_pat|0]")
    loc("MAN_PB_PAT_TT", "§YKwantung Army patience§!" + NL + "Above 50 it raises stability and war support, below 50 it lowers them. It drifts with Kwantung Army Staff favour and falls while banditry stays above 30. Plan reviews and requests move it sharply. Below §R15§! the Kwantung Army intervenes in the government.")
    loc("MAN_PB_HELP_TT", "§YThe Hsinking Bureaucracy§!" + NL + "Favour with each power centre (0 to 100, neutral at 50) feeds §YThe Hsinking Bureaucracy§! spirit:" + NL +
        "Kwantung Army Staff: organisation, and stronger punitive sweeps." + NL + "General Affairs Board: political power gain." + NL +
        "Ministry of Industry: construction speed and planning efficiency." + NL + "Mangyo: factory output." + NL + "Mantetsu: infrastructure construction speed." + NL +
        "Favour slowly drifts back towards 40. When a man leaves for Tokyo, high favour makes him a lasting §Gpatron§!, low favour a lasting §Renemy§!.")
    for k in D.BROKERS:
        loc(f"MAN_PB_I_{k.upper()}_TT", f"§Y{D.BK[k][0]}§!" + NL + D.TTI[k] + NL + "Favour: §Y[?MAN_fav_" + k + "|0]§! (neutral 50)")


# ====================================================================== Public Security
def security_board(p, loc, smap):
    b = p.board("MAN_security_board")
    W.header(b, "MAN_sb", "GFX_focus_MAN_sec_security_plan", "MAN_SB_HELP_TT", "MAN_SB_TITLE")
    b.text("MAN_sb_avg_l", 62, 28, "MAN_SB_AVG_L", 170)
    W.frame_bar(b, "MAN_sb_avg_bar", 235, 31, "GFX_MAN_bar_red", "MAN_f_bavg")
    b.text("MAN_sb_avg_v", 392, 28, "MAN_SB_AVG_V", 40)
    b.text("MAN_sb_avg_s", 62, 47, "[ROOT.GetMANSecurity]", 430)
    y = 74
    b.text("MAN_sb_rh_l", 10, y, "MAN_SB_RH_L", 215)
    b.text("MAN_sb_rh_r", 235, y, "MAN_SB_RH_R", 200, tooltip="MAN_SB_RH_TT")
    loc("MAN_SB_RH_L", "§gRoute Armies§! (the armed resistance)")
    loc("MAN_SB_RH_R", "§gStrength§! (each figure = 10)")
    loc("MAN_SB_RH_TT", "§ORoute Army§! strength runs from §Y0§! (destroyed) to §Y100§!. It is not banditry: a strong army raises §Obanditry§! in its home provinces every week.")
    y += 20
    for n, (bn, leader, homes, ex) in D.BANDS.items():
        b.text(f"MAN_sb_bn_{n}", 10, y, f"MAN_SB_BN_{n}", 215, tooltip=f"MAN_SB_BN_{n}_TT")
        b.text(f"MAN_sb_bs_{n}", 10, y + 18, f"[ROOT.GetMANBandSt_{n}]", 225)
        W.frame_bar(b, f"MAN_sb_bbar_{n}", 235, y + 3, "GFX_MAN_pips_strength", f"MAN_f_band{n}", tooltip=f"MAN_SB_BN_{n}_TT")
        b.text(f"MAN_sb_bv_{n}", 392, y + 1, f"MAN_SB_BV_{n}", 40)
        loc(f"MAN_SB_BN_{n}", f"§Y{bn}§! ({leader})")
        loc(f"MAN_SB_BV_{n}", f"§Y[?MAN_band{n}|0]§!")
        homes_s = " and ".join(D.SNAME[s] for s in homes)
        loc(f"MAN_SB_BN_{n}_TT", f"§Y{bn} of the Northeast Anti-Japanese United Army§!" + NL + f"Commander: {leader}. Operates in {homes_s}, where its strength drives banditry up every week." + NL +
            "Strength recovers slowly through recruitment. Sweeps and Collective Hamlets in its home provinces wear it down; Surrender Campaigns peel men away." +
            (NL + "When broken it may slip across the Amur into the Soviet Union, and come back if the Soviets go to war with us." if ex else ""))
        y += 40
    mh = W.state_map(b, smap, "map", 10, y + 4, "MAN_sb", lambda s: f"MAN_f_bt_{s}", lambda s: f"MAN_SB_MAP_{s}_TT",
                     lambda s: f"{s} = {{ is_owned_by = ROOT }}", [f"MAN_SB_KEY_{i}" for i in range(5)], legend_top=8, legend_w=170)
    for s in D.STATES:
        loc(f"MAN_SB_MAP_{s}_TT", f"§C{D.SNAME[s]}§!" + NL + f"£pol_violence §OBanditry§!: §Y[?MAN_bl_{s}|0]§!")
    for i, nm in enumerate(["Pacified (under 25)", "Bandit Raids (25+)", "Bandit Country (45+)", "Partisan Base Area (65+)", "Lost to the Mountains (85+)"]):
        loc(f"MAN_SB_KEY_{i}", nm)
    y += mh + 10
    y = operations_panel(b, loc, y + 2)
    b.window.h = y + 6
    loc("MAN_SB_TITLE", "Public Security in Manchukuo")
    loc("MAN_SB_AVG_L", "Average banditry")
    loc("MAN_SB_AVG_V", "[?MAN_bandit_avg|0]")
    loc("MAN_SB_GRID_H", "§gBanditry by province§!")
    loc("MAN_SB_HELP_TT", "§YPublic Security§!" + NL + "Every province has a banditry level from 0 to 100. Above 25, 45, 65 and 85 it imposes growing penalties to resources, construction and building slots there." +
        NL + "Banditry also scales down the Plan's project output in that province and drains Kwantung Army patience." +
        NL + "It rises from local grievances and the Route Armies, and falls with garrisons, blockhouses, Collective Hamlets, informant networks and punitive sweeps.")


def operations_panel(b, loc, y):
    """Garrison / sweep / hamlets / blockhouses / informants, one row per province."""
    b.text("MAN_sbp_res", 10, y, "MAN_SBP_RES", 480, tooltip="MAN_SBP_RES_TT")
    loc("MAN_SBP_RES", "§gAvailable:§! £pol_power §Y[?political_power|0]§!  £command_power §Y[?command_power|0]§!  £manpower_texticon §Y[?manpower_k|0]k§!  labour §Y[?MAN_labour|0]k§!  §gGarrisons§! §Y[?MAN_gar_n|0]/[?MAN_gar_cap|0]§!")
    loc("MAN_SBP_RES_TT", "What security operations are paid with. An order whose cost you cannot meet does nothing when clicked: hover it to see the cost and what you have.")
    y += 22
    b.text("MAN_sbp_h", 10, y, "MAN_SBP_H", 100, tooltip="MAN_SBP_H_TT")
    b.text("MAN_sbp_hb", 112, y, "MAN_SBP_HB", 110, tooltip="MAN_SBP_HB_TT")
    b.text("MAN_sbp_ho", 372, y, "MAN_SBP_HO", 140, tooltip="MAN_SBP_H_TT")
    loc("MAN_SBP_H", "§gProvince§!")
    loc("MAN_SBP_HB", "§gBanditry§! (0 to 100)")
    loc("MAN_SBP_HO", "§gOperations§!")
    loc("MAN_SBP_HB_TT", "£pol_violence §Obanditry§! in the province: penalties start at §Y25§! and worsen at §Y45§!, §Y65§! and §Y85§!. It cuts the Plan's output there.")
    loc("MAN_SBP_H_TT", "§OSecurity operations§!\\n£white_dot §OPolice Garrison§!: a year of police and railway guards, paid in £pol_power and manpower\\n£white_dot §OPunitive Sweep§!: paid in £command_power, repeatable every §Y60§! days\\n£white_dot §OCollective Hamlets§!, §OBlockhouse Lines§! and §OInformant Networks§! unlock through the focus tree"
        "\\n£white_dot Works under way finish on their own; hover a button for costs and effects")
    y += 22
    for s in D.STATES:
        own = f"{s} = {{ is_owned_by = ROOT }}"
        b.text(f"MAN_sb_sn_{s}", 10, y + 3, f"[{s}.GetName]", 100)
        W.frame_bar(b, f"MAN_sb_sbar_{s}", 112, y + 8, "GFX_MAN_bar_red_small", f"MAN_f_bl_{s}")
        b.text(f"MAN_sb_sv_{s}", 196, y + 3, f"MAN_SB_SV_{s}", 30)
        b.text(f"MAN_sb_st_{s}", 228, y + 3, f"[ROOT.GetMANSecProv_{s}]", 140)
        for el in (f"MAN_sb_sn_{s}", f"MAN_sb_sbar_{s}", f"MAN_sb_sv_{s}", f"MAN_sb_st_{s}"):
            b.visible(el, own)
        loc(f"MAN_SB_SV_{s}", f"[?MAN_bl_{s}|0]")
        for i, (key, nm, icon, days, pp, lab, cp, gate, cd) in enumerate(D.SEC):
            el = f"MAN_sb_{key}_{s}"
            vis = f"{s} = {{ is_owned_by = ROOT"
            if key == "sw":
                vis += " check_variable = { MAN_bandit > 9.99 } NOT = { has_state_flag = MAN_sw_on }"
            else:
                vis += f" NOT = {{ has_state_flag = {D.SEC_DONE_FLAG[key]} }}" + (f" NOT = {{ has_state_flag = MAN_{key}_on }}" if days else "")
            vis += " }"
            if gate:
                vis += f" has_completed_focus = {gate}"
            en = f"has_political_power > {pp - 0.01}" + (f" check_variable = {{ MAN_labour > {lab - 0.01} }}" if lab else "") + (f" command_power > {cp - 0.01}" if cp else "")
            if key == "gar":
                en += f" has_manpower > {D.GAR_MP - 1} check_variable = {{ MAN_gar_n < MAN_gar_cap }}"
            en += f" {s} = {{ is_controlled_by = ROOT" + (" NOT = { has_state_flag = MAN_sw_cd }" if key == "sw" else "") + " }"
            b.button(el, 372 + i * 28, y, icon, f"MAN_SB_{key.upper()}_{s}_TT", scale=0.75, visible=vis, enabled=en,
                     click=f"{s} = {{ MAN_{key}_begin = yes }} MAN_sec_refresh = yes MAN_ui_refresh = yes")
            cost = f"§Y{pp}§! £pol_power" + (f", §Y{lab}k§! £manpower_texticon §Ylabour§!" if lab else "") + (f", §Y{cp}§! £command_power" if cp else "")
            if key == "gar":
                cost += f", §Y{D.GAR_MP // 1000}k§! £manpower_texticon manpower"
            have = "£pol_power §Y[?political_power|0]§!" + (", £manpower_texticon §Y[?MAN_labour|0]k§! labour" if lab else "") + \
                   (", £command_power §Y[?command_power|0]§!" if cp else "") + (", £manpower_texticon §Y[?manpower_k|0]k§! manpower" if key == "gar" else "")
            cost += f"\\n£white_dot You have: {have}"
            loc(f"MAN_SB_{key.upper()}_{s}_TT", f"§O{nm}§!: §C{D.SNAME[s]}§!\\n£white_dot Cost: {cost}\\n£white_dot {TX.op_effect(key, D.GAR_DAYS)}")
        y += 26
    return y


# ====================================================================== scripted loc
def scripted_loc(p):
    DT = p.defined_text
    DT("GetMANPlanTitle", [
        ("check_variable = { MAN_plan_stage < 0.5 }", "MAN_PLT_0", "§YPreparatory Survey§!: the Plan has not yet been proclaimed"),
        ("has_country_flag = MAN_second_fyp_complete", "MAN_PLT_DONE2", "§GThe Second Plan is concluded§!"),
        ("has_country_flag = MAN_first_fyp_complete check_variable = { MAN_plan_stage < 2.5 }", "MAN_PLT_DONE1", "§GThe First Plan is concluded§!: the planners draft its successor"),
        ("check_variable = { MAN_plan_stage = 1 }", "MAN_PLT_1", "§YFirst Five-Year Plan§!: year [?MAN_plan_year|0] of 5"),
        ("check_variable = { MAN_plan_stage = 2 }", "MAN_PLT_2", "§YRevised First Five-Year Plan§!: year [?MAN_plan_year|0] of 5"),
        ("check_variable = { MAN_plan_stage = 3 }", "MAN_PLT_3", "§YSecond Five-Year Plan§!: year [?MAN_plan_year|0] of 5"),
        ("", "MAN_PLT_4", "§YWartime Emergency Plan§!: year [?MAN_plan_year|0] of 5"),
    ])
    DT("GetMANPlanReview", [
        ("has_country_flag = MAN_review_running has_country_flag = MAN_review_lock", "MAN_PLR_LOCK", "Annual review needs §Y[?MAN_review_need|0]%§! total fulfilment. The books close late in the plan year."),
        ("has_country_flag = MAN_review_running", "MAN_PLR_OPEN", "Annual review needs §Y[?MAN_review_need|0]%§!: §Gthe books are open§!, reach it to pass early."),
        ("", "MAN_PLR_NONE", "§gNo annual review in progress.§!"),
    ])
    for k in D.BROKERS:
        cases = []
        if k in D.VACANT:
            cases.append((f"check_variable = {{ MAN_h_{k} < 0.5 }}", f"MAN_HOLD_{k}_0", f"§g{D.VACANT[k]}§!"))
        for i, nm in enumerate(D.HOLDERS[k], 1):
            last = i == len(D.HOLDERS[k])
            cases.append(("" if last else f"check_variable = {{ MAN_h_{k} = {i} }}", f"MAN_HOLD_{k}_{i}", nm))
        DT(f"GetMANHolder_{k}", cases)
        DT(f"GetMANReq_{k}", [
            (f"has_country_flag = MAN_req_{k}_a", f"MAN_REQL_{k}_a", f"§YRequest:§! {D.REQ_NAMES[k][0]}"),
            (f"has_country_flag = MAN_req_{k}_b", f"MAN_REQL_{k}_b", f"§YRequest:§! {D.REQ_NAMES[k][1]}"),
            (f"check_variable = {{ MAN_h_{k} < 0.5 }}", f"MAN_REQL_{k}_x", ""),
            ("", f"MAN_REQL_{k}_n", "§gNo standing request§!"),
        ])
    DT("GetMANPatience", [
        ("check_variable = { MAN_kw_pat < 15 }", "MAN_PAT_0", "§RThe Kwantung Army is preparing to take matters into its own hands§!"),
        ("check_variable = { MAN_kw_pat < 35 }", "MAN_PAT_1", "§OThe staff in Hsinking is losing patience with the government§!"),
        ("check_variable = { MAN_kw_pat < 65 }", "MAN_PAT_2", "§YThe Kwantung Army is watching closely§!"),
        ("check_variable = { MAN_kw_pat < 85 }", "MAN_PAT_3", "§GThe Kwantung Army trusts Hsinking to deliver§!"),
        ("", "MAN_PAT_4", "§GManchukuo is a trusted partner of the Empire§!"),
    ])
    DT("GetMANSecurity", [
        ("check_variable = { MAN_bandit_avg < 15 }", "MAN_SEC_0", "§GThe countryside is pacified§!"),
        ("check_variable = { MAN_bandit_avg < 30 }", "MAN_SEC_1", "§YScattered bands still raid isolated villages and rail lines§!"),
        ("check_variable = { MAN_bandit_avg < 50 }", "MAN_SEC_2", "§OWhole districts answer to the guerrillas after dark§!"),
        ("", "MAN_SEC_3", "§RThe mountains belong to the United Army§!"),
    ])
    for n in D.BANDS:
        DT(f"GetMANBandSt_{n}", [
            (f"has_country_flag = MAN_band{n}_dead", f"MAN_BST_{n}_dead", "§GDestroyed§!"),
            (f"has_country_flag = MAN_band{n}_exile", f"MAN_BST_{n}_exile", "§YRetreated into the Soviet Union§!"),
            (f"check_variable = {{ MAN_band{n} > 69.99 }}", f"MAN_BST_{n}_3", "§RStrong and recruiting in the villages§!"),
            (f"check_variable = {{ MAN_band{n} > 39.99 }}", f"MAN_BST_{n}_2", "§OActive, raiding mines and railways§!"),
            ("", f"MAN_BST_{n}_1", "§YHunted, short of food and men§!"),
        ])
    for st in D.STATES:
        cases = [(f"{st} = {{ has_state_flag = MAN_zone_{z} }}", f"MAN_PVS_{z}", f"§Y{D.ZNAME_S[z]}§!") for z in D.ZNAME_S]
        cases += [(f"{st} = {{ has_state_flag = MAN_svy_on }}", "MAN_PVS_SVY", "§YSurvey under way§!"),
                  (f"{st} = {{ has_state_flag = MAN_surveyed }}", "MAN_PVS_DONE", "§GSurveyed§!, not designated"),
                  ("", "MAN_PVS_NONE", "§gUnsurveyed§!")]
        DT(f"GetMANProv_{st}", cases)
    DT("GetMANSurveyProv", [(f"{st} = {{ has_state_flag = MAN_svy_on }}", f"MAN_SVYP_{st}", f"§C{D.SNAME[st]}§!") for st in D.STATES]
       + [("", "MAN_SVYP_NONE", "the field")])
    for st in D.STATES:
        DT(f"GetMANSecProv_{st}", [
            (f"{st} = {{ has_state_flag = MAN_sw_on }}", "MAN_SPS_SW", "§OSweep under way§!"),
            (f"{st} = {{ has_state_flag = MAN_hm_on }}", "MAN_SPS_HM", "§OBuilding hamlets§!"),
            (f"{st} = {{ has_state_flag = MAN_bh_on }}", "MAN_SPS_BH", "§OBuilding blockhouses§!"),
            (f"{st} = {{ has_state_flag = MAN_grievance }}", "MAN_SPS_GR", "§RGrievance§!"),
            (f"{st} = {{ has_state_flag = MAN_hamlets has_state_flag = MAN_blockhouses }}", "MAN_SPS_HB", "§GHamlets, blockhouses§!"),
            (f"{st} = {{ has_state_flag = MAN_hamlets }}", "MAN_SPS_H", "§GHamlets§!"),
            (f"{st} = {{ has_state_flag = MAN_blockhouses }}", "MAN_SPS_B", "§GBlockhouses§!"),
            (f"{st} = {{ has_state_flag = MAN_garrisoned }}", "MAN_SPS_G", "§gGarrisoned§!"),
            ("", "MAN_SPS_NONE", ""),
        ])
