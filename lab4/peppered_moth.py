import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🦋 The Peppered Moth, and the Cost of Being Late

    Britain, 1800. Tree trunks are pale, crusted with lichen, and almost
    every *Biston betularia* is pale and speckled — beautifully invisible
    against them. A rare dark ("melanic") form exists, and it is eaten.

    Then the factories arrive. Soot kills the lichen and blackens the
    bark. Now it is the *pale* moths that stand out, and the dark form
    that disappears against the trunk. Birds keep doing exactly what they
    always did: eating whichever moth they can see.

    The population follows — but **it does not follow instantly.** That
    delay is the whole point of this notebook.

    **Press play.** Watch the moths, and watch the red band on the graph:
    the gap between where the population *is* and where it *should be*.
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
    # deliberate: the cards and the bark scene pulse for exactly the same
    # reason as the plot does.
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
    # --- The environment: soot on bark, 1800-2000 --------------------------
    #
    # `soot` runs 0 (pale, lichen-covered bark) to 1 (black, soot-caked
    # bark). The shape is historical rather than fitted: industrial soot
    # climbs through the 1800s, peaks around 1900-1950, then falls sharply
    # after the 1956 Clean Air Act. We model each arm as a logistic so the
    # environment has a smooth but genuinely fast-moving edge -- a slow ramp
    # would let even weak selection keep up, and hide the very lag we are
    # trying to show.
    YEAR_START = 1800
    YEAR_END = 2000

    def soot_at(year):
        rise = 1.0 / (1.0 + np.exp(-(year - 1865.0) / 14.0))
        fall = 1.0 / (1.0 + np.exp((year - 1965.0) / 8.0))
        return rise * fall

    years_all = np.arange(YEAR_START, YEAR_END + 1)
    soot_all = soot_at(years_all)
    return YEAR_END, YEAR_START, soot_all, soot_at, years_all


@app.cell
def _(np, soot_at):
    # --- Survival, genotypes, and one generation of selection --------------
    #
    # Melanism in Biston betularia is a single locus where the melanic allele
    # (carbonaria, here `M`) is DOMINANT over the pale allele (typica, `m`).
    # MM and Mm are both dark and are selected identically; only mm is pale.
    # That dominance matters enormously here: a pale allele can hide inside a
    # dark heterozygote where birds cannot see it, so selection can never
    # fully purge it -- which is exactly why the pale form survived a century
    # of soot and could rebound quickly once the air cleaned up.

    # Recurrent mutation, both directions. Without it a form driven to near
    # zero would have to wait for a brand-new mutation to come back, and the
    # post-1956 recovery would be an artefact of floating-point underflow
    # rather than biology.
    MUTATION = 5e-4

    def survival(soot, strength):
        # Crypsis is contrast against the bark, so each form's survival falls
        # with how badly it MISmatches the background. `strength` is bird
        # predation pressure -- how costly it is to be seen -- and it sets how
        # fast the population can possibly track the bark.
        w_dark = 1.0 - strength * (1.0 - soot)  # dark moth exposed on PALE bark
        w_pale = 1.0 - strength * soot          # pale moth exposed on SOOTY bark
        # Floor above zero: exact zero makes mean fitness collapse to 0/0 when
        # one form is fixed, and no real moth is eaten with certainty.
        return max(w_dark, 1e-6), max(w_pale, 1e-6)

    def dark_fraction(p):
        # What a bird actually sees is the PHENOTYPE. Dominance means every
        # moth carrying at least one melanic allele is dark: MM + Mm.
        return p * p + 2.0 * p * (1.0 - p)

    def step_generation(p, soot, strength):
        # p = frequency of the melanic allele M. Random mating gives
        # Hardy-Weinberg genotype frequencies, then selection, then mutation.
        w_dark, w_pale = survival(soot, strength)
        q = 1.0 - p
        w_bar = dark_fraction(p) * w_dark + q * q * w_pale

        # M is carried by every MM (two copies) and every Mm (one), each
        # weighted by dark survival.
        p = (p * p * w_dark + p * q * w_dark) / w_bar
        p = p * (1.0 - MUTATION) + (1.0 - p) * MUTATION
        return float(np.clip(p, 0.0, 1.0))

    def run_history(years, strength, gens_per_year):
        # Each year the bark has already moved; the moths get
        # `gens_per_year` generations to respond before it moves again.
        # Peppered moths are univoltine (one generation a year), but exposing
        # this lets students watch lag shrink as reproduction speeds up
        # relative to environmental change.
        p = MUTATION
        out = np.empty(len(years))
        for i, year in enumerate(years):
            soot = soot_at(year)
            for _ in range(gens_per_year):
                p = step_generation(p, soot, strength)
            out[i] = dark_fraction(p)
        return out

    return (run_history,)


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
        label="⏮  Back to 1800",
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
def _(run_history, soot_all, years_all):
    # The whole 200-year history is computed ONCE, not per animation frame --
    # the playhead just indexes into it. Recomputing inside the render cell
    # would re-run two centuries of selection on every tick and the animation
    # would crawl.
    #
    # Predation pressure: how costly it is to be seen. 0.35 is chosen so the
    # population visibly trails the bark without ever quite catching it --
    # weaker and it barely responds at all, stronger and the lag closes so
    # fast there is nothing to see.
    STRENGTH = 0.35
    # Peppered moths are univoltine: one generation per year.
    GENS_PER_YEAR = 1

    # Actual dark-phenotype frequency, year by year.
    dark_history = run_history(years_all, STRENGTH, GENS_PER_YEAR)

    # The moving target. A moth is safe when it matches its background, so the
    # best mix for today's bark is simply "as dark as the bark is": on 80%
    # sooty bark, 80% dark moths. This is the target the population chases and
    # never quite reaches.
    dark_target = soot_all

    # Adaptive lag: the signed gap between where the population should be and
    # where it actually is.
    lag = dark_target - dark_history
    return dark_history, dark_target, lag


@app.cell
def _(YEAR_START, get_clock, np, years_all):
    # Index of the playhead into the precomputed arrays.
    _year = get_clock()["year"]
    idx = int(np.clip(_year - YEAR_START, 0, len(years_all) - 1))
    current_year = int(years_all[idx])
    return current_year, idx


@app.cell
def _(np):
    # Moth positions are fixed once, at import, rather than redrawn each
    # frame. If they were re-randomised on every tick the whole population
    # would visibly shuffle 8 times a second and the colour change -- the
    # thing we actually want watched -- would be lost in the noise. Only
    # each moth's COLOUR changes as the generations turn over.
    N_MOTHS = 40
    _pos_rng = np.random.default_rng(4)
    moth_x = _pos_rng.uniform(4.0, 92.0, N_MOTHS)
    moth_y = _pos_rng.uniform(5.0, 88.0, N_MOTHS)
    moth_rot = _pos_rng.uniform(-28.0, 28.0, N_MOTHS)
    moth_scale = _pos_rng.uniform(0.82, 1.18, N_MOTHS)
    # A fixed "rank" per moth turns a frequency into a deterministic picture:
    # moth i is dark when its rank falls below the melanic phenotype
    # frequency. Consecutive frames then differ by a few individuals flipping
    # rather than a whole new random sample, which reads as a population
    # changing instead of a slideshow of unrelated populations.
    moth_rank = _pos_rng.permutation(N_MOTHS) / float(N_MOTHS)
    return moth_rank, moth_rot, moth_scale, moth_x, moth_y


@app.cell
def _(
    current_year,
    dark_history,
    idx,
    mo,
    moth_rank,
    moth_rot,
    moth_scale,
    moth_x,
    moth_y,
    soot_all,
):
    _soot = float(soot_all[idx])
    # Already a phenotype frequency: dominance was applied in the model, so
    # this is the fraction of moths a bird would see as dark.
    _freq_dark = float(dark_history[idx])

    def _mix(pale, dark, t):
        return tuple(int(round(a + (b - a) * t)) for a, b in zip(pale, dark))

    # Bark darkens from lichen-green-grey to soot black as the century turns.
    _bark = _mix((176, 172, 150), (38, 35, 33), _soot)
    _bark_dk = _mix((138, 134, 112), (20, 19, 18), _soot)
    _lichen = max(0.0, 1.0 - _soot * 1.35)

    _moths = []
    for _i in range(len(moth_x)):
        _is_dark = moth_rank[_i] < _freq_dark
        _fill = "#2a2724" if _is_dark else "#ddd8c4"
        _speck = "#6d6659" if _is_dark else "#8d8672"
        _w = 26.0 * moth_scale[_i]
        _moths.append(
            f'<div class="pm-moth" style="left:{moth_x[_i]:.1f}%;'
            f"top:{moth_y[_i]:.1f}%;width:{_w:.1f}px;"
            f'transform:rotate({moth_rot[_i]:.1f}deg);">'
            f'<div class="pm-wing" style="background:{_fill};'
            f'box-shadow:inset 0 0 0 1px {_speck};"></div>'
            f"</div>"
        )

    _style = """
    <style>
    .pm-bark {
        position: relative;
        height: 330px;
        border-radius: 14px;
        overflow: hidden;
        border: 3px solid #2f2a24;
        transition: background 0.35s linear;
    }
    .pm-bark::after {
        content: "";
        position: absolute;
        inset: 0;
        background: repeating-linear-gradient(
            96deg,
            rgba(0, 0, 0, 0.00) 0px,
            rgba(0, 0, 0, 0.13) 7px,
            rgba(255, 255, 255, 0.05) 15px,
            rgba(0, 0, 0, 0.00) 24px
        );
        pointer-events: none;
    }
    .pm-lichen {
        position: absolute;
        inset: 0;
        pointer-events: none;
        background:
            radial-gradient(ellipse 70px 40px at 18% 26%, rgba(186,198,150,0.85) 0%, transparent 70%),
            radial-gradient(ellipse 54px 34px at 74% 15%, rgba(196,206,164,0.75) 0%, transparent 70%),
            radial-gradient(ellipse 80px 44px at 58% 72%, rgba(178,192,146,0.8) 0%, transparent 70%),
            radial-gradient(ellipse 46px 30px at 30% 88%, rgba(200,208,170,0.7) 0%, transparent 70%),
            radial-gradient(ellipse 60px 36px at 88% 58%, rgba(184,196,152,0.75) 0%, transparent 70%);
        transition: opacity 0.35s linear;
    }
    .pm-moth { position: absolute; transition: none; }
    .pm-wing {
        width: 100%;
        aspect-ratio: 1.55 / 1;
        border-radius: 46% 46% 40% 40% / 62% 62% 38% 38%;
        transition: background 0.3s linear;
    }
    .pm-wing::before {
        content: "";
        display: block;
        margin: 0 auto;
        width: 8%;
        height: 100%;
        background: rgba(0, 0, 0, 0.32);
        border-radius: 40%;
    }
    .pm-yearbar {
        display: flex;
        align-items: baseline;
        justify-content: center;
        gap: 1.4rem;
        font-family: system-ui, sans-serif;
        padding: 0.55rem 0 0.15rem 0;
    }
    .pm-year {
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: 0.01em;
        color: #33302c;
    }
    .pm-readout { font-size: 0.95rem; color: #6f6960; font-weight: 600; }
    .pm-readout b { color: #33302c; }
    </style>
    """

    _html = (
        _style
        + f'<div class="pm-yearbar"><div class="pm-year">{current_year}</div>'
        + f'<div class="pm-readout">dark moths: <b>{_freq_dark:.0%}</b>'
        + f" &nbsp;·&nbsp; soot on bark: <b>{_soot:.0%}</b></div></div>"
        + f'<div class="pm-bark" style="background:linear-gradient(100deg,'
        + f"rgb{_bark} 0%, rgb{_bark_dk} 48%, rgb{_bark} 100%);\">"
        + f'<div class="pm-lichen" style="opacity:{_lichen:.2f}"></div>'
        + "".join(_moths)
        + "</div>"
    )

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
def _(current_year, dark_history, dark_target, idx, lag, mo):
    _gap = float(lag[idx])
    _actual = float(dark_history[idx])
    _target = float(dark_target[idx])

    # The lag number is the lesson, so it gets the biggest type on the page.
    # Sign matters and is spelled out in words: students consistently read a
    # bare signed number as "how wrong" rather than "in which direction".
    if abs(_gap) < 0.02:
        _verdict = "caught up"
        _colour = "#1f8a4c"
    elif _gap > 0:
        _verdict = "too pale for this bark"
        _colour = "#C44E52"
    else:
        _verdict = "too dark for this bark"
        _colour = "#C44E52"

    _cards = f"""
    <style>
    .pm-cards {{
        display: flex; gap: 0.9rem; justify-content: center;
        padding: 0.7rem 0 0.2rem 0; flex-wrap: wrap;
    }}
    .pm-card {{
        flex: 1 1 0; min-width: 150px; max-width: 235px;
        border-radius: 12px; padding: 0.85rem 0.7rem; text-align: center;
        font-family: system-ui, sans-serif; border: 2px solid; background: #fbfaf8;
    }}
    .pm-card-title {{
        font-size: 0.74rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.09em; color: #7a7382;
    }}
    .pm-card-val {{ font-size: 2.5rem; font-weight: 800; line-height: 1.15; }}
    .pm-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
    </style>
    <div class="pm-cards">
      <div class="pm-card" style="border-color:#8a8177">
        <div class="pm-card-title">Population is</div>
        <div class="pm-card-val" style="color:#8a8177">{_actual:.0%}</div>
        <div class="pm-card-sub">dark moths in {current_year}</div>
      </div>
      <div class="pm-card" style="border-color:#4C72B0">
        <div class="pm-card-title">Should be</div>
        <div class="pm-card-val" style="color:#4C72B0">{_target:.0%}</div>
        <div class="pm-card-sub">to match today's bark</div>
      </div>
      <div class="pm-card" style="border-color:{_colour}">
        <div class="pm-card-title">Adaptive lag</div>
        <div class="pm-card-val" style="color:{_colour}">{abs(_gap):.0%}</div>
        <div class="pm-card-sub">{_verdict}</div>
      </div>
    </div>
    """

    mo.Html(_cards)
    return


@app.cell
def _(
    YEAR_END,
    YEAR_START,
    current_year,
    dark_history,
    dark_target,
    fig_to_svg,
    idx,
    mo,
    plt,
    years_all,
):
    _fig, _ax = plt.subplots(figsize=(9.2, 4.6))

    # Only history up to the playhead is drawn, so the curves are revealed as
    # the animation runs; the future is not spoiled before it happens.
    _sl = slice(0, idx + 1)

    _ax.plot(
        years_all[_sl], dark_target[_sl],
        color="#4C72B0", linewidth=2.0, linestyle="--",
        label="dark fraction that matches the bark",
    )
    _ax.plot(
        years_all[_sl], dark_history[_sl],
        color="#8a5a2b", linewidth=2.4,
        label="actual dark fraction",
    )
    # The shaded gap between the two curves IS the adaptive lag, and showing
    # it as an area rather than two lines is what makes "lag" read as a
    # quantity rather than a vibe.
    _ax.fill_between(
        years_all[_sl], dark_history[_sl], dark_target[_sl],
        color="#C44E52", alpha=0.20, linewidth=0,
    )
    _ax.axvline(current_year, color="#33302c", linewidth=1.0, alpha=0.5)
    _ax.plot([current_year], [dark_history[idx]], "o",
             color="#8a5a2b", markersize=8, zorder=5)
    _ax.plot([current_year], [dark_target[idx]], "o",
             color="#4C72B0", markersize=8, zorder=5)

    # Axis limits are FIXED to the full timeline rather than left to
    # autoscale. Autoscaled axes would rescale on every frame as the curve
    # grows, so the drawn line would crawl and stretch instead of advancing,
    # and the playhead would never move steadily left to right.
    _ax.set_xlim(YEAR_START, YEAR_END)
    _ax.set_ylim(-0.03, 1.03)
    _ax.set_xlabel("year")
    _ax.set_ylabel("fraction of dark moths")
    _ax.set_title("The population chases a moving target")
    _ax.legend(loc="center left", fontsize=9)
    _ax.spines["top"].set_visible(False)
    _ax.spines["right"].set_visible(False)

    # Historical anchors, so the curve is tied to real events rather than
    # floating in abstract time.
    for _yr, _txt in ((1848, "first melanic\nrecorded"), (1956, "Clean Air Act")):
        _ax.axvline(_yr, color="#9a938a", linewidth=0.9, linestyle=":")
        _ax.text(_yr + 2, 1.0, _txt, fontsize=7.5, color="#6f6960",
                 va="top", ha="left")

    _fig.tight_layout()
    mo.output.replace(mo.Html(fig_to_svg(_fig)))
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What am I looking at?** (play it through first!)": mo.md(
                r"""
                ### The population is always answering an old question

                Natural selection has no foresight. Each generation, birds eat
                the moths they can see *on the bark that exists right now*,
                and the survivors' alleles make the next generation. That is
                the entire mechanism — and it can only ever respond to
                conditions that have **already** happened.

                So when the environment moves, the population does not jump to
                the new optimum. It starts walking toward where the optimum
                *was*, and by the time it arrives the target has moved again.
                The red shaded band in the top panel is that shortfall:

                $$\text{adaptive lag}
                = \underbrace{\text{soot}}_{\text{what would match}}
                - \underbrace{\text{dark fraction}}_{\text{what there is}}$$

                A moth is safe when it matches its background, so the best mix
                for today's bark is simply *as dark as the bark is*: on 80%
                sooty bark, 80% dark moths. That is the dashed blue line.

                Notice the lag is **largest when the environment is changing
                fastest** — around 1860–1900 as the soot rises, and again
                after the 1956 Clean Air Act as it falls. When soot plateaus,
                the population quietly catches up and the band closes.

                ### Why it can't just go faster

                Three things set how far behind the population runs:

                - **Predation pressure.** Selection is the engine. When being
                  conspicuous is only mildly costly, the population barely
                  moves in a generation and the lag is enormous; when it is
                  lethal, the two curves nearly touch.
                - **Generation time.** Adaptation is measured in
                  *generations*, not years. A peppered moth gets one per year,
                  so a century of soot is only about a hundred chances to
                  respond. This is precisely why bacteria evolve resistance to
                  a new drug in months while we do not.
                - **Dominance.** The melanic allele is dominant, so a pale
                  allele can ride along invisibly inside a dark heterozygote.
                  Selection cannot remove what it cannot see, so the pale
                  allele is never fully purged. That hidden reservoir is why
                  the pale form could come back after 1956 rather than
                  waiting for new mutations — but it cuts both ways, and it
                  is why the **recovery lags even harder than the rise did.**
                  Watch the red band after 1956: once dark moths are common,
                  nearly every pale allele is hidden in a heterozygote, and
                  purging the last dark moths is slow going. Selection
                  removing a *dominant* allele has to work through carriers
                  one at a time.

                ### From lag to mismatch

                Adaptive lag is the general principle. **Evolutionary
                mismatch** is what it feels like from the inside: a trait that
                was well-matched to the environment that built it, sitting in
                an environment that has since changed.

                The moths got lucky — soot changed over roughly 150
                generations, slow enough for them to substantially track it.
                Now consider a species whose environment was transformed in a
                handful of generations, or less than one:

                | | Environment that shaped the trait | Environment now |
                |---|---|---|
                | Sweet/fat cravings | calories scarce and unreliable | calories abundant |
                | Fear responses | predators, unfamiliar groups | traffic, public speaking |
                | Sitting still | rest is a scarce, valuable recovery | desks, all day |
                | Sea turtle hatchlings | moonlight on water = the sea | streetlights inland |

                None of these are *defects*. Every one is a trait that was a
                good answer — to a question nobody is asking any more. Humans
                changed our own environment on a timescale of decades while
                our genome still updates on a timescale of millennia, so our
                lag band never gets a chance to close.

                ### One honest caveat about the moths

                This is a deliberately clean model: one locus, two alleles,
                random mating, no migration, no mutation, and crypsis as the
                only thing that matters. Real *Biston betularia* studies also
                involve moth movement between woodlands, bark microhabitat,
                and decades of argument over Kettlewell's original predation
                experiments. The direction of the story has held up — and the
                melanic allele was finally pinned to a transposable element
                insertion in the *cortex* gene in 2016 — but treat the exact
                numbers here as illustration, not measurement.
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
            _svg = _svg.replace(_old, f"pmfig{_i}")

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
