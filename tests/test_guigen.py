"""Unit tests on a tiny throwaway mod (no HOI4 install needed).

    python -m unittest discover -s tests
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guigen import Bar, Flags, Linear, LocError, ModFS, Project, Thresholds
from guigen.cli import compare
from guigen.validate import validate


def make_mod(root, crlf=True):
    nl = "\r\n" if crlf else "\n"
    os.makedirs(os.path.join(root, "interface"))
    os.makedirs(os.path.join(root, "localisation", "english"))
    os.makedirs(os.path.join(root, "common", "decisions", "categories"))
    os.makedirs(os.path.join(root, "common", "scripted_effects"))
    with open(os.path.join(root, "common", "decisions", "categories", "t.txt"), "wb") as f:
        f.write(f"TST_cat = {{{nl}\tscripted_gui = TST_board{nl}}}{nl}".encode())
    with open(os.path.join(root, "common", "scripted_effects", "t.txt"), "wb") as f:
        f.write(f"TST_do_it = {{{nl}\tadd_political_power = 1{nl}}}{nl}".encode())
    with open(os.path.join(root, "interface", "base.gfx"), "wb") as f:
        f.write(f'spriteTypes = {{{nl}\tspriteType = {{{nl}\t\tname = "GFX_button"{nl}\t\ttexturefile = "gfx/b.png"{nl}\t}}{nl}}}{nl}'.encode())


def small_project(fs, **kw):
    p = Project(fs, "TST")
    p.sprite(Bar("GFX_TST_bar", p.png("bar"), 100, 10, "gold"))
    p.frame(Linear("TST_f_x", "TST_x"))
    b = p.board("TST_board")
    b.text("TST_title", 10, 4, "TST_TITLE", 300, 22, "hoi_18mbs")
    b.icon("TST_bar", 10, 30, "GFX_TST_bar", frame_var="TST_f_x", tooltip="TST_BAR_TT")
    b.button("TST_go", 10, 50, "GFX_button", "TST_GO_TT", click="TST_do_it = yes", enabled="always = yes")
    b.window.h = 80
    p.loc("TST_TITLE", "Test board")
    p.loc("TST_BAR_TT", "§YProgress§!")
    p.loc("TST_GO_TT", "Go")
    return p


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="guigen_test_")
        self.mod = os.path.join(self.tmp, "mod")
        make_mod(self.mod)
        self.fs = ModFS(self.mod, vanilla=self.tmp, stage=os.path.join(self.tmp, "stage"))
        self.fs.vanilla = None          # keep tests independent of a local HOI4 install

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def built(self, p):
        p.write()
        return validate(p, self.fs)


class TestFrames(unittest.TestCase):
    def test_linear_text_matches_man(self):
        t = Linear("MAN_f_steel", "MAN_pct_steel").text()
        self.assertEqual(t, "set_variable = { MAN_f_steel = MAN_pct_steel }\ndivide_variable = { MAN_f_steel = 10 }\n"
                            "round_variable = MAN_f_steel\nadd_to_variable = { MAN_f_steel = 1 }\n"
                            "clamp_variable = { var = MAN_f_steel min = 1 max = 11 }\n")

    def test_linear_mapping(self):
        r = Linear("v", "s", frames=21)
        self.assertEqual([r.value_to_frame(v) for v in (0, 4, 50, 100, 140)], [1, 2, 11, 21, 21])
        r = Linear("v", "s", lo=-50, hi=50)
        self.assertEqual(r.value_to_frame(-50), 1)
        self.assertIn("subtract_from_variable = { v = -50 }", r.text())

    def test_thresholds_and_flags(self):
        self.assertEqual(Thresholds("v", "s", [25, 45]).value_to_frame(30), 2)
        self.assertIn("check_variable = { s > 24.99 }", Thresholds("v", "s", [25]).text())
        self.assertEqual(Flags("v", 716, ["a", "b"]).flags_to_frame({"b"}), 3)


class TestLoc(Base):
    def test_rules(self):
        p = Project(self.fs, "TST")
        for bad in ("a — b", "a -- b", "two\nlines", 'say "hi"'):
            with self.assertRaises(LocError):
                p.loc("TST_BAD", bad)
        p.loc("TST_OK", "line one\\nline two")

    def test_merge_keeps_other_keys(self):
        from guigen.loc import Loc
        l = Loc()
        l.add("A", "new a")
        l.add("C", "new c")
        out = l.merge_into('l_english:\n A:0 "old a"\n B:0 "keep b"\n')
        self.assertEqual(out, 'l_english:\n A:0 "new a"\n B:0 "keep b"\n C:0 "new c"\n')


class TestEol(Base):
    def test_matches_existing_file(self):
        rel = "interface/x.gui"
        with open(self.fs.path(rel), "wb") as f:
            f.write(b"a = {\n}\n")
        self.fs.write_text(rel, "b = {\n}\n")
        self.assertEqual(open(self.fs.out_path(rel), "rb").read(), b"b = {\n}\n")

    def test_new_file_defaults_to_crlf(self):
        self.fs.write_text("interface/new.gui", "b = {\n}\n")
        self.assertEqual(open(self.fs.out_path("interface/new.gui"), "rb").read(), b"b = {\r\n}\r\n")

    def test_braces_checked(self):
        with self.assertRaises(ValueError):
            self.fs.write_text("interface/bad.gui", "a = {\n")


class TestValidate(Base):
    def test_clean(self):
        errors, warnings = self.built(small_project(self.fs))
        self.assertEqual(errors, [])
        self.assertEqual([w for w in warnings if "texture" not in w], [])

    def test_catches_mistakes(self):
        p = small_project(self.fs)
        b = p.boards[0]
        b.icon("TST_missing", 10, 60, "GFX_nope")
        b.text("TST_t2", 120, 70, "TST_NO_SUCH_KEY", 100)       # also reaches below the 80 px window
        b.text("TST_t3", 120, 4, "[ROOT.GetTSTNothing]", 100)
        b.visible("TST_ghost", "always = yes")
        b.click("TST_go", "TST_undefined_effect = yes", modifier="right")
        p.frame(Linear("TST_f_big", "TST_y", frames=21))
        b.icon("TST_bar2", 10, 70, "GFX_TST_bar", frame_var="TST_f_big")
        errors, warnings = self.built(p)
        text = "\n".join(errors)
        for needle in ("GFX_nope", "TST_NO_SUCH_KEY", "GetTSTNothing", "TST_ghost", "TST_undefined_effect", "TST_f_big reaches frame 21"):
            self.assertIn(needle, text)
        self.assertTrue(any("bottom" in w for w in warnings))

    def test_missing_category_warns(self):
        p = small_project(self.fs)
        p.boards[0].name = "TST_other"
        _, warnings = self.built(p)
        self.assertTrue(any("no decision category" in w for w in warnings))


class TestDiff(Base):
    def test_identical_then_changed(self):
        live = ModFS(self.mod)
        small_project(live).write()            # "live" files in the mod
        p = small_project(self.fs)
        p.write()
        lines, ok = compare(self.fs, p)
        self.assertTrue(ok, lines)
        fs2 = ModFS(self.mod, stage=os.path.join(self.tmp, "stage2"))
        p2 = small_project(fs2)
        p2.sprites.get("GFX_TST_bar").colour = (1, 2, 3)
        p2.boards[0].window.children[0].text = "TST_GO_TT"
        p2.write()
        lines, ok = compare(fs2, p2)
        self.assertFalse(ok)
        joined = "\n".join(lines)
        self.assertIn("pixels differ", joined)
        self.assertIn("DIFFERS    interface/TST_guigen.gui", joined)


class TestTabs(Base):
    def test_tabs(self):
        from guigen.tabs import TabSet
        p = small_project(self.fs)
        b = p.boards[0]
        tabs = TabSet(p, b, "TST_tab", [("a", "TST_TAB_A"), ("b", "TST_TAB_B")], x=10, y=60, content_y=90, content_h=40)
        with tabs.section("a"):
            b.text("TST_in_a", 0, 0, "TST_TITLE", 100)
        with tabs.section("b"):
            b.text("TST_in_b", 0, 0, "TST_TITLE", 100)
        p.loc("TST_TAB_A", "A")
        p.loc("TST_TAB_B", "B")
        b.window.h = 140
        errors, _ = self.built(p)
        self.assertEqual(errors, [])
        sg = p.scripted_gui_text()
        self.assertIn("TST_tab_sec_a_visible = { check_variable = { TST_tab = 0 } }", sg)
        self.assertIn("TST_tab_btn_b_click = { set_variable = { TST_tab = 1 } }", sg)
        self.assertIn('containerWindowType = {\n\t\t\tname = "TST_tab_sec_a"', p.gui_text())


if __name__ == "__main__":
    unittest.main()
