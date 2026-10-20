#!/usr/bin/env python3
"""Copy the texts in lab7/texts.txt into every Lab 7 notebook.

The demos run in the browser (marimo WASM), where reading a local file is
awkward, so instead of reading texts.txt at runtime each notebook carries its
own copy. This script rewrites the block between the two marker lines

    # >>> TEXTS (generated from texts.txt - do not edit) >>>
    # <<< TEXTS <<<

in each notebook and leaves everything else untouched. Running it twice
changes nothing the second time.

    py -3.10 lab7/embed_texts.py

Problems with a text (too short, a variant word that is not there, ...) are
printed as warnings; they never stop the embed.
"""

import pprint
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEXTS_FILE = HERE / "texts.txt"

START = "# >>> TEXTS (generated from texts.txt - do not edit) >>>"
END = "# <<< TEXTS <<<"

# These must match the constants of the same name in the notebooks.
GENOTYPE_REF_LEN = 300     # genotyping reference = first ~300 characters
MIN_GENERAL_LEN = 600      # the assembly demo wants at least this
MAX_SHORT_READ = 160       # top of the repeats demo's read-length slider
MIN_REPEAT = 20            # a repeat text needs a repeat at least this long


def trim_words(text, n):
    """The first ~n characters of text, cut back to a word boundary."""
    if len(text) <= n:
        return text
    cut = text.rfind(" ", 0, n)
    return text[: cut if cut > 0 else n].rstrip()


def longest_repeat(text):
    """Longest substring that occurs at least twice (overlaps allowed)."""
    suffixes = sorted(range(len(text)), key=lambda i: text[i:])
    best, best_at = 0, 0
    for a, b in zip(suffixes, suffixes[1:]):
        k = 0
        while (a + k < len(text) and b + k < len(text)
               and text[a + k] == text[b + k]):
            k += 1
        if k > best:
            best, best_at = k, a
    return text[best_at:best_at + best]


def parse(path):
    texts = []
    current = None
    in_passage = False
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        if line.startswith("#"):
            continue
        if line.startswith("==="):
            current = {"title": line[3:].strip(), "kind": "general",
                       "puzzle": "", "variants": [], "passage": [],
                       "line": lineno}
            texts.append(current)
            in_passage = False
            continue
        if current is None:
            if line.strip():
                warn("line {}: text before the first === line is ignored"
                     .format(lineno))
            continue
        if in_passage:
            current["passage"].append(line.strip())
        elif line.strip() == "---":
            in_passage = True
        elif not line.strip():
            continue
        else:
            key, _, value = line.partition(":")
            key, value = key.strip().lower(), value.strip()
            if key == "kind":
                if value not in ("general", "repeat"):
                    warn("{}: kind must be 'general' or 'repeat', not {!r}; "
                         "using general".format(current["title"], value))
                    value = "general"
                current["kind"] = value
            elif key == "puzzle":
                current["puzzle"] = value
            elif key == "variants":
                for item in filter(None, (v.strip() for v in value.split(","))):
                    old, sep, new = item.partition(">")
                    if not sep:
                        warn("{}: variant {!r} should look like old>new"
                             .format(current["title"], item))
                        continue
                    current["variants"].append([old.strip(), new.strip()])
            else:
                warn("{} (line {}): unknown setting {!r} - did you forget the "
                     "--- line before the passage?".format(
                         current["title"], lineno, key))

    out = []
    for t in texts:
        passage = re.sub(r"\s+", " ", " ".join(t["passage"])).strip()
        if not passage:
            warn("{}: no passage (put it after a --- line); skipped"
                 .format(t["title"]))
            continue
        out.append({
            "title": t["title"],
            "kind": t["kind"],
            "puzzle": re.sub(r"\s+", " ", t["puzzle"]).strip(),
            "variants": t["variants"],
            "passage": passage,
        })
    return out


WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)


def check(texts):
    general = [t for t in texts if t["kind"] == "general"]
    repeat = [t for t in texts if t["kind"] == "repeat"]
    if not general:
        warn("no 'kind: general' texts - the assembly and "
             "genotyping demos need at least one")
    if not repeat:
        warn("no 'kind: repeat' texts - the repeats demo needs at least one")

    titles = [t["title"] for t in texts]
    for title in sorted({x for x in titles if titles.count(x) > 1}):
        warn("two texts are both called {!r}".format(title))

    for t in general:
        name, passage = t["title"], t["passage"]
        if len(passage) < MIN_GENERAL_LEN:
            warn("{}: passage is {} characters; the assembly "
                 "demo wants at least {}".format(name, len(passage),
                                                 MIN_GENERAL_LEN))
        if t["puzzle"] and not 60 <= len(t["puzzle"]) <= 200:
            warn("{}: puzzle sentence is {} characters; 100-150 works best"
                 .format(name, len(t["puzzle"])))
        ref = trim_words(passage, GENOTYPE_REF_LEN)
        for old, new in t["variants"]:
            if len(old) != len(new) or sum(a != b for a, b in zip(old, new)) != 1:
                warn("{}: variant {}>{} is not a one-letter change"
                     .format(name, old, new))
            elif not re.search(r"\b{}\b".format(re.escape(old)), ref):
                warn("{}: variant word {!r} is not in the first ~{} "
                     "characters (the genotyping reference)".format(
                         name, old, GENOTYPE_REF_LEN))

    for t in repeat:
        rep = longest_repeat(t["passage"])
        print("  repeat text {!r}: {} characters, longest repeat {} "
              "characters".format(t["title"], len(t["passage"]), len(rep)))
        if len(rep) < MIN_REPEAT:
            warn("{}: longest exact repeat is only {} characters - it will "
                 "not trouble the assembler".format(t["title"], len(rep)))
        elif len(rep) > MAX_SHORT_READ:
            warn("{}: longest repeat ({} characters) is longer than the "
                 "longest short read ({}), so short reads can never resolve "
                 "it".format(t["title"], len(rep), MAX_SHORT_READ))
        if len(t["passage"]) > 1500:
            warn("{}: {} characters is long for the repeats demo, which may "
                 "feel slow; 400-1,200 is best".format(
                     t["title"], len(t["passage"])))


def render_block(texts, indent):
    for t in texts:
        t["variants"] = [tuple(v) for v in t["variants"]]
    body = pprint.pformat(texts, width=79 - len(indent), sort_dicts=False)
    lines = ("TEXTS = " + body).splitlines()
    return "\n".join(indent + line for line in lines)


def embed(notebook, texts):
    src = notebook.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^([ \t]*)" + re.escape(START) + r"\n.*?^[ \t]*" + re.escape(END),
        re.S | re.M)
    m = pattern.search(src)
    if not m:
        return None
    indent = m.group(1)
    new = "{i}{s}\n{b}\n{i}{e}".format(
        i=indent, s=START, b=render_block([dict(t) for t in texts], indent),
        e=END)
    out = src[:m.start()] + new + src[m.end():]
    if out == src:
        return False
    notebook.write_text(out, encoding="utf-8")
    return True


def main():
    texts = parse(TEXTS_FILE)
    print("Read {} texts from {}".format(len(texts), TEXTS_FILE.name))
    check(texts)

    notebooks = sorted(p for p in HERE.glob("*.py") if p.name != Path(__file__).name)
    for nb in notebooks:
        result = embed(nb, texts)
        if result is None:
            continue
        print("  {}: {}".format(nb.name, "updated" if result else "unchanged"))

    if WARNINGS:
        print("\nWARNINGS ({}):".format(len(WARNINGS)))
        for w in WARNINGS:
            print("  - " + w)
    else:
        print("\nNo problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
