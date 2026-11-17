"""Manchukuo focus tree, v2.
 - Economy (x0-13): asymmetric Industrial Development Plan tree with trade-off choice pairs that feed the Plan, the Bureaucracy and Public Security.
 - Politics (x15-24): rebuilt. Ishiwara's Concordia line vs An Army with a State, both driving the Hsinking Bureaucracy minigame.
 - Public Security (x30-36, y9-12) under the society branch.
 - Military and society branches keep their focuses but gain minigame hooks (TIE).
"""
from man_common import *
import shutil
import man_sites as SI
import man_systems as MS

L = []
def loc(k, v): L.append((k, v))
QN = dict(QUOTAS)
TT = {}   # tooltip key -> text
INST = {"kw": "Kwantung Army Staff", "gab": "General Affairs Board", "ind": "Ministry of Industry", "mgy": "Mangyo", "smr": "Mantetsu"}
LINE = {"kw": "$MODIFIER_ARMY_ORG_FACTOR$", "gab": "$MODIFIER_POLITICAL_POWER_FACTOR$", "ind": "$MODIFIER_PRODUCTION_SPEED_BUILDINGS_FACTOR$",
        "mgy": "$MODIFIER_INDUSTRIAL_CAPACITY_FACTOR$", "smr": "$modifier_production_speed_infrastructure_factor$"}

def sk(x): return ("m" if x < 0 else "") + str(abs(x)).replace(".", "_")
def sg(x, good_if_pos=True, pct=False):
    good = (x > 0) == good_if_pos
    v = f"{int(round(abs(x) * 100))}%" if pct else f"{abs(x):g}"
    return f"{'§G' if good else '§R'}{'+' if x > 0 else '-'}{v}§!"
def tt(key, text): TT[key] = text; return f"custom_effect_tooltip = {key}\n"
def zcap(n): return f"add_to_variable = {{ MAN_zone_cap = {n} }}\n" + tt(f"MAN_tt_zcap_{n}", f"Development zone allowance: §G+{n}§!")
def slots(n): return f"add_to_variable = {{ MAN_proj_slots = {n} }}\n" + tt(f"MAN_tt_slots_{n}", f"Concurrent plan projects: §G+{n}§!")
def unz(z, nm): return f"set_country_flag = MAN_zone_unl_{z}\n" + tt(f"MAN_tt_unl_{z}", f"Unlocks the §Y{nm}§! designation")
def lab(n): return f"add_to_variable = {{ MAN_labour = {n} }}\n" + tt(f"MAN_tt_labour{'' if n > 0 else 'x'}_{sk(n)}", f"Labour pool: {sg(n)}k workers")
def inc(x): return f"add_to_variable = {{ MAN_labour_income = {x} }}\n" + tt(f"MAN_tt_inc_{sk(x)}", f"Labour income: {sg(x)}k workers a week")
def qf(x): return f"add_to_variable = {{ MAN_quota_focus = {x} }}\n" + tt(f"MAN_tt_qf_{sk(x)}", f"Planning efficiency: {sg(x, pct=True)}")
def fav(k, n): s = f"m{-n}" if n < 0 else f"{n}"; return f"add_to_variable = {{ MAN_fav_{k} = {n} }}\n" + f"custom_effect_tooltip = MAN_tt_fav_{k}_{s}\n"
def pat(n): s = f"m{-n}" if n < 0 else f"{n}"; return f"add_to_variable = {{ MAN_kw_pat = {n} }}\ncustom_effect_tooltip = MAN_tt_pat_{s}\n"
def qa(k, n): return f"add_to_variable = {{ MAN_q_{k} = {n} }}\ncustom_effect_tooltip = MAN_tt_q_{k}_{n}_flat\n"
# ---- system knobs (read by MAN_systems_effects)
def dt(k, n): return f"add_to_variable = {{ MAN_dt_{k} = {n} }}\n" + tt(f"MAN_tt_dt_{k}_{sk(n)}", f"Level that §Y{INST[k]}§! favour drifts back to: {sg(n)}")
def tc(k, x): return f"add_to_variable = {{ MAN_tc_{k} = {x} }}\n" + tt(f"MAN_tt_tc_{k}_{sk(x)}", f"§YHsinking Bureaucracy§!, §Y{INST[k]}§! line: {LINE[k]} {sg(x, pct=True)}")
def pdrift(x): return f"add_to_variable = {{ MAN_pat_drift = {x} }}\n" + tt(f"MAN_tt_pdrift_{sk(x)}", f"Kwantung Army patience: {sg(x)} every week")
def bg(x): return f"add_to_variable = {{ MAN_bgrow_g = {x} }}\n" + tt(f"MAN_tt_bg_{sk(x)}", f"Banditry growth in every province: {sg(x, good_if_pos=False)} a week")
def gcap(n): return f"add_to_variable = {{ MAN_gar_cap = {n} }}\n" + tt(f"MAN_tt_gcap_{n}", f"§OPolice Garrisons§! that can run at once: §G+{n}§!")
def drain(x): return f"add_to_variable = {{ MAN_band_drain = {x} }}\n" + tt(f"MAN_tt_drain_{sk(x)}", f"Strength of every Route Army: {sg(-x, good_if_pos=False)} a week")
def qb(k, x): return f"add_to_variable = {{ MAN_qb_{k} = {x} }}\n" + tt(f"MAN_tt_qb_{k}_{sk(x)}", f"§Y{QN[k]}§! quota points from plan projects: {sg(x, pct=True)}")
def relief(n): return f"add_to_variable = {{ MAN_review_relief = {n} }}\n" + tt(f"MAN_tt_relief_{sk(n)}", f"Annual Review requirement: {sg(-n, good_if_pos=False)}% total fulfilment")
def flag(f_, key, text): return f"set_country_flag = {f_}\n" + tt(key, text)
def sbandit(sids, n, key, text):
    return "every_owned_state = {\n\tlimit = { OR = { " + " ".join(f"state = {s}" for s in sids) + " } }\n\tadd_to_variable = { MAN_bandit = " + str(n) + " }\n}\n" + tt(key, text)
def beh(v, x, t): return f"add_to_variable = {{ var = MAN_behemoth_{v} value = {x} tooltip = {t} }}\n"
def BEH(*items): return "custom_effect_tooltip = MAN_eco_spirit_changed_tt\n" + "".join(beh(*i) for i in items)
def DREAM(*items): return "custom_effect_tooltip = MAN_dream_spirit_changed_tt\n" + "".join(f"add_to_variable = {{ var = MAN_dream_{v} value = {x} tooltip = {t} }}\n" for v, x, t in items)
def build(sid, typ, n): return f"{sid} = {{\n\tadd_extra_state_shared_building_slots = {n}\n\tadd_building_construction = {{ type = {typ} level = {n} instant_build = yes }}\n}}\n"
def res(sid, typ, n): return f"add_resource = {{ type = {typ} amount = {n} state = {sid} }}\n"
def mega(m): return f"unlock_decision_tooltip = MAN_mega_{m}\n"
def avt(key, text, trig):
    TT[key] = text
    return f"\t\tavailable = {{\n\t\t\tcustom_trigger_tooltip = {{\n\t\t\t\ttooltip = {key}\n{ind(trig, 4)}\t\t\t}}\n\t\t}}\n"
END = "hidden_effect = {\n\tforce_update_dynamic_modifier = yes\n\tMAN_pol_compute = yes\n\tMAN_plan_recalc = yes\n\tMAN_ui_refresh = yes\n}\n"

NW = lambda n: WS + "2197593000/gfx/interface/goals/NW_MAN - Manchukou/z_goal_MAN_" + n + ".dds"
NWR = lambda n: WS + "2197593000/gfx/interface/goals/z_goal_MAN_" + n + ".dds"
NWJ = lambda n: WS + "2197593000/gfx/interface/goals/JAP/JAP_" + n + ".dds"
WA = lambda n: WS + "2149567872/gfx/interface/goals/goal_" + n + ".dds"
OAK = lambda n: WS + "2566601386/gfx/interface/goals/jap/" + n
CH = lambda n: WS + "2834647264/gfx/interface/goals/man/" + n
EX = lambda n: "=" + n     # existing sprite

JAPWAR = "JAP = { OR = { has_war_with = CHI has_war_with = PRC } }"
F = []
def f(i, x, y, pre=(), mx=None, av="", cost=7, icon=None, flt="FOCUS_FILTER_INDUSTRY", name="", desc="", rew="", bypass="", ai=1):
    F.append(dict(id=i, x=x, y=y, pre=[list(g) for g in pre], mx=[mx] if isinstance(mx, str) else (mx or []), av=av, cost=cost, icon=icon,
                  flt=flt, name=name, desc=desc, rew=rew, bypass=bypass, ai=ai))

# =====================================================================================================
# ECONOMY: THE INDUSTRIAL DEVELOPMENT PLAN
# =====================================================================================================
# ---- spine
f("MAN_eco_miyazaki_blueprint", 6, 1, cost=5, icon=NWJ("resume_the_ishiwara_mission_in_manchukuo"), name="The Miyazaki Blueprint",
  desc="In 1936 Miyazaki Masayoshi's research association, working in secret for Colonel Ishiwara Kanji, drew up a five-year programme to turn Manchuria into the heavy-industry base for the war with the Soviet Union that Ishiwara believed was coming.",
  rew="set_country_flag = MAN_plan_unlocked\n" + tt("MAN_tt_plan_open", "Opens §YThe Industrial Development Plan§! decisions and board. Liaoning and Kirin are already surveyed; other provinces need a §YMantetsu Geological Survey§! before they can be designated.") + unz("hi", "Heavy Industry Zone") + unz("min", "Mining District") + zcap(2) + lab(20) + END)
f("MAN_eco_kishi_arrives", 5, 2, [["MAN_eco_miyazaki_blueprint"]], cost=5, icon=NW("power_of_progressive_bureaucrats"), flt="FOCUS_FILTER_POLITICAL", name="Kishi Comes to Hsinking",
  desc="Kishi Nobusuke, the brightest of Tokyo's 'reform bureaucrats', arrives as Vice-Minister of Industry. He will run the Plan as an experiment in state-directed capitalism that he means to take home one day.",
  rew="MAN_kishi_arrives = yes\n" + zcap(1) + slots(1) + BEH(("production_speed_buildings_factor", 0.05, "production_speed_buildings_factor_tt")) + END)
f("MAN_eco_mantetsu_research", 8, 2, [["MAN_eco_miyazaki_blueprint"]], cost=7, icon=EX("GFX_MAN_manetsu_research_department-905555"), flt="FOCUS_FILTER_RESEARCH", name="The Mantetsu Research Department",
  desc="The South Manchuria Railway's research department is the finest think tank in Asia: geologists, economists, agronomists and more than a few Marxists. Put it to work for the Plan.",
  rew="add_research_slot = 1\n" + fav("smr", 10) + flag("MAN_lines_unl", "MAN_tt_lines_unl", "Unlocks §YMantetsu railway line§! projects: Jehol, Tumen to Jiamusi, Heihe and the North Manchuria double track") + END)
f("MAN_eco_zone_planning", 3, 3, [["MAN_eco_kishi_arrives"]], cost=5, icon=NW("landscaping_program"), name="Regional Development Zones",
  desc="The planners divide the country into zones of specialised development, each tied to its railway, its river and its mines.",
  rew=zcap(2) + unz("pow", "Power and Water District") + fav("ind", 5) + END)
f("MAN_eco_first_plan", 5, 3, [["MAN_eco_kishi_arrives"]], cost=7, icon=EX("GFX_MAN_first_five_year_plan-905539"), name="The First Five-Year Plan",
  desc="In January 1937 the Five-Year Plan for Industrial Development is proclaimed: steel, coal, oil, power and machinery, all under state direction and Japanese management.",
  rew="set_variable = { MAN_plan_stage = 1 }\nset_country_flag = MAN_first_five_year_plan_active\nMAN_plan_begin = yes\n" + tt("MAN_tt_plan_begin", "The §YFirst Five-Year Plan§! begins. An §YAnnual Review§! of total fulfilment is held each plan year.") + pat(5) +
  BEH(("production_speed_buildings_factor", 0.10, "production_speed_buildings_factor_tt")) + END)

# ---- whose plan is it? (choice)
f("MAN_eco_prio_army", 4, 4, [["MAN_eco_first_plan"]], mx="MAN_eco_prio_balanced", icon=NWR("army_stands_for_economic_planning"), ai=3, name="Munitions First",
  desc="The Kwantung Army staff wrote the Plan and the staff will set its priorities: guns, shells and the steel to make them, with everything else to follow when there is time. The Army will be pleased; the Ministry of Industry will be told what to do.",
  rew=fav("kw", 10) + fav("ind", -5) + pat(5) + qb("mach", 0.25) +
  BEH(("production_speed_arms_factory_factor", 0.10, "production_speed_arms_factory_factor_tt"), ("industrial_capacity_factory", 0.03, "industrial_capacity_factory_tt")) + END)
f("MAN_eco_prio_balanced", 6, 4, [["MAN_eco_first_plan"]], mx="MAN_eco_prio_army", icon=NW("restoring_employee_morale"), ai=1, name="Kishi's Balanced Development",
  desc="Kishi argues that an arsenal without power stations, coal and fed workers is a stage set. The Plan will build the foundations first, and the munitions lines can wait their turn. The Army staff grumble about civilian timidity.",
  rew=fav("ind", 10) + fav("kw", -5) + pat(-5) + qf(0.05) + qb("power", 0.20) + qb("steel", 0.10) + inc(0.5) +
  BEH(("consumer_goods_factor", -0.03, "consumer_goods_expected_value_tt"), ("production_speed_arms_factory_factor", -0.10, "production_speed_arms_factory_factor_tt")) + END)

# ---- centre: the plan backbone
f("MAN_eco_labour_agency", 5, 5, [["MAN_eco_prio_army", "MAN_eco_prio_balanced"]], cost=5, icon=WA("MAN_labor_company"), flt="FOCUS_FILTER_MANPOWER", name="The Daito Koshi Labour Agency",
  desc="Manchuria has the land and the coal; it does not have the workers. The Greater East Company will recruit them in North China by the hundred thousand.",
  rew=lab(20) + inc(1) + "unlock_decision_tooltip = MAN_lab_daito\n" + END)
REV_AV = avt("MAN_tt_av_revised", "Japan is at war in China, or the Plan has reached its second year",
             "OR = {\n\t" + JAPWAR + "\n\tJAP = { has_completed_focus = JAP_war_china_incident }\n\tcheck_variable = { MAN_plan_year > 1.5 }\n}\n")
f("MAN_eco_revised_plan", 5, 6, [["MAN_eco_labour_agency"], ["MAN_eco_zone_planning"]], av=REV_AV, icon=NW("polygon_for_controlled_economy"), name="The Revised Plan",
  desc="With the China Incident the army demands more: in 1938 the Plan's targets are roughly doubled, and Japan's own planners make Manchuria the core of their materials programme.",
  rew="set_variable = { MAN_plan_stage = 2 }\nset_country_flag = MAN_revision_pending\n" +
  tt("MAN_tt_revise", "From the start of the next plan year, all quota targets: §Rx1.6§! (the review now under way is judged on the old targets)") + qf(0.10) + inc(1) + slots(1) + pat(10) + BEH(("industrial_capacity_factory", 0.05, "industrial_capacity_factory_tt")) + END)
f("MAN_eco_material_mobilisation", 4, 7, [["MAN_eco_revised_plan"]], icon=EX("GFX_MAN_the_aikawa_plan-905545"), name="The Materials Mobilisation Plan",
  desc="Tokyo's Planning Board now allocates steel, coal and shipping across the whole empire. Manchuria's share comes with priority for its projects.",
  rew=qf(0.05) + zcap(1) + slots(1) + "add_political_power = 50\n" + END)
f("MAN_eco_fengman_dam", 6, 7, [["MAN_eco_revised_plan"]], icon=WA("MAN_SM_electric"), name="The Fengman Dam",
  desc="A dam across the Sungari above Kirin, meant to be the largest hydroelectric plant in Asia.",
  rew=mega("fengman") + END)
f("MAN_eco_supung_dam", 7, 8, [["MAN_eco_fengman_dam"]], icon=EX("GFX_MAN_restructure_the_liaohe_river_flow-905562"), name="The Supung Dam",
  desc="With the Government-General of Korea, dam the Yalu at Supung and share the current between both banks.",
  rew=mega("supung") + END)
f("MAN_eco_labour_service", 3, 8, [["MAN_eco_material_mobilisation"]], mx="MAN_eco_contract_labour", icon=NWR("law_on_employment_of_forced_labor"), flt="FOCUS_FILTER_MANPOWER", ai=2, name="The Labour Service Law",
  desc="Conscript the labour: every able-bodied man owes the state months of work each year in the labour service corps. The sites will never lack hands again, and the villages will hate us for it.",
  rew=inc(2) + "add_stability = -0.05\n" + pat(5) + "every_owned_state = {\n\tlimit = { " + MANCHURIA_TRIGGER + " }\n\tset_state_flag = { flag = MAN_grievance days = 365 }\n}\n" +
  tt("MAN_tt_all_grievance", "Every Manchurian province gains a §Rgrievance§! for a year.") + BEH(("industrial_capacity_factory", 0.02, "industrial_capacity_factory_tt")) + END)
f("MAN_eco_contract_labour", 5, 8, [["MAN_eco_material_mobilisation"]], mx="MAN_eco_labour_service", icon=NW("wage_equality"), flt="FOCUS_FILTER_MANPOWER", name="Regulate the Labour Contractors",
  desc="Break the grip of the gang bosses who skim the coolies' wages, pay workers in cash and feed them properly. Fewer men, but they stay, and fewer runaways end up in the hills with a rifle.",
  rew=inc(1) + lab(20) + "add_stability = 0.03\n" + bg(-0.01) + fav("gab", 5) + END)
f("MAN_eco_first_plan_fulfilled", 4, 9, [["MAN_eco_labour_service", "MAN_eco_contract_labour"]], cost=5,
  av=avt("MAN_tt_av_model", "The §YFirst Five-Year Plan§! has concluded", "has_country_flag = MAN_first_fyp_complete\n"),
  icon=NWJ("transfer_the_Manchurian_experience_to_Japan"), flt="FOCUS_FILTER_POLITICAL", name="The Manchurian Model",
  desc="The First Plan is done. Its methods, its men and its controlled economy become the template for Japan's own wartime economy.",
  rew="add_political_power = 75\n" + fav("ind", 10) + dt("ind", 5) + BEH(("production_factory_max_efficiency_factor", 0.03, "production_factory_max_efficiency_factor_tt")) + END)
f("MAN_eco_second_plan", 5, 10, [["MAN_eco_first_plan_fulfilled"]], icon=EX("GFX_MAN_second_five_year_plan-905559"), name="The Second Five-Year Plan",
  desc="The Second Plan for 1942 to 1946 drops the dreams of balanced development: everything now serves the war.",
  rew="set_variable = { MAN_plan_stage = 3 }\nset_country_flag = MAN_second_five_year_plan_active\nclr_country_flag = MAN_revision_pending\n" +
  "".join(f"set_variable = {{ MAN_q_{k} = 0 }}\n" for k, _ in QUOTAS) +
  "set_variable = { MAN_qt_steel = 120 }\nset_variable = { MAN_qt_coal = 110 }\nset_variable = { MAN_qt_power = 100 }\nset_variable = { MAN_qt_mach = 140 }\n" +
  "".join(f"add_to_variable = {{ MAN_cap_{s_[0]} = {SI.site_ext(s_[5])} }}\n" for s_ in SI.SITES) +
  "".join(f"add_to_variable = {{ MAN_megacap_{m} = {n} }}\n" for m, n in MS.MEGA_EXT.items()) +
  "MAN_plan_begin = yes\n" + tt("MAN_tt_plan2_begin", "The §YSecond Five-Year Plan§! begins with new quota targets and a new round of Annual Reviews.") +
  tt("MAN_tt_plan2_ext", "Every Plan site gains §Y1§! or §Y2§! expansion stages, thermal stations §Y2§! more per province, and the §1Showa§! and §1Kirin Synthetic Fuel§! megaprojects more stages (quota only, no new buildings)") +
  slots(1) + zcap(1) + BEH(("industrial_capacity_factory", 0.05, "industrial_capacity_factory_tt")) + END)
f("MAN_eco_steel_rolling", 4, 11, [["MAN_eco_second_plan"]], icon=EX("GFX_MAN_breakthrough_in_steel_rolling-905560"), name="Breakthrough in Steel Rolling",
  desc="New rolling mills at Anshan turn out plate and sections instead of shipping pig iron to Japan.",
  rew=res(715, "steel", 60) + qa("steel", 15) + BEH(("production_factory_start_efficiency_factor", 0.05, "production_factory_start_efficiency_factor_tt")) + END)
f("MAN_eco_heavy_machinery", 6, 11, [["MAN_eco_second_plan"]], icon=EX("GFX_MAN_replacemanestsuscontrol-905551"), flt="FOCUS_FILTER_RESEARCH", name="Machine Tools for the Empire",
  desc="Manchurian shops start building the machine tools that Japan can no longer import from America.",
  rew=qa("mach", 15) + "add_tech_bonus = { name = MAN_eco_heavy_machinery bonus = 1.0 uses = 2 category = industry }\n" + END)
TWP_AV = avt("MAN_tt_av_twp", "Japan or Manchukuo is at war with a great power, or the Second Plan has reached its third year",
             "OR = {\n\tJAP = { has_war_with = USA }\n\tJAP = { has_war_with = ENG }\n\tJAP = { has_war_with = SOV }\n\thas_war_with = SOV\n\tcheck_variable = { MAN_plan_year > 2.5 }\n}\n")
f("MAN_eco_total_war_plan", 4, 12, [["MAN_eco_steel_rolling", "MAN_eco_heavy_machinery"]], mx="MAN_eco_preserve_base", av=TWP_AV, icon=NWJ("Manchurian_Cabinet"), ai=3, name="Everything for the Front",
  desc="The Pacific war turns the Second Plan into an emergency programme: munitions first, steel second, everything else last. Grain and cloth are requisitioned, and the countryside pays for it.",
  rew="set_variable = { MAN_plan_stage = 4 }\nmultiply_variable = { MAN_qt_mach = 1.5 }\nmultiply_variable = { MAN_qt_steel = 1.2 }\n" +
  tt("MAN_tt_twp", "Machinery and Munitions target: §Rx1.5§!, Iron and Steel target: §Rx1.2§!") + qf(0.10) + qb("mach", 0.20) + fav("kw", 10) + pat(10) +
  "add_stability = -0.10\n" + bg(0.03) +
  BEH(("production_speed_arms_factory_factor", 0.15, "production_speed_arms_factory_factor_tt"), ("consumer_goods_factor", -0.03, "consumer_goods_expected_value_tt")) + END)
f("MAN_eco_preserve_base", 6, 12, [["MAN_eco_steel_rolling", "MAN_eco_heavy_machinery"]], mx="MAN_eco_total_war_plan", av=TWP_AV, icon=OAK("focus_big_brother_jap_man.dds"), ai=1, name="Preserve the Industrial Base",
  desc="The planners refuse to strip the mills for one more year of shells. Maintenance, spare parts and the workers' rations come first, so that Manchuria can still produce in 1945. The Army staff call it defeatism.",
  rew="set_variable = { MAN_plan_stage = 4 }\n" + qf(0.10) + relief(10) + fav("ind", 10) + pat(-10) +
  BEH(("production_factory_max_efficiency_factor", 0.05, "production_factory_max_efficiency_factor_tt"), ("production_speed_buildings_factor", 0.10, "production_speed_buildings_factor_tt"),
      ("production_speed_arms_factory_factor", -0.10, "production_speed_arms_factory_factor_tt")) + END)
f("MAN_eco_behemoth", 5, 13, [["MAN_eco_total_war_plan", "MAN_eco_preserve_base"]], cost=10,
  av=avt("MAN_tt_av_behemoth", "At least §Y50%§! fulfilment of the current Plan, and §YArsenal of the Continent§! or §YContinental Supply Base§! completed",
         "check_variable = { MAN_plan_pct > 49.99 }\nOR = {\n\thas_completed_focus = MAN_eco_arsenal_of_empire\n\thas_completed_focus = MAN_eco_continental_supply\n}\n"), icon=WA("MAN_the_mukden_capital"), name="The Industrial Behemoth of the East",
  desc="From the Amur to the Yellow Sea, Manchuria is one great works: the arsenal of the continent and the reason the Empire can fight on.",
  rew=pat(15) + BEH(("industrial_capacity_factory", 0.10, "industrial_capacity_factory_tt"), ("production_factory_max_efficiency_factor", 0.05, "production_factory_max_efficiency_factor_tt")) + END)

# Ayukawa's 1936 report opens the Mangyo-or-Mantetsu contest, from whichever of the two focuses before that choice comes first
MQ_START = ("custom_effect_tooltip = MAN_tt_mq_start\nhidden_effect = {\n\tif = {\n\t\tlimit = { NOT = { has_country_flag = MAN_mq_started } }\n"
            "\t\tset_country_flag = MAN_mq_started\n\t\tcountry_event = { id = manchukou.137 days = 7 }\n\t\tJAP = { country_event = { id = manchukou.137 days = 7 } }\n\t}\n}\n")
# ---- left: heavy industry, Mangyo vs Mantetsu, arms
f("MAN_eco_showa_steel", 1, 4, [["MAN_eco_first_plan"]], icon=NWR("modernize_seva_steel_plant"), name="The Showa Steel Works",
  desc="Anshan's Showa Steel Works is already the biggest steel plant in Japan's empire outside the home islands. The Plan will triple it.",
  rew=mega("showa") + res(716, "steel", 40) + qa("steel", 8) + END)
f("MAN_eco_benxihu", 0, 5, [["MAN_eco_showa_steel"]], icon=CH("chire_goal_MAN_generic_coal_mining.dds"), name="Benxihu Coal and Iron",
  desc="The Okura-financed works at Benxihu make the low-phosphorus pig iron Japan's arsenals need for gun barrels.",
  rew=res(716, "steel", 40) + res(716, "coal", 30) + qa("steel", 6) + qa("coal", 6) + MQ_START + END)
f("MAN_eco_control_law", 2, 5, [["MAN_eco_showa_steel"]], icon=EX("GFX_MAN_one_company_one_industry-905547"), name="The Important Industries Control Law",
  desc="Under the 1937 law every key industry is assigned to a single 'special company' answerable to the state: one industry, one company.",
  rew=qf(0.05) + slots(1) + fav("ind", 5) + MQ_START + BEH(("production_factory_efficiency_gain_factor", 0.10, "production_factory_efficiency_gain_factor_tt")) + END)
MGY_AV = avt("MAN_tt_av_mangyo", "Ayukawa won §YThe Mantetsu Question§!, or §YMangyo§! favour is at least 65",
             "OR = {\n\thas_country_flag = MAN_ayukawa_vs_matsuoka_Ayukawa_win_flag\n\tcheck_variable = { MAN_fav_mgy > 64.99 }\n}\n")
SMR_AV = avt("MAN_tt_av_smr", "Matsuoka won §YThe Mantetsu Question§!, or §YMantetsu§! favour is at least 65",
             "OR = {\n\thas_country_flag = MAN_ayukawa_vs_matsuoka_Matsuoka_win_flag\n\tcheck_variable = { MAN_fav_smr > 64.99 }\n}\n")
f("MAN_eco_found_mangyo", 0, 6, [["MAN_eco_benxihu", "MAN_eco_control_law"]], mx="MAN_eco_smr_concern", av=MGY_AV, icon=WA("MAN_mangyo"), ai=2, name="Found Mangyo",
  desc="Ayukawa Yoshisuke moves the whole Nissan combine to Manchuria as the Manchurian Industrial Development Company. Mantetsu's mines and mills are handed over to it.",
  rew="MAN_ayukawa_arrives = yes\nset_country_flag = MAN_mangyo_founded\ncustom_effect_tooltip = MAN_mangyo_founded_tt\n" + fav("mgy", 15) + fav("smr", -15) + dt("mgy", 5) + inc(0.5) +
  BEH(("industrial_capacity_factory", 0.05, "industrial_capacity_factory_tt")) + END)
f("MAN_eco_smr_concern", 2, 6, [["MAN_eco_benxihu", "MAN_eco_control_law"]], mx="MAN_eco_found_mangyo", av=SMR_AV, icon=EX("GFX_MAN_manestu_reborn-905549"), name="Mantetsu's Industrial Empire",
  desc="Matsuoka keeps the railway company whole: mines, steel, chemicals and shipping stay under Mantetsu, run as one great combine along the lines.",
  rew="set_country_flag = MAN_mantetsu_founded\ncustom_effect_tooltip = MAN_mantetsu_founded_tt\n" + fav("smr", 15) + fav("mgy", -15) + dt("smr", 5) + slots(1) +
  BEH(("production_speed_infrastructure_factor", 0.15, "production_speed_infrastructure_factor_tt")) + END)
# Mangyo line: long, capital and vehicles
f("MAN_eco_nissan_moves", 0, 7, [["MAN_eco_found_mangyo"]], icon=NW("manchurian_industrial_development_company"), name="Nissan Moves to Manchuria",
  desc="Nissan's holding company, its engineers and its share register move to Hsinking. Ayukawa promises the army an automobile, aircraft and machine-tool industry within five years.",
  rew=qa("mach", 10) + fav("mgy", 5) + END)
f("MAN_eco_american_capital", 0, 8, [["MAN_eco_nissan_moves"]], icon=EX("GFX_MAN_learn_from_american_steelmakers-905557"), flt="FOCUS_FILTER_RESEARCH", name="Courting American Capital",
  desc="Ayukawa hopes to bring American money and machinery into Manchuria. Washington will never agree to the loans, but the licences and the engineers' visits are worth something. The Army staff watch the Americans closely.",
  rew="add_tech_bonus = { name = MAN_eco_american_capital bonus = 1.0 uses = 1 category = construction_tech }\nadd_tech_bonus = { name = MAN_eco_american_capital_x bonus = 1.0 uses = 1 category = excavation_tech }\n" +
  fav("mgy", 5) + pat(-5) + END)
f("MAN_eco_dowa", 0, 9, [["MAN_eco_american_capital"]], icon=CH("goal_MAN_dowa.dds"), name="Dowa Automobile",
  desc="The Dowa Automobile Company at Mukden assembles lorries for the Kwantung Army from Japanese and imported parts.",
  rew="add_tech_bonus = { name = MAN_eco_dowa bonus = 1.0 uses = 2 category = motorized_equipment }\n" + qa("mach", 8) + fav("kw", 5) + END)
# Mantetsu line: short, rails and coal
f("MAN_eco_smr_industrial", 2, 7, [["MAN_eco_smr_concern"]], icon=NW("mantetsu_industrial_department"), name="The Mantetsu Industrial Department",
  desc="Mantetsu reorganises its sprawling subsidiaries into an industrial department with its own engineers and capital, and the Fushun open pit, the largest coal mine in Asia, gets new excavators.",
  rew=res(716, "coal", 40) + qa("mach", 6) + qa("coal", 8) + fav("smr", 5) + END)
f("MAN_eco_asia_express", 2, 8, [["MAN_eco_smr_industrial"]], icon=EX("GFX_MAN_create_the_main_railway_administration-905541"), name="The Asia Express",
  desc="Mantetsu's streamlined Asia Express runs from Dairen to Hsinking at over a hundred kilometres an hour. The line behind it gets new track, signals, yards and armoured trains.",
  rew="".join(f"{s} = {{ add_building_construction = {{ type = infrastructure level = 1 instant_build = yes }} }}\n" for s in (716, 328, 714)) +
  "".join(qa(k, 3) for k, _ in QUOTAS) + fav("smr", 5) + bg(-0.01) + END)
f("MAN_eco_mukden_arsenal", 1, 10, [["MAN_eco_dowa", "MAN_eco_asia_express"]], icon=NWJ("preparing_Manchuria_for_war"), name="The Mukden Arsenal",
  desc="Zhang Zuolin built the largest arsenal in China at Mukden. Retooled for Japanese patterns, it can arm the whole Manchukuo Army.",
  rew=mega("arsenal") + BEH(("production_speed_arms_factory_factor", 0.10, "production_speed_arms_factory_factor_tt")) + END)
# who gets the guns? (choice)
f("MAN_eco_kw_arms", 0, 11, [["MAN_eco_mukden_arsenal"]], mx="MAN_eco_own_arms", icon=OAK("Kwantung_Army_2.dds"), ai=3, name="Supply the Kwantung Army",
  desc="The arsenals deliver to the Kwantung Army first. It is the only army that can stop the Soviets, and it is the army that decides who governs in Hsinking.",
  rew=fav("kw", 10) + pat(10) + pdrift(0.02) + BEH(("production_speed_arms_factory_factor", 0.15, "production_speed_arms_factory_factor_tt"), ("consumer_goods_factor", 0.02, "consumer_goods_expected_value_tt")) + END)
f("MAN_eco_own_arms", 2, 11, [["MAN_eco_mukden_arsenal"]], mx="MAN_eco_kw_arms", icon=OAK("MAN_Manchukuo_Imperial_Army.png"), name="Arm the Manchukuo Army",
  desc="Keep the new rifles and mortars for the Manchukuo Imperial Army and its anti-bandit columns. A native army with modern weapons makes the Kwantung Army staff nervous.",
  rew=drain(0.08) + fav("kw", -5) + pat(-10) + BEH(("recruitable_population_factor", 0.02, "recruitable_population_factor_tt")) + END)
f("MAN_eco_manshu_hikoki", 0, 12, [["MAN_eco_kw_arms", "MAN_eco_own_arms"]], icon=WA("MAN_MAMC"), name="Manchuria Aircraft Manufacturing",
  desc="Manshu Hikoki, founded in 1938 and soon a Mangyo company, builds and repairs aircraft for the Kwantung Army at Mukden and Harbin.",
  rew=mega("mamc") + "air_experience = 15\n" + fav("mgy", 5) + END)
f("MAN_eco_powder_company", 2, 12, [["MAN_eco_kw_arms", "MAN_eco_own_arms"]], icon=NWR("manchurian_powder_company"), name="The Manchurian Powder Company",
  desc="Explosives and propellant from Kirin's chemical works keep the arsenals' shell lines running.",
  rew="add_tech_bonus = { name = MAN_eco_powder_company bonus = 1.0 uses = 2 category = artillery }\n" + qa("mach", 8) + END)
f("MAN_eco_arsenal_of_empire", 1, 13, [["MAN_eco_manshu_hikoki", "MAN_eco_powder_company"]], cost=10, icon=OAK("man_mil_dev.dds"), name="Arsenal of the Continent",
  desc="Manchuria's arsenals no longer just repair Japanese weapons: they design and build their own, for the Manchukuo Army and for the fronts in China.",
  rew=qa("mach", 15) + BEH(("production_speed_arms_factory_factor", 0.10, "production_speed_arms_factory_factor_tt")) + END)

# ---- right: fuel and metals (hangs off Mantetsu's research department)
f("MAN_eco_fushun_shale", 8, 3, [["MAN_eco_mantetsu_research"]], icon=NWR("fushun_coal_liquefaction_plant"), name="Fushun Oil Shale",
  desc="Above Fushun's coal lies a thick bed of oil shale. Distilled, it yields the fuel oil the navy craves.",
  rew="set_country_flag = MAN_shale_known\n" + tt("MAN_tt_shale", "Unlocks the §YFushun Oil Shale Retorts§! site in Liaoning (Mining District).") + build(716, "synthetic_refinery", 1) + qa("coal", 8) + END)
f("MAN_eco_hydrogenation", 7, 4, [["MAN_eco_fushun_shale"]], mx="MAN_eco_synthetic_fuel", icon=WA("MAN_SM_GAS"), flt="FOCUS_FILTER_RESEARCH", name="The Navy's Hydrogenation Process",
  desc="The Navy's fuel laboratory has its own coal hydrogenation process, and Mantetsu will build it at Fushun. Cheap and Japanese, but the Army resents the Navy's say in Manchurian industry.",
  rew=build(716, "synthetic_refinery", 1) + "add_tech_bonus = { name = MAN_eco_hydrogenation bonus = 1.0 uses = 1 category = synth_resources }\n" + qb("coal", 0.15) + fav("smr", 5) + pat(-5) + END)
f("MAN_eco_synthetic_fuel", 9, 4, [["MAN_eco_fushun_shale"]], mx="MAN_eco_hydrogenation", icon=NWR("purchase_german_licenses"), ai=2, name="The Ruhrchemie Licence",
  desc="Mitsui buys the German Fischer-Tropsch licence, and a great synthetic fuel works rises at Kirin on the German model. Expensive, but it is oil beyond the reach of an American embargo.",
  rew=mega("kirin_fuel") + "add_political_power = -50\n" + BEH(("production_speed_synthetic_refinery_factor", 0.15, "production_speed_synthetic_refinery_factor_tt")) + END)
f("MAN_eco_light_metals", 8, 5, [["MAN_eco_hydrogenation", "MAN_eco_synthetic_fuel"]], icon=NWR("manchu_society_for_light_metals"), name="Manchurian Light Metals",
  desc="Aluminium from Liaoning's alunite shale at the Fushun works, for the Empire's aircraft.",
  rew=res(716, "aluminium", 60) + qa("steel", 4) + qa("mach", 4) + END)
OIL = ("random_list = {\n\t25 = { country_event = { id = man_behemoth.33 days = 30 } custom_effect_tooltip = MAN_tt_oil_strike }\n\t75 = { custom_effect_tooltip = MAN_tt_oil_dry }\n}\n"
       "add_tech_bonus = { name = MAN_eco_oil_surveys bonus = 1.0 uses = 1 category = synth_resources }\n")
f("MAN_eco_oil_surveys", 7, 6, [["MAN_eco_light_metals"]], icon=WS + "1521695605/gfx/interface/goals/oil_derrick.png", flt="FOCUS_FILTER_RESEARCH", name="Drill for Manchurian Oil",
  desc="Japanese geologists have drilled all over the northeast and found nothing. One more campaign of deep wells in the Sungari plain might change that.",
  rew=OIL + END)
loc("MAN_tt_oil_strike", "§G25% chance:§! strike oil in Heilungkiang")
loc("MAN_tt_oil_dry", "§Y75% chance:§! the wells come up dry")
f("MAN_eco_strategic_stockpiles", 9, 6, [["MAN_eco_light_metals"]], icon=EX("GFX_MAN_the_matsuoka_plan-905543"), name="Strategic Resource Stockpiles",
  desc="Ore, coke and fuel are hoarded against the day the sea lanes close.",
  rew=BEH(("local_resources_factor", 0.05, "local_resources_factor_tt")) + END)
f("MAN_eco_aluminium_air", 9, 7, [["MAN_eco_strategic_stockpiles"]], icon=NWR("new_aluminum_plants"), name="Aluminium for the Air Arm",
  desc="New reduction works at Kirin and Antung, powered by the dams.",
  rew=res(328, "aluminium", 60) + qa("mach", 6) + END)

# ---- far right: land and settlement (hangs off Mantetsu's research department)
f("MAN_eco_soybean", 12, 3, [["MAN_eco_mantetsu_research"]], cost=5, icon=NWR("raise_plan_for_soybeans"), flt="FOCUS_FILTER_POLITICAL", name="The Soybean Economy",
  desc="Manchuria feeds half the world's soybean trade. Mantetsu's export monopoly pays for the Plan's first years.",
  rew="add_political_power = 60\n" + lab(10) + END)
f("MAN_eco_million_households", 11, 4, [["MAN_eco_soybean"]], mx="MAN_eco_korean_settlers", icon=NWJ("immigration_plan_to_Manchuria"), flt="FOCUS_FILTER_MANPOWER", ai=2, name="A Million Households in Twenty Years",
  desc="Tokyo's emigration plan will settle five million Japanese farmers in Manchuria by 1956, on land bought cheaply or simply taken from the Chinese and Koreans who farm it.",
  rew=unz("set", "Settlement and Grain Zone") + zcap(1) + inc(0.5) + fav("kw", 10) +
  "every_owned_state = {\n\tlimit = { OR = { state = 717 state = 714 } }\n\tset_state_flag = { flag = MAN_grievance days = 180 }\n}\n" + tt("MAN_tt_north_grievance", "Sungkiang and Heilungkiang gain a §Rgrievance§! for 180 days.") + END)
f("MAN_eco_korean_settlers", 13, 4, [["MAN_eco_soybean"]], mx="MAN_eco_million_households", icon=NWR("manchurian_koreans_leadership_program"), flt="FOCUS_FILTER_MANPOWER", name="The Manchuria Colonisation Company",
  desc="Let the Korean farmers come instead. The Sen-Man Takushoku company settles Korean families on the river flats, where they turn swamp into rice paddy. They work hard and cheaply, but the partisans of the Changbai forests are their cousins.",
  rew=unz("set", "Settlement and Grain Zone") + zcap(1) + inc(1) + lab(15) + fav("kw", -5) + bg(0.01) +
  "custom_effect_tooltip = MAN_tt_korean_waves\nhidden_effect = { country_event = { id = manchukou.52 days = 30 } }\n" + END)
f("MAN_eco_youth_corps", 11, 5, [["MAN_eco_million_households"]], icon=NW("land_preparation_for_japanese_colonists"), flt="FOCUS_FILTER_MANPOWER", name="The Youth Volunteer Corps",
  desc="Japanese boys of fifteen and sixteen are trained as armed pioneer-settlers on the Soviet border: farmers by day, sentries by night.",
  rew="add_manpower = 8000\n" + lab(15) + inc(0.5) + sbandit([717], -5, "MAN_tt_youth", "Banditry in Sungkiang: §G-5§!") + END)
f("MAN_eco_grain_quotas", 11, 6, [["MAN_eco_youth_corps", "MAN_eco_korean_settlers"]], mx="MAN_eco_agri_modern", icon=NWR("focus_on_agriculture"), flt="FOCUS_FILTER_POLITICAL", ai=2, name="Compulsory Grain Deliveries",
  desc="The shussha system: every village owes the state a fixed delivery of grain at fixed prices, whatever the harvest. The cities and the labour camps eat cheaply; the villages go hungry.",
  rew="add_political_power = 80\n" + inc(0.5) + "every_owned_state = {\n\tlimit = { has_state_flag = MAN_zone_set }\n\tadd_to_variable = { MAN_bandit = 5 }\n}\n" +
  tt("MAN_tt_grain", "Banditry in every Settlement and Grain Zone: §R+5§!") + BEH(("consumer_goods_factor", -0.02, "consumer_goods_expected_value_tt")) + END)
f("MAN_eco_agri_modern", 13, 6, [["MAN_eco_youth_corps", "MAN_eco_korean_settlers"]], mx="MAN_eco_grain_quotas", icon=EX("GFX_MAN_modernised_agriculture-905561"), flt="FOCUS_FILTER_STABILITY", name="Modernise Manchurian Agriculture",
  desc="Tractors, fertiliser from Dairen and Mantetsu's agronomists for the plain's farms. Slower to pay off, but a fed village does not feed the partisans.",
  rew="add_stability = 0.05\n" + bg(-0.01) + fav("smr", 5) + BEH(("consumer_goods_pct", -0.05, "consumer_goods_factor_tt")) + END)
f("MAN_eco_resource_board", 11, 7, [["MAN_eco_grain_quotas", "MAN_eco_agri_modern"], ["MAN_eco_strategic_stockpiles"]], icon=EX("GFX_MAN_expansionofmanestucontrol-905550"), name="The Raw Materials Control Board",
  desc="One board allocates every tonne of ore, coal and grain in the country.",
  rew=qa("coal", 6) + qa("steel", 6) + fav("gab", 5) + BEH(("local_resources_factor", 0.10, "local_resources_factor_tt")) + END)
f("MAN_eco_continental_supply", 10, 8, [["MAN_eco_resource_board"], ["MAN_eco_aluminium_air"]], cost=10, icon=OAK("focus_japan_manchoukuo_trade_resource.dds"), name="Continental Supply Base",
  desc="Manchuria becomes the Empire's larder and quarry on the continent, shipping coal, iron and grain south through Dairen and the Korean ports.",
  rew="JAP = { add_political_power = 50 }\n" + pat(10) + BEH(("local_resources_factor", 0.05, "local_resources_factor_tt")) + END)

# =====================================================================================================
# POLITICS: THE HSINKING BUREAUCRACY
# =====================================================================================================
PF = "FOCUS_FILTER_POLITICAL"
# ---- Ishiwara's Concordia (alternative)
f("MAN_restoring_control_to_the_concord_society", 17, 1, mx="MAN_an_army_with_a_state", flt=PF, ai=1, icon=EX("GFX_MAN_restoring_control_to_the_concord_society-905608"),
  av=avt("MAN_tt_av_concordia", "§YGeneral Affairs Board§! favour is at least 50", "check_variable = { MAN_fav_gab > 49.99 }\n"),
  name="Ishiwara's Concordia", cost=5,
  desc="Ishiwara Kanji created Manchukuo and now wants to let it go: the Concordia Association, not the Kwantung Army staff, should govern a true union of the five races. Half the staff think he is a prophet, the other half a traitor.",
  rew="add_political_power = 100\n" + fav("gab", 15) + fav("kw", -10) + pat(-10) + "custom_effect_tooltip = available_political_advisor\nshow_ideas_tooltip = MAN_ruan_zhenduo\n" +
  DREAM(("industrial_capacity_factory", -0.05, "industrial_capacity_factory_tt")) + END)
f("MAN_pol_east_asian_league", 16, 2, [["MAN_restoring_control_to_the_concord_society"]], flt=PF, icon=NWR("ishiwara_repairs_his_creation"), name="The East Asian League",
  desc="Ishiwara's East Asian League preaches equal partnership between Japan, Manchukuo and China against the Western powers. In Hsinking its members fill the General Affairs Board.",
  rew="add_political_power = 50\n" + dt("gab", 5) + DREAM(("political_power_factor", 0.10, "political_power_factor_tt")) + END)
f("MAN_pol_kenkoku_university", 18, 2, [["MAN_restoring_control_to_the_concord_society"]], flt="FOCUS_FILTER_RESEARCH", icon=CH("goal_MAN_education.dds"), name="Kenkoku University",
  desc="The Nation-Building University opens in Hsinking in 1938: Japanese, Chinese, Korean, Mongol and Russian students live and study together, and argue freely in their dormitories.",
  rew=fav("gab", 5) + DREAM(("research_speed_factor", 0.05, "research_speed_factor_tt")) + "add_tech_bonus = { name = MAN_pol_kenkoku_university bonus = 1.0 uses = 1 category = industry }\n" + END)
f("MAN_pol_joint_council", 16, 3, [["MAN_pol_east_asian_league"]], flt=PF, icon=NWR("implement_representative_functions_of_concordia_association"), name="The Concordia Joint Council",
  desc="The Association's national Joint Council becomes a standing assembly of the five races. It cannot legislate, but its voice is loud.",
  rew=flag("MAN_pf_councils", "MAN_tt_pf_councils", "Unlocks the §YConvene the Joint Council§! decision") + dt("gab", 10) + "add_stability = 0.05\n" + END)
f("MAN_pol_pacification_teams", 15, 4, [["MAN_pol_joint_council"]], flt="FOCUS_FILTER_STABILITY", icon=NWR("mobilization_goals_of_concordia_association"), name="Concordia Pacification Teams",
  desc="Instead of punitive columns, Concordia sends teams of doctors, teachers and propagandists into the guerrilla districts, with grain and amnesty papers.",
  rew=bg(-0.03) + drain(0.03) + fav("kw", -5) + END)
f("MAN_pol_withdraw_guidance", 17, 4, [["MAN_pol_joint_council"], ["MAN_pol_kenkoku_university"]], flt=PF, icon=NWR("abandon_internal_control"),
  av=avt("MAN_tt_av_withdraw", "§YGeneral Affairs Board§! favour is at least 60 and §YKwantung Army patience§! is at least 35",
         "check_variable = { MAN_fav_gab > 59.99 }\ncheck_variable = { MAN_kw_pat > 34.99 }\n"),
  name="End Internal Guidance",
  desc="The Kwantung Army's Fourth Section, which has 'guided' every ministry since 1932, is dissolved. The army returns to the frontier and the state governs itself. Fewer garrisons in the interior will be noticed in the hills.",
  rew=tc("kw", -0.03) + tc("gab", 0.05) + pdrift(-0.03) + bg(0.02) + "add_stability = 0.05\n" + DREAM(("production_speed_buildings_factor", 0.10, "production_speed_buildings_factor_tt")) + END)
f("MAN_pol_chinese_ministers", 16, 5, [["MAN_pol_withdraw_guidance"]], mx="MAN_pol_japanese_citizens", flt=PF, icon=OAK("MAN_chinese_leadership.dds"), name="Ministers Who Govern",
  desc="Zhang Jinghui and his Chinese ministers are given real portfolios, and the Japanese vice-ministers become advisers. The gentry and the county magistrates take notice.",
  rew="add_stability = 0.10\n" + bg(-0.03) + fav("gab", -5) + fav("ind", -5) + END)
f("MAN_pol_japanese_citizens", 18, 5, [["MAN_pol_withdraw_guidance"]], mx="MAN_pol_chinese_ministers", flt=PF, icon=NWR("transfer_powers_to_government_of_manchukuo"), name="Japanese Officials Become Manchukuoans",
  desc="Ishiwara's oldest demand: Japanese officials in Manchukuo must give up Japanese nationality and serve this state alone, at its salaries and under its laws.",
  rew=fav("gab", 10) + fav("smr", -10) + dt("gab", 5) + "add_stability = -0.03\n" + DREAM(("industrial_capacity_factory", 0.05, "industrial_capacity_factory_tt")) + END)
f("MAN_pol_railway_zone", 17, 6, [["MAN_pol_chinese_ministers", "MAN_pol_japanese_citizens"]], flt=PF, icon=NW("restructuring_of_mantetsu"), name="The Railway Zone Returns",
  desc="Mantetsu's railway zone, a Japanese colony running the length of the country, is handed to the Manchukuo state with its towns, schools and police.",
  rew=fav("smr", -10) + fav("gab", 10) + "716 = { add_extra_state_shared_building_slots = 1 }\n328 = { add_extra_state_shared_building_slots = 1 }\n" + END)
f("MAN_pol_republic_in_all_but_name", 17, 7, [["MAN_pol_railway_zone"]], cost=10, flt=PF, icon=NW("restore_idea_of_republic"),
  av=avt("MAN_tt_av_republic", "§YGeneral Affairs Board§! favour is at least 70", "check_variable = { MAN_fav_gab > 69.99 }\n"),
  name="A Union of Five Races",
  desc="Puyi reigns, the Joint Council deliberates and the General Affairs Board governs. Manchukuo is still Japan's ally, but it is no longer the Kwantung Army's property.",
  rew=dt("gab", 10) + relief(10) + pdrift(-0.02) + DREAM(("industrial_capacity_factory", 0.10, "industrial_capacity_factory_tt"), ("stability_weekly", 0.001, "stability_weekly_tt")) + END)

# ---- An Army with a State (historical)
f("MAN_an_army_with_a_state", 22, 1, mx="MAN_restoring_control_to_the_concord_society", flt=PF, ai=10, cost=5, icon=EX("GFX_MAN_an_army_with_a_state-905635"), name="An Army with a State",
  desc="The Kwantung Army does not have a state; Manchukuo is a state that has an army. Its commander is also Japan's ambassador, and his staff 'guide' every ministry in Hsinking.",
  rew="add_stability = -0.05\n" + fav("kw", 15) + fav("gab", -5) + pat(10) + flag("MAN_pf_guidance", "MAN_tt_pf_guidance", "Unlocks the §YIssue an Internal Guidance Directive§! decision") +
  DREAM(("industrial_capacity_factory", 0.05, "industrial_capacity_factory_tt")) + END)
f("MAN_pol_concordia_reorganised", 21, 2, [["MAN_an_army_with_a_state"]], flt=PF, icon=NWR("suppress_autonomy_of_concordia_association"), name="Reorganise the Concordia Association",
  desc="In 1936 the Association is purged of its idealists and made the army's instrument for mobilising the population: every official a member, every village a branch.",
  rew=inc(0.5) + pat(5) + fav("gab", -5) + "add_stability = 0.03\n" + END)
f("MAN_pol_tojo_kempeitai", 23, 2, [["MAN_an_army_with_a_state"]], flt="FOCUS_FILTER_STABILITY", icon=NWJ("Tojo_Shogunate"), name="Tojo's Kempeitai",
  desc="General Tojo Hideki commands the Kwantung Army's military police. His files cover communists, Chinese nationalists and Japanese officers alike.",
  rew=bg(-0.02) + fav("kw", 5) + fav("gab", -5) + "add_stability = -0.02\n" + END)
f("MAN_pol_gab_state", 20, 3, [["MAN_pol_concordia_reorganised"]], flt=PF, icon=OAK("MAN_japan_advisors.dds"), name="The General Affairs Board State",
  desc="Under Hoshino Naoki the General Affairs Board drafts every budget, every law and every appointment. The Chinese ministers sign what it sends them.",
  rew=fav("gab", 10) + dt("gab", 5) + tc("gab", 0.03) + END)
f("MAN_pol_extraterritoriality", 22, 3, [["MAN_pol_concordia_reorganised"], ["MAN_pol_tojo_kempeitai"]], flt=PF, icon=NW("cancellation_of_extraterritoriality"), name="Abolish Extraterritoriality",
  desc="In December 1937 Japan gives up its extraterritorial rights and Mantetsu's railway zone. Japanese residents now fall under Manchukuo law, which Japanese officials write.",
  rew=fav("smr", -15) + fav("gab", 10) + fav("kw", 5) + "add_stability = 0.05\n716 = { add_extra_state_shared_building_slots = 1 }\n" + END)
f("MAN_pol_pujie_marriage", 24, 3, [["MAN_pol_tojo_kempeitai"]], flt=PF, icon=NWR("problem_of_succession_to_throne"), name="Prince Pujie's Marriage",
  desc="The Kwantung Army arranges the marriage of Puyi's brother to Saga Hiro, a Japanese noblewoman, and a new succession law makes their son the heir. The dynasty will be half Japanese.",
  rew=pat(10) + fav("kw", 5) + "add_political_power = 50\n" + END)
f("MAN_pol_vice_ministers", 21, 4, [["MAN_pol_gab_state", "MAN_pol_extraterritoriality"]], mx="MAN_pol_zhang_jinghui", flt=PF, icon=NWJ("fix_the_mistakes_of_Manchukuo"), ai=3, name="Rule Through the Vice-Ministers",
  desc="Every ministry is run by its Japanese vice-minister, meeting each Tuesday at the General Affairs Board. The Chinese ministers are told the decisions afterwards.",
  rew=fav("gab", 15) + dt("gab", 5) + tc("gab", 0.03) + "add_stability = -0.05\n" + bg(0.01) + END)
f("MAN_pol_zhang_jinghui", 23, 4, [["MAN_pol_gab_state", "MAN_pol_extraterritoriality"]], mx="MAN_pol_vice_ministers", flt=PF, icon=NW("gain_trust_of_chinese"), name="Rule Through Zhang Jinghui",
  desc="Old Zhang Jinghui, Prime Minister and former bandit, knows every warlord family and county elder in the northeast. Give him face and he will keep the countryside quiet.",
  rew="add_stability = 0.05\n" + bg(-0.02) + fav("gab", -5) + pat(-5) + "add_political_power = 50\n" + END)
f("MAN_pol_foundation_shrine", 24, 5, [["MAN_pol_pujie_marriage"]], flt=PF, icon=WA("MAN_the_god_emperor"), name="The National Foundation Shrine",
  desc="In 1940 Puyi returns from Japan with a replica of the sacred mirror, and Amaterasu becomes the founding deity of Manchukuo. The Kwantung Army is delighted; the Emperor's Chinese subjects are not.",
  rew="add_ideas = MAN_god_emperor_pujie\n" + pat(10) + bg(0.02) + END)
f("MAN_pol_mobilisation_law", 22, 5, [["MAN_pol_vice_ministers", "MAN_pol_zhang_jinghui"]], flt=PF, icon=EX("GFX_MAN_enact_mobilisation-905645"), name="The National Mobilisation Law",
  desc="Manchukuo copies Japan's 1938 mobilisation law: the state may direct any worker, factory or harvest to wherever the war requires.",
  rew=lab(30) + inc(1) + fav("ind", 5) + "add_war_support = 0.05\n" + END)
f("MAN_pol_conscription_law", 21, 6, [["MAN_pol_mobilisation_law"]], flt="FOCUS_FILTER_MANPOWER", icon=NWJ("manchurian_modernizes_the_army"), name="The National Conscription Law",
  desc="From 1940 every young man of Manchukuo is liable for military service. Those the army rejects are sent to the labour service instead.",
  rew=lab(-10) + drain(0.05) + DREAM(("recruitable_population_factor", 0.02, "recruitable_population_factor_tt")) + END)
f("MAN_pol_neighbourhood", 23, 6, [["MAN_pol_mobilisation_law"]], flt="FOCUS_FILTER_STABILITY", icon=NW("social_hierarchy"), name="Collective Responsibility",
  desc="The old baojia system returns: households are grouped in tens and hundreds, each responsible for the others. If one shelters a partisan, all are punished.",
  rew=bg(-0.03) + "add_stability = -0.02\n" + fav("kw", 5) + END)
f("MAN_pol_kwantung_manchukuo", 22, 7, [["MAN_pol_conscription_law"], ["MAN_pol_neighbourhood"]], cost=10, flt=PF, icon=OAK("Kwantung_Army_3.dds"),
  av=avt("MAN_tt_av_kwm", "§YKwantung Army patience§! is at least 70", "check_variable = { MAN_kw_pat > 69.99 }\n"),
  name="The Kwantung Army's Manchukuo",
  desc="The Army's experiment is complete: a state run by staff officers and reform bureaucrats, with every factory, farm and village answering to the needs of the Kwantung Army.",
  rew=tc("kw", 0.03) + pdrift(0.05) + relief(10) + DREAM(("industrial_capacity_factory", 0.05, "industrial_capacity_factory_tt")) + END)

# =====================================================================================================
# PUBLIC SECURITY (under the society branch)
# =====================================================================================================
f("MAN_sec_security_plan", 33, 9, [["MAN_restoring_control_to_the_concord_society", "MAN_an_army_with_a_state"]], cost=5, icon=NWR("hoankyoku"), flt="FOCUS_FILTER_STABILITY", name="The Security Bureau",
  desc="The Three-Year Public Security Plan is already under way, but the army, the police and the Kempeitai each fight their own war. A Security Bureau in Hsinking is to coordinate all three and give the plan a single command.",
  rew=tt("MAN_tt_sec_plan", "Strengthens the running §OThree-Year Public Security Plan§! mission: bring average §Obanditry§! below §Y25§! by early 1939.") + gcap(1) + bg(-0.01) + drain(0.02) + pat(5) + END)
f("MAN_sec_collective_hamlets", 30, 10, [["MAN_sec_security_plan"]], icon=NWJ("resettlement_program_in_manchukuo"), flt="FOCUS_FILTER_STABILITY", name="Collective Hamlets",
  desc="Separate the fish from the water: move the scattered villages of the guerrilla zones into walled, guarded hamlets.",
  rew=tt("MAN_tt_unl_sec_hamlets", "Unlocks §OCollective Hamlets§! in the §OPublic Security§! panel") + END)
f("MAN_sec_kempeitai", 33, 10, [["MAN_sec_security_plan"]], icon=NWR("kempeitai_against_reform_officers"), flt="FOCUS_FILTER_STABILITY", name="The Kempeitai Field Network",
  desc="The military police extend their informers and interrogation centres into every county seat, and answer to nobody in the civil administration.",
  rew=tt("MAN_tt_unl_sec_informants", "Unlocks §OInformant Networks§! in the §OPublic Security§! panel") + gcap(1) + drain(0.03) + fav("kw", 10) + fav("gab", -5) + END)
f("MAN_sec_surrender", 36, 10, [["MAN_sec_security_plan"]], icon=NWR("political_amnesty"), flt="FOCUS_FILTER_STABILITY", name="The Surrender Programme",
  desc="Amnesty, cash and land for any partisan who comes in with his rifle, and death for anyone who shelters those who do not.",
  rew="unlock_decision_tooltip = MAN_sec_surrender_1\n" + drain(0.03) + END)
f("MAN_sec_blockhouses", 30, 11, [["MAN_sec_collective_hamlets"]], icon=WS + "1521695605/gfx/interface/goals/generic_anti_insurgency.png", flt="FOCUS_FILTER_STABILITY", name="Railway Blockhouse Lines",
  desc="Brick blockhouses every few kilometres along the lines, with searchlights, wire and telephone.",
  rew=tt("MAN_tt_unl_sec_blockhouses", "Unlocks §OBlockhouse Lines§! in the §OPublic Security§! panel") + gcap(1) + drain(0.02) + fav("smr", 5) + END)
f("MAN_sec_nozoe", 33, 11, [["MAN_sec_kempeitai"]], icon=WA("MAN_form_raiding_parties"), flt="FOCUS_FILTER_STABILITY", name="The Nozoe Punitive Campaign",
  desc="A special command under General Nozoe Shotoku is formed to hunt down Yang Jingyu's First Route Army in the Changbai forests.",
  bypass="\t\tbypass = { has_country_flag = MAN_band1_dead }\n",
  av=avt("MAN_tt_av_nozoe", "The §OFirst Route Army§! is down to strength §Y55§! or less, or it is mid-1939 (when the historical campaign began)",
         "OR = {\n\tcheck_variable = { MAN_band1 < 55.01 }\n\tdate > 1939.6.1\n}\n"),
  rew="set_country_flag = MAN_nozoe_active\n" + tt("MAN_tt_nozoe", "Starts §YThe Nozoe Punitive Campaign§!: the First Route Army loses strength every week for a year.") + END)
f("MAN_sec_border", 36, 11, [["MAN_sec_surrender"]], icon=NWJ("establish_the_Manchurian_Mongolian_border"), flt="FOCUS_FILTER_STABILITY", name="Seal the Amur",
  desc="Patrol boats, border posts and minefields along the Amur and Ussuri cut the partisans off from Soviet sanctuary and supplies.",
  rew="set_country_flag = MAN_border_sealed\n" + tt("MAN_tt_border", "The Second and Third Route Armies recover more slowly and can no longer escape into the Soviet Union.") + drain(0.03) + pat(5) + END)
f("MAN_sec_pacified", 33, 12, [["MAN_sec_blockhouses"], ["MAN_sec_nozoe"], ["MAN_sec_border"]], cost=10,
  av=avt("MAN_tt_av_pacified", "Average banditry is below 30", "check_variable = { MAN_bandit_avg < 30 }\n"), icon=OAK("MAN_Power_to_the_Kwantung_Army.png"), flt="FOCUS_FILTER_STABILITY", name="A Pacified Manchukuo",
  desc="The organised resistance is broken. Pacified provinces are safer places to build, and the Kwantung Army takes the credit.",
  rew="add_stability = 0.10\n" + pat(15) + fav("kw", 10) + dt("kw", 5) + gcap(2) + bg(-0.02) + relief(5) + BEH(("local_resources_factor", 0.10, "local_resources_factor_tt")) + END)


# =====================================================================================================
# FACTORIES FROM THE FOCUS TREE (decisions are separate). One table so the totals can be audited:
# civilian max 35 (19 on the spine), military max 30 (12 on the spine), steel refineries 1 to 8, high capacity grids 1 to 4.
# The planned-economy / Concordia path leans civilian and grids; the Army / munitions path leans military and steel.
# =====================================================================================================
IC, AF, SR, GRID = "industrial_complex", "arms_factory", "steel_refinery", "industrial_infrastructure"
FAC = {
    # spine
    "MAN_eco_first_plan": [(716, IC, 2)], "MAN_eco_zone_planning": [(715, IC, 1)],
    "MAN_eco_revised_plan": [(328, IC, 2), (716, GRID, 1)], "MAN_eco_fengman_dam": [(328, IC, 1)], "MAN_eco_supung_dam": [(716, IC, 1)],
    "MAN_eco_control_law": [(716, IC, 1)], "MAN_eco_first_plan_fulfilled": [(328, IC, 2)], "MAN_eco_second_plan": [(715, AF, 2)],
    "MAN_eco_heavy_machinery": [(714, IC, 2)], "MAN_eco_behemoth": [(716, IC, 2), (328, AF, 2)],
    "MAN_eco_soybean": [(714, IC, 1)], "MAN_eco_light_metals": [(716, IC, 1)], "MAN_eco_resource_board": [(714, IC, 1)],
    "MAN_eco_continental_supply": [(715, IC, 1)], "MAN_eco_showa_steel": [(716, SR, 1)],
    "MAN_eco_mukden_arsenal": [(716, AF, 2)], "MAN_eco_manshu_hikoki": [(716, AF, 2)], "MAN_eco_powder_company": [(328, AF, 1)],
    "MAN_eco_arsenal_of_empire": [(716, AF, 2)],
    # Mangyo (capital, civilian) or Mantetsu (rails, mixed)
    "MAN_eco_found_mangyo": [(328, SR, 1)], "MAN_eco_nissan_moves": [(716, IC, 2)], "MAN_eco_american_capital": [(328, IC, 2)], "MAN_eco_dowa": [(716, AF, 1)],
    "MAN_eco_smr_industrial": [(716, IC, 1), (716, AF, 1)], "MAN_eco_asia_express": [(715, IC, 2)],
    # whose plan, whose labour, whose guns, which war
    "MAN_eco_prio_army": [(715, AF, 3), (716, SR, 1)], "MAN_eco_prio_balanced": [(328, IC, 2), (715, IC, 1), (328, GRID, 1)],
    "MAN_eco_labour_service": [(715, AF, 1), (715, SR, 1)], "MAN_eco_contract_labour": [(715, IC, 1)],
    "MAN_eco_kw_arms": [(717, AF, 3), (717, SR, 1)], "MAN_eco_own_arms": [(716, AF, 2)],
    "MAN_eco_total_war_plan": [(715, AF, 4), (715, SR, 1)], "MAN_eco_preserve_base": [(717, IC, 3), (717, GRID, 1)],
    "MAN_eco_agri_modern": [(714, IC, 2)],
    # politics: Concordia builds for the civilian economy, the Army state for the war
    "MAN_pol_chinese_ministers": [(328, IC, 1)], "MAN_pol_republic_in_all_but_name": [(328, IC, 2), (715, GRID, 1)],
    "MAN_pol_vice_ministers": [(714, AF, 2), (714, SR, 1)], "MAN_pol_kwantung_manchukuo": [(717, AF, 3), (717, SR, 1)],
}
for d in F:
    if d["id"] in FAC:
        d["rew"] = "".join(build(s, ty, n) for s, ty, n in FAC.pop(d["id"])) + d["rew"]
assert not FAC, FAC

# =====================================================================================================
# minigame hooks on the military and society branches (prepended to their existing rewards)
# =====================================================================================================
TIE = {
    # military: the army tree stays free of minigame hooks (only its share of the factory budget)
    "MAN_manchurian_tank_corps": build(716, "arms_factory", 1),
    # society
    "MAN_kwantung_demands_economic_planning": fav("kw", 5) + fav("ind", 5),
    "MAN_implement_a_japanese_tax_system": fav("gab", 5),
    "MAN_delegate_authority_to_manestsu_research_branch": fav("smr", 10) + fav("gab", -5),
    "MAN_delegate_authority_to_the_manchuko_government": fav("gab", 10) + fav("smr", -5),
    "MAN_establish_the_manchuko_film_association": bg(-0.01) + pat(5),
    "MAN_force_the_japanese_language": fav("kw", 5) + bg(0.02),
    "MAN_keep_chinese_language": fav("kw", -5) + bg(-0.01),
    "MAN_joint_manchukorean_leadership": drain(0.05),
    "MAN_reform_mongolian_territory": sbandit([761, 612, 1043], -5, "MAN_tt_mongol_lands", "Banditry in Hulunbuir, Xilingol and Pailingmiao: §G-5§!"),
}

# ------------------------------------------------------------------ write the tree
OLD_ECO = ["MAN_first_five_year_plan", "MAN_formmanestsusindustrialsector", "MAN_create_the_main_railway_administration", "MAN_the_matsuoka_plan",
           "MAN_the_aikawa_plan", "MAN_one_company_one_industry", "MAN_create_new_worker_ethos", "MAN_manestu_reborn", "MAN_expansionofmanestucontrol",
           "MAN_replacemanestsuscontrol", "MAN_remove_extraterritorially_privledges", "MAN_foundmangyo", "MAN_manetsu_research_department",
           "MAN_purchase_german_liscenses", "MAN_learn_from_american_steelmakers", "MAN_manchurian_aircrafts_company", "MAN_second_five_year_plan",
           "MAN_breakthrough_in_steel_rolling", "MAN_modernised_agriculture", "MAN_restructure_the_liaohe_river_flow", "MAN_foster_a_light_metal_society"]
OLD_POL = ["MAN_restoring_control_to_the_concord_society", "MAN_dreams_of_a_republican_state", "MAN_begin_selfgovernance", "MAN_restoring_the_harmony_society",
           "MAN_legitimise_representative_functions", "MAN_return_japanese_possesions", "MAN_return_japanese_civilians_to_politics", "MAN_progressive_bureaucrats_in_power",
           "MAN_release_intellectual_leftist", "MAN_restore_the_status_of_the_party", "MAN_manchuria_greening_program", "MAN_support_land_reform",
           "MAN_thejapaneseareatthetopchinesesecond", "MAN_an_army_with_a_state", "MAN_finish_off_the_concord_society", "MAN_establish_religious_laws",
           "MAN_punish_thoughtcrimes", "MAN_idealogical_use_for_the_kwantung", "MAN_shut_down_land_reforms", "MAN_enact_mobilisation",
           "MAN_transform_the_civilian_sector", "MAN_pass_forced_labours", "MAN_purge_the_left", "MAN_openthelab"]

# Racial Harmony shifts (negative = Concord of Five Races, positive = Japanese Guidance)
BOPS = {
    "MAN_restoring_control_to_the_concord_society": -0.15, "MAN_pol_east_asian_league": -0.05, "MAN_pol_kenkoku_university": -0.05,
    "MAN_pol_joint_council": -0.05, "MAN_pol_pacification_teams": -0.05, "MAN_pol_withdraw_guidance": -0.10, "MAN_pol_chinese_ministers": -0.10,
    "MAN_pol_japanese_citizens": -0.05, "MAN_pol_republic_in_all_but_name": -0.15,
    "MAN_an_army_with_a_state": 0.10, "MAN_pol_concordia_reorganised": 0.05, "MAN_pol_tojo_kempeitai": 0.05, "MAN_pol_gab_state": 0.05,
    "MAN_pol_pujie_marriage": 0.05, "MAN_pol_vice_ministers": 0.10, "MAN_pol_zhang_jinghui": -0.05, "MAN_pol_foundation_shrine": 0.10,
    "MAN_pol_neighbourhood": 0.05, "MAN_pol_kwantung_manchukuo": 0.10,
    "MAN_eco_million_households": 0.05, "MAN_eco_korean_settlers": -0.03, "MAN_eco_labour_service": 0.03, "MAN_eco_contract_labour": -0.03,
    "MAN_eco_grain_quotas": 0.03, "MAN_eco_agri_modern": -0.03, "MAN_eco_prio_army": 0.03, "MAN_sec_kempeitai": 0.03, "MAN_sec_surrender": -0.02,
    # society branch
    "MAN_keep_chinese_language": -0.05, "MAN_introduce_manchurian_language": -0.03, "MAN_force_the_japanese_language": 0.08,
    "MAN_promote_chinese_multicultralism": -0.05, "MAN_promote_manchurian_identity": -0.05, "MAN_call_for_mixed_marriages": -0.03,
    "MAN_joint_manchukorean_leadership": -0.03, "MAN_reform_mongolian_territory": -0.03, "MAN_recognise_russian_influx": -0.02,
    "MAN_delegate_authority_to_the_manchuko_government": -0.03, "MAN_implement_a_japanese_tax_system": 0.03,
}
def bop(x): return f"add_power_balance_value = {{ id = MAN_racial_harmony value = {x} }}\n"

# custom focus filters: which minigame a focus touches (in its reward or its requirements)
FILTERS = [
    ("FOCUS_FILTER_MAN_PLAN", "Industrial Development Plan", "gfx/interface/focusview/filter/debt_to_the_ifc_icon.dds",
     r"MAN_q_|MAN_qt_|MAN_quota_focus|MAN_qb_|MAN_labour|MAN_zone|MAN_proj_slots|unlock_decision_tooltip = MAN_(mega|lab)|MAN_plan_|MAN_review_relief|MAN_lines_unl|MAN_shale_known|MAN_first_fyp"),
    ("FOCUS_FILTER_MAN_BUREAUCRACY", "Hsinking Bureaucracy", "gfx/interface/focusview/filter/internal_affairs_icon.dds",
     r"MAN_fav_|MAN_kw_pat|MAN_dt_|MAN_tc_|MAN_pat_drift|MAN_pf_|MAN_kishi_arrives|MAN_ayukawa_arrives"),
    ("FOCUS_FILTER_MAN_SECURITY", "Public Security", "gfx/interface/focusview/filter/pol_violence.dds",
     r"MAN_bandit|MAN_bgrow_g|MAN_band_drain|MAN_band\d|unlock_decision_tooltip = MAN_sec|MAN_tt_unl_sec|MAN_grievance|MAN_nozoe|MAN_border_sealed|MAN_sec_plan"),
    ("FOCUS_FILTER_BALANCE_OF_POWER", None, None, r"power_balance"),
]
def add_filters(block):
    body = block.split("search_filters", 1)
    found = [fid for fid, _, _, pat in FILTERS if re.search(pat, re.sub(r"MAN_(plan_recalc|pol_compute|ui_refresh|sec_refresh)", "", block))]
    if not found: return block
    m = re.search(r"search_filters = \{([^}]*)\}", block)
    if not m: return block.replace("\t\tcompletion_reward = {", "\t\tsearch_filters = { " + " ".join(found) + " }\n\t\tcompletion_reward = {", 1)
    have_ = m.group(1).split()
    new = have_ + [f_ for f_ in found if f_ not in have_]
    return block[:m.start()] + "search_filters = { " + " ".join(new) + " }" + block[m.end():]

# layout: same-row focuses must sit at least 2 columns apart or their labels overlap
SHIFT_RIGHT = 3    # politics, society and security move right of the widened economy tree
SEC_GAP = 7       # columns opened between the two political halves (and before society) for the Public Security branch
REPOS = {
    # fuel and metals one column right
    "MAN_eco_fushun_shale": (9, 3), "MAN_eco_hydrogenation": (8, 4), "MAN_eco_synthetic_fuel": (10, 4), "MAN_eco_light_metals": (9, 5),
    "MAN_eco_oil_surveys": (8, 6), "MAN_eco_strategic_stockpiles": (10, 6), "MAN_eco_aluminium_air": (10, 7),
    # land and settlement two columns right
    "MAN_eco_soybean": (14, 3), "MAN_eco_million_households": (13, 4), "MAN_eco_korean_settlers": (15, 4), "MAN_eco_youth_corps": (13, 5),
    "MAN_eco_grain_quotas": (13, 6), "MAN_eco_agri_modern": (15, 6), "MAN_eco_resource_board": (13, 7), "MAN_eco_continental_supply": (12, 8),
    # centre: clear the Mantetsu line
    "MAN_eco_material_mobilisation": (5, 7), "MAN_eco_fengman_dam": (7, 7), "MAN_eco_supung_dam": (8, 8),
    "MAN_eco_labour_service": (4, 8), "MAN_eco_contract_labour": (6, 8), "MAN_eco_first_plan_fulfilled": (5, 9),
    # Public Security is the middle column of the political tree, between Ishiwara's Concordia and An Army with a State
    "MAN_sec_security_plan": (26, 2), "MAN_sec_collective_hamlets": (24, 3), "MAN_sec_kempeitai": (26, 3), "MAN_sec_surrender": (28, 3),
    "MAN_sec_blockhouses": (24, 4), "MAN_sec_nozoe": (26, 4), "MAN_sec_border": (28, 4), "MAN_sec_pacified": (26, 5),
}
def check_layout(text):
    P_ = [(int(x), int(y), i) for i, x, y in re.findall(r"\tfocus = \{\n\t\tid = (\w+)\n.*?\n\t\tx = (-?\d+)\n\t\ty = (\d+)", text, re.S)]
    bad = []
    for a in range(len(P_)):
        for b_ in range(a + 1, len(P_)):
            if P_[a][1] == P_[b_][1] and abs(P_[a][0] - P_[b_][0]) < 2: bad.append((P_[a][2], P_[b_][2], P_[a][1]))
    return bad

BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "man_backup/common/national_focus/manchukuo.txt")
def build_tree():
    t, tb = rd("common/national_focus/manchukuo.txt")
    if "MAN_eco_miyazaki_blueprint" in t:
        t = open(BACKUP, "rb").read().decode("utf-8-sig").replace(chr(13)+chr(10), chr(10))
    t = re.sub(r"continuous_focus_position = \{[^}]*\}", "continuous_focus_position = { x = 2800 y = 1700 }", t, count=1)
    hit = set(); bhit = set()
    def fix(m):
        i, b = m.group(1), m.group(0)
        if i in OLD_ECO or i in OLD_POL: return ""
        y = int(re.search(r"\n\t\ty = (\d+)", b).group(1))
        if y >= 9:   # military branch moves right of the new economy tree
            b = re.sub(r"\n\t\tx = (\d+)", lambda mm: f"\n\t\tx = {int(mm.group(1)) + 12}", b, count=1)
        else:        # society branch moves right of the wider economy and political trees
            b = re.sub(r"\n\t\tx = (\d+)", lambda mm: f"\n\t\tx = {int(mm.group(1)) + SHIFT_RIGHT + SEC_GAP}", b, count=1)
        if i in TIE or i in BOPS:
            assert "\t\tcompletion_reward = {\n" in b, i
            b = b.replace("\t\tcompletion_reward = {\n", "\t\tcompletion_reward = {\n" + ind((bop(BOPS[i]) if i in BOPS else "") + TIE.get(i, "") + (END if (i in BOPS or "MAN_" in TIE.get(i, "")) else ""), 3), 1)
            if i in TIE: hit.add(i)
            if i in BOPS: bhit.add(i)
        if i == "MAN_manchuko_national_musuem":
            b = re.sub(r"add_extra_state_shared_building_slots = 2(\s+add_building_construction = \{\s+type = industrial_complex\s+level = )2", r"add_extra_state_shared_building_slots = 1\g<1>1", b)
        return add_filters(b)
    n0 = len(re.findall(r"\tfocus = \{\n\t\tid = ", t))
    t = re.sub(r"\tfocus = \{\n\t\tid = (\w+)\n.*?\n\t\}\n", fix, t, flags=re.S)
    assert len(re.findall(r"\tfocus = \{\n\t\tid = ", t)) == n0 - len(OLD_ECO) - len(OLD_POL)
    assert hit == set(TIE), set(TIE) - hit
    t = t.rstrip()
    assert t.endswith("}")
    out = t[:-1].rstrip() + "\n\n\t######## ECONOMY / POLITICS / PUBLIC SECURITY ########\n"
    pos = {}
    for d in F:
        if d["id"] in REPOS: d["x"], d["y"] = REPOS[d["id"]]
        elif d["id"].startswith(("MAN_pol_", "MAN_sec_")) or d["id"] in ("MAN_an_army_with_a_state", "MAN_restoring_control_to_the_concord_society"):
            d["x"] += SHIFT_RIGHT
            if d["x"] >= 23: d["x"] += SEC_GAP   # the Army-with-a-State half moves right to open the middle for Public Security
        assert (d["x"], d["y"]) not in pos, (d["id"], pos.get((d["x"], d["y"])))
        pos[(d["x"], d["y"])] = d["id"]
        icon = d["icon"][1:] if d["icon"].startswith("=") else f"GFX_focus_{d['id']}"
        s = f"\tfocus = {{\n\t\tid = {d['id']}\n\t\ticon = {icon}\n\t\tx = {d['x']}\n\t\ty = {d['y']}\n\t\tcost = {d['cost']}\n"
        for g in d["pre"]: s += "\t\tprerequisite = { " + " ".join(f"focus = {p}" for p in g) + " }\n"
        if d["mx"]: s += "\t\tmutually_exclusive = { " + " ".join(f"focus = {p}" for p in d["mx"]) + " }\n"
        s += d["av"] + d["bypass"] + f"\t\tsearch_filters = {{ {d['flt']} }}\n\t\tai_will_do = {{ factor = {d['ai']} }}\n"
        s += "\t\tcompletion_reward = {\n" + ind((bop(BOPS[d["id"]]) if d["id"] in BOPS else "") + d["rew"], 3) + "\t\t}\n\t}\n"
        if d["id"] in BOPS: bhit.add(d["id"])
        out += add_filters(s)
        loc(d["id"], d["name"]); loc(d["id"] + "_desc", d["desc"])
    out += "}\n"
    # no focus longer than 35 days (cost 5 = 5 weeks)
    out = re.sub(r"(\n\t\tcost = )(\d+(?:\.\d+)?)", lambda m: m.group(1) + (m.group(2) if float(m.group(2)) <= 5 else "5"), out)
    assert bhit == set(BOPS), set(BOPS) - bhit
    for a_, b_, y_ in check_layout(out): print(f"  LAYOUT: {a_} and {b_} overlap on row {y_}")
    wr("common/national_focus/manchukuo.txt", out, tb)

def build_icons():
    G = "spriteTypes = {\n"
    for d in F:
        if d["icon"].startswith("="): continue
        src = d["icon"]; ext = os.path.splitext(src)[1]
        tex = f"gfx/interface/goals/man/GFX_focus_{d['id']}{ext}"
        os.makedirs(os.path.dirname(P(tex)), exist_ok=True)
        if os.path.exists(src): shutil.copyfile(src, P(tex))
        elif not os.path.exists(P(tex)): raise FileNotFoundError(f"focus icon for {d['id']}: {src} is gone and the mod has no copy")
        n = f"GFX_focus_{d['id']}"
        G += f"\t##Icon For: {d['id']}\n\tSpriteType = {{\n\t\tname = \"{n}\"\n\t\ttexturefile = \"{tex}\"\n\t}}\n"
        G += f"\tSpriteType = {{\n\t\tname = \"{n}_shine\"\n\t\ttexturefile = \"{tex}\"\n\t\teffectFile = \"gfx/FX/buttonstate.lua\"\n"
        for r in ("-90.0", "90.0"):
            G += (f"\t\tanimation = {{\n\t\t\tanimationmaskfile = \"{tex}\"\n\t\t\tanimationtexturefile = \"gfx/interface/goals/shine_overlay.dds\"\n\t\t\tanimationrotation = {r}\n"
                  "\t\t\tanimationlooping = no\n\t\t\tanimationtime = 0.75\n\t\t\tanimationdelay = 0\n\t\t\tanimationblendmode = \"add\"\n\t\t\tanimationtype = \"scrolling\"\n"
                  "\t\t\tanimationrotationoffset = { x = 0.0 y = 0.0 }\n\t\t\tanimationtexturescale = { x = 1.0 y = 1.0 }\n\t\t}\n")
        G += "\t\tlegacy_lazy_load = no\n\t}\n"
    for fid, nm, tex, _ in FILTERS:
        if not tex: continue
        G += f"\t##Focus filter: {nm}\n\tspriteType = {{\n\t\tname = \"GFX_{fid}\"\n\t\ttexturefile = \"{tex}\"\n\t}}\n"
        loc(fid, nm)
    wr("interface/MAN_eco_focus_icons.gfx", G + "}\n")

def build():
    build_tree(); build_icons()
    for k, v in TT.items(): loc(k, v)
    return L
