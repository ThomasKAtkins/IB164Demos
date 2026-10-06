import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🎲 The Wright–Fisher Model: Evolution by Chance

    A population of **N** diploid individuals carries **2N** copies of a gene.
    Some copies are allele **A**, the rest are allele **a**. There is no
    selection, no mutation, no migration: neither allele is better than the
    other.

    Each generation, the parents die and their offspring replace them, and
    the 2N gene copies of the new generation are drawn **at random, with
    replacement**, from the copies in the old one. Like drawing marbles from
    a bag and putting each one back.

    Nothing pushes the frequency of A up or down, so does it stay where it
    started? **Choose a population size and a starting frequency, then
    step through some generations and see.**
    """)
    return


@app.cell
def _(DEFAULT_N, DEFAULT_P0, mo):
    # Each slider carries an editable box (include_input) for exact values.
    # N is a plain linear integer slider rather than a log-spaced `steps=`
    # ladder: with `steps`, marimo's value is an index into that list, so the
    # box could only pick among the ladder's entries, not any N. Small N is
    # cramped on a linear track, which is what the box is for.
    n_slider = mo.ui.slider(
        start=2,
        stop=1000,
        step=1,
        value=DEFAULT_N,
        include_input=True,
        label="Population size **N** (individuals)",
    )
    # Fine step so any frequency can be typed; it is still rounded to the
    # nearest whole number of gene copies (a multiple of 1/2N) at the start.
    p0_slider = mo.ui.slider(
        start=0.001,
        stop=0.999,
        step=0.001,
        value=DEFAULT_P0,
        include_input=True,
        label="Starting frequency of **A**, p₀",
    )
    mo.hstack([n_slider, p0_slider], justify="start", gap=3, wrap=True)
    return n_slider, p0_slider


@app.cell
def _(fresh_population, n_slider, p0_slider, set_pop):
    # Moving either slider starts a brand-new experiment. The faded past runs
    # are cleared too: they only mean something when compared at the SAME
    # settings, and the fixed/lost tally would otherwise mix experiments.
    set_pop(fresh_population(n_slider.value, p0_slider.value))
    return


@app.cell
def _(get_pop, mo):
    # Say exactly where the population starts. With exact values typed into
    # the boxes, a silent rounding to a whole number of gene copies (e.g.
    # p0 = 0.33 with N = 5 really starts at 3/10) would look like a bug.
    _pop = get_pop()
    _two_n = 2 * _pop["n"]
    _k = _pop["history"][0]
    _note = (
        ""
        if abs(_k / _two_n - _pop["p0"]) < 1e-9
        else f" (rounded from {_pop['p0']:g} to a whole number of copies)"
    )
    mo.md(
        f"<span style='color:#7a7382; font-size:0.9rem'>Starts with "
        f"**{_k} of {_two_n}** gene copies as A, so p₀ = "
        f"**{_k / _two_n:.4g}**{_note}.</span>"
    )
    return


@app.cell
def _(DEFAULT_N, DEFAULT_P0, mo, rng):
    # Safety cap for "until fixation". At N = 1000 and p0 = 0.5 the expected
    # absorption time is about 4N ln 2 ~ 2,800 generations, so this cap is
    # never reached in practice; it only guards against an endless loop.
    MAX_GENERATIONS = 100_000

    # How many faded past runs to keep on the plot.
    MAX_PAST = 50

    def starting_count(n, p0):
        # Frequencies live on a grid of 1/(2N): with N = 5 there are only ten
        # gene copies, so p0 = 0.33 is not reachable. Round to the nearest
        # count, but never all-or-nothing -- a population that starts fixed
        # has nothing to show.
        two_n = 2 * n
        return min(max(round(p0 * two_n), 1), two_n - 1)

    def fresh_population(n, p0):
        return {
            "n": n,
            "p0": p0,
            # history[t] = number of A copies in generation t.
            "history": [starting_count(n, p0)],
            # Each past run is its own history list, kept for the faded
            # traces and the fixed/lost tally.
            "past": [],
        }

    def is_absorbed(count, n):
        return count == 0 or count == 2 * n

    def advance(pop, generations):
        # The whole model is this one line:
        #     next count ~ Binomial(2N, current frequency)
        # Each of the 2N new gene copies independently picks a parent copy at
        # random, so it is A with probability p. The draw happens HERE,
        # inside the click handler, and the result is frozen into state --
        # drawing in a reactive cell would silently re-roll on every
        # re-render.
        n = pop["n"]
        two_n = 2 * n
        count = pop["history"][-1]
        new_counts = []
        for _ in range(generations):
            if is_absorbed(count, n):
                break
            count = int(rng.binomial(two_n, count / two_n))
            new_counts.append(count)
        if not new_counts:
            return pop
        return {**pop, "history": pop["history"] + new_counts}

    get_pop, set_pop = mo.state(fresh_population(DEFAULT_N, DEFAULT_P0))
    return (
        MAX_GENERATIONS,
        MAX_PAST,
        advance,
        fresh_population,
        get_pop,
        is_absorbed,
        set_pop,
    )


@app.cell
def _(MAX_GENERATIONS, MAX_PAST, advance, fresh_population, set_pop):
    # Updates are functional (set_pop receives a function of the current
    # state), so a click always acts on the freshest population. advance()
    # is a no-op once an allele is fixed or lost, so extra clicks are safe.
    def on_step(generations):
        set_pop(lambda pop: advance(pop, generations))

    def on_until_absorbed():
        set_pop(lambda pop: advance(pop, MAX_GENERATIONS))

    def on_new_population():
        def _update(pop):
            # Archive the run we are leaving, unless it never got going.
            past = pop["past"]
            if len(pop["history"]) > 1:
                past = (past + [pop["history"]])[-MAX_PAST:]
            return {**fresh_population(pop["n"], pop["p0"]), "past": past}

        set_pop(_update)
    return on_new_population, on_step, on_until_absorbed


@app.cell
def _(mo, on_new_population, on_step, on_until_absorbed):
    # This cell must NOT read the population state: re-running a cell that
    # creates a UI element resets it, so if these buttons depended on the
    # state they would be rebuilt on every click. Handlers write state; the
    # cells below read it; nothing does both.
    #
    # n_input is defined in this same cell and read only at click time,
    # inside the lambda. A cell is not re-run by changes to its own UI
    # elements, so typing a new n does not rebuild the buttons either.
    n_input = mo.ui.number(start=1, stop=10_000, step=1, value=10)

    step_one_button = mo.ui.button(
        label="▶ 1 generation",
        on_change=lambda v: on_step(1),
    )
    step_n_button = mo.ui.button(
        label="⏩ n generations",
        on_change=lambda v: on_step(int(n_input.value or 1)),
    )
    until_button = mo.ui.button(
        label="⏭ Until fixation / loss",
        kind="success",
        on_change=lambda v: on_until_absorbed(),
    )
    new_button = mo.ui.button(
        label="↺ New population",
        kind="neutral",
        on_change=lambda v: on_new_population(),
    )

    mo.hstack(
        [
            step_one_button,
            mo.hstack([step_n_button, mo.md("n ="), n_input], gap=0.4,
                      align="center", justify="start"),
            until_button,
            new_button,
        ],
        justify="start",
        align="center",
        gap=1,
        wrap=True,
    )
    return


@app.cell
def _(get_pop, is_absorbed, mo):
    _pop = get_pop()
    _n = _pop["n"]
    _two_n = 2 * _n
    _history = _pop["history"]
    _count = _history[-1]
    _gen = len(_history) - 1
    _p = _count / _two_n

    if _count == _two_n:
        _status, _status_colour = "A fixed", "#4C72B0"
        _status_sub = f"in generation {_gen}"
    elif _count == 0:
        _status, _status_colour = "A lost", "#DD8452"
        _status_sub = f"in generation {_gen}"
    else:
        _status, _status_colour = "Both alleles", "#7a7382"
        _status_sub = "still segregating"

    if _gen > 0:
        _change = _count - _history[-2]
        _freq_sub = f"{_count} of {_two_n} copies ({_change:+d} last gen)"
    else:
        _freq_sub = f"{_count} of {_two_n} copies"

    # Tally of FINISHED runs at these settings, current run included once it
    # finishes. Under pure drift the chance A eventually fixes is exactly its
    # starting frequency -- this is where students get to see that.
    _finished = [h for h in _pop["past"] if is_absorbed(h[-1], _n)]
    if is_absorbed(_count, _n):
        _finished = _finished + [_history]
    _n_fixed = sum(1 for h in _finished if h[-1] == _two_n)
    _n_done = len(_finished)
    _start_p = _history[0] / _two_n
    if _n_done:
        _tally_val = f"{_n_fixed} / {_n_done}"
        _tally_sub = f"runs fixed A ({_n_fixed / _n_done:.0%}; p₀ = {_start_p:.3g})"
    else:
        _tally_val = "–"
        _tally_sub = "no finished runs yet"

    mo.Html(f"""
    <style>
    .wf-cards {{
        display: flex; gap: 0.8rem; flex-wrap: wrap;
        padding: 0.4rem 0 0.2rem 0;
    }}
    .wf-card {{
        flex: 1 1 150px; border-radius: 12px; padding: 0.75rem 0.7rem;
        text-align: center; font-family: system-ui, sans-serif;
        border: 2px solid #d9d4cc; background: #fbfaf8;
    }}
    .wf-card-title {{
        font-size: 0.74rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.09em; color: #7a7382;
    }}
    .wf-card-val {{ font-size: 2.1rem; font-weight: 800; line-height: 1.2; color: #33302c; }}
    .wf-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
    </style>
    <div class="wf-cards">
      <div class="wf-card">
        <div class="wf-card-title">Generation</div>
        <div class="wf-card-val">{_gen}</div>
        <div class="wf-card-sub">N = {_n} &middot; 2N = {_two_n} gene copies</div>
      </div>
      <div class="wf-card" style="border-color:#4C72B0">
        <div class="wf-card-title">Frequency of A</div>
        <div class="wf-card-val" style="color:#4C72B0">{_p:.2f}</div>
        <div class="wf-card-sub">{_freq_sub}</div>
      </div>
      <div class="wf-card" style="border-color:{_status_colour}">
        <div class="wf-card-title">Status</div>
        <div class="wf-card-val" style="color:{_status_colour}; font-size:1.6rem; padding:0.15rem 0">{_status}</div>
        <div class="wf-card-sub">{_status_sub}</div>
      </div>
      <div class="wf-card">
        <div class="wf-card-title">Fixed / finished</div>
        <div class="wf-card-val">{_tally_val}</div>
        <div class="wf-card-sub">{_tally_sub}</div>
      </div>
    </div>
    """)
    return


@app.cell
def _(get_pop, mo):
    # The gene pool itself: one dot per gene copy in the CURRENT generation.
    # Sorted A-first so the frequency reads at a glance -- in the model the
    # copies have no positions, so nothing is lost by ordering them.
    _pop = get_pop()
    _two_n = 2 * _pop["n"]
    _count = _pop["history"][-1]

    if _two_n <= 400:
        _size = 22 if _two_n <= 40 else 14 if _two_n <= 200 else 10
        _dots = "".join(
            f'<span class="wf-dot" style="background:{"#4C72B0" if _i < _count else "#DD8452"}"></span>'
            for _i in range(_two_n)
        )
        _pool = f"""
        <style>
        .wf-pool {{ display: flex; flex-wrap: wrap; gap: 3px; padding: 0.3rem 0; }}
        .wf-dot {{ width: {_size}px; height: {_size}px; border-radius: 50%; display: inline-block; }}
        </style>
        <div class="wf-pool">{_dots}</div>
        """
    else:
        # Too many copies to draw individually; show the split as one bar.
        _pct = 100 * _count / _two_n
        _pool = f"""
        <div style="display:flex; height:22px; border-radius:6px; overflow:hidden; margin:0.3rem 0;">
          <div style="width:{_pct}%; background:#4C72B0"></div>
          <div style="width:{100 - _pct}%; background:#DD8452"></div>
        </div>
        """

    mo.Html(
        '<div style="font-family:system-ui,sans-serif; font-size:0.85rem; color:#7a7382; font-weight:600;">'
        'Gene pool this generation: '
        '<span style="color:#4C72B0">● A</span> &nbsp; '
        '<span style="color:#DD8452">● a</span></div>'
        + _pool
    )
    return


@app.cell
def _(get_pop, np, plt):
    _pop = get_pop()
    _two_n = 2 * _pop["n"]
    _history = np.array(_pop["history"]) / _two_n
    _past = _pop["past"]

    _fig, _ax = plt.subplots(figsize=(9, 4.6))

    # Past runs at the same settings, faded, so the spread of outcomes builds
    # up as students press "New population".
    for _h in _past:
        _ax.plot(np.arange(len(_h)), np.array(_h) / _two_n,
                 color="#9a938a", alpha=0.4, linewidth=1.0)

    _ax.axhline(_history[0], color="#33302c", linestyle="--", linewidth=1.0,
                alpha=0.6, label=f"starting frequency ({_history[0]:.3g})")
    _ax.plot(np.arange(len(_history)), _history, color="#4C72B0",
             linewidth=2.2, label="this population",
             marker="o" if len(_history) <= 40 else None, markersize=4)
    _ax.plot(len(_history) - 1, _history[-1], "o", color="#4C72B0",
             markersize=8, zorder=5)

    _longest = max([len(_history)] + [len(_h) for _h in _past])
    _ax.set_xlim(0, max(_longest - 1, 10))
    _ax.set_ylim(-0.03, 1.03)
    _ax.set_xlabel("generation")
    _ax.set_ylabel("frequency of A")
    _ax.set_title(f"Allele frequency under drift (N = {_pop['n']})")
    if _past:
        _ax.plot([], [], color="#9a938a", alpha=0.6,
                 label=f"previous runs ({len(_past)})")
    _ax.legend(loc="upper left", fontsize=9, framealpha=0.9)
    _ax.spines["top"].set_visible(False)
    _ax.spines["right"].set_visible(False)
    _fig.tight_layout()
    _ax
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What is going on?** (try it first!)": mo.md(
                r"""
                **The frequency wanders, even though nothing favours either
                allele.** This is **genetic drift**: change caused purely by the
                randomness of which gene copies happen to get passed on.

                Each generation the number of A copies is a binomial draw:

                $$k_{t+1} \sim \text{Binomial}\!\left(2N,\; p_t\right),
                \qquad p_t = \frac{k_t}{2N}$$

                - **On average nothing changes:** $E[p_{t+1}] = p_t$. Drift has
                  no direction.
                - **But every generation adds noise:**
                  $\operatorname{Var}(p_{t+1}) = \dfrac{p_t(1-p_t)}{2N}$.
                  Small populations take big random steps; large ones take tiny
                  steps. Compare N = 10 with N = 1000.
                - **0 and 1 are traps.** Once an allele is lost it cannot come
                  back without mutation, and once it is fixed there is no
                  longer anything to drift. So, given enough time, drift always
                  ends with one allele **fixed** and the other **lost**, and
                  genetic variation is used up.
                - **Which one wins is a coin toss weighted by the start:** the
                  probability that A eventually fixes is exactly $p_0$. Run
                  many populations to the end with *New population* and check
                  the tally against p₀.
                - **How long it takes scales with N.** Starting from
                  $p_0 = 0.5$, the expected time until one allele fixes is
                  $4N \ln 2 \approx 2.8N$ generations. A brand-new mutation
                  ($p_0 = 1/2N$) is usually lost within a few generations, but
                  the rare ones that fix take about $4N$ generations to do it.

                **The model's assumptions:** constant population size,
                non-overlapping generations, random mating, and no selection,
                mutation or migration. Real populations break all of these.
                Drift still happens in them, and population geneticists
                measure it with an *effective* population size, $N_e$, which
                is usually much smaller than the census count.
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

    # Slider defaults, kept here so the sliders and the initial state agree.
    DEFAULT_N = 20
    DEFAULT_P0 = 0.5

    # Deliberately unseeded: every student should get their own populations.
    rng = np.random.default_rng()
    return DEFAULT_N, DEFAULT_P0, mo, np, plt, rng


if __name__ == "__main__":
    app.run()
