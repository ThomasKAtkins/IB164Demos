import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🪱 The Parasite That Isn't There Any More

    Britain, 1850. Pick anyone in this village and there is a good chance
    they are sharing their body with an intestinal worm. Roundworm,
    whipworm, hookworm — for essentially the whole of human evolution,
    helminths were not a disease you caught. They were a condition you
    lived in, like weather.

    An immune system built in that world has a hard job. A helminth is
    large, long-lived, and actively secretes molecules that damp its host's
    immune response down. To hold one in check you need to push back, and
    hard. Natural selection obliged: it tuned the human immune thermostat
    **up**, to a setting that made sense against something pushing down.

    Then, in about a century, we removed the worms. Sanitation, clean
    water, shoes, anthelmintics. The push from the other side vanished.

    The thermostat did not move. It is still set for a parasite that is no
    longer there, and all that surplus push now lands on pollen, on
    peanuts, and on our own tissue.

    **Press play.** Watch the blue line — the immune setting this world
    would actually reward — fall away, and watch the brown line fail to
    follow it.
    """)
    return


@app.cell
def _(mo):
    # Kill the playback flicker.
    #
    # marimo flags a cell's output as STALE the instant that cell is queued,
    # and clears the flag when the run finishes. Its stylesheet dims stale
    # output:
    #     .marimo-output-stale                       { opacity: .8 }
    #     .marimo-output-stale.marimo-output-loading { opacity: .4 }
    # both with `transition: all .3s .2s`.
    #
    # During playback the ticker re-runs these cells about eight times a
    # second, so every output on the page cycles 1 -> .8 -> .4 -> 1 over and
    # over -- which is the pulsing fade. It is a CSS state class on the
    # output WRAPPER, so nothing about what we render inside it can avoid
    # the dimming; it has to be switched off directly.
    #
    # The selector is over-specified (and !important) to outrank marimo's own
    # `.marimo-cell.stale .output-area...` rule, and the transition is
    # cleared so no residual fade is left behind. Applying it globally is
    # deliberate: the cards and the village scene pulse for exactly the same
    # reason as the plots do.
    mo.Html(
        """
        <style>
        html body .marimo-output-stale,
        html body .marimo-output-stale.marimo-output-loading,
        html body .marimo-cell.stale .output-area.marimo-output-stale,
        html body .marimo-cell.stale .output-area.marimo-output-stale.marimo-output-loading,
        html body .marimo-cell.stale .console-output-area.marimo-output-stale {
            opacity: 1 !important;
            filter: none !important;
            transition: none !important;
        }
        </style>
        """
    )
    return


@app.cell
def _(np):
    # --- The environment: helminth prevalence, 1850-2020 -------------------
    #
    # `worms` runs from ~0.91 (a village where most people carry a worm) down
    # to ~0.02 (the industrialised world today). The shape is historical
    # rather than fitted, and it is deliberately the sum of TWO declines,
    # because the real one had two distinct causes:
    #
    #   - a slow arm centred ~1900: sanitation, sewers, clean water, shoes.
    #     Hookworm goes first because it enters through bare feet.
    #   - a fast arm centred ~1948: mass anthelmintics and public deworming
    #     campaigns, which took out what plumbing had left behind.
    #
    # Weighted 0.35 / 0.65, so the mid-century collapse dominates -- that is
    # what makes the environment outrun the population rather than merely
    # drifting away from it.
    YEAR_START = 1850
    YEAR_END = 2020

    def worms_at(year):
        early = 1.0 / (1.0 + np.exp((year - 1900.0) / 26.0))
        late = 1.0 / (1.0 + np.exp((year - 1948.0) / 11.0))
        # The 0.02 floor is not decoration. Helminths were never eradicated --
        # roughly a quarter of the world still carries one -- and a floor of
        # exactly zero would quietly imply they were.
        return 0.02 + 0.93 * (0.35 * early + 0.65 * late)

    years_all = np.arange(YEAR_START, YEAR_END + 1)
    worm_all = worms_at(years_all)
    return YEAR_END, YEAR_START, worm_all, years_all


@app.cell
def _(np):
    # --- The trait, the optimum, and one generation of selection -----------
    #
    # One continuous trait: immune reactivity set-point, `r`, on an arbitrary
    # 0-1 axis. Low = heavily damped, lots of regulatory braking. High =
    # aggressive, inflammatory, quick to escalate.
    #
    # A single quantitative trait standing in for the whole immune system is
    # a large simplification and is flagged as such in the accordion. It is
    # the right one for this argument because the claim being made is about a
    # SET-POINT moving relative to an optimum, and that claim needs an axis
    # to move along.
    R_LOW, R_HIGH = 0.20, 0.80

    # Standing variation in the population, held constant. Real stabilising
    # selection erodes variance; holding it fixed keeps the picture legible
    # and, importantly, is the CONSERVATIVE choice -- eroding it would make
    # the population respond even more slowly, so the mismatch shown here is
    # if anything an underestimate.
    TRAIT_SD = 0.11

    # Width of the fitness function. Larger omega = flatter, more forgiving
    # selection. 0.28 is chosen so that being badly mismatched costs real
    # fitness without driving anyone to zero.
    OMEGA = 0.28

    # Heritability. Illustrative: immune traits are substantially heritable,
    # and 0.5 is a round teaching value rather than an estimate of anything.
    H2 = 0.5

    # THE most important number in the notebook. A human generation is ~25
    # years, so 1850-2020 is SIX generations. Everything else here is
    # scenery; this is the reason the mismatch never closes.
    GEN_YEARS = 25

    def r_opt_at(worms):
        # With worms everywhere the optimum is a high set-point: you are
        # holding down something that is actively pushing up. Wormless, there
        # is nothing to push against, and the same setting now overshoots
        # onto self-tissue and harmless antigens. So the optimum FALLS as the
        # century turns -- the inverse of the peppered moth, where the target
        # rose and the population climbed after it. Here the target drops out
        # from under a population that cannot follow.
        return R_LOW + (R_HIGH - R_LOW) * worms

    # Trait grid, used for both the density and the exact selection
    # differential. 801 points over [0, 1] is fine enough that the numerical
    # mean matches the analytic one to well past the third decimal, which is
    # all the card ever prints.
    R_GRID = np.linspace(0.0, 1.0, 801)

    def fitness(r, opt):
        # Gaussian stabilising selection about the current optimum.
        return np.exp(-0.5 * ((r - opt) / OMEGA) ** 2)

    def step_generation(mean, opt):
        # The breeder's equation, R = h2 * S, with the selection differential
        # S computed EXACTLY from the population distribution rather than
        # approximated. The alternative (a closed-form Gaussian shortcut)
        # would be faster and would quietly stop being right if anyone later
        # made the fitness function non-Gaussian; this version stays honest
        # and the whole history is precomputed once anyway, so the cost is
        # invisible.
        _d = np.exp(-0.5 * ((R_GRID - mean) / TRAIT_SD) ** 2)
        _d = _d / _d.sum()
        _w = fitness(R_GRID, opt)
        _wbar = float((_d * _w).sum())
        _mean_after_selection = float((_d * _w * R_GRID).sum() / _wbar)
        _S = _mean_after_selection - mean
        return mean + H2 * _S

    def run_history(years, opt_series):
        # Selection acts once per GENERATION, not once per year. Stepping
        # per-year with a scaled response would let the population creep
        # smoothly after the optimum and would hide the actual mechanism:
        # there are only six discrete chances to respond in this entire
        # timeline, and the curve should visibly move in steps.
        mean = float(opt_series[0])  # starts matched -- see the 1850 card
        out = np.empty(len(years))
        last_gen = years[0]
        for i, year in enumerate(years):
            if year - last_gen >= GEN_YEARS:
                mean = step_generation(mean, float(opt_series[i]))
                last_gen = year
            out[i] = mean
        return out

    return R_GRID, R_HIGH, TRAIT_SD, fitness, r_opt_at, run_history


@app.cell
def _(YEAR_START, mo):
    # A single state dict holds the playhead. Separate states for "year" and
    # "playing" would let a render catch one updated and the other stale.
    get_clock, set_clock = mo.state({"year": YEAR_START, "playing": False})
    return get_clock, set_clock


@app.cell
def _(YEAR_END, YEAR_START, set_clock):
    # Writers only. This cell must not read get_clock -- see the button cell
    # below for why.
    STEP_YEARS = 2

    def on_play_pause():
        set_clock(lambda c: {**c, "playing": not c["playing"]})

    def on_rewind():
        set_clock({"year": YEAR_START, "playing": False})

    def on_step():
        set_clock(
            lambda c: {
                **c,
                "year": min(c["year"] + STEP_YEARS, YEAR_END),
                "playing": False,
            }
        )

    def on_tick():
        # Advancing stops at the end of the timeline and clears the playing
        # flag, so the refresh loop below goes quiet instead of spinning on a
        # finished animation.
        def _update(c):
            if not c["playing"]:
                return c
            year = c["year"] + STEP_YEARS
            if year >= YEAR_END:
                return {"year": YEAR_END, "playing": False}
            return {**c, "year": year}

        set_clock(_update)

    return on_play_pause, on_rewind, on_step, on_tick


@app.cell
def _(mo, on_play_pause, on_rewind, on_step):
    # Deliberately does NOT read get_clock: re-running a cell that builds a
    # UI element resets that element, so a button cell that depended on the
    # clock would be rebuilt on every single animation tick and would drop
    # clicks. Handlers write, render cells read, and these buttons do
    # neither.
    play_button = mo.ui.button(
        label="▶  Play  /  ⏸  Pause",
        kind="success",
        on_change=lambda v: on_play_pause(),
    )
    step_button = mo.ui.button(
        label="Step forward",
        on_change=lambda v: on_step(),
    )
    rewind_button = mo.ui.button(
        label="⏮  Back to 1850",
        kind="danger",
        on_change=lambda v: on_rewind(),
    )
    return play_button, rewind_button, step_button


@app.cell
def _(mo, on_tick):
    # mo.ui.refresh is a timer that re-runs its dependents on an interval.
    # It drives the animation; the handler itself checks the playing flag, so
    # while paused the ticks arrive and do nothing.
    ticker = mo.ui.refresh(
        default_interval="0.12s",
        options=["0.12s"],
        on_change=lambda v: on_tick(),
    )
    return (ticker,)


@app.cell
def _(R_HIGH, np, r_opt_at, run_history, worm_all, years_all):
    # The whole 170-year history is computed ONCE, not per animation frame --
    # the playhead just indexes into it. Recomputing inside the render cell
    # would re-run the selection loop on every tick and the animation would
    # crawl.
    opt_history = r_opt_at(worm_all)
    mean_history = run_history(years_all, opt_history)

    # Mismatch: how far the population's set-point sits ABOVE the setting this
    # world would reward. Signed, so the card can say which direction.
    mismatch = mean_history - opt_history

    # Autoimmune / allergic prevalence, as a share of the population.
    #
    # Read the caveat in the accordion before trusting this line for anything.
    # It is defined as a monotone function of the mismatch, which means the
    # notebook CANNOT fail to show disease rising as worms vanish. That is a
    # property of the model, not a finding. P_MAX is set so 2020 lands near
    # the real ~5-10% figure for the industrialised world -- calibrated to
    # look right, not derived.
    P_MAX = 0.11
    prevalence = P_MAX * np.clip(mismatch, 0.0, None) / (R_HIGH - 0.20)
    return mean_history, mismatch, opt_history, prevalence


@app.cell
def _(YEAR_START, get_clock, np, years_all):
    # Index of the playhead into the precomputed arrays.
    _year = get_clock()["year"]
    idx = int(np.clip(_year - YEAR_START, 0, len(years_all) - 1))
    current_year = int(years_all[idx])
    return current_year, idx


@app.cell
def _(np):
    # Villager positions are fixed once, rather than redrawn each frame. If
    # they were re-randomised on every tick the whole village would visibly
    # shuffle 8 times a second and the colour change -- the thing we actually
    # want watched -- would be lost in the noise.
    #
    # Two INDEPENDENT ranks per person, because worms and autoimmunity are two
    # different lotteries: who carries a worm in 1850 tells you nothing about
    # who develops coeliac disease in 2010. Sharing one rank would make the
    # sickest people in the clean world be exactly the wormiest people in the
    # dirty one, which is a claim this notebook is not making.
    N_VILLAGERS = 60
    _rng = np.random.default_rng(1989)  # 1989, for Strachan
    worm_rank = _rng.permutation(N_VILLAGERS) / float(N_VILLAGERS)
    ill_rank = _rng.permutation(N_VILLAGERS) / float(N_VILLAGERS)
    return N_VILLAGERS, ill_rank, worm_rank


@app.cell
def _(
    N_VILLAGERS,
    current_year,
    idx,
    ill_rank,
    mo,
    prevalence,
    worm_all,
    worm_rank,
):
    _worms = float(worm_all[idx])
    _prev = float(prevalence[idx])

    # Each villager is in exactly one of three states, resolved in this order:
    # worm first, then illness, then well. Resolving worm first is a modelling
    # choice with a point behind it -- in the wormy world almost nobody is in
    # the "autoimmune" state, which is the observation the whole hypothesis
    # started from.
    _dots = []
    for _i in range(N_VILLAGERS):
        if worm_rank[_i] < _worms:
            _fill, _ring = "#8a5a2b", "rgba(0,0,0,0.20)"
        elif ill_rank[_i] < _prev:
            _fill, _ring = "#C44E52", "rgba(0,0,0,0.20)"
        else:
            _fill, _ring = "#8a8177", "rgba(0,0,0,0.13)"
        _dots.append(
            f'<div class="hm-person" style="background:{_fill};'
            f'box-shadow:inset 0 0 0 1px {_ring};"></div>'
        )

    _n_worm = sum(1 for _i in range(N_VILLAGERS) if worm_rank[_i] < _worms)
    _n_ill = sum(
        1
        for _i in range(N_VILLAGERS)
        if worm_rank[_i] >= _worms and ill_rank[_i] < _prev
    )

    # The <style> block is re-emitted with its markup on every render. Cell
    # output ordering is not reliable in a WASM export, so a stylesheet parked
    # in some other cell may not have arrived yet; shipping it alongside the
    # thing it styles is idempotent and always in time.
    _html = f"""
    <style>
    .hm-yearbar {{
        display: flex; align-items: baseline; justify-content: center;
        gap: 1.4rem; font-family: system-ui, sans-serif;
        padding: 0.55rem 0 0.15rem 0;
    }}
    .hm-year {{
        font-size: 2.5rem; font-weight: 800; letter-spacing: 0.01em;
        color: #33302c;
    }}
    .hm-readout {{ font-size: 0.95rem; color: #6f6960; font-weight: 600; }}
    .hm-readout b {{ color: #33302c; }}
    .hm-village {{
        display: grid;
        grid-template-columns: repeat(20, 1fr);
        gap: 7px;
        padding: 1.05rem;
        border-radius: 14px;
        background: #fbfaf8;
        border: 2px solid #e6e1d8;
    }}
    .hm-person {{
        aspect-ratio: 1 / 1;
        border-radius: 50%;
        /* The transition is the payoff: brown drains out of the village and
           red seeps in gradually, so the eye follows WHICH people changed
           rather than just noticing the picture is different. */
        transition: background 0.3s linear;
    }}
    .hm-legend {{
        display: flex; gap: 1.3rem; justify-content: center; flex-wrap: wrap;
        padding: 0.7rem 0 0.2rem 0; font-size: 0.9rem; color: #6f6960;
        font-family: system-ui, sans-serif;
    }}
    .hm-key {{ display: flex; align-items: center; gap: 0.4rem; }}
    .hm-key b {{ color: #33302c; }}
    .hm-swatch {{
        width: 0.8rem; height: 0.8rem; border-radius: 50%;
        display: inline-block;
    }}
    </style>
    <div class="hm-yearbar">
      <div class="hm-year">{current_year}</div>
      <div class="hm-readout">carrying worms: <b>{_worms:.0%}</b>
        &nbsp;·&nbsp; allergic or autoimmune: <b>{_prev:.1%}</b></div>
    </div>
    <div class="hm-village">{"".join(_dots)}</div>
    <div class="hm-legend">
      <div class="hm-key"><span class="hm-swatch" style="background:#8a5a2b"></span>
        carrying a helminth &nbsp;<b>{_n_worm}</b></div>
      <div class="hm-key"><span class="hm-swatch" style="background:#8a8177"></span>
        neither &nbsp;<b>{N_VILLAGERS - _n_worm - _n_ill}</b></div>
      <div class="hm-key"><span class="hm-swatch" style="background:#C44E52"></span>
        allergic or autoimmune &nbsp;<b>{_n_ill}</b></div>
    </div>
    """

    mo.Html(_html)
    return


@app.cell
def _(mo, play_button, rewind_button, step_button, ticker):
    # The ticker is rendered (invisibly small) because a refresh element only
    # runs while it is on screen.
    mo.hstack(
        [play_button, step_button, rewind_button, ticker],
        justify="center",
        gap=1,
    )
    return


@app.cell
def _(current_year, idx, mean_history, mismatch, mo, opt_history, worm_all):
    _worms = float(worm_all[idx])
    _mean = float(mean_history[idx])
    _opt = float(opt_history[idx])
    _gap = float(mismatch[idx])

    # Sign matters and is spelled out in words: students consistently read a
    # bare signed number as "how wrong" rather than "in which direction".
    if abs(_gap) < 0.02:
        _verdict = "matched to this world"
        _colour = "#1f8a4c"
    elif _gap > 0:
        _verdict = "tuned for a parasite that is gone"
        _colour = "#C44E52"
    else:
        _verdict = "under-reactive for this world"
        _colour = "#C44E52"

    _cards = f"""
    <style>
    .hm-cards {{
        display: flex; gap: 0.9rem; justify-content: center;
        padding: 0.9rem 0 0.2rem 0; flex-wrap: wrap;
    }}
    .hm-card {{
        flex: 1 1 0; min-width: 150px; max-width: 235px;
        border-radius: 12px; padding: 0.85rem 0.7rem; text-align: center;
        font-family: system-ui, sans-serif; border: 2px solid; background: #fbfaf8;
    }}
    .hm-card-title {{
        font-size: 0.74rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.09em; color: #7a7382;
    }}
    .hm-card-val {{ font-size: 2.5rem; font-weight: 800; line-height: 1.15; }}
    .hm-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
    </style>
    <div class="hm-cards">
      <div class="hm-card" style="border-color:#8a5a2b">
        <div class="hm-card-title">Carrying worms</div>
        <div class="hm-card-val" style="color:#8a5a2b">{_worms:.0%}</div>
        <div class="hm-card-sub">of the village in {current_year}</div>
      </div>
      <div class="hm-card" style="border-color:#8a5a2b">
        <div class="hm-card-title">Immune set-point</div>
        <div class="hm-card-val" style="color:#8a5a2b">{_mean:.2f}</div>
        <div class="hm-card-sub">where the population actually is</div>
      </div>
      <div class="hm-card" style="border-color:#4C72B0">
        <div class="hm-card-title">Optimum now</div>
        <div class="hm-card-val" style="color:#4C72B0">{_opt:.2f}</div>
        <div class="hm-card-sub">what this world would reward</div>
      </div>
      <div class="hm-card" style="border-color:{_colour}">
        <div class="hm-card-title">Mismatch</div>
        <div class="hm-card-val" style="color:{_colour}">{abs(_gap):.2f}</div>
        <div class="hm-card-sub">{_verdict}</div>
      </div>
    </div>
    """

    mo.Html(_cards)
    return


@app.cell
def _(
    R_GRID,
    TRAIT_SD,
    YEAR_END,
    YEAR_START,
    current_year,
    fig_to_svg,
    fitness,
    idx,
    mean_history,
    mo,
    np,
    opt_history,
    plt,
    years_all,
):
    # --- Plot 1: selection toward an optimum that will not stay still ------
    _fig, (_axL, _axR) = plt.subplots(1, 2, figsize=(9.6, 4.3))

    _mean = float(mean_history[idx])
    _opt = float(opt_history[idx])

    # LEFT: the trait axis itself. The population as a density, the fitness
    # function it is being judged by, and the horizontal gap between them.
    _dens = np.exp(-0.5 * ((R_GRID - _mean) / TRAIT_SD) ** 2)
    _dens = _dens / _dens.max()
    _axL.fill_between(R_GRID, 0.0, _dens, color="#8a5a2b", alpha=0.35, linewidth=0)
    _axL.plot(R_GRID, _dens, color="#8a5a2b", linewidth=2.0,
              label="the population")

    # The fitness curve shares the y-axis rather than getting a twin. Both are
    # scaled to peak at 1.0 and neither is a quantity anyone reads off the
    # axis -- what matters is where the two peaks sit relative to each other.
    # A second axis would imply the heights were comparable data.
    _axL.plot(R_GRID, fitness(R_GRID, _opt), color="#4C72B0", linewidth=2.0,
              linestyle="--", label="fitness in this world")

    # The ancestral optimum stays put as a reference, so the student can see
    # how far the world has moved as well as how far the population has not.
    _axL.axvline(float(opt_history[0]), color="#9a938a", linewidth=1.0,
                 linestyle=":")
    _axL.text(float(opt_history[0]) + 0.012, 1.12, "1850\noptimum", fontsize=7,
              color="#9a938a", va="top", ha="left")

    # The shaded horizontal span IS the mismatch. Drawing it as an area rather
    # than two lines is what makes it read as a quantity.
    _lo, _hi = sorted((_mean, _opt))
    _axL.axvspan(_lo, _hi, color="#C44E52", alpha=0.20, linewidth=0)
    _axL.annotate(
        "", xy=(_mean, 0.52), xytext=(_opt, 0.52),
        arrowprops=dict(arrowstyle="<->", color="#C44E52", linewidth=1.2),
    )
    if abs(_mean - _opt) > 0.05:
        _axL.text((_mean + _opt) / 2.0, 0.57, "mismatch", fontsize=8,
                  color="#C44E52", ha="center", fontweight="bold")

    _axL.set_xlim(0.0, 1.0)
    _axL.set_ylim(0.0, 1.2)
    _axL.set_xlabel("immune reactivity set-point")
    _axL.set_ylabel("relative frequency / fitness")
    _axL.set_title("Selection pulls left; the population barely moves",
                   fontsize=10)
    _axL.legend(loc="upper left", fontsize=8)
    _axL.spines["top"].set_visible(False)
    _axL.spines["right"].set_visible(False)

    # RIGHT: the same two numbers over time.
    _sl = slice(0, idx + 1)
    _axR.plot(years_all[_sl], opt_history[_sl], color="#4C72B0", linewidth=2.0,
              linestyle="--", label="optimum set-point")
    _axR.plot(years_all[_sl], mean_history[_sl], color="#8a5a2b", linewidth=2.4,
              label="population mean")
    _axR.fill_between(years_all[_sl], mean_history[_sl], opt_history[_sl],
                      color="#C44E52", alpha=0.20, linewidth=0)
    _axR.axvline(current_year, color="#33302c", linewidth=1.0, alpha=0.5)
    _axR.plot([current_year], [mean_history[idx]], "o", color="#8a5a2b",
              markersize=8, zorder=5)
    _axR.plot([current_year], [opt_history[idx]], "o", color="#4C72B0",
              markersize=8, zorder=5)

    # Axis limits are FIXED to the full timeline rather than left to
    # autoscale. Autoscaled axes would rescale on every frame as the curve
    # grows, so the drawn line would crawl and stretch instead of advancing,
    # and the playhead would never move steadily left to right.
    _axR.set_xlim(YEAR_START, YEAR_END)
    _axR.set_ylim(0.0, 1.0)
    _axR.set_xlabel("year")
    _axR.set_ylabel("immune reactivity set-point")
    _axR.set_title("The gap opens and never closes", fontsize=10)
    _axR.legend(loc="lower left", fontsize=8)
    _axR.spines["top"].set_visible(False)
    _axR.spines["right"].set_visible(False)

    # Historical anchors, so the curve is tied to real events rather than
    # floating in abstract time.
    for _yr, _txt in (
        (1854, "Snow,\nBroad St"),
        (1948, "mass\ndeworming"),
        (1989, "hygiene\nhypothesis"),
    ):
        _axR.axvline(_yr, color="#9a938a", linewidth=0.9, linestyle=":")
        _axR.text(_yr + 2, 0.98, _txt, fontsize=6.5, color="#6f6960",
                  va="top", ha="left")

    _fig.tight_layout()
    mo.output.replace(mo.Html(fig_to_svg(_fig)))
    return


@app.cell
def _(fig_to_svg, fitness, idx, mo, np, plt, r_opt_at, worm_all):
    # --- Plot 2: reaction norms -------------------------------------------
    #
    # Environment on the x-axis, one line per genotype -- the classic reaction
    # norm, drawn this way round (unlike the CCR5 notebook's fitness plot)
    # because here the shape that matters is what happens to EACH genotype as
    # the world changes, and whether their rank order survives it.
    #
    # It does not. These three lines cross, which is the strong form of G x E:
    # not merely that the genotypes respond by different amounts, but that the
    # BEST genotype in one world is the worst in the other.
    _fig, _ax = plt.subplots(figsize=(7.6, 4.4))

    # x runs wormy -> wormless, left to right, matching the direction of
    # history so the plot reads the same way as the timeline above it.
    _w = np.linspace(0.95, 0.02, 200)
    _x = np.linspace(0.0, 1.0, 200)
    _opt = r_opt_at(_w)

    for _r, _lab, _col in (
        (0.28, "low reactivity", "#4C72B0"),
        (0.50, "middling", "#8a8177"),
        (0.76, "high reactivity", "#C44E52"),
    ):
        _ax.plot(_x, fitness(_r, _opt), color=_col, linewidth=2.4, label=_lab)

    # A marker riding the current year along the environment axis, so the
    # animation moves through this plot too rather than sitting inert beside
    # it. Mapped from worm prevalence, not from the year, so it stays correct
    # if the environment curve is ever reshaped.
    _here = float(np.clip((0.95 - worm_all[idx]) / (0.95 - 0.02), 0.0, 1.0))
    _ax.axvline(_here, color="#33302c", linewidth=1.0, alpha=0.5)
    _ax.plot([_here], [1.05], "v", color="#33302c", markersize=8, zorder=6)

    # Placing these two labels is fiddly and the positions below are not
    # arbitrary. Three things are already occupying the axes -- the legend
    # (bottom-left), the playhead triangle (top, and it MOVES during
    # playback), and three curves that between them cross most of the middle
    # of the plot. matplotlib will not reflow a label to dodge any of them,
    # so the two genuinely empty regions have to be found and used:
    #
    #   - a band above y = 1.02, which no curve reaches, for the "wormy" label
    #   - a band below y = 0.16 on the right, which no curve dips into, for
    #     the "clean" label
    #
    # Earlier attempts put the first label at centre-left (straight through
    # the legend box) and then at y = 0.70 (straight through the grey
    # "middling" curve). Both were unreadable. The x-offsets also keep each
    # label clear of the playhead's travel.
    _ax.annotate(
        "in a wormy world the\nhot immune system wins",
        xy=(0.10, fitness(0.76, r_opt_at(0.85))), xytext=(0.17, 1.17),
        fontsize=7.5, color="#6f6960", va="top",
        arrowprops=dict(arrowstyle="->", color="#9a938a", linewidth=0.8),
    )
    _ax.annotate(
        "in a clean world the\nsame genotype is worst",
        xy=(0.97, fitness(0.76, r_opt_at(0.05))), xytext=(0.60, 0.13),
        fontsize=7.5, color="#6f6960", va="top",
        arrowprops=dict(arrowstyle="->", color="#9a938a", linewidth=0.8),
    )

    # Starts at exactly 0.0 rather than -0.02. With a small negative margin
    # the left spine and the 1850 playhead (which sits at x = 0.045) render as
    # two near-parallel vertical lines a few pixels apart, which reads as a
    # drawing error rather than as a marker.
    _ax.set_xlim(0.0, 1.0)
    # Headroom to 1.30: the curves peak at 1.0, the playhead triangle rides at
    # 1.05, and the "wormy" label sits above both.
    _ax.set_ylim(0.0, 1.30)
    _ax.set_xticks([0.0, 1.0])
    _ax.set_xticklabels(["wormy\n(1850)", "wormless\n(2020)"])
    _ax.set_xlabel("environment")
    _ax.set_ylabel("relative fitness")
    _ax.set_title("The best immune system depends on which century you are in")
    _ax.legend(loc="lower left", fontsize=9, title="genotype", title_fontsize=8,
               framealpha=0.95)
    _ax.spines["top"].set_visible(False)
    _ax.spines["right"].set_visible(False)

    _fig.tight_layout()
    mo.output.replace(mo.Html(fig_to_svg(_fig)))
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What am I looking at?** (play it through first!)": mo.md(
                r"""
                ### The optimum moved and nobody followed

                **Evolutionary mismatch** is what happens when a trait that was
                a good answer to the environment that built it is left sitting
                in an environment that has since changed. Not a defect, not a
                disease of civilisation, not something going wrong — a correct
                answer to a question nobody is asking any more.

                The right-hand panel above is the whole idea in one picture.
                The blue line is the immune set-point this world would reward.
                The brown line is where the population actually sits. In 1850
                they are the same line: the population is *well adapted*, and
                that is the point — it is well adapted **to 1850**.

                Selection does move the population. Each generation, the
                breeder's equation says how far:

                $$R = h^{2} S$$

                where $S$ is the selection differential (how far selection
                shifts the trait *within* a generation) and $h^{2}$ is the
                heritability (how much of that shift is actually inherited).
                With $h^{2} = 0.5$, the population keeps half of each
                generation's progress.

                Half of something is a lot. So why does the gap never close?

                ### Six generations

                Because $R$ is a response **per generation**, and this
                population only gets six of them.

                A human generation is about 25 years. The whole helminth
                collapse — sanitation, plumbing, shoes, mass deworming — fits
                into roughly 170 years. That is six chances to respond, and the
                environment did most of its moving inside two of them.

                Compare the peppered moth next door:

                | | environment moved for | generation time | generations to respond |
                |---|---|---|---|
                | *Biston betularia* | ~150 years | 1 year | **~150** |
                | *Homo sapiens* | ~170 years | ~25 years | **~6** |

                The moth substantially caught up. We get about **a fifth** of
                the way. Play the timeline to the end and read the two middle
                cards: the optimum has fallen most of the way down its range,
                and the population mean has barely left where it started.

                This is the most important idea in the lab, and it has nothing
                to do with worms. **Adaptation is measured in generations, not
                years.** Any species that changes its own environment faster
                than it can breed will be mismatched to it, by construction.
                Bacteria evolve resistance to a new antibiotic in months
                because months *are* thousands of generations to them. We
                changed our entire ecology in six.

                ### Why worms tuned the thermostat up

                A helminth is not a bacterium. It is large, long-lived, and it
                cannot be killed quickly — and it fights back, secreting
                molecules that push the host's immune system toward tolerance:
                regulatory T cells, IL-10, TGF-β. A worm's best strategy is to
                turn its host's immune response **down**.

                An immune system evolving against that is being pushed on from
                one side, continuously, for its entire evolutionary history.
                The set-point that comes out the other end is calibrated
                against that push — high enough to hold a worm in check
                *given* that something is damping it.

                Take the worm away and the damping goes with it. Nothing about
                the immune system changed; the thing it was braced against
                simply stopped existing. The surplus push has to land
                somewhere, and it lands on pollen, food proteins, gut lining,
                pancreatic β-cells, myelin.

                This is the **"old friends"** framing, and it is a better name
                than "hygiene hypothesis": the claim is not that dirt is good
                for you, but that we co-evolved with a particular set of
                organisms whose presence our immune development came to expect.

                ### Fitness is not a property of a genotype

                Look at the reaction-norm plot. Three immune genotypes, two
                worlds, and the lines are **not parallel** — that
                non-parallelism is genotype-by-environment interaction
                (**G×E**) in its strict sense. The map from genotype to
                fitness is not a property of the genotype. It is a property of
                the genotype *and* the environment together, and neither alone
                predicts anything.

                This example clears a higher bar than non-parallelism, though.
                The lines actually **cross**: the hot, inflammatory genotype is
                the *best* one to have in 1850 and the *worst* one to have in
                2020. The rank order reverses. That is the strong form of G×E,
                and it means the question "is a reactive immune system good?"
                has no answer at all until you say which century you mean.

                Compare the *CCR5* notebook: there the two susceptible
                genotypes sit at the same height and the lines fan apart
                without crossing. Still G×E — still no context-free answer to
                "what is the fitness of Δ32?" — but the weaker form. Both
                shapes are G×E; only one reverses the ranking.

                ### The evidence

                **Strachan, 1989.** Hay fever in British children fell with the
                number of older siblings they had. The proposed explanation —
                more siblings, more childhood infections, less allergy — is the
                paper that started the field.

                **The Karelia natural experiment.** Finnish and Russian Karelia
                sit either side of one border, sharing a population and a
                genetic background, separated by a large gap in living
                standards. Type 1 diabetes incidence is roughly **six times
                higher** on the affluent Finnish side. Allergy and
                autoimmunity track the same way.

                **Gradients.** Allergic and autoimmune disease rises with
                latitude, with urbanisation, with GDP, and with sanitation
                coverage — and helminth prevalence falls along every one of
                those same axes.

                **Migrant studies — and read this one carefully, because it is
                doing different work from the other three.** Karelia and the
                gradients are *consistent with* mismatch, but they are equally
                consistent with a dozen other things that change when a country
                industrialises: diet, antibiotics, air quality, vitamin D,
                indoor living, the microbiome generally. Correlation with
                industrialisation is cheap.

                Migrant studies are the ones that actually constrain the
                explanation. When families move from a low-prevalence country
                to a high-prevalence one, their allergy and autoimmunity risk
                converges on the **destination** country's — often within a
                single generation, sometimes within childhood. One generation
                is far too fast for allele frequencies to have shifted. The
                genes went with them; the risk did not. Whatever drives the
                difference is **environmental**, and it acts within a lifetime.

                That does not prove it is the worms. It does rule out the
                explanation that would otherwise be most tempting.

                ### One honest caveat

                **The most important sentence in this notebook:** the disease
                line is *defined* as a monotone function of the mismatch. The
                model cannot fail to show allergy and autoimmunity rising as
                worms vanish, because that relationship was written into it.
                The figure **illustrates a proposed mechanism; it does not test
                or demonstrate one.** Anyone reading those curves as evidence
                is reading in something that is not there.

                The peppered moth notebook has the same structure — its target
                is *defined* as the soot level — but there the assumption is
                close to a tautology, since crypsis really is just matching the
                background. Here the assumed link is precisely the contested
                claim. That difference matters.

                And it is genuinely contested. **Helminth therapy has largely
                disappointed.** Early open-label work with *Trichuris suis* ova
                in Crohn's disease and ulcerative colitis looked promising, but
                the randomised controlled trials that followed — in Crohn's, in
                multiple sclerosis, in allergic rhinitis — have mostly failed
                to show benefit, and several were stopped early. If the
                mechanism were as clean as the plots above, giving the worms
                back ought to work better than it does.

                "Hygiene hypothesis" is also a badly chosen and widely misused
                name. It gets quoted as an argument against handwashing, clean
                water and vaccination, which it is not and never was.
                Sanitation is among the largest public-health victories in
                human history, it saved a staggering number of lives, and
                nothing here argues for reversing any of it. The interesting
                question is not whether the trade was worth making — it
                obviously was — but what the bill looks like.

                Finally, the model: one quantitative trait standing in for an
                enormously polygenic, multi-pathway immune system; fixed trait
                variance where real stabilising selection would erode it;
                random mating; no drift, no migration, no population structure;
                and $h^{2}$, $\omega$, the generation time and the disease
                mapping all chosen to be legible rather than measured. Treat
                every number here as illustration, not measurement.
                """
            )
        }
    )
    return


@app.cell
def _():
    import io as _io
    import re as _re

    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt

    plt.rcParams["figure.dpi"] = 120
    plt.rcParams["svg.fonttype"] = "none"  # keep text as text, not outlines

    def fig_to_svg(fig):
        # Rendering the figure as INLINE SVG rather than handing marimo the
        # figure object is what stops the plot pulsing during playback.
        # marimo renders a matplotlib figure as a base64 PNG inside a
        # <marimo-mime-renderer>, so every animation frame mounts a brand-new
        # <img> element -- and each new image fades in as it decodes, which
        # at 8 frames a second reads as a constant distracting flicker.
        # Inline SVG markup goes straight into the DOM with no image decode
        # and no renderer remount, so the browser diffs the drawing in place
        # and the curve simply advances.
        _buf = _io.StringIO()
        fig.savefig(_buf, format="svg", bbox_inches="tight")
        plt.close(fig)  # figures accumulate and leak memory across frames
        _svg = _buf.getvalue()
        _svg = _svg[_svg.index("<svg"):]

        # The <metadata> block carries a render timestamp, so it differs on
        # every single frame and would defeat the id stabilisation below.
        _svg = _re.sub(r"<metadata>.*?</metadata>", "", _svg, flags=_re.S)

        # matplotlib mints fresh clip-path/glyph ids on every render
        # (id="p3f2a1c..."), so consecutive frames share no element ids and
        # the browser tears down and rebuilds the whole subtree instead of
        # updating it. Rewriting them to a stable prefix keeps the ids
        # identical frame to frame, so the DOM diff stays minimal.
        #
        # The ids must be numbered in ORDER OF FIRST APPEARANCE, not sorted:
        # matplotlib's raw ids vary run to run, so sorting them alphabetically
        # would map the same element to a different stable name on each frame
        # and reintroduce exactly the churn this is meant to remove.
        _ids = list(dict.fromkeys(_re.findall(r'id="([^"]+)"', _svg)))
        for _i, _old in enumerate(_ids):
            _svg = _svg.replace(_old, f"hmfig{_i}")

        # The SVG carries absolute pt dimensions; swap them for a responsive
        # width so the plot fits the notebook column at any window size.
        _svg = _re.sub(
            r'(<svg[^>]*?)width="[\d.]+pt" height="[\d.]+pt"',
            r'\1width="100%" style="height:auto;display:block"',
            _svg,
            count=1,
        )
        return _svg
    return fig_to_svg, mo, np, plt


if __name__ == "__main__":
    app.run()
