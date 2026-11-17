Goal: build a general, reusable Python generator for Hearts of Iron IV scripted GUIs, based on the Manchukuo (MAN) one-off generator built earlier. Then expand it with more features. Work in the mod repo `C:\Users\Roberts (ME)\Documents\Paradox Interactive\Hearts of Iron IV\mod\Secret Rearmament`, on git branch Japan-Manchu; the remote is origin, ETAPD/BFFU-DEV.

## Seed code to learn from (read first)
Copies of the original scripts are in `C:\Users\Roberts (ME)\Documents\Paradox Interactive\Hearts of Iron IV\mod\gui_generator_seed\`. The GUI parts:

- **`man_systems2.py`, from the "bars (sprites)" section to the end of the scripted GUI section:**
  - `bar()` draws an 11-frame progress bar PNG with Pillow; `pips()` draws an 11-frame row of soldier figures.
  - Builds the `.gfx` spriteTypes with noOfFrames.
  - Helpers write the `.gui` elements: `T()` instantTextBoxType, `I()` iconType, `B()` buttonType, `W()` containerWindowType.
  - Layout runs on a running `y` value; window height = final `y`.
  - Collects `props` / `trig` / `eff` per window and emits `common/scripted_guis/*.txt` with `context_type = decision_category`, a `properties` block (`elem = { frame = VAR }`), `triggers` (`elem_click_enabled = {...}`) and `effects` (`elem_click = {...}`).
  - `DT()` writes scripted loc `defined_text` blocks.
- **`man_polgui.py`:** a semicircular dial (21 frames), a vertical gauge column (11 frames) with threshold ticks, broker cards with an emblem ring.
- **`man_map.py`:** cuts one sprite per state out of the mod's `map/provinces.bmp` + definitions, with frames coloured by tier. It is used as a clickable province map on the board.
- **`man_sites.py`:** per-province action buttons with click triggers and effects, e.g. Police Garrison capped by `MAN_gar_n < MAN_gar_cap`.
- **`man_build.py`:** runs all modules, writes the files, then validates that every spriteType, texturefile, loc key and scripted loc reference exists.
- **`man_common.py`:** shared paths (`P()`), `wr()` writer, loc collection.

The live generated output is in the mod:
- `interface/MAN_systems.gui` and `interface/MAN_systems.gfx`
- `common/scripted_guis/MAN_systems_guis.txt`
- `common/scripted_localisation/MAN_systems_loc.txt`
- `gfx/interface/MAN/*.png`
- `localisation/english/MAN_systems_l_english.yml`

## What to build
1. **A country-agnostic package**, e.g. `tools/guigen/` in the repo.
   - Declarative widgets: text, icon, button, frame-bar, pips, dial, gauge, state map, list rows, tooltip, emblem/card.
   - A layout engine (vertical stack, rows, columns, auto height).
   - Context types: decision_category plus others the engine supports, such as the country/top-bar window and selected_state_view; check what HOI4 scripted_gui supports.
   - Sprite-sheet generation with Pillow.
   - Variable-to-frame wiring that writes the frame scripted_effect, e.g. clamp then divide into frames.
   - Scripted GUI file output, loc and scripted-loc output.
   - A validator.
2. Input should be a simple Python or YAML spec per board, so a new country board is a short file.
3. **Port the three MAN boards** (Plan, Bureaucracy, Public Security) onto it as the reference spec, and prove byte-identical or functionally identical output.
   - Do NOT overwrite the live MAN files until the port matches. Diff first.
4. **Then expand:** suggest and implement useful extras, e.g.
   - colour themes per country
   - reusable tab/toggle sections (scripted GUI with a toggle variable)
   - a preview renderer that mocks the board to a PNG so layouts can be checked without launching the game
   - a README with usage

## Constraints (important)
- **Line endings:** preserve CRLF on files that are CRLF in git HEAD. Write in binary mode, or match HEAD; Python text-mode writes flip line endings.
- **Loc text:** no em-dashes and no `--` in loc or tooltip text. Write `\n` in loc as a literal backslash-n. Don't use bash heredocs for content with backslashes; write .py files or use the Edit tool.
- **Tooltip colours:** §Y economy, §L politics, §O security, §C places; values §G good / §R bad.
- **Commits:** commit only when asked. Commit as git user Rulo5100, with no Claude co-author trailer.
- **Testing:** nothing can be tested in game from here. Validate statically and with the preview renderer.
