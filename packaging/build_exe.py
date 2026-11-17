"""Build the Windows executables with PyInstaller.

    python packaging/build_exe.py

Run it with the Python whose architecture you want the exe to have. An x64 Python gives an exe that
runs on every Windows 10/11 PC (ARM PCs run it through Windows' x64 emulation).

Needs: pip install pyinstaller pillow numpy pyyaml

Output (dist/):
    GUIGen.exe        the desktop app (double-click; drop a spec file on it to open that spec)
    guigen-cli.exe    the command line (guigen-cli new XYZ, guigen-cli preview spec.yaml ...)
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "packaging")
BUILD = os.path.join(ROOT, "build")
DIST = os.path.join(ROOT, "dist")


def make_icon(path):
    """A small bar-and-line chart icon, drawn with Pillow at the usual Windows icon sizes."""
    from PIL import Image, ImageDraw
    S = 256
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([8, 8, S - 8, S - 8], 44, fill=(30, 34, 42, 255), outline=(150, 160, 175, 255), width=10)
    for i, (h, col) in enumerate(((70, (85, 140, 215)), (120, (205, 160, 55)), (95, (85, 170, 80)), (160, (190, 55, 45)))):
        x = 44 + i * 44
        d.rectangle([x, S - 46 - h, x + 30, S - 46], fill=col + (255,))
    d.line([(46, 150), (100, 112), (146, 128), (214, 60)], fill=(235, 235, 240, 255), width=12, joint="curve")
    img.save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def pyinstaller(entry, name, windowed, icon):
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--name", name,
           "--icon", icon, "--add-data", f"{icon}{os.pathsep}.",
           "--collect-submodules", "guigen", "--hidden-import", "yaml", "--hidden-import", "numpy",
           "--distpath", DIST, "--workpath", os.path.join(BUILD, name), "--specpath", os.path.join(BUILD, name),
           "--paths", ROOT]
    if windowed:
        cmd.append("--windowed")
    cmd.append(entry)
    print(">", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def main():
    os.makedirs(BUILD, exist_ok=True)
    icon = os.path.join(BUILD, "guigen.ico")
    make_icon(icon)
    pyinstaller(os.path.join(PKG, "app_entry.py"), "GUIGen", True, icon)
    pyinstaller(os.path.join(PKG, "cli_entry.py"), "guigen-cli", False, icon)
    for exe in ("GUIGen.exe", "guigen-cli.exe"):
        p = os.path.join(DIST, exe)
        print(f"{exe}: {os.path.getsize(p) / 1e6:.1f} MB  {p}")
    return 0


if __name__ == "__main__":
    if "--clean" in sys.argv:
        shutil.rmtree(BUILD, ignore_errors=True)
        shutil.rmtree(DIST, ignore_errors=True)
    sys.exit(main())
