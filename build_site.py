#!/usr/bin/env python3
"""Build the student-facing IB164 demo site into docs/.

Each marimo WASM export ships an identical ~26 MB assets/ bundle. Every
asset reference in the exported HTML is relative ("./assets/..."), and the
entry-point filenames are distinct, so putting every published HTML file in
one flat directory beside a single shared assets/ works with no path
rewriting and cuts the site from ~189 MB to ~26 MB.

Re-runnable: docs/ is emptied and rebuilt from scratch each time.

    py -3.10 build_site.py
"""

import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"

# Copied once, from the first export that has them. The per-export CLAUDE.md
# is marimo authoring boilerplate, not our content, so it is never copied.
CHROME = [
    "favicon.ico",
    "favicon-16x16.png",
    "favicon-32x32.png",
    "apple-touch-icon.png",
    "android-chrome-192x192.png",
    "android-chrome-512x512.png",
    "logo.png",
    "manifest.json",
    "site.webmanifest",
]


class Demo:
    def __init__(self, export, page, title, blurb, heavy=False):
        self.export = export  # export dir, relative to ROOT
        self.page = page      # entry-point HTML filename, as published
        self.title = title
        self.blurb = blurb
        self.heavy = heavy    # pulls scipy -> slower first load


LABS = [
    (
        "Lab 1",
        "Probability and Inference",
        [
            Demo("lab1/_binomial_app", "binomial_distribution.html",
                 "The Binomial Distribution",
                 "How the shape of the binomial changes with the number of "
                 "trials and the probability of success.",
                 heavy=True),
            Demo("lab1/_binomial_hypothesis_app",
                 "binomial_hypothesis_separation.html",
                 "Distinguishing Close Hypotheses",
                 "Why telling two similar hypotheses apart takes a larger "
                 "sample than you might expect — the power of sample size.",
                 heavy=True),
            # "A Toy Model of a Polygenic Trait" is deliberately not
            # published: the material was not covered in the lab. The notebook
            # and its export remain in lab1/ - re-add this entry to publish it.
        ],
    ),
    (
        "Lab 2",
        "Probability and Intuition",
        [
            Demo("lab2/_monty_hall_app", "monty_hall.html",
                 "Let's Make a Deal",
                 "The Monty Hall problem. Play it, then simulate it, and see "
                 "why switching wins two times in three."),
        ],
    ),
    (
        "Lab 4",
        "Evolution in Action",
        [
            Demo("lab4/_peppered_moth_app", "peppered_moth.html",
                 "The Peppered Moth, and the Cost of Being Late",
                 "Industrial melanism as selection in real time, and what "
                 "happens when a population responds too slowly."),
            Demo("lab4/_helminth_mismatch_app", "helminth_mismatch.html",
                 "The Parasite That Isn't There Any More",
                 "Evolutionary mismatch: an immune system tuned for parasites "
                 "that modern life has removed."),
            Demo("lab4/_ccr5_cryptic_variation_app",
                 "ccr5_cryptic_variation.html",
                 "The Variation You Cannot See",
                 "Cryptic genetic variation at CCR5 — diversity that is "
                 "invisible until the environment changes."),
        ],
    ),
]

ALL_DEMOS = [d for _, _, demos in LABS for d in demos]


def find_entry(export_dir: Path, page: str) -> Path:
    """Locate an export's entry-point HTML.

    Some marimo versions write index.html, others the notebook-named file.
    """
    named = export_dir / page
    if named.is_file():
        return named
    index = export_dir / "index.html"
    if index.is_file():
        return index
    htmls = sorted(p for p in export_dir.glob("*.html"))
    if len(htmls) == 1:
        return htmls[0]
    raise SystemExit(
        "ERROR: no entry-point HTML found in {}\n"
        "  looked for {} and index.html; found: {}".format(
            export_dir, page, [p.name for p in htmls] or "nothing"
        )
    )


def reset_output_dir():
    """Empty docs/ in place, tolerating Windows directory locks.

    On Windows a directory cannot be removed while any process holds it open
    (a preview server, an editor, Explorer, a sync client). Deleting the
    *contents* rather than the directory itself still works in that case, so
    the build succeeds instead of crashing half-way and leaving a broken site.
    """
    OUT.mkdir(parents=True, exist_ok=True)

    failures = []
    for child in OUT.iterdir():
        try:
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, onerror=_force_remove)
            else:
                child.unlink()
        except OSError as exc:
            failures.append((child, exc))

    if failures:
        lines = "\n".join(
            "  {}: {}".format(path.name, exc) for path, exc in failures)
        raise SystemExit(
            "ERROR: could not clear docs/ - these are still in use:\n"
            + lines
            + "\n\nClose anything using the folder (a running preview_site"
              ".bat window, an open editor tab, or an Explorer window inside"
              " docs\\) and run this again."
        )


def _force_remove(func, path, _exc):
    """rmtree handler: clear the read-only bit and retry once."""
    import os
    import stat
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except OSError:
        raise


def build():
    # Fail early and loudly if an export is missing, rather than shipping a
    # landing page with dead links.
    missing = [d.export for d in ALL_DEMOS if not (ROOT / d.export).is_dir()]
    if missing:
        raise SystemExit(
            "ERROR: missing export directories:\n  "
            + "\n  ".join(missing)
            + "\n\nRe-export with:\n"
            "  py -3.10 -m marimo export html-wasm <notebook>.py "
            "-o <export dir> --mode run"
        )

    reset_output_dir()

    # 1. The single shared assets/ bundle.
    src_assets = ROOT / ALL_DEMOS[0].export / "assets"
    if not src_assets.is_dir():
        raise SystemExit("ERROR: no assets/ in {}".format(src_assets.parent))
    shutil.copytree(src_assets, OUT / "assets")
    n_assets = sum(1 for p in (OUT / "assets").rglob("*") if p.is_file())
    print("assets/  {} files (shared by all {} demos)".format(
        n_assets, len(ALL_DEMOS)))

    # 2. Favicons/manifests, once.
    for name in CHROME:
        src = ROOT / ALL_DEMOS[0].export / name
        if src.is_file():
            shutil.copy2(src, OUT / name)

    # 3. Each demo's entry-point HTML, published under its distinct name.
    seen = {}
    for demo in ALL_DEMOS:
        entry = find_entry(ROOT / demo.export, demo.page)
        if demo.page in seen:
            raise SystemExit(
                "ERROR: two demos both publish as {}: {} and {}".format(
                    demo.page, seen[demo.page], demo.export))
        seen[demo.page] = demo.export
        shutil.copy2(entry, OUT / demo.page)
        note = "" if entry.name == demo.page else "  (from {})".format(entry.name)
        print("  {}{}".format(demo.page, note))

    # 4. Tell GitHub Pages not to run Jekyll, which would drop asset files
    #    whose names begin with an underscore.
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    # 5. Landing page.
    (OUT / "index.html").write_text(render_index(), encoding="utf-8")

    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print("\ndocs/ built: {:.1f} MB".format(total / 1e6))
    if total > 60e6:
        print("WARNING: larger than expected - assets/ may not be shared.")


def render_index() -> str:
    e = html.escape
    nl = "\n"
    sections = []
    for lab, subtitle, demos in LABS:
        cards = []
        for d in demos:
            slow = ('<span class="slow" title="Loads scipy as well, so the '
                    'first start takes a little longer">slower first load'
                    '</span>') if d.heavy else ""
            cards.append(
                '        <li class="card">\n'
                '          <a href="{page}">\n'
                '            <h3>{title}{slow}</h3>\n'
                '            <p>{blurb}</p>\n'
                '          </a>\n'
                '        </li>'.format(
                    page=e(d.page), title=e(d.title), slow=slow,
                    blurb=e(d.blurb))
            )
        count = "{} demo{}".format(len(demos), "" if len(demos) == 1 else "s")
        # <details> gives a real accordion with no JavaScript: it works when
        # scripts are blocked, and is keyboard- and screen-reader-accessible
        # for free. Closed by default (no `open` attribute).
        sections.append(
            '      <details class="lab">\n'
            '        <summary>\n'
            '          <span class="lab-tag">{lab}</span>\n'
            '          <span class="lab-name">{sub}</span>\n'
            '          <span class="lab-count">{count}</span>\n'
            '        </summary>\n'
            '        <ul class="cards">\n'
            '{cards}\n'
            '        </ul>\n'
            '      </details>'.format(
                lab=e(lab), sub=e(subtitle), count=count,
                cards=nl.join(cards))
        )

    # Later labs first: students are most likely to want the lab they just did.
    sections.reverse()

    return TEMPLATE.replace("__SECTIONS__", nl.join(sections))


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IB164 Interactive Demos</title>
<meta name="description" content="Interactive browser-based demos for IB164. Nothing to install.">
<link rel="icon" href="favicon.ico">
<style>
  :root {
    --bg: #fbfaf8;
    --surface: #ffffff;
    --border: #e4e0d8;
    --text: #23201c;
    --muted: #625c53;
    --accent: #6b4f9e;
    --accent-soft: #f1ecf9;
    --shadow: 0 1px 2px rgba(35,32,28,.05), 0 4px 14px rgba(35,32,28,.05);
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #17161a;
      --surface: #201f25;
      --border: #333039;
      --text: #ece9f0;
      --muted: #a8a2b0;
      --accent: #b9a0ea;
      --accent-soft: #2b2536;
      --shadow: 0 1px 2px rgba(0,0,0,.3), 0 4px 14px rgba(0,0,0,.25);
    }
    :root:not([data-theme="light"]) .lab-tag { color: #17161a; }
  }
  :root[data-theme="dark"] {
    --bg: #17161a; --surface: #201f25; --border: #333039;
    --text: #ece9f0; --muted: #a8a2b0; --accent: #b9a0ea;
    --accent-soft: #2b2536;
    --shadow: 0 1px 2px rgba(0,0,0,.3), 0 4px 14px rgba(0,0,0,.25);
  }
  :root[data-theme="dark"] .lab-tag { color: #17161a; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font: 16px/1.6 ui-sans-serif, system-ui, -apple-system, "Segoe UI",
          Roboto, Helvetica, Arial, sans-serif;
    -webkit-text-size-adjust: 100%;
  }
  .wrap { max-width: 860px; margin: 0 auto; padding: 48px 16px 72px; }
  header { margin-bottom: 32px; }
  h1 { font-size: 1.9rem; line-height: 1.2; margin: 0 0 6px; letter-spacing: -.02em; }
  .sub { color: var(--muted); margin: 0; }
  .note {
    margin: 28px 0 40px;
    padding: 16px 18px;
    background: var(--accent-soft);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 10px;
  }
  .note p { margin: 0; }
  .note p + p { margin-top: 10px; color: var(--muted); font-size: .92rem; }
  .lab {
    margin-bottom: 14px; background: var(--surface);
    border: 1px solid var(--border); border-radius: 12px;
    box-shadow: var(--shadow); overflow: hidden;
  }
  .lab summary {
    display: flex; align-items: center; gap: 11px; flex-wrap: wrap;
    padding: 16px 18px; cursor: pointer; font-weight: 600;
    color: var(--text); list-style: none; user-select: none;
  }
  /* Replace the native triangle with our own chevron, both engines. */
  .lab summary::-webkit-details-marker { display: none; }
  .lab summary::marker { content: ""; }
  .lab summary::after {
    content: ""; margin-left: auto; width: 8px; height: 8px;
    border-right: 2px solid var(--muted); border-bottom: 2px solid var(--muted);
    transform: rotate(45deg) translate(-2px, -2px);
    transition: transform .2s; flex: none;
  }
  .lab[open] summary::after {
    transform: rotate(225deg) translate(-2px, -2px);
  }
  .lab summary:hover { background: var(--accent-soft); }
  .lab summary:focus-visible {
    outline: 2px solid var(--accent); outline-offset: -2px;
  }
  .lab-name { font-size: 1.02rem; }
  .lab-count {
    font-size: .8rem; font-weight: 500; color: var(--muted);
  }
  .lab[open] summary { border-bottom: 1px solid var(--border); }
  .lab .cards { padding: 16px 18px 18px; }
  .lab-tag {
    background: var(--accent); color: #fff; font-size: .74rem;
    letter-spacing: .06em; text-transform: uppercase; font-weight: 700;
    padding: 3px 9px; border-radius: 999px; flex: none;
  }
  .cards { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
  .card a {
    display: block; padding: 16px 18px; background: var(--bg);
    border: 1px solid var(--border); border-radius: 10px;
    text-decoration: none; color: inherit;
    transition: border-color .15s, transform .15s;
  }
  .card a:hover, .card a:focus-visible {
    border-color: var(--accent); transform: translateY(-1px);
  }
  .card a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
  .card h3 {
    margin: 0 0 5px; font-size: 1.06rem; color: var(--accent);
    display: flex; align-items: center; gap: 9px; flex-wrap: wrap;
  }
  .card p { margin: 0; color: var(--muted); font-size: .93rem; }
  .slow {
    font-size: .68rem; text-transform: uppercase; letter-spacing: .05em;
    font-weight: 700; color: var(--muted); background: var(--bg);
    border: 1px solid var(--border); border-radius: 999px; padding: 2px 8px;
  }
  footer {
    margin-top: 48px; padding-top: 20px; border-top: 1px solid var(--border);
    color: var(--muted); font-size: .88rem;
  }
  footer p { margin: 0; }
  @media (prefers-reduced-motion: reduce) {
    .card a { transition: none; }
    .card a:hover, .card a:focus-visible { transform: none; }
    .lab summary::after { transition: none; }
  }
</style>
</head>
<body>
  <div class="wrap">
    <header>
      <h1>IB164 Interactive Demos</h1>
      <p class="sub">Choose a lab below to see its demos. Each one runs in
      your browser.</p>
    </header>

    <div class="note">
      <p><strong>Nothing to install.</strong> These run entirely in your
      browser. The first demo you open takes <strong>10&ndash;30 seconds</strong>
      to start while it downloads Python behind the scenes &mdash; this is
      normal, so please give it a moment. After that, everything is quick.</p>
      <p>Works on laptops, Chromebooks and tablets. Use an up-to-date Chrome,
      Edge, Firefox or Safari, and stay connected to the internet.</p>
    </div>

__SECTIONS__

    <footer>
      <p>If a demo does not load, refresh the page once and check that you are
      connected to the internet.</p>
    </footer>
  </div>
</body>
</html>
"""


if __name__ == "__main__":
    sys.exit(build())
