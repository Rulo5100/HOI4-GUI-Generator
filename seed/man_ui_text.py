"""Short, coloured, bulleted text for the three decision-tab boards and their categories."""
import re

B = "\\n£white_dot "
PAT = "£army_experience §LKwantung Army patience§!"
BAN = "£pol_violence §Obanditry§!"
RA = "£nato_unit_irregular_infantry_icon_small §ORoute Armies§!"

OVR = {
    "MAN_PL_HELP_TT": "§YThe Industrial Development Plan§!" + B + "§YSurvey§! a province, then §Ydesignate§! it as Heavy Industry, Mining, Power or Settlement" +
        B + "Build its §Ysites§! and projects: they cost £pol_power, £manpower_texticon §Ylabour§! and £civ_factory while they run" +
        B + "Finished work fills the four §Yquotas§!" + B + "Output is cut by " + BAN + " and raised by £prod_eff §Yplanning efficiency§!" +
        B + "§YProduction runs§! and trade sites pay £civ_factory_output §YEconomic Capacity Surplus§!" +
        B + "Labour drives and labour gangs raise £manpower_texticon §YLabour levy pressure§! (now §Y[?MAN_levy|0]§!): every point costs §R0.015%§! stability a week, and it fades by §Y6%§! a week" +
        B + "Each running project ties up §Y0.5k§! £manpower_texticon §Ylabour§! a week, and idle workers above §Y60k§! drift home" +
        B + "Every finished site, project or megaproject risks an §Rindustrial accident§!: §Y20%§! an accident (stability and manpower lost), §Y10%§! a disaster (also war support and a £civ_factory civilian factory)" +
        B + "The §YAnnual Review§! needs §Y20%§! more total fulfilment each plan year: passing raises " + PAT + ", failing lowers it" +
        B + "At §Y100%§! by the third review or later, the Plan closes §Gahead of schedule§!",
    "MAN_PB_HELP_TT": "£pol_idea §LThe Hsinking Bureaucracy§!\\n£influence_texticon Favour (§Y0§! to §Y100§!) with each power centre feeds the spirit:" +
        B + "§LKwantung Army Staff§!: £organization_texticon organisation, £pol_violence stronger §OPunitive Sweeps§!" +
        B + "§LGeneral Affairs Board§!: £pol_power political power" +
        B + "§LMinistry of Industry§!: £construction_speed_icon construction speed, £prod_eff §Yplanning efficiency§!" +
        B + "§LMangyo§!: £industry_texticon factory output" +
        B + "§LMantetsu§!: £infrastructure_texticon infrastructure speed" +
        B + "£influence_texticon Favour drifts back to its §Lresting level§! (§Y40§!, raised by some focuses)" +
        B + "A man leaving for Tokyo becomes a £increase_texticon §Gpatron§! at §Y60§! favour or more, a £decrease_texticon §Renemy§! at §Y30§! or less",
    "MAN_PB_PAT_TT": PAT + B + "Above §Y50§!: §Gmore§! stability and war support. Below: §Rless§!" +
        B + "Below §Y40§!: §Rweekly§! stability loss, worse the lower it falls" + B + "Rises with §LKwantung Army Staff§! favour" +
        B + "Falls while average " + BAN + " is over §Y30§!" + B + "Reviews, requests and focuses move it sharply" +
        B + "Below §R15§!: the Army intervenes in the government",
    "MAN_SB_HELP_TT": "§OPublic Security§!" + B + "Every province has " + BAN + " from §Y0§! to §Y100§!" +
        B + "Penalties start at §Y25§! and worsen at §Y45§!, §Y65§! and §Y85§!" + B + "It cuts the Plan's output there and drains " + PAT +
        B + "Average " + BAN + " costs §R0.2%§! stability per point, and above §Y25§! also stability §Revery week§!" +
        B + "§RRaised by§!: §Ogrievances§! and the " + RA +
        B + "A §Ogrievance§! is local anger from reprisals, forced labour, settlers or requisitions: §R+0.15§! " + BAN + " growth a week in that province until it fades (§Y120§! to §Y365§! days)" +
        B + "§GLowered by§!: §OPolice Garrisons§!, blockhouses, §OCollective Hamlets§!, informants and §OPunitive Sweeps§!",
    "MAN_plan_cat_desc": "Survey and designate provinces, build their sites, and fill the four §Yquotas§! before each §YAnnual Review§!.",
    "MAN_politics_cat_desc": "Five Japanese power centres run Manchukuo. Court them, answer their requests and keep the " + PAT + ".",
    "MAN_security_cat_desc": "The " + RA + " of the Northeast Anti-Japanese United Army still hold the forests. £pol_violence §OBanditry§! slows construction, resources and the Plan.",
}
BANDS_TXT = {1: ("Yang Jingyu", ["Liaobei", "Kirin"], False), 2: ("Zhou Baozhong", ["Sungkiang", "Kirin"], True), 3: ("Zhao Shangzhi", ["Heilungkiang", "Sungkiang"], True)}
for n, (cmd, homes, exile) in BANDS_TXT.items():
    nm = ["", "First", "Second", "Third"][n]
    OVR[f"MAN_SB_BN_{n}_TT"] = (f"£nato_unit_irregular_infantry_icon_small §O{nm} Route Army§! ({cmd})" + B + "Home: " + ", ".join(f"§C{h}§!" for h in homes) +
        B + "Its strength raises " + BAN + " there every week" + B + "Worn down by §OPunitive Sweeps§! and §OCollective Hamlets§!" +
        B + "§OSurrender Campaigns§! peel men away" +
        (B + "When broken it may flee across the Amur, and return if the Soviets go to war" if exile else ""))

QI = {"STEEL": "£resources_strip|5 §YIron and Steel§!", "COAL": "£resources_strip|7 §YCoal and Liquid Fuel§!", "POWER": "£energy_texticon §YElectric Power§!",
      "MACH": "£mil_factory §YMachinery and Munitions§!", "PLAN": "£industry_texticon §YTotal plan fulfilment§!"}

def court(v):
    parts = v.split("\\n")
    body = [re.sub(r"^(Kwantung Army Staff|General Affairs Board|Ministry of Industry|Mangyo|Mantetsu) favour", r"£influence_texticon §L\1§! favour", p) for p in parts[1:]]
    return parts[0] + "".join(B + p for p in body)

def apply(entries):
    out = []
    for k, v in entries:
        if k in OVR: v = OVR[k]
        elif k.startswith("MAN_PB_COURT_") and k.endswith("_TT") and "£white_dot" not in v: v = court(v)
        elif k.startswith("MAN_PL_N_") and k.endswith("_TT"): v = QI[k[9:-3]] + "\\n" + v
        elif k.startswith("MAN_PB_I_") and k.endswith("_TT"):
            v = v.replace("\\nFavour: ", B + "£influence_texticon Favour: ").replace(" (neutral 50)", " (neutral §Y50§!)")
        out.append((k, v))
    return out
