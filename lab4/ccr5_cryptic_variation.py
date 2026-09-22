import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # 🧬 The Variation You Cannot See

    Below are a thousand people from a Northern European population. Nobody
    here is ill. Nobody has an unusual phenotype. By every measure their
    environment has ever applied to them, they are the same.

    They are not. About one in ten copies of their *CCR5* gene carries a
    32-base-pair deletion — **Δ32** — that breaks the receptor the gene codes
    for. Carrying it costs nothing. Carrying it gains nothing. For their
    entire lives it has been, as far as anything could tell, not there.

    Then HIV arrives: a virus this population has never met, that not one of
    their ancestors was ever selected against.

    **Flip the switch below.** Look at the same thousand people three times —
    as their world sees them, as their genomes actually are, and as the virus
    sorts them.

    Nothing in this notebook evolves. No generations pass. The population
    does not have time to adapt — and it does not need to.
    """)
    return


@app.cell
def _():
    # --- One population, one instant, no time axis -------------------------
    #
    # This notebook is a photograph, not a film. There are no generations
    # anywhere in it, nothing is iterated, and the allele frequency never
    # moves. That is the whole design: cryptic variation is a fact about a
    # population as it stands right now, and putting a time axis on it would
    # quietly turn it into a story about adaptation instead.
    #
    # Hardy-Weinberg is the right lens precisely because it needs no history.
    # Given random mating and an allele frequency, the genotype proportions
    # follow -- we do not have to know, or claim, anything about how the
    # allele got to that frequency.
    #
    # Throughout, Delta32 is treated as STRICTLY NEUTRAL: it does nothing, for
    # or against, in a world without HIV. Whether something once acted on it
    # is a live argument in the literature and is deliberately not this
    # notebook's business.
    N_PEOPLE = 1000
    # Columns only: CSS grid takes the row count from how many items it is
    # given, so 1000 people at 40 across lays itself out as 25 rows. Naming a
    # GRID_ROWS here would look like a setting and change nothing if edited.
    GRID_COLS = 40

    # Fixed, not adjustable. Real Delta32 frequencies run from roughly 0.16 in
    # Norway and Finland down to about 0.04 in Sardinia and Greece, and
    # essentially zero in African and East Asian populations. 0.10 is the
    # round Northern European value, and fixing it means the counts below come
    # out as flat, quotable integers instead of numbers that slide around.
    Q_DELTA32 = 0.10

    # Genotype codes, used everywhere: index into colours, labels, fitnesses.
    WT, HET, HOM = 0, 1, 2

    def hw_freqs(q):
        # Random mating, so a genotype is just two independent draws from the
        # allele pool: p^2 wild-type, 2pq heterozygous, q^2 homozygous.
        p = 1.0 - q
        return p * p, 2.0 * p * q, q * q

    def hidden_fraction(q):
        # What share of all the Delta32 copies in the population are sitting
        # inside heterozygotes, where no phenotype ever reveals them?
        #
        #   copies in carriers    = 2pq   (one copy each)
        #   copies in homozygotes = 2q^2  (two copies each)
        #
        #        2pq          2pq        p
        #   ------------- = --------- = ----- = p
        #    2pq + 2q^2     2q(p + q)   p + q
        #
        # Exactly p. Not an approximation, not a limit -- the fraction of a
        # recessive allele that hides is just the frequency of the OTHER
        # allele. At q = 0.10 that is 90%.
        return 1.0 - q

    # --- Relative fitness, by genotype and by environment -------------------
    #
    # Illustrative teaching values, not epidemiological estimates. The whole
    # argument of the reaction-norm plot rests on the SHAPE -- flat in one
    # environment, fanned in the other -- and not on the magnitude, so the
    # exact cost of susceptibility is chosen to be legible rather than
    # accurate.
    #
    # The two susceptible genotypes share a value because Delta32 resistance
    # is recessive: a heterozygote has functional CCR5 and is not protected.
    W_NO_HIV = {WT: 1.00, HET: 1.00, HOM: 1.00}
    W_HIV = {WT: 0.50, HET: 0.50, HOM: 1.00}
    return (
        GRID_COLS,
        HET,
        HOM,
        N_PEOPLE,
        Q_DELTA32,
        WT,
        W_HIV,
        W_NO_HIV,
        hidden_fraction,
        hw_freqs,
    )


@app.cell
def _(N_PEOPLE, np):
    # Each person gets a fixed rank, a shuffled integer in 0..N-1, and the
    # Hardy-Weinberg counts cut that range into three. Assigning genotypes
    # this way rather than sampling them has two payoffs.
    #
    # First, the layout is frozen: the three views recolour the same thousand
    # circles instead of drawing three unrelated populations, so a student can
    # watch one individual change category.
    #
    # Second, the counts land on the Hardy-Weinberg proportions EXACTLY --
    # 810 / 180 / 10, not a random draw near them. That is deliberate.
    # Sampling noise here would be noise about a completely different topic,
    # and a student puzzling over why they got 9 resistant people instead of
    # 10 is not thinking about cryptic variation.
    #
    # The rank is an integer rather than a fraction in [0, 1) for a reason
    # found the hard way. Ranks of i/N thresholded against q^2 very nearly
    # worked: person 11 sits at exactly 0.010, q^2 evaluates to
    # 0.010000000000000002, and that last bit tipped one extra person into the
    # resistant class -- 809/180/11, and a hidden fraction of 89% printed
    # underneath a heading claiming exactly 90%. Counting in whole people
    # cannot drift.
    #
    # Seeded so the picture is identical on every machine: an instructor can
    # point at a circle and have the whole room looking at the same person.
    _rank_rng = np.random.default_rng(32)  # 32, for the 32 bases
    person_rank = _rank_rng.permutation(N_PEOPLE)
    return (person_rank,)


@app.cell
def _(mo):
    # The only control in the notebook. There is deliberately no slider for
    # the allele frequency or for the fitness cost: this demo makes one
    # argument about one real population, and a parameter to sweep would
    # invite exactly the "watch it adapt" reading the notebook is built to
    # avoid.
    #
    # It opens on the blind view on purpose. The reveal has to be something
    # the student does, not something already done for them on load.
    VIEW_BLIND = "🙈  What the environment sees"
    VIEW_GENOME = "🧬  What the genome contains"
    VIEW_HIV = "🦠  HIV arrives"

    view_radio = mo.ui.radio(
        options=[VIEW_BLIND, VIEW_GENOME, VIEW_HIV],
        value=VIEW_BLIND,
        inline=True,
    )
    return VIEW_BLIND, VIEW_GENOME, VIEW_HIV, view_radio


@app.cell
def _(mo, view_radio):
    mo.hstack([view_radio], justify="center")
    return


@app.cell
def _(HET, HOM, N_PEOPLE, Q_DELTA32, WT, hidden_fraction, hw_freqs, np, person_rank):
    # Everything here is constant -- q never moves -- but it lives in one cell
    # so the grid, the cards and the plot all read the same numbers rather
    # than each recomputing Hardy-Weinberg slightly differently.
    q = Q_DELTA32
    p = 1.0 - q
    f_wt, f_het, f_hom = hw_freqs(q)
    frac_hidden = hidden_fraction(q)

    # Convert the Hardy-Weinberg proportions into whole numbers of people
    # FIRST, then cut the integer ranks on those counts. Going via counts is
    # what makes the grid land on exactly 810 / 180 / 10; comparing a float
    # rank against q^2 does not (see the rank cell above).
    #
    # Rarest class first, so the resistant homozygotes are a stable contiguous
    # block at the bottom of the rank order rather than a set that reshuffles
    # if the thresholds are ever recomputed.
    n_hom = int(round(f_hom * N_PEOPLE))
    n_het = int(round(f_het * N_PEOPLE))
    n_wt = N_PEOPLE - n_hom - n_het  # absorbs any rounding, so the total is N

    genotype = np.where(
        person_rank < n_hom,
        HOM,
        np.where(person_rank < n_hom + n_het, HET, WT),
    )

    # Copies of the allele, not people carrying it: one per heterozygote, two
    # per homozygote. This is what the 90% is a fraction OF.
    n_copies = n_het + 2 * n_hom
    n_copies_hidden = n_het
    return (
        f_het,
        f_hom,
        f_wt,
        frac_hidden,
        genotype,
        n_copies,
        n_copies_hidden,
        n_het,
        n_hom,
        n_wt,
        p,
        q,
    )


@app.cell
def _(
    GRID_COLS,
    HET,
    HOM,
    N_PEOPLE,
    VIEW_BLIND,
    VIEW_GENOME,
    VIEW_HIV,
    genotype,
    mo,
    n_het,
    n_hom,
    n_wt,
    view_radio,
):
    # The three colour maps. Only this dictionary differs between the views --
    # the grid itself, the positions, and the genotypes are identical in all
    # three, which is the point being made.
    _view = view_radio.value

    _GREY = "#8a8177"
    _BLUE = "#4C72B0"
    _RED = "#C44E52"
    _GREEN = "#1f8a4c"

    if _view == VIEW_BLIND:
        # Every genotype maps to the same colour. Not "hard to tell apart" --
        # literally the same value, because the environment is not making a
        # distinction it is failing to make well. It is making none at all.
        _fill = {0: _GREY, HET: _GREY, HOM: _GREY}
        _legend = [(_GREY, "a person")]
        _caption = (
            "A thousand people, and not one visible difference between them. "
            "As far as any environment this population has ever encountered "
            "is concerned, it is <b>monomorphic</b> at this locus."
        )
    elif _view == VIEW_GENOME:
        _fill = {0: _GREY, HET: _BLUE, HOM: _RED}
        _legend = [
            (_GREY, f"+/+ &nbsp;<b>{n_wt}</b>"),
            (_BLUE, f"+/Δ32 &nbsp;<b>{n_het}</b>"),
            (_RED, f"Δ32/Δ32 &nbsp;<b>{n_hom}</b>"),
        ]
        _caption = (
            "The same thousand people, at the same instant. "
            "<b>Nothing evolved between these two pictures.</b> The only "
            "thing that changed is that we were allowed to look at the "
            "genotype instead of the phenotype."
        )
    else:
        # The virus draws its own line, and it is not the genome's line.
        # Carriers go back to grey here -- that reversion is the single most
        # important frame in the notebook.
        _fill = {0: _GREY, HET: _GREY, HOM: _GREEN}
        _legend = [
            (_GREY, f"can be infected &nbsp;<b>{n_wt + n_het}</b>"),
            (_GREEN, f"resistant &nbsp;<b>{n_hom}</b>"),
        ]
        _caption = (
            "The virus sorts them differently than the genome does. R5-tropic "
            "HIV-1 needs a working CCR5 receptor to enter a cell, and a "
            "heterozygote has one — so <b>carriers are not protected</b>, and "
            "to the virus they are indistinguishable from wild-type. "
            f"Resistance is recessive, so it surfaces in <b>{n_hom} people</b>, "
            f"not the {n_het + n_hom} who carry the allele."
        )

    # Plain `_i` is fine as a loop variable here: marimo rewrites underscore
    # names into cell-locals, which breaks them only when a closure has to
    # resolve them later. Nothing captures this one -- the string is built and
    # finished inside the cell.
    _cells = "".join(
        f'<div class="cc-dot" style="background:{_fill[int(genotype[_i])]}"></div>'
        for _i in range(N_PEOPLE)
    )

    _legend_html = "".join(
        f'<div class="cc-key"><span class="cc-swatch" style="background:{_c}">'
        f"</span>{_t}</div>"
        for _c, _t in _legend
    )

    # The <style> block is re-emitted with its markup on every render. Cell
    # output ordering is not reliable in a WASM export, so a stylesheet parked
    # in some other cell may not have arrived yet; shipping it alongside the
    # thing it styles is idempotent and always in time.
    _html = f"""
    <style>
    .cc-wrap {{ font-family: system-ui, sans-serif; }}
    .cc-legend {{
        display: flex; gap: 1.3rem; justify-content: center; flex-wrap: wrap;
        padding: 0.2rem 0 0.7rem 0; font-size: 0.9rem; color: #6f6960;
    }}
    .cc-key {{ display: flex; align-items: center; gap: 0.4rem; }}
    .cc-key b {{ color: #33302c; }}
    .cc-swatch {{
        width: 0.8rem; height: 0.8rem; border-radius: 50%;
        display: inline-block;
    }}
    .cc-grid {{
        display: grid;
        grid-template-columns: repeat({GRID_COLS}, 1fr);
        gap: 3px;
        padding: 0.9rem;
        border-radius: 14px;
        background: #fbfaf8;
        border: 2px solid #e6e1d8;
    }}
    .cc-dot {{
        aspect-ratio: 1 / 1;
        border-radius: 50%;
        /* The transition is the payoff: the reveal blooms across the
           population instead of cutting, so the eye follows WHICH circles
           changed rather than just noticing the picture is different. */
        transition: background 0.28s ease;
        box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.13);
    }}
    .cc-caption {{
        max-width: 46rem; margin: 0.85rem auto 0 auto; text-align: center;
        font-size: 0.93rem; line-height: 1.5; color: #6f6960;
    }}
    .cc-caption b {{ color: #33302c; }}
    </style>
    <div class="cc-wrap">
      <div class="cc-legend">{_legend_html}</div>
      <div class="cc-grid">{_cells}</div>
      <div class="cc-caption">{_caption}</div>
    </div>
    """

    mo.Html(_html)
    return


@app.cell
def _(f_het, f_hom, f_wt, frac_hidden, mo, n_copies, n_copies_hidden, n_het, n_hom, n_wt, p):
    # Counts lead, percentages follow. "10 people" is a fact a student can
    # picture; "1.0%" is a number they skim past -- and at this frequency the
    # gap between 18% of people carrying the allele and 1% showing anything is
    # the entire lesson, so it needs to be countable.
    _cards = f"""
    <style>
    .cc-cards {{
        display: flex; gap: 0.9rem; justify-content: center;
        padding: 1.1rem 0 0.2rem 0; flex-wrap: wrap;
    }}
    .cc-card {{
        flex: 1 1 0; min-width: 150px; max-width: 235px;
        border-radius: 12px; padding: 0.85rem 0.7rem; text-align: center;
        font-family: system-ui, sans-serif; border: 2px solid; background: #fbfaf8;
    }}
    .cc-card-title {{
        font-size: 0.74rem; font-weight: 800; text-transform: uppercase;
        letter-spacing: 0.09em; color: #7a7382;
    }}
    .cc-card-val {{ font-size: 2.5rem; font-weight: 800; line-height: 1.15; }}
    .cc-card-sub {{ font-size: 0.8rem; color: #7a7382; }}
    </style>
    <div class="cc-cards">
      <div class="cc-card" style="border-color:#8a8177">
        <div class="cc-card-title">Susceptible +/+</div>
        <div class="cc-card-val" style="color:#8a8177">{n_wt}</div>
        <div class="cc-card-sub">{f_wt:.0%} — no Δ32 copy at all</div>
      </div>
      <div class="cc-card" style="border-color:#4C72B0">
        <div class="cc-card-title">Silent carriers +/Δ32</div>
        <div class="cc-card-val" style="color:#4C72B0">{n_het}</div>
        <div class="cc-card-sub">{f_het:.0%} — one copy, no phenotype</div>
      </div>
      <div class="cc-card" style="border-color:#1f8a4c">
        <div class="cc-card-title">Resistant Δ32/Δ32</div>
        <div class="cc-card-val" style="color:#1f8a4c">{n_hom}</div>
        <div class="cc-card-sub">{f_hom:.1%} — the only ones HIV cannot enter</div>
      </div>
      <div class="cc-card" style="border-color:#C44E52">
        <div class="cc-card-title">Δ32 copies hidden</div>
        <div class="cc-card-val" style="color:#C44E52">{frac_hidden:.0%}</div>
        <div class="cc-card-sub">
          {n_copies_hidden} of {n_copies} copies — that is <i>p</i>, exactly
        </div>
      </div>
    </div>
    """

    mo.Html(_cards)
    return


@app.cell
def _(HET, HOM, WT, W_HIV, W_NO_HIV, plt):
    # --- Fitness by genotype, in two environments ---------------------------
    #
    # Genotype on the x-axis, one coloured series per environment. Drawn this
    # way round rather than as classic reaction norms (environment on x, a
    # line per genotype) because the shape that matters here is what happens
    # ACROSS genotypes within an environment:
    #
    #   no HIV      - three points at the same height. Flat. A population with
    #                 plenty of genetic variation and zero fitness variation.
    #   HIV present - flat across +/+ and +/Delta32, then a step up at
    #                 Delta32/Delta32.
    #
    # That step is the recessiveness, drawn. With environment on the x-axis
    # the two susceptible genotypes' lines lie exactly on top of each other
    # and have to be dashed and nudged apart to stay visible; here they are
    # simply two points at the same height, which states the same fact
    # without the drawing trick.
    _fig, _ax = plt.subplots(figsize=(7.4, 4.4))

    _order = [WT, HET, HOM]
    _xs = [0, 1, 2]
    _labels = ["+/+", "+/Δ32", "Δ32/Δ32"]

    for _w, _lab, _col, _mk in (
        (W_NO_HIV, "no HIV", "#4C72B0", "o"),
        (W_HIV, "HIV present", "#C44E52", "s"),
    ):
        _ys = [_w[_g] for _g in _order]
        _ax.plot(_xs, _ys, "-", color=_col, linewidth=2.4, zorder=3)
        _ax.plot(_xs, _ys, _mk, color=_col, markersize=10, label=_lab, zorder=4)

    # Two annotations, one per environment, both parked in empty space.
    # An earlier version had three arrows converging on the middle of the
    # plot and they crossed each other; the two line shapes already carry
    # the argument, so the labels only have to name what each shape means.
    _ax.text(
        1.0, 1.10,
        "flat: every genotype equally fit,\nnothing for selection to act on",
        fontsize=8.5, color="#4C72B0", ha="center", va="bottom",
    )
    _ax.annotate(
        "the step is the recessiveness:\nonly Δ32/Δ32 gains anything",
        xy=(1.62, 0.76), xytext=(0.44, 0.20),
        fontsize=8.5, color="#C44E52",
        arrowprops=dict(arrowstyle="->", color="#C44E52", linewidth=0.9,
                        alpha=0.7),
    )

    _ax.set_xlim(-0.35, 2.35)
    _ax.set_ylim(0.0, 1.25)
    _ax.set_xticks(_xs)
    _ax.set_xticklabels(_labels)
    _ax.set_xlabel("genotype")
    _ax.set_ylabel("relative fitness")
    _ax.set_title("The same genotypes, valued differently by two environments")
    _ax.legend(loc="center right", fontsize=9, title="environment", title_fontsize=8)
    _ax.spines["top"].set_visible(False)
    _ax.spines["right"].set_visible(False)

    _fig.tight_layout()
    _fig
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **What am I actually looking at?** (explore it first!)": mo.md(
                r"""
                ### The population was never monomorphic

                Flipping between the first two views changes nothing about the
                population. No generation passed. No allele frequency moved.
                Not one person's genotype is different between those two
                pictures. The only thing that changed is **what we were
                allowed to see.**

                That gap — between the variation a population contains and the
                variation its environment can act on — is **cryptic
                variation**, and it is enormous. Selection cannot act on
                variation it cannot see. But the variation does not need
                selection's permission to be there.

                ### Why Δ32 is silent

                *CCR5* codes for a chemokine receptor that sits on the surface
                of immune cells. The Δ32 allele is a 32-base-pair deletion, and
                because 32 is not a multiple of three it throws the reading
                frame out, producing a premature stop codon. The truncated
                protein never reaches the cell surface.

                A person with no functional CCR5 is, under ordinary
                circumstances, entirely unremarkable. There is no syndrome, no
                visible trait, no test a physician would think to run. This is
                the sense in which the allele is invisible: not that it is
                masked by a dominant partner, but that **nothing in the
                environment was ever asking the question it answers.**

                ### Then HIV asks the question

                R5-tropic HIV-1 enters a cell using CD4 *and* CCR5 together.
                No CCR5 on the surface, no entry. Δ32/Δ32 homozygotes are
                strongly resistant to acquiring infection with R5-tropic
                strains — this is the observation behind the Berlin and London
                patients, both of whom cleared HIV after receiving stem cells
                from Δ32/Δ32 donors.

                Heterozygotes are a different story, and the third view is
                built around it. A carrier has reduced but **functional** CCR5.
                They are *not* protected from becoming infected; what they show
                is somewhat slower progression once they are. So the phenotype
                the virus reveals is effectively **recessive**:

                | | people | of 1000 |
                |---|---|---|
                | carry at least one Δ32 | 2pq + q² | 190 |
                | actually resistant | q² | 10 |

                Nineteen out of twenty people carrying this allele get nothing
                from it, even after the environment changes. The reveal is far
                less generous than the genome.

                ### The algebra of invisibility

                Of all the Δ32 copies in a population, the share sitting inside
                heterozygotes — where no phenotype ever exposes them — is

                $$\frac{\text{copies in carriers}}{\text{all copies}}
                = \frac{2pq}{2pq + 2q^{2}}
                = \frac{p}{p + q}
                = p$$

                Exactly $p$. The fraction of a recessive allele that hides is
                simply the frequency of the other allele:

                | q | carriers 2pq | resistant q² | share of copies hidden |
                |---|---|---|---|
                | 0.01 | 2.0% | 0.01% | **99%** |
                | 0.05 | 9.5% | 0.25% | **95%** |
                | 0.10 | 18% | 1.0% | **90%** |
                | 0.16 | 26.9% | 2.6% | **84%** |

                The rarer an allele is, the more completely it disappears. And
                this has nothing to do with *CCR5* — it is true of every
                recessive allele in every randomly mating population. Whatever
                variation you can see in a population, there is systematically
                more that you cannot.

                ### Fitness is not a property of a genotype

                The plot above shows the same three genotypes, valued by two
                different environments. Read the **blue** line first: it is
                flat. Every genotype has the same fitness, so every bit of
                genetic variation in the grid is present in that environment
                and **none of it is worth anything**. Selection there is not
                weak — it is blind. There is nothing for it to act on.

                Now read the **red** line. No new mutation appeared. No allele
                frequency shifted. Not one person's genotype changed. The
                genetic variation is *identical*. What appeared is **fitness**
                variation.

                This is genotype-by-environment interaction (**G×E**) in its
                strict sense: the map from genotype to fitness is not a
                property of the genotype. It is a property of the genotype
                *and* the environment together, and neither one alone predicts
                anything. The question "what is the fitness of Δ32?" has no
                answer until you say which world you are asking in.

                Notice the *shape* of the red line too. It is flat across
                `+/+` and `+/Δ32`, then steps up only at `Δ32/Δ32`. A carrier
                is worth exactly what a non-carrier is worth, even in the
                world where the allele matters enormously. **That step is the
                recessiveness**, drawn: one copy buys nothing, and the whole
                benefit arrives only with the second.

                ### Where Δ32 actually is

                | population | Δ32 frequency |
                |---|---|
                | Norway, Finland | up to ~16% |
                | Northern Europe generally | ~10% |
                | Sardinia, Greece | ~4% |
                | African, East Asian populations | ≈ 0 |

                This notebook makes **no claim about why** that cline exists.
                Δ32 is treated here as strictly neutral standing variation, and
                what put it at 10% in Northern Europe is a genuinely open and
                well-argued question that has nothing to do with HIV — the
                allele was at roughly its present frequency long before the
                virus existed.

                That is worth sitting with. **HIV resistance is not what this
                allele is for.** It is not what it was selected for, not what
                it was maintained for, and not a trait any ancestor of these
                thousand people was ever tested on. It is a coincidence that
                became load-bearing.

                ### The flip side of mismatch

                Evolutionary mismatch is what happens when the environment
                changes and an organism's traits are still good answers to the
                old world. Cryptic variation is the same coin's other face: the
                environment changes, and the answer to the *new* world turns
                out to be already sitting in the population, unremarked,
                because nothing had ever tested it.

                A population's capacity to respond to a novel challenge is
                therefore not limited to what you can see it doing now. It runs
                as deep as its standing variation — most of which is, at any
                given moment, doing nothing at all.

                ### One honest caveat

                This is a deliberately clean picture: one locus, two alleles,
                random mating, exact Hardy–Weinberg proportions, no migration,
                no population structure, and no selection of any kind. The
                fitness values in the reaction-norm plot are illustrative
                teaching numbers chosen to make the shape legible, not
                estimates of anything measured. And resistance in Δ32/Δ32
                individuals, while strong, is not absolute — X4-tropic HIV-1
                strains enter cells through a different co-receptor, CXCR4, and
                are unaffected by the deletion. Treat the numbers here as
                illustration rather than measurement.
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
    return mo, np, plt


if __name__ == "__main__":
    app.run()
