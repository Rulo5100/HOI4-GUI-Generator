"""guigen app: a desktop window to edit a spec and see the board update.

    guigen app            (or: python -m guigen app, or the guigen-app shortcut)

* Mod / Spec / Mock pickers (remembered in ~/.guigen.json).
* Left: the spec (YAML or Python). Ctrl+S saves and re-renders. "Watch" re-renders when the file
  changes on disk (edit in your own editor if you prefer).
* Right: the preview, drawn with the game's fonts and the mock state. Click a button in the preview
  to run its effect on the mock (switch tabs, close the window, step values, flip switches); click
  anything else to see its name and tooltip. Reset mock reloads the mock file.
* Validate / Diff / Build run the same checks as the command line; Build asks before writing.
"""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import threading
import time
import traceback

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:          # pragma: no cover
    tk = None

from PIL import Image

from .modfs import ModFS


class App:
    def __init__(self, root):
        from .cli import load_config
        self.root = root
        root.title("guigen")
        root.geometry("1500x920")
        cfg = load_config()
        self.mod = tk.StringVar(value=cfg.get("mod", ""))
        self.spec = tk.StringVar(value=cfg.get("spec", ""))
        self.mock = tk.StringVar(value=cfg.get("mock", ""))
        self.board = tk.StringVar(value=cfg.get("board", ""))
        self.sets = tk.StringVar(value="")
        self.zoom = tk.StringVar(value=cfg.get("zoom", "100%"))
        self.debug = tk.BooleanVar(value=False)
        self.tooltips = tk.BooleanVar(value=False)
        self.watch = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="ready")
        self.project = self.fs = self.renderer = None
        self.stage = None
        self.img = None
        self._mtime = 0
        self._busy = False
        self._build_ui()
        if self.spec.get() and os.path.exists(self.spec.get()):
            self.load_editor()
            self.render(reload=True)
        root.after(1000, self._poll)

    # ------------------------------------------------------------------ ui
    def _build_ui(self):
        r = self.root
        top = ttk.Frame(r, padding=4)
        top.pack(fill="x")
        for i, (label, var, cmd) in enumerate((("Mod", self.mod, self.pick_mod), ("Spec", self.spec, self.pick_spec),
                                                ("Mock", self.mock, self.pick_mock))):
            ttk.Label(top, text=label).grid(row=0, column=i * 3, sticky="e", padx=(8, 2))
            ttk.Entry(top, textvariable=var, width=46 if label != "Mod" else 40).grid(row=0, column=i * 3 + 1, sticky="ew")
            ttk.Button(top, text="...", width=3, command=cmd).grid(row=0, column=i * 3 + 2)
        bar = ttk.Frame(r, padding=(4, 0, 4, 4))
        bar.pack(fill="x")
        ttk.Label(bar, text="Board").pack(side="left", padx=(8, 2))
        self.board_box = ttk.Combobox(bar, textvariable=self.board, width=28, state="readonly")
        self.board_box.pack(side="left")
        self.board_box.bind("<<ComboboxSelected>>", lambda e: self.render())
        ttk.Label(bar, text="Set").pack(side="left", padx=(12, 2))
        e = ttk.Entry(bar, textvariable=self.sets, width=34)
        e.pack(side="left")
        e.bind("<Return>", lambda ev: self.render(reset_mock=True))
        ttk.Label(bar, text="Zoom").pack(side="left", padx=(12, 2))
        z = ttk.Combobox(bar, textvariable=self.zoom, values=["50%", "75%", "100%", "150%", "200%"], width=6, state="readonly")
        z.pack(side="left")
        z.bind("<<ComboboxSelected>>", lambda e: self.show())
        for text, var in (("Debug boxes", self.debug), ("Tooltips", self.tooltips), ("Watch file", self.watch)):
            ttk.Checkbutton(bar, text=text, variable=var, command=self.render if var is not self.watch else None).pack(side="left", padx=6)
        acts = ttk.Frame(r, padding=(4, 0, 4, 4))
        acts.pack(fill="x")
        for text, cmd in (("Render (F5)", lambda: self.render(reload=True)), ("Save (Ctrl+S)", self.save),
                          ("Reset mock", lambda: self.render(reset_mock=True)), ("Validate", self.validate), ("Diff", self.diff),
                          ("Build...", self.build), ("New...", self.new), ("Save PNG", self.save_png)):
            ttk.Button(acts, text=text, command=cmd).pack(side="left", padx=(8 if text.startswith("Render") else 2, 2))
        ttk.Label(acts, text="Click a button in the preview to run its effect on the mock.", foreground="#777").pack(side="left", padx=12)

        pan = ttk.PanedWindow(r, orient="horizontal")
        pan.pack(fill="both", expand=True)
        left = ttk.Frame(pan)
        self.editor = tk.Text(left, wrap="none", undo=True, font=("Consolas", 10), width=70)
        ys = ttk.Scrollbar(left, orient="vertical", command=self.editor.yview)
        xs = ttk.Scrollbar(left, orient="horizontal", command=self.editor.xview)
        self.editor.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side="right", fill="y")
        xs.pack(side="bottom", fill="x")
        self.editor.pack(fill="both", expand=True)
        pan.add(left, weight=1)
        right = ttk.Frame(pan)
        self.canvas = tk.Canvas(right, background="#141414", highlightthickness=0)
        cy = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        cx = ttk.Scrollbar(right, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=cy.set, xscrollcommand=cx.set)
        cy.pack(side="right", fill="y")
        cx.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        pan.add(right, weight=2)

        self.log = tk.Text(r, height=9, font=("Consolas", 9), background="#1b1b1b", foreground="#d8d8d8")
        self.log.pack(fill="x")
        ttk.Label(r, textvariable=self.status, anchor="w", padding=(6, 2)).pack(fill="x")
        r.bind("<F5>", lambda e: self.render(reload=True))
        r.bind("<Control-s>", lambda e: self.save())

    # ------------------------------------------------------------------ helpers
    def say(self, text):
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")

    def remember(self):
        from .cli import save_config
        save_config(mod=self.mod.get(), spec=self.spec.get(), mock=self.mock.get(), board=self.board.get(), zoom=self.zoom.get())

    def pick_mod(self):
        d = filedialog.askdirectory(title="Mod folder", initialdir=self.mod.get() or None)
        if d:
            self.mod.set(d)
            self.render(reload=True)

    def pick_spec(self):
        f = filedialog.askopenfilename(title="Spec", filetypes=[("guigen spec", "*.yaml *.yml *.py"), ("all", "*.*")])
        if f:
            self.spec.set(f)
            self.load_editor()
            self.render(reload=True)

    def pick_mock(self):
        f = filedialog.askopenfilename(title="Mock state", filetypes=[("YAML", "*.yaml *.yml"), ("all", "*.*")])
        if f:
            self.mock.set(f)
            self.render(reset_mock=True)

    def load_editor(self):
        with open(self.spec.get(), encoding="utf-8") as f:
            text = f.read()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_reset()
        self._mtime = os.path.getmtime(self.spec.get())

    def save(self):
        if not self.spec.get():
            return
        with open(self.spec.get(), "w", encoding="utf-8", newline="\n") as f:
            f.write(self.editor.get("1.0", "end-1c"))
        self._mtime = os.path.getmtime(self.spec.get())
        self.status.set("saved")
        self.render(reload=True)

    def _poll(self):
        try:
            p = self.spec.get()
            if self.watch.get() and p and os.path.exists(p) and os.path.getmtime(p) > self._mtime + 0.01 and not self._busy:
                self.load_editor()
                self.render(reload=True)
        finally:
            self.root.after(1000, self._poll)

    def _need(self, mod=True):
        """Check the inputs. Rendering works without a mod (base-game sprites, fonts and loc still apply);
        validate / diff / build compare against the mod, so they need one."""
        if not self.spec.get() or not os.path.exists(self.spec.get()):
            self.say("Pick a spec (Spec ...) or create one (New ...).")
            return False
        if mod and (not self.mod.get() or not os.path.isdir(self.mod.get())):
            self.say("Pick the mod folder first (Mod ...).")
            return False
        return True

    def _mod_or_empty(self):
        m = self.mod.get()
        if m and os.path.isdir(m):
            return m
        if not getattr(self, "_empty_mod", None):
            self._empty_mod = tempfile.mkdtemp(prefix="guigen_nomod_")
            self.say("No mod folder picked: previewing without your mod's own sprites and loc (base-game ones still work). "
                     "Pick it with Mod ... to validate, diff and build.")
        return self._empty_mod

    # ------------------------------------------------------------------ build + render
    def _load(self, mod=None, spec=None):
        from .cli import load_spec
        mod, spec = mod or self.mod.get(), spec or self.spec.get()
        if self.stage:
            shutil.rmtree(self.stage, ignore_errors=True)
        self.stage = tempfile.mkdtemp(prefix="guigen_app_")
        self.fs = ModFS(mod, stage=self.stage)
        self.project = load_spec(spec)(self.fs)
        self.project.write()

    def _new_renderer(self, mock, sets, debug):
        from .mock import Mock
        from .preview import Renderer, apply_overrides
        m = Mock.load(mock or None)
        apply_overrides(m, sets.split())
        self.renderer = Renderer(self.project, self.fs, m, debug)

    def render(self, reload=False, reset_mock=False):
        if not self._need(mod=False) or self._busy:
            return
        self._busy = True
        self.status.set("rendering...")
        self.remember()
        # read every Tk variable here: the worker thread must not touch Tk
        mod, spec, mock, sets = self._mod_or_empty(), self.spec.get(), self.mock.get(), self.sets.get()
        board, debug, tips = self.board.get(), self.debug.get(), self.tooltips.get()

        def work():
            t0 = time.time()
            try:
                if reload or self.project is None:
                    self._load(mod, spec)
                    if self.renderer is not None and not reset_mock:      # keep the clicked-in state across edits
                        from .preview import Renderer
                        self.renderer = Renderer(self.project, self.fs, self.renderer.mock, debug)
                if reset_mock or self.renderer is None:
                    self._new_renderer(mock, sets, debug)
                self.renderer.debug = debug
                names = [b.name for b in self.project.boards]
                b = next((x for x in self.project.boards if x.name == board), None) or self.project.boards[0]
                img = self.renderer.render_tooltips(b) if tips else self.renderer.render_board(b, respect_visible=True)
                notes = [f"clipped: {c}" for c in self.renderer.clipped[-5:]]
                self.renderer.clipped.clear()
                self.root.after(0, lambda: self._done(img, names, b.name, notes, time.time() - t0))
            except Exception:
                err = traceback.format_exc()
                self.root.after(0, lambda: self._fail(err))
        threading.Thread(target=work, daemon=True).start()

    def _done(self, img, names, current, notes, dt):
        self._busy = False
        self.board_box["values"] = names
        self.board.set(current)
        self.img = img
        self.show()
        for n in notes:
            self.say(n)
        self.status.set(f"{current}: {img.width}x{img.height}, {dt:.1f}s")

    def _fail(self, err):
        self._busy = False
        self.say(err)
        self.status.set("error, see the log")

    def show(self):
        if self.img is None:
            return
        from PIL import ImageTk
        z = int(self.zoom.get().rstrip("%")) / 100
        im = self.img if z == 1 else self.img.resize((max(1, int(self.img.width * z)), max(1, int(self.img.height * z))), Image.LANCZOS)
        bg = Image.new("RGBA", im.size, (20, 20, 20, 255))
        bg.alpha_composite(im)
        self._tk = ImageTk.PhotoImage(bg)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self._tk)
        self.canvas.configure(scrollregion=(0, 0, im.width, im.height))

    def on_click(self, ev):
        if not self.renderer or self.tooltips.get() or self._busy:
            return
        z = int(self.zoom.get().rstrip("%")) / 100
        x, y = self.canvas.canvasx(ev.x) / z, self.canvas.canvasy(ev.y) / z
        b = next((x_ for x_ in self.project.boards if x_.name == self.board.get()), None)
        if b is None:
            return
        msg = self.renderer.click(b, x, y)
        if msg:
            self.status.set(msg)
            if msg.endswith("clicked"):
                unknown = getattr(self.renderer.mock, "unknown_effects", set())
                if unknown:
                    self.say("effects not simulated: " + ", ".join(sorted(unknown)))
                    unknown.clear()
                self.render()

    # ------------------------------------------------------------------ commands
    def _cli(self, fn, *args):
        """Run a cli command function with a namespace, capturing its output into the log."""
        import argparse
        ns = argparse.Namespace(spec=self.spec.get(), mod=self.mod.get(), vanilla=None, eol="auto", keep=False, yes=False, force=False)

        def work():
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    rc = fn(ns, *args)
            except Exception:
                buf.write(traceback.format_exc())
                rc = -1
            self.root.after(0, lambda: (self.say(buf.getvalue()), self.status.set(f"{fn.__name__}: exit {rc}")))
        threading.Thread(target=work, daemon=True).start()

    def validate(self):
        from .cli import cmd_validate
        if self._need():
            self.say("== validate")
            self._cli(cmd_validate)

    def diff(self):
        from .cli import cmd_diff
        if self._need():
            self.say("== diff")
            self._cli(cmd_diff)

    def build(self):
        from .cli import cmd_build, compare
        if not self._need():
            return
        self._load()
        lines, ok = compare(self.fs, self.project)
        changed = [l for l in lines if not l.startswith(("identical", "    ", "loc "))]
        text = "\n".join(changed[:30]) + ("\n..." if len(changed) > 30 else "")
        if ok:
            messagebox.showinfo("guigen", "The mod already matches the spec: nothing to write.")
            return
        if not messagebox.askyesno("Write into the mod?", f"These files will be written in\n{self.mod.get()}\n\n{text}\n\nContinue?"):
            return
        self.say("== build")
        import argparse
        ns = argparse.Namespace(spec=self.spec.get(), mod=self.mod.get(), vanilla=None, eol="auto", yes=True, force=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_build(ns)
        self.say(buf.getvalue())
        self.status.set(f"build: exit {rc}")

    def new(self):
        from .templates import TEMPLATES, render
        win = tk.Toplevel(self.root)
        win.title("New spec")
        pre, tpl = tk.StringVar(value="XYZ"), tk.StringVar(value="window")
        ttk.Label(win, text="Prefix (country tag)").grid(row=0, column=0, padx=6, pady=4, sticky="e")
        ttk.Entry(win, textvariable=pre, width=12).grid(row=0, column=1, padx=6, pady=4)
        ttk.Label(win, text="Template").grid(row=1, column=0, padx=6, pady=4, sticky="e")
        ttk.Combobox(win, textvariable=tpl, values=list(TEMPLATES), state="readonly", width=10).grid(row=1, column=1, padx=6, pady=4)

        def ok():
            folder = filedialog.askdirectory(title="Folder for the new spec", parent=win)
            if not folder:
                return
            spec = os.path.join(folder, f"{pre.get()}_{tpl.get()}.yaml")
            mock = os.path.join(folder, f"{pre.get()}_{tpl.get()}_mock.yaml")
            if (os.path.exists(spec) or os.path.exists(mock)) and not messagebox.askyesno("Overwrite?", f"{spec} exists. Overwrite?", parent=win):
                return
            s, m = render(tpl.get(), pre.get(), os.path.basename(spec), os.path.basename(mock))
            for path, text in ((spec, s), (mock, m)):
                with open(path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
            win.destroy()
            self.spec.set(spec)
            self.mock.set(mock)
            self.board.set("")
            self.load_editor()
            self.render(reload=True)
        ttk.Button(win, text="Create...", command=ok).grid(row=2, column=0, columnspan=2, pady=8)

    def save_png(self):
        if self.img is None:
            return
        f = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], initialfile=f"{self.board.get()}.png")
        if f:
            self.img.save(f)
            self.say(f"saved {f}")


def main(argv=None):
    """Open the app. A spec path (.yaml / .yml / .py) on the command line, e.g. a file dropped on
    GUIGen.exe, is opened instead of the last one used (a mock next to it is picked up too)."""
    if tk is None:
        print("tkinter is not available in this Python; install the python.org build or use the command line.")
        return 1
    argv = sys.argv[1:] if argv is None else argv
    root = tk.Tk()
    _set_icon(root)
    app = App(root)
    spec = next((a for a in argv if a.lower().endswith((".yaml", ".yml", ".py")) and os.path.exists(a)), None)
    if spec:
        app.spec.set(os.path.abspath(spec))
        stem = os.path.splitext(os.path.abspath(spec))[0]
        for cand in (stem + "_mock.yaml", os.path.join(os.path.dirname(spec), "mock.yaml")):
            if os.path.exists(cand) and not cand.endswith(os.path.basename(spec)):
                app.mock.set(cand)
                break
        app.board.set("")
        app.load_editor()
        app.render(reload=True)
    root.mainloop()
    return 0


def _set_icon(root):
    """Window icon: the bundled guigen.ico when frozen into an exe, else nothing."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        ico = os.path.join(base, "guigen.ico")
        if os.path.exists(ico):
            try:
                root.iconbitmap(ico)
            except tk.TclError:
                pass


if __name__ == "__main__":
    sys.exit(main())
