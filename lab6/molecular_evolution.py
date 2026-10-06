import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🧬 Molecular Evolution: Differences as a Clock

    Two populations split from a common ancestor. At the moment of the split
    they carry **the same DNA sequence**, L = 1000 bases long. From then on, each lineage collects
    its own random mutations, and the two sequences drift apart.

    In this model, each lineage gains on average **μ** new mutations per
    generation across its whole sequence (μ is the mutation rate **per
    genome** per generation). Each mutation lands on a random site and
    changes it to one of the other three bases. As in class, mutation is rare enough
    that **no site is ever hit twice**, so every mutation leaves a visible
    difference.

    **Set the mutation rate and the number of generations, then press Run.**
    The differences between the two sequences are highlighted. Then ask:
    *if you only had the two sequences, how long ago would you say they
    split?*
    """)
    return


@app.cell
def _(DEFAULTS, mo, on_new_ancestor, on_run):
    # The settings are read only when Run is pressed (inside the lambda), so
    # moving a slider never changes a result already on screen: each result
    # belongs to exactly the settings it was run with, and says so.
    #
    # This cell must not read the simulation state: re-running a cell that
    # creates UI elements resets them, so a click would wipe the sliders.
    mu_slider = mo.ui.slider(
        start=0.001, stop=0.1, step=0.001, value=DEFAULTS["mu"],
        include_input=True, label="Mutation rate **μ** (per genome per generation)",
    )
    gens_slider = mo.ui.slider(
        start=1, stop=1000, step=1, value=DEFAULTS["generations"],
        include_input=True, label="Generations since the split **t**",
    )

    run_button = mo.ui.button(
        label="▶ Run simulation",
        kind="success",
        on_change=lambda v: on_run(
            DEFAULTS["length"], float(mu_slider.value),
            int(gens_slider.value),
        ),
    )
    new_button = mo.ui.button(
        label="↺ New ancestor sequence",
        kind="neutral",
        on_change=lambda v: on_new_ancestor(DEFAULTS["length"]),
    )

    mo.vstack(
        [
            mu_slider,
            gens_slider,
            mo.hstack([run_button, new_button], justify="start", gap=1),
        ],
        gap=0.6,
    )
    return


@app.cell
def _(np, rng):
    BASES = "ACGT"

    def random_sequence(length):
        return rng.integers(0, 4, size=length).tolist()

    def simulate(ancestor, mu, generations):
        # mu is the PER-GENOME rate: expected new mutations per lineage per
        # generation across the whole sequence. Spread evenly over L sites,
        # that is a per-site chance of mu / L each generation.
        # Two identical copies of the ancestor, then mutation in each lineage
        # independently. All randomness is drawn HERE, inside the click
        # handler, and frozen into state -- drawing in a reactive cell would
        # silently re-roll on every re-render.
        #
        # The model: each generation, each site in each lineage mutates with
        # probability mu / L, to one of the other three bases, and no site ever
        # mutates twice (the infinite-sites assumption) -- once a site has
        # mutated in EITHER lineage it is used up.
        #
        # Rather than loop over every generation, draw directly the
        # generation of each site's first mutation in each lineage: with a
        # per-generation chance p = mu / L, that waiting time is Geometric(p). A site
        # ends up mutated if the earlier of its two waiting times falls within
        # the run, and it belongs to whichever lineage got there first (ties
        # go to lineage 1, as if it mutated first that generation). This is
        # exactly the generation-by-generation process, just without the loop.
        n_sites = len(ancestor)
        first_hit = rng.geometric(mu / n_sites, size=(2, n_sites))
        mutated = first_hit.min(axis=0) <= generations
        # owner[i] = which lineage (0 or 1) mutated site i, or -1 if neither.
        owner = np.where(mutated, first_hit.argmin(axis=0), -1)

        seqs = (list(ancestor), list(ancestor))
        sites = np.flatnonzero(mutated)
        shifts = rng.integers(1, 4, size=len(sites))
        for s, shift in zip(sites.tolist(), shifts.tolist()):
            lineage = int(owner[s])
            seqs[lineage][s] = (seqs[lineage][s] + shift) % 4

        return {
            "mu": mu,
            "generations": generations,
            "a": seqs[0],
            "b": seqs[1],
            "owner": owner.tolist(),
            "n_diff": len(sites),
        }

    return BASES, random_sequence, simulate


@app.cell
def _(DEFAULTS, mo, random_sequence):
    # One state dict: the ancestor, plus the result of the last run (None
    # until Run is pressed). They are replaced together so they never
    # disagree.
    get_sim, set_sim = mo.state(
        {"ancestor": random_sequence(DEFAULTS["length"]), "result": None}
    )
    return get_sim, set_sim


@app.cell
def _(random_sequence, set_sim, simulate):
    def on_run(length, mu, generations):
        def _update(sim):
            # Re-running keeps the same ancestor, so students can rerun and
            # see that the SAME setup gives a different number of differences
            # each time. (The length is fixed, so the check below is only a
            # guard.)
            ancestor = sim["ancestor"]
            if len(ancestor) != length:
                ancestor = random_sequence(length)
            return {
                "ancestor": ancestor,
                "result": simulate(ancestor, mu, generations),
            }

        set_sim(_update)

    def on_new_ancestor(length):
        set_sim({"ancestor": random_sequence(length), "result": None})

    return on_new_ancestor, on_run


@app.cell
def _(mo):
    show_ancestor = mo.ui.checkbox(
        label="Show the common ancestor (which lineage changed?)"
    )
    show_ancestor
    return (show_ancestor,)


@app.cell
def _(BASES, get_sim, mo, show_ancestor):
    _sim = get_sim()
    _anc = _sim["ancestor"]
    _res = _sim["result"]
    _n = len(_anc)

    if _res is None:
        _a = _b = _anc
        _owner = [-1] * _n
        _heading = (
            "**Before the split:** two identical copies of the ancestral "
            "sequence. Press **Run simulation**."
        )
    else:
        _a, _b = _res["a"], _res["b"]
        _owner = _res["owner"]
        _d = sum(1 for _o in _owner if _o >= 0)
        _heading = (
            f"**After {_res['generations']:,} generations** at "
            f"μ = {_res['mu']:.8f}".rstrip("0") + f": **{_d}** of {_n} sites differ."
        )

    def row_html(seq, lineage, idx, owner):
        # A differing site is highlighted in BOTH lineages; the lineage whose
        # base actually changed gets the strong colour, the other (still the
        # ancestral base) a pale one. lineage=None is the ancestor row.
        out = []
        for i in idx:
            ch = BASES[seq[i]]
            if lineage is None or owner[i] < 0:
                out.append(ch)
            elif owner[i] == lineage:
                out.append(f'<span class="me-mut">{ch}</span>')
            else:
                out.append(f'<span class="me-other">{ch}</span>')
        return "".join(out)

    # One unbroken line per sequence, all inside ONE horizontally scrolling
    # box so the rows stay lined up as it scrolls. Wrapping into blocks (the
    # usual alignment format) confused students who have not met it.
    _idx = range(_n)
    _rows = []
    if show_ancestor.value:
        _rows.append(("Ancestor", row_html(_anc, None, _idx, _owner), True))
    _rows.append(("Lineage 1", row_html(_a, 0, _idx, _owner), False))
    _rows.append(("Lineage 2", row_html(_b, 1, _idx, _owner), False))
    _labels = "".join(
        f'<div class="me-lab{" me-anc" if _faint else ""}">{_lab}</div>'
        for _lab, _, _faint in _rows
    )
    _lines = "".join(
        f'<div class="me-line{" me-anc" if _faint else ""}">{_html}</div>'
        for _, _html, _faint in _rows
    )

    mo.vstack([
        mo.md(_heading),
        mo.Html(f"""
        <style>
        .me-wrap {{
            display: flex; background: #fbfaf8; border: 1px solid #e4e0d8;
            border-radius: 10px; padding: 0.6rem 0.8rem; gap: 0.6rem;
        }}
        .me-lab {{
            font-family: system-ui, sans-serif; font-size: 0.78rem;
            font-weight: 700; color: #7a7382; white-space: nowrap;
            height: 28px; line-height: 28px;
        }}
        .me-scroll {{
            overflow-x: auto; flex: 1 1 auto; min-width: 0;
            font-family: ui-monospace, "Cascadia Mono", Consolas, monospace;
            font-size: 1rem; padding-bottom: 0.3rem;
        }}
        .me-line {{
            white-space: pre; color: #33302c; width: max-content;
            height: 28px; line-height: 28px;
        }}
        .me-anc {{ color: #9a938a; }}
        .me-mut {{
            background: #C44E52; color: #fff; font-weight: 800; border-radius: 2px;
        }}
        .me-other {{
            background: #f6d6d7; color: #9e2a2f; font-weight: 700; border-radius: 2px;
        }}
        .me-legend {{ font-family: system-ui, sans-serif; font-size: 0.82rem;
                      color: #7a7382; margin-top: 0.3rem; }}
        </style>
        <div class="me-wrap">
          <div class="me-labels">{_labels}</div>
          <div class="me-scroll">{_lines}</div>
        </div>
        <div class="me-legend">
          <span class="me-mut">&nbsp;X&nbsp;</span> mutated in this lineage
          &nbsp;&nbsp;
          <span class="me-other">&nbsp;X&nbsp;</span> unchanged here, but the
          other lineage mutated
          &nbsp;&nbsp;·&nbsp;&nbsp; scroll sideways to see the whole sequence →
        </div>
        """),
    ], gap=0.4)
    return


@app.cell
def _(get_sim, mo):
    _res = get_sim()["result"]
    if _res is None:
        mo.output.replace(None)
    else:
        _n = len(_res["a"])
        _d = _res["n_diff"]

        # Only the observed count is shown. The expected D (2*mu*t) and the
        # clock estimate of t (D / 2*mu) are deliberately left for students
        # to work out.

        # The no-double-hits assumption needs mutated sites to be a small
        # fraction of the sequence. Past ~20% a real sequence would be taking
        # repeat hits that this model forbids, so say so rather than let the
        # demo quietly mislead.
        _frac = _d / _n
        _warn = ""
        if _frac > 0.2:
            _warn = (
                '<div class="me-warn">⚠️ <b>{:.0%} of sites have mutated.</b> '
                "At this level, real sequences would start getting the same "
                "site hit twice, so the class assumption is breaking "
                "down. Try a smaller μ or fewer "
                "generations.</div>".format(_frac)
            )

        mo.output.replace(mo.Html(f"""
        <style>
        .me-cards {{ display: flex; gap: 0.8rem; flex-wrap: wrap; padding: 0.3rem 0; }}
        .me-card {{
            flex: 0 1 220px; border-radius: 12px; padding: 0.75rem 0.7rem;
            text-align: center; font-family: system-ui, sans-serif;
            border: 2px solid #d9d4cc; background: #fbfaf8;
        }}
        .me-card-title {{
            font-size: 0.72rem; font-weight: 800; text-transform: uppercase;
            letter-spacing: 0.08em; color: #7a7382;
        }}
        .me-card-val {{ font-size: 2rem; font-weight: 800; line-height: 1.2; color: #33302c; }}
        .me-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
        .me-warn {{
            font-family: system-ui, sans-serif; font-size: 0.88rem; color: #6b4a12;
            background: #fbf0d9; border: 1px solid #e8cf9a; border-radius: 8px;
            padding: 0.5rem 0.7rem; margin-top: 0.4rem;
        }}
        </style>
        <div class="me-cards">
          <div class="me-card" style="border-color:#C44E52">
            <div class="me-card-title">Differences observed</div>
            <div class="me-card-val" style="color:#C44E52">{_d}</div>
            <div class="me-card-sub">D, one per mutation</div>
          </div>
        </div>
        {_warn}
        """))
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What is going on?** (run it a few times first!)": mo.md(
                r"""
                **Differences between sequences are a clock.** Each lineage
                gains about $\mu$ new mutations per generation ($\mu$ is the
                rate per genome). There are **two** lineages, each
                mutating independently since the split, so after $t$
                generations the expected number of differences is

                $$E[D] = 2\mu t.$$

                Because no site mutates twice, every mutation shows up as
                exactly one difference, and nothing is ever hidden. Turn this
                around and you can read time off the sequences:

                $$\hat{t} = \frac{D}{2\mu}.$$

                This is the **molecular clock**. Note the factor of 2: the
                differences between two species measure the time back to their
                common ancestor *twice*, once down each branch.

                **The clock ticks randomly.** Press Run several times with the
                same settings. $D$ changes from run to run (it is roughly
                Poisson, so its spread is about $\sqrt{2\mu t}$), and so does
                the estimate of $t$. Short times, with only a few
                differences, give especially noisy clocks.

                **Things to try**
                - Double $t$. Does $D$ double?
                - Double $\mu$ instead. Can you tell, from the sequences alone,
                  whether the lineages split long ago with a slow rate, or
                  recently with a fast one? (This is why a clock must be
                  *calibrated*, e.g. with a dated fossil.)
                - Tick *Show the common ancestor*. In real data we almost
                  never have the ancestor, so we see that two sequences differ
                  but not which lineage changed.
                - Real genomes are far bigger than 1000 bases: a human child
                  carries roughly 60 new mutations that neither parent had.
                  Spread over the billions of sites in a genome, though, that
                  is only about $10^{-8}$ per site, which is why the "no site
                  mutates twice" assumption is reasonable for closely related
                  species.
                """
            )
        }
    )
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np

    # The sequence length is fixed (no slider) at 1000 bases. About
    # 2 * mu * t = 20 differences at the defaults (mu is per genome).
    # Generations are capped at 1000 so the fraction of sites mutated,
    # 2 * mu * t / L, stays small (at most 0.2, at the highest mu): only
    # then is D / (2 * mu) a good estimate of t.
    DEFAULTS = {"length": 1000, "mu": 0.01, "generations": 1000}

    # Deliberately unseeded: every student should get their own mutations.
    rng = np.random.default_rng()
    return DEFAULTS, mo, np, rng


if __name__ == "__main__":
    app.run()
