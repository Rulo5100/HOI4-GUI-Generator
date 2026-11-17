"""Manchukuo advisors, rebuilt: every advisor has a unique trait; many hook into the Plan / Bureaucracy / Security / Racial Harmony systems
through on_add / on_remove (variables read by MAN_systems_effects), others are flat national bonuses."""
import re, os
from man_common import *

L = []
def loc(k, v): L.append((k, v))

INST = {"kw": "Kwantung Army Staff", "gab": "General Affairs Board", "ind": "Ministry of Industry", "mgy": "Mangyo", "smr": "Mantetsu"}

# knob: (variable, value, tooltip text). Reversed on removal.
def K_dt(k, n): return (f"MAN_dt_{k}", n, f"Resting level of §L{INST[k]}§! favour: §G+{n}§!")
def K_fav(k, n): return (f"MAN_fav_{k}", n, f"£influence_texticon §L{INST[k]}§! favour: §G+{n}§!", False)   # one-off, not reversed
def K_bg(x): return ("MAN_bgrow_g", x, f"£pol_violence §OBanditry growth§! in every province: {'§G' if x < 0 else '§R+'}{x}§! a week")
def K_drain(x): return ("MAN_band_drain", x, f"Strength of every £nato_unit_irregular_infantry_icon_small §ORoute Army§!: §G-{x}§! a week")
def K_pd(x): return ("MAN_pat_drift", x, f"£army_experience §LKwantung Army patience§!: {'§G+' if x > 0 else '§R'}{x}§! every week")
def K_inc(x): return ("MAN_labour_income", x, f"£manpower_texticon §YLabour income§!: §G+{x}k§! workers a week")
def K_qf(x): return ("MAN_quota_focus", x, f"£prod_eff §YPlanning efficiency§!: §G+{int(x * 100)}%§!")
def K_slot(n): return ("MAN_proj_slots", n, f"£civ_factory §YConcurrent plan projects§!: §G+{n}§!")
def K_qb(k, x): return (f"MAN_qb_{k}", x, f"§Y{dict(QUOTAS)[k]}§! quota points from plan projects: §G+{int(x * 100)}%§!")
def K_rail(n): return ("MAN_rail_built", n, f"Counts as §Y{n}§! {'line' if n == 1 else 'lines'} of new track for §LMantetsu§!'s requests", False)
def K_flag(f, text): return ("FLAG", f, text)
def K_levy(x): return ("MAN_levy_g", x, f"£manpower_texticon §YLabour levy pressure§!: §R+{x}§! a week")

# seat requirement for the Bureaucracy brokers, shown in the hire tooltip
SEAT = {
    ("ind", 1): "§YKishi Nobusuke§! holds the §LMinistry of Industry§! seat in the Bureaucracy (he arrives with the focus §YKishi Comes to Hsinking§!)",
    ("mgy", 1): "§YAyukawa Yoshisuke§! holds the §LMangyo§! seat in the Bureaucracy (he arrives with the focus §YFound Mangyo§!, or in December 1937)",
    ("mgy", 2): "§YTakasaki Tatsunosuke§! holds the §LMangyo§! seat in the Bureaucracy (he succeeds Ayukawa when Ayukawa leaves Hsinking)",
    ("smr", 1): "§YMatsuoka Yosuke§! still holds the §LMantetsu§! seat in the Bureaucracy",
    ("gab", 1): "§YHoshino Naoki§! still holds the §LGeneral Affairs Board§! seat in the Bureaucracy",
}
def HOLDER(k, i):
    key = f"MAN_tt_adv_seat_{k}_{i}"
    loc(key, SEAT[(k, i)])
    return f"custom_trigger_tooltip = {{ tooltip = {key} check_variable = {{ MAN_h_{k} = {i} }} }}"
def K_rev(n): return ("MAN_review_relief", n, f"£industry_texticon The §YAnnual Plan Review§! needs §G-{n}%§! total fulfilment")

# id, name (None = keep loc key), portrait small (None = keep), slot, cost, trait key, trait name, trait modifiers, available, knobs, ai factor, ledger
ADV = [
    # ---------------- political: the Plan
    ("MAN_nobusuke_kishi", "Kishi Nobusuke", "GFX_idea_generic_political_advisor_asia_1", "political_advisor", 150, "MAN_adv_reform_bureaucrat", "Architect of the Plan",
     {"production_speed_industrial_complex_factor": 0.10}, HOLDER("ind", 1), [K_qf(0.05), K_slot(1)], 3, None),
    ("MAN_yoshisuke_ayukawa", "Ayukawa Yoshisuke", "GFX_idea_generic_political_advisor_asia_2", "political_advisor", 150, "MAN_adv_nissan_capital", "Nissan Capital",
     {"industrial_capacity_factory": 0.04, "production_factory_efficiency_gain_factor": 0.10}, HOLDER("mgy", 1), [K_inc(0.5), K_dt("mgy", 10)], 3, None),
    ("MAN_songgotu_zhanshan", "Takasaki Tatsunosuke", None, "political_advisor", 125, "MAN_adv_mangyo_engineer", "Engineer-President of Mangyo",
     {"production_factory_max_efficiency_factor": 0.05, "production_speed_arms_factory_factor": 0.05}, HOLDER("mgy", 2), [K_qb("mach", 0.15)], 2, None),
    ("MAN_matsuoka_yosuke", "Matsuoka Yosuke", "GFX_idea_generic_political_advisor_asia_3", "political_advisor", 125, "MAN_adv_mantetsu_president", "President of Mantetsu",
     {"production_speed_infrastructure_factor": 0.15, "production_speed_rail_way_factor": 0.15}, HOLDER("smr", 1), [K_dt("smr", 10), K_rail(2)], 2, None),
    ("MAN_ding_jianxiu", None, None, "political_advisor", 100, "MAN_adv_labour_recruiter", "Master of the Labour Gangs",
     {"production_speed_buildings_factor": 0.03}, "", [K_inc(0.75), K_qb("coal", 0.10), K_levy(0.6)], 2, None),
    # ---------------- political: the Bureaucracy and the Kwantung Army
    ("MAN_naoki_hoshino", "Hoshino Naoki", None, "political_advisor", 150, "MAN_adv_gab_director", "Director of General Affairs",
     {"political_power_factor": 0.10, "production_speed_buildings_factor": 0.05}, HOLDER("gab", 1), [K_dt("gab", 10), K_fav("gab", 10)], 3, None),
    ("MAN_bao_manbo", None, None, "political_advisor", 100, "MAN_adv_envoy_tokyo", "Envoy to Tokyo",
     {"political_power_factor": 0.05}, "", [K_pd(0.03), K_fav("kw", 5)], 2, None),
    ("MAN_masahiko_amakasu", None, None, "political_advisor", 125, "MAN_adv_manei_chief", "The Kempeitai's Film Director",
     {"political_power_gain": 0.10, "war_support_weekly": 0.001, "power_balance_weekly": 0.002},
     "OR = { has_completed_focus = MAN_establish_the_manchuko_film_association date > 1939.11.1 }", [K_bg(-0.01)], 2, None),
    # ---------------- political: Racial Harmony and the countryside
    ("MAN_zhang_jinghui", None, None, "political_advisor", 150, "MAN_adv_old_bandit_premier", "Premier of the Old School",
     {"stability_factor": 0.08, "power_balance_weekly": -0.002}, "", [K_bg(-0.02)], 3, None),
    ("MAN_ruan_zhenduo", None, None, "political_advisor", 125, "MAN_cofounder_of_concordia", "Co-Founder of the Concordia",
     {"stability_weekly": 0.001, "power_balance_weekly": -0.004}, "has_completed_focus = MAN_restoring_control_to_the_concord_society", [K_dt("gab", 5), K_pd(-0.02)], 2, None),
    ("MAN_yoshiko_kawashima", None, None, "political_advisor", 100, "MAN_adv_eastern_jewel", "The Eastern Jewel",
     {"civilian_intel_factor": 0.15, "stability_factor": -0.03}, "date < 1941.1.1", [K_bg(-0.02)], 1, None),
    ("MAN_Hajime_Satomi", None, None, "political_advisor", 125, "MAN_adv_opium_king", "The Opium King",
     {"political_power_gain": 0.20, "stability_weekly": -0.002}, "", [K_bg(0.01), K_flag("MAN_adv_satomi", "The §YJehol Opium Monopoly§! pays an extra §G+1500§! £civ_factory_output §YEconomic Capacity Surplus§!")], 1, None),
    # ---------------- political: flat national bonuses
    ("MAN_zhang_shiyi", None, None, "political_advisor", 100, "MAN_adv_fengtian_elder", "Elder of the Fengtian Clique",
     {"stability_weekly": 0.0015, "political_power_factor": -0.05}, "", [], 2, None),
    ("MAN_sun_qichang", None, None, "political_advisor", 125, "MAN_adv_finance_minister", "Minister of Finance",
     {"consumer_goods_expected_value": -0.03, "political_power_factor": 0.03}, "", [], 2, None),
    ("MAN_xie_jieshi", None, None, "political_advisor", 100, "MAN_adv_foreign_minister", "Foreign Minister of the New State",
     {"autonomy_gain": 0.5, "improve_relations_maintain_cost_factor": -0.25, "political_power_factor": 0.05}, "", [K_pd(0.02), K_rev(5)], 2, None),
    ("MAN_Chu_Kudo", None, None, "political_advisor", 75, "MAN_adv_imperial_bodyguard", "The Emperor's Bodyguard",
     {"stability_factor": 0.05, "political_advisor_cost_factor": -0.15}, "", [], 2, None),
    ("MAN_li_shaogeng", None, None, "political_advisor", 100, "MAN_adv_cer_veteran", "Railwayman of the Chinese Eastern",
     {"production_speed_rail_way_factor": 0.25, "production_speed_supply_node_factor": 0.25, "attrition": -0.05}, "", [K_rail(1), K_dt("smr", 5), K_bg(-0.01)], 2, None),
    # ---------------- army chief
    ("MAN_yu_zhishan", "Yu Zhishan", "gfx/leaders/MAN/Portrait_Man_Yu_Zhishan1.dds", "army_chief", 125, "MAN_adv_defence_minister", "Minister of Military Affairs",
     {"training_time_army_factor": -0.10, "recruitable_population_factor": 0.02, "experience_gain_army": 0.05}, "", [K_drain(0.03)], 3, "army"),
    ("MAN_aisin_gioro_xiqia", None, None, "army_chief", 125, "MAN_adv_bannerman_general", "Bannerman General",
     {"army_morale_factor": 0.05, "army_defence_factor": 0.05}, "", [], 2, "army"),
    ("MAN_guan_xingde", None, None, "army_chief", 100, "MAN_adv_winter_campaigner", "Winter Campaigner",
     {"winter_attrition_factor": -0.25, "attrition": -0.05}, "", [], 2, "army"),
    # ---------------- high command
    ("MAN_yonimitsu_kasahara", None, None, "high_command", 100, "MAN_adv_pacification_staff", "Pacification Staff Officer",
     {"army_org_regain": 0.05}, "", [K_drain(0.05)], 2, "army"),
    ("MAN_ding_chao", None, None, "high_command", 100, "MAN_adv_turncoat_general", "The Turncoat General",
     {"army_defence_factor": 0.05}, "", [K_drain(0.02), K_bg(-0.01)], 1, "army"),
    ("MAN_kyoiji_tomonaga", None, None, "high_command", 100, "MAN_adv_xingan_cavalry", "Inspector of the Xing'an Cavalry",
     {"cavalry_attack_factor": 0.10, "cavalry_defence_factor": 0.10}, "", [], 2, "army"),
    ("MAN_hesehn_tiemei", None, None, "high_command", 100, "MAN_adv_rail_logistics", "Railway Logistician",
     {"supply_consumption_factor": -0.05, "river_crossing_factor": 0.10}, "", [], 2, "army"),
    # ---------------- air and navy
    ("MAN_nakajima_kesago", None, None, "air_chief", 100, "MAN_adv_army_air_liaison", "Kwantung Air Liaison",
     {"air_cas_efficiency": 0.10, "air_ace_generation_chance_factor": 0.10}, "", [], 2, "air"),
    ("MAN_yin_zuoqian", None, None, "navy_chief", 100, "MAN_adv_sungari_flotilla", "Commander of the Sungari Flotilla",
     {"navy_org_factor": 0.05, "naval_detection": 0.10}, "", [], 1, "navy"),
    # ---------------- theorists
    ("MAN_pujie", None, None, "theorist", 100, "MAN_adv_imperial_guard", "Officer of the Imperial Guard",
     {"land_doctrine_cost_factor": -0.07, "stability_factor": 0.02}, "not_already_hired_except_as = theorist", [], 2, "army"),
    ("MAN_xian_yuan", None, None, "theorist", 100, "MAN_adv_river_war_theorist", "Theorist of River Warfare",
     {"naval_doctrine_cost_factor": -0.07, "river_crossing_factor": 0.05}, "", [], 1, "navy"),
    ("MAN_deng_linge", None, None, "theorist", 100, "MAN_adv_steppe_air_theorist", "Theorist of Steppe Air Power",
     {"air_doctrine_cost_factor": -0.07, "air_superiority_bonus_in_combat": 0.03}, "", [], 1, "air"),
]
DROP = ["MAN_megata_toshiro", "MAN_nalan_kang_an", "MAN_zhang_yanqing", "MAN_hung_zhehuang"]
TOKEN = {"MAN_Chu_Kudo": "Chu_Kudo", "MAN_masahiko_amakasu": "masahiko_amakasu", "MAN_Hajime_Satomi": "Hajime_Satomi", "MAN_pujie": "MAN_pujie_theorist"}

def knob_effects(cid, knobs):
    add, rem = "", ""
    for i, kn in enumerate(knobs):
        key = f"MAN_tt_adv_{cid[4:].lower()}_{i}"
        if kn[0] == "FLAG":
            add += f"set_country_flag = {kn[1]}\ncustom_effect_tooltip = {key}\n"; rem += f"clr_country_flag = {kn[1]}\n"
        else:
            var, val = kn[0], kn[1]
            add += f"add_to_variable = {{ {var} = {val} }}\ncustom_effect_tooltip = {key}\n"
            if len(kn) == 3: rem += f"subtract_from_variable = {{ {var} = {val} }}\n"
        loc(key, kn[2])
    if add:
        add += "hidden_effect = { MAN_pol_compute = yes MAN_plan_recalc = yes MAN_ui_refresh = yes }\n"
        rem += "MAN_pol_compute = yes\nMAN_plan_recalc = yes\nMAN_ui_refresh = yes\n"
    return add, rem

def advisor_block(a):
    (cid, nm, por, slot, cost, trait, tname, mods, av, knobs, ai, ledger) = a
    add, rem = knob_effects(cid, knobs)
    s = "advisor = {\n" + f"\tslot = {slot}\n\tidea_token = {TOKEN.get(cid, cid)}\n"
    if ledger: s += f"\tledger = {ledger}\n"
    s += "\tallowed = { original_tag = MAN }\n"
    if av: s += f"\tavailable = {{ {av} }}\n"
    s += f"\tcost = {cost}\n\ttraits = {{ {trait} }}\n"
    if add:
        # advisor on_add/on_remove run in character scope: country flags and variables go through owner
        s += "\talways_show_on_actions_tooltip = yes\n\ton_add = {\n\t\towner = {\n" + "".join("\t\t\t" + l + "\n" for l in add.strip().split("\n")) + "\t\t}\n\t}\n"
        s += "\ton_remove = {\n\t\thidden_effect = {\n\t\t\towner = {\n" + "".join("\t\t\t\t" + l + "\n" for l in rem.strip().split("\n")) + "\t\t\t}\n\t\t}\n\t}\n"
    s += f"\tai_will_do = {{ factor = {ai} }}\n}}\n"
    return s

# trait sprite = advisor filter category in the hire window (ADVISOR_CATEGORY_<n>):
# 10 Industry = the Plan, 13 Political = Bureaucracy / Racial Harmony, 15 Intelligence = security and the underworld
CAT = {
    "MAN_adv_reform_bureaucrat": 10, "MAN_adv_nissan_capital": 10, "MAN_adv_mangyo_engineer": 10, "MAN_adv_mantetsu_president": 10,
    "MAN_adv_labour_recruiter": 10, "MAN_adv_finance_minister": 10, "MAN_adv_cer_veteran": 10,
    "MAN_adv_gab_director": 13, "MAN_adv_envoy_tokyo": 13, "MAN_adv_old_bandit_premier": 13, "MAN_cofounder_of_concordia": 13,
    "MAN_adv_fengtian_elder": 13, "MAN_adv_foreign_minister": 13, "MAN_adv_imperial_bodyguard": 13,
    "MAN_adv_manei_chief": 15, "MAN_adv_eastern_jewel": 15, "MAN_adv_opium_king": 15,
    "MAN_adv_defence_minister": 5, "MAN_adv_bannerman_general": 5, "MAN_adv_winter_campaigner": 6,
    "MAN_adv_pacification_staff": 18, "MAN_adv_turncoat_general": 18, "MAN_adv_xingan_cavalry": 17, "MAN_adv_rail_logistics": 6,
    "MAN_adv_army_air_liaison": 2, "MAN_adv_sungari_flotilla": 3,
    "MAN_adv_imperial_guard": 14, "MAN_adv_river_war_theorist": 14, "MAN_adv_steppe_air_theorist": 14,
}

def traits_file():
    t = "leader_traits = {\n"
    for a in ADV:
        trait, tname, mods = a[5], a[6], a[7]
        t += f"\t{trait} = {{\n\t\trandom = no\n\t\tsprite = {CAT[trait]}\n" +"".join(f"\t\t{k} = {v}\n" for k, v in mods.items())
        if trait == "MAN_cofounder_of_concordia": t += "\t\tcustom_modifier_tooltip = MAN_ruan_factory_growth_tt\n"
        t += "\t}\n"
        if trait != "MAN_cofounder_of_concordia": loc(trait, tname)   # keeps its existing name
    return t + "}\n"

def block_end(t, start):
    i = t.index("{", start); d = 0
    for j in range(i, len(t)):
        if t[j] == "{": d += 1
        elif t[j] == "}":
            d -= 1
            if d == 0: return j + 1

def characters():
    t, bom = rd("common/characters/MAN.txt")
    body = t[t.index("{") + 1: t.rindex("}")]
    chars, order, pos = {}, [], 0
    for m in re.finditer(r"\n\t(\w+)\s*=\s*\{", body):
        if m.start() < pos: continue
        e = block_end(body, m.start()); chars[m.group(1)] = body[m.start():e]; order.append(m.group(1)); pos = e
    byid = {a[0]: a for a in ADV}
    out = "characters={\n"
    for cid in order:
        if cid in DROP: continue
        b = chars[cid]
        # strip existing advisor roles and their comments
        while True:
            m = re.search(r"\n\t\t(#[^\n]*\n\t\t)*advisor\s*=\s*\{", b)
            if not m: break
            e = block_end(b, m.start()); b = b[:m.start()] + b[e:]
        b = re.sub(r"\n\t\t#[^\n]*(Imported advisor|Political Advisors)[^\n]*", "", b)
        if cid in byid:
            a = byid[cid]
            if a[1] and not re.search(r"\n\t\tname\s*=", b): pass
            close = b.rstrip().rfind("}")
            b = b[:close].rstrip() + "\n" + "".join("\t\t" + l + "\n" for l in advisor_block(a).strip().split("\n")) + "\t}"
            if not re.search(r"civilian\s*=", b) and a[3] == "political_advisor":
                # political advisors need a civilian portrait: reuse the character's own small portrait
                own = re.search(r'small\s*=\s*"?([\w./-]+)"?', b)
                pic = own.group(1) if own else "GFX_idea_generic_political_advisor_asia_2"
                b = re.sub(r"portraits\s*=\s*\{", "portraits = {\n\t\t\tcivilian = { small = \"" + pic + "\" }", b, count=1)
        out += b.strip("\n").join(["\t", "\n"]) if False else "\t" + b.strip().lstrip("\t") + "\n"
    for a in ADV:   # new characters
        if a[0] in chars: continue
        cid, nm, por = a[0], a[1], a[2]
        kind = "civilian" if a[3] == "political_advisor" else "army"
        pt = f"{kind} = {{ small = \"{por}\" }}" if por.startswith("GFX") else f"{kind} = {{ small = \"{por}\" large = \"{por}\" }}"
        out += f"\t{cid} = {{\n\t\tname = \"{nm}\"\n\t\tportraits = {{ {pt} }}\n" + "".join("\t\t" + l + "\n" for l in advisor_block(a).strip().split("\n")) + "\t}\n"
    out += "}\n"
    wr("common/characters/MAN.txt", out, bom)
    return [a[0] for a in ADV]

def history(ids):
    p = "history/countries/MAN - Manchukou.txt"
    t, bom = rd(p)
    for d in DROP: t = re.sub(rf"\n#?\s*recruit_character = {d}\b[^\n]*", "", t)
    have = set(re.findall(r"^recruit_character = (\w+)", t, re.M))
    add = [i for i in ids if i not in have]
    if add:
        anchor = "# Generals imported from Oak's Manchukuo."
        t = t.replace(anchor, "# Advisors added by the advisor rework\n" + "".join(f"recruit_character = {i}\n" for i in add) + "\n" + anchor, 1)
    wr(p, t, bom)
    return add

# ------------------------------------------------------------------ industrial concerns
FOC = lambda *f: "OR = { " + " ".join(f"has_completed_focus = {x}" for x in f) + " }"
# id, picture, name (None = keep loc), available, modifiers, research bonus, knobs, cost, ai
CONCERNS = [
    ("MAN_south_manchuria_railway_company", "MAN_mantetsu_concern", None, "",
     {"production_speed_infrastructure_factor": 0.15, "production_speed_rail_way_factor": 0.15}, {}, [K_dt("smr", 5), K_qb("coal", 0.10)], 150, 3),
    ("MAN_mange_concern", "MAN_mangyo_concern", None, "has_country_flag = MAN_mangyo_founded",
     {"industrial_capacity_factory": 0.05}, {}, [K_dt("mgy", 5), K_qb("steel", 0.10), K_qb("mach", 0.10)], 150, 3),
    ("MAN_showa_steel", "JAP_japan_steel_works", None, FOC("MAN_eco_showa_steel"),
     {"production_factory_start_efficiency_factor": 0.05}, {}, [K_qb("steel", 0.20)], 150, 2),
    ("MAN_manchuria_electric", "CHI_shanghai_power_company", "Manchuria Electric Industry", FOC("MAN_eco_zone_planning"),
     {"production_speed_buildings_factor": 0.05}, {}, [K_qb("power", 0.25)], 150, 2),
    ("MAN_manchuria_coal_mining", "PER_iranian_oil_company", "Manchuria Coal Mining Company", FOC("MAN_eco_fushun_shale"),
     {"fuel_gain_factor": 0.10}, {}, [K_qb("coal", 0.20)], 150, 2),
    ("MAN_manchuria_chemical", "CHI_yongli_chemical_industries", "Manchuria Chemical Industries", FOC("MAN_eco_powder_company", "MAN_eco_synthetic_fuel", "MAN_eco_hydrogenation"),
     {"production_speed_synthetic_refinery_factor": 0.10}, {"synth_resources": 0.15}, [], 125, 1),
    ("MAN_manshu_hikoki_concern", "JAP_tachikawa_aircraft_company", "Manshu Hikoki", FOC("MAN_eco_manshu_hikoki"),
     {}, {"air_equipment": 0.15}, [K_qb("mach", 0.10)], 150, 2),
    ("MAN_dowa_automobile", "ENG_crossley_motors", "Dowa Automobile", FOC("MAN_eco_dowa"),
     {}, {"motorized_equipment": 0.15}, [K_qb("mach", 0.05)], 125, 1),
    ("MAN_daito_koshi", "MAN_manchurian_industry", "Daito Koshi", FOC("MAN_eco_labour_agency"),
     {"production_speed_industrial_complex_factor": 0.05}, {}, [K_inc(1.0), K_levy(0.8)], 125, 2),
    ("MAN_korean_colonisation_company", "MAN_korean_colonisation_company", None,
     "OR = { has_country_flag = MAN_korean_colonisation_unlocked has_completed_focus = MAN_eco_korean_settlers has_completed_focus = MAN_eco_million_households }",
     {"recruitable_population_factor": 0.03}, {}, [("MAN_zone_cap", 1, "£state §YDevelopment zone allowance§!: §G+1§!")], 125, 2),
    ("MAN_manchukuo_film_association", "MAN_manchukuo_film_association", None,
     "OR = { has_country_flag = MAN_film_association_unlocked date > 1937.8.21 }",
     {"stability_weekly": 0.001, "war_support_weekly": 0.001, "power_balance_weekly": 0.001}, {"electronics": 0.10}, [], 125, 1),
]

def concerns():
    p = "common/ideas/manchukou.txt"
    t, bom = rd(p)
    i = t.index("\tindustrial_concern = {")
    e = block_end(t, i)
    s = "\tindustrial_concern = {\n"
    for (cid, pic, nm, av, mods, rb, knobs, cost, ai) in CONCERNS:
        add, rem = knob_effects(cid, knobs)
        s += f"\t\t{cid} = {{\n\t\t\tpicture = {pic}\n\t\t\tallowed = {{ original_tag = MAN }}\n"
        if av: s += f"\t\t\tavailable = {{ {av} }}\n"
        s += f"\t\t\tcost = {cost}\n"
        if mods: s += "\t\t\tmodifier = {\n" + "".join(f"\t\t\t\t{k} = {v}\n" for k, v in mods.items()) + "\t\t\t}\n"
        if rb: s += "\t\t\tresearch_bonus = {\n" + "".join(f"\t\t\t\t{k} = {v}\n" for k, v in rb.items()) + "\t\t\t}\n"
        if add:
            s += "\t\t\ton_add = {\n" + "".join("\t\t\t\t" + l + "\n" for l in add.strip().split("\n")) + "\t\t\t}\n"
            s += "\t\t\ton_remove = {\n\t\t\t\thidden_effect = {\n" + "".join("\t\t\t\t\t" + l + "\n" for l in rem.strip().split("\n")) + "\t\t\t\t}\n\t\t\t}\n"
        s += f"\t\t\tai_will_do = {{ factor = {ai} }}\n\t\t}}\n"
        if nm: loc(cid, nm)
    loc("MAN_showa_steel_works", "Showa Steel Works")   # shared Chinese concern in china_shared.txt
    s += "\t}"
    wr(p, t[:i] + s + t[e:], bom)

def build():
    concerns()
    wr("common/country_leader/MAN_imported_traits.txt", traits_file())
    ids = characters()
    added = history(ids)
    return L, added
