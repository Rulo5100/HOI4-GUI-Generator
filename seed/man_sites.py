"""Manchukuo Plan v3 project layer: survey (state marking), unique historical sites, Mantetsu lines, CIC output runs.
Imported by man_systems.build(); appends loc to man_systems.L via the passed loc function."""
from man_common import *

def cic(base, key_pfx="MAN_tt_cic"):
    """CIC payout from a state-targeted decision (ROOT = MAN, FROM = state), reduced by banditry via FROM.MAN_eff."""
    k = f"{key_pfx}_{base}"
    s = f"custom_effect_tooltip = {k}\nhidden_effect = {{\n"
    s += f"\tif = {{ limit = {{ FROM = {{ check_variable = {{ MAN_eff > 0.849 }} }} }} add_cic = {base} }}\n"
    s += f"\telse_if = {{ limit = {{ FROM = {{ check_variable = {{ MAN_eff > 0.599 }} }} }} add_cic = {int(base * 0.75)} }}\n"
    s += f"\telse = {{ add_cic = {base // 2} }}\n}}\n"
    return k, s

# ------------------------------------------------------------------ sites
# key, state, zone, name, icon, levels, days, pp, lab, civ, state reward (per level), quota awards per level, root reward per level,
# extra root gate (visible), cic per level, desc
SITES = [
    # Liaoning (Mukden, Anshan, Fushun, Benxi, Antung)
    ("gongchangling", 716, "min", "Gongchangling Magnetite Mines", "GFX_decision_steel", 2, 90, 20, 15, 1,
     "add_resource = { type = steel amount = 30 }", [("steel", 10)], "", "", 0,
     "The rich magnetite at Gongchangling feeds the Showa furnaces at Anshan directly, without the costly ore beneficiation that the lean Anshan ores need."),
    ("fushun_shale", 716, "min", "Fushun Oil Shale Retorts", "GFX_decision_oil", 2, 120, 30, 20, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = synthetic_refinery level = 1 instant_build = yes }", [("coal", 10)], "",
     "has_country_flag = MAN_shale_known", 0,
     "More retorts on the shale stripped from above the Fushun coal. Each battery adds a refinery. Requires the Fushun Oil Shale focus."),
    ("tiexi", 716, "hi", "The Tiexi Industrial District", "GFX_decision_generic_factory", 3, 100, 25, 20, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = industrial_complex level = 1 instant_build = yes }", [("mach", 6), ("steel", 3)], "", "", 0,
     "West of the Mukden railway yards the planners lay out a whole district of factories: machine shops, tanneries, cement and textile mills along new paved streets."),
    ("antung", 716, "hi", "Antung Light Metals Works", "GFX_decision_aluminium", 1, 120, 30, 20, 2,
     "add_resource = { type = aluminium amount = 40 }", [("mach", 6), ("steel", 4)], "",
     "has_completed_focus = MAN_eco_light_metals", 0,
     "An aluminium reduction works at Antung on the Yalu, waiting for the current from the Supung turbines. Requires the Manchurian Light Metals focus."),
    # Liaobei (Tongliao, Fuxin, Jinzhou hills)
    ("fuxin", 715, "min", "The Fuxin Open Pit", "GFX_decision_coal", 3, 90, 20, 20, 1,
     "add_resource = { type = coal amount = 40 }", [("coal", 9)], "", "", 0,
     "The Fuxin coalfield is opened from 1936 as a vast open pit, worked by contract labour from Shandong under brutal conditions."),
    ("molybdenum", 715, "min", "Yangjiazhangzi Molybdenum", "GFX_decision_steel", 1, 90, 25, 10, 1,
     "add_resource = { type = tungsten amount = 20 }", [("steel", 4), ("mach", 6)], "", "", 0,
     "The molybdenum mine at Yangjiazhangzi supplies an alloy metal that Japanese armour plate and gun steel cannot do without."),
    # Kirin (Hsinking, Kirin, Harbin, Tonghua)
    ("hsinking", 328, "hi", "The Great Hsinking Plan", "GFX_decision_generic_construction", 2, 120, 30, 15, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = industrial_complex level = 1 instant_build = yes }", [("mach", 5)],
     "add_political_power = 15\n", "", 0,
     "The new capital is laid out with boulevards, ministries and an industrial quarter, planned from nothing on the plain around the old town of Changchun."),
    ("harbin", 328, "hi", "Harbin Railway Workshops", "GFX_decision_generic_train", 2, 100, 20, 15, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = arms_factory level = 1 instant_build = yes }", [("mach", 8)], "", "", 0,
     "The great workshops of the old Chinese Eastern Railway, bought from the Soviets in 1935, are retooled to build rolling stock and shells."),
    ("dongbiandao", 328, "min", "The Dongbiandao Development Company", "GFX_decision_steel", 3, 120, 30, 25, 2,
     "add_resource = { type = steel amount = 25 }\nadd_resource = { type = coal amount = 20 }", [("steel", 8), ("coal", 6)], "fav_mgy3",
     "OR = { has_country_flag = MAN_mangyo_founded check_variable = { MAN_fav_mgy > 49.99 } }", 0,
     "Mangyo's company for the Tonghua highlands: iron at Dalizi and coal at Tiechang, in the forests where the First Route Army hides. Requires Mangyo, or 50 Mangyo favour."),
    ("kirin_chem", 328, "pow", "Kirin Electro-Chemical Works", "GFX_decision_rubber", 2, 120, 30, 20, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = synthetic_refinery level = 1 instant_build = yes }", [("power", 6), ("coal", 4)], "",
     "check_variable = { MAN_mega_fengman_n > 0.5 }", 0,
     "Cheap current from Fengman makes calcium carbide, and carbide makes acetylene, synthetic rubber and explosives. Requires the first stage of the §1Fengman Dam§! megaproject."),
    # Chuho / Sungkiang (Jiamusi, Mudanjiang, Hegang, Jixi)
    ("hegang", 717, "min", "Hegang Collieries", "GFX_decision_coal", 3, 90, 20, 20, 1,
     "add_resource = { type = coal amount = 35 }", [("coal", 9)], "", "", 0,
     "Mangyo opens the Hegang field north of Jiamusi, the largest coal reserve in the north, and hauls its coal south on the new Tumen line."),
    ("jixi", 717, "min", "Jixi and Mishan Coal", "GFX_decision_coal", 2, 90, 20, 15, 1,
     "add_resource = { type = coal amount = 30 }\nadd_to_variable = { MAN_bandit = 3 }", [("coal", 8)], "", "", 0,
     "Coal pits close to the Soviet border, in country the Third Route Army knows well. Every new pit brings new targets for raids."),
    ("mudanjiang", 717, "hi", "Mudanjiang Garrison Works", "GFX_decision_generic_factory", 2, 100, 25, 15, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = arms_factory level = 1 instant_build = yes }", [("mach", 8)], "kw_fav3", "", 0,
     "Mudanjiang becomes the Kwantung Army's eastern base against the Soviet Maritime Province, with repair shops and ammunition works behind the fortified zones."),
    ("jingpo", 717, "pow", "Jingpo Lake Hydro Station", "GFX_decision_generic_electricity", 1, 150, 30, 25, 2,
     "add_extra_state_shared_building_slots = 1", [("power", 14)], "", "", 0,
     "A small hydro station at the outlet of Jingpo Lake, where the Mudan River falls through a basalt gorge."),
    # Heilungkiang (Qiqihar, Heihe, Mohe)
    ("heihe_gold", 714, "min", "The Heihe and Mohe Gold Fields", "GFX_decision_hol_attract_foreign_investors", 3, 90, 15, 20, 1,
     "", [], "add_political_power = 15\n", "", 3000,
     "Placer gold from the Amur valleys, which the Manchukuo Gold Mining Company sells for foreign currency to buy machine tools abroad."),
    ("qiqihar", 714, "hi", "Qiqihar Machine Works", "GFX_decision_generic_industry", 2, 100, 20, 15, 2,
     "add_extra_state_shared_building_slots = 1\nadd_building_construction = { type = industrial_complex level = 1 instant_build = yes }", [("mach", 6), ("steel", 2)], "", "", 0,
     "Locomotive and machine works at the junction of the western lines, building for the railways and for the army's northern front."),
    # Hulunbuir (Manzhouli, Hailar)
    ("jalainur", 761, "min", "Jalainur Collieries", "GFX_decision_coal", 2, 90, 20, 15, 1,
     "add_resource = { type = coal amount = 30 }", [("coal", 8)], "", "", 0,
     "Lignite at Jalainur on the Soviet frontier, worked since the days of the Chinese Eastern Railway."),
    ("hailar", 761, "set", "Hailar Meat and Hides", "GFX_decision_USA_cnc_trade_pact", 1, 60, 10, 5, 1,
     "", [], "", "", 2000,
     "Barga herds driven into a new meat-packing plant at Hailar: tinned beef for the army and hides for export."),
    # Jehol
    ("beipiao", 610, "min", "Beipiao Collieries", "GFX_decision_coal", 2, 90, 20, 15, 1,
     "add_resource = { type = coal amount = 25 }", [("coal", 8)], "", "", 0,
     "Coking coal at Beipiao near Chaoyang, on the new line to Jinzhou."),
    # Inner Mongolia
    ("wool", 611, "set", "The Chahar Wool Trade", "GFX_decision_USA_cnc_trade_pact", 1, 60, 10, 5, 1,
     "", [], "", "", 1500,
     "Buy the Mongol wool clip at fixed prices and ship it to the Japanese mills."),
    ("remount", 612, "set", "Xilingol Remount Depots", "GFX_decision_generic_cavalry", 2, 90, 15, 5, 1,
     "", [], "kw_fav3", "", 1200,
     "Mongol horses for the Kwantung Army's cavalry and transport columns, bought on the steppe and broken at new depots."),
]
SITE_STATES = {}
for st in SITES: SITE_STATES.setdefault(st[1], []).append(st[3])

def site_ext(lv): return 2 if lv >= 3 else 1   # Second Five-Year Plan expansion stages per site

def site_rew_root(code):
    if code == "fav_mgy3": return "add_to_variable = { MAN_fav_mgy = 3 }\ncustom_effect_tooltip = MAN_tt_fav_mgy_3\n"
    if code == "kw_fav3": return "add_to_variable = { MAN_fav_kw = 3 }\ncustom_effect_tooltip = MAN_tt_fav_kw_3\n"
    return code

def site(st, pri, cc, award, ind, loc):
    (key, sid, z, nm, icon, lv, days, pp, lab, civ, srew, aw, rr, gate, cicv, desc) = st
    cost, pay = cc(pp, lab)
    root = "".join(award(k, n) for k, n in aw) + site_rew_root(rr)
    if cicv:
        k, s = cic(cicv); root += s
        loc(k, f"§YEconomic Capacity Surplus§!: §G+{cicv}§! (cut by up to half in provinces troubled by banditry)")
    if z == "min": root += "add_to_variable = { MAN_rail_built = 1 }\n" + "custom_effect_tooltip = MAN_tt_spur\n"
    # sites show their progress in the title (the level lives on the province, mirrored on the country for the title)
    root += f"add_to_variable = {{ MAN_lvc_{key} = 1 }}\n"
    loc(f"MAN_site_{key}", f"{nm} (stage [?MAN_lvc_{key}|0]/[?MAN_cap_{key}|0])")
    # stages beyond the first plan's (opened by the Second Five-Year Plan) give quota only: no new buildings or resources
    if srew: srew = f"if = {{\n\tlimit = {{ check_variable = {{ MAN_lv_{key} < {lv + 0.5} }} }}\n" + ind(srew, 1) + "}\n"
    loc(f"MAN_site_{key}_desc", desc + NL + NL + f"Site in §Y{SNAME[sid]}§!. Needs the province surveyed and designated as a §Y{ZNAME[z]}§!. Up to §Y{lv}§! stage{'s' if lv > 1 else ''}, and §Y{site_ext(lv)}§! more in the §YSecond Five-Year Plan§! (quota only). Quota output is scaled by the province's security and by planning efficiency.")
    return f"""MAN_site_{key} = {{
	icon = {icon}
	priority = {pri}
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = MAN_plan_unlocked {gate} }}
	state_target = yes
	targets = {{ {sid} }}
	target_trigger = {{
		FROM = {{
			is_owned_and_controlled_by = ROOT
			has_state_flag = MAN_surveyed
			has_state_flag = MAN_zone_{z}
			OR = {{
				NOT = {{ check_variable = {{ MAN_lv_{key} > {lv - 0.5} }} }}
				AND = {{
					ROOT = {{ has_country_flag = MAN_second_five_year_plan_active }}
					NOT = {{ check_variable = {{ MAN_lv_{key} > {lv + site_ext(lv) - 0.5} }} }}
				}}
			}}
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
			add_to_variable = {{ MAN_lv_{key} = 1 }}
{ind(srew, 3) if srew else ''}		}}
{ind(root, 2) if root else ''}		custom_effect_tooltip = MAN_behemoth_risk_tt
		hidden_effect = {{
			MAN_behemoth_accident_roll = yes
			MAN_plan_recalc = yes
			MAN_ui_refresh = yes
		}}
	}}
	ai_will_do = {{ base = 10 }}
}}
"""

ZNAME = {"hi": "Heavy Industry Zone", "min": "Mining District", "pow": "Power and Water District", "set": "Settlement and Grain Zone"}

# ------------------------------------------------------------------ survey (state marking)
FOUND = {
    716: "Gongchangling magnetite and the Fushun shale beds; room for an industrial district at Tiexi and light metals at Antung",
    715: "the Fuxin coalfield and molybdenum at Yangjiazhangzi",
    328: "Tonghua iron and coal for a Dongbiandao company; sites for Hsinking's industrial quarter, the Harbin workshops and electro-chemistry below Fengman",
    717: "the Hegang and Jixi coalfields, a garrison works site at Mudanjiang and a hydro site at Jingpo Lake",
    714: "gold in the Amur valleys and a machine works site at Qiqihar",
    761: "Jalainur lignite and the Barga herds",
    610: "coking coal at Beipiao",
    611: "the Chahar wool trade",
    612: "remount pastures on the Xilingol steppe",
    1043: "nothing worth the expense",
}
MAIN_RES = {716: "steel", 715: "coal", 328: "steel", 717: "coal", 714: "coal", 761: "coal", 610: "coal", 611: "coal", 612: "coal", 1043: "coal"}

def survey(cc, ind, loc):
    cost, pay = cc(15, 5)
    found = "".join(f"if = {{ limit = {{ state = {s} }} custom_effect_tooltip = MAN_tt_found_{s} }}\n" for s in STATES)
    rich = "".join(f"if = {{ limit = {{ state = {s} }} add_resource = {{ type = {MAIN_RES[s]} amount = 15 }} }}\n" for s in STATES)
    for s in STATES: loc(f"MAN_tt_found_{s}", f"The geologists report: §Y{FOUND[s]}§!.")
    loc("MAN_tt_rich_find", "§G30% chance:§! a rich find adds §G15§! of the province's main resource")
    loc("MAN_survey", "Mantetsu Geological Survey")
    loc("MAN_survey_desc", "Send a Mantetsu survey party with an army escort to map the province's ore bodies, coal seams, rivers and towns. A surveyed province is marked on the Plan's map and can be designated for development; what the survey finds decides which sites can be opened there." + NL + NL + "Only one survey party can be in the field at a time.")
    return f"""MAN_survey = {{
	icon = GFX_decision_generic_research
	priority = 210
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = MAN_plan_unlocked }}
	state_target = yes
	targets = {TARGETS}
	target_trigger = {{ FROM = {{ is_owned_and_controlled_by = ROOT NOT = {{ has_state_flag = MAN_surveyed }} }} }}
	on_map_mode = map_and_decisions_view
	available = {{ NOT = {{ has_country_flag = MAN_surveying }} }}
{ind(cost, 1)}	fire_only_once = no
	days_remove = 45
	cancel_trigger = {{ FROM = {{ NOT = {{ is_owned_and_controlled_by = ROOT }} }} }}
	cancel_effect = {{ clr_country_flag = MAN_surveying }}
	complete_effect = {{
{ind(pay, 2)}		set_country_flag = MAN_surveying
	}}
	remove_effect = {{
		clr_country_flag = MAN_surveying
		FROM = {{
			set_state_flag = MAN_surveyed
			add_dynamic_modifier = {{ modifier = MAN_surveyed_dm }}
{ind(found, 3)}			custom_effect_tooltip = MAN_tt_rich_find
			hidden_effect = {{
				random_list = {{
					30 = {{
{ind(rich, 6)}					}}
					70 = {{ }}
				}}
			}}
		}}
		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 12 }}
}}
"""

# ------------------------------------------------------------------ Mantetsu lines (one-off, map highlighted)
LINES = [
    ("jehol", "The Jinzhou to Chengde Line", [715, 610], {610: -8}, 25, 20, 120, "",
     "Carry the railway up into the Jehol hills to Chengde, binding the province to Manchukuo and opening the Beipiao coal."),
    ("tumen", "The Tumen to Jiamusi Line", [717], {717: -8}, 30, 25, 150, "",
     "A strategic line through the eastern forests from the Korean border to the Sungari, opening Hegang and cutting the partisans' hinterland in two."),
    ("heihe", "The Bei'an to Heihe Line", [714], {714: -6}, 25, 20, 120, "add_to_variable = { MAN_fav_kw = 5 }\ncustom_effect_tooltip = MAN_tt_fav_kw_5\n",
     "The line north to Heihe on the Amur, which the Kwantung Army wants for an offensive into the Soviet Far East."),
    ("north", "Double-Track the North Manchuria Line", [328, 761], {761: -4}, 30, 25, 150, "add_to_variable = { MAN_fav_kw = 3 }\ncustom_effect_tooltip = MAN_tt_fav_kw_3\n",
     "Convert the old Russian broad gauge from Harbin to Manzhouli to standard gauge and double it, so that troop trains can reach the Mongolian front."),
]
def line(ln, pri, cc, award, ind, loc):
    (key, nm, sts, bandit, pp, lab, days, extra, desc) = ln
    cost, pay = cc(pp, lab)
    infra = "".join(f"if = {{ limit = {{ {s} = {{ is_owned_and_controlled_by = ROOT }} }} {s} = {{ add_building_construction = {{ type = infrastructure level = 1 instant_build = yes }} }} }}\n" for s in sts)
    infra += "".join(f"if = {{ limit = {{ {s} = {{ is_owned_and_controlled_by = ROOT }} }} {s} = {{ add_to_variable = {{ MAN_bandit = {b} }} }} }}\n" for s, b in bandit.items())
    loc(f"MAN_tt_line_{key}", ", ".join(SNAME[s] for s in sts) + ": §G+1§! infrastructure. Banditry " + ", ".join(f"in {SNAME[s]} §G{b}§!" for s, b in bandit.items()))
    loc(f"MAN_line_{key}", nm)
    loc(f"MAN_line_{key}_desc", desc + NL + NL + "A Mantetsu construction project. It counts as a plan project and as new track for Mantetsu's requests.")
    hl = " ".join(f"state = {s}" for s in sts)
    return f"""MAN_line_{key} = {{
	icon = GFX_decision_generic_train
	priority = {pri}
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = MAN_lines_unl }}
	highlight_states = {{ highlight_state_targets = {{ {hl} }} }}
	available = {{
		{sts[0]} = {{ is_owned_and_controlled_by = ROOT }}
		check_variable = {{ MAN_proj_active < MAN_proj_slots }}
	}}
{ind(cost, 1)}	fire_only_once = yes
	days_remove = {days}
	modifier = {{ civilian_factory_use = 2 }}
	complete_effect = {{
{ind(pay, 2)}		add_to_variable = {{ MAN_proj_active = 1 }}
		hidden_effect = {{ MAN_ui_refresh = yes }}
	}}
	remove_effect = {{
		subtract_from_variable = {{ MAN_proj_active = 1 }}
		add_to_variable = {{ MAN_proj_done = 1 }}
		add_to_variable = {{ MAN_rail_built = 1 }}
		custom_effect_tooltip = MAN_tt_line_{key}
		hidden_effect = {{
{ind(infra, 3)}		}}
		add_to_variable = {{ MAN_fav_smr = 5 }}
		custom_effect_tooltip = MAN_tt_fav_smr_5
{ind(extra + award('steel', 3, scaled=False) + award('coal', 3, scaled=False), 2)}		hidden_effect = {{ MAN_plan_recalc = yes MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 6 }}
}}
"""

# ------------------------------------------------------------------ output runs (CIC)
RUNS = [
    # key, name, icon, targets, target extra trigger, cost, days, civ, cic base, cooldown, extra root effect, extra state effect, desc
    ("empire", "Production Run for the Empire", "GFX_decision_USA_cnc_arms_export", ZONES["hi"], "has_state_flag = MAN_zone_hi", 10, 60, 3, 3000, 90,
     "MACH4add_to_variable = { MAN_fav_ind = 2 }\ncustom_effect_tooltip = MAN_tt_fav_ind_2\n", "",
     "Turn the province's works over to a contract run for Japanese buyers. The factories are tied up for two months; the proceeds go into the construction budget."),
    ("soy", "Soybean Export Season", "GFX_decision_USA_cnc_trade_pact", ZONES["set"], "has_state_flag = MAN_zone_set", 5, 30, 1, 1500, 180,
     "add_to_variable = { MAN_fav_smr = 3 }\ncustom_effect_tooltip = MAN_tt_fav_smr_3\n",
     "random_list = { 25 = { set_state_flag = { flag = MAN_grievance days = 120 } } 75 = { } }\n",
     "Mantetsu buys the harvest at fixed prices and ships it out through Dairen to Germany and Japan. The peasants get paper money; a quarter of the time they get angry too."),
    ("opium", "The Jehol Opium Monopoly", "GFX_decision_USA_cnc_money", [610], "", 0, 30, 0, 2500, 120,
     "add_stability = -0.02\nadd_to_variable = { MAN_fav_kw = 2 }\ncustom_effect_tooltip = MAN_tt_fav_kw_2\n"
     "if = { limit = { has_country_flag = MAN_adv_satomi } add_cic = 1500 }\n" + __import__("man_library").opium_hook(),
     "add_to_variable = { MAN_bandit = 4 }\n",
     "The state Opium Monopoly Bureau buys the Jehol poppy harvest and sells it through licensed dens across the country. It is one of the regime's richest sources of revenue and one of its most shameful."),
]
def run(r, pri, award, ind, loc):
    (key, nm, icon, tl, xt, pp, days, civ, base, cd, rroot, rstate, desc) = r
    k, cs = cic(base)
    loc(k, f"§YEconomic Capacity Surplus§!: §G+{base}§! (cut by up to half in provinces troubled by banditry)")
    rroot = rroot.replace("MACH4", award("mach", 4))
    loc(f"MAN_run_{key}", nm)
    loc(f"MAN_run_{key}_desc", desc + NL + NL + f"The province cannot repeat this for §Y{cd}§! days afterwards. Economic Capacity Surplus speeds up construction lines.")
    tlist = "{ " + " ".join(map(str, tl)) + " }"
    state_fx = f"set_state_flag = {{ flag = MAN_run_cd days = {cd} }}\n" + rstate
    return f"""MAN_run_{key} = {{
	icon = {icon}
	priority = {pri}
	allowed = {{ original_tag = MAN }}
	visible = {{ has_country_flag = MAN_plan_unlocked }}
	state_target = yes
	targets = {tlist}
	target_trigger = {{
		FROM = {{
			is_owned_and_controlled_by = ROOT
			NOT = {{ has_state_flag = MAN_run_cd }}
			{xt}
		}}
	}}
	on_map_mode = map_and_decisions_view
	cost = {pp}
	fire_only_once = no
	days_remove = {days}
	modifier = {{ civilian_factory_use = {civ} }}
	cancel_trigger = {{ FROM = {{ NOT = {{ is_owned_and_controlled_by = ROOT }} }} }}
	remove_effect = {{
{ind(cs + rroot, 2)}		FROM = {{
{ind(state_fx, 3)}		}}
		hidden_effect = {{ MAN_plan_recalc = yes MAN_ui_refresh = yes }}
	}}
	ai_will_do = {{ base = 4 }}
}}
"""

# ------------------------------------------------------------------ Provinces panel (survey + designation by GUI instead of map decisions)
ZNAME_S = {"hi": "Heavy Industry Zone", "min": "Mining District", "pow": "Power and Water District", "set": "Settlement and Grain Zone"}
ZICON = {"hi": "GFX_decision_generic_factory", "min": "GFX_decision_generic_merge_plant_materiel",
         "pow": "GFX_decision_hol_inundate_water_lines", "set": "GFX_decision_generic_colonial_administration"}
ZCOST, SCOST_PP, SCOST_LAB, SDAYS, LIFT = 25, 15, 5, 45, 50
AI_ZONES = [(716, "hi"), (328, "hi"), (715, "min"), (717, "min"), (714, "min"), (761, "min"), (610, "min"), (612, "set"), (611, "set"), (717, "pow")]

def prov_effects(ind):
    rich = "".join(f"if = {{ limit = {{ state = {s} }} add_resource = {{ type = {MAIN_RES[s]} amount = 15 }} }}\n" for s in STATES)
    E = "MAN_survey_begin = {\n\tset_state_flag = MAN_svy_on\n\tset_variable = { MAN_svy = " + str(SDAYS) + " }\n\tROOT = {\n\t\tset_country_flag = MAN_surveying\n" \
        f"\t\tadd_political_power = -{SCOST_PP}\n\t\tsubtract_from_variable = {{ MAN_labour = {SCOST_LAB} }}\n\t}}\n}}\n\n"
    E += "MAN_survey_done = {\n\tset_state_flag = MAN_surveyed\n\tadd_dynamic_modifier = { modifier = MAN_surveyed_dm }\n\trandom_list = {\n\t\t30 = {\n" + ind(rich, 3) + "\t\t}\n\t\t70 = { }\n\t}\n}\n\n"
    for z in ZNAME_S:
        E += f"MAN_zone_apply_{z} = {{\n\tset_state_flag = MAN_zoned\n\tset_state_flag = MAN_zone_{z}\n\tadd_dynamic_modifier = {{ modifier = MAN_zone_{z}_dm }}\n}}\n\n"
    E += "MAN_zone_lift = {\n\tclr_state_flag = MAN_zoned\n" + "".join(f"\tclr_state_flag = MAN_zone_{z}\n\tremove_dynamic_modifier = {{ modifier = MAN_zone_{z}_dm }}\n" for z in ZNAME_S) + "}\n\n"
    # the survey itself is timed by the MAN_survey_mission decision; weekly only cleans up a survey whose province was lost
    E += ("MAN_prov_weekly = {\n"
          "\tif = {\n\t\tlimit = { has_country_flag = MAN_surveying NOT = { any_owned_state = { has_state_flag = MAN_svy_on } } }\n\t\tclr_country_flag = MAN_surveying\n\t}\n}\n\n")
    ai = "if = {\n\tlimit = { NOT = { has_country_flag = MAN_surveying } has_political_power > 40 check_variable = { MAN_labour > 9.99 } }\n" \
         "\trandom_owned_controlled_state = {\n\t\tlimit = { " + MANCHURIA_TRIGGER + " NOT = { has_state_flag = MAN_surveyed } }\n\t\tMAN_survey_begin = yes\n\t}\n}\n"
    chain = ""
    for i, (s, z) in enumerate(AI_ZONES):
        kw = "if" if i == 0 else "else_if"
        chain += (f"{kw} = {{\n\tlimit = {{ has_country_flag = MAN_zone_unl_{z} {s} = {{ is_owned_and_controlled_by = ROOT has_state_flag = MAN_surveyed NOT = {{ has_state_flag = MAN_zoned }} }} }}\n"
                  f"\tadd_political_power = -{ZCOST}\n\tadd_to_variable = {{ MAN_zones_used = 1 }}\n\t{s} = {{ MAN_zone_apply_{z} = yes }}\n}}\n")
    ai += "if = {\n\tlimit = { has_political_power > 60 check_variable = { MAN_zones_used < MAN_zone_cap } }\n" + ind(chain, 1) + "}\n"
    E += "MAN_prov_ai = {\n\tif = {\n\t\tlimit = { is_ai = yes has_country_flag = MAN_plan_unlocked }\n" + ind(ai, 2) + "\t}\n}\n\n"
    return E

def prov_gui(T, I, B, props, trig, eff, loc, y):
    """Rows for the Plan board: province name, status, survey / designate / lift buttons. Returns (gui text, new y)."""
    b = T("MAN_pv_h", 10, y, "MAN_PV_H", 300, tt="MAN_PV_H_TT")
    loc("MAN_PV_H", "§gProvinces§! (survey and designate here)")
    loc("MAN_PV_H_TT", "§YProvinces§!\\n£white_dot §YSurvey§! a province (§Y" + str(SDAYS) + "§! days, one at a time)\\n£white_dot Then §Ydesignate§! it with one of the zone buttons\\n"
        "£white_dot Its §Ysites§! then appear as decisions\\n£white_dot Lifting a designation costs §Y" + str(LIFT) + "§! £pol_power; built works stay")
    y += 22
    for s in STATES:
        b += T(f"MAN_pv_n_{s}", 10, y + 3, f"[{s}.GetName]", 110)
        b += T(f"MAN_pv_s_{s}", 122, y + 3, f"[ROOT.GetMANProv_{s}]", 220)
        own = f"{s} = {{ is_owned_by = ROOT }}"
        trig.append(f"MAN_pv_n_{s}_visible = {{ {own} }}")
        trig.append(f"MAN_pv_s_{s}_visible = {{ {own} }}")
        # survey
        el = f"MAN_pv_svy_{s}"
        b += B(el, 345, y, "GFX_decision_generic_research", f"MAN_PV_SVY_{s}_TT", scale=0.75)
        trig.append(f"{el}_visible = {{ {s} = {{ is_owned_by = ROOT NOT = {{ has_state_flag = MAN_surveyed }} NOT = {{ has_state_flag = MAN_svy_on }} }} }}")
        trig.append(f"{el}_click_enabled = {{ NOT = {{ has_country_flag = MAN_surveying }} has_political_power > {SCOST_PP - 0.01} check_variable = {{ MAN_labour > {SCOST_LAB - 0.01} }} {s} = {{ is_controlled_by = ROOT }} }}")
        eff.append(f"{el}_click = {{ {s} = {{ MAN_survey_begin = yes }} MAN_ui_refresh = yes }}")
        loc(f"MAN_PV_SVY_{s}_TT", f"§YMantetsu Geological Survey§!: §C{SNAME[s]}§!\\n£white_dot Cost: §Y{SCOST_PP}§! £pol_power, §Y{SCOST_LAB}k§! £manpower_texticon §Ylabour§!"
            f"\\n£white_dot Takes §Y{SDAYS}§! days; only one survey party at a time\\n£white_dot Expected finds: §Y{FOUND[s]}§!\\n£white_dot §G30%§! chance of a rich find: §G+15§! of the main resource"
            "\\n£white_dot Surveyed provinces gain §G+5%§! local resources and can be designated")
        # designations
        for i, z in enumerate(ZNAME_S):
            if s not in ZONES[z]: continue
            el = f"MAN_pv_z{z}_{s}"
            b += B(el, 345 + i * 28, y, ZICON[z], f"MAN_PV_Z_{z}_{s}_TT", scale=0.75)
            trig.append(f"{el}_visible = {{ has_country_flag = MAN_zone_unl_{z} {s} = {{ is_owned_by = ROOT has_state_flag = MAN_surveyed NOT = {{ has_state_flag = MAN_zoned }} }} }}")
            trig.append(f"{el}_click_enabled = {{ has_political_power > {ZCOST - 0.01} check_variable = {{ MAN_zones_used < MAN_zone_cap }} {s} = {{ is_controlled_by = ROOT }} }}")
            eff.append(f"{el}_click = {{ add_political_power = -{ZCOST} add_to_variable = {{ MAN_zones_used = 1 }} {s} = {{ MAN_zone_apply_{z} = yes }} MAN_ui_refresh = yes }}")
            sites = [st[3] for st in SITES if st[1] == s and st[2] == z]
            extra = {"pow": ["Thermal Power Station", "Transmission Grid"], "set": ["Pioneer Colony", "Soybean Export Season"], "hi": ["Production Run for the Empire"]}.get(z, [])
            opens = ", ".join(sites + extra) or "no special sites"
            loc(f"MAN_PV_Z_{z}_{s}_TT", f"§YDesignate {ZNAME_S[z]}§!: §C{SNAME[s]}§!\\n£white_dot Cost: §Y{ZCOST}§! £pol_power and one £state §Yzone§! (§Y[?MAN_zones_used|0]§! of §Y[?MAN_zone_cap|0]§! used)"
                f"\\n£white_dot Opens: §Y{opens}§!\\n£white_dot A province holds one designation")
        # lift
        el = f"MAN_pv_lift_{s}"
        b += B(el, 460, y, "GFX_decision_generic_break_treaty", f"MAN_PV_LIFT_{s}_TT", scale=0.75)
        trig.append(f"{el}_visible = {{ {s} = {{ is_owned_by = ROOT has_state_flag = MAN_zoned }} }}")
        trig.append(f"{el}_click_enabled = {{ has_political_power > {LIFT - 0.01} {s} = {{ NOT = {{ has_state_flag = MAN_busy }} }} }}")
        eff.append(f"{el}_click = {{ add_political_power = -{LIFT} subtract_from_variable = {{ MAN_zones_used = 1 }} {s} = {{ MAN_zone_lift = yes }} MAN_ui_refresh = yes }}")
        loc(f"MAN_PV_LIFT_{s}_TT", f"§YLift the designation§!: §C{SNAME[s]}§!\\n£white_dot Cost: §Y{LIFT}§! £pol_power\\n£white_dot Frees a £state §Yzone§!; built works stay\\n£white_dot Not while a project is under way here")
        y += 26
    return b, y

def prov_sl(DT):
    s = ""
    for st in STATES:
        cases = [(f"{st} = {{ has_state_flag = MAN_zone_{z} }}", f"MAN_PVS_{z}", f"§Y{ZNAME_S[z]}§!") for z in ZNAME_S]
        cases += [(f"{st} = {{ has_state_flag = MAN_svy_on }}", "MAN_PVS_SVY", "§YSurvey under way§!"),
                  (f"{st} = {{ has_state_flag = MAN_surveyed }}", "MAN_PVS_DONE", "§GSurveyed§!, not designated"),
                  ("", "MAN_PVS_NONE", "§gUnsurveyed§!")]
        s += DT(f"GetMANProv_{st}", cases)
    # name of the province being surveyed (one survey party at a time), for the survey mission
    s += DT("GetMANSurveyProv", [(f"{st} = {{ has_state_flag = MAN_svy_on }}", f"MAN_SVYP_{st}", f"§C{SNAME[st]}§!") for st in STATES]
            + [("", "MAN_SVYP_NONE", "the field")])
    return s

SURVEY_MISSION = f"""MAN_survey_mission = {{
	icon = GFX_decision_generic_research
	priority = 299
	allowed = {{ original_tag = MAN }}
	activation = {{ has_country_flag = MAN_surveying }}
	available = {{ always = no }}
	cancel_trigger = {{ NOT = {{ any_owned_state = {{ has_state_flag = MAN_svy_on }} }} }}
	days_mission_timeout = {SDAYS}
	fire_only_once = no
	is_good = yes
	timeout_effect = {{
		custom_effect_tooltip = MAN_tt_survey_report
		hidden_effect = {{
			every_owned_state = {{
				limit = {{ has_state_flag = MAN_svy_on }}
				clr_state_flag = MAN_svy_on
				MAN_survey_done = yes
			}}
			clr_country_flag = MAN_surveying
			MAN_ui_refresh = yes
		}}
	}}
	ai_will_do = {{ base = 1 }}
}}
"""
SURVEY_LOC = [("MAN_survey_mission", "Mantetsu Geological Survey"),
              ("MAN_survey_mission_desc", "A Mantetsu survey party is in the field in [ROOT.GetMANSurveyProv]. When the time runs out it reports, and the province can be designated for the Plan."),
              ("MAN_tt_survey_report", "The survey party reports: the province is §Gsurveyed§! and can be designated, with a §Y30%§! chance of a rich find")]

# ------------------------------------------------------------------ Public Security panel (sweeps, hamlets, blockhouses, informants by GUI)
# order: key, name, icon, days (0 = instant), pp, labour, cp, focus gate, cooldown flag days
SEC = [
    ("gar", "Police Garrison", "GFX_decision_generic_protection", 0, 15, 0, 0, "", 0),
    ("sw", "Punitive Sweep", "GFX_decision_generic_army_support", 30, 10, 0, 15, "", 60),
    ("hm", "Collective Hamlets", "GFX_decision_oppression", 120, 40, 10, 0, "MAN_sec_collective_hamlets", 0),
    ("bh", "Blockhouse Line", "GFX_decision_generic_fortification", 60, 30, 10, 0, "MAN_sec_blockhouses", 0),
    ("inf", "Informant Network", "GFX_decision_generic_police_action", 0, 20, 0, 0, "MAN_sec_kempeitai", 0),
]
SEC_DONE_FLAG = {"gar": "MAN_garrisoned", "hm": "MAN_hamlets", "bh": "MAN_blockhouses", "inf": "MAN_informants"}
GAR_MP, GAR_DAYS = 5000, 365   # a police and railway-guard garrison: manpower and political power, renewed yearly
GAR_CAP0 = 3                   # garrisons that can run at once; the Public Security focuses raise it (MAN_gar_cap)

def sec_effects(ind, BANDS):
    def band_hit(n_amt):
        s = ""
        for n, (_, _, homes, _) in BANDS.items():
            cond = " ".join(f"state = {sid}" for sid, _ in homes)
            s += f"if = {{ limit = {{ OR = {{ {cond} }} ROOT = {{ check_variable = {{ MAN_band{n} > 0 }} }} }} ROOT = {{ subtract_from_variable = {{ MAN_band{n} = {n_amt} }} }} }}\n"
        return s
    E = ""
    for key, nm, icon, days, pp, lab, cp, gate, cd in SEC:
        pay = (f"add_political_power = -{pp}\n" if pp else "") + (f"subtract_from_variable = {{ MAN_labour = {lab} }}\n" if lab else "") + (f"add_command_power = -{cp}\n" if cp else "")
        body = ""
        if days: body += f"set_state_flag = MAN_{key}_on\nset_variable = {{ MAN_{key} = {days} }}\n"
        if cd: body += f"set_state_flag = {{ flag = MAN_{key}_cd days = {cd} }}\n"
        if key == "inf": body += "set_state_flag = { flag = MAN_informants days = 180 }\n"
        if key == "gar":
            body += f"set_state_flag = {{ flag = MAN_garrisoned days = {GAR_DAYS} }}\n"
            pay += f"add_manpower = -{GAR_MP}\n"
        body += "ROOT = {\n" + ind(pay, 1) + "}\n"
        E += f"MAN_{key}_begin = {{\n" + ind(body, 1) + "}\n\n"
    E += ("MAN_sw_done = {\n\tset_temp_variable = { MAN_s = ROOT.MAN_fav_kw }\n\tdivide_temp_variable = { MAN_s = 10 }\n\tadd_to_temp_variable = { MAN_s = 10 }\n"
          "\tif = { limit = { has_state_flag = MAN_informants } multiply_temp_variable = { MAN_s = 1.5 } }\n\tsubtract_from_variable = { MAN_bandit = MAN_s }\n"
          "\tclamp_variable = { var = MAN_bandit min = 0 max = 100 }\n" + ind(band_hit(6), 1) +
          "\tROOT = { add_stability = -0.005 army_experience = 1 }\n\trandom_list = {\n\t\t70 = { }\n\t\t30 = { set_state_flag = { flag = MAN_grievance days = 120 } }\n\t}\n}\n\n")
    E += ("MAN_hm_done = {\n\tset_state_flag = MAN_hamlets\n\tadd_dynamic_modifier = { modifier = MAN_hamlets_dm }\n\tsubtract_from_variable = { MAN_bandit = 15 }\n"
          "\tclamp_variable = { var = MAN_bandit min = 0 max = 100 }\n" + ind(band_hit(10), 1) + "\tROOT = { add_stability = -0.02 }\n}\n\n")
    E += "MAN_bh_done = {\n\tset_state_flag = MAN_blockhouses\n}\n\n"
    wk = ""
    for key in ("sw", "hm", "bh"):
        wk += (f"every_owned_state = {{\n\tlimit = {{ has_state_flag = MAN_{key}_on }}\n\tsubtract_from_variable = {{ MAN_{key} = 7 }}\n"
               f"\tif = {{\n\t\tlimit = {{ check_variable = {{ MAN_{key} < 0.5 }} }}\n\t\tclr_state_flag = MAN_{key}_on\n\t\tMAN_{key}_done = yes\n\t}}\n}}\n")
    E += "MAN_sec_orders_weekly = {\n" + ind(wk, 1) + "}\n\n"
    # AI: one sweep a month where it hurts most, hamlets and blockhouses when rich enough
    ai = ""
    for i, s in enumerate(sorted(STATES, key=lambda x: -BANDIT0[x])):   # garrison the worst ungarrisoned province
        ai += (f"{'if' if i == 0 else 'else_if'} = {{\n\tlimit = {{ has_political_power > 40 has_manpower > {GAR_MP * 3} check_variable = {{ MAN_gar_n < MAN_gar_cap }} "
               f"{s} = {{ is_owned_and_controlled_by = ROOT check_variable = {{ MAN_bandit > 20 }} NOT = {{ has_state_flag = MAN_garrisoned }} }} }}\n\t{s} = {{ MAN_gar_begin = yes }}\n}}\n")
    for i, s in enumerate(sorted(STATES, key=lambda x: -BANDIT0[x])):
        ai += (f"{'if' if i == 0 else 'else_if'} = {{\n\tlimit = {{ has_political_power > 50 command_power > 30 "
               f"{s} = {{ is_owned_and_controlled_by = ROOT check_variable = {{ MAN_bandit > 35 }} NOT = {{ has_state_flag = MAN_sw_on }} NOT = {{ has_state_flag = MAN_sw_cd }} }} }}\n\t{s} = {{ MAN_sw_begin = yes }}\n}}\n")
    ai += ("if = {\n\tlimit = { has_completed_focus = MAN_sec_collective_hamlets has_political_power > 90 check_variable = { MAN_labour > 30 } }\n"
           "\trandom_owned_controlled_state = {\n\t\tlimit = { " + MANCHURIA_TRIGGER + " check_variable = { MAN_bandit > 50 } NOT = { has_state_flag = MAN_hamlets } NOT = { has_state_flag = MAN_hm_on } }\n\t\tMAN_hm_begin = yes\n\t}\n}\n")
    ai += ("if = {\n\tlimit = { has_completed_focus = MAN_sec_blockhouses has_political_power > 90 check_variable = { MAN_labour > 30 } }\n"
           "\trandom_owned_controlled_state = {\n\t\tlimit = { " + MANCHURIA_TRIGGER + " check_variable = { MAN_bandit > 30 } NOT = { has_state_flag = MAN_blockhouses } NOT = { has_state_flag = MAN_bh_on } }\n\t\tMAN_bh_begin = yes\n\t}\n}\n")
    E += "MAN_sec_ai = {\n\tif = {\n\t\tlimit = { is_ai = yes }\n" + ind(ai, 2) + "\t}\n}\n\n"
    return E

def sec_gui(T, I, B, props, trig, eff, loc, y):
    # what the operations are paid with, so a refused click is never a mystery
    b = T("MAN_sbp_res", 10, y, "MAN_SBP_RES", 480, tt="MAN_SBP_RES_TT")
    loc("MAN_SBP_RES", "§gAvailable:§! £pol_power §Y[?political_power|0]§!  £command_power §Y[?command_power|0]§!  £manpower_texticon §Y[?manpower_k|0]k§!  labour §Y[?MAN_labour|0]k§!  §gGarrisons§! §Y[?MAN_gar_n|0]/[?MAN_gar_cap|0]§!")
    loc("MAN_SBP_RES_TT", "What security operations are paid with. An order whose cost you cannot meet does nothing when clicked: hover it to see the cost and what you have.")
    y += 22
    b += T("MAN_sbp_h", 10, y, "MAN_SBP_H", 100, tt="MAN_SBP_H_TT")
    b += T("MAN_sbp_hb", 112, y, "MAN_SBP_HB", 110, tt="MAN_SBP_HB_TT")
    b += T("MAN_sbp_ho", 372, y, "MAN_SBP_HO", 140, tt="MAN_SBP_H_TT")
    loc("MAN_SBP_H", "§gProvince§!")
    loc("MAN_SBP_HB", "§gBanditry§! (0 to 100)")
    loc("MAN_SBP_HO", "§gOperations§!")
    loc("MAN_SBP_HB_TT", "£pol_violence §Obanditry§! in the province: penalties start at §Y25§! and worsen at §Y45§!, §Y65§! and §Y85§!. It cuts the Plan's output there.")
    loc("MAN_SBP_H_TT", "§OSecurity operations§!\\n£white_dot §OPolice Garrison§!: a year of police and railway guards, paid in £pol_power and manpower\\n£white_dot §OPunitive Sweep§!: paid in £command_power, repeatable every §Y60§! days\\n£white_dot §OCollective Hamlets§!, §OBlockhouse Lines§! and §OInformant Networks§! unlock through the focus tree"
        "\\n£white_dot Works under way finish on their own; hover a button for costs and effects")
    y += 22
    for s in STATES:
        own = f"{s} = {{ is_owned_by = ROOT }}"
        b += T(f"MAN_sb_sn_{s}", 10, y + 3, f"[{s}.GetName]", 100)
        b += I(f"MAN_sb_sbar_{s}", 112, y + 8, "GFX_MAN_bar_red_small")
        props.append((f"MAN_sb_sbar_{s}", f"MAN_f_bl_{s}"))
        b += T(f"MAN_sb_sv_{s}", 196, y + 3, f"MAN_SB_SV_{s}", 30)
        b += T(f"MAN_sb_st_{s}", 228, y + 3, f"[ROOT.GetMANSecProv_{s}]", 140)
        for el in (f"MAN_sb_sn_{s}", f"MAN_sb_sbar_{s}", f"MAN_sb_sv_{s}", f"MAN_sb_st_{s}"):
            trig.append(f"{el}_visible = {{ {own} }}")
        loc(f"MAN_SB_SV_{s}", f"[?MAN_bl_{s}|0]")
        for i, (key, nm, icon, days, pp, lab, cp, gate, cd) in enumerate(SEC):
            el = f"MAN_sb_{key}_{s}"
            b += B(el, 372 + i * 28, y, icon, f"MAN_SB_{key.upper()}_{s}_TT", scale=0.75)
            vis = f"{s} = {{ is_owned_by = ROOT"
            if key == "sw": vis += " check_variable = { MAN_bandit > 9.99 } NOT = { has_state_flag = MAN_sw_on }"
            else: vis += f" NOT = {{ has_state_flag = {SEC_DONE_FLAG[key]} }}" + (f" NOT = {{ has_state_flag = MAN_{key}_on }}" if days else "")
            vis += " }"
            if gate: vis += f" has_completed_focus = {gate}"
            trig.append(f"{el}_visible = {{ {vis} }}")
            en = f"has_political_power > {pp - 0.01}" + (f" check_variable = {{ MAN_labour > {lab - 0.01} }}" if lab else "") + (f" command_power > {cp - 0.01}" if cp else "")
            if key == "gar": en += f" has_manpower > {GAR_MP - 1} check_variable = {{ MAN_gar_n < MAN_gar_cap }}"
            en += f" {s} = {{ is_controlled_by = ROOT" + (" NOT = { has_state_flag = MAN_sw_cd }" if key == "sw" else "") + " }"
            trig.append(f"{el}_click_enabled = {{ {en} }}")
            eff.append(f"{el}_click = {{ {s} = {{ MAN_{key}_begin = yes }} MAN_sec_refresh = yes MAN_ui_refresh = yes }}")
            cost = f"§Y{pp}§! £pol_power" + (f", §Y{lab}k§! £manpower_texticon §Ylabour§!" if lab else "") + (f", §Y{cp}§! £command_power" if cp else "")
            if key == "gar": cost += f", §Y{GAR_MP // 1000}k§! £manpower_texticon manpower"
            have = "£pol_power §Y[?political_power|0]§!" + (", £manpower_texticon §Y[?MAN_labour|0]k§! labour" if lab else "") + \
                   (", £command_power §Y[?command_power|0]§!" if cp else "") + (", £manpower_texticon §Y[?manpower_k|0]k§! manpower" if key == "gar" else "")
            cost += f"\\n£white_dot You have: {have}"
            what = {"gar": f"For §Y{GAR_DAYS}§! days: §G-0.08§! £pol_violence §Obanditry§! growth a week from police posts and railway guards\\n£white_dot Renew it when it runs out"
                           "\\n£white_dot Garrisons in use: §Y[?MAN_gar_n|0]§! of §Y[?MAN_gar_cap|0]§! (the §OPublic Security§! focuses allow more)",
                    "sw": f"After §Y30§! days: £pol_violence §Obanditry§! §G-10§! to §G-20§! (more with §LKwantung Army Staff§! favour, ×1.5 with an §OInformant Network§!), local £nato_unit_irregular_infantry_icon_small §ORoute Army§! §G-6§!"
                          "\\n£white_dot §R30%§! chance of reprisals: a §Ogrievance§! for 120 days (§R+0.15§! banditry growth a week here)\\n£white_dot Repeatable every §Y60§! days",
                    "hm": "After §Y120§! days: £pol_violence §Obanditry§! §G-15§!, §G-0.25§! a week for good, local £nato_unit_irregular_infantry_icon_small §ORoute Army§! §G-10§!\\n£white_dot §R-5%§! local resources, §R-10%§! recruitable population, §R-2%§! stability",
                    "bh": "After §Y60§! days: §G-0.10§! £pol_violence §Obanditry§! growth a week for good",
                    "inf": "For §Y180§! days: §G-0.15§! £pol_violence §Obanditry§! growth a week, and §OPunitive Sweeps§! here are §G50%§! stronger"}[key]
            loc(f"MAN_SB_{key.upper()}_{s}_TT", f"§O{nm}§!: §C{SNAME[s]}§!\\n£white_dot Cost: {cost}\\n£white_dot {what}")
        y += 26
    return b, y

def sec_sl(DT):
    s = ""
    for st in STATES:
        cases = [(f"{st} = {{ has_state_flag = MAN_sw_on }}", "MAN_SPS_SW", "§OSweep under way§!"),
                 (f"{st} = {{ has_state_flag = MAN_hm_on }}", "MAN_SPS_HM", "§OBuilding hamlets§!"),
                 (f"{st} = {{ has_state_flag = MAN_bh_on }}", "MAN_SPS_BH", "§OBuilding blockhouses§!"),
                 (f"{st} = {{ has_state_flag = MAN_grievance }}", "MAN_SPS_GR", "§RGrievance§!"),
                 (f"{st} = {{ has_state_flag = MAN_hamlets has_state_flag = MAN_blockhouses }}", "MAN_SPS_HB", "§GHamlets, blockhouses§!"),
                 (f"{st} = {{ has_state_flag = MAN_hamlets }}", "MAN_SPS_H", "§GHamlets§!"),
                 (f"{st} = {{ has_state_flag = MAN_blockhouses }}", "MAN_SPS_B", "§GBlockhouses§!"),
                 (f"{st} = {{ has_state_flag = MAN_garrisoned }}", "MAN_SPS_G", "§gGarrisoned§!"),
                 ("", "MAN_SPS_NONE", "")]
        s += DT(f"GetMANSecProv_{st}", cases)
    return s
