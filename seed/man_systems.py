"""Manchukuo: three decision systems.
 1. The Industrial Development Plan (state zones, state projects, megaprojects, labour pool, quota tracks, annual reviews)
 2. The Hsinking Bureaucracy (five power brokers, favour, requests, Tokyo patrons, Kwantung Army patience)
 3. Public Security (state banditry, three Route Armies, sweeps / hamlets / blockhouses / informants / surrender)
"""
from man_common import *

L = []          # loc entries
def loc(k, v): L.append((k, v))

QN = dict(QUOTAS)
CC = set()      # custom cost texts needed (pp, labour, cp)
QT = set()      # quota award tooltips needed

def cc(pp=0, lab=0, cp=0):
    CC.add((pp, lab, cp))
    trig = []
    if pp: trig.append(f"has_political_power > {pp - 0.01:.2f}")
    if lab: trig.append(f"check_variable = {{ MAN_labour > {lab - 0.01:.2f} }}")
    if cp: trig.append(f"command_power > {cp - 0.01:.2f}")
    pay = []
    if pp: pay.append(f"add_political_power = -{pp}")
    if lab: pay.append(f"subtract_from_variable = {{ MAN_labour = {lab} }}")
    if cp: pay.append(f"add_command_power = -{cp}")
    return ("custom_cost_trigger = { " + " ".join(trig) + " }\n"
            f"custom_cost_text = MAN_cc_{pp}_{lab}_{cp}\n"), "\n".join(pay)

QB_CAP = 0.5   # stacked per-quota bonuses (focuses, advisors, concerns) count up to +50%
def award(k, n, scaled=True, in_state=False):
    """ROOT = MAN, FROM = the state (state-targeted decisions). in_state: run inside the state's own scope (megaprojects)."""
    QT.add((k, n, scaled))
    R = "ROOT." if in_state else ""
    s = f"custom_effect_tooltip = MAN_tt_q_{k}_{n}{'' if scaled else '_flat'}\n"
    s += f"set_temp_variable = {{ MAN_t = {n} }}\n"
    if scaled: s += f"multiply_temp_variable = {{ MAN_t = {'THIS' if in_state else 'FROM'}.MAN_eff }}\n"
    s += f"multiply_temp_variable = {{ MAN_t = {R}MAN_quota_mult }}\n"
    # per-quota bonus from focus choices (MAN_qb_<k>, 0 by default), capped
    s += (f"set_temp_variable = {{ MAN_t3 = {R}MAN_qb_{k} }}\nclamp_temp_variable = {{ var = MAN_t3 min = 0 max = {QB_CAP} }}\n"
          f"set_temp_variable = {{ MAN_t2 = MAN_t }}\nmultiply_temp_variable = {{ MAN_t2 = MAN_t3 }}\nadd_to_temp_variable = {{ MAN_t = MAN_t2 }}\n")
    s += f"add_to_variable = {{ {R}MAN_q_{k} = MAN_t }}\n"
    return s

# =====================================================================================================
# 1. THE INDUSTRIAL DEVELOPMENT PLAN
# =====================================================================================================
ZINFO = {  # zone: (name, icon, unlock flag, modifier lines, desc)
    "hi":   ("Heavy Industry Zone", "GFX_decision_generic_factory", "MAN_zone_unl_hi",
             ["state_production_speed_industrial_complex_factor = 0.15", "state_production_speed_arms_factory_factor = 0.15", "local_building_slots = 1"],
             "Concentrate furnaces, machine shops and arsenals here. Unlocks the province's industrial district sites and Production Runs for the Empire."),
    "min":  ("Mining District", "GFX_decision_generic_merge_plant_materiel", "MAN_zone_unl_min",
             ["local_resources_factor = 0.15"],
             "Open the coal seams and ore bodies the survey found. Unlocks the province's mine and colliery sites."),
    "pow":  ("Power and Water District", "GFX_decision_hol_inundate_water_lines", "MAN_zone_unl_pow",
             ["state_production_speed_buildings_factor = 0.10", "local_factory_energy_consumption = -0.10"],
             "Harness the rivers of the northeast. Unlocks Thermal Station and Transmission Grid projects, and the province's hydro and electro-chemical sites."),
    "set":  ("Settlement and Grain Zone", "GFX_decision_generic_colonial_administration", "MAN_zone_unl_set",
             ["recruitable_population_factor = 0.10"],
             "Open the land to pioneer colonies and the export trade. Unlocks Pioneer Colonies, export seasons and the province's trade sites. Dispossession breeds banditry."),
}
for z, (nm, _, _, mods, desc) in ZINFO.items():
    loc(f"MAN_zone_{z}", f"Designate {nm}")
    loc(f"MAN_zone_{z}_desc", desc + NL + NL + "Only surveyed provinces can be designated, and each may hold one designation. Designations are limited by the Plan's zone allowance.")
    loc(f"MAN_zone_{z}_dm", nm)

# projects: id, zone, name, icon, cap, days, pp, lab, civ, state rewards, quota awards[(k,n)], extra target, extra avail, desc
PROJ = [
    ("thermal", "pow", "Thermal Power Station", "GFX_decision_generic_electricity", 3, 90, 20, 15, 2,
     """if = { limit = { check_variable = { MAN_lv_thermal = 1 } } add_dynamic_modifier = { modifier = MAN_power_station_1 } }
else_if = { limit = { check_variable = { MAN_lv_thermal = 2 } } remove_dynamic_modifier = { modifier = MAN_power_station_1 } add_dynamic_modifier = { modifier = MAN_power_station_2 } }
else_if = { limit = { check_variable = { MAN_lv_thermal = 3 } } remove_dynamic_modifier = { modifier = MAN_power_station_2 } add_dynamic_modifier = { modifier = MAN_power_station_3 } }""", [("power", 14)], "", "",
     "A coal-fired station to feed the new works. Each station raises local construction speed."),
    ("grid", "pow", "Transmission Grid", "GFX_decision_generic_electricity", 1, 60, 15, 10, 1,
     "add_dynamic_modifier = { modifier = MAN_grid_dm }", [("power", 8), ("mach", 4)], "", "",
     "High-tension lines carrying current from the dams to the factories."),
    ("colony", "set", "Pioneer Colony", "GFX_decision_generic_colonial_administration", 3, 90, 15, 10, 1,
     """add_to_variable = { MAN_colony_g = 0.03 }
add_to_variable = { MAN_bandit = 6 }
set_state_flag = { flag = MAN_grievance days = 180 }""", [], "", "",
     "Settle a Japanese pioneer group (kaitakudan) on land bought cheap or simply taken from Chinese and Korean farmers. Adds to the labour pool for good, but the dispossessed go to the hills."),
]
PROJ_EXT = {"thermal": 2}   # extra per-province stages opened by the Second Five-Year Plan
for (pid, z, nm, icon, cap, days, pp, lab, civ, srew, aw, xt, xa, desc) in PROJ:
    loc(f"MAN_pj_{pid}", nm)
    ext = f" The §YSecond Five-Year Plan§! allows §Y{PROJ_EXT[pid]}§! more." if pid in PROJ_EXT else ""
    loc(f"MAN_pj_{pid}_desc", desc + NL + NL + f"Up to §Y{cap}§! per province.{ext} Quota output is scaled by the province's security (banditry) and by planning efficiency.")

def project(pid, z, nm, icon, cap, days, pp, lab, civ, srew, aw, xt, xa, desc, pri):
    cost, pay = cc(pp, lab)
    extra_rew = ""
    if pid == "colony":
        extra_rew = "add_to_variable = { MAN_labour_income = 0.25 }\ncustom_effect_tooltip = MAN_tt_colony\nadd_to_variable = { var = MAN_behemoth_consumer_goods_factor value = -0.005 tooltip = consumer_goods_expected_value_tt }\n"
    if pid == "rail":
        extra_rew = "add_to_variable = { MAN_rail_built = 1 }\n"
    s = f"""MAN_pj_{pid} = {{
	icon = {icon}
	priority = {pri}
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = MAN_plan_unlocked {xa} }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{
		FROM = {{
			is_owned_and_controlled_by = ROOT
			has_state_flag = MAN_zone_{z}
			OR = {{
				NOT = {{ check_variable = {{ MAN_lv_{pid} > {cap - 0.5} }} }}
				AND = {{
					ROOT = {{ has_country_flag = MAN_second_five_year_plan_active }}
					NOT = {{ check_variable = {{ MAN_lv_{pid} > {cap + PROJ_EXT.get(pid, 0) - 0.5} }} }}
				}}
			}}
			{xt}
		}}
	}}
	on_map_mode = map_and_decisions_view
	available = {{
		FROM = {{ NOT = {{ has_state_flag = MAN_busy }} }}
		check_variable = {{ MAN_proj_active < MAN_proj_slots }}
	}}
{ind(cost, 1)}	fire_only_once = no
	days_remove = {days}
	modifier = {{ civilian_factory_use = {civ} }}
	cancel_trigger = {{ FROM = {{ NOT = {{ is_owned_and_controlled_by = ROOT }} }} }}
	cancel_effect = {{
		subtract_from_variable = {{ MAN_proj_active = 1 }}
		FROM = {{ clr_state_flag = MAN_busy }}
	}}
	complete_effect = {{
{ind(pay, 2)}		add_to_variable = {{ MAN_proj_active = 1 }}
		FROM = {{ set_state_flag = MAN_busy }}
		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	remove_effect = {{
		subtract_from_variable = {{ MAN_proj_active = 1 }}
		add_to_variable = {{ MAN_proj_done = 1 }}
		FROM = {{
			clr_state_flag = MAN_busy
			add_to_variable = {{ MAN_lv_{pid} = 1 }}
{ind(srew, 3)}		}}
{ind(''.join(award(k, n) for k, n in aw) + extra_rew, 2) if (aw or extra_rew) else ''}		custom_effect_tooltip = MAN_behemoth_risk_tt
		hidden_effect = {{
			MAN_behemoth_accident_roll = yes
			MAN_plan_recalc = yes
			MAN_ui_refresh = yes
		}}
	}}
	ai_will_do = {{ base = 8 }}
}}
"""
    return s

def zone_dec(z, pri):
    nm, icon, unl, mods, desc = ZINFO[z]
    tl = "{ " + " ".join(map(str, ZONES[z])) + " }"
    return f"""MAN_zone_{z} = {{
	icon = {icon}
	priority = {pri}
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = {unl} }}
	state_target = yes
	targets = {tl}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT has_state_flag = MAN_surveyed NOT = {{ has_state_flag = MAN_zoned }} }} }}
	on_map_mode = map_and_decisions_view
	available = {{ check_variable = {{ MAN_zones_used < MAN_zone_cap }} }}
	cost = 25
	fire_only_once = no
	complete_effect = {{
		FROM = {{
			set_state_flag = MAN_zoned
			set_state_flag = MAN_zone_{z}
			add_dynamic_modifier = {{ modifier = MAN_zone_{z}_dm }}
		}}
		add_to_variable = {{ MAN_zones_used = 1 }}
		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 10 }}
}}
"""

UNZONE = f"""MAN_zone_clear = {{
	icon = GFX_decision_generic_break_treaty
	priority = 60
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = MAN_plan_unlocked }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT has_state_flag = MAN_zoned }} }}
	on_map_mode = map_and_decisions_view
	available = {{ FROM = {{ NOT = {{ has_state_flag = MAN_busy }} }} }}
	cost = 50
	fire_only_once = no
	complete_effect = {{
		FROM = {{
			clr_state_flag = MAN_zoned
{ind(''.join(f'clr_state_flag = MAN_zone_{z}' + chr(10) + f'remove_dynamic_modifier = {{ modifier = MAN_zone_{z}_dm }}' + chr(10) for z in ZINFO), 3)}		}}
		subtract_from_variable = {{ MAN_zones_used = 1 }}
		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 0 }}
}}
"""
loc("MAN_zone_clear", "Lift Development Designation")
loc("MAN_zone_clear_desc", "Release the province from its current designation so it can be re-zoned. Completed projects stay built.")

# megaprojects: id, state, name, icon, stages, days, pp, lab, civ, focus, per-stage rewards (state-scope, root-scope), final rewards
MEGA = [
    ("showa", 716, "Expand the Showa Steel Works", "GFX_decision_steel", 3, 150, 40, 30, 3, "MAN_eco_showa_steel",
     "add_extra_state_shared_building_slots = 2\nadd_building_construction = { type = industrial_complex level = 2 instant_build = yes }\nadd_resource = { type = steel amount = 60 }",
     [("steel", 20)],
     "custom_effect_tooltip = MAN_eco_spirit_changed_tt\nadd_to_variable = { var = MAN_behemoth_industrial_capacity_factory value = 0.04 tooltip = industrial_capacity_factory_tt }",
     "The Showa Steel Works at Anshan is the heart of Manchurian heavy industry. Each stage adds furnaces, rolling mills and coke ovens."),
    ("fengman", 328, "Build the Fengman Dam", "GFX_decision_hol_inundate_water_lines", 3, 180, 40, 40, 3, "MAN_eco_fengman_dam",
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = industrial_complex level = 1 instant_build = yes }",
     [("power", 12)],
     "328 = { add_building_construction = { type = dam level = 1 instant_build = yes province = { id = 946 } } }\n"
     + award("power", 14, scaled=False),
     "A concrete wall across the Sungari above Kirin, the largest dam in Asia. Tens of thousands of labourers will pour it."),
    ("supung", 716, "Build the Supung Dam", "GFX_decision_hol_inundate_water_lines", 2, 180, 50, 40, 3, "MAN_eco_supung_dam",
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = industrial_complex level = 1 instant_build = yes }",
     [("power", 14)],
     "716 = { add_building_construction = { type = dam level = 1 instant_build = yes province = { id = 836 } } }\n"
     + award("power", 14, scaled=False) + "JAP = { add_political_power = 25 }",
     "A joint project with the Government-General of Korea to dam the Yalu. Its turbines will light both banks of the river."),
    ("kirin_fuel", 328, "Kirin Synthetic Fuel Works", "GFX_decision_oil", 2, 160, 40, 30, 3, "MAN_eco_synthetic_fuel",
     "add_extra_state_shared_building_slots = 2\nadd_building_construction = { type = synthetic_refinery level = 2 instant_build = yes }",
     [("coal", 15)],
     "custom_effect_tooltip = MAN_eco_spirit_changed_tt\nadd_to_variable = { var = MAN_behemoth_production_speed_synthetic_refinery_factor value = 0.15 tooltip = production_speed_synthetic_refinery_factor_tt }",
     "Coal hydrogenation on the German model at Kirin, meant to free the Empire from American oil."),
    ("mamc", 716, "Manchuria Aircraft Works", "GFX_decision_generic_merge_plant_aircraft", 2, 150, 40, 30, 3, "MAN_eco_manshu_hikoki",
     "add_extra_state_shared_building_slots = 3\nadd_building_construction = { type = arms_factory level = 3 instant_build = yes }",
     [("mach", 18)],
     "add_tech_bonus = { name = MAN_mega_mamc bonus = 1.0 uses = 2 category = air_equipment }",
     "Manshu Hikoki at Mukden and Harbin, assembling Nakajima and Tachikawa designs for the Kwantung Army air arm."),
    ("arsenal", 716, "The Mukden Arsenal", "GFX_decision_generic_factory", 2, 150, 40, 30, 3, "MAN_eco_mukden_arsenal",
     "add_extra_state_shared_building_slots = 2\nadd_building_construction = { type = arms_factory level = 2 instant_build = yes }",
     [("mach", 15)],
     "add_tech_bonus = { name = MAN_mega_arsenal bonus = 1.0 uses = 2 category = infantry_weapons }",
     "Zhang Zuolin's old arsenal, the largest in China, retooled for Japanese patterns."),
]
# Second Five-Year Plan expansions: extra stages (quota only, no new buildings) opened by the Second Plan focus
MEGA_EXT = {"showa": 2, "kirin_fuel": 1}
MEGA_UNSCALED = {"fengman", "supung"}   # dams are heavily guarded fixed works: their power output ignores banditry
for (mid, sid, nm, icon, st, days, pp, lab, civ, foc, srew, aw, fin, desc) in MEGA:
    loc(f"MAN_mega_{mid}", f"{nm} (stage [?MAN_mega_{mid}_n|0]/[?MAN_megacap_{mid}|0])")
    ext = f" The §YSecond Five-Year Plan§! adds §1{MEGA_EXT[mid]}§! expansion stage{'s' if MEGA_EXT[mid] > 1 else ''} (quota only)." if mid in MEGA_EXT else ""
    sc = " Its output is §Gnot§! affected by §Obanditry§!." if mid in MEGA_UNSCALED else " Output is scaled by the province's §Osecurity§!."
    loc(f"MAN_mega_{mid}_desc", desc + NL + NL + f"§1Megaproject§! in §C{SNAME[sid]}§!: §1{st}§! stages. Completing the final stage grants a §1lasting bonus§!.{sc}{ext}")

def mega(mid, sid, nm, icon, st, days, pp, lab, civ, foc, srew, aw, fin, desc, pri):
    cost, pay = cc(pp, lab)
    aws = "".join(award(k, n, scaled=mid not in MEGA_UNSCALED, in_state=True) for k, n in aw)
    srew = f"if = {{\n\tlimit = {{ ROOT = {{ check_variable = {{ MAN_mega_{mid}_n < {st + 0.5} }} }} }}\n" + ind(srew, 1) + "}\n"
    return f"""MAN_mega_{mid} = {{
	icon = {icon}
	priority = {pri}
	allowed = {{ original_tag = MAN }}
	visible = {{
		has_completed_focus = {foc}
		check_variable = {{ MAN_mega_{mid}_n < MAN_megacap_{mid} }}
	}}
	highlight_states = {{ highlight_state_targets = {{ state = {sid} }} }}
	available = {{
		{sid} = {{ is_owned_and_controlled_by = ROOT }}
	}}
{ind(cost, 1)}	fire_only_once = no
	days_remove = {days}
	modifier = {{ civilian_factory_use = {civ} }}
	complete_effect = {{
{ind(pay, 2)}		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	remove_effect = {{
		add_to_variable = {{ MAN_mega_{mid}_n = 1 }}
		{sid} = {{
{ind(srew, 3)}{ind(aws, 3)}		}}
		if = {{
			limit = {{ check_variable = {{ MAN_mega_{mid}_n > {st - 0.5} }} check_variable = {{ MAN_mega_{mid}_n < {st + 0.5} }} }}
			custom_effect_tooltip = MAN_mega_final_tt
{ind(fin, 3)}			hidden_effect = {{ force_update_dynamic_modifier = yes }}
		}}
		custom_effect_tooltip = MAN_behemoth_risk_tt
		hidden_effect = {{
			MAN_behemoth_accident_roll = yes
			MAN_plan_recalc = yes
			MAN_ui_refresh = yes
		}}
	}}
	ai_will_do = {{ base = 15 }}
}}
"""

LABOUR_DEC = """MAN_lab_concordia = {
	icon = GFX_decision_generic_civil_support
	priority = 70
	allowed = { original_tag = MAN }
	visible = { has_country_flag = MAN_plan_unlocked }
	cost = 10
	days_re_enable = 90
	fire_only_once = no
	complete_effect = {
		add_to_variable = { MAN_labour = 12 }
		custom_effect_tooltip = MAN_tt_labour_12
		add_to_variable = { MAN_levy = 10 }
		custom_effect_tooltip = MAN_tt_levy_10
		hidden_effect = { force_update_dynamic_modifier = yes MAN_ui_refresh = yes }
	}
	ai_will_do = {
		base = 5
		modifier = { factor = 0 OR = { has_stability < 0.25 check_variable = { MAN_levy > 20 } } }
	}
}
MAN_lab_daito = {
	icon = GFX_decision_generic_construction
	priority = 71
	allowed = { original_tag = MAN }
	visible = { has_completed_focus = MAN_eco_labour_agency }
	cost = 25
	days_remove = 30
	days_re_enable = 60
	fire_only_once = no
	remove_effect = {
		add_to_variable = { MAN_labour = 25 }
		custom_effect_tooltip = MAN_tt_labour_25
		add_to_variable = { MAN_levy = 15 }
		custom_effect_tooltip = MAN_tt_levy_15
		hidden_effect = { force_update_dynamic_modifier = yes MAN_ui_refresh = yes }
	}
	ai_will_do = {
		base = 6
		modifier = { factor = 0 OR = { has_stability < 0.25 check_variable = { MAN_levy > 20 } } }
	}
}
MAN_lab_special = {
	icon = oppression
	priority = 69
	allowed = { original_tag = MAN }
	visible = {
		has_country_flag = MAN_plan_unlocked
		OR = { has_war_with = CHI JAP = { has_war_with = CHI } JAP = { has_war_with = PRC } }
	}
	cost = 0
	days_re_enable = 120
	fire_only_once = no
	complete_effect = {
		add_to_variable = { MAN_labour = 30 }
		custom_effect_tooltip = MAN_tt_labour_30
		add_stability = -0.03
		add_to_variable = { MAN_levy = 25 }
		custom_effect_tooltip = MAN_tt_levy_25
		add_war_support = -0.01
		add_to_variable = { MAN_kw_pat = 3 }
		custom_effect_tooltip = MAN_tt_pat_3
		random_owned_controlled_state = {
			limit = { has_state_flag = MAN_zone_min }
			set_state_flag = { flag = MAN_grievance days = 180 }
		}
		hidden_effect = { force_update_dynamic_modifier = yes MAN_ui_refresh = yes }
	}
	ai_will_do = {
		base = 2
		modifier = { factor = 0 OR = { has_stability < 0.3 check_variable = { MAN_levy > 15 } } }
	}
}
"""
loc("MAN_lab_concordia", "Concordia Labour Service")
loc("MAN_lab_concordia_desc", "The Concordia Association calls out its youth and neighbourhood groups for a season of 'voluntary' labour on the Plan's sites.")
loc("MAN_lab_daito", "Daito Koshi Recruitment Drive")
loc("MAN_lab_daito_desc", "The Greater East Company sends its agents into Shandong and Hebei to sign up seasonal labourers with advances, promises and threats. Hundreds of thousands cross the Wall each spring.")
loc("MAN_lab_special", "Special Workers Programme")
loc("MAN_lab_special_desc", "Captured soldiers and rounded-up civilians from the China front are shipped north as 'special workers' for the mines. Death rates are appalling, escapes are frequent, and the Kwantung Army approves.")

PLAN_REVIEW = """MAN_plan_review = {
	icon = generic_industry
	priority = 300
	allowed = { original_tag = MAN }
	activation = { has_country_flag = MAN_review_running }
	available = {
		NOT = { has_country_flag = MAN_review_lock }
		check_variable = { MAN_plan_pct > MAN_review_need_m }
	}
	cancel_trigger = { NOT = { has_country_flag = MAN_review_running } }
	days_mission_timeout = 365
	fire_only_once = no
	is_good = yes
	complete_effect = {
		clr_country_flag = MAN_review_running
		country_event = { id = man_sys.2 hours = 6 }
	}
	timeout_effect = {
		clr_country_flag = MAN_review_running
		add_to_variable = { MAN_kw_pat = -8 }
		custom_effect_tooltip = MAN_tt_pat_m8
		country_event = { id = man_sys.3 hours = 6 }
	}
	ai_will_do = { base = 1 }
}
"""
loc("MAN_plan_review", "Annual Plan Review")
loc("MAN_plan_review_desc", "The Planning Board and the Kwantung Army staff audit this year's deliveries. Total plan fulfilment must reach §Y[?MAN_review_need|0]%§!. The review cannot close early in the first months of the plan year.")

# =====================================================================================================
# 2. THE HSINKING BUREAUCRACY
# =====================================================================================================
BK = {  # key: (institution, rival, modifier desc)
    "kw":  ("Kwantung Army Staff", "gab"),
    "gab": ("General Affairs Board", "kw"),
    "ind": ("Ministry of Industry", None),
    "mgy": ("Mangyo", "smr"),
    "smr": ("Mantetsu", "mgy"),
}
HOLDERS = {
    "kw":  ["Itagaki Seishiro", "Tojo Hideki", "Isogai Rensuke"],
    "gab": ["Hoshino Naoki", "Takebe Rokuzo"],
    "ind": ["Kishi Nobusuke", "Shiina Etsusaburo"],
    "mgy": ["Ayukawa Yoshisuke", "Takasaki Tatsunosuke"],
    "smr": ["Matsuoka Yosuke", "Omura Takuichi"],
}
VACANT = {"ind": "Vacant: awaiting a Tokyo bureaucrat", "mgy": "Not yet founded"}
REQ = {  # key: (a_name, a_desc, a_avail, a_target_set, a_complete_extra, b_name, b_desc, b_avail, b_target_set, b_complete_extra)
    "kw": ("Secure the Railway Zone", "The Kwantung Army wants average banditry pushed below §Y[?MAN_req_kw_t|0]§!.",
           "check_variable = { MAN_bandit_avg < MAN_req_kw_t }",
           "set_variable = { MAN_req_kw_t = MAN_bandit_avg }\nsubtract_from_variable = { MAN_req_kw_t = 6 }\nclamp_variable = { var = MAN_req_kw_t min = 5 max = 100 }", "",
           "Feed the Kwantung Army", "The Kwantung Army demands 1500 rifles from Manchurian arsenals. They will be taken the moment they are in store.",
           "has_equipment = { infantry_equipment > 1499 }", "",
           "send_equipment = { equipment = infantry_equipment amount = 1500 target = JAP }"),
    "gab": ("Fund the Concordia Budget", "The General Affairs Board needs the state's reserves: hold §Y120§! political power and it will draw 80.",
            "has_political_power > 119.99", "", "add_political_power = -80",
            "Clean the Ministries", "Hoshino's office wants order in the provinces before the next budget: reach §Y60%§! stability.",
            "has_stability > 0.6", "", ""),
    "ind": ("Meet the Steel Target", "The Ministry of Industry wants Iron and Steel fulfilment above §Y[?MAN_req_ind_t|0]%§!.",
            "check_variable = { MAN_pct_steel > MAN_req_ind_t }",
            "set_variable = { MAN_req_ind_t = MAN_pct_steel }\nadd_to_variable = { MAN_req_ind_t = 12 }\nclamp_variable = { var = MAN_req_ind_t min = 0 max = 99 }", "",
            "Zone New Ground", "The Ministry wants another province brought under a development designation (§Y[?MAN_req_ind_t|0]§! zones).",
            "check_variable = { MAN_zones_used > MAN_req_ind_m }",
            "set_variable = { MAN_req_ind_t = MAN_zones_used }\nadd_to_variable = { MAN_req_ind_t = 1 }\nset_variable = { MAN_req_ind_m = MAN_req_ind_t }\nsubtract_from_variable = { MAN_req_ind_m = 0.5 }", ""),
    "mgy": ("Machinery for Mangyo", "Ayukawa's holding company wants Machinery and Munitions fulfilment above §Y[?MAN_req_mgy_t|0]%§!.",
            "check_variable = { MAN_pct_mach > MAN_req_mgy_t }",
            "set_variable = { MAN_req_mgy_t = MAN_pct_mach }\nadd_to_variable = { MAN_req_mgy_t = 12 }\nclamp_variable = { var = MAN_req_mgy_t min = 0 max = 99 }", "",
            "A Free Hand for Mangyo", "Mangyo wants results it can show its shareholders: complete §Y[?MAN_req_mgy_t|0]§! plan projects in total.",
            "check_variable = { MAN_proj_done > MAN_req_mgy_m }",
            "set_variable = { MAN_req_mgy_t = MAN_proj_done }\nadd_to_variable = { MAN_req_mgy_t = 3 }\nset_variable = { MAN_req_mgy_m = MAN_req_mgy_t }\nsubtract_from_variable = { MAN_req_mgy_m = 0.5 }", ""),
    "smr": ("Lay More Track", "Mantetsu wants more track laid: §Y[?MAN_req_smr_t|0]§! railway lines or mine spurs in total.",
            "check_variable = { MAN_rail_built > MAN_req_smr_m }",
            "set_variable = { MAN_req_smr_t = MAN_rail_built }\nadd_to_variable = { MAN_req_smr_t = 1 }\nset_variable = { MAN_req_smr_m = MAN_req_smr_t }\nsubtract_from_variable = { MAN_req_smr_m = 0.5 }", "",
            "Coal for the Railways", "The railway's locomotives burn Fushun coal by the trainload: raise Coal and Liquid Fuel fulfilment above §Y[?MAN_req_smr_t|0]%§!.",
            "check_variable = { MAN_pct_coal > MAN_req_smr_t }",
            "set_variable = { MAN_req_smr_t = MAN_pct_coal }\nadd_to_variable = { MAN_req_smr_t = 12 }\nclamp_variable = { var = MAN_req_smr_t min = 0 max = 99 }", ""),
}

def req_missions():
    s = ""
    for k, r in REQ.items():
        for ab, (nm, desc, av, tgt, extra) in (("a", r[0:5]), ("b", r[5:10])):
            loc(f"MAN_req_{k}_{ab}", f"{BK[k][0]}: {nm}")
            loc(f"MAN_req_{k}_{ab}_desc", desc + NL + NL + "Success: §G+18 favour§!, §G+5 Kwantung patience§!, §G+25§! political power. Failure: §R-15 favour§!, §R-5 Kwantung patience§!.")
            loc(f"MAN_REQ_{k}_{ab}_LINE", f"§YRequest:§! {nm}")
            s += f"""MAN_req_{k}_{ab} = {{
	icon = GFX_decision_generic_political_discourse
	priority = 250
	allowed = {{ original_tag = MAN }}
	activation = {{ has_country_flag = MAN_req_{k}_{ab} }}
	available = {{ {av} }}
	cancel_trigger = {{ NOT = {{ has_country_flag = MAN_req_{k}_{ab} }} }}
	days_mission_timeout = 150
	fire_only_once = no
	is_good = yes
	complete_effect = {{
		clr_country_flag = MAN_req_{k}_{ab}
{ind(extra, 2) if extra else ''}		MAN_req_success_{k} = yes
	}}
	timeout_effect = {{
		clr_country_flag = MAN_req_{k}_{ab}
		MAN_req_fail_{k} = yes
	}}
	ai_will_do = {{ base = 1 }}
}}
"""
    return s

POL_DEC = """MAN_mantetsu_question = {
	icon = GFX_decision_category_MAN_second_fyp
	priority = 260
	allowed = { original_tag = MAN }
	activation = { has_country_flag = MAN_ayukawa_vs_matsuoka_flag }
	available = { always = no }
	cancel_trigger = { NOT = { has_country_flag = MAN_ayukawa_vs_matsuoka_flag } }
	days_mission_timeout = 180
	fire_only_once = yes
	is_good = no
	timeout_effect = {
		if = {
			limit = { check_variable = { MAN_fav_mgy > MAN_fav_smr } }
			country_event = { id = manchukou.127 hours = 6 }
			JAP = { country_event = { id = manchukou.127 hours = 6 } }
		}
		else = {
			country_event = { id = manchukou.132 hours = 6 }
			JAP = { country_event = { id = manchukou.132 hours = 6 } }
		}
	}
	ai_will_do = { base = 1 }
}
MAN_pol_concordia_rally = {
	icon = GFX_decision_generic_political_rally
	priority = 90
	allowed = { original_tag = MAN }
	cost = 25
	days_re_enable = 120
	fire_only_once = no
	complete_effect = {
		add_stability = 0.03
		add_war_support = 0.02
		add_to_variable = { MAN_levy = -8 }
		custom_effect_tooltip = MAN_tt_levy_m8
		add_to_variable = { MAN_kw_pat = 2 }
		custom_effect_tooltip = MAN_tt_pat_2
		hidden_effect = { MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 3 }
}
MAN_pol_imperial_tour = {
	icon = GFX_decision_generic_political_discourse
	priority = 91
	allowed = { original_tag = MAN }
	visible = { check_variable = { MAN_kw_pat < 70 } }
	cost = 50
	fire_only_once = yes
	days_remove = 30
	remove_effect = {
		add_stability = 0.05
		add_to_variable = { MAN_kw_pat = 15 }
		custom_effect_tooltip = MAN_tt_pat_15
		add_power_balance_value = { id = MAN_racial_harmony value = 0.05 }
		hidden_effect = { MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 2 }
}
MAN_pol_appeal_tokyo = {
	icon = GFX_decision_generic_political_address
	priority = 92
	allowed = { original_tag = MAN }
	visible = { has_country_flag = MAN_has_patron }
	cost = 50
	days_re_enable = 180
	fire_only_once = no
	complete_effect = {
		add_to_variable = { MAN_kw_pat = 15 }
		custom_effect_tooltip = MAN_tt_pat_15
		hidden_effect = { MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 2 }
}
MAN_pol_joint_council = {
	icon = GFX_decision_generic_political_rally
	priority = 93
	allowed = { original_tag = MAN }
	visible = { has_country_flag = MAN_pf_councils }
	cost = 40
	days_re_enable = 180
	fire_only_once = no
	complete_effect = {
		add_stability = 0.04
		add_to_variable = { MAN_fav_gab = 8 }
		custom_effect_tooltip = MAN_tt_fav_gab_8
		add_to_variable = { MAN_kw_pat = -3 }
		custom_effect_tooltip = MAN_tt_pat_m3
		add_power_balance_value = { id = MAN_racial_harmony value = -0.05 }
		hidden_effect = { MAN_pol_compute = yes MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 2 }
}
MAN_pol_guidance_directive = {
	icon = GFX_decision_generic_political_address
	priority = 94
	allowed = { original_tag = MAN }
	visible = { has_country_flag = MAN_pf_guidance }
	cost = 35
	days_re_enable = 120
	fire_only_once = no
	complete_effect = {
		add_stability = -0.03
		add_to_variable = { MAN_fav_kw = 10 }
		custom_effect_tooltip = MAN_tt_fav_kw_10
		add_to_variable = { MAN_kw_pat = 5 }
		custom_effect_tooltip = MAN_tt_pat_5
		add_to_variable = { MAN_fav_gab = -5 }
		custom_effect_tooltip = MAN_tt_fav_gab_m5
		add_power_balance_value = { id = MAN_racial_harmony value = 0.04 }
		hidden_effect = { MAN_pol_compute = yes MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 3 }
}
"""
loc("MAN_pol_joint_council", "Convene the Joint Council")
loc("MAN_pol_joint_council_desc", "Delegates of the five races meet in Hsinking as the Concordia Association's national Joint Council. It cannot pass laws, but its resolutions give the General Affairs Board a mandate the Kwantung Army staff cannot simply ignore.")
loc("MAN_pol_guidance_directive", "Issue an Internal Guidance Directive")
loc("MAN_pol_guidance_directive_desc", "The Fourth Section of the Kwantung Army staff sends Hsinking another set of 'suggestions'. The ministries will comply, and the vice-ministers will remember who wrote them.")
loc("MAN_mantetsu_question", "The Mantetsu Question")
loc("MAN_mantetsu_question_desc", "Ayukawa Yoshisuke wants Mantetsu's mines and mills folded into a new holding company; Matsuoka Yosuke will not see the railway carved up. When the year is out, whichever of §YMangyo§! and §YMantetsu§! holds the greater favour in Hsinking wins the argument.")
loc("MAN_pol_concordia_rally", "Concordia Association Rally")
loc("MAN_pol_concordia_rally_desc", "Flags of the five races, speeches on the Kingly Way, and a parade of youth corps before the Kwantung Army's observers.")
loc("MAN_pol_imperial_tour", "The Emperor Visits Tokyo")
loc("MAN_pol_imperial_tour_desc", "Puyi travels to Japan to pay his respects at Ise and returns with the sacred mirror for a new National Foundation Shrine in Hsinking. The Kwantung Army is delighted; the Emperor's Chinese subjects are not.")
loc("MAN_pol_appeal_tokyo", "Appeal to Our Friends in Tokyo")
loc("MAN_pol_appeal_tokyo_desc", "A former Hsinking man now sits in a Tokyo ministry. A quiet word from him calms the Kwantung Army staff.")

# =====================================================================================================
# 3. PUBLIC SECURITY
# =====================================================================================================
BANDS = {  # n: (name, leader, home states [(sid, coef)], exile_possible)
    1: ("First Route Army", "Yang Jingyu", [(715, 0.002), (328, 0.001)], False),
    2: ("Second Route Army", "Zhou Baozhong", [(717, 0.002), (328, 0.0005)], True),
    3: ("Third Route Army", "Zhao Shangzhi", [(714, 0.002), (717, 0.0005)], True),
}
HOME = {1: 715, 2: 717, 3: 714}

def troops_ok():
    alts = " ".join(f"AND = {{ FROM = {{ state = {s} }} divisions_in_state = {{ state = {s} size > 1 }} }}" for s in STATES)
    return f"custom_trigger_tooltip = {{\n\ttooltip = MAN_sweep_troops_tt\n\tOR = {{ {alts} }}\n}}"

def band_hit(n_expr_state, amount):
    """reduce the band whose home is the target state."""
    s = ""
    for n, (_, _, homes, _) in BANDS.items():
        cond = " ".join(f"state = {sid}" for sid, _ in homes)
        s += f"if = {{ limit = {{ FROM = {{ OR = {{ {cond} }} }} check_variable = {{ MAN_band{n} > 0 }} }} subtract_from_variable = {{ MAN_band{n} = {amount} }} }}\n"
    return s

sweep_cost, sweep_pay = cc(10, 0, 15)
SEC_DEC = f"""MAN_sec_sweep = {{
	icon = GFX_decision_generic_army_support
	priority = 100
	allowed = {{ original_tag = MAN }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT check_variable = {{ MAN_bandit > 9.99 }} }} }}
	on_map_mode = map_and_decisions_view
	available = {{
{ind(troops_ok(), 2)}	}}
{ind(sweep_cost, 1)}	fire_only_once = no
	days_remove = 30
	days_re_enable = 60
	complete_effect = {{
{ind(sweep_pay, 2)}	}}
	remove_effect = {{
		custom_effect_tooltip = MAN_tt_sweep
		set_temp_variable = {{ MAN_s = MAN_fav_kw }}
		divide_temp_variable = {{ MAN_s = 10 }}
		add_to_temp_variable = {{ MAN_s = 10 }}
		if = {{ limit = {{ FROM = {{ has_state_flag = MAN_informants }} }} multiply_temp_variable = {{ MAN_s = 1.5 }} }}
		FROM = {{
			subtract_from_variable = {{ MAN_bandit = MAN_s }}
			clamp_variable = {{ var = MAN_bandit min = 0 max = 100 }}
		}}
{ind(band_hit('FROM', 6), 2)}		add_stability = -0.005
		army_experience = 1
		random_list = {{
			70 = {{ }}
			30 = {{ FROM = {{ set_state_flag = {{ flag = MAN_grievance days = 120 }} }} custom_effect_tooltip = MAN_tt_reprisal }}
		}}
		hidden_effect = {{ MAN_sec_refresh = yes MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{
		base = 2
		modifier = {{ FROM = {{ check_variable = {{ MAN_bandit > 40 }} }} add = 15 }}
	}}
}}
MAN_sec_hamlets = {{
	icon = oppression
	priority = 99
	allowed = {{ original_tag = MAN }}
	visible = {{ has_completed_focus = MAN_sec_collective_hamlets }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT NOT = {{ has_state_flag = MAN_hamlets }} check_variable = {{ MAN_bandit > 19.99 }} }} }}
	on_map_mode = map_and_decisions_view
{ind(cc(40, 10)[0], 1)}	fire_only_once = no
	days_remove = 120
	modifier = {{ civilian_factory_use = 1 }}
	complete_effect = {{
{ind(cc(40, 10)[1], 2)}	}}
	remove_effect = {{
		FROM = {{
			set_state_flag = MAN_hamlets
			add_dynamic_modifier = {{ modifier = MAN_hamlets_dm }}
			subtract_from_variable = {{ MAN_bandit = 15 }}
			clamp_variable = {{ var = MAN_bandit min = 0 max = 100 }}
		}}
		custom_effect_tooltip = MAN_tt_hamlets
{ind(band_hit('FROM', 10), 2)}		add_stability = -0.02
		hidden_effect = {{ MAN_sec_refresh = yes MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 2 modifier = {{ FROM = {{ check_variable = {{ MAN_bandit > 50 }} }} add = 8 }} }}
}}
MAN_sec_blockhouses = {{
	icon = GFX_decision_generic_fortification
	priority = 98
	allowed = {{ original_tag = MAN }}
	visible = {{ has_completed_focus = MAN_sec_blockhouses }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT NOT = {{ has_state_flag = MAN_blockhouses }} }} }}
	on_map_mode = map_and_decisions_view
{ind(cc(30, 10)[0], 1)}	fire_only_once = no
	days_remove = 60
	complete_effect = {{
{ind(cc(30, 10)[1], 2)}	}}
	remove_effect = {{
		FROM = {{ set_state_flag = MAN_blockhouses }}
		custom_effect_tooltip = MAN_tt_blockhouses
		hidden_effect = {{ MAN_sec_refresh = yes MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 4 }}
}}
MAN_sec_informants = {{
	icon = GFX_decision_generic_police_action
	priority = 97
	allowed = {{ original_tag = MAN }}
	visible = {{ has_completed_focus = MAN_sec_kempeitai }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT NOT = {{ has_state_flag = MAN_informants }} }} }}
	on_map_mode = map_and_decisions_view
	cost = 20
	fire_only_once = no
	complete_effect = {{
		FROM = {{ set_state_flag = {{ flag = MAN_informants days = 180 }} }}
		custom_effect_tooltip = MAN_tt_informants
		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 3 }}
}}
"""
for n, (bn, leader, homes, ex) in BANDS.items():
    SEC_DEC += f"""MAN_sec_surrender_{n} = {{
	icon = GFX_decision_generic_civil_support
	priority = {90 - n}
	allowed = {{ original_tag = MAN }}
	visible = {{ has_completed_focus = MAN_sec_surrender check_variable = {{ MAN_band{n} > 0 }} NOT = {{ has_country_flag = MAN_band{n}_exile }} }}
	highlight_states = {{ highlight_state_targets = {{ state = {HOME[n]} }} }}
	cost = 40
	days_remove = 45
	days_re_enable = 90
	fire_only_once = no
	remove_effect = {{
		subtract_from_variable = {{ MAN_band{n} = 12 }}
		custom_effect_tooltip = MAN_tt_band{n}_m12
		add_to_variable = {{ MAN_labour = 5 }}
		custom_effect_tooltip = MAN_tt_labour_5
		add_manpower = 2000
		{HOME[n]} = {{ subtract_from_variable = {{ MAN_bandit = 5 }} clamp_variable = {{ var = MAN_bandit min = 0 max = 100 }} }}
		hidden_effect = {{ MAN_sec_refresh = yes MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 3 }}
}}
"""
    loc(f"MAN_sec_surrender_{n}", f"Surrender Campaign: {bn}")
    loc(f"MAN_sec_surrender_{n}_desc", f"Leaflets, bribes and amnesties for the men of {leader}'s {bn}. Each band that comes down from the hills goes straight into the labour corps or the Manchukuo Army.")
    loc(f"MAN_tt_band{n}_m12", f"§Y{bn}§! strength: §G-12§!")

SEC_DEC += """MAN_sec_three_year = {
	icon = GFX_decision_generic_police_action
	priority = 280
	allowed = { original_tag = MAN }
	activation = { has_country_flag = MAN_sec_plan_active }
	available = { check_variable = { MAN_bandit_avg < 25 } }
	days_mission_timeout = 1095
	fire_only_once = yes
	is_good = yes
	complete_effect = {
		add_stability = 0.05
		add_to_variable = { MAN_kw_pat = 15 }
		custom_effect_tooltip = MAN_tt_pat_15
		add_to_variable = { MAN_fav_kw = 15 }
		custom_effect_tooltip = MAN_tt_fav_kw_15
		add_political_power = 100
		hidden_effect = { MAN_ui_refresh = yes }
	}
	timeout_effect = {
		add_to_variable = { MAN_kw_pat = -20 }
		custom_effect_tooltip = MAN_tt_pat_m20
		add_to_variable = { MAN_fav_kw = -15 }
		custom_effect_tooltip = MAN_tt_fav_kw_m15
		add_stability = -0.08
		hidden_effect = { MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 1 }
}
MAN_sec_nozoe = {
	icon = GFX_decision_generic_army_support
	priority = 270
	allowed = { original_tag = MAN }
	activation = { has_country_flag = MAN_nozoe_active }
	available = { check_variable = { MAN_band1 < 0.01 } }
	days_mission_timeout = 365
	fire_only_once = yes
	is_good = yes
	complete_effect = {
		clr_country_flag = MAN_nozoe_active
		add_to_variable = { MAN_kw_pat = 20 }
		custom_effect_tooltip = MAN_tt_pat_20
		add_to_variable = { MAN_fav_kw = 15 }
		custom_effect_tooltip = MAN_tt_fav_kw_15
		army_experience = 20
		hidden_effect = { MAN_ui_refresh = yes }
	}
	timeout_effect = {
		clr_country_flag = MAN_nozoe_active
		add_to_variable = { MAN_kw_pat = -8 }
		custom_effect_tooltip = MAN_tt_pat_m8
		hidden_effect = { MAN_ui_refresh = yes }
	}
	ai_will_do = { base = 1 }
}
"""
loc("MAN_sec_sweep", "Punitive Sweep")
loc("MAN_sec_sweep_desc", "Japanese and Manchukuo columns comb the valleys, burning camps and seizing grain caches. Needs at least two of our divisions stationed in the province. Stronger with Kwantung Army favour and with an informant network in place.")
loc("MAN_sweep_troops_tt", "At least §Y2§! of our divisions are stationed in the province")
loc("MAN_sec_hamlets", "Concentrate into Collective Hamlets")
loc("MAN_sec_hamlets_desc", "Burn the scattered farmsteads and herd their people behind the walls of fortified 'collective hamlets', starving the guerrillas of food and recruits. It works, at a terrible cost to the people moved.")
loc("MAN_sec_blockhouses", "Build Railway Blockhouses")
loc("MAN_sec_blockhouses_desc", "A chain of brick blockhouses, wire and searchlights along every line and road in the province.")
loc("MAN_sec_informants", "Plant a Kempeitai Informant Network")
loc("MAN_sec_informants_desc", "Paid informers in every village headman's house. For six months banditry grows more slowly and sweeps strike harder.")
loc("MAN_sec_three_year", "The Three-Year Public Security Plan")
loc("MAN_sec_three_year_desc", "The Kwantung Army has given Hsinking three years to break the armed resistance. Average banditry must fall below §Y25§!.")
loc("MAN_sec_nozoe", "The Nozoe Punitive Campaign")
loc("MAN_sec_nozoe_desc", "General Nozoe's special command hunts Yang Jingyu's First Route Army through the Changbai forests through a winter. While the campaign runs the First Route Army loses strength every week. Destroy it before the year is out.")

# =====================================================================================================
# CATEGORIES
# =====================================================================================================
CATS = """
MAN_plan_cat = {
	icon = GFX_decision_category_MAN_first_fyp
	priority = 100
	allowed = { original_tag = MAN }
	visible = { has_country_flag = MAN_plan_unlocked }
	scripted_gui = MAN_plan_board
	visible_when_empty = yes   # the board is the content: keep it when every decision is on cooldown
}

MAN_politics_cat = {
	icon = GFX_decision_category_generic_political_actions
	priority = 99
	allowed = { original_tag = MAN }
	scripted_gui = MAN_politics_board
	visible_when_empty = yes   # the board is the content: keep it when every decision is on cooldown
}

MAN_security_cat = {
	icon = GFX_decision_category_generic_crisis
	priority = 98
	allowed = { original_tag = MAN }
	scripted_gui = MAN_security_board
	visible_when_empty = yes   # the board is the content: keep it when every decision is on cooldown
}
"""
loc("MAN_plan_cat", "The Industrial Development Plan")
loc("MAN_plan_cat_desc", "Zone provinces, start projects and feed the labour pool. Every project adds to the four quota tracks; the Annual Review checks total fulfilment each plan year.")
loc("MAN_politics_cat", "The Hsinking Bureaucracy")
loc("MAN_politics_cat_desc", "Manchukuo is governed by five Japanese power centres. Court them, answer their requests, and keep the Kwantung Army's patience. Favour shapes your economy; men who leave for Tokyo on good terms remain friends there.")
loc("MAN_security_cat", "Public Security")
loc("MAN_security_cat_desc", "The Northeast Anti-Japanese United Army still holds the forests and mountains. Banditry slows construction and resource extraction in each province and scales down the Plan's output there.")

def build():
    dec = "# Manchukuo rework: three decision systems\n\n"
    plan = ""
    # surveying and designating are done from the Provinces panel on the Plan board (man_sites.prov_gui), not map decisions
    import man_sites as SI
    for i, st in enumerate(SI.SITES): plan += SI.site(st, 170 - i, cc, award, ind, loc)
    for i, p in enumerate(PROJ): plan += project(*p, pri=140 - i)
    for i, ln in enumerate(SI.LINES): plan += SI.line(ln, 130 - i, cc, award, ind, loc)
    for i, r in enumerate(SI.RUNS): plan += SI.run(r, 120 - i, award, ind, loc)
    loc("MAN_tt_spur", "A new mine spur counts as track for §YMantetsu§!'s requests")
    for i, m in enumerate(MEGA): plan += mega(*m, pri=180 - i)
    plan += LABOUR_DEC + PLAN_REVIEW + SI.SURVEY_MISSION
    for k_, v_ in SI.SURVEY_LOC: loc(k_, v_)
    dec += "MAN_plan_cat = {\n" + ind(plan, 1) + "}\n\n"
    dec += "MAN_politics_cat = {\n" + ind(POL_DEC + req_missions(), 1) + "}\n\n"
    # sweeps, hamlets, blockhouses and informants are run from the Public Security panel (man_sites.sec_gui)
    sec = re.sub(r"^MAN_sec_(sweep|hamlets|blockhouses|informants) = \{\n.*?^\}\n", "", SEC_DEC, flags=re.S | re.M)
    assert "MAN_sec_sweep = {" not in sec and "MAN_sec_surrender_1 = {" in sec
    dec += "MAN_security_cat = {\n" + ind(sec, 1) + "}\n"
    # the Library: historical vignettes read on demand instead of firing on their own
    import man_library as LIB
    dec += "\nMAN_library_cat = {\n" + ind(LIB.decisions(loc), 1) + "}\n"
    for k_, v_ in LIB.CAT_LOC + LIB.OPIUM_LOC: loc(k_, v_)
    wr("common/decisions/MAN_decisions.txt", dec)
    cats, cb = rd("common/decisions/categories/MAN_decision_categories.txt")
    keep = cats[cats.index("############################################################\n########### RACIAL HARMONY"):]
    wr("common/decisions/categories/MAN_decision_categories.txt",
       "# Manchukuo rework decision categories.\n" + CATS + LIB.CAT + "\n" + keep, cb)
    # custom cost loc
    QT.add(("power", 20, False))
    for pp, lab, cp in sorted(CC):
        parts = []
        if pp: parts.append(f"{pp} £pol_power")
        if cp: parts.append(f"{cp} £command_power")
        if lab: parts.append(f"{lab}k £manpower_texticon")
        loc(f"MAN_cc_{pp}_{lab}_{cp}", "  ".join(parts))
        loc(f"MAN_cc_{pp}_{lab}_{cp}_blocked", "§R" + "  ".join(parts) + "§!")
    for k, n, sc in sorted(QT):
        loc(f"MAN_tt_q_{k}_{n}{'' if sc else '_flat'}",
            f"§Y{QN[k]}§! quota: §G+{n}§!" + (" (scaled by provincial security and planning efficiency)" if sc else " (scaled by planning efficiency)"))
    return L
