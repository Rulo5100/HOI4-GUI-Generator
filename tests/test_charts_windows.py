"""Tests for charts, popup windows, controls, YAML templates, the mock interpreter and click simulation.

    python -m unittest discover -s tests
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guigen import ModFS, Project
from guigen.charts import BarChart, LineChart, PieChart, ScaleMarker, StackedBar
from guigen.chartsprites import LineSegments
from guigen.mock import Mock
from guigen.validate import validate
from guigen.windows import PopupWindow, stepper, switch
from test_guigen import make_mod


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="guigen_test_")
        self.mod = os.path.join(self.tmp, "mod")
        make_mod(self.mod)
        self.fs = ModFS(self.mod, stage=os.path.join(self.tmp, "stage"))
        self.fs.vanilla = None

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def project(self):
        p = Project(self.fs, "TST")
        b = p.board("TST_board")
        b.window.h = 400
        return p, b


class TestCharts(Base):
    def test_pie_layers_are_cumulative(self):
        p, b = self.project()
        pie = PieChart(p, b, "TST_pie", 10, 10, 100, [("TST_a", "A", "red"), ("TST_b", "B", "blue"), ("TST_c", "C", "green")], steps=50)
        v = pie.mock_vars(Mock({"vars": {"TST_a": 10, "TST_b": 30, "TST_c": 60}}))
        self.assertEqual([v["TST_pie_f_0"], v["TST_pie_f_1"], v["TST_pie_f_2"]], [6, 21, 51])     # 10%, 40%, 100% of 50 steps, +1
        self.assertAlmostEqual(v["TST_pie_p_1"], 30)
        names = [e.name for e in b.elements() if e.name.startswith("TST_pie_s")]
        self.assertEqual(names, ["TST_pie_s2", "TST_pie_s1", "TST_pie_s0"])      # largest cumulative layer drawn first
        body = pie.update_body()
        self.assertIn("add_to_temp_variable = { gg_cum = TST_b }", body)
        self.assertIn("divide_variable = { TST_pie_f_1 = TST_pie_total }", body)

    def test_pie_shader_mode_uses_vanilla_radial(self):
        p, b = self.project()
        PieChart(p, b, "TST_pie", 10, 10, 100, [("TST_a", "A", "red")], mode="shader")
        gfx = p.gfx_text()
        self.assertIn("progressbartype = {", gfx)
        self.assertIn('effectFile = "gfx/FX/progress_radial.lua"', gfx)
        self.assertEqual(p.shader_files(), [])                 # no custom shader needed for pies

    def test_line_chart_levels_and_encoding(self):
        p, b = self.project()
        lc = LineChart(p, b, "TST_line", 10, 10, 220, 90, [{"array": "TST_hist", "source": "TST_x"}], points=12, levels=10)
        v = lc.mock_vars(Mock({"arrays": {"TST_hist": [0, 100, 50]}}))
        self.assertEqual(v["TST_line_f0_0"], LineSegments.frame_of(0, 9, 10))
        self.assertEqual(v["TST_line_f0_1"], LineSegments.frame_of(9, round(4.5), 10))
        self.assertNotIn("TST_line_f0_2", v)                  # only 3 points: 2 segments
        names = dict(lc.effects())
        self.assertIn("TST_line_record", names)
        self.assertIn("remove_from_array = { array = TST_hist index = 0 }", names["TST_line_record"])
        self.assertIn("check_variable = { TST_hist^num > 2 }", p.scripted_gui_text())

    def test_line_shader_writes_shader_file(self):
        p, b = self.project()
        LineChart(p, b, "TST_line", 10, 10, 220, 90, [{"array": "TST_hist"}], points=12, mode="shader")
        self.assertEqual(p.shader_files()[0][0], "gfx/FX/guigen_line.shader")
        self.assertNotIn("textureFile1", p.gfx_text())      # the line shader draws from colours only

    def test_auto_switches_wide_bars_to_vanilla_progress(self):
        p, b = self.project()
        StackedBar(p, b, "TST_stack", 10, 10, 600, 20, [("TST_a", "A", "red"), ("TST_b", "B", "blue")])
        self.assertIn('effectFile = "gfx/FX/progress.lua"', p.gfx_text())
        p2, b2 = self.project()
        StackedBar(p2, b2, "TST_stack", 10, 10, 120, 20, [("TST_a", "A", "red")])
        self.assertNotIn("progressbartype", p2.gfx_text())

    def test_bar_auto_max_and_marker(self):
        p, b = self.project()
        bc = BarChart(p, b, "TST_bars", 10, 10, 200, 100, [("TST_a", "A", "red"), ("TST_b", "B", "blue")], steps=20)
        v = bc.mock_vars(Mock({"vars": {"TST_a": 50, "TST_b": 200}}))
        self.assertEqual((v["TST_bars_max"], v["TST_bars_f_0"], v["TST_bars_f_1"]), (200, 6, 21))
        sm = ScaleMarker(p, b, "TST_scale", 20, 200, 100, "TST_v", 0, 100, marker=10)
        self.assertEqual(sm.mock_vars(Mock({"vars": {"TST_v": 25}}))["TST_scale_x"], 20 + 25 - 5)
        self.assertIn("TST_scale_mk = { x = TST_scale_x }", p.scripted_gui_text())

    def test_chart_project_validates(self):
        p, b = self.project()
        PieChart(p, b, "TST_pie", 10, 10, 100, [("TST_a", "A", "red"), ("TST_b", "B", "blue")])
        LineChart(p, b, "TST_line", 10, 150, 220, 90, [{"array": "TST_hist", "source": "TST_x"}], points=12)
        p.write()
        errors, warnings = validate(p, self.fs)
        self.assertEqual(errors, [])
        self.assertIn("TST_guigen_refresh = {", p.frames_text())


class TestWindows(Base):
    def test_popup_wiring(self):
        p = Project(self.fs, "TST")
        win = PopupWindow(p, "TST_win", "TST_TITLE", 500, 300, opener="top_bar", opener_xy=(100, 4))
        p.loc("TST_TITLE", "Title")
        stepper(win.board, p, "TST_step", 20, 60, "TST_v", step=5, lo=0, hi=50)
        switch(win.board, p, "TST_sw", 20, 100, "TST_on", label="On")
        sg, gui = p.scripted_gui_text(), p.gui_text()
        self.assertIn("visible = { has_country_flag = TST_win_open }", sg)
        self.assertIn("parent_window_token = top_bar", sg)
        self.assertIn("TST_win_close_click = { clr_country_flag = TST_win_open }", sg)
        self.assertIn("moveable = yes", gui)
        self.assertIn("corneredTileSpriteType", p.gfx_text())
        p.write()
        errors, _ = validate(p, self.fs)
        self.assertEqual(errors, [])

    def test_mock_effects(self):
        m = Mock({"vars": {"x": 5, "political_power": 50}, "flags": ["open"]})
        m.run("add_to_variable = { x = 10 } clamp_variable = { var = x min = 0 max = 12 } add_political_power = -5 "
              "if = { limit = { has_country_flag = open } clr_country_flag = open } else = { set_country_flag = open } "
              "716 = { set_state_flag = done }")
        self.assertEqual((m.var("x"), m.var("political_power"), "open" in m.flags), (12, 45, False))
        self.assertIn("done", m.state_flags["716"])
        m.run("if = { limit = { has_country_flag = open } clr_country_flag = open } else = { set_country_flag = open }")
        self.assertIn("open", m.flags)

    def test_click_switches_tab(self):
        from guigen.preview import Renderer
        from guigen.tabs import TabSet
        p, b = self.project()
        tabs = TabSet(p, b, "TST_tab", [("a", "TST_A"), ("b", "TST_B")], x=10, y=10, content_y=40, content_h=100)
        p.loc("TST_A", "A")
        p.loc("TST_B", "B")
        p.write()
        r = Renderer(p, self.fs, Mock({"vars": {"TST_tab": 0}}))
        r.render_board(b)
        el, bb = next((e, bb) for e, bb in r.last_boxes if e.name == "TST_tab_btn_b")
        self.assertEqual(r.click(b, bb[0] + 2, bb[1] + 2), "TST_tab_btn_b: clicked")
        self.assertEqual(r.mock.var("TST_tab"), 1)


class TestTemplates(Base):
    def test_templates_validate(self):
        from guigen.templates import render
        from guigen.yamlspec import load_yaml
        for tpl in ("window", "board"):
            spec, _ = render(tpl, "TST", "x.yaml", "x_mock.yaml")
            path = os.path.join(self.tmp, f"{tpl}.yaml")
            with open(path, "w", encoding="utf-8") as f:
                f.write(spec)
            fs = ModFS(self.mod, stage=os.path.join(self.tmp, f"stage_{tpl}"))
            fs.vanilla = None
            p = load_yaml(fs, path)
            p.write()
            errors, _ = validate(p, fs)
            if tpl == "board":                          # uses two vanilla sprites, absent from the bare test mod
                errors = [e for e in errors if "GFX_goal_generic_trade" not in e and "GFX_button_94x31" not in e]
            self.assertEqual(errors, [], tpl)


@unittest.skipUnless(os.environ.get("GUIGEN_REFERENCE_MOD"), "set GUIGEN_REFERENCE_MOD to the reference mod to run")
class TestReferencePort(unittest.TestCase):
    """The three-board reference port in tests/fixtures/port_reference must rebuild the reference mod's
    files byte for byte (text and PNG), with its loc entries and embedded effect block matching."""

    def test_identical(self):
        from guigen.cli import compare, load_spec
        stage = tempfile.mkdtemp(prefix="guigen_ref_")
        try:
            fs = ModFS(os.environ["GUIGEN_REFERENCE_MOD"], stage=stage)
            p = load_spec(os.path.join(os.path.dirname(__file__), "fixtures", "port_reference", "spec.py"))(fs)
            p.write()
            lines, ok = compare(fs, p)
            self.assertTrue(ok, "\n".join(l for l in lines if not l.startswith("identical")))
        finally:
            shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
