import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🧮 How Much Variation? θ = 4Nμ

    A population of **N** diploid individuals carries **2N** copies of a DNA
    sequence, each **l = 1000** bases long. At the start every copy is
    **identical**: there is no variation at all.

    Each generation does two things, as in the Wright–Fisher model:

    1. **Drift.** Each of the 2N copies in the new generation comes from one
       of the 2N copies in the previous generation, each equally likely to
       be its parent.
    2. **Mutation.** Each site in each new copy mutates with probability
       **μ** per generation. We use the **infinite sites model**: every new
       mutation creates a new segregating site, and no site is ever mutated
       twice.

    The demo has three steps:

    1. **Run the population** and watch how much variation builds up.
    2. **Trace pairs of sequences back in time** to see *why* it ends up
       where it does.
    3. **Estimate θ from a sample**, with Tajima's estimator π, as you would
       with real data.

    ## 1. Run the population

    The plot tracks **π**, the average number of differences per site
    between two copies in the population. **Before you run it, predict:**
    will variation keep building up forever, since mutations keep arriving?
    Then run a few hundred generations at a time and see.
    """)
    return


@app.cell
def _(DEFAULTS, mo):
    n_slider = mo.ui.slider(
        start=5, stop=200, step=1, value=DEFAULTS["n"],
        include_input=True, label="Population size **N** (individuals)",
    )
    mu_slider = mo.ui.slider(
        start=0.0000001, stop=0.00002, step=0.0000001, value=DEFAULTS["mu"],
        include_input=True, label="Mutation rate **μ** (per site per generation)",
    )
    mo.vstack([n_slider, mu_slider], gap=0.6)
    return mu_slider, n_slider


@app.cell
def _(fresh_population, mu_slider, n_slider, set_pop):
    # Moving either slider starts a brand-new population, back at zero
    # variation: a history traced at one N and mu means nothing at another.
    set_pop(fresh_population(int(n_slider.value), float(mu_slider.value)))
    return


@app.cell
def _(DEFAULTS, mo, np, rng):
    LENGTH = DEFAULTS["length"]

    # At most this many points are recorded per click, so a long run doesn't
    # spend its time measuring diversity every single generation.
    MAX_POINTS_PER_RUN = 300

    # Rows of the traced-pairs table to keep.
    MAX_TRACES = 30

    NO_HITS = np.zeros(0, dtype=np.int64)

    def diversity(seqs):
        # Average number of differences between two copies (over ALL pairs),
        # and the number of segregating sites. A site contributes, to the
        # pair count, every pair whose bases differ there:
        #     C(n, 2) - sum over bases b of C(count_b, 2).
        # Only segregating sites can contribute, so count bases there alone:
        # one pass over the whole array instead of four.
        n = seqs.shape[0]
        pairs = n * (n - 1) / 2
        seqs = seqs[:, (seqs != seqs[0]).any(axis=0)]
        same = np.zeros(seqs.shape[1])
        for b in range(4):
            c = (seqs == b).sum(axis=0)
            same += c * (c - 1) / 2
        differing = pairs - same
        return differing.sum() / pairs, int((differing > 0).sum())

    def mutate(seqs, mu):
        # Mutates seqs IN PLACE; only ever called on a freshly drawn
        # generation, never on an array held in state.
        #
        # Infinite sites: a new mutation may only land on a site where every
        # copy is still the same (and only one mutation per site per
        # generation). One that falls on an already-variable site is moved to
        # a random unused site instead, so the number of mutations, and hence
        # mu, is unchanged.
        #
        # Returns the mutated array plus which copies (rows) and sites were
        # hit, so a pair's ancestry can later be traced mutation by mutation.
        two_n, length = seqs.shape
        m = int(rng.binomial(two_n * length, mu))
        if m == 0:
            return seqs, NO_HITS, NO_HITS
        rows = rng.integers(0, two_n, m)
        sites = rng.integers(0, length, m)

        ok = ~(seqs[:, sites] != seqs[0, sites]).any(axis=0)
        first = np.zeros(m, dtype=bool)
        first[np.unique(sites, return_index=True)[1]] = True
        ok &= first
        taken = set(sites[ok].tolist())
        for j in np.flatnonzero(~ok).tolist():
            for _ in range(100):
                s = int(rng.integers(0, length))
                if s not in taken and (seqs[:, s] == seqs[0, s]).all():
                    sites[j] = s
                    ok[j] = True
                    taken.add(s)
                    break

        rows, sites = rows[ok], sites[ok]
        shifts = rng.integers(1, 4, len(sites))
        seqs[rows, sites] = (seqs[rows, sites] + shifts) % 4
        return seqs, rows, sites

    def trace_pair(pop):
        # Follow two random copies of today's population back, parent by
        # parent, until they meet at their most recent common ancestor, and
        # collect the mutations that happened on each branch on the way.
        # Under infinite sites these are exactly the differences between the
        # two sequences. Randomness (which pair) is drawn here, in a click
        # handler, and frozen into state.
        g_now = pop["gen"]
        if g_now == 0:
            return pop
        i, j = (int(x) for x in rng.choice(2 * pop["n"], 2, replace=False))
        a, b = i, j
        branches = ([], [])  # (generations ago, site) for each branch
        tmrca = None
        for g in range(g_now, 0, -1):
            rows, sites = pop["muts"][g - 1]
            if len(rows):
                for k, idx in enumerate((a, b)):
                    for s in sites[rows == idx].tolist():
                        branches[k].append((g_now - g, s))
            parents = pop["parents"][g - 1]
            a, b = int(parents[a]), int(parents[b])
            if a == b:
                tmrca = g_now - g + 1
                break
        trace = {
            "i": i,
            "j": j,
            "gen": g_now,
            # None: the two lines have not met since generation 0, when every
            # copy was identical.
            "tmrca": tmrca,
            "branch_a": branches[0],
            "branch_b": branches[1],
        }
        return {**pop, "traces": (pop["traces"] + [trace])[-MAX_TRACES:]}

    def fresh_population(n, mu):
        ancestor = rng.integers(0, 4, LENGTH, dtype=np.int8)
        return {
            "n": n,
            "mu": mu,
            "seqs": np.tile(ancestor, (2 * n, 1)),
            "gen": 0,
            # Population pi per site, recorded as the run goes.
            "hist_gen": [0],
            "hist_pi": [0.0],
            "seg_frac": 0.0,
            # A random ordering of the 2N copies; the sample is its first n.
            # Drawn here and in the click handlers, never in a reactive cell.
            "order": rng.permutation(2 * n),
            # The full family history: parents[g - 1][c] is the copy in
            # generation g - 1 that copy c of generation g came from, and
            # muts[g - 1] = (copies, sites) mutated in generation g. Small
            # (a few hundred bytes a generation) and needed for tracing.
            "parents": [],
            "muts": [],
            # Pairs traced back so far, in the CURRENT generation.
            "traces": [],
        }

    def advance(pop, generations):
        # Drift then mutation, once per generation. All randomness is drawn
        # HERE, inside the click handler, and frozen into state.
        two_n = 2 * pop["n"]
        seqs = pop["seqs"]
        gen = pop["gen"]
        hist_gen = list(pop["hist_gen"])
        hist_pi = list(pop["hist_pi"])
        parents_hist = list(pop["parents"])
        muts_hist = list(pop["muts"])
        seg = pop["seg_frac"] * LENGTH
        stride = max(1, generations // MAX_POINTS_PER_RUN)
        for i in range(1, generations + 1):
            # Each new copy picks a random parent copy (Wright-Fisher). The
            # fancy index returns a NEW array, so mutating it in place never
            # touches the previous state.
            parents = rng.integers(0, two_n, two_n).astype(np.int16)
            seqs = seqs[parents]
            seqs, rows, sites = mutate(seqs, pop["mu"])
            parents_hist.append(parents)
            muts_hist.append((rows, sites))
            gen += 1
            if i % stride == 0 or i == generations:
                pi, seg = diversity(seqs)
                hist_gen.append(gen)
                hist_pi.append(pi / LENGTH)
        return {
            **pop,
            "seqs": seqs,
            "gen": gen,
            "hist_gen": hist_gen,
            "hist_pi": hist_pi,
            "seg_frac": seg / LENGTH,
            "order": rng.permutation(two_n),
            "parents": parents_hist,
            "muts": muts_hist,
            # Traced pairs belonged to the old generation; start afresh.
            "traces": [],
        }

    def resample(pop):
        return {**pop, "order": rng.permutation(2 * pop["n"])}

    get_pop, set_pop = mo.state(fresh_population(DEFAULTS["n"], DEFAULTS["mu"]))
    return (
        LENGTH,
        advance,
        fresh_population,
        get_pop,
        resample,
        set_pop,
        trace_pair,
    )


@app.cell
def _(advance, fresh_population, resample, set_pop, trace_pair):
    # Functional updates, so a click always acts on the freshest population.
    def on_step(generations):
        set_pop(lambda pop: advance(pop, generations))

    def on_new_population():
        set_pop(lambda pop: fresh_population(pop["n"], pop["mu"]))

    def on_new_sample():
        set_pop(resample)

    def on_trace():
        set_pop(trace_pair)

    return on_new_population, on_new_sample, on_step, on_trace


@app.cell
def _(mo, on_new_population, on_step):
    # This cell must NOT read the population state: re-running a cell that
    # creates a UI element resets it, so the buttons would be rebuilt on every
    # click. n_input is read only at click time, inside the lambda.
    n_input = mo.ui.number(start=1, stop=5000, step=1, value=100)

    step_ten_button = mo.ui.button(
        label="▶ 10 generations",
        on_change=lambda v: on_step(10),
    )
    step_n_button = mo.ui.button(
        label="⏩ n generations",
        kind="success",
        on_change=lambda v: on_step(int(n_input.value or 1)),
    )
    new_button = mo.ui.button(
        label="↺ New population",
        kind="neutral",
        on_change=lambda v: on_new_population(),
    )

    mo.hstack(
        [
            step_ten_button,
            mo.hstack([step_n_button, mo.md("n ="), n_input], gap=0.4,
                      align="center", justify="start"),
            new_button,
        ],
        justify="start",
        align="center",
        gap=1,
        wrap=True,
    )
    return


@app.cell
def _(LENGTH, get_pop, mo):
    _pop = get_pop()
    _two_n = 2 * _pop["n"]
    _pi_site = _pop["hist_pi"][-1]

    # Infinite sites needs variable sites to be a small fraction of the
    # sequence; past ~20% real sequences would be taking repeat hits.
    _warn = ""
    if _pop["seg_frac"] > 0.2:
        _warn = (
            '<div class="gd-warn">⚠️ <b>{:.0%} of sites are segregating in the '
            "population.</b> At this level, real sequences would start getting "
            "the same site hit twice, so the infinite sites model is breaking "
            "down. Try a smaller N or μ.</div>".format(_pop["seg_frac"])
        )

    mo.Html(f"""
    <style>
    .gd-cards {{ display: flex; gap: 0.8rem; flex-wrap: wrap; padding: 0.4rem 0 0.2rem; }}
    .gd-card {{
        flex: 1 1 170px; border-radius: 12px; padding: 0.75rem 0.7rem;
        text-align: center; font-family: system-ui, sans-serif;
        border: 2px solid #d9d4cc; background: #fbfaf8;
    }}
    .gd-card-title {{
        font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.08em; color: #7a7382;
    }}
    .gd-card-val {{ font-size: 2rem; font-weight: 800; line-height: 1.2; color: #33302c; }}
    .gd-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
    .gd-warn {{
        font-family: system-ui, sans-serif; font-size: 0.88rem; color: #6b4a12;
        background: #fbf0d9; border: 1px solid #e8cf9a; border-radius: 8px;
        padding: 0.5rem 0.7rem; margin-top: 0.4rem;
    }}
    </style>
    <div class="gd-cards">
      <div class="gd-card">
        <div class="gd-card-title">Generation</div>
        <div class="gd-card-val">{_pop["gen"]:,}</div>
        <div class="gd-card-sub">N = {_pop["n"]} &middot; 2N = {_two_n} sequences
          &middot; μ = {_pop["mu"]:.7f}</div>
      </div>
      <div class="gd-card" style="border-color:#4C72B0">
        <div class="gd-card-title">π in the whole population</div>
        <div class="gd-card-val" style="color:#4C72B0">{_pi_site:.4f}</div>
        <div class="gd-card-sub">per site &middot; two random copies differ at
          {_pi_site * LENGTH:.1f} of {LENGTH} sites on average</div>
      </div>
    </div>
    {_warn}
    """)
    return


@app.cell
def _(mo):
    show_theta = mo.ui.checkbox(label="Show θ = 4Nμ on the plot")
    show_theta
    return (show_theta,)


@app.cell
def _(get_pop, plt, show_theta):
    _pop = get_pop()
    _fig, _ax = plt.subplots(figsize=(9, 4.2))
    _ax.plot(_pop["hist_gen"], _pop["hist_pi"], color="#4C72B0", linewidth=2.0,
             label="π, whole population")
    _ax.plot(_pop["hist_gen"][-1], _pop["hist_pi"][-1], "o", color="#4C72B0",
             markersize=7, zorder=5)
    _top = max(_pop["hist_pi"])
    if show_theta.value:
        _theta = 4 * _pop["n"] * _pop["mu"]
        _ax.axhline(_theta, color="#C44E52", linestyle="--", linewidth=1.4,
                    label=f"θ = 4Nμ = {_theta:.4f}")
        _top = max(_top, _theta)
    _ax.set_xlim(0, max(_pop["gen"], 10))
    _ax.set_ylim(0, _top * 1.15 if _top > 0 else 0.01)
    _ax.set_xlabel("generation")
    _ax.set_ylabel("π (per site)")
    _ax.set_title(f"Variation in the population (N = {_pop['n']}, μ = {_pop['mu']:.7f})")
    _ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    _ax.spines["top"].set_visible(False)
    _ax.spines["right"].set_visible(False)
    _fig.tight_layout()
    _ax
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 2. Why does π stop growing? Trace two copies back in time

    Mutations keep arriving every generation, yet π levels off. To see why,
    pick **two copies** from today's population and follow each one back,
    parent by parent, until they reach a shared ancestor, their **most
    recent common ancestor (MRCA)**. When that ancestor lived, the two
    copies were one sequence. Every difference between them today is a
    mutation that happened on one of the two branches since then.

    Press the button a few times, at different stages of the run.
    """)
    return


@app.cell
def _(mo, on_trace):
    # Must not read the population state (see the run buttons).
    trace_button = mo.ui.button(
        label="🔍 Trace a random pair back",
        kind="success",
        on_change=lambda v: on_trace(),
    )
    trace_button
    return


@app.cell
def _(BASES, MaxNLocator, get_pop, mo, plt):
    _pop = get_pop()
    _traces = _pop["traces"]

    if _pop["gen"] == 0:
        _out = mo.md(
            "*Run the population for a while first: right now every copy "
            "is identical and there is no history to trace.*"
        )
    elif not _traces:
        _out = mo.md(f"*No pairs traced yet in generation {_pop['gen']:,}. "
                     "Press the button.*")
    else:
        _t = _traces[-1]
        _g = _t["gen"]
        _met = _t["tmrca"] is not None
        _depth = _t["tmrca"] if _met else _g
        _na, _nb = len(_t["branch_a"]), len(_t["branch_b"])
        _blue, _orange = "#4C72B0", "#DD8452"

        # The slide-14 picture: two tips today, joined at the MRCA, with
        # each mutation drawn where (when) it happened on its branch.
        _fig, _ax = plt.subplots(figsize=(4.6, 4.4))
        _xa, _xb, _xm = 0.15, 0.85, 0.5
        if _met:
            _ax.plot([_xa, _xm], [0, _depth], color=_blue, linewidth=2.5)
            _ax.plot([_xb, _xm], [0, _depth], color=_orange, linewidth=2.5)
            _ax.plot([_xm, _xm], [_depth, _depth * 1.12], color="#7a7382",
                     linewidth=2.5)
            _ax.plot(_xm, _depth, "o", color="#33302c", markersize=7, zorder=5)
            _ax.text(_xm + 0.04, _depth, "MRCA", va="center", fontsize=9,
                     fontweight="bold", color="#33302c")

            def _pos(x0, ago):
                f = (ago + 0.5) / _depth
                return x0 + (_xm - x0) * f, ago + 0.5
        else:
            _ax.plot([_xa, _xa], [0, _depth], color=_blue, linewidth=2.5)
            _ax.plot([_xb, _xb], [0, _depth], color=_orange, linewidth=2.5)
            _ax.axhline(_depth, color="#7a7382", linestyle=":", linewidth=1.2)
            _ax.text(_xm, _depth * 1.03, "generation 0: every copy identical",
                     ha="center", va="top", fontsize=8.5, color="#7a7382")

            def _pos(x0, ago):
                return x0, ago + 0.5

        for _x0, _branch, _c in ((_xa, _t["branch_a"], _blue),
                                 (_xb, _t["branch_b"], _orange)):
            for _ago, _site in _branch:
                _px, _py = _pos(_x0, _ago)
                _ax.plot(_px, _py, marker="o", markersize=8, color="#C44E52",
                         markeredgecolor="white", zorder=6)

        _ax.text(_xa, -0.03 * _depth, "copy A", ha="center", va="bottom",
                 fontsize=9, fontweight="bold", color=_blue)
        _ax.text(_xb, -0.03 * _depth, "copy B", ha="center", va="bottom",
                 fontsize=9, fontweight="bold", color=_orange)
        _ax.set_ylim(_depth * 1.18, -0.12 * _depth)
        _ax.set_xlim(0, 1)
        _ax.set_xticks([])
        _ax.set_ylabel("generations ago")
        _ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        for _side in ("top", "right", "bottom"):
            _ax.spines[_side].set_visible(False)
        _ax.plot([], [], "o", color="#C44E52", label="a mutation")
        _ax.legend(loc="lower left", fontsize=8.5, frameon=False)
        _fig.tight_layout()

        if _met:
            _story = (
                f"Copies A and B last shared an ancestor "
                f"**T<sub>MRCA</sub> = {_depth:,} generations ago**. "
                f"Since then, **{_na}** mutation{'s' if _na != 1 else ''} "
                f"happened on A's branch and **{_nb}** on B's, so today they "
                f"differ at **d = {_na + _nb}** sites."
            )
        else:
            _story = (
                f"Copies A and B **have not met yet**: their ancestry runs "
                f"all the way back to generation 0 (**{_g:,} generations "
                f"ago**), when every copy was identical. Since then "
                f"**{_na}** mutation{'s' if _na != 1 else ''} happened on "
                f"A's line and **{_nb}** on B's, so they differ at "
                f"**d = {_na + _nb}** sites."
            )

        # The two sequences, one line each; each difference coloured by the
        # branch its mutation happened on.
        _seqs = _pop["seqs"]
        _sa, _sb = _seqs[_t["i"]], _seqs[_t["j"]]
        _on_a = {s for _, s in _t["branch_a"]}
        _on_b = {s for _, s in _t["branch_b"]}

        def _row(seq, mine, cls):
            out = []
            for k in range(len(seq)):
                ch = BASES[seq[k]]
                if k in mine:
                    out.append(f'<span class="{cls}">{ch}</span>')
                elif k in _on_a or k in _on_b:
                    out.append(f'<span class="gd-pale">{ch}</span>')
                else:
                    out.append(ch)
            return "".join(out)

        _seq_html = f"""
        <style>
        .gd-wrap {{
            display: flex; background: #fbfaf8; border: 1px solid #e4e0d8;
            border-radius: 10px; padding: 0.6rem 0.8rem; gap: 0.6rem;
        }}
        .gd-lab {{
            font-family: system-ui, sans-serif; font-size: 0.78rem;
            font-weight: 700; color: #7a7382; white-space: nowrap;
            height: 28px; line-height: 28px;
        }}
        .gd-scroll {{
            overflow-x: auto; flex: 1 1 auto; min-width: 0;
            font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
            font-size: 1rem; padding-bottom: 0.3rem;
        }}
        .gd-line {{
            white-space: pre; color: #33302c; width: max-content;
            height: 28px; line-height: 28px;
        }}
        .gd-legend {{ font-family: system-ui, sans-serif; font-size: 0.82rem;
                      color: #7a7382; margin-top: 0.3rem; }}
        .gd-pa {{ background: {_blue}; color: #fff; font-weight: 800; border-radius: 2px; }}
        .gd-pb {{ background: {_orange}; color: #fff; font-weight: 800; border-radius: 2px; }}
        .gd-pale {{ background: #ece8e1; color: #6d6660; font-weight: 700; border-radius: 2px; }}
        </style>
        <div class="gd-wrap">
          <div>
            <div class="gd-lab" style="color:{_blue}">Copy A</div>
            <div class="gd-lab" style="color:{_orange}">Copy B</div>
          </div>
          <div class="gd-scroll">
            <div class="gd-line">{_row(_sa, _on_a, "gd-pa")}</div>
            <div class="gd-line">{_row(_sb, _on_b, "gd-pb")}</div>
          </div>
        </div>
        <div class="gd-legend">
          <span class="gd-pa">&nbsp;X&nbsp;</span> mutated on A's branch &nbsp;&nbsp;
          <span class="gd-pb">&nbsp;X&nbsp;</span> mutated on B's branch &nbsp;&nbsp;
          <span class="gd-pale">&nbsp;X&nbsp;</span> the other copy, still the
          ancestral base &nbsp;&nbsp;·&nbsp;&nbsp; scroll sideways →
        </div>
        """

        # Every pair traced in this generation, so students can look for the
        # pattern themselves (no expected values shown).
        _rows = []
        for _k, _tr in enumerate(_traces, start=1):
            _a, _b = len(_tr["branch_a"]), len(_tr["branch_b"])
            _tm = f"{_tr['tmrca']:,}" if _tr["tmrca"] is not None else (
                f"not met (&gt; {_tr['gen']:,})")
            _rows.append(f"<tr><td>{_k}</td><td>{_tm}</td><td>{_a}</td>"
                         f"<td>{_b}</td><td><b>{_a + _b}</b></td></tr>")
        _met_t = [_tr["tmrca"] for _tr in _traces if _tr["tmrca"] is not None]
        _ds = [len(_tr["branch_a"]) + len(_tr["branch_b"]) for _tr in _traces]
        _avg_t = f"{sum(_met_t) / len(_met_t):,.0f}" if _met_t else "–"
        _avg_row = (
            f'<tr class="gd-avg"><td>average</td><td>{_avg_t}</td><td></td>'
            f"<td></td><td><b>{sum(_ds) / len(_ds):.1f}</b></td></tr>"
            if len(_traces) > 1 else ""
        )
        _table = f"""
        <style>
        .gd-tt {{ border-collapse: collapse; font-family: system-ui, sans-serif;
                  font-size: 0.86rem; }}
        .gd-tt th, .gd-tt td {{ padding: 0.25rem 0.7rem; text-align: center;
                                border-bottom: 1px solid #ece8e1; }}
        .gd-tt th {{ color: #7a7382; font-size: 0.75rem; }}
        .gd-tt .gd-avg td {{ border-top: 2px solid #d9d4cc; font-weight: 700; }}
        </style>
        <div style="font-family:system-ui,sans-serif; font-size:0.85rem;
                    color:#7a7382; font-weight:600; margin-bottom:0.2rem">
          Pairs traced in generation {_pop['gen']:,}
          (N = {_pop['n']}, so 2N = {2 * _pop['n']})</div>
        <div style="max-height:260px; overflow-y:auto">
        <table class="gd-tt">
          <tr><th>pair</th><th>T<sub>MRCA</sub> (generations)</th>
              <th>mutations on A's branch</th><th>on B's branch</th>
              <th>d (differences)</th></tr>
          {''.join(_rows)}
          {_avg_row}
        </table>
        </div>
        """

        _out = mo.vstack([
            mo.hstack([_ax, mo.vstack([mo.md(_story), mo.Html(_table)],
                                      gap=0.8)],
                      widths=[1, 1.4], align="start", gap=1.5, wrap=True),
            mo.Html(_seq_html),
        ], gap=0.8)
    _out
    return


@app.cell
def _(mo):
    mo.md(r"""
    **Questions to explore**

    - Trace several pairs late in a run, once π has levelled off. How do
      their $T_{MRCA}$ values compare with $2N$? Then press *New population*,
      run it just as long, and trace again. (Pairs from one population share
      one family tree, so their $T_{MRCA}$ values rise and fall together; a
      single population can sit well above or below $2N$. Compare across
      several populations.) Try a different N.
    - Each branch is $T_{MRCA}$ generations long and gains about $\mu l$
      mutations per generation. Using that, how many differences d would you
      expect for one pair? Check it against the table.
    - Now trace pairs **early** in a run (after 20 or 50 generations). What
      is different? Why does π keep rising while most pairs "have not met
      yet", and stop rising once they have?
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 3. Estimating θ from a sample

    In real life we can't sequence the whole population, only a sample. Here
    is a random sample of n sequences from the current generation. Count
    $d_{ij}$, the number of differences between sequences $i$ and $j$, for
    every pair. Tajima's estimator averages them over the $n(n-1)/2$ pairs
    and divides by the sequence length $l$:

    $$\pi = \frac{1}{l}\,\frac{\sum_{i<j} d_{ij}}{n(n-1)/2}$$

    Because $E[\pi] = \theta$, π is our estimate of θ, written $\hat\theta_T$.
    """)
    return


@app.cell
def _(mo, on_new_sample):
    # Must not read the population state (see the run buttons).
    sample_slider = mo.ui.slider(
        start=2, stop=10, step=1, value=5, include_input=True,
        label="Sample size **n** (sequences)",
    )
    sample_button = mo.ui.button(
        label="🎲 New sample",
        on_change=lambda v: on_new_sample(),
    )
    mo.hstack([sample_slider, sample_button], justify="start", align="center",
              gap=2, wrap=True)
    return (sample_slider,)


@app.cell
def _(BASES, get_pop, mo, np, sample_slider):
    _pop = get_pop()
    _seqs = _pop["seqs"]
    _k = min(int(sample_slider.value), _seqs.shape[0])
    _sample = _seqs[_pop["order"][:_k]]
    _length = _seqs.shape[1]

    # Population consensus at each site: the base most copies carry. In a
    # column that varies within the sample, bases that differ from it are
    # highlighted (the new mutation, almost always).
    _counts = np.stack([(_seqs == _b).sum(axis=0) for _b in range(4)])
    _consensus = _counts.argmax(axis=0)
    _variable = (_sample != _sample[0]).any(axis=0)
    _n_var = int(_variable.sum())

    def row_html(seq):
        out = []
        for i in range(_length):
            ch = BASES[seq[i]]
            if not _variable[i]:
                out.append(ch)
            elif seq[i] != _consensus[i]:
                out.append(f'<span class="gd-mut">{ch}</span>')
            else:
                out.append(f'<span class="gd-col">{ch}</span>')
        return "".join(out)

    # One unbroken line per sequence inside ONE horizontally scrolling box,
    # so the rows stay lined up; students have not met wrapped alignments.
    _labels = "".join(f'<div class="gd-lab">Seq {_i + 1}</div>' for _i in range(_k))
    _lines = "".join(f'<div class="gd-line">{row_html(_s)}</div>' for _s in _sample)

    mo.vstack([
        mo.md(f"This sample has **{_n_var}** segregating sites, out of "
              f"l = {_length}."),
        mo.Html(f"""
        <style>
        .gd-wrap {{
            display: flex; background: #fbfaf8; border: 1px solid #e4e0d8;
            border-radius: 10px; padding: 0.6rem 0.8rem; gap: 0.6rem;
        }}
        .gd-lab {{
            font-family: system-ui, sans-serif; font-size: 0.78rem;
            font-weight: 700; color: #7a7382; white-space: nowrap;
            height: 28px; line-height: 28px;
        }}
        .gd-scroll {{
            overflow-x: auto; flex: 1 1 auto; min-width: 0;
            font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
            font-size: 1rem; padding-bottom: 0.3rem;
        }}
        .gd-line {{
            white-space: pre; color: #33302c; width: max-content;
            height: 28px; line-height: 28px;
        }}
        .gd-mut {{
            background: #C44E52; color: #fff; font-weight: 800; border-radius: 2px;
        }}
        .gd-col {{
            background: #f6d6d7; color: #9e2a2f; font-weight: 700; border-radius: 2px;
        }}
        .gd-legend {{ font-family: system-ui, sans-serif; font-size: 0.82rem;
                      color: #7a7382; margin-top: 0.3rem; }}
        </style>
        <div class="gd-wrap">
          <div>{_labels}</div>
          <div class="gd-scroll">{_lines}</div>
        </div>
        <div class="gd-legend">
          <span class="gd-mut">&nbsp;X&nbsp;</span> differs from the common base
          &nbsp;&nbsp;
          <span class="gd-col">&nbsp;X&nbsp;</span> common base, at a segregating
          site
          &nbsp;&nbsp;·&nbsp;&nbsp; scroll sideways to see the whole sequence →
        </div>
        """),
    ], gap=0.4)
    return


@app.cell
def _(get_pop, mo, sample_slider):
    _pop = get_pop()
    _seqs = _pop["seqs"]
    _k = min(int(sample_slider.value), _seqs.shape[0])
    _sample = _seqs[_pop["order"][:_k]]
    _length = _seqs.shape[1]

    # Upper triangle only, so each pair is counted exactly once.
    _diffs = {}
    for _i in range(_k):
        for _j in range(_i + 1, _k):
            _diffs[(_i, _j)] = int((_sample[_i] != _sample[_j]).sum())
    _n_pairs = len(_diffs)
    _total = sum(_diffs.values())
    _pi = _total / _n_pairs

    _head = "".join(f"<th>Seq {_j + 1}</th>" for _j in range(1, _k))
    _body = []
    for _i in range(_k - 1):
        _cells = []
        for _j in range(1, _k):
            if _j > _i:
                _cells.append(f'<td class="gd-d">{_diffs[(_i, _j)]}</td>')
            else:
                _cells.append('<td class="gd-blank"></td>')
        _body.append(f"<tr><th>Seq {_i + 1}</th>{''.join(_cells)}</tr>")

    mo.Html(f"""
    <style>
    .gd-tab {{ border-collapse: collapse; font-family: system-ui, sans-serif;
               font-size: 0.9rem; margin: 0.3rem 0; }}
    .gd-tab th {{ color: #7a7382; font-weight: 700; padding: 0.3rem 0.6rem;
                  font-size: 0.78rem; }}
    .gd-tab td {{ text-align: center; padding: 0.3rem 0.6rem;
                  min-width: 2.6rem; }}
    .gd-d {{ background: #eef2f9; border: 1px solid #d5ddeb; color: #33302c;
             font-weight: 700; }}
    .gd-blank {{ background: transparent; }}
    .gd-calc {{ font-family: system-ui, sans-serif; font-size: 0.95rem;
                color: #33302c; margin-top: 0.5rem; line-height: 1.7; }}
    .gd-calc b.v {{ color: #C44E52; }}
    </style>
    <div style="font-family:system-ui,sans-serif; font-size:0.85rem;
                color:#7a7382; font-weight:600;">
      d<sub>ij</sub>: the number of differences between sequences i and j</div>
    <div style="overflow-x:auto">
      <table class="gd-tab">
        <tr><th></th>{_head}</tr>
        {''.join(_body)}
      </table>
    </div>
    <div class="gd-calc">
      Sum of all d<sub>ij</sub> = {_total} &nbsp;&middot;&nbsp;
      pairs: n(n−1)/2 = {_k}×{_k - 1}/2 = {_n_pairs} &nbsp;&middot;&nbsp;
      average d<sub>ij</sub> = {_total} / {_n_pairs} = {_pi:.2f}<br>
      π = (1/l) × {_pi:.2f} = {_pi:.2f} / {_length} =
      <b class="v">{_pi / _length:.4f}</b> per site
      &nbsp;=&nbsp; θ̂<sub>T</sub>, our estimate of θ
    </div>
    """)
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What is going on?** (try steps 1 and 2 first!)": mo.md(
                r"""
                **Two phases.** Step 2 shows them directly.

                - **Early on, π grows like a molecular clock.** Few pairs have
                  met since the start, so each pair's two lines run all the way
                  back to generation 0, when every copy was identical. After
                  $t$ generations they have collected about $2\mu t$
                  differences per site, so π keeps rising with $t$.
                - **Later, π levels off.** Drift keeps merging lines: each
                  generation, two lines pick the same parent with chance
                  $\frac{1}{2N}$. Once the run is much longer than $2N$
                  generations, almost every pair has met, typically about
                  $2N$ generations back, and running longer doesn't push that
                  meeting point further into the past. The branches stop
                  getting longer, so π stops growing.

                Seen forwards in time, this is a balance between **mutation**,
                which adds new variants every generation, and **drift**, which
                loses most of them and fixes a few.

                **Why that level is $4N\mu$.** Pick two copies of the
                sequence and trace them back in time. Each generation, the
                chance that they share a parent (coalesce) is $\frac{1}{2N}$,
                so on average their most recent common ancestor (MRCA) lived

                $$E(T_{MRCA}) = 2N \text{ generations ago.}$$

                Over $r$ generations, a lineage gains $\mu r$ mutations per
                site. There are **two** lineages running back to the MRCA,
                each of length $2N$, so the expected number of differences
                between the two copies, per site, is

                $$\theta = 2 \times 2N \times \mu = 4N\mu.$$

                **Tajima's estimator.** Under infinite sites, every mutation
                on either lineage is one difference, so $E[d_{ij}] = \theta$
                for every pair. Averaging over all $n(n-1)/2$ pairs keeps the
                same expectation, so $E[\pi] = \theta$: π is an estimate of
                θ, written $\hat\theta_T$.

                **Small populations coalesce faster**, so there is less time
                for mutations to build up between copies: smaller θ, less
                genetic variability. Large populations coalesce more slowly
                and carry more variability.

                **Things to try**
                - Run until π levels off. Roughly how many generations does
                  that take? Does it change with $N$?
                - Double $N$, then double $\mu$ instead. Does variation
                  respond in the same way? Can you tell, from the sequences
                  alone, whether a population is large with a low mutation
                  rate or small with a high one?
                - Press *New sample* several times. How much does
                  $\hat\theta_T$ change between samples? Does a bigger sample
                  help? (Even the whole population's π wobbles, because the
                  population has only one genealogy.)
                - Tick *Show θ = 4Nμ* and compare it with where π settles.

                **From θ to population size.** If we know μ, measuring θ
                tells us N. For a real population, the N we get this way is
                the **effective population size** $N_e$: the size of a
                Wright–Fisher population that would show the same amount of
                drift. It is often very different from the census size.
                """
            )
        }
    )
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator

    plt.rcParams["figure.dpi"] = 120

    BASES = "ACGT"

    # 4 * N * mu * l = 2 differences between two copies at the defaults,
    # reached after a few hundred generations.
    DEFAULTS = {"length": 1000, "n": 50, "mu": 0.00001}

    # Deliberately unseeded: every student should get their own population.
    rng = np.random.default_rng()
    return BASES, DEFAULTS, MaxNLocator, mo, np, plt, rng


if __name__ == "__main__":
    app.run()
