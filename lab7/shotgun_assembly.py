import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🧩 Putting the Pieces Back Together: Genome Assembly

    A sequencing machine cannot read a genome from one end to the other. It
    reads millions of short, random snippets called **reads**, and has no
    idea where in the genome each one came from. **Assembly** means putting
    the genome back together from those pieces, like rebuilding a book that
    has been through a paper shredder.

    Here the "genome" is a piece of text, so you can read the pieces yourself.
    The trick is the same one real assemblers use. Reads taken from
    neighbouring places **overlap**: the end of one read is the same as the
    start of the next. Line the reads up so the overlaps match, and the text
    comes back.
    """)
    return


@app.cell
def _(GENERAL, mo, on_new_puzzle, on_text):
    # This cell must not read the state: re-running a cell that creates UI
    # elements resets them.
    text_dd = mo.ui.dropdown(
        options=[t["title"] for t in GENERAL],
        value=GENERAL[0]["title"],
        label="**Choose a text**",
        on_change=lambda v: on_text(v),
    )
    # Buttons must be bound to global variables, or marimo ignores clicks.
    new_puzzle_btn = mo.ui.button(label="🎲 New puzzle",
                                  on_change=on_new_puzzle)
    mo.hstack([text_dd, new_puzzle_btn], justify="start", gap=1,
              align="center")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 1: assemble it by hand

    A sentence has been shredded into overlapping reads. **Drag the pieces**
    (sideways, and up or down) so that their letters stack up in the same
    columns. When a piece overlaps another by at least 4 matching letters it
    **snaps into place and sticks** (green outline). From then on the pieces
    move together as one. **Double-click** a piece to pull it off again, for
    example if it stuck somewhere by chance. Where overlapping letters
    disagree they turn **red**. The line at the bottom shows the text your
    arrangement spells out, with gaps where nothing covers it. A faint `·`
    is a space.
    """)
    return


@app.cell
def _(BOARD_HTML, get_game, iframe_html, json, mo):
    _pz = get_game()["puzzle"]
    _data = json.dumps({
        "truth": _pz["truth"], "reads": _pz["reads"], "alt": None,
        "next": "Now watch the computer do a bigger one in Part 2.",
    })
    mo.Html(iframe_html(
        BOARD_HTML.replace("__DATA__", _data.replace("</", "<\\/")),
        height=560))
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Part 2: watch the computer do it

    Real data has millions of reads, so assembly is done by computer. A
    simple strategy is the **greedy assembler**. It looks at every pair of
    pieces, finds the two with the **longest** overlap, and joins them. Then
    it does the same again, and again, until no two pieces overlap by at
    least a **minimum overlap** that you choose.

    Press **Sequence and assemble** to shred the first part of your text into
    50 random reads of 40 letters. Unlike the puzzle, these reads start at
    random places, so some parts of the text are read many times and some,
    by bad luck, not at all. Pieces are joined only if they overlap by at
    least 15 letters. Press **Next join** or **Play** to watch the assembler
    work, and **Compare with the original text** to check its result.
    """)
    return


@app.cell
def _(mo, on_sequence):
    # Bound to a global variable, or marimo ignores its clicks.
    sequence_btn = mo.ui.button(label="🔬 Sequence and assemble",
                                kind="success", on_change=on_sequence)
    sequence_btn
    return


@app.cell
def _(
    ASSEMBLER_HTML,
    compare_html,
    final_pieces,
    get_game,
    iframe_html,
    json,
    mo,
):
    _m = get_game()["machine"]
    if _m is None:
        _out = mo.md("*Press **Sequence and assemble**.*")
    else:
        _data = json.dumps({
            "truth": _m["truth"], "initial": _m["initial"],
            "merges": _m["merges"], "minov": _m["min_ov"],
            "dropped": _m["dropped"], "run": _m["run"],
            "compare": compare_html(
                _m["truth"], final_pieces(_m["initial"], _m["merges"])),
        })
        _out = mo.vstack([
            mo.md(
                f"**{len(_m['reads'])} reads** of {_m['read_len']} letters from "
                f"a {len(_m['truth'])}-letter text."),
            mo.Html(iframe_html(
                ASSEMBLER_HTML.replace("__DATA__", _data.replace("</", "<\\/")),
                height=700)),
        ], gap=0.4)
    _out
    return


@app.cell
def _(mo):
    mo.accordion({
        "🔎 **What is going on?** (try it a few times first!)": mo.md(r"""
        **Overlaps are the whole trick.** Two reads from neighbouring places
        share some text: the end of one is the start of the other. The longer
        the overlap, the less likely it is to have happened by chance, which
        is why the greedy assembler always joins the longest overlaps first.

        **Why does it often finish in several pieces?** The reads land at
        random, so by bad luck some stretches of text are never read at all.
        No assembler can bridge a gap with no reads in it. Press *Sequence
        and assemble* a few times: the number of pieces changes from run to
        run. Real projects read every letter about 30 times over to make
        gaps rare.

        **Why insist on a long overlap?** Lots of words end in a letter that
        starts another word, so a short overlap of a few letters can happen
        by pure chance. Joining on those would glue together pieces that do
        not belong together: a **misassembly**. Requiring 15 matching
        letters makes chance matches very unlikely.

        **Real genomes.** The human genome is about 3 billion letters, and a
        typical sequencing run produces hundreds of millions of reads of
        about 150 letters. The pieces an assembler produces are called
        **contigs**, short for *contiguous sequences*. The most common reason
        assemblies break, or go wrong, is repeated sequence. That is the
        subject of the next demo.
        """)
    })
    return


@app.cell
def _(GENERAL, fresh_game, mo):
    # One state dict for the whole notebook, so the puzzle and the machine
    # can never disagree about which text they belong to.
    get_game, set_game = mo.state(fresh_game(GENERAL[0]))
    return get_game, set_game


@app.cell
def _(
    TEXT_BY_TITLE,
    fresh_game,
    greedy_history,
    new_puzzle,
    rng,
    set_game,
    shotgun,
    trim_words,
):
    MACHINE_LEN = 600
    READ_LEN, N_READS, MIN_OVERLAP = 40, 50, 15

    def on_text(title):
        set_game(fresh_game(TEXT_BY_TITLE[title]))

    def on_new_puzzle(_):
        set_game(lambda g: {**g, "puzzle": new_puzzle(g["text"])})

    def _assemble(m, min_ov):
        initial, merges, dropped = greedy_history(m["reads"], min_ov, rng)
        return {**m, "min_ov": min_ov, "initial": initial, "merges": merges,
                "dropped": dropped, "run": m.get("run", 0) + 1}

    def on_sequence(_):
        # All randomness is drawn here, inside the click handler, and frozen
        # into state - a draw in a reactive cell would re-roll on every
        # re-render.
        def _update(g):
            truth = trim_words(g["text"]["passage"], MACHINE_LEN)
            reads = shotgun(truth, READ_LEN, N_READS, rng)
            m = {"truth": truth, "read_len": READ_LEN, "reads": reads,
                 "run": (g["machine"] or {}).get("run", 0)}
            return {**g, "machine": _assemble(m, MIN_OVERLAP)}

        set_game(_update)

    return on_new_puzzle, on_sequence, on_text


@app.cell
def _(html):
    def iframe_html(doc, height):
        """A self-contained page in an iframe, so its script runs. (mo.iframe
        would strip every newline, which breaks JavaScript.) The page resizes
        the iframe to fit its content."""
        return (f'<iframe srcdoc="{html.escape(doc, quote=True)}" '
                f'style="width:100%;height:{height}px;border:0;display:block" '
                'loading="eager"></iframe>')

    # The drag-and-drop puzzle. Everything happens in the browser; the reads
    # come in through __DATA__.
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

    # The greedy assembler, animated. Python works out every join in
    # advance (greedy_history); the page just plays them back.
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
def _(TEXTS, make_puzzle, rng, trim_words):
    GENERAL = [t for t in TEXTS if t["kind"] == "general"]
    TEXT_BY_TITLE = {t["title"]: t for t in GENERAL}
    LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def new_puzzle(text):
        sentence = text["puzzle"] or trim_words(text["passage"], 120)
        reads = make_puzzle(sentence, rng)
        return {
            "truth": sentence,
            "reads": [{"id": LETTERS[i % 26], "seq": r, "start": s}
                      for i, (r, s) in enumerate(reads)],
        }

    def fresh_game(text):
        return {"text": text, "puzzle": new_puzzle(text), "machine": None}

    return GENERAL, TEXT_BY_TITLE, fresh_game, new_puzzle


@app.cell
def _():
    import html
    import json

    import marimo as mo
    import numpy as np

    # Deliberately unseeded: every student gets their own shredding.
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
    return TEXTS, html, json, mo, rng


if __name__ == "__main__":
    app.run()
