"""Run the whole Manchukuo systems + economy tree build, write loc, validate."""
import sys, os, re, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from man_common import *
import man_systems as MS
L1 = MS.build()
import man_systems2 as MS2          # writes on import
import man_focus as MF
L3 = MF.build()
import man_bop as MB
LB = MB.build(ind)
import man_advisors as MA
LA, ADV_ADDED = MA.build()
entries = L1 + MS2.L + L3 + LA
# ---- readable requirement tooltips instead of raw variable checks
TRIG = [
    ("FROM = { NOT = { has_state_flag = MAN_busy } }", "MAN_trg_not_busy", "No other §Yproject§! is under way in this province"),
    ("check_variable = { MAN_proj_active < MAN_proj_slots }", "MAN_trg_slot", "A free £civ_factory §Yproject slot§! (§Y[?MAN_proj_active|0]§! of §Y[?MAN_proj_slots|0]§! in use)"),
    ("check_variable = { MAN_zones_used < MAN_zone_cap }", "MAN_trg_zone", "£state §YZone allowance§! left (§Y[?MAN_zones_used|0]§! of §Y[?MAN_zone_cap|0]§! used)"),
    ("NOT = { has_country_flag = MAN_surveying }", "MAN_trg_survey", "No §Ysurvey party§! is already in the field"),
    ("NOT = { has_country_flag = MAN_review_lock }", "MAN_trg_review_lock", "The first months of the plan year have passed"),
    ("check_variable = { MAN_plan_pct > MAN_review_need_m }", "MAN_trg_review", "£industry_texticon §YTotal plan fulfilment§! above §Y[?MAN_review_need|0]%§! (now §Y[?MAN_plan_pct|0]%§!)"),
    ("check_variable = { MAN_bandit_avg < MAN_req_kw_t }", "MAN_trg_req_kw", "Average £pol_violence §Obanditry§! below §Y[?MAN_req_kw_t|0]§! (now §Y[?MAN_bandit_avg|0]§!)"),
    ("check_variable = { MAN_pct_steel > MAN_req_ind_t }", "MAN_trg_req_ind_a", "£resources_strip|5 §YIron and Steel§! fulfilment above §Y[?MAN_req_ind_t|0]%§! (now §Y[?MAN_pct_steel|0]%§!)"),
    ("check_variable = { MAN_zones_used > MAN_req_ind_m }", "MAN_trg_req_ind_b", "At least §Y[?MAN_req_ind_t|0]§! designated zones (now §Y[?MAN_zones_used|0]§!)"),
    ("check_variable = { MAN_pct_mach > MAN_req_mgy_t }", "MAN_trg_req_mgy_a", "£mil_factory §YMachinery and Munitions§! fulfilment above §Y[?MAN_req_mgy_t|0]%§! (now §Y[?MAN_pct_mach|0]%§!)"),
    ("check_variable = { MAN_proj_done > MAN_req_mgy_m }", "MAN_trg_req_mgy_b", "At least §Y[?MAN_req_mgy_t|0]§! plan projects completed (now §Y[?MAN_proj_done|0]§!)"),
    ("check_variable = { MAN_rail_built > MAN_req_smr_m }", "MAN_trg_req_smr_a", "At least §Y[?MAN_req_smr_t|0]§! railway lines or mine spurs (now §Y[?MAN_rail_built|0]§!)"),
    ("check_variable = { MAN_pct_coal > MAN_req_smr_t }", "MAN_trg_req_smr_b", "£resources_strip|7 §YCoal and Liquid Fuel§! fulfilment above §Y[?MAN_req_smr_t|0]%§! (now §Y[?MAN_pct_coal|0]%§!)"),
    ("check_variable = { MAN_bandit_avg < 25 }", "MAN_trg_bandit25", "Average £pol_violence §Obanditry§! below §Y25§! (now §Y[?MAN_bandit_avg|0]§!)"),
    ("check_variable = { MAN_band1 < 0.01 }", "MAN_trg_band1", "The £nato_unit_irregular_infantry_icon_small §OFirst Route Army§! is destroyed"),
]
for p in ("common/decisions/MAN_decisions.txt", "common/decisions/MAN_racial_harmony_bop_decisions.txt"):
    t_, bom_ = rd(p)
    for raw, key, txt in TRIG:
        t_ = t_.replace(raw, f"custom_trigger_tooltip = {{ tooltip = {key} {raw} }}")
    wr(p, t_, bom_)
entries += [(key, txt) for _, key, txt in TRIG]
have = {k for k, _ in entries}

GEN = ["common/decisions/MAN_decisions.txt", "common/decisions/categories/MAN_decision_categories.txt", "common/scripted_effects/MAN_systems_effects.txt",
       "common/dynamic_modifiers/MAN_dynamic_modifiers.txt", "events/MAN_systems_events.txt", "common/national_focus/manchukuo.txt",
       "common/scripted_guis/MAN_systems_guis.txt", "interface/MAN_systems.gui", "common/scripted_localisation/MAN_systems_loc.txt",
       "events/MAN_flavor_events.txt", "common/on_actions/16_man_flavor_on_actions.txt", "interface/MAN_eco_focus_icons.gfx", "interface/MAN_systems.gfx",
       "common/decisions/MAN_racial_harmony_bop_decisions.txt", "common/bop/MAN.txt",
       "common/characters/MAN.txt", "common/country_leader/MAN_imported_traits.txt"]
alltext = "".join(rd(p)[0] for p in GEN)
# auto tooltips
INST = {k: v[0] for k, v in MS.BK.items()}
for key in sorted(set(re.findall(r"custom_effect_tooltip = (MAN_tt_\w+)", alltext))):
    if key in have: continue
    m = re.fullmatch(r"MAN_tt_pat_(m?)(\d+)", key)
    if m: entries.append((key, f"Kwantung Army patience: {'§R-' if m.group(1) else '§G+'}{m.group(2)}§!")); have.add(key); continue
    m = re.fullmatch(r"MAN_tt_fav_(kw|gab|ind|mgy|smr)_(m?)(\d+)", key)
    if m: entries.append((key, f"§Y{INST[m.group(1)]}§! favour: {'§R-' if m.group(2) else '§G+'}{m.group(3)}§!")); have.add(key); continue
    m = re.fullmatch(r"MAN_tt_levy_(m?)(\d+)", key)
    if m: entries.append((key, f"£manpower_texticon §YLabour levy pressure§!: {'§G-' if m.group(1) else '§R+'}{m.group(2)}§! (each point costs §R0.015%§! stability a week, fading by §Y6%§! a week)")); have.add(key); continue
    m = re.fullmatch(r"MAN_tt_labour_(\d+)", key)
    if m: entries.append((key, f"Labour pool: §G+{m.group(1)}k§! workers")); have.add(key); continue
    m = re.fullmatch(r"MAN_tt_q_(\w+?)_(\d+)_flat", key)
    if m: entries.append((key, f"§Y{dict(QUOTAS)[m.group(1)]}§! quota: §G+{m.group(2)}§!")); have.add(key); continue
# dedupe keeping first
seen = set(); out = []
for k, v in entries:
    if k in seen: continue
    seen.add(k); out.append((k, v))
# ---- colour-code tooltip labels (yellow subject, green/red values)
LABELS = ["Kwantung Army patience", "Labour pool", "Labour income", "Planning efficiency", "Development zone allowance",
          "Concurrent plan projects", "Annual Review requirement", "All quota targets", "Machinery and Munitions target", "Iron and Steel target"]
PLACES = "|".join(sorted(SNAME.values(), key=len, reverse=True))
def colourise(k, v):
    if not k.startswith("MAN_tt_"): return v
    for lb in LABELS:
        v = re.sub(rf"(?<!§Y)\b{lb}\b(?=[: ])", f"§Y{lb}§!", v)
    v = v.replace("Banditry growth in every province:", "§YBanditry growth§! in every province:")
    v = v.replace("Strength of every Route Army:", "Strength of every §YRoute Army§!:")
    v = re.sub(r"Level that (§Y[^§]+§!) favour drifts back to:", r"§YResting level§! of \1 favour:", v)
    v = re.sub(r"(?<![§\w])(weekly banditry growth|banditry growth|Average banditry|Banditry|banditry)(?![^§]*§!)", r"§Y\1§!", v)
    v = re.sub(rf"(?<!§Y)\b({PLACES})\b(?![^§]*§!)", r"§Y\1§!", v)
    v = re.sub(r"(?<!§Y)\b(infrastructure|grievance|Route Army|Route Armies|Settlement and Grain Zone|Heavy Industry Zone|Mining District|Power and Water District|Kwantung Army Staff|Punitive Sweeps)\b(?![^§]*§!)", r"§Y\1§!", v)
    v = re.sub(r"(§[GR][+\-][\d.]+)§!k", r"\1k§!", v)          # keep the k inside the colour
    v = re.sub(r"§Y§Y([^§]+)§!§!", r"§Y\1§!", v)
    return v
# category colours: §Y economy/plan (default), §L politics, §O public security, §C places
POL_T = list(INST.values()) + ["Kwantung Army patience", "Hsinking Bureaucracy", "Resting level", "The Mantetsu Question", "Mantetsu Question",
         "Convene the Joint Council", "Issue an Internal Guidance Directive", "Kwantung Army", "Tokyo"]
SEC_T = ["Banditry growth", "weekly banditry growth", "Average banditry", "Banditry", "banditry", "Route Army", "Route Armies",
         "First Route Army", "Second Route Army", "Third Route Army", "grievance", "Punitive Sweeps", "Punitive Sweep",
         "Three-Year Public Security Plan", "The Three-Year Public Security Plan", "The Nozoe Punitive Campaign", "Public Security"]
def recolour(v):
    for terms, c in ((POL_T, "L"), (SEC_T, "O"), (list(SNAME.values()), "C")):
        for t_ in sorted(terms, key=len, reverse=True):
            v = v.replace(f"§Y{t_}§!", f"§{c}{t_}§!")
    v = re.sub(r"§R(grievance)§!", r"§O\1§!", v)
    return v
# vanilla text icons in front of the coloured subject
ICONS = [
    (r"§YLabour (pool|income)§!", "£manpower_texticon "), (r"§YPlanning efficiency§!", "£prod_eff "), (r"§YDevelopment zone allowance§!", "£state "),
    (r"§YConcurrent plan projects§!", "£civ_factory "), (r"§YAnnual Review requirement§!", "£decision_icon_small "),
    (r"§YIron and Steel( target)?§!", "£resources_strip|5 "), (r"§YCoal and Liquid Fuel§!", "£resources_strip|7 "),
    (r"§YElectric Power§!", "£energy_texticon "), (r"§YMachinery and Munitions( target)?§!", "£mil_factory "),
    (r"§YAll quota targets§!", "£industry_texticon "), (r"§YEconomic Capacity Surplus§!", "£civ_factory_output "),
    (r"§LKwantung Army patience§!", "£army_experience "),
    (r"§L(Kwantung Army Staff|General Affairs Board|Ministry of Industry|Mangyo|Mantetsu)§! favour", "£influence_texticon "),
    (r"§LHsinking Bureaucracy§!", "£pol_idea "),
    (r"§O(Banditry growth|Banditry|Average banditry|weekly banditry growth)§!", "£pol_violence "),
    (r"§O(Route Army|Route Armies)§!", "£nato_unit_irregular_infantry_icon_small "), (r"§Yinfrastructure§!", "£infrastructure_texticon "),
]
def iconise(k, v):
    if not k.startswith("MAN_tt_") or "£" in v: return v
    for pat, ic in ICONS:
        v = re.sub(rf"({pat})", lambda m: ic + m.group(1), v, count=1)
    return v
out = [(k, iconise(k, recolour(colourise(k, v)))) for k, v in out]
import man_ui_text as UT
out = UT.apply(out)
outb = [(k, iconise(k, recolour(colourise(k, v)))) for k, v in LB]
# ---- colour the decision titles themselves by category (Y plan, C railway lines, L politics / balance of power, O security)
DEC_IDS = set()
for p in ("common/decisions/MAN_decisions.txt", "common/decisions/MAN_racial_harmony_bop_decisions.txt"):
    DEC_IDS |= set(re.findall(r"^\t(MAN_\w+) = \{", rd(p)[0], re.M))
DEC_IDS -= set(re.findall(r"\bid = (MAN_\w+)", rd("common/national_focus/manchukuo.txt")[0]))   # a few decisions share their loc key with a focus
def dec_colour(k):
    if k.startswith("MAN_mega_"): return "1"    # megaprojects: their own violet (gradient colour 1)
    if k.startswith("MAN_line_"): return "C"
    if k.startswith(("MAN_pol_", "MAN_bop_", "MAN_court_", "MAN_req_")): return "L"
    if k.startswith("MAN_sec_"): return "O"
    return "Y"
def colour_title(k, v):
    if k not in DEC_IDS or "§" in v: return v
    return f"§{dec_colour(k)}{v}§!"
out = [(k, colour_title(k, v)) for k, v in out]
outb = [(k, colour_title(k, v)) for k, v in outb]
wr_loc("localisation/english/MAN_racial_harmony_bop_l_english.yml", outb)
wr_loc("localisation/english/MAN_systems_l_english.yml", out)
# ---- guard dynamic modifier removals (the game logs an error when removing one that is not applied)
for p in ("common/decisions/MAN_decisions.txt", "common/scripted_effects/MAN_systems_effects.txt", "events/MAN_systems_events.txt"):
    t_, bom_ = rd(p)
    t2 = re.sub(r"(?<!\} )remove_dynamic_modifier = \{ modifier = (\w+) \}",
                r"if = { limit = { has_dynamic_modifier = { modifier = \1 } } remove_dynamic_modifier = { modifier = \1 } }", t_)
    if t2 != t_: wr(p, t2, bom_)

# ---------------------------------------------------------------- validation
problems = []
allloc = set()
for f in glob.glob(P("localisation/**/*.yml"), recursive=True):
    for l in open(f, encoding="utf-8-sig", errors="ignore"):
        m = re.match(r"\s*([\w.\-]+):\d*\s*\"", l)
        if m: allloc.add(m.group(1))
V = r"C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV/"
for f in glob.glob(V + "localisation/english/*.yml"):
    for l in open(f, encoding="utf-8-sig", errors="ignore"):
        m = re.match(r"\s*([\w.\-]+):\d*\s*\"", l)
        if m: allloc.add(m.group(1))
for key in set(re.findall(r"(?:custom_effect_tooltip|localization_key|custom_cost_text|tooltip) = (MAN_\w+)", alltext)):
    if key not in allloc: problems.append(f"missing loc {key}")
for p in GEN:
    t = rd(p)[0]
    if t.count("{") != t.count("}"): problems.append(f"braces {p}")
    if "\r" in t: problems.append(f"CR {p}")
# decisions loc
dec = rd("common/decisions/MAN_decisions.txt")[0]
for d in re.findall(r"^\t(MAN_\w+) = \{", dec, re.M):
    if d not in allloc: problems.append(f"missing decision loc {d}")
    if d + "_desc" not in allloc: problems.append(f"missing decision desc {d}")
# effects referenced exist
eff = rd("common/scripted_effects/MAN_systems_effects.txt")[0] + rd("common/scripted_effects/MAN_behemoth_scripted_effects.txt")[0]
defined = set(re.findall(r"^(MAN_\w+) = \{", eff, re.M))
for e in set(re.findall(r"\b(MAN_\w+) = yes", alltext)):
    if e not in defined: problems.append(f"undefined effect {e}")
# events
evs = set(re.findall(r"id = (man_sys\.\d+)", rd("events/MAN_systems_events.txt")[0]))
for e in set(re.findall(r"id = (man_sys\.\d+)", alltext)):
    if e not in evs: problems.append(f"undefined event {e}")
# sprites
gfx = ""
for f in glob.glob(P("interface/*.gfx")): gfx += open(f, encoding="utf-8-sig", errors="ignore").read()
for f in glob.glob(V + "interface/*.gfx"): gfx += open(f, encoding="utf-8-sig", errors="ignore").read()
sprites = set(re.findall(r'name\s*=\s*"?(GFX_[\w\-.]+)"?', gfx))
for s in set(re.findall(r"(?:icon|spriteType) = \"?(GFX_[\w\-]+)\"?", alltext)):
    if s not in sprites: problems.append(f"missing sprite {s}")
short = set(re.findall(r"^\t\ticon = ([a-z]\w+)$", dec, re.M))
for s in short:
    if "GFX_decision_" + s not in sprites: problems.append(f"missing short decision icon {s}")
for s in set(re.findall(r'texturefile = "(gfx/[^"]+)"', rd("interface/MAN_eco_focus_icons.gfx")[0] + rd("interface/MAN_systems.gfx")[0])):
    if not os.path.exists(P(s)): problems.append(f"missing texture {s}")
# focus loc + prereq ids
ft = rd("common/national_focus/manchukuo.txt")[0]
ids = set(re.findall(r"\n\t\tid = (\w+)", ft))
for i in ids:
    if i not in allloc: problems.append(f"missing focus loc {i}")
for p in set(re.findall(r"focus = (MAN_\w+)", ft)):
    if p not in ids: problems.append(f"bad prereq {p}")
for p in set(re.findall(r"has_completed_focus = (MAN_\w+)", alltext)):
    if p not in ids: problems.append(f"bad has_completed_focus {p}")
for t_ in (t for k, t in out):
    if "--" in t_ or "\u2014" in t_: problems.append("dash in loc")
print(f"loc entries {len(out)} | focuses {len(ids)} | problems {len(problems)}")
for p in sorted(set(problems)): print("  ", p)
