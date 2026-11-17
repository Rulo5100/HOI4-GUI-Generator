"""Mod file access: reading, line-ending aware writing, staging for diffs.

Every text file goes through `ModFS.write_text`, which writes bytes (never text mode) and picks the
line ending per file:

* ``eol="auto"`` (default): match the file already on disk; if there is none, match the blob in git
  HEAD; if that is missing too, use CRLF (the HOI4 convention on Windows).
* ``eol="crlf"`` / ``eol="lf"``: force one.

With ``stage`` set, nothing in the mod is touched: files go to the staging folder instead, so a build
can be diffed against the live mod first (see ``guigen diff``).
"""
import os
import subprocess

VANILLA_GUESSES = [
    r"C:/Program Files (x86)/Steam/steamapps/common/Hearts of Iron IV",
    r"C:/Program Files/Steam/steamapps/common/Hearts of Iron IV",
    r"D:/SteamLibrary/steamapps/common/Hearts of Iron IV",
    os.path.expanduser("~/.steam/steam/steamapps/common/Hearts of Iron IV"),
    os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/Hearts of Iron IV"),
]

BOM = b"\xef\xbb\xbf"


def find_vanilla(explicit=None):
    for p in ([explicit] if explicit else []) + [os.environ.get("HOI4_PATH")] + VANILLA_GUESSES:
        if p and os.path.isdir(os.path.join(p, "interface")):
            return p
    return None


def detect_eol(data):
    """'crlf', 'lf' or None (no line breaks at all)."""
    head = data[:65536]
    if b"\r\n" in head:
        return "crlf"
    if b"\n" in head:
        return "lf"
    return None


class ModFS:
    def __init__(self, root, vanilla=None, stage=None, eol="auto"):
        self.root = os.path.abspath(root)
        self.vanilla = find_vanilla(vanilla)
        self.stage = os.path.abspath(stage) if stage else None
        self.eol = eol
        self.written = []          # (rel, kind) in write order
        self._head_cache = {}

    # ------------------------------------------------------------------ paths
    def path(self, rel):
        """Path inside the live mod."""
        return os.path.join(self.root, rel)

    def out_path(self, rel):
        """Where a generated file is written (the staging folder when staging)."""
        return os.path.join(self.stage or self.root, rel)

    def vpath(self, rel):
        return os.path.join(self.vanilla, rel) if self.vanilla else None

    def exists(self, rel):
        return os.path.exists(self.path(rel))

    def find(self, rel):
        """First existing copy of rel: staged output, mod, then vanilla."""
        for p in (self.stage and os.path.join(self.stage, rel), self.path(rel), self.vpath(rel)):
            if p and os.path.exists(p):
                return p
        return None

    # ------------------------------------------------------------------ reading
    def read_bytes(self, rel):
        with open(self.path(rel), "rb") as f:
            return f.read()

    def read_text(self, rel):
        """(text with LF line endings, had_bom)."""
        b = self.read_bytes(rel)
        return b.decode("utf-8-sig").replace("\r\n", "\n"), b.startswith(BOM)

    def head_blob(self, rel):
        """Bytes of rel in git HEAD, or None (no repo, untracked, git missing)."""
        if rel in self._head_cache:
            return self._head_cache[rel]
        data = None
        try:
            r = subprocess.run(["git", "-C", self.root, "show", "HEAD:" + rel.replace("\\", "/")],
                               capture_output=True, timeout=30)
            if r.returncode == 0:
                data = r.stdout
        except (OSError, subprocess.SubprocessError):
            pass
        self._head_cache[rel] = data
        return data

    def eol_for(self, rel):
        if self.eol in ("crlf", "lf"):
            return self.eol
        if self.exists(rel):
            e = detect_eol(self.read_bytes(rel))
            if e:
                return e
        blob = self.head_blob(rel)
        if blob:
            e = detect_eol(blob)
            if e:
                return e
        return "crlf"

    # ------------------------------------------------------------------ writing
    def encode_text(self, rel, text, bom=False):
        text = text.replace("\r\n", "\n")
        if self.eol_for(rel) == "crlf":
            text = text.replace("\n", "\r\n")
        return (BOM if bom else b"") + text.encode("utf-8")

    def write_bytes(self, rel, data, kind="bin"):
        p = self.out_path(rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as f:
            f.write(data)
        self.written.append((rel, kind))
        return p

    def write_text(self, rel, text, bom=False, check_braces=True):
        if check_braces and rel.endswith((".txt", ".gui", ".gfx")):
            o, c = text.count("{"), text.count("}")
            if o != c:
                raise ValueError(f"unbalanced braces in {rel}: {o} '{{' vs {c} '}}'")
        return self.write_bytes(rel, self.encode_text(rel, text, bom), "text")

    def write_image(self, rel, img):
        p = self.out_path(rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p)
        self.written.append((rel, "image"))
        return p
