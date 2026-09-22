# IB164 — Interactive Lab Demos

Interactive [marimo](https://marimo.io) notebooks for IB164, published as a
static website so students can run them in a browser with nothing to install.

**Live site:** <https://thomaskatkins.github.io/IB164/>
*(live once the steps in `PUBLISHING.md` are done)*

## For students

Open the link above and click a demo. Everything runs in the browser — no
Python, no downloads, no setup. The first demo takes 10–30 seconds to start
while it fetches Python in the background; after that it is quick.

An internet connection is required, and a current version of Chrome, Edge,
Firefox or Safari.

## Repository layout

```
lab1/  binomial_distribution.py, binomial_hypothesis_separation.py
       polygenic_height.py (kept, but NOT published - see below)
lab2/  monty_hall.py
lab3/  GWAS report generator (NOT published — see below)
lab4/  peppered_moth.py, helminth_mismatch.py, ccr5_cryptic_variation.py

build_site.py     builds docs/ from the marimo exports
docs/             the built site; GitHub Pages serves this folder
update_site.bat   rebuild + commit + push
preview_site.bat  preview docs/ locally before publishing
PUBLISHING.md     step-by-step first-time GitHub Pages setup
```

The `lab*/_*_app/` export folders and `lab3/` are intentionally git-ignored
(see [Why some things are not committed](#why-some-things-are-not-committed)).

## Editing a demo

1. Edit the notebook:

   ```
   py -3.10 -m marimo edit lab4/peppered_moth.py
   ```

   marimo only runs under `py -3.10` on this machine.

2. Re-export it to WASM:

   ```
   py -3.10 -m marimo export html-wasm lab4/peppered_moth.py -o lab4/_peppered_moth_app --mode run
   ```

3. Preview locally — worth doing, since a notebook can work in `marimo edit`
   and still fail in the browser:

   ```
   preview_site.bat
   ```

4. Publish:

   ```
   update_site.bat "Update peppered moth demo"
   ```

   GitHub Pages refreshes within about a minute. Students may need one refresh.

## Adding a new demo

Export it as above, then add one `Demo(...)` entry to the `LABS` list near the
top of `build_site.py` and run `update_site.bat`. The landing page is generated
from that list, so nothing else needs editing.

Keep `LABS` in ascending lab order (Lab 1 first). The landing page reverses
it at render time so the most recent lab appears at the top, which is the
one students usually want.

Set `heavy=True` if the notebook imports scipy — it tags the demo as a slower
first load on the landing page.

## How the site is built

Each marimo WASM export ships its own copy of the same ~26 MB `assets/` bundle.
They are byte-identical, every asset reference in the exported HTML is
relative (`./assets/...`), and the entry-point filenames are distinct.
So `build_site.py` puts every published HTML file in one flat directory
beside a single shared `assets/`, with no path rewriting.

That takes the site from ~189 MB to ~26 MB — a comfortable fit for GitHub Pages
and a fast clone.

`docs/` is emptied and rebuilt on every run, so never edit it by hand.
It is emptied in place rather than deleted, because on Windows the folder
cannot be removed while a preview server, editor or Explorer window holds
it open.

## First-time GitHub Pages setup

See **`PUBLISHING.md`** for the full step-by-step guide, including how to
create the access token git will ask for.

The short version: `git init -b main`, commit, create a public repo named
`IB164` on GitHub, push, then set **Settings > Pages > Deploy from a
branch > `main` / `docs`**.

Check `git status` shows no `.tsv.bgz` files before the first push.

## Demos that exist but are not published

`lab1/polygenic_height.py` ("A Toy Model of a Polygenic Trait") is
deliberately left off the site: the material was not covered in the lab,
and showing it would confuse students. The notebook and its export are
untouched in `lab1/`.

To publish it again, un-comment its `Demo(...)` entry in the `LABS` list
in `build_site.py` and run `update_site.bat`.

## Why some things are not committed

- **`lab3/` and `*.tsv.bgz`** — the Pan-UKBB GWAS summary statistics are about
  8.8 GB across five files, the largest 2.3 GB. GitHub rejects any file over
  100 MB, and a single `git add .` without these rules produces a repository
  that cannot be pushed and is awkward to unpick. `lab3` is a local command-line
  tool, not a student-facing demo.
- **`lab*/_*_app/`** — generated export folders, ~189 MB of duplicated
  `assets/`. `docs/` already contains everything the site needs; these are
  reproducible from the notebooks at any time.

## Note on the demos themselves

All the notebooks are fully self-contained: they generate their data with
numpy and read no external files, which is what makes them work in the browser.
If you add a demo that loads a data file, it will need extra handling to work
under WASM.
