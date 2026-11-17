"""Example: a full economy window in the style of the big overhaul mods.

An "Economy" button in the top bar opens a moveable window with four tabs:

* Overview  line + area chart of GDP and debt history, two ring gauges, a market-freedom scale
* Budget    revenue pie, spending donut (shader mode: vanilla progress_radial), a stacked debt bar
* Sectors   column chart of output by sector, heatmap of regions x sectors
* Policy    party positions on a compass, a tax-rate stepper and a price-controls switch

Every number comes from plain variables and two history arrays (see mock.yaml). In your mod:
    on_monthly: ECO_gdp_chart_record = yes      (appends ECO_gdp / ECO_debt, keeps 24 months)
    after changing any value: ECO_guigen_refresh = yes

    guigen preview examples/economy_window/spec.py --mod <mod> --mock examples/economy_window/mock.yaml
"""
from guigen import Project, TabSet
from guigen.charts import BarChart, Heatmap, LineChart, PieChart, RingGauge, ScaleMarker, Scatter, StackedBar, legend
from guigen.loc import bullets, c
from guigen.windows import PopupWindow, stepper, switch

SECTORS = [("agr", "Agriculture", "green"), ("min", "Mining", "#9c7a4a"), ("ind", "Industry", "gold"),
           ("srv", "Services", "blue"), ("mil", "Arms", "red")]
REGIONS = [("north", "North"), ("south", "South"), ("east", "East"), ("west", "West")]


def build(fs):
    p = Project(fs, "ECO", theme="steel")
    loc = p.loc
    win = PopupWindow(p, "ECO_econ", "ECO_TITLE", 720, 580, opener="top_bar", opener_xy=(620, 6),
                      opener_tooltip="ECO_OPEN_TT")
    b = win.board
    loc("ECO_TITLE", "The National Economy")
    loc("ECO_OPEN_TT", bullets(c.econ("The National Economy"), "Growth, budget, sectors and policy at a glance"))
    tabs = TabSet(p, b, "ECO_econ_tab", [("overview", "ECO_TAB_OVERVIEW"), ("budget", "ECO_TAB_BUDGET"),
                                         ("sectors", "ECO_TAB_SECTORS"), ("policy", "ECO_TAB_POLICY")],
                  x=16, y=win.top + 4, content_y=win.top + 40, content_h=520, refresh=f"{p.refresh_effect} = yes")
    for k, v in (("OVERVIEW", "Overview"), ("BUDGET", "Budget"), ("SECTORS", "Sectors"), ("POLICY", "Policy")):
        loc(f"ECO_TAB_{k}", v)

    # ------------------------------------------------------------------ overview
    with tabs.section("overview"):
        b.text("ECO_ov_h", 16, 0, "ECO_OV_H", 460, 22, "hoi_18mbs")
        loc("ECO_OV_H", "§YOutput and debt§!, last 24 months")
        LineChart(p, b, "ECO_gdp_chart", 16, 28, 460, 170, points=24, area=True, series=[
            {"array": "ECO_gdp_hist", "source": "ECO_gdp", "label": "GDP (bn)", "colour": "good"},
            {"array": "ECO_debt_hist", "source": "ECO_debt", "label": "Public debt (bn)", "colour": "bad"},
        ])
        legend(b, p, "ECO_gdp_key", 490, 34, [("GDP (bn)", "good"), ("Public debt (bn)", "bad")], w=200)
        RingGauge(p, b, "ECO_growth", 500, 92, 84, "ECO_growth", lo=-5, hi=10, colour="good", label="Growth (% a year)", value_fmt="1")
        RingGauge(p, b, "ECO_infl", 604, 92, 84, "ECO_inflation", lo=0, hi=20, colour="bad", label="Inflation (%)", value_fmt="1")
        b.text("ECO_ov_free_h", 16, 236, "ECO_OV_FREE_H", 460, 20)
        loc("ECO_OV_FREE_H", "§YEconomic freedom§! index: §Y[?ECO_freedom|0]§!")
        ScaleMarker(p, b, "ECO_freedom", 16, 258, 460, "ECO_freedom", 0, 100, stops=("blue", "mid", "gold"),
                    left="Command economy", right="Free market")
        BarChart(p, b, "ECO_rates", 16, 330, 680, 96, horizontal=True, max=25, label_w=160, value_fmt="1", bars=[
            {"var": "ECO_unemployment", "label": "Unemployment %", "colour": "red"},
            {"var": "ECO_interest", "label": "Interest rate %", "colour": "blue"},
            {"var": "ECO_inflation", "label": "Inflation %", "colour": "gold"},
        ])

    # ------------------------------------------------------------------ budget
    with tabs.section("budget"):
        b.text("ECO_bu_rev_h", 16, 0, "ECO_BU_REV_H", 330, 22, "hoi_18mbs")
        loc("ECO_BU_REV_H", "§YRevenue§!: §G[?ECO_rev_chart_total|0]§! bn")
        PieChart(p, b, "ECO_rev_chart", 16, 30, 150, [
            {"var": "ECO_rev_income", "label": "Income tax", "colour": "blue"},
            {"var": "ECO_rev_business", "label": "Business tax", "colour": "gold"},
            {"var": "ECO_rev_excise", "label": "Excise", "colour": "green"},
            {"var": "ECO_rev_tariffs", "label": "Tariffs", "colour": "#8f6bb8"},
            {"var": "ECO_rev_other", "label": "Other", "colour": "outline"},
        ], legend_w=160)
        b.text("ECO_bu_exp_h", 360, 0, "ECO_BU_EXP_H", 330, 22, "hoi_18mbs")
        loc("ECO_BU_EXP_H", "§YSpending§!: §R[?ECO_exp_chart_total|0]§! bn")
        PieChart(p, b, "ECO_exp_chart", 360, 30, 150, [
            {"var": "ECO_exp_military", "label": "Military", "colour": "red"},
            {"var": "ECO_exp_welfare", "label": "Welfare", "colour": "green"},
            {"var": "ECO_exp_infra", "label": "Infrastructure", "colour": "gold"},
            {"var": "ECO_exp_interest", "label": "Debt interest", "colour": "outline"},
        ], inner=0.55, mode="shader", center="ECO_EXP_CENTER", legend_w=160)
        loc("ECO_EXP_CENTER", "§R[?ECO_exp_chart_total|0]§!")
        b.text("ECO_bu_debt_h", 16, 210, "ECO_BU_DEBT_H", 600, 22, "hoi_18mbs")
        loc("ECO_BU_DEBT_H", "§YWho holds the debt§!")
        StackedBar(p, b, "ECO_holders", 16, 238, 680, 22, [
            {"var": "ECO_debt_central", "label": "Central bank", "colour": "blue"},
            {"var": "ECO_debt_banks", "label": "Domestic banks", "colour": "gold"},
            {"var": "ECO_debt_foreign", "label": "Foreign creditors", "colour": "red"},
        ])

    # ------------------------------------------------------------------ sectors
    with tabs.section("sectors"):
        b.text("ECO_se_h", 16, 0, "ECO_SE_H", 600, 22, "hoi_18mbs")
        loc("ECO_SE_H", "§YOutput by sector§! (bn a year)")
        BarChart(p, b, "ECO_sectors", 16, 30, 400, 170, [{"var": f"ECO_out_{k}", "label": nm, "colour": col} for k, nm, col in SECTORS])
        b.text("ECO_se_hm_h", 16, 254, "ECO_SE_HM_H", 600, 22, "hoi_18mbs")
        loc("ECO_SE_HM_H", "§YDevelopment by region§! (0 to 100)")
        Heatmap(p, b, "ECO_regions", 16, 280, REGIONS, [(k, nm) for k, nm, _ in SECTORS], lambda r, s: f"ECO_dev_{r}_{s}",
                cell=(70, 24), stops=("bad", "mid", "good"))

    # ------------------------------------------------------------------ policy
    with tabs.section("policy"):
        b.text("ECO_po_h", 16, 0, "ECO_PO_H", 300, 22, "hoi_18mbs")
        loc("ECO_PO_H", "§LWhere the parties stand§!")
        Scatter(p, b, "ECO_compass", 16, 30, 260, 260, [
            {"x": "ECO_party_a_econ", "y": "ECO_party_a_auth", "label": "Ruling party", "colour": "gold", "shape": "diamond"},
            {"x": "ECO_party_b_econ", "y": "ECO_party_b_auth", "label": "Opposition", "colour": "blue"},
            {"x": "ECO_party_c_econ", "y": "ECO_party_c_auth", "label": "Radicals", "colour": "red", "shape": "triangle"},
        ], quadrants=[(4, 4, "Authoritarian left"), (134, 4, "Authoritarian right"), (4, 238, "Libertarian left"), (134, 238, "Libertarian right")])
        b.text("ECO_po_tax_h", 310, 30, "ECO_PO_TAX_H", 380, 22, "hoi_18mbs")
        loc("ECO_PO_TAX_H", "§YFiscal policy§!")
        stepper(b, p, "ECO_tax", 310, 60, "ECO_tax_rate", step=1, lo=5, hi=60, label="Income tax %", label_w=150,
                cost="add_political_power = -5")
        switch(b, p, "ECO_pc", 310, 96, "ECO_price_controls", label="Price controls",
               tooltip="ECO_PC_TT")
        loc("ECO_PC_TT", bullets(c.econ("Price controls"), f"Inflation {c.signed(-2, False)} a year", f"Shortages: {c.bad('likely')}"))
        b.text("ECO_po_note", 310, 140, "ECO_PO_NOTE", 380, 120)
        loc("ECO_PO_NOTE", "Each change to the tax rate costs §Y5§! £pol_power.\\nHigher rates raise §Yrevenue§! but slow §Ygrowth§!.")
    return p
