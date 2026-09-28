#!/usr/bin/env python3
"""Print resume.html to assets/resume/King-Joshua-Marcos-Resume.pdf.

resume.html is the source of truth and its @media print rules define the paper
layout, so all this has to do is print the page. It drives a headless Edge or
Chrome, which means there is nothing to install.

    python scripts/build-resume-pdf.py
    python scripts/build-resume-pdf.py --browser "C:/path/to/chrome.exe"

The site has no build step, so the PDF is a committed artifact: re-run this and
commit both files whenever resume.html changes.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "resume.html"
OUTPUT = ROOT / "assets" / "resume" / "King-Joshua-Marcos-Resume.pdf"
MAX_PAGES = 2
LETTER = (0.0, 0.0, 612.0, 792.0)

BROWSER_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]
BROWSER_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "microsoft-edge", "msedge", "chrome"]


def find_browser(explicit):
    candidates = [explicit or os.environ.get("BROWSER")]
    candidates += BROWSER_PATHS + [shutil.which(name) for name in BROWSER_NAMES]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    sys.exit("No Edge or Chrome found. Pass --browser <path> or set BROWSER.")


def print_pdf(browser, out, extra_flags=()):
    """Print resume.html to `out`. Returns None on success, else a reason string.

    A throwaway profile stops headless from handing off to an already-running
    browser, which then exits without writing anything.
    """
    profile = tempfile.mkdtemp(prefix="resume-pdf-")
    try:
        run = subprocess.run(
            [browser, "--headless", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
             *extra_flags, f"--user-data-dir={profile}", f"--print-to-pdf={out}", SOURCE.as_uri()],
            capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "did not finish within 120s"
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if out.is_file():
        return None
    return f"exited {run.returncode} without writing a PDF\n{run.stderr.strip()[-600:]}"


def check(pdf):
    """Refuse to replace the committed PDF with one that is obviously worse."""
    data = pdf.read_bytes()
    if not data.startswith(b"%PDF") or len(data) < 10_000:
        sys.exit(f"Browser output is not a usable PDF ({len(data)} bytes).")

    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    if pages == 0:
        print("warning: could not count pages (compressed page tree), skipping the page-count check")
    elif pages > MAX_PAGES:
        sys.exit(f"Resume printed to {pages} pages, limit is {MAX_PAGES}. Tighten resume.html.")

    boxes = {tuple(float(n) for n in raw.decode("ascii", "replace").split())
             for raw in re.findall(rb"/MediaBox\s*\[([^\]]*)\]", data)}
    if boxes and boxes != {LETTER}:
        sys.exit(f"Expected US Letter pages {LETTER}, got {sorted(boxes)}.")
    return pages


def main():
    parser = argparse.ArgumentParser(description="Print resume.html to the committed resume PDF.")
    parser.add_argument("--browser", help="Chromium-based browser to use (default: auto-detect Edge/Chrome)")
    args = parser.parse_args()

    if not SOURCE.is_file():
        sys.exit(f"Missing {SOURCE}")
    browser = find_browser(args.browser)
    name = Path(browser).name

    # Print to a temp file next to the output and only swap it in once it passes
    # check(), so a bad render never overwrites the good PDF.
    building = OUTPUT.with_suffix(".building.pdf")
    building.unlink(missing_ok=True)
    try:
        error = print_pdf(browser, building)
        if error:
            # Chromium's child-process sandbox can fail to start in locked-down
            # shells (GPU/network service crash on launch). The only page loaded
            # is our own local file, so retrying without it is safe.
            print(f"{name} {error.splitlines()[0]}; retrying with --no-sandbox (only a local file is loaded)")
            error = print_pdf(browser, building, ["--no-sandbox"])
        if error:
            sys.exit(f"{name} {error}")
        pages = check(building)
        os.replace(building, OUTPUT)
    finally:
        building.unlink(missing_ok=True)

    print(f"wrote {OUTPUT.relative_to(ROOT)} ({pages or '?'} pages, {OUTPUT.stat().st_size // 1024} KB) via {name}")


if __name__ == "__main__":
    main()
