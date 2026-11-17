"""Command line.

    python -m guigen build    SPEC --mod MOD           write into the mod
    python -m guigen diff     SPEC --mod MOD           build into a temp folder and compare with the mod
    python -m guigen validate SPEC --mod MOD           static checks (sprites, loc, scripted loc, wiring)
    python -m guigen preview  SPEC --mod MOD [--mock mock.yaml] [--out DIR] [--debug]

SPEC is a .py file with `build(fs) -> Project`, or a .yaml board spec.
`build` refuses to overwrite files that differ from the generated ones unless --force is given, so
run `diff` first.
"""
import argparse
import difflib
import importlib.util
import os
import shutil
import sys
import tempfile

from .modfs import ModFS


def load_spec(path):
    path = os.path.abspath(path)
    if path.endswith((".yaml", ".yml")):
        from .yamlspec import load_yaml
        return lambda fs: load_yaml(fs, path)
    spec = importlib.util.spec_from_file_location("guigen_spec_" + os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise SystemExit(f"{path}: a spec must define build(fs) -> Project")
    return mod.build


# ---------------------------------------------------------------------- diff
def _read(path):
    with open(path, "rb") as f:
        return f.read()


def _img_compare(a_path, b_path):
    from PIL import Image, ImageChops
    a, b = Image.open(a_path).convert("RGBA"), Image.open(b_path).convert("RGBA")
    if a.size != b.size:
        return f"size {a.size} vs {b.size}"
    if a.tobytes() == b.tobytes():
        return None
    # getbbox() on an RGBA image only looks at alpha, so take the bbox of each band separately
    d = ImageChops.difference(a, b)
    bands = d.split()
    boxes = [bb for bb in (band.getbbox() for band in bands) if bb]
    box = (min(x[0] for x in boxes), min(x[1] for x in boxes), max(x[2] for x in boxes), max(x[3] for x in boxes))
    m = bands[0]
    for band in bands[1:]:
        m = ImageChops.lighter(m, band)          # per pixel: the largest channel difference
    n = sum(m.histogram()[1:])
    return f"{n} pixels differ in {box}"


def compare(fs, p, show=40):
    """Compare a staged build with the live mod. Returns (report lines, ok)."""
    from .loc import parse_yml
    from .pdxscript import find_block
    lines, ok = [], True
    for rel, kind in fs.written:
        new, live = fs.out_path(rel), fs.path(rel)
        if not os.path.exists(live):
            lines.append(f"NEW        {rel}")
            ok = False
            continue
        nb, lb = _read(new), _read(live)
        if nb == lb:
            lines.append(f"identical  {rel}")
            continue
        if kind == "image":
            r = _img_compare(new, live)
            if r is None:
                lines.append(f"pixels ok  {rel}  (PNG bytes differ: encoder/zlib version)")
            else:
                lines.append(f"DIFFERS    {rel}  {r}")
                ok = False
            continue
        nt, lt = nb.decode("utf-8-sig"), lb.decode("utf-8-sig")
        if nt.replace("\r\n", "\n") == lt.replace("\r\n", "\n"):
            lines.append(f"EOL only   {rel}  (same text, different line endings)")
            ok = False
            continue
        if rel == p.files.get("loc") and p.loc_mode == "merge":
            lines.append(f"DIFFERS    {rel}  (loc entries, see below)")
        else:
            lines.append(f"DIFFERS    {rel}")
            d = list(difflib.unified_diff(lt.replace("\r\n", "\n").split("\n"), nt.replace("\r\n", "\n").split("\n"), "live", "generated", lineterm="", n=1))
            lines += ["    " + l for l in d[:show]] + (["    ..."] if len(d) > show else [])
        ok = False
    # loc entries (also when another build owns the yml)
    if p.locs.entries and fs.exists(p.files["loc"]):
        live = parse_yml(fs.read_text(p.files["loc"])[0])
        bad = [(k, v, live.get(k)) for k, v in p.locs.items() if live.get(k) != v]
        lines.append(f"loc        {len(p.locs.entries) - len(bad)}/{len(p.locs.entries)} entries match {p.files['loc']}")
        for k, v, lv in bad[:show]:
            ok = False
            lines.append(f"    {k}\n      live: {lv!r}\n      gen : {v!r}")
    for k, a, b in p.locs.conflicts:
        lines.append(f"loc dup    {k}: kept {a!r}, ignored {b!r}")
    for rel, name, text in p.embedded:
        if not fs.exists(rel):
            lines.append(f"MISSING    {rel} (embedded {name})")
            ok = False
            continue
        blk = find_block(fs.read_text(rel)[0], name)
        if blk == text:
            lines.append(f"identical  {rel} :: {name}")
        else:
            ok = False
            lines.append(f"DIFFERS    {rel} :: {name}")
            d = list(difflib.unified_diff((blk or "").split("\n"), text.split("\n"), "live", "generated", lineterm="", n=1))
            lines += ["    " + l for l in d[:show]]
    return lines, ok


# ---------------------------------------------------------------------- commands
def cmd_diff(a):
    stage = tempfile.mkdtemp(prefix="guigen_")
    try:
        fs = ModFS(a.mod, a.vanilla, stage=stage, eol=a.eol)
        p = load_spec(a.spec)(fs)
        p.write()
        lines, ok = compare(fs, p)
        print("\n".join(lines))
        print("\nRESULT:", "output matches the live mod" if ok else "differences found")
        return 0 if ok else 1
    finally:
        if not a.keep:
            shutil.rmtree(stage, ignore_errors=True)
        else:
            print("staged build kept in", stage)


def cmd_build(a):
    if not a.force:
        stage = tempfile.mkdtemp(prefix="guigen_")
        try:
            fs = ModFS(a.mod, a.vanilla, stage=stage, eol=a.eol)
            p = load_spec(a.spec)(fs)
            p.write()
            changed = [rel for rel, _ in fs.written if os.path.exists(fs.path(rel)) and _read(fs.out_path(rel)) != _read(fs.path(rel))]
        finally:
            shutil.rmtree(stage, ignore_errors=True)
        if changed and not a.yes:
            print("These existing files would change:\n  " + "\n  ".join(changed))
            print("Run `diff` to review, then `build --yes` (or --force) to write.")
            return 2
    fs = ModFS(a.mod, a.vanilla, eol=a.eol)
    p = load_spec(a.spec)(fs)
    p.write()
    print(f"wrote {len(fs.written)} files")
    return cmd_validate(a, p=p, fs=fs)


def cmd_validate(a, p=None, fs=None):
    from .validate import validate
    if p is None:
        stage = tempfile.mkdtemp(prefix="guigen_")
        fs = ModFS(a.mod, a.vanilla, stage=stage, eol=a.eol)
        p = load_spec(a.spec)(fs)
        p.write()
    errors, warnings = validate(p, fs)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:  ", e)
    print(f"validate: {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


def cmd_preview(a):
    from .preview import preview_project
    stage = tempfile.mkdtemp(prefix="guigen_")
    try:
        fs = ModFS(a.mod, a.vanilla, stage=stage, eol=a.eol)
        p = load_spec(a.spec)(fs)
        p.write()
        out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.spec)), "preview")
        files, notes = preview_project(p, fs, out, mock=a.mock, debug=a.debug, width=a.width, boards=a.board,
                                       overrides=a.set, suffix=a.suffix)
        for n in notes:
            print("note:", n)
        for f in files:
            print("preview:", f)
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


CONFIG = os.path.join(os.path.expanduser("~"), ".guigen.json")


def load_config():
    import json
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(**kw):
    import json
    cfg = load_config()
    cfg.update({k: v for k, v in kw.items() if v is not None})
    try:
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass


def cmd_new(a):
    from .templates import render
    os.makedirs(a.folder, exist_ok=True)
    spec = os.path.join(a.folder, f"{a.prefix}_{a.template}.yaml")
    mock = os.path.join(a.folder, f"{a.prefix}_{a.template}_mock.yaml")
    for path in (spec, mock):
        if os.path.exists(path) and not a.force:
            print(f"{path} exists (use --force to overwrite)")
            return 2
    s, m = render(a.template, a.prefix, spec.replace("\\", "/"), mock.replace("\\", "/"))
    for path, text in ((spec, s), (mock, m)):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote", path)
    print(f"next: guigen preview {spec} --mock {mock}" + ("" if _default_mod() else " --mod <mod folder>"))
    return 0


def cmd_doctor(a):
    from .modfs import find_vanilla
    ok = True
    print("python      ", sys.version.split()[0])
    for mod in ("PIL", "numpy", "yaml", "tkinter"):
        try:
            m = __import__(mod)
            print(f"{mod:12s} ok {getattr(m, '__version__', '')}")
        except ImportError:
            print(f"{mod:12s} MISSING" + ("  (pip install pillow numpy pyyaml)" if mod != "tkinter" else "  (needed only by guigen app)"))
            ok = ok and mod == "tkinter"
    v = find_vanilla(getattr(a, "vanilla", None))
    print("HOI4        ", v or "not found (set HOI4_PATH or pass --vanilla)")
    if v:
        print("game fonts  ", "ok" if os.path.exists(os.path.join(v, "gfx", "fonts", "hoi_16mbs.fnt")) else "missing")
    print("default mod ", _default_mod() or "none (pass --mod, set GUIGEN_MOD, or pick one in guigen app)")
    return 0 if ok else 1


def cmd_themes(a):
    from .theme import THEMES
    for name, t in THEMES.items():
        print(f"{name:10s} accent {t.accent}  bars: {', '.join(t.bars)}")
    return 0


def cmd_app(a):
    from .app import main as app_main
    return app_main()


def _default_mod():
    return os.environ.get("GUIGEN_MOD") or load_config().get("mod")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="guigen", description="HOI4 scripted GUI generator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new", help="write a starter YAML spec and mock")
    s.add_argument("prefix", help="prefix for every name, usually the country tag")
    s.add_argument("--template", default="window", choices=["window", "board"])
    s.add_argument("--folder", default=".")
    s.add_argument("--force", action="store_true")
    sub.add_parser("doctor", help="check Python packages, the HOI4 install and fonts")
    sub.add_parser("themes", help="list the colour themes")
    sub.add_parser("app", help="open the desktop app")
    for name in ("build", "diff", "validate", "preview"):
        s = sub.add_parser(name)
        s.add_argument("spec")
        s.add_argument("--mod", default=_default_mod(), required=_default_mod() is None,
                       help="mod root folder (default: $GUIGEN_MOD or the last one used in guigen app)")
        s.add_argument("--vanilla", help="HOI4 install folder (auto-detected)")
        s.add_argument("--eol", default="auto", choices=["auto", "crlf", "lf"])
        if name == "build":
            s.add_argument("--yes", action="store_true", help="write even if existing files change")
            s.add_argument("--force", action="store_true", help="skip the pre-write comparison")
        if name == "diff":
            s.add_argument("--keep", action="store_true", help="keep the staged build folder")
        if name == "preview":
            s.add_argument("--mock", help="YAML with variables / flags / scripted loc picks")
            s.add_argument("--out", help="output folder (default: preview/ next to the spec)")
            s.add_argument("--debug", action="store_true", help="draw element boxes and names")
            s.add_argument("--width", type=int, default=520, help="width used for 100%% windows")
            s.add_argument("--board", action="append", help="only these boards")
            s.add_argument("--set", action="append", metavar="VAR=VALUE",
                           help="override a mock variable, a flag (flag:NAME) or an array (VAR=[1,2,3]); repeatable")
            s.add_argument("--suffix", default="", help="added to the output file names (e.g. _budget)")
    a = ap.parse_args(argv)
    return {"build": cmd_build, "diff": cmd_diff, "validate": cmd_validate, "preview": cmd_preview, "new": cmd_new,
            "doctor": cmd_doctor, "themes": cmd_themes, "app": cmd_app}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
