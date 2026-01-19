#!/usr/bin/env python3
"""Convert Markdown files to HTML using pandoc (preferred) or pypandoc fallback.

Usage: python scripts/convert_md_to_html.py file1.md file2.md ...

This script is intended to be used as a pre-commit hook. It writes an HTML file
next to each Markdown file with the same basename and a .html extension.
"""
import shutil
import subprocess
import sys
from pathlib import Path


def find_pandoc():
    exe = shutil.which("pandoc")
    if exe:
        return exe
    # Common Windows location used by the workspace task
    possible = Path("C:/bci/pandoc/pandoc.exe")
    if possible.exists():
        return str(possible)
    return None


def convert_with_pandoc(pandoc, src: Path, dst: Path) -> bool:
    cmd = [pandoc, str(src), "-s", "-o", str(dst)]
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def convert_with_pypandoc(src: Path, dst: Path) -> bool:
    try:
        import pypandoc

        content = pypandoc.convert_file(str(src), "html")
        dst.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def main(argv):
    if len(argv) < 2:
        print("No files supplied; nothing to do.")
        return 0

    pandoc = find_pandoc()
    had_error = False
    for f in argv[1:]:
        p = Path(f)
        if not p.exists():
            # pre-commit may pass filenames that were removed; skip
            continue
        if p.suffix.lower() != ".md":
            continue
        out = p.with_suffix(".html")
        print(f"Converting {p} -> {out}")
        ok = False
        if pandoc:
            ok = convert_with_pandoc(pandoc, p, out)
        if not ok:
            ok = convert_with_pypandoc(p, out)
        if not ok:
            print(f"Warning: failed to convert {p} (no pandoc/pypandoc available)")
            had_error = True

    return 1 if had_error else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
