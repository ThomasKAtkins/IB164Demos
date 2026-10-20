import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🔍 Calling Genotypes from Reads

    Once a species has a **reference genome**, there is no need to assemble
    every new individual from scratch. Instead, we sequence them, line each
    read up against the reference (**mapping**), and look for places where
    the reads disagree with it. This is **genotyping**.

    Here the reference is a piece of text. Our individual is **diploid**: it
    carries two copies of the text, one from each parent, and each copy may
    differ from the reference by a few letters. Each read comes from one of
    the two copies, chosen at random, and the sequencer makes the occasional
    **error**.

    At each position, your job is to decide which of three things is true:

    - **0/0**: both copies match the reference (no variant here);
    - **0/1**: one copy differs (**heterozygous**), so about half the reads
      should show the new letter;
    - **1/1**: both copies differ (**homozygous**), so nearly all the reads
      should show it.

    **Choose a text, then press Sequence.**
    """)
    return


@app.cell
def _(DEPTH, ERROR_RATE, GENERAL, mo, on_new, on_resequence, on_text):
    # This cell never reads the state (re-running a cell that creates UI
    # elements resets them). UI elements are bound to global variables, or
    # marimo ignores their clicks.
    text_dd = mo.ui.dropdown(
        options=[t["title"] for t in GENERAL], value=GENERAL[0]["title"],
        label="**Choose a text**", on_change=lambda v: on_text(v))
    new_btn = mo.ui.button(
        label="🧍 Sequence a new individual", kind="success",
        on_change=lambda v: on_new(DEPTH, ERROR_RATE))
    again_btn = mo.ui.button(
        label="🔁 Sequence the same individual again",
        on_change=lambda v: on_resequence(DEPTH, ERROR_RATE))
    mo.vstack([
        text_dd,
        mo.hstack([new_btn, again_btn], justify="start", gap=1, wrap=True),
        mo.md(f"Every letter is read about **{DEPTH} times**, and the "
              f"sequencer gets about **1 letter in {round(1 / ERROR_RATE)}** "
              "wrong."),
    ], gap=0.6)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Step 1: map some reads yourself

    Each read is a short piece of text, and we know roughly what the whole
    text should say: the **reference**. **Mapping** means finding where each
    read belongs on the reference. Here are a few of this individual's reads.
    **Drag each one** along under the reference until its letters line up.
    Green letters match the reference, and red ones do not. When you think
    every read is in the right place, press **Check my work**.
    """)
    return


@app.cell
def _(MAP_HTML, get_sim, iframe_html, json, mo):
    _s = get_sim()
    if _s["reads"] is None:
        _out = mo.md("*Press **Sequence a new individual**.*")
    else:
        _data = json.dumps({"ref": _s["ref"], "reads": _s["map_reads"],
                            "run": _s["run"]})
        _out = mo.Html(iframe_html(
            MAP_HTML.replace("__DATA__", _data.replace("</", "<\\/")),
            height=420))
    _out
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Step 2: the pileup

    Real data has far too many reads to map by hand, so the computer maps
    them all. The top line of letters is the reference. Below it, every read
    is lined up where it maps, and letters that **disagree with the reference** are
    red. The **bars** along the top show, for each position, what fraction of
    the reads there disagree with the reference.

    **Click any column** (or use the ← → keys) to see the letters stacked in
    it, then make your call with the buttons: **0/0** if you think there is
    no variant there (just sequencing errors), **0/1** or **1/1** if there
    is. Nothing is called until you choose. Call every column with red
    letters, then press **Reveal the truth**.
    """)
    return


@app.cell
def _(VIEWER_HTML, get_sim, iframe_html, json, mo):
    _s = get_sim()
    if _s["reads"] is None:
        _out = mo.md("*Press **Sequence a new individual**.*")
    else:
        _data = json.dumps({
            "ref": _s["ref"],
            "reads": [[r["start"], r["seq"], r["hap"]] for r in _s["reads"]],
            "variants": _s["variants"],
            "depth": _s["depth"], "err": _s["err"],
            "run": _s["run"],
        })
        _out = mo.Html(iframe_html(
            VIEWER_HTML.replace("__DATA__", _data.replace("</", "<\\/")),
            height=900))
    _out
    return


@app.cell
def _(mo):
    mo.accordion({
        "🔎 **What is going on?** (call some genotypes first!)": mo.md(r"""
        **Errors and real variants look different.** A sequencing error hits
        one read at one position, at random. A real variant is in the genome
        itself, so it shows up in **every** read from that copy, all in the
        same column. A single red letter means very little. A column where
        many reads agree on the same new letter is a variant. In the bar
        track, errors make short, scattered bars, and variants make tall
        ones.

        **Heterozygous or homozygous?** Each read comes from one copy or the
        other with probability ½, just like a coin toss. At a heterozygous
        site with 10 reads, you would expect about 5 to show the new letter,
        but 2 or 8 happen too (this is the binomial distribution from Lab 1).
        At **low depth** this goes badly wrong. With 3 reads there is a 1 in 4
        chance that all of them come from the same copy, and then a
        heterozygote looks exactly like a homozygote, or is missed
        altogether. That is why genotyping needs depth.

        **Things to try**

        - Press *Sequence the same individual again* a few times. The
          variants stay put, but the reads change. Does the number of reads
          showing each variant change too? Would any of your calls change?
        - Sometimes two reads share the same error by chance. How would you
          set a rule (a *threshold*) that ignores these but keeps real
          heterozygotes?
        - After revealing, the reads are coloured by which parent's copy they
          came from. Real short reads rarely carry this information. Working
          out which variants sit together on the same copy (*phasing*) is a
          problem of its own, and long reads are good at it.

        Real genotype callers, such as GATK and DeepVariant, do exactly this,
        with a proper likelihood model of errors and of the binomial sampling
        of the two copies, at millions of sites at once.
        """)
    })
    return


@app.cell
def _(GENERAL, fresh_sim, mo):
    # One state dict, replaced whole on every change, so the reads and the
    # true variants always belong to the same individual.
    get_sim, set_sim = mo.state(fresh_sim(GENERAL[0]))
    return get_sim, set_sim


@app.cell
def _(
    TEXT_BY_TITLE,
    draw_individual,
    fresh_sim,
    pick_map_reads,
    rng,
    sequence,
    set_sim,
):
    def on_text(title):
        set_sim(fresh_sim(TEXT_BY_TITLE[title]))

    def on_new(depth, err):
        # All randomness is drawn here, in the click handler.
        def _update(s):
            haps, variants = draw_individual(s["ref"], s["text"], rng)
            seq = sequence(haps, depth, err, rng)
            return {**s, "haps": haps, "variants": variants,
                    "run": s["run"] + 1, **seq,
                    "map_reads": pick_map_reads(seq["reads"], variants, rng)}

        set_sim(_update)

    def on_resequence(depth, err):
        def _update(s):
            if s["haps"] is None:
                return s
            seq = sequence(s["haps"], depth, err, rng)
            return {**s, "run": s["run"] + 1, **seq,
                    "map_reads": pick_map_reads(seq["reads"], s["variants"],
                                                rng)}

        set_sim(_update)

    return on_new, on_resequence, on_text


@app.cell
def _(html):
    def iframe_html(doc, height):
        """A self-contained page in an iframe, so its script runs. (mo.iframe
        would strip every newline, which breaks JavaScript.)"""
        return (f'<iframe srcdoc="{html.escape(doc, quote=True)}" '
                f'style="width:100%;height:{height}px;border:0;display:block" '
                'loading="eager"></iframe>')

    # The interactive pileup viewer. All clicking and calling happens in the
    # browser; the individual comes in through __DATA__.
    VIEWER_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         color: #33302c; background: transparent; font-size: 14px; }
  #sc { overflow: auto; max-height: 470px; border: 1px solid #e4e0d8;
        border-radius: 10px; background: #fbfaf8; outline: none; }
  #sc:focus { border-color: #6b4f9e; }
  #grid { position: relative; padding: 6px 10px 10px 10px; cursor: pointer; }
  .mono { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
          font-size: 14px; }
  #track { position: relative; height: 70px; border-bottom: 1px solid #d9d4cc; }
  .bar { position: absolute; bottom: 0; background: #4C72B0; }
  .guide { position: absolute; left: 0; right: 0; border-top: 1px dashed #c4bdb2; }
  .guidelab { position: sticky; left: 0; font-size: 10px; color: #9a938a;
              background: #fbfaf8; padding-right: 3px; }
  .callmark.none { background: #9a938a; }
  .callmark { position: absolute; top: 0; font-size: 10px; font-weight: 800;
              color: #fff; background: #4C72B0; border-radius: 3px;
              padding: 0 2px; transform: translateX(-30%); }
  .truemark { position: absolute; font-size: 13px; transform: translateX(-15%); }
  .row { white-space: pre; height: 19px; line-height: 19px; color: #8f887f; }
  .ruler { color: #a8a198; height: 16px; line-height: 16px; }
  .ref { color: #23201c; font-weight: 800; height: 24px; line-height: 24px;
         border-bottom: 1px solid #e4e0d8; margin-bottom: 3px; }
  .sp { color: #d6d0c7; }
  .mm { color: #C44E52; font-weight: 800; }
  .h1 { background: #dbe6f6; }
  .h2 { background: #fbe3cc; }
  #sel { position: absolute; top: 0; bottom: 0; background: rgba(255, 214, 0, 0.28);
         border-left: 1px solid #e6b800; border-right: 1px solid #e6b800;
         pointer-events: none; }
  #panel { display: flex; gap: 1rem; flex-wrap: wrap; margin-top: 0.6rem;
           align-items: stretch; }
  .card { background: #fff; border: 1px solid #e4e0d8; border-radius: 10px;
          padding: 0.6rem 0.8rem; }
  #info { flex: 1 1 320px; }
  #info h4, #callbox h4 { margin: 0 0 0.35rem; font-size: 0.95rem; }
  .stack { display: flex; height: 22px; border-radius: 5px; overflow: hidden;
           margin: 0.35rem 0; background: #eee9e1; }
  .stack div { display: flex; align-items: center; justify-content: center;
               color: #fff; font-weight: 800; font-size: 12px; min-width: 0; }
  .legend span { display: inline-block; margin-right: 0.8rem; }
  #callbox { flex: 0 1 330px; }
  button { font: inherit; font-size: 0.85rem; padding: 0.3rem 0.65rem;
           border-radius: 6px; border: 1px solid #cfc8bd; background: #fff;
           cursor: pointer; margin: 0 0.25rem 0.3rem 0; }
  button:hover { border-color: #6b4f9e; }
  button.on { background: #4C72B0; color: #fff; border-color: #4C72B0; }
  #reveal { background: #fdf0d8; border-color: #e0b866; font-weight: 700; }
  #calls { margin-top: 0.6rem; font-size: 0.9rem; }
  .chip { display: inline-block; background: #e3ecf8; border-radius: 999px;
          padding: 0.1rem 0.55rem; margin: 0 0.3rem 0.3rem 0; cursor: pointer; }
  #truth table { border-collapse: collapse; margin-top: 0.4rem; }
  #truth th, #truth td { padding: 0.25rem 0.6rem; border-bottom: 1px solid #eee9e1;
                         text-align: left; }
  #truth th { background: #f4f1ec; }
  #truth { margin-top: 0.6rem; }
  .cap { font-size: 0.82rem; color: #7a7382; margin: 0 0 0.35rem; }
</style></head>
<body>
<p class="cap" id="cap"></p>
<div id="sc" tabindex="0"><div id="grid" class="mono">
  <div id="track"></div>
  <div id="rows"></div>
  <div id="sel"></div>
</div></div>
<div id="panel">
  <div id="info" class="card"></div>
  <div id="callbox" class="card">
    <h4>Your call at this position <span id="notcalled" style="font-weight:400;color:#9a938a"></span></h4>
    <div>
      <button data-gt="0/0">0/0 no variant</button>
      <button data-gt="0/1">0/1 heterozygous</button>
      <button data-gt="1/1">1/1 homozygous</button>
    </div>
    <div style="margin-top:0.3rem">
      <button id="prev">◀ previous red column</button>
      <button id="next">next red column ▶</button>
    </div>
    <div style="margin-top:0.3rem"><button id="reveal">👀 Reveal the truth</button></div>
  </div>
</div>
<div id="calls"></div>
<div id="truth"></div>
<script>
(function () {
  var D = __DATA__;
  var ref = D.ref, L = ref.length;
  var reads = D.reads.map(function (r) { return {s: r[0], q: r[1], h: r[2]}; });
  var sel = 0, calls = {}, revealed = false;

  /* Measure the monospace character width, so columns line up exactly. */
  var probe = document.createElement("span");
  probe.className = "mono";
  probe.style.visibility = "hidden";
  probe.style.position = "absolute";
  probe.style.whiteSpace = "pre";
  probe.textContent = new Array(101).join("M");
  document.body.appendChild(probe);
  var CW = probe.getBoundingClientRect().width / 100;
  document.body.removeChild(probe);

  var grid = document.getElementById("grid");
  var sc = document.getElementById("sc");
  var track = document.getElementById("track");
  var rowsEl = document.getElementById("rows");
  var selEl = document.getElementById("sel");
  grid.style.width = (L * CW + 20) + "px";
  var PADL = 10;

  /* Letter counts per column. */
  var cols = [];
  for (var c = 0; c < L; c++) cols.push({});
  reads.forEach(function (r) {
    for (var k = 0; k < r.q.length; k++) {
      var col = cols[r.s + k], ch = r.q.charAt(k);
      col[ch] = (col[ch] || 0) + 1;
    }
  });
  function depthAt(c) {
    var t = 0;
    for (var k in cols[c]) t += cols[c][k];
    return t;
  }
  function altAt(c) { return depthAt(c) - (cols[c][ref.charAt(c)] || 0); }
  var redCols = [];
  for (var c2 = 0; c2 < L; c2++) if (altAt(c2) > 0) redCols.push(c2);

  function esc(ch) {
    return ch === "&" ? "&amp;" : ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch;
  }
  function show(ch) { return ch === " " ? "·" : esc(ch); }

  /* Pack reads into rows, left to right. */
  var sorted = reads.slice().sort(function (a, b) { return a.s - b.s; });
  var packed = [], ends = [];
  sorted.forEach(function (r) {
    for (var i = 0; i < ends.length; i++) {
      if (ends[i] < r.s) { ends[i] = r.s + r.q.length; packed[i].push(r); return; }
    }
    ends.push(r.s + r.q.length);
    packed.push([r]);
  });

  function drawRows() {
    var out = [];
    var nums = [], ticks = [];
    for (var c = 0; c < L; c++) { nums.push(" "); ticks.push(" "); }
    for (var p = 9; p < L; p += 10) {
      ticks[p] = "|";
      var lab = String(p + 1);
      for (var j = 0; j < lab.length && p + j < L; j++) nums[p + j] = lab.charAt(j);
    }
    out.push('<div class="row ruler">' + nums.join("") + "</div>");
    out.push('<div class="row ruler">' + ticks.join("") + "</div>");
    var r0 = [];
    for (var c3 = 0; c3 < L; c3++) {
      var ch = ref.charAt(c3);
      r0.push(ch === " " ? '<span class="sp">·</span>' : esc(ch));
    }
    out.push('<div class="row ref">' + r0.join("") + "</div>");
    packed.forEach(function (row) {
      var bits = [], x = 0;
      row.forEach(function (r) {
        bits.push(new Array(r.s - x + 1).join(" "));
        var inner = [];
        for (var k = 0; k < r.q.length; k++) {
          var ch = r.q.charAt(k), rc = ref.charAt(r.s + k);
          if (ch !== rc) inner.push('<span class="mm">' + show(ch) + "</span>");
          else if (ch === " ") inner.push('<span class="sp">·</span>');
          else inner.push(esc(ch));
        }
        bits.push('<span class="' + (revealed ? "h" + r.h : "") + '">' +
                  inner.join("") + "</span>");
        x = r.s + r.q.length;
      });
      out.push('<div class="row">' + bits.join("") + "</div>");
    });
    rowsEl.innerHTML = out.join("");
  }

  function drawTrack() {
    var H = 56, out = [];
    out.push('<div class="guide" style="top:' + (70 - H) + 'px"><span class="guidelab">all reads</span></div>');
    out.push('<div class="guide" style="top:' + (70 - H / 2) + 'px"><span class="guidelab">half</span></div>');
    for (var c = 0; c < L; c++) {
      var d = depthAt(c);
      if (!d) continue;
      var f = altAt(c) / d;
      if (f <= 0) continue;
      out.push('<div class="bar" style="left:' + (c * CW + 1) + "px;width:" +
               Math.max(CW - 2, 2) + "px;height:" + Math.max(f * H, 2) + 'px"></div>');
    }
    for (var p in calls) {
      out.push('<div class="callmark' + (calls[p] === "0/0" ? " none" : "") +
               '" style="left:' + (p * CW) + 'px">' + calls[p] + "</div>");
    }
    if (revealed) {
      D.variants.forEach(function (v) {
        out.push('<div class="truemark" style="left:' + (v.pos * CW) +
                 'px;top:' + 14 + 'px" title="true variant">⭐</div>');
      });
    }
    track.innerHTML = out.join("");
  }

  function drawSel() {
    selEl.style.left = (PADL + sel * CW) + "px";
    selEl.style.width = CW + "px";
    var c = cols[sel], d = depthAt(sel), rch = ref.charAt(sel);
    var items = Object.keys(c).sort(function (a, b) { return c[b] - c[a]; });
    var COL = ["#C44E52", "#8172B3", "#DD8452", "#937860"];
    var stack = [], legend = [], ai = 0;
    items.forEach(function (k) {
      var isRef = k === rch;
      var colr = isRef ? "#8f887f" : COL[ai++ % COL.length];
      var nm = k === " " ? "space" : "“" + esc(k) + "”";
      stack.push('<div style="flex:' + c[k] + ";background:" + colr + '">' + c[k] + "</div>");
      legend.push('<span><b style="color:' + colr + '">■</b> ' + nm + " × " +
                  c[k] + (isRef ? " (reference)" : "") + "</span>");
    });
    var word = (function () {
      var a = sel, b = sel;
      while (a > 0 && /[A-Za-z]/.test(ref.charAt(a - 1))) a--;
      while (b < L && /[A-Za-z]/.test(ref.charAt(b))) b++;
      return ref.slice(a, b);
    })();
    document.getElementById("info").innerHTML =
      "<h4>Position " + (sel + 1) + (word ? ' · in the word “' + esc(word) + '”' : "") +
      "</h4>The reference letter is <b>" + (rch === " " ? "a space" : "“" + esc(rch) + "”") +
      "</b>. <b>" + d + "</b> read" + (d === 1 ? "" : "s") + " cover this position:" +
      (d ? '<div class="stack">' + stack.join("") + '</div><div class="legend">' +
           legend.join("") + "</div>" : "<p>No reads here.</p>");
    var mine = calls[sel] || null;
    var btns = document.querySelectorAll("button[data-gt]");
    for (var i = 0; i < btns.length; i++) {
      btns[i].classList.toggle("on", btns[i].getAttribute("data-gt") === mine);
    }
    document.getElementById("notcalled").textContent = mine ? "" : "(not called yet)";
    var vis = PADL + sel * CW;
    if (vis < sc.scrollLeft + 40 || vis > sc.scrollLeft + sc.clientWidth - 40) {
      sc.scrollLeft = vis - sc.clientWidth / 2;
    }
  }

  function uncalledRed() {
    return redCols.filter(function (c) { return !calls[c]; }).length;
  }
  function drawCalls() {
    var ks = Object.keys(calls).map(Number).sort(function (a, b) { return a - b; });
    document.getElementById("calls").innerHTML = ks.length ?
      "<b>Your calls:</b> " + ks.map(function (k) {
        return '<span class="chip" data-p="' + k + '">' + (k + 1) + ": " + calls[k] + "</span>";
      }).join("") + ' <span style="color:#7a7382">(' + uncalledRed() + " column" +
      (uncalledRed() === 1 ? "" : "s") + " with red letters not called yet)</span>" :
      '<span style="color:#7a7382">No calls yet. Click a column with red letters and choose 0/0, 0/1 or 1/1.</span>';
    var chips = document.querySelectorAll(".chip");
    for (var i = 0; i < chips.length; i++) {
      chips[i].addEventListener("click", function () {
        sel = Number(this.getAttribute("data-p"));
        drawSel();
      });
    }
  }

  function drawTruth() {
    if (!revealed) { document.getElementById("truth").innerHTML = ""; return; }
    var truth = {};
    D.variants.forEach(function (v) { truth[v.pos] = v; });
    var ps = {};
    Object.keys(truth).forEach(function (k) { ps[k] = 1; });
    Object.keys(calls).forEach(function (k) { if (calls[k] !== "0/0") ps[k] = 1; });
    var goodNone = Object.keys(calls).filter(function (k) {
      return calls[k] === "0/0" && !truth[k];
    }).length;
    var keys = Object.keys(ps).map(Number).sort(function (a, b) { return a - b; });
    var right = 0, fa = 0, rows = [];
    keys.forEach(function (p) {
      var v = truth[p], c = calls[p] || "\u2014";
      var verdict, what, tg;
      if (v) {
        what = "“" + esc(v.word_ref) + "” → “" + esc(v.word_alt) + "”";
        tg = v.gt;
        if (c === v.gt) { verdict = "✅ correct"; right++; }
        else if (c === "\u2014") verdict = "❌ not called";
        else if (c === "0/0") verdict = "❌ missed: you called it 0/0";
        else verdict = "⚠️ right place, wrong genotype";
      } else {
        what = "no variant (just sequencing errors)";
        tg = "0/0";
        verdict = "❌ false alarm";
        fa++;
      }
      rows.push("<tr><td>" + (p + 1) + "</td><td>" + what + "</td><td>" + tg +
                "</td><td>" + c + "</td><td>" + verdict + "</td></tr>");
    });
    document.getElementById("truth").innerHTML =
      '<div class="card"><b>The truth:</b> this individual carries <b>' + D.variants.length +
      "</b> variants (⭐ in the bar track). You called <b>" + right +
      "</b> correctly and made <b>" + fa + "</b> false alarm" + (fa === 1 ? "" : "s") +
      ". You also called <b>" + goodNone + "</b> column" + (goodNone === 1 ? "" : "s") +
      " correctly as 0/0 (red letters that were only sequencing errors)." +
      " The reads are now coloured by which parent's copy they came from " +
      '(<span class="h1">&nbsp;copy 1&nbsp;</span> or <span class="h2">&nbsp;copy 2&nbsp;</span>).' +
      "<table><tr><th>Position</th><th>Change</th><th>True genotype</th><th>Your call</th><th></th></tr>" +
      rows.join("") + "</table></div>";
  }

  function redraw() { drawTrack(); drawSel(); drawCalls(); drawTruth(); fit(); }
  function fit() {
    if (window.frameElement) {
      window.frameElement.style.height = (document.documentElement.scrollHeight + 6) + "px";
    }
  }

  grid.addEventListener("click", function (ev) {
    var r = grid.getBoundingClientRect();
    var c = Math.floor((ev.clientX - r.left - PADL) / CW);
    if (c >= 0 && c < L) { sel = c; drawSel(); sc.focus(); }
  });
  sc.addEventListener("keydown", function (ev) {
    if (ev.key === "ArrowLeft" && sel > 0) { sel--; drawSel(); ev.preventDefault(); }
    if (ev.key === "ArrowRight" && sel < L - 1) { sel++; drawSel(); ev.preventDefault(); }
  });
  document.getElementById("next").addEventListener("click", function () {
    for (var i = 0; i < redCols.length; i++) {
      if (redCols[i] > sel) { sel = redCols[i]; drawSel(); return; }
    }
  });
  document.getElementById("prev").addEventListener("click", function () {
    for (var i = redCols.length - 1; i >= 0; i--) {
      if (redCols[i] < sel) { sel = redCols[i]; drawSel(); return; }
    }
  });
  var gtBtns = document.querySelectorAll("button[data-gt]");
  for (var i = 0; i < gtBtns.length; i++) {
    gtBtns[i].addEventListener("click", function () {
      var gt = this.getAttribute("data-gt");
      calls[sel] = gt;
      redraw();
    });
  }
  document.getElementById("reveal").addEventListener("click", function () {
    revealed = true;
    drawRows();
    redraw();
  });

  document.getElementById("cap").textContent =
    reads.length + " reads of up to 30 letters, " + D.depth + "× depth, " +
    (100 * D.err).toFixed(1) + "% sequencing errors. " + redCols.length +
    " of " + L + " positions have at least one red letter. Scroll sideways (and down) to see everything.";
  drawRows();
  if (redCols.length) sel = redCols[0];
  redraw();
  window.addEventListener("resize", fit);
})();
</script>
</body></html>
"""
    # Drag reads onto the reference (mapping by hand). The reads come in
    # through __DATA__.
    MAP_HTML = r"""<!doctype html>
<html><head><meta charset="utf-8">
<style>
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
         color: #33302c; background: transparent; font-size: 14px; }
  .bar { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap;
         margin: 0 0 0.5rem; }
  button { font: inherit; font-size: 0.85rem; padding: 0.3rem 0.75rem;
           border-radius: 6px; border: 1px solid #cfc8bd; background: #fff;
           cursor: pointer; }
  button:hover { border-color: #6b4f9e; }
  #ws { position: relative; overflow: auto; border: 1px solid #e4e0d8;
        border-radius: 10px; background: #fbfaf8; }
  #inner { position: relative; }
  .ch { display: inline-block; text-align: center; flex: none;
        font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
        font-size: 15px; }
  .sp { color: #c9c2b8; }
  #ref { position: absolute; display: flex; font-weight: 800; color: #23201c;
         border-bottom: 2px solid #33302c; background: #fff; }
  #reflab { position: absolute; font-size: 11px; font-weight: 800; color: #7a7382;
            text-transform: uppercase; letter-spacing: 0.06em; }
  #ruler { position: absolute; display: flex; color: #a8a198; font-size: 11px; }
  .tile { position: absolute; display: flex; cursor: grab; user-select: none;
          touch-action: none; border-radius: 5px; background: #fff;
          border: 1px solid #b9b1a5; border-left-width: 5px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.15); }
  .tile.drag { cursor: grabbing; box-shadow: 0 6px 16px rgba(0,0,0,0.25);
               z-index: 10; opacity: 0.95; }
  .tile.mapped { border-color: #55A868; box-shadow: 0 0 0 2px #a8d8b4; }
  .tile.wrongspot { border-color: #C44E52; box-shadow: 0 0 0 2px #f2b8b9; }
  .tile.wrongspot .score { color: #C44E52; }
  #status.fail { background: #fbe1e1; border: 1px solid #e9a5a7; }
  .tile .ch.m { background: #dff1e3; }
  .tile .ch.x { background: #f6c6c7; color: #a01e24; font-weight: 800; }
  .tile .ch.off { color: #b5aea4; }
  .lab { position: absolute; left: -23px; top: 4px; width: 19px;
         font-size: 11px; font-weight: 800; color: #9a938a; text-align: right; }
  .score { position: absolute; right: -78px; top: 4px; width: 74px;
           font-size: 11px; font-weight: 700; color: #7a7382; white-space: nowrap; }
  .tile.mapped .score { color: #2e7d43; }
  #status { margin-top: 0.5rem; padding: 0.55rem 0.8rem; border-radius: 8px;
            background: #f4f1ec; font-size: 0.92rem; line-height: 1.5; }
  #status.win { background: #dff3e3; border: 1px solid #9fd4ab; }
</style></head>
<body>
<div class="bar">
  <button id="shuffle">🔀 Shuffle the reads</button>
  <button id="check" style="background:#55A868;border-color:#55A868;color:#fff;font-weight:700">✅ Check my work</button>
  <button id="hint">💡 Hint: map one read</button>
  <span id="note" style="font-size:0.85rem;color:#7a7382"></span>
</div>
<div id="ws"><div id="inner"></div></div>
<div id="status"></div>
<script>
(function () {
  var D = __DATA__;
  var ref = D.ref, reads = D.reads, n = reads.length, L = ref.length;
  var CW = 12, RH = 32, TH = 26, PADL = 30, TOP = 52;
  var ROWS = n + 1;
  var COLS = L;
  var PAL = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
             "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"];
  var inner = document.getElementById("inner");
  var ws = document.getElementById("ws");
  var status = document.getElementById("status");
  var note = document.getElementById("note");
  inner.style.width = (PADL + COLS * CW + 100) + "px";
  inner.style.height = (TOP + ROWS * RH + 16) + "px";
  ws.style.height = Math.min(480, TOP + ROWS * RH + 36) + "px";
  inner.style.backgroundImage =
    "repeating-linear-gradient(90deg, transparent 0 " + (CW - 1) +
    "px, rgba(0,0,0,0.035) " + (CW - 1) + "px " + CW + "px)";
  inner.style.backgroundPosition = PADL + "px 0";

  function esc(ch) {
    return ch === "&" ? "&amp;" : ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch;
  }
  function cell(ch) {
    return '<span class="ch' + (ch === " " ? " sp" : "") + '" style="width:' + CW +
           "px;height:" + TH + "px;line-height:" + TH + 'px">' +
           (ch === " " ? "·" : esc(ch)) + "</span>";
  }

  /* The reference, with a ruler above it. */
  var ruler = document.createElement("div");
  ruler.id = "ruler";
  var rr = [];
  for (var c = 0; c < L; c++) {
    var lab = (c + 1) % 10 === 0 ? String(c + 1) : "";
    rr.push('<span class="ch" style="width:' + CW + 'px;font-size:10px;overflow:visible">' +
            (lab ? lab : ((c + 1) % 5 === 0 ? "·" : "")) + "</span>");
  }
  ruler.innerHTML = rr.join("");
  ruler.style.left = PADL + "px";
  ruler.style.top = "2px";
  inner.appendChild(ruler);
  var refEl = document.createElement("div");
  refEl.id = "ref";
  refEl.innerHTML = ref.split("").map(cell).join("");
  refEl.style.left = PADL + "px";
  refEl.style.top = "18px";
  inner.appendChild(refEl);
  var refLab = document.createElement("div");
  refLab.id = "reflab";
  refLab.textContent = "Ref";
  refLab.style.left = "2px";
  refLab.style.top = "26px";
  inner.appendChild(refLab);

  /* Best possible number of mismatches for each read, anywhere. */
  function mism(i, col) {
    var r = reads[i].seq, x = 0;
    for (var k = 0; k < r.length; k++) {
      var p = col + k;
      if (p < 0 || p >= L || ref.charAt(p) !== r.charAt(k)) x++;
    }
    return x;
  }
  var best = reads.map(function (r, i) {
    var b = Infinity;
    for (var c = 0; c + r.seq.length <= L; c++) b = Math.min(b, mism(i, c));
    return b;
  });

  var pos = [], drag = null, hints = 0, verdict = null;
  var tiles = reads.map(function (r, i) {
    var t = document.createElement("div");
    t.className = "tile";
    t.style.borderLeftColor = PAL[i % PAL.length];
    var lab = document.createElement("span");
    lab.className = "lab";
    lab.textContent = r.id;
    t.appendChild(lab);
    var holder = document.createElement("span");
    holder.style.display = "flex";
    holder.innerHTML = r.seq.split("").map(cell).join("");
    t.appendChild(holder);
    var sc = document.createElement("span");
    sc.className = "score";
    t.appendChild(sc);
    inner.appendChild(t);
    return t;
  });

  function draw(i) {
    tiles[i].style.left = (PADL + pos[i].col * CW) + "px";
    tiles[i].style.top = (TOP + pos[i].row * RH) + "px";
  }
  function colour(i) {
    var cs = tiles[i].children[1].children, r = reads[i].seq, good = 0;
    for (var k = 0; k < r.length; k++) {
      var p = pos[i].col + k;
      cs[k].classList.remove("m", "x", "off");
      if (p < 0 || p >= L) { cs[k].classList.add("off"); continue; }
      if (ref.charAt(p) === r.charAt(k)) { cs[k].classList.add("m"); good++; }
      else cs[k].classList.add("x");
    }
    var mapped = mism(i, pos[i].col) === best[i] && pos[i].col >= 0 &&
                 pos[i].col + r.length <= L;
    var shown = verdict ? verdict[i] : null;
    tiles[i].classList.toggle("mapped", shown === true);
    tiles[i].classList.toggle("wrongspot", shown === false);
    tiles[i].children[2].textContent =
      (shown === true ? "\u2713 " : shown === false ? "\u2717 " : "") +
      good + "/" + r.length + " match";
    return mapped;
  }
  function fits(i, col, row) {
    for (var j = 0; j < n; j++) {
      if (j === i || pos[j].row !== row) continue;
      if (col < pos[j].col + reads[j].seq.length && pos[j].col < col + reads[i].seq.length) return false;
    }
    return true;
  }
  function place(i, col, row) {
    col = Math.max(0, Math.min(COLS - reads[i].seq.length, col));
    row = Math.max(0, Math.min(ROWS - 1, row));
    for (var d = 0; d < ROWS; d++) {
      var tries = [row + d, row - d];
      for (var q = 0; q < 2; q++) {
        var r = tries[q];
        if (r >= 0 && r < ROWS && fits(i, col, r)) { pos[i] = {col: col, row: r}; draw(i); return; }
      }
    }
    pos[i] = {col: col, row: row};
    draw(i);
  }
  function fitFrame() {
    if (window.frameElement) {
      window.frameElement.style.height = (document.documentElement.scrollHeight + 4) + "px";
    }
  }
  function evaluate() {
    for (var i = 0; i < n; i++) colour(i);
    if (!verdict) {
      status.className = "";
      status.innerHTML = "Slide each read along under the reference until (almost) all " +
        "its letters match, then press <b>Check my work</b>. Don't expect every letter " +
        "to match: this individual differs from the reference in a few places, and the " +
        "sequencer makes the odd mistake.";
    }
    fitFrame();
  }
  function check() {
    verdict = reads.map(function (r, i) {
      return mism(i, pos[i].col) === best[i] && pos[i].col >= 0 &&
             pos[i].col + r.seq.length <= L;
    });
    var done = verdict.filter(Boolean).length;
    evaluate();
    if (done === n) {
      status.className = "win";
      status.innerHTML = "\ud83c\udf89 <b>All " + n + " reads are in the right place" +
        (hints ? " (with " + hints + " hint" + (hints > 1 ? "s" : "") + ")" : "") +
        ".</b> Now look down the columns. Where <b>several</b> reads show the same " +
        "red letter in the same column, the individual really differs from the " +
        "reference there: a <b>variant</b>. A red letter in just <b>one</b> read is " +
        "more likely a sequencing error. Below, the computer has mapped every " +
        "read for you.";
    } else {
      status.className = "fail";
      status.innerHTML = "<b>" + done + " of " + n + "</b> reads are in the right place " +
        "(\u2713). The ones marked \u2717 would match the reference better somewhere " +
        "else: keep sliding them, then check again.";
    }
    fitFrame();
  }
  function shuffle() {
    pos = reads.map(function (r, i) {
      return {col: Math.floor(Math.random() * Math.max(1, L - r.seq.length)), row: i + 1};
    });
    for (var i = 0; i < n; i++) draw(i);
    evaluate();
  }

  tiles.forEach(function (t, i) {
    t.addEventListener("pointerdown", function (ev) {
      ev.preventDefault();
      t.setPointerCapture(ev.pointerId);
      drag = {i: i, x0: ev.clientX, y0: ev.clientY, dx: 0, dy: 0};
      t.classList.add("drag");
    });
    t.addEventListener("pointermove", function (ev) {
      if (!drag || drag.i !== i) return;
      drag.dx = ev.clientX - drag.x0;
      drag.dy = ev.clientY - drag.y0;
      t.style.left = (PADL + pos[i].col * CW + drag.dx) + "px";
      t.style.top = (TOP + pos[i].row * RH + drag.dy) + "px";
      /* Live feedback while dragging: colour as if dropped here. */
      var save = pos[i];
      pos[i] = {col: save.col + Math.round(drag.dx / CW), row: save.row};
      colour(i);
      pos[i] = save;
    });
    function drop() {
      if (!drag || drag.i !== i) return;
      var d = drag;
      drag = null;
      t.classList.remove("drag");
      place(i, pos[i].col + Math.round(d.dx / CW), pos[i].row + Math.round(d.dy / RH));
      if (verdict) verdict[i] = null;
      evaluate();
    }
    t.addEventListener("pointerup", drop);
    t.addEventListener("pointercancel", drop);
  });

  document.getElementById("shuffle").addEventListener("click", function () {
    hints = 0;
    verdict = null;
    note.textContent = "";
    shuffle();
  });
  document.getElementById("check").addEventListener("click", check);
  document.getElementById("hint").addEventListener("click", function () {
    for (var i = 0; i < n; i++) {
      if (colour(i)) continue;
      place(i, reads[i].start, pos[i].row);
      if (verdict) verdict[i] = null;
      hints++;
      note.textContent = "Mapped read " + reads[i].id + " for you.";
      evaluate();
      ws.scrollLeft = Math.max(0, PADL + reads[i].start * CW - ws.clientWidth / 3);
      return;
    }
    note.textContent = "Every read is already mapped!";
  });

  shuffle();
})();
</script>
</body></html>
"""
    return MAP_HTML, VIEWER_HTML, iframe_html


@app.cell
def _(GENOTYPE_REF_LEN, READ_LEN, re, trim_words):
    LETTERS = "abcdefghijklmnopqrstuvwxyz"

    def fresh_sim(text):
        return {"text": text,
                "ref": trim_words(text["passage"], GENOTYPE_REF_LEN),
                "haps": None, "variants": [], "reads": None, "run": 0,
                "map_reads": [],
                "depth": 0, "err": 0.0, "read_len": READ_LEN}

    def word_at(text, p):
        a = p
        while a > 0 and text[a - 1].isalpha():
            a -= 1
        b = p
        while b < len(text) and text[b].isalpha():
            b += 1
        return a, b

    def draw_individual(ref, text, rng, n_target=5):
        """Two copies of the reference carrying a few one-letter changes:
        those listed for the text in texts.txt where possible, otherwise
        random letters inside words."""
        sites = {}       # position -> alt letter
        options = list(text["variants"])
        for i in rng.permutation(len(options)).tolist():
            if len(sites) >= n_target:
                break
            old, new = options[i]
            hits = [m.start() for m in re.finditer(rf"\b{re.escape(old)}\b", ref)]
            if not hits or len(old) != len(new):
                continue
            at = hits[int(rng.integers(len(hits)))]
            diff = [j for j, (a, b) in enumerate(zip(old, new)) if a != b]
            if len(diff) != 1 or any(abs(at + diff[0] - p) < 3 for p in sites):
                continue
            sites[at + diff[0]] = new[diff[0]]
        letters = [p for p, c in enumerate(ref) if c.isalpha()]
        for _ in range(1000):
            if len(sites) >= n_target or not letters:
                break
            p = letters[int(rng.integers(len(letters)))]
            if any(abs(p - q) < 3 for q in sites):
                continue
            alts = [c for c in LETTERS if c != ref[p].lower()]
            alt = alts[int(rng.integers(len(alts)))]
            sites[p] = alt.upper() if ref[p].isupper() else alt

        # At least one of each genotype, then the rest at random.
        positions = sorted(sites)
        gts = ["0/1", "1/1"] + [
            "0/1" if rng.random() < 0.6 else "1/1"
            for _ in range(len(positions) - 2)]
        gts = [gts[i] for i in rng.permutation(len(gts)).tolist()][:len(positions)]
        h1, h2 = list(ref), list(ref)
        variants = []
        for p, gt in zip(positions, gts):
            if gt == "1/1":
                h1[p] = h2[p] = sites[p]
            elif rng.random() < 0.5:
                h1[p] = sites[p]
            else:
                h2[p] = sites[p]
            a, b = word_at(ref, p)
            alt_word = ref[a:p] + sites[p] + ref[p + 1:b]
            variants.append({"pos": p, "alt": sites[p], "gt": gt,
                             "word_ref": ref[a:b], "word_alt": alt_word})
        return ["".join(h1), "".join(h2)], variants

    def sequence(haps, depth, err, rng):
        """Reads from random places on a random copy, with random errors.
        A read may hang off either end of the text and is clipped there."""
        L = len(haps[0])
        n = max(1, round(depth * L / READ_LEN))
        keep = READ_LEN // 2
        reads = []
        for _ in range(n):
            s = int(rng.integers(keep - READ_LEN, L - keep + 1))
            h = int(rng.integers(2))
            a, b = max(0, s), min(L, s + READ_LEN)
            seq = list(haps[h][a:b])
            for j in range(len(seq)):
                if rng.random() < err:
                    alts = [c for c in LETTERS + " " if c != seq[j].lower()]
                    seq[j] = alts[int(rng.integers(len(alts)))]
            reads.append({"start": a, "seq": "".join(seq), "hap": h + 1})
        return {"reads": reads, "depth": depth, "err": err,
                "read_len": READ_LEN}

    def pick_map_reads(reads, variants, rng, n=8):
        """A handful of reads for mapping by hand: one over each variant if
        possible (so the variants show up as red letters), then others."""
        ids = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        full = [i for i, r in enumerate(reads) if len(r["seq"]) >= 20]
        order = [full[i] for i in rng.permutation(len(full)).tolist()]
        chosen = []
        for v in variants:
            for i in order:
                r = reads[i]
                if i not in chosen and r["start"] <= v["pos"] < r["start"] + len(r["seq"]):
                    chosen.append(i)
                    break
        for i in order:
            if len(chosen) >= n:
                break
            if i not in chosen:
                chosen.append(i)
        chosen = chosen[:n]
        chosen = [chosen[i] for i in rng.permutation(len(chosen)).tolist()]
        return [{"id": ids[k], "seq": reads[i]["seq"], "start": reads[i]["start"]}
                for k, i in enumerate(chosen)]

    return draw_individual, fresh_sim, pick_map_reads, sequence


@app.cell
def _(TEXTS):
    GENERAL = [t for t in TEXTS if t["kind"] == "general"]
    TEXT_BY_TITLE = {t["title"]: t for t in GENERAL}
    GENOTYPE_REF_LEN = 300   # must match embed_texts.py
    READ_LEN = 30
    DEPTH = 10               # average reads covering each letter
    ERROR_RATE = 0.005       # 1 letter in 200

    def trim_words(text, n):
        """The first ~n characters of text, cut back to a word boundary."""
        if len(text) <= n:
            return text
        cut = text.rfind(" ", 0, n)
        return text[: cut if cut > 0 else n].rstrip()

    return (
        DEPTH,
        ERROR_RATE,
        GENERAL,
        GENOTYPE_REF_LEN,
        READ_LEN,
        TEXT_BY_TITLE,
        trim_words,
    )


@app.cell
def _():
    import html
    import json
    import re

    import marimo as mo
    import numpy as np

    # Deliberately unseeded: every student gets their own individual.
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
    return TEXTS, html, json, mo, re, rng


if __name__ == "__main__":
    app.run()
