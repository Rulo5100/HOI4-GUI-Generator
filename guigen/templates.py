"""Starter specs for `guigen new`. $P$ is replaced by the prefix (usually the country tag)."""

BOARD = """# A decision-category board for $P$. Add `scripted_gui = $P$_board` to one of your decision categories.
#   guigen preview $FILE$ --mod <mod> --mock $MOCK$
project:
  prefix: $P$
  theme: parchment

sprites:
  - {type: bar, name: bar, w: 150, h: 14, colour: gold}

frames:
  - {var: $P$_f_progress, source: $P$_progress}

boards:
  - name: $P$_board
    context: decision_category
    elements:
      - header: {emblem: GFX_goal_generic_trade, help: $P$_HELP_TT, title: $P$_TITLE, subs: [$P$_SUB]}
      - row:
          height: 26
          items:
            - text: {name: $P$_progress_l, text: $P$_PROGRESS_L, w: 140, tooltip: $P$_PROGRESS_TT}
            - bar: {name: $P$_progress, x: 160, dy: 3, sprite: GFX_$P$_bar, frame_var: $P$_f_progress, tooltip: $P$_PROGRESS_TT}
            - text: {name: $P$_progress_v, text: $P$_PROGRESS_V, x: 316, w: 60}
      - chart:
          type: hbar
          name: $P$_needs
          w: 480
          h: 72
          max: 100
          bars:
            - {var: $P$_food, label: Food, colour: green}
            - {var: $P$_fuel, label: Fuel, colour: gold}
            - {var: $P$_arms, label: Arms, colour: red}
      - button:
          name: $P$_act
          sprite: GFX_button_94x31
          text: $P$_ACT
          tooltip: $P$_ACT_TT
          enabled: "has_political_power > 24.99"
          click: "add_political_power = -25 add_to_variable = { $P$_progress = 10 } $P$_guigen_refresh = yes"

loc:
  $P$_TITLE: "§YA new board§!"
  $P$_SUB: "Progress so far: §Y[?$P$_progress|0]%§!"
  $P$_HELP_TT: "§YHow it works§!\\\\n£white_dot Click §YPush on§! to make progress\\\\n£white_dot Each click costs §Y25§! £pol_power"
  $P$_PROGRESS_L: "Progress"
  $P$_PROGRESS_V: "§Y[?$P$_progress|0]%§!"
  $P$_PROGRESS_TT: "§YProgress§!: §Y[?$P$_progress|0]%§!"
  $P$_ACT: "Push on"
  $P$_ACT_TT: "§YPush on§!\\\\n£white_dot Cost: §Y25§! £pol_power\\\\n£white_dot Progress: §G+10%§!"
"""

BOARD_MOCK = """vars: {$P$_progress: 40, $P$_food: 72, $P$_fuel: 35, $P$_arms: 58, political_power: 60}
"""

WINDOW = """# An interactive window for $P$: a button in the top bar opens it; it is moveable and has tabs.
# It shows every chart type guigen has, so delete what you do not need.
#   guigen preview $FILE$ --mod <mod> --mock $MOCK$ --set $P$_tab=1
# In your mod: call $P$_guigen_refresh = yes after the data changes, $P$_trend_record = yes monthly.
project:
  prefix: $P$
  theme: steel

boards:
  - name: $P$_window
    window:
      title: $P$_TITLE
      w: 720
      h: 560
      opener: top_bar
      opener_xy: [620, 6]
      opener_tooltip: $P$_OPEN_TT
    elements:
      - tabs:
          var: $P$_tab
          height: 470
          refresh: $P$_guigen_refresh = yes
          tabs:
            - key: trends
              label: $P$_TAB_TRENDS
              elements:
                - text: {name: $P$_trend_h, text: $P$_TREND_H, w: 460, h: 22, font: hoi_18mbs}
                - chart:
                    type: area
                    name: $P$_trend
                    w: 460
                    h: 160
                    points: 24
                    series:
                      - {array: $P$_output_hist, source: $P$_output, label: Output, colour: good}
                      - {array: $P$_costs_hist, source: $P$_costs, label: Costs, colour: bad}
                - legend: {name: $P$_trend_key, x: 490, y: 34, w: 200, items: [[Output, good], [Costs, bad]]}
                - chart: {type: ring, name: $P$_morale, x: 520, y: 100, size: 84, var: $P$_morale, label: Morale}
                - chart: {type: scale, name: $P$_lean, w: 460, var: $P$_lean, left: Hawks, right: Doves, stops: [red, mid, blue]}
                - chart:
                    type: hbar
                    name: $P$_stocks
                    w: 680
                    h: 90
                    max: 100
                    bars:
                      - {var: $P$_food, label: Food, colour: green}
                      - {var: $P$_fuel, label: Fuel, colour: gold}
                      - {var: $P$_arms, label: Arms, colour: red}
            - key: shares
              label: $P$_TAB_SHARES
              elements:
                - row:
                    items:
                      - chart:
                          type: pie
                          name: $P$_income
                          size: 150
                          legend_w: 150
                          slices:
                            - {var: $P$_inc_tax, label: Taxes, colour: blue}
                            - {var: $P$_inc_trade, label: Trade, colour: gold}
                            - {var: $P$_inc_aid, label: Aid, colour: green}
                      - chart:
                          type: donut
                          name: $P$_spend
                          x: 360
                          size: 150
                          legend_w: 150
                          slices:
                            - {var: $P$_sp_army, label: Army, colour: red}
                            - {var: $P$_sp_people, label: People, colour: green}
                            - {var: $P$_sp_other, label: Other, colour: outline}
                - space: 20
                - chart:
                    type: stacked
                    name: $P$_seats
                    w: 680
                    h: 22
                    parts:
                      - {var: $P$_seats_a, label: Government, colour: gold}
                      - {var: $P$_seats_b, label: Opposition, colour: blue}
                      - {var: $P$_seats_c, label: Independents, colour: outline}
            - key: compare
              label: $P$_TAB_COMPARE
              elements:
                - chart:
                    type: bar
                    name: $P$_cmp
                    w: 400
                    h: 150
                    bars:
                      - {var: $P$_cmp_a, label: North, colour: blue}
                      - {var: $P$_cmp_b, label: South, colour: gold}
                      - {var: $P$_cmp_c, label: East, colour: green}
                      - {var: $P$_cmp_d, label: West, colour: red}
                - chart:
                    type: heatmap
                    name: $P$_grid
                    rows: [[n, North], [s, South]]
                    cols: [[a, Farms], [b, Mines], [c, Mills]]
                    var: "$P$_grid_{row}_{col}"
                    cell: [70, 24]
            - key: controls
              label: $P$_TAB_CONTROLS
              elements:
                - chart:
                    type: scatter
                    name: $P$_map
                    w: 240
                    h: 240
                    points:
                      - {x: $P$_us_x, y: $P$_us_y, label: Us, colour: gold, shape: diamond}
                      - {x: $P$_them_x, y: $P$_them_y, label: Them, colour: red}
                - stepper: {name: $P$_budget, x: 300, y: 0, var: $P$_budget, step: 5, lo: 0, hi: 100, label: "Budget %", label_w: 120}
                - switch: {name: $P$_mobilise, x: 300, y: 36, var: $P$_mobilised, label: Mobilise}

loc:
  $P$_TITLE: "The Situation Room"
  $P$_OPEN_TT: "§YThe Situation Room§!\\\\n£white_dot Open or close the window"
  $P$_TAB_TRENDS: "Trends"
  $P$_TAB_SHARES: "Shares"
  $P$_TAB_COMPARE: "Compare"
  $P$_TAB_CONTROLS: "Controls"
  $P$_TREND_H: "§YOutput and costs§!, last 24 months"
"""

WINDOW_MOCK = """flags: [$P$_window_open]
default_var: 0
vars:
  $P$_tab: 0
  $P$_morale: 64
  $P$_lean: 35
  $P$_food: 72
  $P$_fuel: 35
  $P$_arms: 58
  $P$_inc_tax: 50
  $P$_inc_trade: 30
  $P$_inc_aid: 12
  $P$_sp_army: 40
  $P$_sp_people: 35
  $P$_sp_other: 15
  $P$_seats_a: 210
  $P$_seats_b: 160
  $P$_seats_c: 30
  $P$_cmp_a: 80
  $P$_cmp_b: 45
  $P$_cmp_c: 120
  $P$_cmp_d: 64
  $P$_grid_n_a: 20
  $P$_grid_n_b: 75
  $P$_grid_n_c: 50
  $P$_grid_s_a: 90
  $P$_grid_s_b: 10
  $P$_grid_s_c: 35
  $P$_us_x: 30
  $P$_us_y: 40
  $P$_them_x: -50
  $P$_them_y: 60
  $P$_budget: 45
  $P$_mobilised: 0
  political_power: 100
arrays:
  $P$_output_hist: [50, 52, 51, 55, 57, 56, 60, 62, 61, 64, 66, 65, 68, 70, 69, 71, 74, 73, 76, 78, 77, 80, 81, 83]
  $P$_costs_hist: [40, 41, 43, 42, 44, 46, 45, 47, 49, 48, 50, 51, 53, 52, 54, 55, 57, 56, 58, 60, 59, 61, 62, 64]
"""

TEMPLATES = {"board": (BOARD, BOARD_MOCK), "window": (WINDOW, WINDOW_MOCK)}


def render(template, prefix, file_name, mock_name):
    spec, mock = TEMPLATES[template]
    fill = lambda s: s.replace("$P$", prefix).replace("$FILE$", file_name).replace("$MOCK$", mock_name)
    return fill(spec), fill(mock)
