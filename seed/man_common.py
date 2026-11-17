"""Shared helpers + constants for the Manchukuo systems build."""
import os, re
ROOT = r"C:/Users/Roberts (ME)/Documents/Paradox Interactive/Hearts of Iron IV/mod/Secret Rearmament"
WS = r"C:/Program Files (x86)/Steam/steamapps/workshop/content/394360/"
P = lambda p: os.path.join(ROOT, p)
NL = chr(92) + "n"

def rd(p):
    b = open(P(p), "rb").read()
    return b.decode("utf-8-sig").replace("\r\n", "\n"), b.startswith(b"\xef\xbb\xbf")

def wr(p, t, bom=False):
    os.makedirs(os.path.dirname(P(p)), exist_ok=True)
    t = t.replace("\r\n", "\n")
    assert t.count("{") == t.count("}"), (p, t.count("{"), t.count("}"))
    open(P(p), "wb").write((b"\xef\xbb\xbf" if bom else b"") + t.replace("\n", "\r\n").encode("utf-8"))

def wr_loc(p, entries):
    """entries: list of (key, text). Writes l_english yml with BOM."""
    s = "l_english:\n"
    for k, v in entries:
        assert "\u2014" not in v and "--" not in v, (k, v)
        s += f" {k}:0 \"{v}\"\n"
    open(P(p), "wb").write(b"\xef\xbb\xbf" + s.replace("\n", "\r\n").encode("utf-8"))

def ind(s, n):
    pad = "\t" * n
    return "".join(pad + l + "\n" if l.strip() else "\n" for l in s.strip("\n").split("\n"))

# Manchurian heartland states (Inner Mongolian ones may later pass to Mengjiang; every effect checks ownership)
STATES = [716, 715, 328, 717, 714, 761, 610, 611, 612, 1043]
SNAME = {716: "Liaoning", 715: "Liaobei", 328: "Kirin", 717: "Sungkiang", 714: "Heilungkiang", 761: "Hulunbuir",
         610: "Jehol", 611: "Chahar", 612: "Xilingol", 1043: "Pailingmiao"}
BANDIT0 = {716: 20, 715: 55, 328: 50, 717: 60, 714: 35, 761: 15, 610: 40, 611: 25, 612: 20, 1043: 20}
BGROW = {716: 0.08, 715: 0.15, 328: 0.15, 717: 0.15, 714: 0.12, 761: 0.08, 610: 0.15, 611: 0.08, 612: 0.08, 1043: 0.08}
# zone type -> eligible states (only where that zone has something to build: keeps the decision list short)
ZONES = {
    "hi":   [716, 328, 717, 714],
    "min":  [716, 715, 328, 717, 714, 761, 610],
    "pow":  [716, 328, 717],
    "set":  [717, 714, 761, 328, 715, 611, 612],
}
QUOTAS = [("steel", "Iron and Steel"), ("coal", "Coal and Liquid Fuel"), ("power", "Electric Power"), ("mach", "Machinery and Munitions")]
BROKERS = ["kw", "gab", "ind", "mgy", "smr"]
TARGETS = "{ " + " ".join(map(str, STATES)) + " }"
MANCHURIA_TRIGGER = "OR = { " + " ".join(f"state = {s}" for s in STATES) + " }"
