"""Entry point of guigen-cli.exe (the command line: new, preview, validate, diff, build, app, doctor, themes)."""
import sys

from guigen.cli import main

if __name__ == "__main__":
    sys.exit(main())
