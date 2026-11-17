"""Manchukuo 'Racial Harmony' balance of power, rebuilt as the Concordia question:
Concord of Five Races (left, negative) vs Japanese Guidance (right, positive). Ids kept so history/set_power_balance still work."""
from man_common import *

BOP = """# Racial Harmony: Concord of Five Races (left) vs Japanese Guidance (right).
# The weekly systems read the active band (MAN_bop_tier): Japanese Guidance raises Kwantung Army patience and planning
# efficiency but feeds banditry; the Concord of Five Races calms the countryside and brings voluntary labour but tries the Army's patience.
MAN_racial_harmony = {
	initial_value = 0.45
	left_side = MAN_racial_harmony_chinese_bop
	right_side = MAN_racial_harmony_japanese_bop
	decision_category = MAN_racial_harmony_category_bop

	range = {
		id = MAN_racial_harmony_balance
		min = -0.1
		max = 0.1
		modifier = {
			political_power_factor = 0.10
			stability_factor = 0.03
		}
	}

	side = {
		id = MAN_racial_harmony_chinese_bop
		icon = GFX_bop_MAN_racial_harmony_chinese
		range = {
			id = MAN_racial_harmony_chinese_bop_moderate
			min = -0.4
			max = -0.1
			modifier = {
				stability_factor = 0.05
				political_power_factor = 0.05
				war_support_factor = -0.03
			}
		}
		range = {
			id = MAN_racial_harmony_chinese_bop_high
			min = -0.7
			max = -0.4
			modifier = {
				stability_factor = 0.08
				political_power_factor = 0.05
				recruitable_population_factor = 0.02
				war_support_factor = -0.06
			}
		}
		range = {
			id = MAN_racial_harmony_chinese_bop_total
			min = -1
			max = -0.7
			modifier = {
				stability_factor = 0.12
				political_power_factor = 0.10
				recruitable_population_factor = 0.04
				war_support_factor = -0.10
			}
		}
	}

	side = {
		id = MAN_racial_harmony_japanese_bop
		icon = GFX_bop_MAN_racial_harmony_japanese
		range = {
			id = MAN_racial_harmony_japanese_bop_moderate
			min = 0.1
			max = 0.4
			modifier = {
				industrial_capacity_factory = 0.02
				stability_factor = -0.03
			}
		}
		range = {
			id = MAN_racial_harmony_japanese_bop_high
			min = 0.4
			max = 0.7
			modifier = {
				industrial_capacity_factory = 0.04
				war_support_factor = 0.04
				stability_factor = -0.07
			}
		}
		range = {
			id = MAN_racial_harmony_japanese_bop_total
			min = 0.7
			max = 1
			modifier = {
				industrial_capacity_factory = 0.06
				war_support_factor = 0.08
				stability_factor = -0.12
				political_power_factor = -0.10
			}
		}
	}
}
"""

def fv(k, n): s = f"m{-n}" if n < 0 else f"{n}"; return f"add_to_variable = {{ MAN_fav_{k} = {n} }}\ncustom_effect_tooltip = MAN_tt_fav_{k}_{s}\n"
def pt(n): s = f"m{-n}" if n < 0 else f"{n}"; return f"add_to_variable = {{ MAN_kw_pat = {n} }}\ncustom_effect_tooltip = MAN_tt_pat_{s}\n"
def shift(x): return f"add_power_balance_value = {{ id = MAN_racial_harmony value = {x} }}\n"
def bandit(sids, n): return "".join(f"if = {{ limit = {{ {s} = {{ is_owned_and_controlled_by = ROOT }} }} {s} = {{ add_to_variable = {{ MAN_bandit = {n} }} }} }}\n" for s in sids)
UPD = "hidden_effect = { MAN_pol_compute = yes MAN_sec_refresh = yes MAN_ui_refresh = yes }\n"

# key, icon, cost, re_enable (0 = once), visible, available, effect, ai, name, desc, extra loc
DEC = [
    ("chinese_officials", "MAN_promote_chinese_in_concordia_association", 40, 90, "", "",
     shift(-0.06) + "add_stability = 0.01\n" + pt(-4) + fv("ind", -2), 2,
     "Appoint Chinese Officials",
     "Give county magistracies and a few vice-ministerial posts to Chinese officials of proven loyalty. The Japanese staff resent losing the seats.", {}),
    ("mongol_autonomy", "MAN_promote_mongols_in_concordia_association", 35, 180,
     "OR = { 761 = { is_owned_and_controlled_by = ROOT } 612 = { is_owned_and_controlled_by = ROOT } }", "",
     shift(-0.05) + "custom_effect_tooltip = MAN_tt_bop_mongol\nhidden_effect = {\n" + bandit((761, 612, 1043), -5) + "}\n" + fv("kw", -2), 2,
     "Xing'an Mongol Autonomy",
     "Confirm the princes and lamas of the Xing'an provinces in their own administration, with Mongol schools and a Mongol cavalry force.",
     {"MAN_tt_bop_mongol": "Banditry in Hulunbuir, Xilingol and Pailingmiao: §G-5§!"}),
    ("korean_council", "MAN_promote_koreans_in_concordia_association", 30, 120, "", "",
     shift(-0.04) + "add_to_variable = { MAN_labour = 8 }\ncustom_effect_tooltip = MAN_tt_labour_8\n" +
     "custom_effect_tooltip = MAN_tt_bop_korean\nhidden_effect = { if = { limit = { check_variable = { MAN_band1 > 5 } } subtract_from_variable = { MAN_band1 = 5 } } }\n", 2,
     "Korean Seats in the Concordia",
     "Give the Korean farmers of Jiandao and the river flats their own councils. Many of Yang Jingyu's partisans are Korean, and some of their families take the offer.",
     {"MAN_tt_bop_korean": "£nato_unit_irregular_infantry_icon_small §OFirst Route Army§! strength: §G-5§!"}),
    ("russian_bureau", "MAN_promote_russians_in_concordia_association", 25, 180, "", "",
     shift(-0.03) + fv("kw", 3) + "custom_effect_tooltip = MAN_tt_bop_russian\nhidden_effect = { if = { limit = { check_variable = { MAN_band3 > 3 } } subtract_from_variable = { MAN_band3 = 3 } } }\n", 2,
     "The White Russian Bureau",
     "The Bureau of Russian Emigrants in Harbin speaks for the city's White Russians, and supplies scouts and interpreters to the Kwantung Army's intelligence service.",
     {"MAN_tt_bop_russian": "£nato_unit_irregular_infantry_icon_small §OThird Route Army§! strength: §G-3§!"}),
    ("fugu", "MAN_promote_jews_in_concordia_association", 50, 0, "", "date > 1937.12.25",
     shift(-0.05) + fv("mgy", 8) + "add_cic = 2000\n", 1,
     "The Far Eastern Jewish Conference",
     "In December 1937 the Jewish communities of the Far East meet in Harbin with Japanese blessing. Ayukawa and the army's Jewish experts dream of American Jewish capital for Manchuria; a little of it actually comes.", {}),
    ("vice_ministers", "MAN_promote_japanese_in_concordia_association", 30, 90, "", "",
     shift(0.06) + fv("gab", 4) + pt(3), 3,
     "The Vice-Ministers' Conference",
     "Every Tuesday the Japanese vice-ministers meet at the General Affairs Board and decide what the Chinese ministers will sign on Wednesday.", {}),
    ("manchu_court", "MAN_promote_manchus_in_concordia_association", 35, 180, "", "",
     shift(0.03) + "add_stability = 0.02\n" + pt(2), 2,
     "Honour the Manchu Bannermen",
     "Restore stipends and court ranks to the Manchu banner families around the throne. Their loyalty is to Puyi, and Puyi's to the Kwantung Army.", {}),
    ("kempeitai", "oppression", 20, 180,
     "OR = { has_completed_focus = MAN_sec_kempeitai has_completed_focus = MAN_pol_tojo_kempeitai }", "",
     shift(0.08) + "add_stability = -0.02\n" + fv("kw", 3) + fv("gab", -3) +
     "custom_effect_tooltip = MAN_tt_bop_kempeitai\nhidden_effect = { every_owned_state = { limit = { " + MANCHURIA_TRIGGER + " } add_to_variable = { MAN_bandit = -3 } } }\n", 2,
     "Kempeitai Thought Control",
     "Arrest the Concordia's Chinese activists as 'thought criminals'. The countryside is quieter for a while, and the Concordia's ideal of harmony a little emptier.",
     {"MAN_tt_bop_kempeitai": "Banditry in every Manchurian province: §G-3§!"}),
]

RANGES = {
    "MAN_racial_harmony": "Racial Harmony",
    "MAN_racial_harmony_chinese_bop": "Concord of Five Races",
    "MAN_racial_harmony_japanese_bop": "Japanese Guidance",
    "MAN_racial_harmony_balance": "The Kingly Way in Balance",
    "MAN_racial_harmony_chinese_bop_moderate": "Concord of Nations",
    "MAN_racial_harmony_chinese_bop_high": "The Five Races in Harmony",
    "MAN_racial_harmony_chinese_bop_total": "A Manchurian Nation",
    "MAN_racial_harmony_japanese_bop_moderate": "Internal Guidance",
    "MAN_racial_harmony_japanese_bop_high": "Japanese Officials Rule",
    "MAN_racial_harmony_japanese_bop_total": "A Japanese Colony in All But Name",
}

def build(ind):
    B = "\\n£white_dot "
    wr("common/bop/MAN.txt", BOP)
    d = "# Racial Harmony balance of power decisions (shown in the balance of power window)\nMAN_racial_harmony_category_bop = {\n"
    L = []
    for (k, icon, cost, ren, vis, av, eff, ai, nm, desc, extra) in DEC:
        s = f"MAN_bop_{k} = {{\n\ticon = {icon}\n\tallowed = {{ original_tag = MAN }}\n"
        if vis: s += f"\tvisible = {{ {vis} }}\n"
        if av: s += f"\tavailable = {{ {av} }}\n"
        s += f"\tcost = {cost}\n"
        s += "\tfire_only_once = yes\n" if ren == 0 else f"\tfire_only_once = no\n\tdays_re_enable = {ren}\n"
        s += "\tcomplete_effect = {\n" + ind(eff + UPD, 2) + "\t}\n"
        s += f"\tai_will_do = {{ base = {ai} }}\n}}\n"
        d += ind(s, 1)
        L += [(f"MAN_bop_{k}", nm), (f"MAN_bop_{k}_desc", desc)]
        L += list(extra.items())
    d += "}\n"
    wr("common/decisions/MAN_racial_harmony_bop_decisions.txt", d)
    L += list(RANGES.items())
    L += [("MAN_racial_harmony_category_bop", "$MAN_racial_harmony$"),
          ("MAN_racial_harmony_desc", "Is Manchukuo a union of five races, or a Japanese colony with a Manchu emperor?" +
           B + "§LJapanese Guidance§!: §G+§! £army_experience §LKwantung Army patience§! and £prod_eff §Yplanning efficiency§!, §R+§! £pol_violence §Obanditry§! growth" +
           B + "§LConcord of Five Races§!: §G-§! £pol_violence §Obanditry§! growth and voluntary £manpower_texticon §Ylabour§!, §R-§! £army_experience §LKwantung Army patience§!" +
           B + "The further from the centre, the stronger both effects")]
    return L
