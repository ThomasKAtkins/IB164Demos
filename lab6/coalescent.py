import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🌳 The Coalescent: Tracing Genes Back in Time

    The Wright–Fisher model runs **forwards**: each generation, the 2N gene
    copies are drawn at random from the copies in the generation before.
    The coalescent runs the same model **backwards**.

    Below, every dot is one gene copy in today's population (generation 0).
    **Pick two of them**, then **step back in time** one generation at a
    time. At each step every copy picks its parent at random from the
    generation before (the red lines), and you follow your two copies'
    ancestry (blue). Keep going until both land on the **same parent**:
    their lineages **coalesce**, and that copy is their **most recent
    common ancestor (MRCA)**.

    How many generations back do you have to go? Try it a few times, in
    small populations and in larger ones.
    """)
    return


@app.cell
def _(DEFAULT_N, MAX_N, mo):
    # Small on purpose: every gene copy of every generation is drawn, so 2N
    # has to stay countable. Linear with an editable box, as in the
    # Wright-Fisher demo.
    n_slider = mo.ui.slider(
        start=1,
        stop=MAX_N,
        step=1,
        value=DEFAULT_N,
        include_input=True,
        label="Population size **N** (individuals; 2N gene copies)",
    )
    n_slider
    return (n_slider,)


@app.cell
def _(mo, n_slider):
    # Recreated (and so cleared) whenever N changes, because the copies on
    # offer change. Numbers match the labels on the top row of the plot.
    picker = mo.ui.multiselect(
        options={f"copy {i + 1}": i for i in range(2 * n_slider.value)},
        max_selections=2,
        label="Pick **two** gene copies from today to follow back in time",
    )
    picker
    return (picker,)


@app.cell
def _(fresh_trace, n_slider, picker, set_coal):
    # A new N or a new pair starts a fresh trace from generation 0.
    set_coal(fresh_trace(n_slider.value, picker.value))
    return


@app.cell
def _(DEFAULT_N, mo, rng):
    def fresh_trace(n_pop, picks):
        picks = sorted(picks or [])
        return {
            "n": n_pop,
            # The two copies being followed, or fewer while still picking.
            "picks": picks if len(picks) == 2 else picks[:1],
            # parents[g][i]: the copy in generation g+1 (one further back)
            # that copy i of generation g came from. Grows one row per step.
            "parents": [],
            # Generations back at which the two lineages met, once they have.
            "met_at": None,
        }

    def lineage_positions(state):
        # Where the two followed lineages are in the oldest row drawn.
        a, b = state["picks"]
        for row in state["parents"]:
            a, b = row[a], row[b]
        return a, b

    def step_back(state):
        # One generation further into the past: EVERY copy in the current
        # oldest row picks a parent uniformly from the 2N copies before it,
        # exactly the Wright-Fisher model. The draw happens here, inside the
        # click's state update, and is frozen into state -- drawing in a
        # render cell would re-roll on every re-render. A no-op until two
        # copies are picked, and once the lineages have met.
        if len(state["picks"]) != 2 or state["met_at"] is not None:
            return state
        two_n = 2 * state["n"]
        parents = state["parents"] + [rng.integers(two_n, size=two_n).tolist()]
        new = {**state, "parents": parents}
        a, b = lineage_positions(new)
        if a == b:
            new["met_at"] = len(parents)
        return new

    get_coal, set_coal = mo.state(fresh_trace(DEFAULT_N, []))
    return fresh_trace, get_coal, lineage_positions, set_coal, step_back


@app.cell
def _(fresh_trace, set_coal, step_back):
    # Functional updates, so a click always acts on the freshest state.
    def on_step():
        set_coal(step_back)

    def on_restart():
        # Same population size and same two copies, new random history.
        set_coal(lambda s: fresh_trace(s["n"], s["picks"]))
    return on_restart, on_step


@app.cell
def _(mo, on_restart, on_step):
    # This cell must NOT read the trace state: re-running a cell that
    # creates a UI element resets it, so if these buttons depended on the
    # state they would be rebuilt on every click.
    step_button = mo.ui.button(
        label="⬇ Back one generation",
        kind="success",
        on_change=lambda v: on_step(),
    )
    restart_button = mo.ui.button(
        label="↺ Start over (same two copies)",
        kind="neutral",
        on_change=lambda v: on_restart(),
    )
    mo.hstack([step_button, restart_button], justify="start", gap=1, wrap=True)
    return


@app.cell
def _(get_coal, lineage_positions, mo):
    _s = get_coal()
    _gen = len(_s["parents"])
    _picks = _s["picks"]

    if len(_picks) < 2:
        _following = "–"
        _following_sub = "pick two copies above"
        _status, _status_colour = "Waiting", "#7a7382"
        _status_sub = "choose two copies to start"
    else:
        _following = f"{_picks[0] + 1} & {_picks[1] + 1}"
        _following_sub = "gene copies from generation 0"
        if _s["met_at"] is not None:
            _status, _status_colour = "Coalesced!", "#3B7BBF"
            _status_sub = (f"their common ancestor lived {_s['met_at']} "
                           f"generation{'s' if _s['met_at'] != 1 else ''} ago")
        else:
            _a, _b = lineage_positions(_s)
            _status, _status_colour = "Two lineages", "#D6404A"
            _status_sub = (f"now copies {_a + 1} and {_b + 1} of generation "
                           f"−{_gen}; keep going back")

    mo.Html(f"""
    <style>
    .co-cards {{
        display: flex; gap: 0.8rem; flex-wrap: wrap;
        padding: 0.4rem 0 0.2rem 0;
    }}
    .co-card {{
        flex: 1 1 150px; border-radius: 12px; padding: 0.75rem 0.7rem;
        text-align: center; font-family: system-ui, sans-serif;
        border: 2px solid #d9d4cc; background: #fbfaf8;
    }}
    .co-card-title {{
        font-size: 0.74rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.09em; color: #7a7382;
    }}
    .co-card-val {{ font-size: 2.1rem; font-weight: 800; line-height: 1.2; color: #33302c; }}
    .co-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
    </style>
    <div class="co-cards">
      <div class="co-card">
        <div class="co-card-title">Following</div>
        <div class="co-card-val">{_following}</div>
        <div class="co-card-sub">{_following_sub}</div>
      </div>
      <div class="co-card">
        <div class="co-card-title">Generations back</div>
        <div class="co-card-val">{_gen}</div>
        <div class="co-card-sub">N = {_s["n"]} &middot; 2N = {2 * _s["n"]} gene copies</div>
      </div>
      <div class="co-card" style="border-color:{_status_colour}">
        <div class="co-card-title">Status</div>
        <div class="co-card-val" style="color:{_status_colour}; font-size:1.6rem; padding:0.15rem 0">{_status}</div>
        <div class="co-card-sub">{_status_sub}</div>
      </div>
    </div>
    """)
    return


@app.cell
def _(MIN_ROWS, get_coal, plt):
    _s = get_coal()
    _parents = _s["parents"]
    _two_n = 2 * _s["n"]
    _depth = len(_parents)
    _picks = _s["picks"]
    _met = _s["met_at"] is not None
    _red, _blue, _grey = "#D6404A", "#3B7BBF", "#9a938a"

    # Copies on the followed lineages, row by row. Once the two meet they
    # share a copy, so use sets.
    _on_path = [set(_picks)]
    for _g in range(_depth):
        _on_path.append({_parents[_g][_i] for _i in _on_path[_g]})

    # Fixed vertical room for MIN_ROWS generations so the plot does not
    # rescale on every step; it extends only when the trace goes deeper.
    _rows = max(_depth, MIN_ROWS)
    _crowd = max(_two_n, _rows / 2)
    _dot = max(1.5, min(3.5, 40 / _crowd))
    _thin = max(0.4, min(0.9, 10 / _crowd))
    _thick = max(1.4, min(2.4, 25 / _crowd))

    _fig, _axes = plt.subplots(1, 3, figsize=(10, 5.6), sharey=True)

    def _draw_genealogy(ax, xpos):
        # Red: every parent link in the population. Blue: the followed
        # lineages, drawn on top.
        for _g in range(_depth):
            for _i in range(_two_n):
                _is_blue = _i in _on_path[_g]
                ax.plot([xpos(_g, _i), xpos(_g + 1, _parents[_g][_i])],
                        [-_g, -_g - 1],
                        color=_blue if _is_blue else _red,
                        linewidth=_thick if _is_blue else _thin,
                        zorder=3 if _is_blue else 2)
        for _g in range(_depth + 1):
            ax.plot([xpos(_g, _i) for _i in range(_two_n)], [-_g] * _two_n,
                    "o", color=_red if _picks else _grey, markersize=_dot,
                    zorder=2)
            ax.plot([xpos(_g, _i) for _i in _on_path[_g]],
                    [-_g] * len(_on_path[_g]), "o", color=_blue,
                    markersize=_dot * 1.6, zorder=4)

    # Panel 1: the genealogy as it is built, step by step. The top row is
    # numbered to match the picker.
    _ax = _axes[0]
    _draw_genealogy(_ax, lambda g, i: i)
    for _i in range(_two_n):
        _ax.annotate(str(_i + 1), (_i, 0), xytext=(0, 7),
                     textcoords="offset points", ha="center",
                     fontsize=8 if _two_n <= 12 else 6,
                     color=_blue if _i in _picks else "#33302c",
                     fontweight="bold" if _i in _picks else "normal")
    if _met:
        _mrca = next(iter(_on_path[_depth]))
        _ax.plot(_mrca, -_depth, "o", color="#33302c",
                 markersize=_dot * 2.2, zorder=5)
    _ax.set_title("genealogy", pad=14)

    if _met:
        # Panel 2: sorted genealogy. Keep the oldest row as is, then place
        # each younger row in order of its parents' places (ties by original
        # order): siblings sit together and no two lines cross. Shown only
        # at the end, since every new row would reshuffle the whole layout.
        _rank = [None] * (_depth + 1)
        _rank[_depth] = list(range(_two_n))
        for _g in range(_depth - 1, -1, -1):
            _order = sorted(range(_two_n),
                            key=lambda i, g=_g: (_rank[g + 1][_parents[g][i]], i))
            _rank[_g] = [0] * _two_n
            for _place, _i in enumerate(_order):
                _rank[_g][_i] = _place
        _draw_genealogy(_axes[1], lambda g, i: _rank[g][i])

        # Panel 3: the coalescent tree, just the two sampled copies joining
        # at their MRCA, with the MRCA's lineage continuing a little further.
        _ax = _axes[2]
        _left, _right, _mid = 0, _two_n - 1, (_two_n - 1) / 2
        for _x0 in (_left, _right):
            _ax.plot([_x0, _mid], [0, -_depth], color=_blue, linewidth=2)
        _ax.plot([_mid, _mid], [-_depth, -_depth - 0.6], color=_blue,
                 linewidth=2)
        _ax.plot([_left, _right], [0, 0], "o", color=_blue, markersize=6,
                 zorder=4, linestyle="none")
        for _x0, _p in ((_left, _picks[0]), (_right, _picks[1])):
            _ax.annotate(str(_p + 1), (_x0, 0), xytext=(0, 7),
                         textcoords="offset points", ha="center", fontsize=8,
                         color=_blue, fontweight="bold")
        _ax.plot(_mid, -_depth, "o", color="#33302c", markersize=7, zorder=5)
        _ax.annotate(f"MRCA, {_depth} generation{'s' if _depth != 1 else ''} ago",
                     (_mid, -_depth), xytext=(8, 0), textcoords="offset points",
                     fontsize=9, va="center", color="#33302c")
    else:
        _hint = ("revealed when the\ntwo lineages meet" if len(_picks) == 2
                 else "pick two copies,\nthen step back")
        for _a in _axes[1:]:
            _a.text(0.5, 0.5, _hint, transform=_a.transAxes, ha="center",
                    va="center", fontsize=10, color=_grey, style="italic")
    _axes[1].set_title("sorted genealogy", pad=14)
    _axes[2].set_title("coalescent tree", pad=14)

    _step = 2 if _rows <= 12 else max(2, round(_rows / 6 / 2) * 2)
    for _a in _axes:
        _a.set_xlim(-0.6, _two_n - 0.4)
        _a.set_xticks([])
        _a.tick_params(axis="y", length=0)
        for _side in ("top", "right", "bottom", "left"):
            _a.spines[_side].set_visible(False)
    _axes[0].set_ylim(-_rows - 0.8, 0.6)
    _axes[0].set_yticks(range(0, -_rows - 1, -_step))
    _axes[0].set_ylabel("generation (0 = today)")
    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What is going on?** (try it first!)": mo.md(
                r"""
                **Any two gene copies share an ancestor, and in a small
                population that ancestor is recent.** Each step back, your two
                lineages each pick a parent from the 2N copies, so they pick
                the **same** parent with probability $\frac{1}{2N}$. That
                makes the wait until they coalesce about **2N generations** on
                average, but very variable: sometimes the two copies are
                siblings, sometimes it takes several times longer.

                - **Bigger populations, older ancestors.** The chance of
                  meeting each generation is $\frac{1}{2N}$, so doubling the
                  population doubles the typical wait.
                - **Most copies leave no descendants.** In the sorted
                  genealogy, follow lines up from the bottom: many copies in
                  each past generation have no line reaching today. Their
                  lineages died out by chance. That is drift, the same thing
                  the Wright–Fisher demo shows forwards in time.
                - **The coalescent tree ignores everyone else.** The red
                  lines are the whole population's history, which we never
                  observe. The tree on the right is all the two copies' DNA
                  can tell us about, and its depth carries information about
                  the population's size.

                **The connection to drift.** Forward in time, drift means some
                gene copies leave many descendants and others none; backward
                in time, the same randomness makes lineages run into each
                other. Both happen faster in small populations, and both are
                governed by the *effective* population size $N_e$, which is
                why the depth of real gene trees is used to estimate it.
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

    plt.rcParams["figure.dpi"] = 120

    # Kept small so every gene copy of every generation can be drawn.
    MAX_N = 10
    DEFAULT_N = 3

    # Vertical room reserved in the plot, in generations, so it does not
    # rescale with every step until the trace goes deeper than this.
    MIN_ROWS = 10

    # Deliberately unseeded: every student should get their own histories.
    rng = np.random.default_rng()
    return DEFAULT_N, MAX_N, MIN_ROWS, mo, plt, rng


if __name__ == "__main__":
    app.run()
