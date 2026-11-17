"""Manchukuo systems: scripted effects, triggers, dynamic modifiers, GUIs, events, hooks."""
from man_common import *
import man_systems as MS
from man_sites import SITES as SI_SITES
from PIL import Image, ImageDraw

L = []
def loc(k, v): L.append((k, v))

def clamp(v, lo=0, hi=100): return f"clamp_variable = {{ var = {v} min = {lo} max = {hi} }}\n"
def frame(fv, src):
    return (f"set_variable = {{ {fv} = {src} }}\ndivide_variable = {{ {fv} = 10 }}\nround_variable = {fv}\n"
            f"add_to_variable = {{ {fv} = 1 }}\nclamp_variable = {{ var = {fv} min = 1 max = 11 }}\n")

# ------------------------------------------------------------------------------------------------ effects
E = "# Manchukuo: Industrial Development Plan / Hsinking Bureaucracy / Public Security\n\n"

init = "set_country_flag = MAN_sys_init\n"
init += "".join(f"set_variable = {{ {v} = {x} }}\n" for v, x in [
    ("MAN_plan_stage", 0), ("MAN_plan_year", 0), ("MAN_labour", 20), ("MAN_labour_income", 1), ("MAN_zone_cap", 0), ("MAN_zones_used", 0),
    ("MAN_proj_slots", 2), ("MAN_proj_active", 0), ("MAN_proj_done", 0), ("MAN_rail_built", 0), ("MAN_quota_focus", 0), ("MAN_quota_mult", 1),
    ("MAN_review_need", 20), ("MAN_review_need_m", 19.99),
    ("MAN_qt_steel", 100), ("MAN_qt_coal", 100), ("MAN_qt_power", 70), ("MAN_qt_mach", 90),
    ("MAN_q_steel", 0), ("MAN_q_coal", 0), ("MAN_q_power", 0), ("MAN_q_mach", 0),
    ("MAN_fav_kw", 50), ("MAN_fav_gab", 45), ("MAN_fav_ind", 0), ("MAN_fav_mgy", 0), ("MAN_fav_smr", 50),
    ("MAN_h_kw", 1), ("MAN_h_gab", 1), ("MAN_h_ind", 0), ("MAN_h_mgy", 0), ("MAN_h_smr", 1),
    ("MAN_tc_kw", 0), ("MAN_tc_gab", 0), ("MAN_tc_ind", 0), ("MAN_tc_mgy", 0), ("MAN_tc_smr", 0),
    ("MAN_bm_kw", 0), ("MAN_bm_gab", 0), ("MAN_bm_ind", 0), ("MAN_bm_mgy", 0), ("MAN_bm_smr", 0),
    ("MAN_kw_pat", 60), ("MAN_kp_stab", 0), ("MAN_kp_ws", 0),
    ("MAN_band1", 80), ("MAN_band2", 70), ("MAN_band3", 60), ("MAN_band1p", 80), ("MAN_band2p", 70), ("MAN_band3p", 60),
    ("MAN_bandit_avg", 30), ("MAN_ps_stab", 0), ("MAN_ps_wk", 0), ("MAN_kp_wk", 0),
    ("MAN_levy", 0), ("MAN_levy_g", 0), ("MAN_lv_wk", 0), ("MAN_gar_n", 0), ("MAN_gar_cap", 3)] + [(f"MAN_mega_{m[0]}_n", 0) for m in MS.MEGA]
    + [(f"MAN_megacap_{m[0]}", m[4]) for m in MS.MEGA] + [(f"MAN_cap_{s_[0]}", s_[5]) for s_ in SI_SITES] + [(f"MAN_lvc_{s_[0]}", 0) for s_ in SI_SITES])
init += "if = { limit = { date > 1937.12.1 } MAN_ayukawa_arrives = yes }\n"
# the Three-Year Public Security Plan (1936 to 1939) runs from the start, not from a focus
init += "if = { limit = { date < 1938.1.1 } set_country_flag = MAN_sec_plan_active }\n"
init += "".join(f"{s_} = {{ set_state_flag = MAN_surveyed add_dynamic_modifier = {{ modifier = MAN_surveyed_dm }} }}\n" for s_ in (716, 328))
init += "if = {\n\tlimit = { date > 1938.12.31 }\n\tset_variable = { MAN_band1 = 45 }\n\tset_variable = { MAN_band2 = 40 }\n\tset_variable = { MAN_band3 = 40 }\n}\n"
for s in STATES:
    init += f"{s} = {{ set_variable = {{ MAN_bandit = {BANDIT0[s]} }} set_variable = {{ MAN_bgrow = {BGROW[s]} }} set_variable = {{ MAN_eff = 1 }} set_variable = {{ MAN_btier = 0 }} set_variable = {{ MAN_colony_g = 0 }} }}\n"
init += ("add_dynamic_modifier = { modifier = MAN_hsinking_bureaucracy }\n"
         "add_dynamic_modifier = { modifier = MAN_public_security }\nMAN_pol_compute = yes\nMAN_sec_refresh = yes\nMAN_plan_recalc = yes\nMAN_ui_refresh = yes\n")
E += "MAN_systems_init = {\n" + ind(init, 1) + "}\n\n"

# ---- plan
rc = ""
for k, _ in QUOTAS:
    rc += f"set_variable = {{ MAN_pct_{k} = MAN_q_{k} }}\nmultiply_variable = {{ MAN_pct_{k} = 100 }}\ndivide_variable = {{ MAN_pct_{k} = MAN_qt_{k} }}\n" + clamp(f"MAN_pct_{k}")
rc += "set_variable = { MAN_plan_pct = MAN_pct_steel }\nadd_to_variable = { MAN_plan_pct = MAN_pct_coal }\nadd_to_variable = { MAN_plan_pct = MAN_pct_power }\nadd_to_variable = { MAN_plan_pct = MAN_pct_mach }\ndivide_variable = { MAN_plan_pct = 4 }\n"
E += "MAN_plan_recalc = {\n" + ind(rc, 1) + "}\n\n"
E += "MAN_plan_weekly = {\n" + ind("add_to_variable = { MAN_labour = MAN_labour_income }\n"
      "if = { limit = { check_variable = { MAN_bop_t < -0.5 } } set_temp_variable = { MAN_v = MAN_bop_t } multiply_temp_variable = { MAN_v = -0.2 } add_to_variable = { MAN_labour = MAN_v } }\n"
      # labour stays scarce: each running project ties up 0.5k a week in wages and rations, and idle workers above 60k drift home (5% of the excess a week)
      + "set_temp_variable = { MAN_v = MAN_proj_active }\nmultiply_temp_variable = { MAN_v = 0.5 }\nsubtract_from_variable = { MAN_labour = MAN_v }\n"
      + "if = {\n\tlimit = { check_variable = { MAN_labour > 60 } }\n\tset_temp_variable = { MAN_v = MAN_labour }\n\tsubtract_from_temp_variable = { MAN_v = 60 }\n"
        "\tmultiply_temp_variable = { MAN_v = 0.05 }\n\tsubtract_from_variable = { MAN_labour = MAN_v }\n}\n"
      + clamp("MAN_labour", 0, 200)
      # labour levy pressure: fades 6% a week, fed by levy decisions and labour-gang knobs; each point costs 0.015% stability a week
      + "multiply_variable = { MAN_levy = 0.94 }\nadd_to_variable = { MAN_levy = MAN_levy_g }\n" + clamp("MAN_levy", 0, 40)
      + "set_variable = { MAN_lv_wk = MAN_levy }\nmultiply_variable = { MAN_lv_wk = -0.00015 }\nMAN_dm_sums = yes\n"
      + "MAN_prov_weekly = yes\nMAN_plan_recalc = yes\n", 1) + "}\n\n"
# Racial Harmony balance of power tier (-3 Manchurian Nation .. +3 Japanese Colony), read by the weekly systems
bt = "set_variable = { MAN_bop_t = 0 }\n"
for lo, t in ((0.1, 1), (0.4, 2), (0.7, 3)):
    bt += f"if = {{ limit = {{ power_balance_value = {{ id = MAN_racial_harmony value > {lo} }} }} set_variable = {{ MAN_bop_t = {t} }} }}\n"
    bt += f"if = {{ limit = {{ power_balance_value = {{ id = MAN_racial_harmony value < -{lo} }} }} set_variable = {{ MAN_bop_t = -{t} }} }}\n"
bt += "if = { limit = { check_variable = { MAN_kw_pat < 30 } } add_power_balance_value = { id = MAN_racial_harmony value = 0.005 } }\n"
E += "MAN_bop_tier = {\n" + ind(bt, 1) + "}\n\n"

start_year = """if = {
	limit = { has_country_flag = MAN_revision_pending }
	clr_country_flag = MAN_revision_pending
""" + "".join(f"\tmultiply_variable = {{ MAN_qt_{k} = 1.6 }}\n" for k, _ in QUOTAS) + """	MAN_plan_recalc = yes
}
set_country_flag = MAN_review_running
set_country_flag = { flag = MAN_review_lock days = 300 }
set_variable = { MAN_review_need = MAN_plan_year }
multiply_variable = { MAN_review_need = 20 }
subtract_from_variable = { MAN_review_need = MAN_review_relief }
clamp_variable = { var = MAN_review_need min = 0 max = 100 }
set_variable = { MAN_review_need_m = MAN_review_need }
subtract_from_variable = { MAN_review_need_m = 0.01 }
"""
E += "MAN_plan_start_year = {\n" + ind(start_year, 1) + "}\n\n"
next_year = """# a plan fulfilled in full by its third review or later closes ahead of schedule
if = {
	limit = { check_variable = { MAN_plan_year > 2.5 } check_variable = { MAN_plan_pct > 99.99 } check_variable = { MAN_plan_year < 4.5 } }
	set_variable = { MAN_plan_year = 5 }
	set_country_flag = MAN_plan_early
	custom_effect_tooltip = MAN_tt_plan_early
	add_political_power = 50
	add_to_variable = { MAN_kw_pat = 5 }
	add_to_variable = { MAN_fav_ind = 5 }
}
add_to_variable = { MAN_plan_year = 1 }
if = {
	limit = { check_variable = { MAN_plan_year > 5.5 } }
	clr_country_flag = MAN_plan_running
	if = {
		limit = { check_variable = { MAN_plan_stage < 2.5 } }
		set_country_flag = MAN_first_fyp_complete
		country_event = { id = man_sys.4 days = 2 }
	}
	else = {
		set_country_flag = MAN_second_fyp_complete
		country_event = { id = man_sys.5 days = 2 }
	}
}
else = {
	MAN_plan_start_year = yes
}
MAN_ui_refresh = yes
"""
E += "MAN_plan_next_year = {\n" + ind(next_year, 1) + "}\n\n"
loc("MAN_tt_plan_early", "§GThe Plan is fulfilled ahead of schedule!§! It closes now: £pol_power §G+50§!, £army_experience §LKwantung Army patience§! §G+5§!, £influence_texticon §LMinistry of Industry§! favour §G+5§!")
E += """MAN_plan_begin = {
	set_country_flag = MAN_plan_running
	set_variable = { MAN_plan_year = 1 }
	MAN_plan_start_year = yes
	MAN_plan_recalc = yes
	MAN_ui_refresh = yes
}

"""

# ---- security
def sec_state_loop():
    s = "every_owned_state = {\n\tlimit = { " + MANCHURIA_TRIGGER + " }\n"
    body = "set_temp_variable = { MAN_g = MAN_bgrow }\nadd_to_temp_variable = { MAN_g = MAN_colony_g }\nadd_to_temp_variable = { MAN_g = ROOT.MAN_bgrow_g }\nset_temp_variable = { MAN_v = ROOT.MAN_bop_t }\nmultiply_temp_variable = { MAN_v = 0.01 }\nadd_to_temp_variable = { MAN_g = MAN_v }\n"
    for fl, d in [("MAN_garrisoned", -0.08), ("MAN_hamlets", -0.25), ("MAN_blockhouses", -0.10), ("MAN_informants", -0.15), ("MAN_grievance", 0.15), ("MAN_8ra", 0.15)]:
        body += f"if = {{ limit = {{ has_state_flag = {fl} }} add_to_temp_variable = {{ MAN_g = {d} }} }}\n"
    for n, (_, _, homes, _) in MS.BANDS.items():
        for sid, coef in homes:
            body += f"if = {{ limit = {{ state = {sid} }} set_temp_variable = {{ MAN_b = ROOT.MAN_band{n}p }} multiply_temp_variable = {{ MAN_b = {coef} }} add_to_temp_variable = {{ MAN_g = MAN_b }} }}\n"
    body += "set_temp_variable = { MAN_r = MAN_bandit }\nmultiply_temp_variable = { MAN_r = 0.006 }\nsubtract_from_temp_variable = { MAN_g = MAN_r }\n"
    body += "add_to_variable = { MAN_bandit = MAN_g }\n" + clamp("MAN_bandit")
    return s + ind(body, 1) + "}\n"

sw = "MAN_bop_tier = yes\nMAN_sec_orders_weekly = yes\n"
sw += sec_state_loop()   # garrisons are a paid security order (MAN_gar_begin), not divisions on the map
for n, (_, _, _, ex) in MS.BANDS.items():
    grow = "0.2"
    sw += f"""if = {{
	limit = {{ NOT = {{ has_country_flag = MAN_band{n}_dead }} NOT = {{ has_country_flag = MAN_band{n}_exile }} }}
	if = {{ limit = {{ check_variable = {{ MAN_band{n} > 0 }} }} add_to_variable = {{ MAN_band{n} = {grow} }} subtract_from_variable = {{ MAN_band{n} = MAN_band_drain }} }}
"""
    if ex: sw += f"\tif = {{ limit = {{ has_country_flag = MAN_border_sealed }} subtract_from_variable = {{ MAN_band{n} = 0.1 }} }}\n"
    if n == 1: sw += "\tif = { limit = { has_country_flag = MAN_nozoe_active } subtract_from_variable = { MAN_band1 = 0.95 } }\n"
    sw += f"""	if = {{
		limit = {{ check_variable = {{ MAN_band{n} < 0.01 }} }}
		set_variable = {{ MAN_band{n} = 0 }}
		set_country_flag = MAN_band{n}_dead
		country_event = {{ id = man_sys.3{n - 1} days = 1 }}
	}}
	{clamp(f'MAN_band{n}').strip()}
}}
"""
sw += "MAN_sec_refresh = yes\n"
E += "MAN_sec_weekly = {\n" + ind(sw, 1) + "}\n\n"

rf = ""
for n in MS.BANDS:
    rf += f"set_variable = {{ MAN_band{n}p = MAN_band{n} }}\nif = {{ limit = {{ OR = {{ has_country_flag = MAN_band{n}_dead has_country_flag = MAN_band{n}_exile }} }} set_variable = {{ MAN_band{n}p = 0 }} }}\n"
rf += "set_variable = { MAN_bsum = 0 }\nset_variable = { MAN_bn = 0 }\nset_variable = { MAN_gar_n = 0 }\n"
rf += "".join(f"set_variable = {{ MAN_bl_{s} = 0 }}\n" for s in STATES)
loopb = ("set_variable = { MAN_eff = MAN_bandit }\ndivide_variable = { MAN_eff = -150 }\nadd_to_variable = { MAN_eff = 1 }\nclamp_variable = { var = MAN_eff min = 0.35 max = 1 }\n"
         "add_to_variable = { ROOT.MAN_bsum = THIS.MAN_bandit }\nadd_to_variable = { ROOT.MAN_bn = 1 }\nMAN_sec_set_tier = yes\n"
         "if = { limit = { has_state_flag = MAN_garrisoned } add_to_variable = { ROOT.MAN_gar_n = 1 } }\n")
loopb += "".join(f"if = {{ limit = {{ state = {s} }} set_variable = {{ ROOT.MAN_bl_{s} = THIS.MAN_bandit }} }}\n" for s in STATES)
rf += "every_owned_state = {\n\tlimit = { " + MANCHURIA_TRIGGER + " }\n" + ind(loopb, 1) + "}\n"
rf += "if = {\n\tlimit = { check_variable = { MAN_bn > 0 } }\n\tset_variable = { MAN_bandit_avg = MAN_bsum }\n\tdivide_variable = { MAN_bandit_avg = MAN_bn }\n}\n"
# public security: -0.2% stability per point of average banditry, and above 25 a weekly drain of 0.005% per point
rf += ("set_variable = { MAN_ps_stab = MAN_bandit_avg }\nmultiply_variable = { MAN_ps_stab = -0.002 }\n"
       "set_variable = { MAN_ps_wk = MAN_bandit_avg }\nsubtract_from_variable = { MAN_ps_wk = 25 }\nmultiply_variable = { MAN_ps_wk = -0.00005 }\n"
       "clamp_variable = { var = MAN_ps_wk min = -0.004 max = 0 }\nMAN_dm_sums = yes\n")
E += "MAN_sec_refresh = {\n" + ind(rf, 1) + "}\n\n"

tier = "set_temp_variable = { MAN_nt = 0 }\n"
for i, th in enumerate([24.99, 44.99, 64.99, 84.99], 1):
    tier += f"if = {{ limit = {{ check_variable = {{ MAN_bandit > {th} }} }} set_temp_variable = {{ MAN_nt = {i} }} }}\n"
tier += "if = {\n\tlimit = { NOT = { check_variable = { MAN_btier = MAN_nt } } }\n"
tier += "".join(f"\tremove_dynamic_modifier = {{ modifier = MAN_bandits_{i} }}\n" for i in range(1, 5))
tier += "".join(f"\tif = {{ limit = {{ check_variable = {{ MAN_nt = {i} }} }} add_dynamic_modifier = {{ modifier = MAN_bandits_{i} }} }}\n" for i in range(1, 5))
tier += "\tset_variable = { MAN_btier = MAN_nt }\n}\n"
E += "MAN_sec_set_tier = {\n" + ind(tier, 1) + "}\n\n"

sm = """if = {
	limit = { JAP = { OR = { has_war_with = CHI has_war_with = PRC } } 610 = { is_owned_by = ROOT } }
	610 = { set_state_flag = { flag = MAN_8ra days = 40 } }
}
"""
for n in (2, 3):
    sm += f"""if = {{
	limit = {{
		NOT = {{ has_country_flag = MAN_band{n}_dead }}
		NOT = {{ has_country_flag = MAN_band{n}_exile }}
		NOT = {{ has_country_flag = MAN_border_sealed }}
		check_variable = {{ MAN_band{n} < 25 }}
		country_exists = SOV
	}}
	random_list = {{
		20 = {{ set_country_flag = MAN_band{n}_exile country_event = {{ id = man_sys.3{n + 1} days = 2 }} }}
		80 = {{ }}
	}}
}}
if = {{
	limit = {{
		has_country_flag = MAN_band{n}_exile
		OR = {{ has_war_with = SOV JAP = {{ has_war_with = SOV }} }}
	}}
	clr_country_flag = MAN_band{n}_exile
	set_variable = {{ MAN_band{n} = 55 }}
	country_event = {{ id = man_sys.35 days = 1 }}
}}
"""
E += "MAN_sec_monthly = {\n" + ind(sm, 1) + "}\n\n"

# ---- politics
pc = ""
for k in BROKERS:
    pc += clamp(f"MAN_fav_{k}")
DIV = {"kw": 1000, "gab": 500, "ind": 625, "mgy": 833, "smr": 250}
for k in BROKERS:
    pc += f"set_variable = {{ MAN_bm_{k} = MAN_fav_{k} }}\nsubtract_from_variable = {{ MAN_bm_{k} = 50 }}\ndivide_variable = {{ MAN_bm_{k} = {DIV[k]} }}\n"
    pc += f"if = {{ limit = {{ check_variable = {{ MAN_h_{k} < 0.5 }} }} set_variable = {{ MAN_bm_{k} = 0 }} }}\n"
    pc += f"add_to_variable = {{ MAN_bm_{k} = MAN_tc_{k} }}\n"
pc += """set_variable = { MAN_quota_mult = MAN_fav_ind }
subtract_from_variable = { MAN_quota_mult = 50 }
divide_variable = { MAN_quota_mult = 250 }
if = { limit = { check_variable = { MAN_h_ind < 0.5 } } set_variable = { MAN_quota_mult = 0 } }
add_to_variable = { MAN_quota_mult = 1 }
add_to_variable = { MAN_quota_mult = MAN_quota_focus }
if = { limit = { check_variable = { MAN_bop_t > 0.5 } } set_temp_variable = { MAN_v = MAN_bop_t } multiply_temp_variable = { MAN_v = 0.03 } add_to_variable = { MAN_quota_mult = MAN_v } }
clamp_variable = { var = MAN_quota_mult min = 0.6 max = 2 }
""" + clamp("MAN_kw_pat") + """set_variable = { MAN_kp_stab = MAN_kw_pat }
subtract_from_variable = { MAN_kp_stab = 50 }
divide_variable = { MAN_kp_stab = 500 }
set_variable = { MAN_kp_ws = MAN_kw_pat }
subtract_from_variable = { MAN_kp_ws = 50 }
divide_variable = { MAN_kp_ws = 1000 }
set_variable = { MAN_kp_wk = MAN_kw_pat }
subtract_from_variable = { MAN_kp_wk = 40 }
multiply_variable = { MAN_kp_wk = 0.0001 }
clamp_variable = { var = MAN_kp_wk min = -0.004 max = 0 }
MAN_dm_sums = yes
"""
E += "MAN_pol_compute = {\n" + ind(pc, 1) + "}\n\n"

# ---- the four country spirits share modifiers, so each shared modifier reads one summed variable
DM_SUMS = [
    ("MAN_s_res", 0, ["MAN_influence_local_resources_factor", "MAN_dream_local_resources_factor", "MAN_behemoth_local_resources_factor"]),
    ("MAN_s_effg", 0.1, ["MAN_behemoth_production_factory_efficiency_gain_factor"]),
    ("MAN_s_effm", 0, ["MAN_dream_production_factory_max_efficiency_factor", "MAN_behemoth_production_factory_max_efficiency_factor"]),
    ("MAN_s_bld", 0, ["MAN_dream_production_speed_buildings_factor", "MAN_behemoth_production_speed_buildings_factor", "MAN_bm_ind"]),
    ("MAN_s_ic", 0, ["MAN_dream_production_speed_industrial_complex_factor", "MAN_behemoth_production_speed_industrial_complex_factor"]),
    ("MAN_s_arms", 0, ["MAN_dream_production_speed_arms_factory_factor", "MAN_behemoth_production_speed_arms_factory_factor"]),
    ("MAN_s_infra", 0, ["MAN_behemoth_production_speed_infrastructure_factor", "MAN_bm_smr"]),
    ("MAN_s_icf", 0, ["MAN_dream_industrial_capacity_factory", "MAN_behemoth_industrial_capacity_factory", "MAN_bm_mgy"]),
    ("MAN_s_cge", 0, ["MAN_dream_consumer_goods_expected_value", "MAN_behemoth_consumer_goods_factor"]),
    ("MAN_s_rsp", 0, ["MAN_dream_research_speed_factor", "MAN_behemoth_research_speed_factor"]),
    ("MAN_s_rec", 0, ["MAN_dream_recruitable_population_factor", "MAN_behemoth_recruitable_population_factor"]),
    ("MAN_s_ppf", 0, ["MAN_dream_political_power_factor", "MAN_behemoth_political_power_factor", "MAN_bm_gab"]),
    ("MAN_s_stf", -0.2, ["MAN_behemoth_stability_factor", "MAN_kp_stab"]),
    ("MAN_s_stw", 0, ["MAN_dream_stability_weekly", "MAN_behemoth_stability_weekly", "MAN_kp_wk"]),
    ("MAN_s_psw", 0, ["MAN_ps_wk", "MAN_lv_wk"]),
]
ds = ""
for v, base, parts in DM_SUMS:
    ds += f"set_variable = {{ {v} = {base} }}\n" + "".join(f"add_to_variable = {{ {v} = {p} }}\n" for p in parts)
ds += "force_update_dynamic_modifier = yes\n"
E += "MAN_dm_sums = {\n" + ind(ds, 1) + "}\n\n"

pw = ""
for k in BROKERS:
    pw += f"if = {{ limit = {{ check_variable = {{ MAN_h_{k} > 0.5 }} }} set_temp_variable = {{ MAN_d = 40 }} add_to_temp_variable = {{ MAN_d = MAN_dt_{k} }} subtract_from_temp_variable = {{ MAN_d = MAN_fav_{k} }} multiply_temp_variable = {{ MAN_d = 0.02 }} add_to_variable = {{ MAN_fav_{k} = MAN_d }} }}\n"
pw += """set_temp_variable = { MAN_d = MAN_fav_kw }
subtract_from_temp_variable = { MAN_d = 50 }
divide_temp_variable = { MAN_d = 250 }
set_temp_variable = { MAN_e = MAN_bandit_avg }
subtract_from_temp_variable = { MAN_e = 30 }
divide_temp_variable = { MAN_e = 150 }
subtract_from_temp_variable = { MAN_d = MAN_e }
add_to_temp_variable = { MAN_d = MAN_pat_drift }
set_temp_variable = { MAN_v = MAN_bop_t }
multiply_temp_variable = { MAN_v = 0.03 }
add_to_temp_variable = { MAN_d = MAN_v }
add_to_variable = { MAN_kw_pat = MAN_d }
MAN_pol_compute = yes
if = {
	limit = { check_variable = { MAN_kw_pat < 15 } NOT = { has_country_flag = MAN_guidance_cd } }
	set_country_flag = { flag = MAN_guidance_cd days = 365 }
	country_event = { id = man_sys.20 days = 1 }
}
if = {
	limit = { check_variable = { MAN_kw_pat > 84.99 } NOT = { has_country_flag = MAN_trusted_done } }
	set_country_flag = MAN_trusted_done
	country_event = { id = man_sys.21 days = 1 }
}
"""
E += "MAN_pol_weekly = {\n" + ind(pw, 1) + "}\n\n"

COURT_COST = {"kw": 30, "gab": 30, "ind": 40, "mgy": 30, "smr": 30}
for k in BROKERS:
    riv = MS.BK[k][1]
    s = f"add_political_power = -{COURT_COST[k]}\nadd_to_variable = {{ MAN_fav_{k} = 12 }}\n"
    if riv: s += f"subtract_from_variable = {{ MAN_fav_{riv} = 6 }}\n"
    s += f"set_country_flag = {{ flag = MAN_court_cd_{k} days = 60 }}\nMAN_pol_compute = yes\nMAN_ui_refresh = yes\n"
    E += f"MAN_court_{k} = {{\n" + ind(s, 1) + "}\n"
    E += f"""MAN_req_success_{k} = {{
	add_to_variable = {{ MAN_fav_{k} = 18 }}
	custom_effect_tooltip = MAN_tt_fav_{k}_18
	add_to_variable = {{ MAN_kw_pat = 5 }}
	custom_effect_tooltip = MAN_tt_pat_5
	add_political_power = 25
	set_country_flag = {{ flag = MAN_req_cd_{k} days = 60 }}
	hidden_effect = {{ MAN_pol_compute = yes MAN_ui_refresh = yes }}
}}
MAN_req_fail_{k} = {{
	add_to_variable = {{ MAN_fav_{k} = -15 }}
	custom_effect_tooltip = MAN_tt_fav_{k}_m15
	add_to_variable = {{ MAN_kw_pat = -5 }}
	custom_effect_tooltip = MAN_tt_pat_m5
	set_country_flag = {{ flag = MAN_req_cd_{k} days = 60 }}
	hidden_effect = {{ MAN_pol_compute = yes MAN_ui_refresh = yes }}
}}

"""

# departures: (event id, broker, holder from, date, patron person key, patron tc var, amount, extra on patron)
DEP = [
    (10, "kw", 1, "1937.3.1", "itagaki", "MAN_tc_kw", 0.02, ""),
    (11, "kw", 2, "1938.5.30", "tojo", "MAN_tc_kw", 0.03, ""),
    (12, "smr", 1, "1939.3.24", "matsuoka", "MAN_tc_gab", 0.05, ""),
    (13, "ind", 1, "1939.10.1", "kishi", "MAN_tc_ind", 0.05, "add_to_variable = { MAN_quota_focus = 0.05 }\n"),
    (14, "gab", 1, "1940.7.20", "hoshino", "MAN_tc_gab", 0.05, ""),
    (15, "mgy", 1, "1942.12.1", "ayukawa", "MAN_tc_mgy", 0.03, ""),
]
mon = ""
for k in BROKERS:
    pick = MS.REQ[k]
    mon += f"""if = {{
	limit = {{ check_variable = {{ MAN_h_{k} > 0.5 }} NOT = {{ has_country_flag = MAN_req_{k}_a }} NOT = {{ has_country_flag = MAN_req_{k}_b }} NOT = {{ has_country_flag = MAN_req_cd_{k} }} }}
	random_list = {{
		20 = {{
			set_country_flag = MAN_req_{k}_a
{ind(pick[3], 3) if pick[3] else ''}		}}
		20 = {{
			set_country_flag = MAN_req_{k}_b
{ind(pick[8], 3) if pick[8] else ''}		}}
		60 = {{ }}
	}}
}}
"""
for (eid, k, h, d, who, tc, amt, extra) in DEP:
    mon += f"if = {{ limit = {{ date > {d} check_variable = {{ MAN_h_{k} = {h} }} NOT = {{ has_country_flag = MAN_dep_{who} }} }} random_list = {{ 30 = {{ set_country_flag = MAN_dep_{who} country_event = {{ id = man_sys.{eid} days = 1 }} }} 70 = {{ }} }} }}\n"
mon += """if = {
	limit = { is_ai = yes has_political_power > 120 }
	if = { limit = { check_variable = { MAN_h_ind > 0.5 } check_variable = { MAN_fav_ind < 45 } NOT = { has_country_flag = MAN_court_cd_ind } } MAN_court_ind = yes }
	else_if = { limit = { check_variable = { MAN_fav_kw < 45 } NOT = { has_country_flag = MAN_court_cd_kw } } MAN_court_kw = yes }
	else_if = { limit = { check_variable = { MAN_h_mgy > 0.5 } check_variable = { MAN_fav_mgy < 45 } NOT = { has_country_flag = MAN_court_cd_mgy } } MAN_court_mgy = yes }
	else_if = { limit = { check_variable = { MAN_fav_smr < 45 } NOT = { has_country_flag = MAN_court_cd_smr } } MAN_court_smr = yes }
}
"""
E += "MAN_pol_monthly = {\n" + ind(mon + "MAN_prov_ai = yes\nMAN_sec_ai = yes\n", 1) + "}\n\n"
for (eid, k, h, d, who, tc, amt, extra) in DEP:
    E += f"""MAN_depart_{who} = {{
	if = {{
		limit = {{ check_variable = {{ MAN_fav_{k} > 59.99 }} }}
		set_country_flag = MAN_patron_{who}
		set_country_flag = MAN_has_patron
		custom_effect_tooltip = MAN_tt_patron_{who}
		add_to_variable = {{ {tc} = {amt} }}
{ind(extra, 2)}	}}
	else_if = {{
		limit = {{ check_variable = {{ MAN_fav_{k} < 30.01 }} }}
		set_country_flag = MAN_enemy_{who}
		custom_effect_tooltip = MAN_tt_enemy_{who}
		add_to_variable = {{ {tc} = -{amt / 2:g} }}
	}}
	else = {{ custom_effect_tooltip = MAN_tt_neutral_departure }}
	add_to_variable = {{ MAN_h_{k} = 1 }}
	set_variable = {{ MAN_fav_{k} = 45 }}
	custom_effect_tooltip = MAN_tt_new_holder
	hidden_effect = {{ MAN_pol_compute = yes MAN_ui_refresh = yes }}
}}
"""
E += """MAN_ayukawa_arrives = {
	if = {
		limit = { check_variable = { MAN_h_mgy < 0.5 } }
		set_variable = { MAN_h_mgy = 1 }
		set_variable = { MAN_fav_mgy = 45 }
		custom_effect_tooltip = MAN_tt_ayukawa_arrives
	}
}
MAN_kishi_arrives = {
	if = {
		limit = { check_variable = { MAN_h_ind < 0.5 } }
		set_variable = { MAN_h_ind = 1 }
		set_variable = { MAN_fav_ind = 55 }
		custom_effect_tooltip = MAN_tt_kishi_arrives
	}
}

"""
# ---- UI refresh (frames)
ui = ""
for k, _ in QUOTAS: ui += frame(f"MAN_f_{k}", f"MAN_pct_{k}")
ui += frame("MAN_f_plan", "MAN_plan_pct") + frame("MAN_f_pat", "MAN_kw_pat")
ui += ("set_variable = { MAN_f_pat21 = MAN_kw_pat }\ndivide_variable = { MAN_f_pat21 = 5 }\nround_variable = MAN_f_pat21\n"
       "add_to_variable = { MAN_f_pat21 = 1 }\nclamp_variable = { var = MAN_f_pat21 min = 1 max = 21 }\n")
for k in BROKERS: ui += frame(f"MAN_f_fav_{k}", f"MAN_fav_{k}")
ui += frame("MAN_f_bavg", "MAN_bandit_avg")
for n in MS.BANDS: ui += frame(f"MAN_f_band{n}", f"MAN_band{n}")
for s in STATES: ui += frame(f"MAN_f_bl_{s}", f"MAN_bl_{s}")
import man_map as MAP
ui += MAP.frame_effect()
E += "MAN_ui_refresh = {\n" + ind(ui, 1) + "}\n\n"
import man_sites as SI
E += SI.prov_effects(ind)
E += SI.sec_effects(ind, MS.BANDS)
wr("common/scripted_effects/MAN_systems_effects.txt", E)

# remove old FYP completion checks from the behemoth file (the accident rolls + MIO funding stay)
bt, bb = rd("common/scripted_effects/MAN_behemoth_scripted_effects.txt")
bt = re.sub(r"# Plan completion checks\n.*?(?=# Construction-MIO)", "", bt, flags=re.S)
bt = bt.replace("shared effects for the Five-Year Plan decisions.", "shared effects for the Industrial Development Plan.")
wr("common/scripted_effects/MAN_behemoth_scripted_effects.txt", bt, bb)

# ------------------------------------------------------------------------------------------------ dynamic modifiers
DM = "\n# ---- Manchukuo systems ----\n"
# four country spirits: economy (Behemoth, with the Pan-Asian dream, the zaibatsu and the brokers' economic bonuses),
# politics (Bureaucracy, with Kwantung supervision and the dream's political side), Public Security (banditry and labour levies), the Army
DM += """MAN_industrial_behemoth = {
	enable = { always = yes }
	icon = GFX_idea_MAN_industrial_behemoth
	extra_trade_to_overlord_factor = MAN_influence_extra_trade_to_overlord_factor
	overlord_trade_cost_factor = -0.5
	cic_to_overlord_factor = MAN_influence_cic_to_overlord_factor
	mic_to_overlord_factor = MAN_influence_mic_to_overlord_factor
	local_resources_factor = MAN_s_res
	production_factory_efficiency_gain_factor = MAN_s_effg
	production_factory_max_efficiency_factor = MAN_s_effm
	production_factory_start_efficiency_factor = MAN_behemoth_production_factory_start_efficiency_factor
	production_speed_buildings_factor = MAN_s_bld
	production_speed_industrial_complex_factor = MAN_s_ic
	production_speed_arms_factory_factor = MAN_s_arms
	production_speed_infrastructure_factor = MAN_s_infra
	production_speed_synthetic_refinery_factor = MAN_behemoth_production_speed_synthetic_refinery_factor
	industrial_capacity_factory = MAN_s_icf
	consumer_goods_expected_value = MAN_s_cge
	consumer_goods_factor = MAN_behemoth_consumer_goods_pct
	research_speed_factor = MAN_s_rsp
	recruitable_population_factor = MAN_s_rec
	line_change_production_efficiency_factor = MAN_dream_line_change_production_efficiency_factor
}
MAN_hsinking_bureaucracy = {
	enable = { always = yes }
	icon = GFX_idea_MAN_reorganisation_process
	stability_factor = MAN_s_stf
	stability_weekly = MAN_s_stw
	war_support_factor = MAN_kp_ws
	political_power_factor = MAN_s_ppf
	political_power_gain = MAN_dream_political_power_gain
	army_org_factor = MAN_bm_kw
	fascism_drift = MAN_dream_fascism_drift
}
MAN_public_security = {
	enable = { always = yes }
	icon = GFX_idea_chi_war_of_resistance
	stability_factor = MAN_ps_stab
	stability_weekly = MAN_s_psw
}
"""
for z, (nm, _, _, mods, _) in MS.ZINFO.items():
    mods = [m.replace("local_manpower = 0.05", "recruitable_population_factor = 0.05") for m in mods]
    DM += f"MAN_zone_{z}_dm = {{\n\tenable = {{ always = yes }}\n\ticon = GFX_idea_generic_production_bonus\n" + "".join(f"\t{m}\n" for m in mods) + "}\n"
BT = [("Bandit Raids", -0.05, -0.10, 0, 0), ("Bandit Country", -0.10, -0.20, -0.10, 0.1), ("Partisan Base Area", -0.20, -0.30, -0.15, 0.2), ("Lost to the Mountains", -0.30, -0.50, -0.25, 0.3)]
for i, (nm, r, b, sl, sab) in enumerate(BT, 1):
    DM += f"MAN_bandits_{i} = {{\n\tenable = {{ always = yes }}\n\ticon = GFX_idea_ITA_bandits_war\n\tlocal_resources_factor = {r}\n\tstate_production_speed_buildings_factor = {b}\n"
    if sl: DM += f"\tlocal_building_slots_factor = {sl}\n"
    if sab: DM += f"\tlocal_factory_sabotage = {sab}\n"
    DM += "}\n"
    loc(f"MAN_bandits_{i}", nm)
DM += "MAN_hamlets_dm = {\n\tenable = { always = yes }\n\ticon = GFX_idea_ITA_bandits_war\n\tlocal_resources_factor = -0.05\n\trecruitable_population_factor = -0.10\n}\n"
DM += "MAN_surveyed_dm = {\n\tenable = { always = yes }\n\ticon = GFX_idea_generic_production_bonus\n\tlocal_resources_factor = 0.05\n}\n"
loc("MAN_surveyed_dm", "Surveyed by Mantetsu")
DM += "MAN_grid_dm = {\n\tenable = { always = yes }\n\ticon = GFX_idea_generic_production_bonus\n\tstate_production_speed_buildings_factor = 0.10\n\tlocal_factory_energy_consumption = -0.10\n}\n"
for i in (1, 2, 3):
    DM += f"MAN_power_station_{i} = {{\n\tenable = {{ always = yes }}\n\ticon = GFX_idea_generic_production_bonus\n\tstate_production_speed_buildings_factor = {0.05 * i:.2f}\n\tlocal_building_slots = {i}\n}}\n"
    loc(f"MAN_power_station_{i}", f"Thermal Power Stations ({i})")
dt, db = rd("common/dynamic_modifiers/MAN_dynamic_modifiers.txt")
dt = dt.split("\n# ---- Manchukuo systems")[0]
# keep only the hand-written spirits that were not merged (Capital of the East state modifier and the Manchurian Army)
def _blk(t, name):
    i = t.index(f"\n{name} = {{") + 1; d = 0
    for j in range(t.index("{", i), len(t)):
        d += t[j] == "{"; d -= t[j] == "}"
        if d == 0: return t[i:j + 1]
army = _blk(dt, "MAN_manchurian_army")
if "acclimatization_cold_climate_gain_factor" not in army:
    army = army[:-1] + "\tacclimatization_cold_climate_gain_factor = MAN_dream_acclimatization_cold_climate_gain_factor\n}"
top = ("# Manchukuo dynamic modifiers\n\n# Capital of the East: state modifier for Kirin, unlocked by the Recognise Russian Influx focus.\n" + _blk(dt, "MAN_capital_of_the_east")
       + "\n\n# The Manchurian Army: day-1 spirit for the whole Kwantung-supervised armed forces.\n" + army + "\n")
wr("common/dynamic_modifiers/MAN_dynamic_modifiers.txt", top + DM, db)
for k, v in [("MAN_hsinking_bureaucracy", "The Hsinking Bureaucracy"),
             ("MAN_public_security", "Public Security and Labour Levies"), ("MAN_hamlets_dm", "Collective Hamlets"), ("MAN_grid_dm", "Transmission Grid")]:
    loc(k, v)
loc("MAN_hsinking_bureaucracy_desc", "Manchukuo is governed by its Japanese vice-ministers, the General Affairs Board and the Kwantung Army staff, not by its ministers. "
    "The favour of each power centre, and the Kwantung Army's patience, shape this spirit. The old Pan-Asian ideal of the Concordia still weighs on it.")
loc("MAN_public_security_desc", "Bandit gangs, Communist guerrillas and the Northeast Anti-Japanese United Army hold the hills and the forests. "
    "Average banditry drags on stability, and so do the labour drives that feed the Plan.")

# ------------------------------------------------------------------------------------------------ bars (sprites)
def bar(name, w, h, col):
    img = Image.new("RGBA", (w * 11, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for f in range(11):
        x0 = f * w
        d.rectangle([x0, 0, x0 + w - 1, h - 1], fill=(28, 26, 22, 235), outline=(120, 110, 90, 255))
        fw = int((w - 4) * f / 10)
        if fw > 0:
            d.rectangle([x0 + 2, 2, x0 + 1 + fw, h - 3], fill=col + (255,))
            d.line([x0 + 2, 2, x0 + 1 + fw, 2], fill=tuple(min(255, c + 50) for c in col) + (255,))
    p = P(f"gfx/interface/MAN/{name}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)
    return f"gfx/interface/MAN/{name}.png"
def pips(name, n=10, pw=15, h=16):
    """Route Army strength: a row of soldier silhouettes (frame f lights f-1 of them), so it never reads like a banditry bar."""
    w = n * pw
    img = Image.new("RGBA", (w * 11, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for f in range(11):
        for i in range(n):
            x0 = f * w + i * pw + 2
            lit = i < f
            body = (176, 158, 92, 255) if lit else (70, 66, 56, 200)
            edge = (60, 50, 30, 255) if lit else (40, 38, 34, 200)
            d.ellipse([x0 + 3, 1, x0 + 7, 5], fill=body, outline=edge)                         # head
            d.polygon([(x0 + 2, 6), (x0 + 8, 6), (x0 + 9, 11), (x0 + 1, 11)], fill=body, outline=edge)  # torso
            d.rectangle([x0 + 2, 11, x0 + 4, h - 1], fill=body)                                 # legs
            d.rectangle([x0 + 6, 11, x0 + 8, h - 1], fill=body)
            d.line([x0 + 9, 2, x0 + 11, 12], fill=edge if lit else (55, 52, 46, 200), width=1)  # rifle
    p = P(f"gfx/interface/MAN/{name}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)
    return f"gfx/interface/MAN/{name}.png"
BARS = {"gold": (205, 160, 55), "blue": (85, 140, 215), "red": (190, 55, 45), "green": (85, 170, 80)}
gfx = "spriteTypes = {\n"
gfx += f"\tspriteType = {{\n\t\tname = \"GFX_MAN_pips_strength\"\n\t\ttexturefile = \"{pips('MAN_pips_strength')}\"\n\t\tnoOfFrames = 11\n\t}}\n"
for nm, col in BARS.items():
    for sz, (w, h) in (("", (150, 14)), ("_small", (80, 10))):
        tex = bar(f"MAN_bar_{nm}{sz}", w, h, col)
        gfx += f"\tspriteType = {{\n\t\tname = \"GFX_MAN_bar_{nm}{sz}\"\n\t\ttexturefile = \"{tex}\"\n\t\tnoOfFrames = 11\n\t}}\n"
import man_polgui as PG
gfx += PG.make_sprites()
gfx += MAP.make_sprites()
gfx += "}\n"
wr("interface/MAN_systems.gfx", gfx)

# ------------------------------------------------------------------------------------------------ GUI
def T(name, x, y, text, w, h=20, font="hoi_16mbs", fmt="left", tt=None):
    s = f"\t\tinstantTextBoxType = {{\n\t\t\tname = \"{name}\"\n\t\t\tposition = {{ x = {x} y = {y} }}\n\t\t\tfont = \"{font}\"\n\t\t\ttext = \"{text}\"\n\t\t\tmaxWidth = {w}\n\t\t\tmaxHeight = {h}\n\t\t\tfixedsize = yes\n\t\t\tformat = {fmt}\n"
    if tt: s += f"\t\t\tpdx_tooltip = \"{tt}\"\n"
    return s + "\t\t}\n"
def I(name, x, y, sprite, tt=None):
    s = f"\t\ticonType = {{\n\t\t\tname = \"{name}\"\n\t\t\tposition = {{ x = {x} y = {y} }}\n\t\t\tspriteType = \"{sprite}\"\n\t\t\tframe = 1\n"
    if tt: s += f"\t\t\tpdx_tooltip = \"{tt}\"\n"
    return s + "\t\t}\n"
def B(name, x, y, sprite, tt, text=None, scale=None):
    s = f"\t\tbuttonType = {{\n\t\t\tname = \"{name}\"\n\t\t\tposition = {{ x = {x} y = {y} }}\n\t\t\tspriteType = \"{sprite}\"\n\t\t\tclicksound = click_default\n\t\t\tpdx_tooltip = \"{tt}\"\n"
    if text: s += f"\t\t\tbuttonText = \"{text}\"\n\t\t\tbuttonFont = \"hoi_16mbs\"\n"
    if scale: s += f"\t\t\tscale = {scale}\n"
    return s + "\t\t}\n"
def W(name, h, body):
    return f"\tcontainerWindowType = {{\n\t\tname = \"{name}\"\n\t\tposition = {{ x = 0 y = 0 }}\n\t\tsize = {{ width = 100%% height = {h} }}\n{body}\t}}\n"

props = {"MAN_plan_board": [], "MAN_politics_board": [], "MAN_security_board": []}
trig = {"MAN_plan_board": [], "MAN_politics_board": [], "MAN_security_board": []}
eff = {"MAN_plan_board": [], "MAN_politics_board": [], "MAN_security_board": []}

# plan board
b = B("MAN_pl_emblem", 6, 2, "GFX_MAN_first_five_year_plan-905539", "MAN_PL_HELP_TT", scale=0.5)
b += T("MAN_pl_title", 62, 4, "[ROOT.GetMANPlanTitle]", 430, 22, "hoi_18mbs")
b += T("MAN_pl_sub1", 62, 27, "MAN_PL_SUB1", 430)
b += T("MAN_pl_sub2", 62, 45, "MAN_PL_SUB2", 430)
b += T("MAN_pl_sub3", 62, 63, "[ROOT.GetMANPlanReview]", 430)
b += T("MAN_pl_h1", 10, 88, "MAN_PL_H_QUOTA", 140) + T("MAN_pl_h2", 160, 88, "MAN_PL_H_PROGRESS", 150) + T("MAN_pl_h3", 322, 88, "MAN_PL_H_DELIV", 110) + T("MAN_pl_h4", 438, 88, "MAN_PL_H_PCT", 52)
y = 110
for k, nm in QUOTAS + [("plan", "Total plan fulfilment")]:
    src = "MAN_plan_pct" if k == "plan" else f"MAN_pct_{k}"
    b += T(f"MAN_pl_n_{k}", 10, y, f"MAN_PL_N_{k.upper()}", 145, 20, "hoi_18mbs" if k == "plan" else "hoi_16mbs", tt=f"MAN_PL_N_{k.upper()}_TT")
    b += I(f"MAN_pl_bar_{k}", 160, y + 3, "GFX_MAN_bar_gold")
    props["MAN_plan_board"].append((f"MAN_pl_bar_{k}", f"MAN_f_{k}"))
    if k != "plan": b += T(f"MAN_pl_v_{k}", 322, y, f"MAN_PL_V_{k.upper()}", 110)
    b += T(f"MAN_pl_p_{k}", 438, y, f"MAN_PL_P_{k.upper()}", 52)
    loc(f"MAN_PL_N_{k.upper()}", nm if k != "plan" else "§YTotal plan fulfilment§!")
    loc(f"MAN_PL_N_{k.upper()}_TT", {"steel": "Pig iron, steel ingots and rolled plate from Anshan, Benxihu and the new furnaces.",
                                    "coal": "Coal from Fushun and the open pits, plus shale oil and synthetic fuel.",
                                    "power": "Generating capacity from thermal stations and the great dams.",
                                    "mach": "Machine tools, vehicles, aircraft and munitions.",
                                    "plan": "The average of the four quota tracks. The Annual Review judges this number."}[k])
    if k != "plan": loc(f"MAN_PL_V_{k.upper()}", f"[?MAN_q_{k}|0] / [?MAN_qt_{k}|0]")
    loc(f"MAN_PL_P_{k.upper()}", f"[?{src}|0]%")
    y += 26 if k != "mach" else 32
import man_sites as SI
mp, mh = MAP.gui_plan(props["MAN_plan_board"], trig["MAN_plan_board"], loc, 10, y + 8, NL)
b += mp
y += mh + 10
pv, y = SI.prov_gui(T, I, B, props["MAN_plan_board"], trig["MAN_plan_board"], eff["MAN_plan_board"], loc, y + 6)
b += pv
PLAN_H = y + 6
GUI = "guiTypes = {\n" + W("MAN_plan_board", PLAN_H, b)
loc("MAN_PL_SUB1", "Labour pool §Y[?MAN_labour|0]k§! workers (§G+[?MAN_labour_income|1]k§! a week)")
loc("MAN_PL_SUB2", "Zones §Y[?MAN_zones_used|0]/[?MAN_zone_cap|0]§!   Projects §Y[?MAN_proj_active|0]/[?MAN_proj_slots|0]§!   Planning efficiency §Y[?MAN_quota_mult|%0]§!")
loc("MAN_PL_H_QUOTA", "§gQuota track§!"); loc("MAN_PL_H_PROGRESS", "§gFulfilment§!"); loc("MAN_PL_H_DELIV", "§gDelivered§!"); loc("MAN_PL_H_PCT", "§g%§!")
loc("MAN_PL_HELP_TT", "§YHow the Plan works§!" + NL + "1. §YZone§! provinces (Heavy Industry, Mining, Power, Settlement, Railway) with the map decisions." + NL +
    "2. Start §Yprojects§! in zoned provinces. They cost political power and §Ylabour§!, tie up civilian factories, and add to the quota tracks when finished." + NL +
    "3. Output is scaled by the province's §Ysecurity§! (Public Security tab) and by §Yplanning efficiency§! (Ministry of Industry favour in the Hsinking Bureaucracy tab)." + NL +
    "4. Each plan year the §YAnnual Review§! needs total fulfilment of 20% per year. Passing pleases the Kwantung Army; failing angers it." + NL +
    "5. §YMegaprojects§! unlocked by the focus tree give large, fixed quota deliveries.")

# politics board
import man_polgui as PG
b, POL_H = PG.board(T, B, props["MAN_politics_board"], trig["MAN_politics_board"], eff["MAN_politics_board"], loc, MS.BK, COURT_COST, NL)
GUI += W("MAN_politics_board", POL_H, b)
loc("MAN_PB_TITLE", "The Hsinking Bureaucracy")
loc("MAN_PB_COURT", "Court")
loc("MAN_PB_PAT_L", "Kwantung Army patience")
loc("MAN_PB_PAT_V", "[?MAN_kw_pat|0]")
loc("MAN_PB_PAT_TT", "§YKwantung Army patience§!" + NL + "Above 50 it raises stability and war support, below 50 it lowers them. It drifts with Kwantung Army Staff favour and falls while banditry stays above 30. Plan reviews and requests move it sharply. Below §R15§! the Kwantung Army intervenes in the government.")
loc("MAN_PB_HELP_TT", "§YThe Hsinking Bureaucracy§!" + NL + "Favour with each power centre (0 to 100, neutral at 50) feeds §YThe Hsinking Bureaucracy§! spirit:" + NL +
    "Kwantung Army Staff: organisation, and stronger punitive sweeps." + NL + "General Affairs Board: political power gain." + NL +
    "Ministry of Industry: construction speed and planning efficiency." + NL + "Mangyo: factory output." + NL + "Mantetsu: infrastructure construction speed." + NL +
    "Favour slowly drifts back towards 40. When a man leaves for Tokyo, high favour makes him a lasting §Gpatron§!, low favour a lasting §Renemy§!.")
TTI = {"kw": "Commands Manchukuo in all but name. Wants the bandits crushed and the arsenals working for the army.",
       "gab": "The Japanese-run cabinet secretariat that really governs. Wants money and order.",
       "ind": "The reform bureaucrats' planning ministry. Drives the Five-Year Plan.",
       "mgy": "Ayukawa Yoshisuke's Manchurian Industrial Development Company, built on Nissan capital.",
       "smr": "The South Manchuria Railway Company: railways, mines, research and a state within the state."}
for k in BROKERS:
    loc(f"MAN_PB_I_{k.upper()}_TT", f"§Y{MS.BK[k][0]}§!" + NL + TTI[k] + NL + "Favour: §Y[?MAN_fav_" + k + "|0]§! (neutral 50)")

# security board
b = B("MAN_sb_emblem", 6, 2, "GFX_focus_MAN_sec_security_plan", "MAN_SB_HELP_TT", scale=0.5)
b += T("MAN_sb_title", 62, 4, "MAN_SB_TITLE", 430, 22, "hoi_18mbs")
b += T("MAN_sb_avg_l", 62, 28, "MAN_SB_AVG_L", 170)
b += I("MAN_sb_avg_bar", 235, 31, "GFX_MAN_bar_red")
props["MAN_security_board"].append(("MAN_sb_avg_bar", "MAN_f_bavg"))
b += T("MAN_sb_avg_v", 392, 28, "MAN_SB_AVG_V", 40)
b += T("MAN_sb_avg_s", 62, 47, "[ROOT.GetMANSecurity]", 430)
y = 74
b += T("MAN_sb_rh_l", 10, y, "MAN_SB_RH_L", 215) + T("MAN_sb_rh_r", 235, y, "MAN_SB_RH_R", 200, tt="MAN_SB_RH_TT")
loc("MAN_SB_RH_L", "§gRoute Armies§! (the armed resistance)")
loc("MAN_SB_RH_R", "§gStrength§! (each figure = 10)")
loc("MAN_SB_RH_TT", "§ORoute Army§! strength runs from §Y0§! (destroyed) to §Y100§!. It is not banditry: a strong army raises §Obanditry§! in its home provinces every week.")
y += 20
for n, (bn, leader, homes, ex) in MS.BANDS.items():
    b += T(f"MAN_sb_bn_{n}", 10, y, f"MAN_SB_BN_{n}", 215, tt=f"MAN_SB_BN_{n}_TT")
    b += T(f"MAN_sb_bs_{n}", 10, y + 18, f"[ROOT.GetMANBandSt_{n}]", 225)
    b += I(f"MAN_sb_bbar_{n}", 235, y + 3, "GFX_MAN_pips_strength", f"MAN_SB_BN_{n}_TT")
    props["MAN_security_board"].append((f"MAN_sb_bbar_{n}", f"MAN_f_band{n}"))
    b += T(f"MAN_sb_bv_{n}", 392, y + 1, f"MAN_SB_BV_{n}", 40)
    loc(f"MAN_SB_BN_{n}", f"§Y{bn}§! ({leader})")
    loc(f"MAN_SB_BV_{n}", f"§Y[?MAN_band{n}|0]§!")
    homes_s = " and ".join(SNAME[s] for s, _ in homes)
    loc(f"MAN_SB_BN_{n}_TT", f"§Y{bn} of the Northeast Anti-Japanese United Army§!" + NL + f"Commander: {leader}. Operates in {homes_s}, where its strength drives banditry up every week." + NL +
        "Strength recovers slowly through recruitment. Sweeps and Collective Hamlets in its home provinces wear it down; Surrender Campaigns peel men away." +
        (NL + "When broken it may slip across the Amur into the Soviet Union, and come back if the Soviets go to war with us." if ex else ""))
    y += 40
import man_sites as SI
mp, mh = MAP.gui(props["MAN_security_board"], trig["MAN_security_board"], loc, 10, y + 4, NL)
b += mp
y += mh + 10
pv, y = SI.sec_gui(T, I, B, props["MAN_security_board"], trig["MAN_security_board"], eff["MAN_security_board"], loc, y + 2)
b += pv
SEC_H = y + 6
GUI += W("MAN_security_board", SEC_H, b) + "}\n"
wr("interface/MAN_systems.gui", GUI)
loc("MAN_SB_TITLE", "Public Security in Manchukuo")
loc("MAN_SB_AVG_L", "Average banditry")
loc("MAN_SB_AVG_V", "[?MAN_bandit_avg|0]")
loc("MAN_SB_GRID_H", "§gBanditry by province§!")
loc("MAN_SB_HELP_TT", "§YPublic Security§!" + NL + "Every province has a banditry level from 0 to 100. Above 25, 45, 65 and 85 it imposes growing penalties to resources, construction and building slots there." +
    NL + "Banditry also scales down the Plan's project output in that province and drains Kwantung Army patience." +
    NL + "It rises from local grievances and the Route Armies, and falls with garrisons, blockhouses, Collective Hamlets, informant networks and punitive sweeps.")

sg = "scripted_gui = {\n"
for gname in ("MAN_plan_board", "MAN_politics_board", "MAN_security_board"):
    sg += f"\t{gname} = {{\n\t\tcontext_type = decision_category\n\t\twindow_name = \"{gname}\"\n"
    sg += "\t\tproperties = {\n" + "".join(f"\t\t\t{e} = {{ frame = {v} }}\n" for e, v in props[gname]) + "\t\t}\n"
    if trig[gname]: sg += "\t\ttriggers = {\n" + "".join(f"\t\t\t{t}\n" for t in trig[gname]) + "\t\t}\n"
    if eff[gname]: sg += "\t\teffects = {\n" + "".join(f"\t\t\t{t}\n" for t in eff[gname]) + "\t\t}\n"
    sg += "\t}\n"
sg += "}\n"
wr("common/scripted_guis/MAN_systems_guis.txt", sg)

# ------------------------------------------------------------------------------------------------ scripted loc
def DT(name, cases):
    s = f"defined_text = {{\n\tname = {name}\n"
    for trg, key, txt in cases:
        s += "\ttext = {\n" + (f"\t\ttrigger = {{ {trg} }}\n" if trg else "") + f"\t\tlocalization_key = {key}\n\t}}\n"
        loc(key, txt)
    return s + "}\n"
SL = "# Manchukuo systems scripted loc\n"
SL += DT("GetMANPlanTitle", [
    ("check_variable = { MAN_plan_stage < 0.5 }", "MAN_PLT_0", "§YPreparatory Survey§!: the Plan has not yet been proclaimed"),
    ("has_country_flag = MAN_second_fyp_complete", "MAN_PLT_DONE2", "§GThe Second Plan is concluded§!"),
    ("has_country_flag = MAN_first_fyp_complete check_variable = { MAN_plan_stage < 2.5 }", "MAN_PLT_DONE1", "§GThe First Plan is concluded§!: the planners draft its successor"),
    ("check_variable = { MAN_plan_stage = 1 }", "MAN_PLT_1", "§YFirst Five-Year Plan§!: year [?MAN_plan_year|0] of 5"),
    ("check_variable = { MAN_plan_stage = 2 }", "MAN_PLT_2", "§YRevised First Five-Year Plan§!: year [?MAN_plan_year|0] of 5"),
    ("check_variable = { MAN_plan_stage = 3 }", "MAN_PLT_3", "§YSecond Five-Year Plan§!: year [?MAN_plan_year|0] of 5"),
    ("", "MAN_PLT_4", "§YWartime Emergency Plan§!: year [?MAN_plan_year|0] of 5"),
])
SL += DT("GetMANPlanReview", [
    ("has_country_flag = MAN_review_running has_country_flag = MAN_review_lock", "MAN_PLR_LOCK", "Annual review needs §Y[?MAN_review_need|0]%§! total fulfilment. The books close late in the plan year."),
    ("has_country_flag = MAN_review_running", "MAN_PLR_OPEN", "Annual review needs §Y[?MAN_review_need|0]%§!: §Gthe books are open§!, reach it to pass early."),
    ("", "MAN_PLR_NONE", "§gNo annual review in progress.§!"),
])
for k in BROKERS:
    cases = []
    if k in MS.VACANT: cases.append((f"check_variable = {{ MAN_h_{k} < 0.5 }}", f"MAN_HOLD_{k}_0", f"§g{MS.VACANT[k]}§!"))
    for i, nm in enumerate(MS.HOLDERS[k], 1):
        last = i == len(MS.HOLDERS[k])
        cases.append(("" if last else f"check_variable = {{ MAN_h_{k} = {i} }}", f"MAN_HOLD_{k}_{i}", nm))
    SL += DT(f"GetMANHolder_{k}", cases)
    SL += DT(f"GetMANReq_{k}", [
        (f"has_country_flag = MAN_req_{k}_a", f"MAN_REQL_{k}_a", f"§YRequest:§! {MS.REQ[k][0]}"),
        (f"has_country_flag = MAN_req_{k}_b", f"MAN_REQL_{k}_b", f"§YRequest:§! {MS.REQ[k][5]}"),
        (f"check_variable = {{ MAN_h_{k} < 0.5 }}", f"MAN_REQL_{k}_x", ""),
        ("", f"MAN_REQL_{k}_n", "§gNo standing request§!"),
    ])
SL += DT("GetMANPatience", [
    ("check_variable = { MAN_kw_pat < 15 }", "MAN_PAT_0", "§RThe Kwantung Army is preparing to take matters into its own hands§!"),
    ("check_variable = { MAN_kw_pat < 35 }", "MAN_PAT_1", "§OThe staff in Hsinking is losing patience with the government§!"),
    ("check_variable = { MAN_kw_pat < 65 }", "MAN_PAT_2", "§YThe Kwantung Army is watching closely§!"),
    ("check_variable = { MAN_kw_pat < 85 }", "MAN_PAT_3", "§GThe Kwantung Army trusts Hsinking to deliver§!"),
    ("", "MAN_PAT_4", "§GManchukuo is a trusted partner of the Empire§!"),
])
SL += DT("GetMANSecurity", [
    ("check_variable = { MAN_bandit_avg < 15 }", "MAN_SEC_0", "§GThe countryside is pacified§!"),
    ("check_variable = { MAN_bandit_avg < 30 }", "MAN_SEC_1", "§YScattered bands still raid isolated villages and rail lines§!"),
    ("check_variable = { MAN_bandit_avg < 50 }", "MAN_SEC_2", "§OWhole districts answer to the guerrillas after dark§!"),
    ("", "MAN_SEC_3", "§RThe mountains belong to the United Army§!"),
])
for n in MS.BANDS:
    SL += DT(f"GetMANBandSt_{n}", [
        (f"has_country_flag = MAN_band{n}_dead", f"MAN_BST_{n}_dead", "§GDestroyed§!"),
        (f"has_country_flag = MAN_band{n}_exile", f"MAN_BST_{n}_exile", "§YRetreated into the Soviet Union§!"),
        (f"check_variable = {{ MAN_band{n} > 69.99 }}", f"MAN_BST_{n}_3", "§RStrong and recruiting in the villages§!"),
        (f"check_variable = {{ MAN_band{n} > 39.99 }}", f"MAN_BST_{n}_2", "§OActive, raiding mines and railways§!"),
        ("", f"MAN_BST_{n}_1", "§YHunted, short of food and men§!"),
    ])
SL += SI.prov_sl(DT)
SL += SI.sec_sl(DT)
wr("common/scripted_localisation/MAN_systems_loc.txt", SL)

# ------------------------------------------------------------------------------------------------ events
EV = "add_namespace = man_sys\n\n"
def ev(eid, title, desc, pic, opts, imm="", hidden=False):
    global EV
    loc(f"man_sys.{eid}.t", title); loc(f"man_sys.{eid}.d", desc)
    s = f"country_event = {{\n\tid = man_sys.{eid}\n\ttitle = man_sys.{eid}.t\n\tdesc = man_sys.{eid}.d\n\tpicture = {pic}\n\tis_triggered_only = yes\n"
    if imm: s += "\timmediate = {\n" + ind(imm, 2) + "\t}\n"
    for i, (name, body, ai) in enumerate(opts):
        key = f"man_sys.{eid}.{'abcd'[i]}"; loc(key, name)
        s += f"\toption = {{\n\t\tname = {key}\n" + (f"\t\tai_chance = {{ factor = {ai} }}\n" if ai is not None else "") + ind(body, 2) + "\t}\n"
    EV += s + "}\n\n"

ev(2, "Annual Review: Quotas Met", "The Planning Board's auditors sign off the year's deliveries. Furnaces, pits and shops have met their targets, and the Kwantung Army's economic staff sends its compliments to Hsinking.",
   "GFX_report_event_generic_factory",
   [("The Plan marches on.",
     "add_to_variable = { MAN_kw_pat = 8 }\ncustom_effect_tooltip = MAN_tt_pat_8\nadd_to_variable = { MAN_fav_ind = 8 }\ncustom_effect_tooltip = MAN_tt_fav_ind_8\nadd_political_power = 40\n"
     "custom_effect_tooltip = MAN_eco_spirit_changed_tt\nadd_to_variable = { var = MAN_behemoth_production_factory_max_efficiency_factor value = 0.01 tooltip = production_factory_max_efficiency_factor_tt }\n"
     "set_temp_variable = { MAN_x = MAN_review_need }\nadd_to_temp_variable = { MAN_x = 19.99 }\nif = {\n\tlimit = { check_variable = { MAN_plan_pct > MAN_x } }\n\tcustom_effect_tooltip = MAN_tt_overfulfil\n\tadd_to_variable = { var = MAN_behemoth_industrial_capacity_factory value = 0.01 tooltip = industrial_capacity_factory_tt }\n}\n"
     "hidden_effect = { force_update_dynamic_modifier = yes }\nMAN_plan_next_year = yes\n", None)])
ev(3, "Annual Review: Shortfall", "The auditors' figures do not add up. Steel, coal and machinery have fallen short of the year's targets and the Kwantung Army wants to know why. Someone will have to answer for it.",
   "GFX_report_event_generic_read_write",
   [("Purge the planning section.", "add_to_variable = { MAN_fav_ind = -12 }\ncustom_effect_tooltip = MAN_tt_fav_ind_m12\nadd_to_variable = { MAN_kw_pat = 4 }\ncustom_effect_tooltip = MAN_tt_pat_4\nadd_stability = -0.02\nMAN_plan_next_year = yes\n", 40),
    ("Blame bandit sabotage.", "add_to_variable = { MAN_fav_kw = 6 }\ncustom_effect_tooltip = MAN_tt_fav_kw_6\nadd_to_variable = { MAN_kw_pat = -4 }\ncustom_effect_tooltip = MAN_tt_pat_m4\nMAN_plan_next_year = yes\n", 40),
    ("Ask our friends in Tokyo to intercede.", "trigger = { has_country_flag = MAN_has_patron }\nadd_to_variable = { MAN_kw_pat = 6 }\ncustom_effect_tooltip = MAN_tt_pat_6\nadd_political_power = -30\nMAN_plan_next_year = yes\n", 20)])
ev(4, "The First Plan Concludes", "Five years of furnaces, pits and dams are tallied. Whether or not every target was met, the First Plan for Industrial Development has turned Manchuria into the Empire's arsenal on the continent, at a cost in lives the reports never print.",
   "GFX_report_event_generic_factory",
   [("Draft the Second Plan.",
     "if = {\n\tlimit = { check_variable = { MAN_plan_pct > 99.99 } }\n\tcustom_effect_tooltip = MAN_tt_plan_full\n\tadd_stability = 0.05\n\tadd_to_variable = { MAN_kw_pat = 10 }\n\tcustom_effect_tooltip = MAN_tt_pat_10\n"
     "\tcustom_effect_tooltip = MAN_eco_spirit_changed_tt\n\tadd_to_variable = { var = MAN_behemoth_industrial_capacity_factory value = 0.05 tooltip = industrial_capacity_factory_tt }\n\tadd_to_variable = { var = MAN_behemoth_production_factory_max_efficiency_factor value = 0.03 tooltip = production_factory_max_efficiency_factor_tt }\n}\n"
     "else_if = {\n\tlimit = { check_variable = { MAN_plan_pct > 69.99 } }\n\tcustom_effect_tooltip = MAN_tt_plan_part\n\tcustom_effect_tooltip = MAN_eco_spirit_changed_tt\n\tadd_to_variable = { var = MAN_behemoth_industrial_capacity_factory value = 0.03 tooltip = industrial_capacity_factory_tt }\n}\n"
     "else = {\n\tcustom_effect_tooltip = MAN_tt_plan_fail\n\tadd_stability = -0.06\n\tadd_to_variable = { MAN_kw_pat = -10 }\n\tcustom_effect_tooltip = MAN_tt_pat_m10\n}\n"
     "hidden_effect = { force_update_dynamic_modifier = yes }\ncustom_effect_tooltip = MAN_tt_second_plan_focus\n", None)])
ev(5, "The Second Plan Concludes", "The Second Plan ends in the middle of the Empire's great war. Manchuria's mills and arsenals feed fronts from the Amur to the South Seas.",
   "GFX_report_event_generic_factory",
   [("The Behemoth of the East stands.",
     "if = {\n\tlimit = { check_variable = { MAN_plan_pct > 99.99 } }\n\tcustom_effect_tooltip = MAN_tt_plan_full\n\tadd_war_support = 0.05\n\tcustom_effect_tooltip = MAN_eco_spirit_changed_tt\n\tadd_to_variable = { var = MAN_behemoth_industrial_capacity_factory value = 0.06 tooltip = industrial_capacity_factory_tt }\n}\n"
     "else = {\n\tcustom_effect_tooltip = MAN_eco_spirit_changed_tt\n\tadd_to_variable = { var = MAN_behemoth_industrial_capacity_factory value = 0.03 tooltip = industrial_capacity_factory_tt }\n}\nhidden_effect = { force_update_dynamic_modifier = yes }\n", None)])
DEPTXT = {
    "itagaki": ("Itagaki Leaves the Kwantung Army", "Itagaki Seishiro, architect of the Mukden Incident and the Kwantung Army's long-serving chief of staff, hands over to the former head of the Kwantung Kempeitai, Tojo Hideki. Itagaki is bound for a division command and, it is said, the War Ministry."),
    "tojo": ("Tojo Recalled to Tokyo", "Tojo Hideki, 'the Razor', leaves Hsinking to become Vice-Minister of War. His successor as chief of staff is Isogai Rensuke. Tojo's friends in Manchuria expect great things of him."),
    "matsuoka": ("Matsuoka Leaves Mantetsu", "Matsuoka Yosuke resigns the presidency of the South Manchuria Railway Company. Omura Takuichi takes over a railway already stripped of its heavy industry. Matsuoka's ambitions now lie with the Foreign Ministry."),
    "kishi": ("Kishi Returns to Tokyo", "Kishi Nobusuke, the reform bureaucrat who drove the Plan, goes home to the Ministry of Commerce and Industry, leaving the ministry to his protege Shiina Etsusaburo. 'Manchuria is my work of art,' he tells his staff."),
    "hoshino": ("Hoshino Joins the Planning Board", "Hoshino Naoki leaves the General Affairs Board to head the Cabinet Planning Board in Tokyo. Takebe Rokuzo becomes Director of General Affairs."),
    "ayukawa": ("Ayukawa Resigns from Mangyo", "Frustrated by army interference and the failure to win American capital, Ayukawa Yoshisuke steps down as president of Mangyo. Takasaki Tatsunosuke succeeds him."),
}
for (eid, k, h, d, who, tc, amt, extra) in DEP:
    t, ds = DEPTXT[who]
    ev(eid, t, ds, "GFX_report_event_japanese_officers", [("A new man in the post.", f"MAN_depart_{who} = yes\n", None)])
PATRON = {"itagaki": ("organisation", "MAN_tc_kw", "Army Organisation +2%"), "tojo": ("organisation", "MAN_tc_kw", "Army Organisation +3%"),
          "matsuoka": ("pp", "MAN_tc_gab", "Political Power Gain +5%"), "kishi": ("build", "MAN_tc_ind", "Construction Speed +5% and Planning efficiency +5%"),
          "hoshino": ("pp", "MAN_tc_gab", "Political Power Gain +5%"), "ayukawa": ("output", "MAN_tc_mgy", "Factory Output +3%")}
NAMES = {"itagaki": "Itagaki Seishiro", "tojo": "Tojo Hideki", "matsuoka": "Matsuoka Yosuke", "kishi": "Kishi Nobusuke", "hoshino": "Hoshino Naoki", "ayukawa": "Ayukawa Yoshisuke"}
for who, (_, _, txt) in PATRON.items():
    loc(f"MAN_tt_patron_{who}", f"§G{NAMES[who]} remains a patron of Manchukuo in Tokyo§!: The Hsinking Bureaucracy gains §G{txt}§! permanently.")
    loc(f"MAN_tt_enemy_{who}", f"§R{NAMES[who]} leaves as an enemy of Hsinking§!: The Hsinking Bureaucracy permanently loses half of what a patron would have given ({txt}).")
loc("MAN_tt_neutral_departure", "He leaves on indifferent terms. Favour of 60 or more would have made him a patron; 30 or less an enemy.")
loc("MAN_tt_new_holder", "The successor starts at §Y45§! favour.")
loc("MAN_tt_ayukawa_arrives", "§YAyukawa Yoshisuke§! of Nissan takes the Mangyo seat in the Hsinking Bureaucracy (favour 45).")
loc("MAN_tt_kishi_arrives", "§YKishi Nobusuke§! takes the Ministry of Industry seat in the Hsinking Bureaucracy (favour 55).")

ev(20, "Internal Guidance", "The Kwantung Army's staff has lost patience with Hsinking. A colonel arrives at the State Council with a list of ministers to be dismissed and a draft of the next budget, already approved by the army.",
   "GFX_report_event_japanese_officers",
   [("Submit to the army's guidance.", "add_political_power = -50\nadd_to_variable = { MAN_kw_pat = 30 }\ncustom_effect_tooltip = MAN_tt_pat_30\nadd_power_balance_value = { id = MAN_racial_harmony value = 0.1 }\nadd_to_variable = { MAN_fav_gab = -10 }\ncustom_effect_tooltip = MAN_tt_fav_gab_m10\nhidden_effect = { MAN_pol_compute = yes MAN_ui_refresh = yes }\n", 60),
    ("Appeal to our patrons in Tokyo.", "trigger = { has_country_flag = MAN_has_patron }\nadd_political_power = -25\nadd_to_variable = { MAN_kw_pat = 20 }\ncustom_effect_tooltip = MAN_tt_pat_20\nhidden_effect = { MAN_pol_compute = yes MAN_ui_refresh = yes }\n", 30),
    ("Stall and delay.", "add_stability = -0.08\nadd_war_support = -0.03\nadd_to_variable = { MAN_kw_pat = 10 }\ncustom_effect_tooltip = MAN_tt_pat_10\nhidden_effect = { MAN_pol_compute = yes MAN_ui_refresh = yes }\n", 10)])
ev(21, "A Trusted Partner", "The Kwantung Army's commander praises Manchukuo's government as a model for the whole Co-Prosperity Sphere. The army hands over the management of several of its own arsenals and depots to Hsinking.",
   "GFX_report_event_generic_sign_treaty1",
   [("An honour for the Five Races.", "random_owned_controlled_state = {\n\tprioritize = { 716 715 328 }\n\tlimit = { " + MANCHURIA_TRIGGER + " }\n\tadd_extra_state_shared_building_slots = 2\n\tadd_building_construction = { type = arms_factory level = 2 instant_build = yes }\n}\nadd_political_power = 50\n", None)])
BDEAD = {1: ("The Death of Yang Jingyu", "Betrayed by a subordinate and run down in the snow near Mengjiang, Yang Jingyu fights alone to the end. The Japanese surgeons who open his stomach find only bark, grass roots and cotton padding. The First Route Army is finished as an organised force."),
         2: ("The Second Route Army Breaks", "Zhou Baozhong's columns are cut to pieces in the forests of eastern Kirin. The survivors scatter into small groups that can no longer hold territory."),
         3: ("Zhao Shangzhi Falls", "Zhao Shangzhi is lured into an ambush by an informer and mortally wounded. His Third Route Army melts away into the northern forests.")}
for n, (t, ds) in BDEAD.items():
    ev(29 + n, t, ds, "GFX_report_event_japan_army_mountainside",
       [("The mountains fall quiet.", f"add_to_variable = {{ MAN_kw_pat = 10 }}\ncustom_effect_tooltip = MAN_tt_pat_10\nadd_to_variable = {{ MAN_fav_kw = 10 }}\ncustom_effect_tooltip = MAN_tt_fav_kw_10\n{MS.HOME[n]} = {{ subtract_from_variable = {{ MAN_bandit = 15 }} clamp_variable = {{ var = MAN_bandit min = 0 max = 100 }} }}\nhidden_effect = {{ MAN_sec_refresh = yes MAN_ui_refresh = yes }}\n", None)])
for n in (2, 3):
    bn = MS.BANDS[n][0]
    ev(31 + n, f"The {bn} Crosses the Amur", f"Broken and starving, the remnants of the {bn} slip across the frozen Amur into Soviet territory. Moscow will feed them, train them and keep them for a day when they might be useful.",
       "GFX_report_event_chinese_soldiers_fighting",
       [("Good riddance.", f"custom_effect_tooltip = MAN_tt_exile\nhidden_effect = {{ MAN_sec_refresh = yes MAN_ui_refresh = yes }}\n", None)])
ev(35, "The Exiles Return", "The Chinese and Korean partisans who fled to the Soviet Union return, retrained as a Red Army brigade with radios, explosives and Soviet officers. Their old base areas rise with them.",
   "GFX_report_event_chinese_soldiers_fighting",
   [("Hunt them down again.", "every_owned_state = {\n\tlimit = { OR = { state = 714 state = 717 state = 328 } }\n\tadd_to_variable = { MAN_bandit = 15 }\n\tclamp_variable = { var = MAN_bandit min = 0 max = 100 }\n}\nhidden_effect = { MAN_sec_refresh = yes MAN_ui_refresh = yes }\n", None)])
wr("events/MAN_systems_events.txt", EV)
loc("MAN_tt_exile", "The Route Army no longer raids Manchukuo, but it may return if the Soviet Union goes to war with us or with Japan.")
loc("MAN_tt_overfulfil", "§GOverfulfilment bonus§! (20 points or more above the target):")
loc("MAN_tt_plan_full", "§GThe Plan was fulfilled in full.§!")
loc("MAN_tt_plan_part", "§YThe Plan was largely fulfilled (70% or more).§!")
loc("MAN_tt_plan_fail", "§RThe Plan fell badly short.§!")
loc("MAN_tt_second_plan_focus", "The §YSecond Five-Year Plan§! focus can now be taken.")
loc("MAN_mega_final_tt", "§1Final stage of the megaproject:§!")
loc("MAN_tt_colony", "Labour income: §G+0.25k§! a week. Banditry in the province: §R+6§!, and a §Rgrievance§! for 180 days.")
loc("MAN_tt_sweep", "Banditry in the province: §G-10 to -20§! (more with Kwantung Army Staff favour, ×1.5 with an informant network). The local Route Army loses §G6§! strength. 30% chance of reprisals causing a grievance.")
loc("MAN_tt_reprisal", "§RReprisals against villagers leave a grievance in the province.§!")
loc("MAN_tt_hamlets", "Permanently §G-0.25§! weekly banditry growth in the province. The local Route Army loses §G10§! strength.")
loc("MAN_tt_blockhouses", "Permanently §G-0.10§! weekly banditry growth in the province.")
loc("MAN_tt_informants", "For 180 days: §G-0.15§! weekly banditry growth, and Punitive Sweeps here are §G50%§! stronger.")
loc("production_speed_synthetic_refinery_factor_tt", " $modifier_production_speed_synthetic_refinery_factor$: $RIGHT|+=%1$")

# ------------------------------------------------------------------------------------------------ on_actions + event hook
oa, ob = rd("common/on_actions/16_man_flavor_on_actions.txt")
if "MAN_systems_init" not in oa:
    oa = oa.replace("""				MAN = {
					if = {
						limit = { has_start_date < 1936.1.2 }""", """				MAN = {
					if = {
						limit = { NOT = { has_country_flag = MAN_sys_init } }
						MAN_systems_init = yes
					}
					if = {
						limit = { has_start_date < 1936.1.2 }""", 1)
    assert "MAN_systems_init" in oa
    oa = oa.rstrip().rstrip("}") + """
	# Manchukuo systems: Plan, Bureaucracy, Public Security
	on_weekly_MAN = {
		effect = {
			if = {
				limit = { has_country_flag = MAN_sys_init }
				MAN_sec_weekly = yes
				MAN_pol_weekly = yes
				MAN_plan_weekly = yes
				MAN_ui_refresh = yes
			}
		}
	}
	on_monthly_MAN = {
		effect = {
			if = {
				limit = { has_country_flag = MAN_sys_init }
				MAN_pol_monthly = yes
				MAN_sec_monthly = yes
			}
		}
	}
}
"""
    wr("common/on_actions/16_man_flavor_on_actions.txt", oa, ob)

# the Library: historical chains no longer fire at game start, and read on demand without stat effects
import man_library as LIB
oa, ob = rd("common/on_actions/16_man_flavor_on_actions.txt")
oa2 = LIB.clean_on_actions(oa)
if oa2 != oa: wr("common/on_actions/16_man_flavor_on_actions.txt", oa2, ob)

et, eb = rd("events/MAN_flavor_events.txt")
et = LIB.clean_events(et)
et = LIB.rehook_events(et)
for k_, v_ in LIB.REHOOK_LOC: loc(k_, v_)
et = et.replace("unlock_decision_category_tooltip = MAN_ayukawa_vs_matsuoka_category\n\t\t\tactivate_mission = MAN_bureaucratic_confrontation",
                "MAN_ayukawa_arrives = yes\n\t\t\tcustom_effect_tooltip = MAN_tt_mantetsu_question")
assert "MAN_bureaucratic_confrontation" not in et
wr("events/MAN_flavor_events.txt", et, eb)
loc("MAN_tt_mantetsu_question", "Starts §YThe Mantetsu Question§! in the Hsinking Bureaucracy: in a year, whichever of Mangyo and Mantetsu holds more favour wins.")

def build():
    return L
