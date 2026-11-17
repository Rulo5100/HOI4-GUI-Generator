"""Manchukuo Library: the imported historical vignettes no longer fire on their own. They are read on demand from a
Library decision category at the bottom of the decisions screen, with their stat effects stripped (reading is free and
changes nothing). The opium-trade events are tied to the Jehol Opium Monopoly run instead."""
import re
from man_common import *

# key, first event of the chain, decision name, short description
LIB = [
    ("history", "manchukou.141", "The History of Manchuria", "Ten chapters, from the Russo-Japanese War and the founding of Mantetsu to Puyi's gilded cage."),
    ("hujun", "manchukou.1", "The Hujun Incident", "A border clash on the Mongolian frontier in 1936."),
    ("xingan", "manchukou.14", "The Xing'an Affair", "The Mongol governors of Xing'an, the arrests, and the execution of Lin Sheng."),
    ("kaspe", "manchukou.23", "The Kaspe Affair", "The kidnapping and murder of Simon Kaspe in Harbin, and the trials that followed."),
    ("pujie", "manchukou.45", "Prince Pujie's Marriage", "The search for a Japanese bride for the Emperor's brother, and his wedding to Saga Hiro."),
    ("fugu", "manchukou.53", "The Fugu Plan", "Japanese schemes to settle European Jewish refugees in Manchukuo."),
    ("puyi", "manchukou.151", "The Veneration of Puyi", "The cult of the Kangde Emperor."),
    ("living_death", "manchukou.152", "A Living Death", "The Emperor's life inside the palace in Hsinking."),
    ("tour", "manchukou.126", "The Industrialists' Tour", "Japanese industrialists tour Manchukuo in 1936."),
    ("governor", "manchukou.35", "A Governor Resigns", "A provincial governor leaves office."),
    ("luo", "manchukou.36", "Luo Zhenyu Retires", "The Qing loyalist scholar withdraws from public life."),
    ("sasaki", "manchukou.37", "Sasaki Toichi Leaves", "The Kwantung Army's China hand leaves Manchukuo."),
    ("crime", "manchukou.89", "Criminal Altercations", "Gang wars and police shootouts in the cities."),
]
LIB_EVENTS = {"manchukou.%d" % i for i in [1, 14, 15, 16, 17, 18, 19, 23, 24, 25, 26, 27, 28, 29, 35, 36, 37, 45, 46, 47, 48,
                                            53, 54, 55, 56, 89, 90, 91, 126] + list(range(141, 153))}
OPIUM = ["manchukou_opium.%d" % i for i in range(1, 7)]

def decisions(loc):
    s = ""
    for i, (k, ev, nm, desc) in enumerate(LIB):
        s += f"""MAN_lib_{k} = {{
	icon = GFX_decision_generic_political_discourse
	priority = {100 - i}
	allowed = {{ original_tag = MAN }}
	cost = 0
	fire_only_once = no
	days_re_enable = 7
	complete_effect = {{
		custom_effect_tooltip = MAN_tt_lib_read
		hidden_effect = {{ country_event = {{ id = {ev} }} }}
	}}
	ai_will_do = {{ base = 0 }}
}}
"""
        loc(f"MAN_lib_{k}", nm)
        loc(f"MAN_lib_{k}_desc", desc)
    loc("MAN_tt_lib_read", "Read the story. Library entries are for reading only: they change nothing.")
    return s

CAT = """
MAN_library_cat = {
	icon = GFX_decision_category_generic_political_actions
	priority = 1
	allowed = { original_tag = MAN }
	visible_when_empty = yes
}
"""
CAT_LOC = [("MAN_library_cat", "Library"),
           ("MAN_library_cat_desc", "Historical vignettes from the archive of the Manchukuo state. They never fire on their own; read them whenever you like.")]

def opium_hook():
    """Root effect for the Jehol Opium Monopoly run: each completed run brings the next chapter of the opium trade."""
    s = "add_to_variable = { MAN_opium_runs = 1 }\ncustom_effect_tooltip = MAN_tt_opium_chapter\nhidden_effect = {\n"
    for i, ev in enumerate(OPIUM, 1):
        s += f"\tif = {{ limit = {{ check_variable = {{ MAN_opium_runs = {i} }} }} country_event = {{ id = {ev} days = 3 }} }}\n"
    return s + "}\n"
OPIUM_LOC = [("MAN_tt_opium_chapter", "The first §Y6§! runs each bring a new chapter of the opium trade (an event)")]

STAT = r"(add_political_power|add_stability|add_war_support|add_manpower|army_experience) = -?[\d.]+"

def clean_events(t):
    """Strip stat effects from library events and shorten their chain delays to one day."""
    out, pos = [], 0
    for m in re.finditer(r"\n(country_event|news_event) = \{", t):
        i = m.end(); d = 1
        while d: d += t[i] == "{"; d -= t[i] == "}"; i += 1
        b = t[m.start():i]
        eid = re.search(r"\bid = ([\w.]+)", b).group(1)
        if eid in LIB_EVENTS:
            b = re.sub(r"\n[ \t]*" + STAT + r"[ \t]*(?=\r?\n)", "", b)
            b = re.sub(r"\n[ \t]*\d+ = \{ " + STAT + r" \}[ \t]*(?=\r?\n)", "", b)   # inline state-scope stat effects
            b = re.sub(r"\n[ \t]*add_popularity = \{[^{}]*\}[ \t]*(?=\r?\n)", "", b)
            b = re.sub(r"\n[ \t]*set_country_flag = MAN_(jewish_state_available|jews_are_another_one_race_available)_flag[ \t]*(?=\r?\n)", "", b)
            b = re.sub(r"(country_event = \{ id = manchukou\.\d+ )days = \d+", r"\1days = 1", b)
            b = re.sub(r"(country_event = \{\s*id = manchukou\.\d+\s+)days = \d+", r"\1days = 1", b)
        out.append(t[pos:m.start()]); out.append(b); pos = i
    out.append(t[pos:])
    return "".join(out)

REHOOKED = ["manchukou.137", "manchukou.52"]   # now started by focuses (Mantetsu Question, Korean resettlement)

def _event(t, eid):
    m = re.search(r"\n(country_event|news_event) = \{\r?\n\tid = " + re.escape(eid) + r"\r?\n", t)
    i = m.end(); d = 1
    while d: d += t[i] == "{"; d -= t[i] == "}"; i += 1
    return m.start(), i

def _patch(t, eid, fn):
    a, b = _event(t, eid)
    return t[:a] + fn(t[a:b]) + t[b:]

def rehook_events(t):
    """Wire the imported Mantetsu Question chain and the Korean resettlement into the focus tree (idempotent)."""
    nl = "\r\n" if "\r\n" in t else "\n"
    def add_after(b, anchor, line):
        if line in b: return b
        assert anchor in b, anchor
        return b.replace(anchor, anchor + nl + "\t\t\t" + line, 1)
    # the question opens: Matsuoka discovers the plot partway through
    t = _patch(t, "manchukou.137", lambda b: add_after(b, "MAN_ayukawa_arrives = yes", "country_event = { id = manchukou.133 days = 90 }"))
    t = _patch(t, "manchukou.133", lambda b: b.replace("add_political_power = 100", "add_political_power = 25"))
    # outcomes: Ayukawa's victory ends in Matsuoka's fall; Matsuoka's victory in his new research division
    t = _patch(t, "manchukou.127", lambda b: add_after(b, "set_country_flag = MAN_ayukawa_vs_matsuoka_Ayukawa_win_flag", "country_event = { id = manchukou.134 days = 30 }"))
    t = _patch(t, "manchukou.132", lambda b: add_after(b, "set_country_flag = MAN_ayukawa_vs_matsuoka_Matsuoka_win_flag", "country_event = { id = manchukou.136 days = 30 }"))
    # Korean resettlement: a yearly choice (up to 4 waves) once the Colonisation Company exists
    def k52(b):
        if "manchukou.52.b" in b: return b
        pic = re.search(r"picture = [\w.]+", b)
        new = ("\ncountry_event = {\n\tid = manchukou.52\n\ttitle = manchukou.52.t\n\tdesc = manchukou.52.d\n" + (f"\t{pic.group(0)}\n" if pic else "") +
               "\tis_triggered_only = yes\n\ttrigger = { check_variable = { event_manchukou_52_count < 4 } }\n\n"
               "\toption = {\n\t\tname = manchukou.52.a\n\t\tadd_to_variable = { event_manchukou_52_count = 1 }\n"
               "\t\t714 = { add_manpower = 9000 }\n\t\t717 = { add_manpower = 9000 }\n"
               "\t\tadd_to_variable = { MAN_labour = 10 }\n\t\tcustom_effect_tooltip = MAN_tt_labour_10\n"
               "\t\t717 = { set_state_flag = { flag = MAN_grievance days = 180 } }\n\t\tcustom_effect_tooltip = MAN_tt_korean_grievance\n"
               "\t\tcountry_event = { id = manchukou.52 days = 365 }\n\t}\n"
               "\toption = {\n\t\tname = manchukou.52.b\n\t\tadd_to_variable = { event_manchukou_52_count = 1 }\n"
               "\t\tcustom_effect_tooltip = MAN_tt_korean_refuse\n\t\tcountry_event = { id = manchukou.52 days = 365 }\n\t}\n}\n")
        return new.replace("\n", nl)
    t = _patch(t, "manchukou.52", k52)
    return t
REHOOK_LOC = [("manchukou.52.b", "Settle this wave somewhere else"),
              ("MAN_tt_korean_grievance", "§CSungkiang§!: a §Ogrievance§! for 180 days, as Chinese tenants are pushed off the land"),
              ("MAN_tt_korean_refuse", "No settlers this year. Another wave can come next year."),
              ("MAN_tt_mq_start", "If it has not begun yet: §YAyukawa's Report§! opens §LThe Mantetsu Question§! (180 days). Whoever wins, Mangyo or Mantetsu, decides which industrial focus opens"),
              ("MAN_tt_korean_waves", "Korean settler families start arriving: a yearly §YResettlement§! decision, up to §Y4§! waves")]

def clean_on_actions(oa):
    """Stop the library chains, the opium events and the rehooked chains from being scheduled at game start."""
    lib_first = {ev for _, ev, _, _ in LIB}
    for ev in sorted(lib_first | set(OPIUM) | set(REHOOKED)):
        oa = re.sub(r"\n[ \t]*country_event = \{ id = " + re.escape(ev) + r" days = \d+ \}[^\n]*(?=\r?\n)", "", oa)
    return oa
