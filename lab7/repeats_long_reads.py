import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🔁 Repeats, and Why Long Reads Help

    Genomes are full of **repeats**: stretches of DNA that appear, letter for
    letter, in more than one place. About half of the human genome is
    repeats, mostly copies of "jumping genes" that have pasted themselves all
    over the place.

    Repeats are the main reason genome assembly goes wrong. Here the
    "genome" is a text that naturally repeats itself, like a chorus or a
    cumulative rhyme. First you will try to assemble some of it yourself.
    Then you will watch a computer try.
    """)
    return


@app.cell
def _(REPEAT, mo, on_new_puzzle, on_text):
    # Must not read the state: re-running a cell that creates UI elements
    # resets them.
    text_dd = mo.ui.dropdown(
        options=[t["title"] for t in REPEAT],
        value=REPEAT[0]["title"],
        label="**Choose a text**",
        on_change=lambda v: on_text(v),
    )
    # Buttons must be bound to global variables, or marimo ignores clicks.
    new_puzzle_btn = mo.ui.button(label="🎲 New puzzle",
                                  on_change=on_new_puzzle)
    mo.hstack([text_dd, new_puzzle_btn], justify="start", gap=1,
              align="center")
    return (text_dd,)


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 1: try it yourself

    Here is a short stretch of the text, shredded into pieces. Just as in the
    first demo, **drag the pieces** so their letters line up. Pieces that
    overlap correctly snap together, and double-clicking a piece pulls it off.

    One thing is different: **some words repeat, and the repeated stretch is
    longer than any piece.** Assemble a complete line with no gaps and no
    clashes, and see what happens. Stuck? **Give up** shows you the answer,
    and how your arrangement compares with it.
    """)
    return


@app.cell
def _(BOARD_HTML, get_sim, iframe_html, json, mo):
    _pz = get_sim()["puzzle"]
    _parts = []
    if _pz["alt"] is None:
        _parts.append(mo.callout(mo.md(
            "This text's repeats are too short to fool you in a puzzle this "
            "size, so this one is just an ordinary puzzle. Try another text "
            "for the full effect."), kind="neutral"))
    _data = json.dumps({
        "truth": _pz["truth"], "reads": _pz["reads"], "alt": _pz["alt"],
        "giveup": True,
        "next": "Now see how a computer gets on in Part 2.",
    })
    _parts.append(mo.Html(iframe_html(
        BOARD_HTML.replace("__DATA__", _data.replace("</", "<\\/")),
        height=560)))
    mo.vstack(_parts, gap=0.4)
    return


@app.cell
def _(LONGEST_REPEAT, greedy_read_len, mo, text_dd):
    _rep = len(LONGEST_REPEAT[text_dd.value])
    mo.md(rf"""
    ## Part 2: the computer falls for it too

    Now the computer assembles the **whole** text, using the greedy
    assembler from the first demo: it keeps joining the two pieces with the
    longest overlap. The reads have no errors, and every letter is read
    about 10 times. Each read is **{greedy_read_len(_rep)} letters** long,
    shorter than the longest repeated stretch in this text
    (**{_rep} letters**).

    Press **Sequence and assemble**, watch it work, then press **Compare
    with the original text** to see exactly where it went wrong.
    """)
    return


@app.cell
def _(mo, on_greedy):
    # Bound to a global variable, or marimo ignores its clicks.
    greedy_btn = mo.ui.button(label="🔬 Sequence and assemble",
                              kind="success", on_change=on_greedy)
    greedy_btn
    return


@app.cell
def _(
    ASSEMBLER_HTML,
    compare_html,
    final_pieces,
    get_sim,
    iframe_html,
    json,
    mo,
):
    _a = get_sim()["greedy"]
    if _a is None:
        _out = mo.md("*Press **Sequence and assemble**.*")
    else:
        _data = json.dumps({
            "truth": _a["truth"], "initial": _a["initial"],
            "merges": _a["merges"], "minov": _a["min_ov"],
            "dropped": _a["dropped"], "run": _a["run"],
            "compare": compare_html(
                _a["truth"], final_pieces(_a["initial"], _a["merges"])),
        })
        _out = mo.vstack([
            mo.md(
                f"**{_a['n_reads']} reads** of {_a['read_len']} letters. "
                f"Pieces are joined only if they overlap by at least "
                f"{_a['min_ov']} letters (half a read)."),
            mo.Html(iframe_html(
                ASSEMBLER_HTML.replace("__DATA__", _data.replace("</", "<\\/")),
                height=700)),
        ], gap=0.4)
    _out
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 3: the fix is longer reads

    A read that starts in ordinary text, runs right through the repeated
    words and comes out the other side shows you which way round the text
    goes. So the cure for repeats is **reads longer than the repeats**. There
    is a catch:

    - **Long reads** (made by PacBio and Oxford Nanopore machines): 10,000
      to 100,000 DNA letters or more, but until recently they made a lot of
      mistakes, around 1 letter in 10.
    - **Short reads** (the most common kind, made by Illumina machines):
      about 150 letters long, but very accurate (about 1 mistake in 1,000
      letters), and cheap.

    First sequence the text with **long reads** (300 letters each, 1 letter
    in 10 wrong). The view below works like a genome browser: the original
    text (the genome) on top, then what was assembled, then every read
    lined up where it belongs. Red letters disagree with the original.
    Then **add short reads** and use them to fix the long-read text.
    """)
    return


@app.cell
def _(mo, on_long, on_short):
    # Bound to global variables, or marimo ignores their clicks. This cell
    # never reads the state.
    long_btn = mo.ui.button(label="🔬 Sequence with long reads",
                            kind="success", on_change=on_long)
    short_btn = mo.ui.button(label="✨ Add short reads to fix the text",
                             on_change=on_short)
    show_reads = mo.ui.checkbox(value=True, label="Show every read")
    mo.hstack([long_btn, short_btn, show_reads], justify="start", gap=1,
              wrap=True, align="center")
    return (show_reads,)


@app.cell
def _(compare_to_truth, get_sim, igv_html, mo, show_reads):
    _b = get_sim()["tech"]

    def _card(text, colour):
        return (f'<span style="display:inline-block;border:2px solid {colour};'
                'border-radius:10px;padding:0.3rem 0.7rem;margin:0 0.5rem 0.3rem 0;'
                f'font-family:system-ui,sans-serif;font-weight:700">{text}</span>')

    def _wrong(n):
        return (f"<span style='color:#C44E52'>{n} wrong letter"
                f"{'s' if n != 1 else ''}</span>")

    if _b is None:
        _out = mo.md("*Press **Sequence with long reads**.*")
    else:
        _truth = _b["truth"]
        _lg = _b["long"]
        _rows, _cards = [], []
        _bad_long = _bad_fixed = 0
        for _ci, _c in enumerate(_lg["contigs"]):
            _d, _bad = compare_to_truth(_c["seq"], _truth)
            if _d is None:
                continue
            _bad_long += len(_bad)
            _label = "Long-read text" + (f" {_ci + 1}" if len(_lg["contigs"]) > 1 else "")
            _rows.append(("contig", _label, _d, _c["seq"], None))
            if _b["short"] is not None:
                _fixed = _b["fixed"][_ci]
                _, _fbad = compare_to_truth(_fixed["seq"], _truth)
                _bad_fixed += len(_fbad)
                _changed = {p for p, (x, y) in enumerate(zip(_c["seq"], _fixed["seq"]))
                            if x != y}
                _rows.append(("contig", "Fixed with short reads", _d,
                              _fixed["seq"], _changed))
            if show_reads.value:
                _rows.append(("reads", "Long reads", None,
                              [(_d + off, _lg["reads"][i]) for i, off in _c["reads"]],
                              None))
                if _b["short"] is not None:
                    _rows.append(("reads", "Short reads", None,
                                  [(_d + off, _b["short"]["reads"][i])
                                   for i, off in _b["fixed"][_ci]["placed"]], None))
        _n = len(_lg["contigs"])
        _cards.append(_card(f"Long reads: {_n} piece{'s' if _n != 1 else ''} · "
                            + _wrong(_bad_long), "#8172B3"))
        if _b["short"] is not None:
            _cards.append(_card("After fixing with short reads: "
                                + _wrong(_bad_fixed), "#55A868"))
        _parts = [mo.Html("".join(_cards)),
                  mo.Html(igv_html(_truth, _rows))]
        _parts.append(mo.md(
            "Scroll sideways to follow the text, and down to see all the "
            "reads. Red letters disagree with the original. "
            + ("Green letters in the fixed text are the ones the short reads "
               "corrected." if _b["short"] is not None else
               "Now press **Add short reads to fix the text**.")))
        if _b["short"] is not None:
            _own = [c for c in _b["short"]["contigs"] if c["n_reads"] >= 2]
            _orows = []
            for _c in _own:
                _d, _ = compare_to_truth(_c["seq"], _truth)
                if _d is not None:
                    _orows.append(("contig", "", _d, _c["seq"], None))
            _parts.append(mo.md(
                f"**What if we had used only the short reads?** On their own "
                f"they assemble into **{len(_orows)} separate pieces**, "
                "breaking wherever the text repeats itself, because no short "
                "read reaches across a repeat:"))
            _parts.append(mo.Html(igv_html(_truth, _orows)))
        _out = mo.vstack(_parts, gap=0.5)
    _out
    return


@app.cell
def _(mo):
    mo.accordion({
        "🔎 **What is going on?** (try all three parts first!)": mo.md(r"""
        **Why repeats fool everyone.** Every piece is shorter than the
        repeated words, so a piece that ends in the repeat could carry on
        into *any* of the places where the repeat appears. In the puzzle,
        the pieces fit together in more than one order, and every order uses
        every piece with no clashes and no gaps. Nothing in the pieces
        themselves says which order is right.

        **What the computer does.** The greedy assembler always takes the
        longest overlap. Inside a repeat, the longest overlap is often with
        a piece from a *different* copy of the repeat, so it jumps from one
        copy to another. Whole verses get skipped, or put in the wrong
        order. A careful assembler (Part 3) notices that the pieces disagree
        and stops, giving several correct pieces instead of one wrong one.
        That is why many genome assemblies come in thousands of pieces.

        **Why long reads help.** A read longer than the repeat carries some
        ordinary text on both sides of it, which ties the repeat to its
        neighbours. Long reads used to make many more mistakes, but the
        mistakes are random, so where several reads overlap, the majority
        letter is usually right. Short reads can then fix the rest. Using
        long reads for the order and short reads for the spelling is called
        a **hybrid** assembly. The first truly complete human genome (2022)
        needed long, accurate reads to get through its biggest repeats.

        **Things to try**

        - In Part 2, find the shortest read length that gives one perfect
          piece. How does it compare with the longest repeat?
        - In Part 3, cut the long reads to 2 per letter, then raise them to
          10. What happens to the wrong letters, before and after fixing?
        - Set the long reads' mistakes to 0%. Are long reads now simply
          better?
        """)
    })
    return


@app.cell
def _(
    LONGEST_REPEAT,
    TEXT_BY_TITLE,
    fresh,
    greedy_history,
    greedy_read_len,
    layout_assemble,
    new_puzzle,
    noisy_reads,
    polish_placed,
    rng,
    set_sim,
    shotgun,
):
    GREEDY_COVERAGE = 10
    LONG = (300, 4, 0.10)      # read length, reads per letter, error rate
    SHORT = (40, 20, 0.002)

    def on_text(title):
        set_sim(fresh(TEXT_BY_TITLE[title]))

    def on_new_puzzle(_):
        set_sim(lambda s: {**s, "puzzle": new_puzzle(s["text"])})

    def on_greedy(_):
        # Randomness is drawn here, in the click handler, never in a
        # reactive cell.
        def _update(s):
            truth = s["text"]["passage"]
            read_len = greedy_read_len(len(LONGEST_REPEAT[s["text"]["title"]]))
            n = max(1, round(GREEDY_COVERAGE * len(truth) / read_len))
            reads = shotgun(truth, read_len, n, rng)
            min_ov = max(5, read_len // 2)
            initial, merges, dropped = greedy_history(reads, min_ov, rng)
            old = s["greedy"]
            return {**s, "greedy": {
                "truth": truth, "read_len": read_len, "n_reads": n,
                "min_ov": min_ov, "initial": initial, "merges": merges,
                "dropped": dropped, "run": (old["run"] + 1) if old else 1}}

        set_sim(_update)

    def _run_tech(truth, read_len, coverage, err):
        n = max(1, round(coverage * len(truth) / read_len))
        reads = noisy_reads(truth, read_len, n, err, rng)
        max_mis = min(0.45, 2.5 * err + 0.04)
        contigs = layout_assemble(reads, 8, max(12, read_len // 2), max_mis)
        return {
            "read_len": read_len, "err": err, "n_reads": n, "reads": reads,
            "contigs": [{"seq": c["seq"], "n_reads": len(c["reads"]),
                         "reads": c["reads"]} for c in contigs],
        }

    def on_long(_):
        def _update(s):
            truth = s["text"]["passage"]
            lg = _run_tech(truth, *LONG)
            # Keep only real pieces (two or more reads) for the view.
            lg["contigs"] = [c for c in lg["contigs"] if c["n_reads"] >= 2]
            return {**s, "tech": {"truth": truth, "long": lg, "short": None,
                                  "fixed": None}}

        set_sim(_update)

    def on_short(_):
        def _update(s):
            b = s["tech"]
            if b is None or b["short"] is not None:
                return s
            short = _run_tech(b["truth"], *SHORT)
            fixed = []
            for c in b["long"]["contigs"]:
                seq, placed = polish_placed(c["seq"], short["reads"])
                fixed.append({"seq": seq, "placed": placed})
            return {**s, "tech": {**b, "short": short, "fixed": fixed}}

        set_sim(_update)

    return on_greedy, on_long, on_new_puzzle, on_short, on_text


@app.cell
def _(REPEAT, fresh, mo):
    # One state dict, replaced whole on every change.
    get_sim, set_sim = mo.state(fresh(REPEAT[0]))
    return get_sim, set_sim


@app.cell
def _(html):
    def iframe_html(doc, height):
        """A self-contained page in an iframe, so its script runs. (mo.iframe
        would strip every newline, which breaks JavaScript.) The page resizes
        the iframe to fit its content."""
        return (f'<iframe srcdoc="{html.escape(doc, quote=True)}" '
                f'style="width:100%;height:{height}px;border:0;display:block" '
                'loading="eager"></iframe>')

    # The drag-and-drop puzzle (shared with the first demo). With "alt" in
    # its data it also knows the other way the pieces fit.
    BOARD_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         color: #33302c; background: transparent; }
  .bar { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;
         margin: 0 0 0.5rem; }
  button { font: inherit; font-size: 0.85rem; padding: 0.3rem 0.75rem;
           border-radius: 6px; border: 1px solid #cfc8bd; background: #fff;
           cursor: pointer; }
  button:hover { border-color: #6b4f9e; }
  #ws { position: relative; overflow: auto; border: 1px solid #e4e0d8;
        border-radius: 10px; background: #fbfaf8; height: 430px; }
  #inner { position: relative; }
  .tile { position: absolute; display: flex; cursor: grab; user-select: none;
          touch-action: none; border-radius: 5px; background: #fff;
          border: 1px solid #b9b1a5; border-left-width: 5px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
  .tile.drag { cursor: grabbing; box-shadow: 0 6px 16px rgba(0,0,0,0.25);
               z-index: 10; opacity: 0.95; }
  .tile.glued { box-shadow: 0 0 0 2px #55A868, 0 1px 3px rgba(0,0,0,0.15); }
  .tile.drag.glued { box-shadow: 0 0 0 2px #55A868, 0 6px 16px rgba(0,0,0,0.25); }
  .tile.pop { animation: pop 0.35s ease-out; }
  @keyframes pop { 0% { transform: scale(1); } 40% { transform: scale(1.06); }
                   100% { transform: scale(1); } }
  @media (prefers-reduced-motion: reduce) { .tile.pop { animation: none; } }
  .lab { position: absolute; left: -20px; top: 4px; width: 16px;
         font-size: 11px; font-weight: 800; color: #9a938a; text-align: right; }
  .ch { display: inline-block; text-align: center;
        font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
        font-size: 15px; }
  .ch.sp { color: #c9c2b8; }
  .ch.ok { background: #cdebd3; }
  .ch.bad { background: #f6c6c7; color: #a01e24; font-weight: 800; }
  #cons { position: absolute; display: flex; }
  #cons .ch { border-bottom: 2px solid #33302c; font-weight: 700; }
  #cons .gap { background: repeating-linear-gradient(45deg, #f6c6c7 0 3px,
               #fff 3px 6px); border-bottom-color: #C44E52; }
  #cons .bad { color: #a01e24; }
  #conslab { position: absolute; font-size: 11px; font-weight: 800;
             color: #7a7382; text-transform: uppercase; letter-spacing: 0.06em; }
  #status { margin-top: 0.5rem; padding: 0.55rem 0.8rem; border-radius: 8px;
            background: #f4f1ec; font-size: 0.92rem; }
  #status.win { background: #dff3e3; border: 1px solid #9fd4ab; }
  #status.near { background: #fdf0d8; border: 1px solid #ecd09a; }
  #status.fail { background: #fbe1e1; border: 1px solid #e9a5a7; }
  .cmp { display: flex; gap: 0.5rem; margin: 0.5rem 0; background: #fff;
         border: 1px solid #e4e0d8; border-radius: 8px; padding: 0.4rem 0.6rem; }
  .cmplab div { font-size: 0.75rem; font-weight: 800; color: #7a7382;
                height: 22px; line-height: 22px; white-space: nowrap; }
  .cmpscroll { overflow-x: auto; flex: 1; min-width: 0; }
  .cmpscroll div { white-space: pre; height: 22px; line-height: 22px;
                   font-family: ui-monospace, Consolas, monospace; width: max-content; }
  .cmpscroll .sp { color: #cbc4ba; }
  .dif { background: #f6c6c7; color: #a01e24; font-weight: 800; }
  .gapc { background: repeating-linear-gradient(45deg, #eee9e1 0 2px, #fff 2px 4px); }
</style></head>
<body>
<div class="bar">
  <button id="shuffle">🔀 Shuffle the pieces</button>
  <button id="giveup" style="display:none">🏳 Give up: show me the answer</button>
  <button id="hint">💡 Hint: place one piece</button>
  <span id="hintcount" style="font-size:0.85rem;color:#7a7382"></span>
</div>
<div id="ws"><div id="inner"></div></div>
<div id="status"></div>
<script>
(function () {
  var D = __DATA__;
  var truth = D.truth, reads = D.reads, n = reads.length;
  var CW = 12, RH = 32, TH = 26, PADL = 28, PADT = 10;
  var ROWS = n + 2;
  var COLS = 2 * truth.length + 10;
  var MINOV = 4;      /* letters two pieces must share before they stick */
  var SNAP = 3;       /* how many columns a drop may be nudged to fit */
  var PAL = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
             "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"];
  var inner = document.getElementById("inner");
  var ws = document.getElementById("ws");
  var status = document.getElementById("status");
  var note = document.getElementById("hintcount");
  inner.style.width = (PADL + COLS * CW + 20) + "px";
  inner.style.height = (PADT + (ROWS + 1) * RH + 24) + "px";
  ws.style.height = Math.min(470, PADT + (ROWS + 1) * RH + 40) + "px";
  inner.style.backgroundImage =
    "repeating-linear-gradient(90deg, transparent 0 " + (CW - 1) +
    "px, rgba(0,0,0,0.035) " + (CW - 1) + "px " + CW + "px)";
  inner.style.backgroundPosition = PADL + "px 0";

  var pos = [], hints = 0, drag = null, current = "", gaveUp = false;
  var glue = {};      /* glue[i][j] = true when pieces i and j are stuck */
  for (var g0 = 0; g0 < n; g0++) glue[g0] = {};

  var tiles = reads.map(function (r, i) {
    var t = document.createElement("div");
    t.className = "tile";
    t.style.borderLeftColor = PAL[i % PAL.length];
    t.title = "Drag to move. Double-click to pull this piece off its group.";
    var lab = document.createElement("span");
    lab.className = "lab";
    lab.textContent = r.id;
    t.appendChild(lab);
    for (var k = 0; k < r.seq.length; k++) {
      var s = document.createElement("span");
      var ch = r.seq.charAt(k);
      s.className = "ch" + (ch === " " ? " sp" : "");
      s.textContent = ch === " " ? "·" : ch;
      s.style.width = CW + "px";
      s.style.height = TH + "px";
      s.style.lineHeight = TH + "px";
      t.appendChild(s);
    }
    inner.appendChild(t);
    return t;
  });
  var consLab = document.createElement("div");
  consLab.id = "conslab";
  consLab.textContent = "Your text";
  inner.appendChild(consLab);
  var cons = document.createElement("div");
  cons.id = "cons";
  inner.appendChild(cons);

  function len(i) { return reads[i].seq.length; }
  function draw(i) {
    tiles[i].style.left = (PADL + pos[i].col * CW) + "px";
    tiles[i].style.top = (PADT + pos[i].row * RH) + "px";
  }

  /* ---- groups of stuck-together pieces ---- */
  function groupOf(i) {
    var seen = {}, stack = [i], out = [];
    seen[i] = true;
    while (stack.length) {
      var a = stack.pop();
      out.push(a);
      for (var b in glue[a]) {
        b = Number(b);
        if (!seen[b]) { seen[b] = true; stack.push(b); }
      }
    }
    return out;
  }
  function unglue(i) {
    for (var b in glue[i]) delete glue[b][i];
    glue[i] = {};
  }
  function showGlue() {
    for (var i = 0; i < n; i++) {
      tiles[i].classList.toggle("glued", Object.keys(glue[i]).length > 0);
    }
  }

  /* How piece i (if it sat at column ci) overlaps piece j where j is now:
     the number of shared columns, and whether every shared letter agrees. */
  function overlap(i, ci, j) {
    var a = Math.max(ci, pos[j].col);
    var b = Math.min(ci + len(i), pos[j].col + len(j));
    var ok = true;
    for (var c = a; c < b; c++) {
      if (reads[i].seq.charAt(c - ci) !== reads[j].seq.charAt(c - pos[j].col)) {
        ok = false;
        break;
      }
    }
    return {n: Math.max(0, b - a), ok: ok};
  }
  function clashFree(members) {
    for (var x = 0; x < members.length; x++) {
      for (var y = x + 1; y < members.length; y++) {
        var o = overlap(members[x], pos[members[x]].col, members[y]);
        if (o.n > 0 && !o.ok) return false;
      }
    }
    return true;
  }

  /* Would the group, shifted by (dc, dr) from `from`, sit on top of any
     other piece in the same row, or off the board? */
  function blocked(grp, from, dc, dr) {
    var inGrp = {};
    grp.forEach(function (g) { inGrp[g] = true; });
    for (var x = 0; x < grp.length; x++) {
      var g = grp[x], c = from[g].col + dc, r = from[g].row + dr;
      if (c < 0 || c + len(g) > COLS || r < 0 || r >= ROWS) return true;
      for (var j = 0; j < n; j++) {
        if (inGrp[j] || pos[j].row !== r) continue;
        if (c < pos[j].col + len(j) && pos[j].col < c + len(g)) return true;
      }
    }
    return false;
  }
  function snapshot(grp) {
    var from = {};
    grp.forEach(function (g) { from[g] = {col: pos[g].col, row: pos[g].row}; });
    return from;
  }
  /* Move a group as one, by (dc, dr), choosing the nearest free rows. */
  function moveGroup(grp, from, dc, dr) {
    var minC = Infinity, maxC = -Infinity, minR = Infinity, maxR = -Infinity;
    grp.forEach(function (g) {
      minC = Math.min(minC, from[g].col);
      maxC = Math.max(maxC, from[g].col + len(g));
      minR = Math.min(minR, from[g].row);
      maxR = Math.max(maxR, from[g].row);
    });
    dc = Math.max(-minC, Math.min(COLS - maxC, dc));
    dr = Math.max(-minR, Math.min(ROWS - 1 - maxR, dr));
    var chosen = null;
    for (var d = 0; d <= ROWS && chosen === null; d++) {
      var tries = [dr + d, dr - d];
      for (var q = 0; q < 2; q++) {
        if (!blocked(grp, from, dc, tries[q])) { chosen = tries[q]; break; }
      }
    }
    if (chosen === null) chosen = dr;
    grp.forEach(function (g) {
      pos[g] = {col: from[g].col + dc, row: from[g].row + chosen};
      draw(g);
    });
  }

  /* After a drop: nudge the group a few columns if that makes it overlap
     another piece perfectly, then stick together everything that overlaps
     by at least MINOV agreeing letters. */
  function snapAndStick(grp) {
    var inGrp = {};
    grp.forEach(function (g) { inGrp[g] = true; });
    var best = null;
    grp.forEach(function (g) {
      for (var o = 0; o < n; o++) {
        if (inGrp[o]) continue;
        for (var s = -SNAP; s <= SNAP; s++) {
          var ov = overlap(g, pos[g].col + s, o);
          if (ov.n >= MINOV && ov.ok &&
              (!best || Math.abs(s) < Math.abs(best.s) ||
               (Math.abs(s) === Math.abs(best.s) && ov.n > best.n))) {
            best = {s: s, n: ov.n};
          }
        }
      }
    });
    if (best && best.s !== 0) {
      var from = snapshot(grp);
      if (!blocked(grp, from, best.s, 0)) {
        grp.forEach(function (g) { pos[g].col += best.s; draw(g); });
      }
    }
    var stuck = 0;
    grp.forEach(function (g) {
      for (var o = 0; o < n; o++) {
        if (inGrp[o] || glue[g][o]) continue;
        var ov = overlap(g, pos[g].col, o);
        if (ov.n < MINOV || !ov.ok) continue;
        var merged = groupOf(g).concat(groupOf(o));
        if (!clashFree(merged)) continue;
        glue[g][o] = glue[o][g] = true;
        stuck++;
        merged.forEach(function (m) { inGrp[m] = true; });
      }
    });
    if (stuck) {
      grp.forEach(function (g) {
        tiles[g].classList.remove("pop");
        void tiles[g].offsetWidth;
        tiles[g].classList.add("pop");
      });
    }
    showGlue();
  }

  function shuffle() {
    for (var i = 0; i < n; i++) glue[i] = {};
    pos = reads.map(function (r, i) {
      var span = Math.max(1, truth.length - len(i));
      return {col: Math.floor(Math.random() * span), row: i};
    });
    for (var j = 0; j < n; j++) draw(j);
    showGlue();
    evaluate();
  }

  function evaluate() {
    var cols = {}, minC = Infinity, maxC = -Infinity;
    for (var i = 0; i < n; i++) {
      for (var k = 0; k < len(i); k++) {
        var c = pos[i].col + k;
        (cols[c] = cols[c] || []).push([i, k]);
        tiles[i].children[k + 1].classList.remove("ok", "bad");
      }
      minC = Math.min(minC, pos[i].col);
      maxC = Math.max(maxC, pos[i].col + len(i) - 1);
    }
    var text = "", clashes = 0, gaps = 0, html = [];
    for (var c = minC; c <= maxC; c++) {
      var e = cols[c];
      if (!e) {
        gaps++;
        text += "\u0000";
        html.push('<span class="ch gap" style="width:' + CW + 'px;height:' +
                  TH + 'px"></span>');
        continue;
      }
      var first = reads[e[0][0]].seq.charAt(e[0][1]);
      var same = e.every(function (x) {
        return reads[x[0]].seq.charAt(x[1]) === first;
      });
      if (e.length > 1) {
        e.forEach(function (x) {
          tiles[x[0]].children[x[1] + 1].classList.add(same ? "ok" : "bad");
        });
      }
      if (!same) clashes++;
      text += same ? first : "\u0001";
      var shown = !same ? "?" : (first === " " ? "·" : first);
      shown = shown.replace(/&/g, "&amp;").replace(/</g, "&lt;");
      html.push('<span class="ch' + (same ? (first === " " ? " sp" : "") : " bad") +
                '" style="width:' + CW + 'px;height:' + TH + 'px;line-height:' +
                TH + 'px">' + shown + "</span>");
    }
    cons.innerHTML = html.join("");
    current = text;
    var y = PADT + ROWS * RH + 14;
    cons.style.left = (PADL + minC * CW) + "px";
    cons.style.top = y + "px";
    consLab.style.left = (PADL + minC * CW) + "px";
    consLab.style.top = (y - 14) + "px";

    var groups = 0, seen = {};
    for (var g = 0; g < n; g++) {
      if (seen[g]) continue;
      groups++;
      groupOf(g).forEach(function (m) { seen[m] = true; });
    }

    if (gaveUp) { gu.click(); return; }
    status.className = "";
    var alt = D.alt || null;
    if (!clashes && !gaps && text === truth) {
      if (alt) {
        status.className = "near";
        status.innerHTML = "\ud83c\udf89 <b>That's the original text!</b> " +
          "<b>But here is the catch:</b> the very same pieces also fit together like " +
          "this, using every piece, with no clashes and no gaps:" +
          compare(alt, truth, "Also fits", "Original") +
          "Without already knowing the original, you could not have told which " +
          "one is right. Neither could a computer.";
      } else {
        status.className = "win";
        status.innerHTML = "\ud83c\udf89 <b>That's the original text. You have assembled a genome!</b> " +
          (hints ? "(with " + hints + " hint" + (hints > 1 ? "s" : "") + ")" : "(with no hints!)") +
          " " + (D.next || "");
      }
    } else if (!clashes && !gaps && alt && text === alt) {
      status.className = "fail";
      status.innerHTML = "\u274c <b>It reads perfectly well, it uses every piece, and " +
        "there are no clashes or gaps. But it is not the original text!</b> " +
        "Here are yours and the original, with the differences highlighted:" +
        compare(text, truth, "Yours", "Original") +
        "You did nothing wrong. The pieces really do fit both ways: the repeated " +
        "words are longer than any piece, so no piece reaches across them to show " +
        "which way round the text goes.";
    } else if (!clashes && !gaps) {
      status.className = "near";
      status.innerHTML = "One unbroken line of text with no clashes, but it is <b>not</b> the " +
        "original. Either some pieces just sit end to end without overlapping, " +
        "or two pieces stuck together on a short match that happened by chance (like " +
        "<code>\u00b7the\u00b7</code>). Double-click a piece to pull it off." +
        (alt ? compare(text, truth, "Yours", "Original") : "");
    } else {
      status.innerHTML = "<b>" + groups + "</b> separate piece" + (groups === 1 ? "" : "s") +
        " or stuck-together group" + (groups === 1 ? "" : "s") + ", <b>" + clashes +
        "</b> clashing column" + (clashes === 1 ? "" : "s") + " and <b>" + gaps +
        "</b> gap" + (gaps === 1 ? "" : "s") + ". Keep going!";
    }
    fit();
  }

  /* Two texts one above the other. Letters are lined up by a longest-common-
     subsequence alignment, so one missing word does not make everything after
     it look wrong. Red in the top row: not in the original (or in the wrong
     place). Red in the bottom row: missing from the top row. */
  function compare(a, b, la, lb) {
    var n1 = a.length, n2 = b.length, i, j;
    var T = [];
    for (i = 0; i <= n1; i++) { T.push(new Array(n2 + 1).fill(0)); }
    for (i = n1 - 1; i >= 0; i--) {
      for (j = n2 - 1; j >= 0; j--) {
        T[i][j] = a.charAt(i) === b.charAt(j) ? T[i + 1][j + 1] + 1 :
                  Math.max(T[i + 1][j], T[i][j + 1]);
      }
    }
    var top = [], bot = [];
    function show(ch) {
      if (ch === " ") return "\u00b7";
      if (ch === "\u0000") return "_";
      if (ch === "\u0001") return "?";
      return ch.replace(/&/g, "&amp;").replace(/</g, "&lt;");
    }
    function cellOf(ch, cls) {
      return '<span class="' + cls + (ch === " " && !cls ? "sp" : "") + '">' + show(ch) + "</span>";
    }
    i = 0; j = 0;
    while (i < n1 || j < n2) {
      if (i < n1 && j < n2 && a.charAt(i) === b.charAt(j)) {
        top.push(cellOf(a.charAt(i), "")); bot.push(cellOf(b.charAt(j), ""));
        i++; j++;
      } else if (j >= n2 || (i < n1 && T[i + 1][j] >= T[i][j + 1])) {
        top.push(cellOf(a.charAt(i), "dif")); bot.push('<span class="gapc"> </span>');
        i++;
      } else {
        top.push('<span class="gapc"> </span>'); bot.push(cellOf(b.charAt(j), "dif"));
        j++;
      }
    }
    return '<div class="cmp"><div class="cmplab"><div>' + la + "</div><div>" + lb +
           '</div></div><div class="cmpscroll"><div>' + top.join("") + "</div><div>" +
           bot.join("") + "</div></div></div>";
  }
  function fit() {
    if (window.frameElement) {
      window.frameElement.style.height = (document.documentElement.scrollHeight + 4) + "px";
    }
  }

  tiles.forEach(function (t, i) {
    t.addEventListener("pointerdown", function (ev) {
      if (ev.button !== undefined && ev.button !== 0) return;
      ev.preventDefault();
      t.setPointerCapture(ev.pointerId);
      var grp = groupOf(i);
      drag = {i: i, grp: grp, from: snapshot(grp), x0: ev.clientX, y0: ev.clientY,
              dx: 0, dy: 0};
      grp.forEach(function (g) { tiles[g].classList.add("drag"); });
    });
    t.addEventListener("pointermove", function (ev) {
      if (!drag || drag.i !== i) return;
      drag.dx = ev.clientX - drag.x0;
      drag.dy = ev.clientY - drag.y0;
      drag.grp.forEach(function (g) {
        tiles[g].style.left = (PADL + drag.from[g].col * CW + drag.dx) + "px";
        tiles[g].style.top = (PADT + drag.from[g].row * RH + drag.dy) + "px";
      });
    });
    function drop() {
      if (!drag || drag.i !== i) return;
      var d = drag;
      drag = null;
      d.grp.forEach(function (g) { tiles[g].classList.remove("drag"); });
      moveGroup(d.grp, d.from, Math.round(d.dx / CW), Math.round(d.dy / RH));
      snapAndStick(d.grp);
      evaluate();
    }
    t.addEventListener("pointerup", drop);
    t.addEventListener("pointercancel", drop);
    t.addEventListener("dblclick", function () {
      if (!Object.keys(glue[i]).length) return;
      unglue(i);
      moveGroup([i], snapshot([i]), 0, 1);
      showGlue();
      note.textContent = "Pulled piece " + reads[i].id + " off its group.";
      evaluate();
    });
  });

  document.getElementById("shuffle").addEventListener("click", function () {
    hints = 0;
    gaveUp = false;
    note.textContent = "";
    shuffle();
  });
  document.getElementById("hint").addEventListener("click", function () {
    var order = reads.map(function (r, i) { return i; });
    order.sort(function (a, b) { return reads[a].start - reads[b].start; });
    for (var q = 1; q < order.length; q++) {
      var a = order[q - 1], b = order[q];
      var want = pos[a].col + reads[b].start - reads[a].start;
      if (pos[b].col === want) continue;
      /* A piece stuck in the wrong place has to come off first. */
      if (groupOf(b).indexOf(a) >= 0) unglue(b);
      var mover = b, target = want, row = pos[a].row + 1;
      if (want + len(b) > COLS) {
        mover = a;
        target = pos[b].col - (reads[b].start - reads[a].start);
        row = pos[b].row - 1;
      }
      var grp = groupOf(mover);
      moveGroup(grp, snapshot(grp), target - pos[mover].col, row - pos[mover].row);
      snapAndStick(grp);
      hints++;
      note.textContent = "Placed piece " + reads[b].id + " after piece " + reads[a].id + ".";
      evaluate();
      return;
    }
    note.textContent = "Every piece is already in place!";
  });

  var gu = document.getElementById("giveup");
  if (D.giveup) gu.style.display = "";
  gu.addEventListener("click", function () {
    gaveUp = true;
    status.className = "fail";
    status.innerHTML = "<b>Here is the answer.</b> The top row is what your pieces " +
      "spell out right now (<b>_</b> = a gap, <b>?</b> = a clash); the bottom row is the " +
      "original text. Red letters are where they differ:" +
      compare(current, truth, "Yours", "Original") +
      (D.alt ? "And here is a <b>different</b> order that also uses every piece with no " +
       "gaps or clashes. Did you build this one?" + compare(D.alt, truth, "Also fits", "Original") +
       "The repeated words are longer than any piece, so the pieces alone cannot " +
       "say which order is right." : "");
    fit();
  });

  shuffle();
})();
</script>
</body></html>
"""

    # The greedy assembler, animated (shared with the first demo).
    ASSEMBLER_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         color: #33302c; background: transparent; font-size: 14px; }
  .bar { display: flex; gap: 0.45rem; align-items: center; flex-wrap: wrap;
         margin: 0 0 0.5rem; }
  button { font: inherit; font-size: 0.85rem; padding: 0.3rem 0.7rem;
           border-radius: 6px; border: 1px solid #cfc8bd; background: #fff;
           cursor: pointer; }
  button:hover { border-color: #6b4f9e; }
  button.primary { background: #55A868; border-color: #55A868; color: #fff;
                   font-weight: 700; }
  button:disabled { opacity: 0.45; cursor: default; }
  select { font: inherit; font-size: 0.85rem; }
  label { font-size: 0.85rem; color: #5b554d; }
  #msg { min-height: 2.4em; padding: 0.5rem 0.75rem; border-radius: 8px;
         background: #f4f1ec; margin-bottom: 0.5rem; line-height: 1.5; }
  #msg.bad { background: #fbe1e1; border: 1px solid #e9a5a7; }
  #msg.done { background: #dff3e3; border: 1px solid #9fd4ab; }
  #msg code { background: #f3d36b; padding: 0 3px; border-radius: 3px;
              font-family: ui-monospace, Consolas, monospace; white-space: pre; }
  #cmp:empty { display: none; }
  #cmp { margin-top: 0.6rem; }
  #wrap { position: relative; overflow: auto; max-height: 520px;
          border: 1px solid #e4e0d8; border-radius: 10px; background: #fbfaf8; }
  #board { position: relative; }
  .piece { position: absolute; left: 0; top: 0; background: #fff;
           border: 1px solid #d9d4cc; border-radius: 5px; padding: 2px 0 4px;
           transition: transform 0.6s ease, opacity 0.4s ease; }
  .piece.active { border-color: #e6b800; box-shadow: 0 0 0 2px #f3d36b; z-index: 5; }
  .piece.fresh { border-color: #55A868; box-shadow: 0 0 0 2px #a8d8b4; }
  .piece.wrong { border-color: #C44E52; box-shadow: 0 0 0 2px #f2b8b9; }
  .piece.wrong.fresh { box-shadow: 0 0 0 3px #e98b8d; }
  .seq { white-space: pre; display: flex; height: 20px; line-height: 20px;
         font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
         font-size: 14px; }
  .c { display: inline-block; text-align: center; flex: none; }
  .c.sp { color: #cbc4ba; }
  .c.ov { background: #f3d36b; color: #33302c; }
  .bars { position: relative; }
  .rb { position: absolute; height: 3px; border-radius: 2px; opacity: 0.85; }
  .legend { font-size: 0.8rem; color: #7a7382; margin-top: 0.35rem; }
  @media (prefers-reduced-motion: reduce) { .piece { transition: none; } }
</style></head>
<body>
<div class="bar">
  <button id="step" class="primary">▶ Next join</button>
  <button id="play">⏵ Play</button>
  <button id="finish">⏭ Finish</button>
  <button id="restart">↺ Start again</button>
  <label>Speed <select id="speed">
    <option value="2">slow</option>
    <option value="1" selected>normal</option>
    <option value="0">fast (no animation)</option>
  </select></label>
  <button id="compare">🔍 Compare with the original text</button>
</div>
<div id="msg"></div>
<div id="wrap"><div id="board"></div></div>
<div id="cmp"></div>
<div class="legend">Each white box is one piece: its letters on top, and a thin
  coloured line under them for every read it is built from.
  <span style="background:#f3d36b;padding:0 3px">Yellow</span> = the overlap
  being joined. <span id="wronglegend" style="display:none">A
  <b style="color:#C44E52">red outline</b> = this piece is <b>not</b> in the
  original text: the assembler joined things that do not belong together.</span>
</div>
<script>
(function () {
  var D = __DATA__;
  var truth = D.truth, merges = D.merges;
  var CW = 11, PAD = 10, GAP = 7, BAR = 4;
  var PAL = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
             "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"];
  var board = document.getElementById("board");
  var wrap = document.getElementById("wrap");
  var msg = document.getElementById("msg");
  var pieces, order, t, playing = false, busy = false, last = null;

  function speed() { return Number(document.getElementById("speed").value); }
  var revealed = false;
  function checking() { return revealed; }
  function esc(ch) {
    return ch === "&" ? "&amp;" : ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch;
  }
  function dots(s) { return esc(s).split(" ").join("·"); }

  /* The widest any piece will ever get, so the board never needs to grow. */
  (function () {
    var lens = {}, widest = 0;
    D.initial.forEach(function (p) { lens[p.id] = p.seq.length; widest = Math.max(widest, p.seq.length); });
    merges.forEach(function (m) {
      lens[m.new] = lens[m.l] + lens[m.r] - m.k;
      widest = Math.max(widest, lens[m.new], lens[m.l] - m.k + lens[m.r]);
    });
    board.style.width = (2 * PAD + widest * CW + 20) + "px";
  })();

  function makePiece(id, seq, reads) {
    var el = document.createElement("div");
    el.className = "piece";
    var s = document.createElement("div");
    s.className = "seq";
    var html = [];
    for (var i = 0; i < seq.length; i++) {
      var ch = seq.charAt(i);
      html.push('<span class="c' + (ch === " " ? " sp" : "") + '" style="width:' +
                CW + 'px">' + (ch === " " ? "·" : esc(ch)) + "</span>");
    }
    s.innerHTML = html.join("");
    var bars = document.createElement("div");
    bars.className = "bars";
    var ends = [];
    reads.slice().sort(function (a, b) { return a.off - b.off; }).forEach(function (r) {
      var row = 0;
      while (row < ends.length && ends[row] > r.off) row++;
      ends[row] = r.off + r.len;
      var b = document.createElement("div");
      b.className = "rb";
      b.style.left = (r.off * CW + 1) + "px";
      b.style.width = Math.max(r.len * CW - 2, 2) + "px";
      b.style.top = (row * BAR + 2) + "px";
      b.style.background = PAL[r.c % PAL.length];
      bars.appendChild(b);
    });
    bars.style.height = (ends.length * BAR + 2) + "px";
    el.style.width = (seq.length * CW) + "px";
    el.appendChild(s);
    el.appendChild(bars);
    board.appendChild(el);
    return {id: id, seq: seq, reads: reads, el: el, h: 20 + ends.length * BAR + 10, x: PAD, y: PAD};
  }
  function put(p, x, y, animate) {
    p.x = x;
    p.y = y;
    if (!animate) p.el.style.transition = "none";
    p.el.style.transform = "translate(" + x + "px," + y + "px)";
    if (!animate) { void p.el.offsetWidth; p.el.style.transition = ""; }
  }
  function layout(animate) {
    var y = PAD;
    order.forEach(function (id) {
      put(pieces[id], PAD, y, animate);
      y += pieces[id].h + GAP;
    });
    board.style.height = (y + PAD + 40) + "px";
  }
  function markWrong() {
    var on = checking();
    document.getElementById("wronglegend").style.display = on ? "inline" : "none";
    order.forEach(function (id) {
      pieces[id].el.classList.toggle("wrong", on && truth.indexOf(pieces[id].seq) < 0);
    });
  }
  function setMsg(html, cls) { msg.innerHTML = html; msg.className = cls || ""; }
  function buttons() {
    var left = t < merges.length;
    document.getElementById("step").disabled = !left || busy;
    document.getElementById("finish").disabled = !left;
    document.getElementById("play").disabled = !left;
    document.getElementById("play").textContent = playing ? "⏸ Pause" : "⏵ Play";
  }

  function init() {
    playing = false;
    revealed = false;
    document.getElementById("cmp").innerHTML = "";
    busy = false;
    last = null;
    board.innerHTML = "";
    pieces = {};
    order = [];
    D.initial.forEach(function (p) {
      pieces[p.id] = makePiece(p.id, p.seq, [{off: 0, len: p.seq.length, c: p.id}]);
      order.push(p.id);
    });
    t = 0;
    layout(false);
    markWrong();
    wrap.scrollTop = 0;
    wrap.scrollLeft = 0;
    if (typeof fit === "function") setTimeout(fit, 0);
    setMsg("<b>" + D.initial.length + " pieces</b> to start with: every read, in no " +
           "particular order" + (D.dropped ? " (" + D.dropped + " reads that were " +
           "duplicates, or sat wholly inside another read, were set aside)" : "") +
           ". The assembler will make <b>" + merges.length + "</b> joins. Press " +
           "<b>Next join</b> to watch one at a time, or <b>Play</b>.");
    buttons();
  }

  function finishedMsg() {
    var longest = 0, wrong = 0;
    order.forEach(function (id) {
      longest = Math.max(longest, pieces[id].seq.length);
      if (truth.indexOf(pieces[id].seq) < 0) wrong++;
    });
    var s = "<b>Finished.</b> No two pieces overlap by " + D.minov + " or more letters, " +
            "so the assembler stops with <b>" + order.length + "</b> piece" +
            (order.length === 1 ? "" : "s") + " (the original is " + truth.length +
            " letters; the longest piece is " + longest + ").";
    if (checking()) {
      if (order.length === 1 && pieces[order[0]].seq === truth) {
        setMsg(s + " 🎉 It is exactly the original text.", "done");
        return;
      }
      s += " <b>" + wrong + "</b> piece" + (wrong === 1 ? " is" : "s are") +
           " not in the original (red).";
    }
    setMsg(s, checking() && wrong ? "bad" : "done");
  }

  /* Apply merge number t. With animate, it plays out in three beats:
     highlight the overlap, slide the right piece under the left one, fuse. */
  function doMerge(mode, done) {
    var animate = mode === "animate", shown = mode === "animate" || mode === "instant";
    var m = merges[t];
    var L = pieces[m.l], R = pieces[m.r];
    var shift = L.seq.length - m.k;
    var seq = L.seq + R.seq.slice(m.k);
    var reads = L.reads.concat(R.reads.map(function (r) {
      return {off: r.off + shift, len: r.len, c: r.c};
    }));
    m.gone.forEach(function (g) {
      var at = seq.indexOf(pieces[g].seq);
      if (at >= 0) {
        reads = reads.concat(pieces[g].reads.map(function (r) {
          return {off: r.off + at, len: r.len, c: r.c};
        }));
      }
    });
    if (last && pieces[last]) {
      pieces[last].el.classList.remove("fresh");
      var old = pieces[last].el.querySelectorAll(".ov");
      for (var i = 0; i < old.length; i++) old[i].classList.remove("ov");
    }

    function fuse() {
      var x = L.x, y = L.y;
      [m.l, m.r].concat(m.gone).forEach(function (id) {
        if (pieces[id]) { board.removeChild(pieces[id].el); delete pieces[id]; }
      });
      var N = makePiece(m.new, seq, reads);
      pieces[m.new] = N;
      put(N, x, y, false);
      order = order.filter(function (id) { return id !== m.r && m.gone.indexOf(id) < 0; })
                   .map(function (id) { return id === m.l ? m.new : id; });
      t++;
      last = m.new;
      if (shown) {
        N.el.classList.add("fresh");
        var cs = N.el.querySelector(".seq").children;
        for (var j = shift; j < shift + m.k; j++) cs[j].classList.add("ov");
        layout(animate);
        wrap.scrollTop = Math.max(0, N.y - 30);
        wrap.scrollLeft = Math.max(0, PAD + shift * CW - wrap.clientWidth / 2);
        markWrong();
        var bad = checking() && truth.indexOf(seq) < 0;
        var shared = dots(L.seq.slice(shift));
        var text = "<b>Join " + t + " of " + merges.length + ":</b> the two pieces with " +
                   "the longest overlap shared <b>" + m.k + "</b> letters " +
                   "(<code>" + shared + "</code>), so they were joined into one piece of " +
                   seq.length + " letters.";
        if (bad) {
          text += " <b>⚠ This piece is not in the original!</b> The overlap " +
                  "matched, but these pieces come from different places in the text.";
        }
        setMsg(text, bad ? "bad" : "");
        if (t === merges.length) finishedMsg();
      }
      if (done) done();
    }

    if (!animate) { fuse(); return; }
    var sp = speed();
    L.el.classList.add("active");
    R.el.classList.add("active");
    var lc = L.el.querySelector(".seq").children, rc = R.el.querySelector(".seq").children;
    for (var a = shift; a < L.seq.length; a++) lc[a].classList.add("ov");
    for (var b = 0; b < m.k; b++) rc[b].classList.add("ov");
    wrap.scrollTop = Math.max(0, L.y - 30);
    wrap.scrollLeft = Math.max(0, PAD + shift * CW - wrap.clientWidth / 2);
    setMsg("<b>Join " + (t + 1) + " of " + merges.length + ":</b> looking for the two " +
           "pieces with the <b>longest</b> overlap… these share <b>" + m.k +
           "</b> letters: <code>" + dots(L.seq.slice(shift)) + "</code>");
    setTimeout(function () {
      R.el.style.zIndex = 6;
      put(R, PAD + shift * CW, L.y + L.h + 2, true);
      setTimeout(fuse, 750 * sp);
    }, 1000 * sp);
  }

  function step() {
    if (busy || t >= merges.length) return;
    busy = true;
    buttons();
    doMerge(speed() > 0 ? "animate" : "instant", function () {
      busy = false;
      buttons();
      if (playing) {
        if (t < merges.length) setTimeout(step, speed() > 0 ? 350 * speed() : 120);
        else { playing = false; buttons(); }
      }
    });
  }

  document.getElementById("step").addEventListener("click", function () {
    playing = false;
    step();
  });
  document.getElementById("play").addEventListener("click", function () {
    playing = !playing;
    buttons();
    if (playing && !busy) step();
  });
  document.getElementById("finish").addEventListener("click", function () {
    playing = false;
    var go = function () {
      while (t < merges.length) doMerge(false);
      layout(true);
      markWrong();
      finishedMsg();
      buttons();
    };
    if (busy) {
      var wait = setInterval(function () {
        if (!busy) { clearInterval(wait); go(); }
      }, 50);
    } else {
      go();
    }
  });
  document.getElementById("restart").addEventListener("click", init);
  document.getElementById("compare").addEventListener("click", function () {
    playing = false;
    var go = function () {
      while (t < merges.length) doMerge(false);
      revealed = true;
      layout(false);
      markWrong();
      finishedMsg();
      buttons();
      document.getElementById("cmp").innerHTML = D.compare || "";
      document.getElementById("cmp").scrollIntoView({block: "start", behavior: "smooth"});
      fit();
    };
    if (busy) {
      var wait = setInterval(function () {
        if (!busy) { clearInterval(wait); go(); }
      }, 50);
    } else {
      go();
    }
  });
  function fit() {
    if (window.frameElement) {
      window.frameElement.style.height = (document.documentElement.scrollHeight + 6) + "px";
    }
  }

  init();
})();
</script>
</body></html>
"""
    return ASSEMBLER_HTML, BOARD_HTML, iframe_html


@app.cell
def _(html):
    # Sequences are shown one unbroken line per row in a single horizontally
    # scrolling box (students find wrapped alignment blocks confusing).
    SEQ_CSS = """
    <style>
    .l7-box { display: flex; gap: 0.6rem; background: #fbfaf8;
      border: 1px solid #e4e0d8; border-radius: 10px; padding: 0.6rem 0.8rem;
      overflow-y: auto; }
    .l7-lab { font-family: system-ui, sans-serif; font-size: 0.78rem;
      font-weight: 700; color: #7a7382; white-space: nowrap;
      height: 26px; line-height: 26px; }
    .l7-scroll { overflow-x: auto; flex: 1 1 auto; min-width: 0;
      font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
      font-size: 0.95rem; padding-bottom: 0.3rem; }
    .l7-line { white-space: pre; color: #33302c; width: max-content;
      height: 26px; line-height: 26px; }
    .l7-faint { color: #9a938a; }
    .l7-box .sp { color: #cbc4ba; }
    .l7-box .rep { background: #fbe1c4; }
    .l7-box .segA { background: #d6e4f5; }
    .l7-box .segB { background: #f8d7b5; }
    .l7-box .bad { background: #C44E52; color: #fff; font-weight: 800;
      border-radius: 2px; }
    </style>
    """

    def seq_html(seq, marks=None):
        """One sequence as HTML: spaces as faint dots, optional per-position
        CSS classes in `marks`."""
        out = []
        for i, ch in enumerate(seq):
            cls = marks.get(i) if marks else None
            if ch == " ":
                cls = f"{cls} sp" if cls else "sp"
                disp = "·"
            else:
                disp = html.escape(ch)
            out.append(f'<span class="{cls}">{disp}</span>' if cls else disp)
        return "".join(out)

    def seq_box(rows, max_height=None):
        """rows: (label, inner html[, extra css class]). Labels sit outside the
        scrolling area, so they stay put while the sequences scroll."""
        labels, lines = [], []
        for row in rows:
            label, inner = row[0], row[1]
            extra = row[2] if len(row) > 2 else ""
            labels.append(f'<div class="l7-lab {extra}">{html.escape(label)}</div>')
            lines.append(f'<div class="l7-line {extra}">{inner}</div>')
        style = f' style="max-height:{max_height}px"' if max_height else ""
        return (SEQ_CSS + f'<div class="l7-box"{style}><div>{"".join(labels)}'
                f'</div><div class="l7-scroll">{"".join(lines)}</div></div>')

    return seq_box, seq_html


@app.cell
def _(longest_repeat, other_texts, re):
    def tile(text, rng, read_len):
        """Cut text into reads that tile it end to end with random overlaps.
        Returns ([(read, start)], the smallest overlap used)."""
        n = len(text)
        lo = max(3, min(8, read_len // 3))
        hi = max(lo, min(13, read_len // 2))
        starts = [0]
        while starts[-1] + read_len < n:
            starts.append(min(starts[-1] + read_len - int(rng.integers(lo, hi + 1)),
                              n - read_len))
        return [(text[s:s + read_len], s) for s in starts], lo

    def other_order(window, reads, lo):
        """Another text, as long as the window, that uses every piece and
        leaves no gaps: the pieces fit together this way too."""
        for k in range(lo, 3, -1):
            for alt in other_texts(window, k):
                if len(alt) != len(window) or alt == window:
                    continue
                covered = [False] * len(alt)
                fits = True
                for r, _ in reads:
                    p = alt.find(r)
                    if p < 0:
                        fits = False
                        break
                    while p != -1:
                        for q in range(p, p + len(r)):
                            covered[q] = True
                        p = alt.find(r, p + 1)
                if fits and all(covered):
                    return alt
        return None

    def windows(text, tidy, shortest=100, longest=230):
        """Stretches of the text, each with a piece length just shorter than
        its longest repeat. With tidy, stretches start and end at
        punctuation, so the puzzle reads as whole phrases."""
        if tidy:
            starts = [0] + [m.end() for m in re.finditer(r"[.!?;,]\s+", text)]
            ends = [m.end() for m in re.finditer(r"[.!?;,](?=\s|$)", text)]
        else:
            starts = [0] + [m.end() for m in re.finditer(r"\s+", text)]
            ends = [m.start() for m in re.finditer(r"\s", text)] + [len(text)]
        for a in starts:
            for e in ends:
                if not shortest <= e - a <= longest:
                    continue
                w = text[a:e]
                rep = longest_repeat(w)
                if len(rep) >= 10:
                    yield w, min(24, len(rep) - 1)

    def repeat_puzzle(text, rng):
        """A short puzzle from the text whose pieces fit together in more
        than one order. Falls back to an ordinary puzzle if the text has no
        long enough repeat."""
        candidates = [c for tidy in (True, False) for c in windows(text, tidy)]
        for w, read_len in candidates[:400]:
            for _ in range(3):
                reads, lo = tile(w, rng, read_len)
                if len(set(r for r, _ in reads)) != len(reads):
                    continue
                alt = other_order(w, reads, lo)
                if alt:
                    return w, reads, alt
        w = text[:text.rfind(" ", 0, 140)] if len(text) > 140 else text
        reads, _ = tile(w, rng, 24)
        return w, reads, None

    return (repeat_puzzle,)


@app.cell
def _():
    def unitig_walk(text, k):
        """Split the text at every point where its k-letter words could
        continue in more than one way. Returns (the distinct stretches, the
        order the text passes through them). Neighbouring stretches share
        k-1 letters."""
        kmers = [text[i:i + k] for i in range(len(text) - k + 1)]
        outs, ins = {}, {}
        for km in set(kmers):
            outs.setdefault(km[:-1], set()).add(km[1:])
            ins.setdefault(km[1:], set()).add(km[:-1])

        def branching(node):
            return len(outs.get(node, ())) != 1 or len(ins.get(node, ())) != 1

        chunks, cur = [], [kmers[0]]
        for km in kmers[1:]:
            if branching(km[:-1]):
                chunks.append(cur)
                cur = [km]
            else:
                cur.append(km)
        chunks.append(cur)
        stretches, walk, index = [], [], {}
        for ch in chunks:
            s = ch[0] + "".join(km[-1] for km in ch[1:])
            if s not in index:
                index[s] = len(stretches)
                stretches.append(s)
            walk.append(index[s])
        return stretches, walk

    def other_texts(text, k, limit=30, budget=100000):
        """Other texts built from exactly the same stretches, used the same
        number of times, joined at the same places, but in a different
        order. Iterative, because browsers allow only shallow recursion."""
        if k >= len(text):
            return []
        units, walk = unitig_walk(text, k)

        def spell(path):
            out = units[path[0]]
            for u in path[1:]:
                out += units[u][k - 1:]
            return out

        steps = {}
        for a, b in zip(walk, walk[1:]):
            steps[(a, b)] = steps.get((a, b), 0) + 1
        succ = {}
        for a, b in sorted(steps):
            succ.setdefault(a, []).append(b)
        n_steps, end = len(walk) - 1, walk[-1]
        found, seen = [], {text}
        path, stack, work = [walk[0]], [0], 0
        while stack and work < budget and len(found) < limit:
            work += 1
            node, i = path[-1], stack[-1]
            if len(path) - 1 == n_steps:
                if node == end:
                    t = spell(path)
                    if t not in seen:
                        seen.add(t)
                        found.append(t)
                i = len(succ.get(node, ()))
            nbrs = succ.get(node, ())
            while i < len(nbrs) and steps[(node, nbrs[i])] == 0:
                i += 1
            if i < len(nbrs):
                stack[-1] = i + 1
                steps[(node, nbrs[i])] -= 1
                path.append(nbrs[i])
                stack.append(0)
            else:
                stack.pop()
                path.pop()
                if path:
                    steps[(path[-1], node)] += 1
        return found

    return (other_texts,)


@app.cell
def _():
    def trim_words(text, n):
        """The first ~n characters of text, cut back to a word boundary."""
        if len(text) <= n:
            return text
        cut = text.rfind(" ", 0, n)
        return text[: cut if cut > 0 else n].rstrip()

    def suffix_prefix_overlap(a, b, min_len):
        """Longest k >= min_len with the last k characters of a equal to the
        first k of b. k stays shorter than both, so neither is swallowed."""
        if min_len < 1 or min_len >= min(len(a), len(b)):
            return 0
        seed = b[:min_len]
        p = a.find(seed, max(1, len(a) - len(b) + 1))
        while p != -1:
            if b.startswith(a[p:]):
                return len(a) - p   # smallest p first = the longest overlap
            p = a.find(seed, p + 1)
        return 0

    def drop_contained(seqs):
        """Remove duplicates and any string lying inside a longer one."""
        out = []
        for s in sorted(set(seqs), key=len, reverse=True):
            if not any(s in t for t in out):
                out.append(s)
        return out

    def greedy_history(reads, min_len, rng=None):
        """Greedy assembly: repeatedly join the two pieces with the longest
        overlap. Returns (initial pieces, the joins in order, how many reads
        were set aside as duplicates or contained), for the page to replay.
        Each join is {"l", "r", "k", "new", "gone"}: piece l's end overlaps
        piece r's start by k letters, making piece new; pieces in gone were
        swallowed whole by the join (it happens in repeats)."""
        base = drop_contained(reads)
        if rng is not None:
            base = [base[i] for i in rng.permutation(len(base)).tolist()]
        pieces = dict(enumerate(base))
        initial = [{"id": i, "seq": s} for i, s in pieces.items()]
        nxt = len(pieces)
        ov = {}
        for i in pieces:
            for j in pieces:
                if i != j:
                    k = suffix_prefix_overlap(pieces[i], pieces[j], min_len)
                    if k:
                        ov[(i, j)] = k
        merges = []
        while ov:
            (i, j), k = max(ov.items(),
                            key=lambda kv: (kv[1], -kv[0][0], -kv[0][1]))
            left, right = pieces.pop(i), pieces.pop(j)
            merged = left + right[k:]
            gone = [c for c, s in pieces.items() if s in merged]
            for c in gone:
                del pieces[c]
            dead = {i, j, *gone}
            ov = {p: v for p, v in ov.items()
                  if p[0] not in dead and p[1] not in dead}
            new = nxt
            nxt += 1
            pieces[new] = merged
            merges.append({"l": i, "r": j, "k": k, "new": new, "gone": gone})
            for c, s in pieces.items():
                if c == new:
                    continue
                k1 = suffix_prefix_overlap(merged, s, min_len)
                if k1:
                    ov[(new, c)] = k1
                k2 = suffix_prefix_overlap(s, merged, min_len)
                if k2:
                    ov[(c, new)] = k2
        return initial, merges, len(reads) - len(base)

    def final_pieces(initial, merges):
        """Replay the joins: the pieces the assembler ends with."""
        pieces = {p["id"]: p["seq"] for p in initial}
        for m in merges:
            seq = pieces[m["l"]] + pieces[m["r"]][m["k"]:]
            for c in [m["l"], m["r"], *m["gone"]]:
                del pieces[c]
            pieces[m["new"]] = seq
        return list(pieces.values())

    def greedy_assemble(reads, min_len):
        """The pieces the greedy assembler ends with."""
        initial, merges, _ = greedy_history(reads, min_len)
        return final_pieces(initial, merges)

    def compare_html(truth, pieces):
        """What the assembler made, against the original text, as HTML.

        Each piece is split into the fewest chunks that each appear, letter
        for letter, in the original. A piece made of one chunk is correct; a
        boundary between two chunks is a wrong join, where the assembler
        stuck together text that is not neighbouring in the original. Any
        stretch of the original not in a correct chunk is missing."""
        import html as _h

        def chunks(seq):
            out, i = [], 0
            while i < len(seq):
                lo, hi = 1, len(seq) - i
                while lo < hi:
                    mid = (lo + hi + 1) // 2
                    if seq[i:i + mid] in truth:
                        lo = mid
                    else:
                        hi = mid - 1
                out.append(seq[i:i + lo])
                i += lo
            return out

        def place(chunk, near):
            hits, q = [], truth.find(chunk)
            while q != -1:
                hits.append(q)
                q = truth.find(chunk, q + 1)
            if near is None:
                return hits[0]
            return min(hits, key=lambda h: abs(h - near))

        mapped = []
        for seq in pieces:
            parts, near = [], None
            for c in chunks(seq):
                at = place(c, near)
                parts.append((c, at))
                near = at + len(c)
            mapped.append(parts)
        mapped.sort(key=lambda parts: parts[0][1])

        covered = [False] * len(truth)
        joins = 0
        top = []
        for n, parts in enumerate(mapped, 1):
            top.append(f'<span class="cp-brk">Piece {n}</span>')
            for j, (c, at) in enumerate(parts):
                for q in range(at, at + len(c)):
                    covered[q] = True
                if j:
                    joins += 1
                    top.append('<span class="cp-jump">⚠ wrong join</span>')
                cls = "" if len(parts) == 1 else (
                    "cp-a" if j % 2 == 0 else "cp-b")
                txt = _h.escape(c)
                top.append(f'<span class="{cls}">{txt}</span>' if cls else txt)
            top.append("<br>")
        bot, i, missing = [], 0, 0
        while i < len(truth):
            j = i
            while j < len(truth) and covered[j] == covered[i]:
                j += 1
            txt = _h.escape(truth[i:j])
            if covered[i]:
                bot.append(txt)
            else:
                missing += j - i
                bot.append(f'<del class="cp-miss">{txt}</del>')
            i = j
        if len(pieces) == 1 and pieces[0] == truth:
            verdict = "🎉 <b>Perfect:</b> one piece, exactly the original text."
        else:
            plural = lambda k: "" if k == 1 else "s"  # noqa: E731
            verdict = (
                f"The assembler made <b>{len(pieces)}</b> piece"
                f"{plural(len(pieces))}, with <b>{joins}</b> wrong join"
                f"{plural(joins)} (<span class='cp-jump'>⚠</span>: two bits of "
                "text stuck together that are not next to each other in the "
                f"original). <b>{missing}</b> letter{plural(missing)} of the "
                "original are missing from the assembly "
                "(<del class='cp-miss'>crossed out</del>).")
            if not joins and len(pieces) > 1:
                verdict += (" No wrong joins this time, but the text is still in "
                            "pieces: wherever the pieces could carry on in more "
                            "than one way, or nothing was read, the assembler "
                            "could not join them.")
        return f"""
        <style>
        .cp-wrap {{ font-family: system-ui, sans-serif; }}
        .cp-h {{ font-weight: 800; font-size: 0.8rem; text-transform: uppercase;
          letter-spacing: 0.05em; color: #7a7382; margin: 0.7rem 0 0.2rem; }}
        .cp-text {{ font-family: Georgia, "Times New Roman", serif;
          font-size: 1rem; line-height: 1.9; background: #fff;
          border: 1px solid #e4e0d8; border-radius: 8px;
          padding: 0.5rem 0.8rem; }}
        .cp-a {{ background: #e3e0f5; border-radius: 2px; }}
        .cp-b {{ background: #fbe3cc; border-radius: 2px; }}
        .cp-jump {{ display: inline-block; font: 800 0.72rem system-ui, sans-serif;
          color: #fff; background: #C44E52; border-radius: 4px;
          padding: 0 0.35rem; margin: 0 0.25rem; }}
        .cp-miss {{ background: #fbe1e1; color: #a01e24; }}
        .cp-brk {{ display: inline-block; font: 700 0.72rem system-ui, sans-serif;
          color: #fff; background: #7a7382; border-radius: 4px;
          padding: 0 0.35rem; margin-right: 0.35rem; }}
        .cp-verdict {{ padding: 0.5rem 0.75rem; border-radius: 8px;
          background: #f4f1ec; line-height: 1.6; }}
        </style>
        <div class="cp-wrap">
          <div class="cp-verdict">{verdict}</div>
          <div class="cp-h">What the assembler made</div>
          <div class="cp-text">{"".join(top)}</div>
          <div class="cp-h">The original text</div>
          <div class="cp-text">{"".join(bot)}</div>
        </div>"""

    def shotgun(text, read_len, n_reads, rng):
        """Reads from random places. A read may hang off either end of the
        text (and is clipped there), so the ends get read as often as the
        middle; at least half of every read lies inside the text."""
        read_len = min(read_len, len(text))
        keep = (read_len + 1) // 2
        starts = rng.integers(keep - read_len, len(text) - keep + 1,
                              size=n_reads)
        return [text[max(0, s):s + read_len] for s in starts.tolist()]

    def make_puzzle(sentence, rng, read_len=24, tries=200):
        """Cut a sentence into reads that tile it end to end, overlapping by
        8-13 characters, such that joining by longest overlap rebuilds it.
        Returns [(read, start)] in shuffled order."""
        n = len(sentence)
        read_len = min(read_len, max(12, n // 3))
        lo = min(8, read_len // 3)
        hi = max(lo, min(13, read_len // 2))
        best = None
        for _ in range(tries):
            starts = [0]
            while starts[-1] + read_len < n:
                step = read_len - int(rng.integers(lo, hi + 1))
                starts.append(min(starts[-1] + step, n - read_len))
            reads = [sentence[s:s + read_len] for s in starts]
            if len(set(reads)) != len(reads):
                continue
            best = best or list(zip(reads, starts))
            if greedy_assemble(reads, 4) == [sentence]:
                best = list(zip(reads, starts))
                break
        order = rng.permutation(len(best)).tolist()
        return [best[i] for i in order]

    return (
        compare_html,
        final_pieces,
        greedy_history,
        make_puzzle,
        shotgun,
        trim_words,
    )

@app.cell
def _(candidate_offsets, mismatch_rate):
    def polish_placed(contig, short_reads, k=10, max_mis=0.15):
        """Fix a noisy piece by majority vote of the short reads that fit it,
        and say where each short read went (for the genome view). A read from
        a repeat fits every copy equally well, and the copies really are the
        same text, so it votes at every place it fits; it is drawn at the
        place it fits best."""
        counts = [dict() for _ in contig]
        placed = []
        for i, r in enumerate(short_reads):
            best = None
            for d in sorted(candidate_offsets(contig, r, k)):
                mis, n = mismatch_rate(contig, r, d)
                if n < len(r) * 0.8 or mis > max_mis:
                    continue
                for p, ch in enumerate(r):
                    q = d + p
                    if 0 <= q < len(contig):
                        counts[q][ch] = counts[q].get(ch, 0) + 1
                if best is None or mis < best[0]:
                    best = (mis, d)
            if best is not None:
                placed.append((i, best[1]))
        fixed = "".join(
            max(col.items(), key=lambda kv: kv[1])[0]
            if sum(col.values()) >= 2 else ch
            for ch, col in zip(contig, counts))
        return fixed, placed

    return (polish_placed,)


@app.cell
def _(html):
    def igv_html(truth, rows):
        """A genome-browser style view, one letter per column: the genome
        (the original text) on top, then each row placed at its position.
        rows: ("contig", label, start, seq, changed) or ("reads", label, None,
        [(start, seq)], None); reads are packed into as few lines as fit."""
        L = len(truth)

        def line(items, cls_ok, changed=None):
            cells = [" "] * L
            for start, seq in items:
                for p, ch in enumerate(seq):
                    q = start + p
                    if not 0 <= q < L:
                        continue
                    shown = "·" if ch == " " else html.escape(ch)
                    if ch != truth[q]:
                        cls = "ig-x"
                    elif changed and p in changed:
                        cls = "ig-fix"
                    else:
                        cls = cls_ok if ch != " " else cls_ok + " ig-sp"
                    cells[q] = f'<span class="{cls}">{shown}</span>'
            return "".join(cells)

        ruler = [" "] * L
        for p in range(9, L, 10):
            for j, dch in enumerate(str(p + 1)):
                if p + j < L:
                    ruler[p + j] = dch
        out = [("", "".join(ruler), "ig-ruler"),
               ("Genome", line([(0, truth)], "ig-g"), "ig-genome")]
        for kind, label, start, data, changed in rows:
            if kind == "contig":
                out.append((label, line([(start, data)], "ig-c", changed),
                            "ig-contig"))
            else:
                lanes, ends = [], []
                for st, seq in sorted(data, key=lambda x: x[0]):
                    for k, e in enumerate(ends):
                        if e < st:
                            ends[k] = st + len(seq)
                            lanes[k].append((st, seq))
                            break
                    else:
                        ends.append(st + len(seq))
                        lanes.append([(st, seq)])
                for k, lane in enumerate(lanes):
                    out.append((label if k == 0 else "", line(lane, "ig-r"),
                                "ig-read"))
        labels = "".join(f'<div class="ig-lab {c}">{html.escape(l)}</div>'
                         for l, _, c in out)
        lines = "".join(f'<div class="ig-line {c}">{t}</div>' for _, t, c in out)
        return f"""
        <style>
        .ig-box {{ display: flex; gap: 0.6rem; background: #fbfaf8;
          border: 1px solid #e4e0d8; border-radius: 10px; padding: 0.5rem 0.8rem;
          max-height: 520px; overflow-y: auto; }}
        .ig-lab {{ font: 700 0.72rem system-ui, sans-serif; color: #7a7382;
          white-space: nowrap; height: 17px; line-height: 17px; }}
        .ig-scroll {{ overflow-x: auto; flex: 1 1 auto; min-width: 0;
          font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
          font-size: 13px; padding-bottom: 0.3rem; }}
        .ig-line {{ white-space: pre; width: max-content; height: 17px;
          line-height: 17px; color: #b5aea4; }}
        .ig-genome, .ig-contig {{ height: 22px; line-height: 22px; }}
        .ig-genome {{ border-bottom: 2px solid #33302c; margin-bottom: 4px; }}
        .ig-contig {{ margin-top: 4px; }}
        .ig-ruler {{ color: #a8a198; font-size: 11px; }}
        .ig-g {{ color: #23201c; font-weight: 800; }}
        .ig-c {{ color: #33302c; font-weight: 700; background: #e8eef8; }}
        .ig-r {{ color: #9a938a; }}
        .ig-sp {{ color: #d0c9bf; }}
        .ig-x {{ background: #f6c6c7; color: #a01e24; font-weight: 800; }}
        .ig-fix {{ background: #bfe6c8; color: #1f6b33; font-weight: 800; }}
        </style>
        <div class="ig-box"><div>{labels}</div>
          <div class="ig-scroll">{lines}</div></div>"""

    return (igv_html,)


@app.cell
def _(np):
    ALPHABET = "abcdefghijklmnopqrstuvwxyz "

    def noisy_reads(text, read_len, n_reads, err, rng):
        """Reads from random places with random letter substitutions. Reads
        may hang off either end of the text and are clipped there."""
        read_len = min(read_len, len(text))
        keep = (read_len + 1) // 2
        starts = rng.integers(keep - read_len, len(text) - keep + 1,
                              size=n_reads).tolist()
        reads = []
        for s in starts:
            r = list(text[max(0, s):s + read_len])
            for h in np.flatnonzero(rng.random(len(r)) < err).tolist():
                choices = [c for c in ALPHABET if c != r[h].lower()]
                r[h] = choices[int(rng.integers(len(choices)))]
            reads.append("".join(r))
        return reads

    def mismatch_rate(a, b, d):
        """b placed with b[0] under a[d]. Returns (fraction of mismatches over
        the overlap, overlap length)."""
        lo, hi = max(0, d), min(len(a), d + len(b))
        n = hi - lo
        if n <= 0:
            return 1.0, 0
        x = np.frombuffer(a[lo:hi].encode("utf-32-le"), dtype=np.uint32)
        y = np.frombuffer(b[lo - d:hi - d].encode("utf-32-le"), dtype=np.uint32)
        return float(np.mean(x != y)), n

    def find_overlaps(reads, k, min_ov, max_mis):
        """Seed and extend: shared k-mers propose how two reads line up, then
        the whole overlap is checked. Returns {(i, j): (d, n)}: read j starts
        d >= 0 letters after read i, overlapping it by n letters."""
        index = {}
        for r, s in enumerate(reads):
            for p in range(len(s) - k + 1):
                index.setdefault(s[p:p + k], []).append((r, p))
        votes = {}
        for hits in index.values():
            if len(hits) > 60:            # a k-mer that is everywhere
                continue
            for a in range(len(hits)):
                ra, pa = hits[a]
                for b in range(a + 1, len(hits)):
                    rb, pb = hits[b]
                    if ra == rb:
                        continue
                    d = pa - pb
                    key = (ra, rb, d) if d >= 0 else (rb, ra, -d)
                    votes[key] = votes.get(key, 0) + 1
        out = {}
        for (i, j, d), v in votes.items():
            if v < 2:
                continue
            mis, n = mismatch_rate(reads[i], reads[j], d)
            if n >= min_ov and mis <= max_mis:
                if (i, j) not in out or n > out[(i, j)][1]:
                    out[(i, j)] = (d, n)
        return out

    def consensus(reads, placed):
        length = max(off + len(reads[r]) for r, off in placed)
        counts = [dict() for _ in range(length)]
        for r, off in placed:
            for p, ch in enumerate(reads[r]):
                col = counts[off + p]
                col[ch] = col.get(ch, 0) + 1
        return "".join(max(c.items(), key=lambda kv: kv[1])[0] for c in counts)

    def layout_assemble(reads, k, min_ov, max_mis):
        """A cautious assembler for reads with errors.

        Each read is linked to the read overlapping its right end the most,
        but only if all the reads overlapping that end agree with one another
        (inside a repeat they do not), and only if the link is mutual. Chains
        of links become pieces, spelled out by majority vote.
        """
        n = len(reads)
        ov = find_overlaps(reads, k, min_ov, max_mis)
        contained = set()
        for (i, j), (d, m) in ov.items():
            if d + len(reads[j]) <= len(reads[i]):
                contained.add(j)
            elif d == 0:
                contained.add(i)
        right = {i: [] for i in range(n)}
        left = {i: [] for i in range(n)}
        for (i, j), (d, m) in ov.items():
            if i in contained or j in contained or d == 0:
                continue
            right[i].append((d, j))
            left[j].append((d, i))

        def consistent(cands, on_right):
            for x in range(len(cands)):
                for y in range(x + 1, len(cands)):
                    (d1, r1), (d2, r2) = cands[x], cands[y]
                    rel = (d2 - d1) if on_right else (d1 - d2)
                    a, b = (r1, r2) if rel >= 0 else (r2, r1)
                    mis, m = mismatch_rate(reads[a], reads[b], abs(rel))
                    if m == 0 or mis > max_mis:
                        return False
            return True

        best_right, best_left = {}, {}
        for i in range(n):
            if right[i] and consistent(right[i], True):
                best_right[i] = min(right[i])   # smallest offset = biggest overlap
            if left[i] and consistent(left[i], False):
                best_left[i] = min(left[i])
        nxt = {}
        for i, (d, j) in best_right.items():
            if best_left.get(j, (None, None))[1] == i:
                nxt[i] = (j, d)
        has_prev = {j for j, _ in nxt.values()}
        chains = []
        for i in range(n):
            if i in contained or i in has_prev:
                continue
            chain, pos, cur, seen = [(i, 0)], 0, i, {i}
            while cur in nxt and nxt[cur][0] not in seen:
                j, d = nxt[cur]
                pos += d
                chain.append((j, pos))
                seen.add(j)
                cur = j
            chains.append(chain)
        # Reads lying inside another read add depth to its piece.
        where = {r: (c, off) for c, ch in enumerate(chains) for r, off in ch}
        for (i, j), (d, m) in ov.items():
            if j in contained and i in where and j not in where:
                c, off = where[i]
                chains[c].append((j, off + d))
                where[j] = (c, off + d)
        out = [{"seq": consensus(reads, ch), "reads": ch} for ch in chains]
        out.sort(key=lambda c: -len(c["seq"]))
        return out

    def place_on(target, read, k):
        """Offset where `read` best sits on `target`, by k-mer votes."""
        votes = {}
        for p in range(len(read) - k + 1):
            km = read[p:p + k]
            q = target.find(km)
            while q != -1:
                votes[q - p] = votes.get(q - p, 0) + 1
                q = target.find(km, q + 1)
        if not votes:
            return None
        return max(votes.items(), key=lambda kv: kv[1])[0]

    def candidate_offsets(target, read, k):
        offs = set()
        for p in range(0, len(read) - k + 1, 2):
            km = read[p:p + k]
            q = target.find(km)
            while q != -1:
                offs.add(q - p)
                q = target.find(km, q + 1)
        return offs

    def polish(contig, short_reads, k=10, max_mis=0.15):
        """Fix a noisy piece by majority vote of the short reads that fit it.
        A read from a repeat fits every copy equally well, and the copies
        really are the same text, so it votes at every place it fits."""
        counts = [dict() for _ in contig]
        for r in short_reads:
            for d in candidate_offsets(contig, r, k):
                mis, n = mismatch_rate(contig, r, d)
                if n < len(r) * 0.8 or mis > max_mis:
                    continue
                for p, ch in enumerate(r):
                    q = d + p
                    if 0 <= q < len(contig):
                        counts[q][ch] = counts[q].get(ch, 0) + 1
        return "".join(
            max(col.items(), key=lambda kv: kv[1])[0]
            if sum(col.values()) >= 2 else ch
            for ch, col in zip(contig, counts))

    def compare_to_truth(seq, truth, k=12):
        """Line seq up on the truth. Returns (offset, positions in seq that
        differ), or (None, None) if it cannot be placed."""
        d = place_on(truth, seq, min(k, len(seq)))
        if d is None:
            return None, None
        bad = [p for p, ch in enumerate(seq)
               if not (0 <= d + p < len(truth)) or truth[d + p] != ch]
        return d, bad

    return (
        candidate_offsets,
        compare_to_truth,
        layout_assemble,
        mismatch_rate,
        noisy_reads,
        polish,
    )


@app.cell
def _(TEXTS, repeat_puzzle, rng):
    REPEAT = [t for t in TEXTS if t["kind"] == "repeat"]
    TEXT_BY_TITLE = {t["title"]: t for t in REPEAT}
    MAX_SHORT_READ = 160
    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def new_puzzle(text):
        window, reads, alt = repeat_puzzle(text["passage"], rng)
        order = rng.permutation(len(reads)).tolist()
        return {
            "truth": window, "alt": alt,
            "reads": [{"id": LETTERS[i % 26], "seq": reads[j][0],
                       "start": reads[j][1]} for i, j in enumerate(order)],
        }

    def fresh(text):
        return {"text": text, "puzzle": new_puzzle(text), "greedy": None,
                "tech": None}

    def greedy_read_len(longest):
        """Reads a little shorter than the longest repeat, so it fools the
        assembler."""
        return max(12, min(30, longest - 6))

    return MAX_SHORT_READ, REPEAT, TEXT_BY_TITLE, fresh, greedy_read_len, new_puzzle


@app.cell
def _(TEXTS):
    def longest_repeat(text):
        """Longest stretch occurring at least twice."""
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

    _rep = [t for t in TEXTS if t["kind"] == "repeat"]
    LONGEST_REPEAT = {t["title"]: longest_repeat(t["passage"]) for t in _rep}
    return LONGEST_REPEAT, longest_repeat


@app.cell
def _():
    import html
    import json
    import re

    import marimo as mo
    import numpy as np

    # Deliberately unseeded: every student gets their own reads.
    rng = np.random.default_rng()

    # >>> TEXTS (generated from texts.txt - do not edit) >>>
    TEXTS = [{'title': 'On the Origin of Species',
      'kind': 'general',
      'puzzle': 'There is grandeur in this view of life, with its several '
                'powers, having been originally breathed into a few forms or '
                'into one.',
      'variants': [('bank', 'band'),
                   ('kinds', 'kings'),
                   ('birds', 'bards'),
                   ('bushes', 'pushes'),
                   ('worms', 'words'),
                   ('damp', 'camp'),
                   ('forms', 'firms'),
                   ('plants', 'planes')],
      'passage': 'It is interesting to contemplate an entangled bank, clothed '
                 'with many plants of many kinds, with birds singing on the '
                 'bushes, with various insects flitting about, and with worms '
                 'crawling through the damp earth, and to reflect that these '
                 'elaborately constructed forms, so different from each '
                 'other, and dependent on each other in so complex a manner, '
                 'have all been produced by laws acting around us. These '
                 'laws, taken in the highest sense, being Growth with '
                 'Reproduction; Inheritance which is almost implied by '
                 'reproduction; Variability from the indirect and direct '
                 'action of the external conditions of life, and from use and '
                 'disuse; a Ratio of Increase so high as to lead to a '
                 'Struggle for Life, and as a consequence to Natural '
                 'Selection, entailing Divergence of Character and the '
                 'Extinction of less-improved forms. Thus, from the war of '
                 'nature, from famine and death, the most exalted object '
                 'which we are capable of conceiving, namely, the production '
                 'of the higher animals, directly follows. There is grandeur '
                 'in this view of life, with its several powers, having been '
                 'originally breathed into a few forms or into one; and that, '
                 'whilst this planet has gone cycling on according to the '
                 'fixed law of gravity, from so simple a beginning endless '
                 'forms most beautiful and most wonderful have been, and are '
                 'being, evolved.'},
     {'title': 'Star Wars',
      'kind': 'general',
      'puzzle': "Pursued by the Empire's sinister agents, Princess Leia races "
                'home aboard her starship, custodian of the stolen plans that '
                'can save her people and restore freedom to the galaxy....',
      'variants': [('civil', 'cavil'),
                   ('war', 'bar'),
                   ('from', 'frog'),
                   ('base', 'bare'),
                   ('won', 'win'),
                   ('battle', 'bottle'),
                   ('spies', 'skies'),
                   ('steal', 'steel'),
                   ('plans', 'plant')],
      'passage': 'It is a period of civil war. Rebel spaceships, striking '
                 'from a hidden base, have won their first victory against '
                 'the evil Galactic Empire. During the battle, Rebel spies '
                 "managed to steal secret plans to the Empire's ultimate "
                 'weapon, the DEATH STAR, an armored space station with '
                 'enough power to destroy an entire planet. Pursued by the '
                 "Empire's sinister agents, Princess Leia races home aboard "
                 'her starship, custodian of the stolen plans that can save '
                 'her people and restore freedom to the galaxy....'},
     {'title': 'The First Human Genome Paper',
      'kind': 'general',
      'puzzle': 'The human genome holds an extraordinary trove of information '
                'about human development, physiology, medicine and evolution.',
      'variants': [('holds', 'folds'),
                   ('trove', 'grove'),
                   ('about', 'above'),
                   ('report', 'resort'),
                   ('make', 'made'),
                   ('draft', 'drift')],
      'passage': 'The human genome holds an extraordinary trove of '
                 'information about human development, physiology, medicine '
                 'and evolution. Here we report the results of an '
                 'international collaboration to produce and make freely '
                 'available a draft sequence of the human genome. We also '
                 'present an initial analysis of the data, describing some of '
                 'the insights that can be gleaned from the sequence. The '
                 "rediscovery of Mendel's laws of heredity in the opening "
                 'weeks of the 20th century sparked a scientific quest to '
                 'understand the nature and content of genetic information '
                 'that has propelled biology for the last hundred years. The '
                 'scientific progress made falls naturally into four main '
                 'phases, corresponding roughly to the four quarters of the '
                 'century. The first established the cellular basis of '
                 'heredity: the chromosomes. The second defined the molecular '
                 'basis of heredity: the DNA double helix. The third unlocked '
                 'the informational basis of heredity, with the discovery of '
                 'the biological mechanism by which cells read the '
                 'information contained in genes and with the invention of '
                 'the recombinant DNA technologies of cloning and sequencing '
                 'by which scientists can do the same.'},
     {'title': 'Pink Pony Inn',
      'kind': 'repeat',
      'puzzle': '',
      'variants': [],
      'passage': 'I have these wicked dreams of leaving Annecy Oh Saint '
                 'Cecelia, I swear she calleth me Shan’t make my mother '
                 'proud, the thought is too obscene To see her darling girl, '
                 'I know that she shall scream Lord, what hast thou done? '
                 'Thou’rt a pink pony maid Thou shouldst be a nun Oh mother, '
                 'I just want to run With the mummers and clowns ‘Tis where I '
                 'belong, down at the Pink Pony Inn, I shall keep on dancing '
                 'at the Pink Pony Inn, I shall keep on dancing, let them '
                 'Call it a sin, I shall keep on dancing at the Pink Pony '
                 'Inn, Pink Pony Inn Barefoot, I spin upon the floor Ale and '
                 'mead aplenty, and a sign above the door Firelight, and a '
                 'boar’s head on the wall Every night a new reminder why I '
                 'left it all'},
     {'title': 'Galileo Figaro',
      'kind': 'repeat',
      'puzzle': '',
      'variants': [],
      'passage': 'I see a little silhouetto of a man Scaramouche, '
                 'Scaramouche, will you do the Fandango? Thunderbolt and '
                 'lightning, very, very frightening me Galileo Galileo '
                 "Galileo Galileo Galileo Figaro, magnifico But I'm just a "
                 "poor boy, nobody loves me He's just a poor boy from a poor "
                 'family Spare him his life from this monstrosity Easy come, '
                 'easy go, will you let me go? No, we will not let you go, '
                 'let him go We will not let you go, let him go We will not '
                 'let you go, let me go Will not let you go, let me go Will '
                 'not let you go never, never, never, never let me go No, no, '
                 'no, no, no, no, no Oh, mamma mia, mamma mia Mamma mia, let '
                 'me go'},
     {'title': 'Tell Me What You Want',
      'kind': 'repeat',
      'puzzle': '',
      'variants': [],
      'passage': "Yo, I'll tell you what I want, what I really, really want "
                 "So tell me what you want, what you really, really want I'll "
                 'tell you what I want, what I really, really want So tell me '
                 'what you want, what you really, really want I wanna, (ha) I '
                 'wanna, (ha) I wanna, (ha) I wanna, (ha) I wanna really, '
                 'really, really wanna zigazig ah If you want my future, '
                 'forget my past If you wanna get with me, better make it '
                 "fast Now don't go wasting my precious time Get your act "
                 "together we could be just fine I'll tell you what I want, "
                 'what I really, really want So tell me what you want, what '
                 'you really, really want I wanna, (ha) I wanna, (ha) I '
                 'wanna, (ha) I wanna, (ha) I wanna really, really, really '
                 'wanna zigazig ah If you wanna be my lover, you gotta get '
                 'with my friends (Gotta get with my friends) Make it last '
                 'forever, friendship never ends If you wanna be my lover, '
                 "you have got to give Taking is too easy, but that's the way "
                 'it is'}]
    # <<< TEXTS <<<
    return TEXTS, html, json, mo, np, re, rng


if __name__ == "__main__":
    app.run()
