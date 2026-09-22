import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(
        r"""
        # A Toy Model of a "Complex" (Polygenic) Trait

        Traits like height are called **polygenic** because they are
        influenced by many genes at once, each with a small effect — unlike
        a trait such as ABO blood type, which is controlled by a single
        gene. This notebook builds a deliberately oversimplified model of a
        polygenic trait (think: height) to show *why* traits like this end
        up looking smooth and bell-curve-shaped, even though the underlying
        genetics is a bunch of discrete on/off coin flips.

        **The model, per locus:**

        Each of the $n$ loci is biallelic ($A$ / $a$) with both alleles
        equally common in the population, so under Hardy–Weinberg
        equilibrium a person's genotype at that locus is

        $$P(AA) = 0.25, \qquad P(Aa) = 0.5, \qquad P(aa) = 0.25$$

        We assume **full dominance**: one copy of $A$ is as good as two, so
        a locus "contributes" (genotype $AA$ or $Aa$) with probability
        $0.75$, and contributes nothing (genotype $aa$) with probability
        $0.25$ — independently at every locus.

        If a contributing locus adds a fixed amount `effect_size` to height,
        then the total genetic contribution across all $n$ loci is exactly

        $$\text{height} = \text{baseline} + \text{effect\_size} \times X,
        \qquad X \sim \text{Binomial}(n,\ 0.75)$$

        **Holding the effect size fixed to the number of loci:** so that
        changing $n$ doesn't also change the *total possible* height range,
        we scale the per-locus effect down as $n$ grows:
        $\text{effect\_size} = k / n$, where $k$ is a fixed constant. This
        keeps the minimum and maximum possible height the same no matter
        how many loci you choose — only the *shape* of the distribution
        changes.

        Move the slider below to change $n$ (the number of loci) and watch
        the phenotype distribution smooth out — this is the Central Limit
        Theorem in action, and it's the real reason polygenic traits look
        continuous and normally distributed despite being built from
        discrete Mendelian pieces underneath.
        """
    )
    return


@app.cell
def _(mo):
    n_loci_slider = mo.ui.slider(
        start=1,
        stop=200,
        value=1,
        step=1,
        label="n_loci (number of contributing genes)",
        show_value=True,
        full_width=True,
    )
    n_loci_slider
    return (n_loci_slider,)


@app.cell
def _(n_loci_slider, np, stats):
    n_loci = n_loci_slider.value

    baseline_height = 150.0  # cm, height with zero contributing loci
    total_range_cm = 40.0  # cm, fixed total swing from 0 to n_loci contributing loci
    p_contributes = 0.75  # P(locus contributes) under full dominance, allele freq 0.5

    effect_size = total_range_cm / n_loci

    x_values = np.arange(0, n_loci + 1)
    height_values = baseline_height + effect_size * x_values
    pmf_values = stats.binom.pmf(x_values, n_loci, p_contributes)

    mean_height = baseline_height + effect_size * n_loci * p_contributes
    std_height = effect_size * np.sqrt(n_loci * p_contributes * (1 - p_contributes))
    return (
        baseline_height,
        effect_size,
        height_values,
        mean_height,
        n_loci,
        pmf_values,
        std_height,
        total_range_cm,
    )


@app.cell
def _(baseline_height, effect_size, mean_height, mo, n_loci, std_height, total_range_cm):
    mo.md(
        f"""
        **n_loci = {n_loci}**  &nbsp;|&nbsp;  effect_size $= {total_range_cm:.0f} / n\\_loci = {effect_size:.3f}$ cm per contributing locus

        Possible height range: **{baseline_height:.0f} – {baseline_height + total_range_cm:.0f} cm** (fixed, independent of n_loci)

        Mean $= {mean_height:.2f}$ cm &nbsp;|&nbsp; Std. Dev. $= {std_height:.3f}$ cm
        """
    )
    return


@app.cell
def _(height_values, mean_height, n_loci, plt, pmf_values, total_range_cm):
    fig, ax = plt.subplots(figsize=(9, 5))

    # At small n_loci there are only a few possible heights, so we draw
    # them as visibly thin, fixed-width spikes — narrow relative to the
    # *fixed* total height range, not just the spacing between points — to
    # make clear this is a genuinely discrete distribution, not a
    # histogram with coarse bins. Once n_loci is large enough that those
    # thin spikes would be narrower than the spacing between them (i.e.
    # they'd start overlapping or shrink to sub-pixel width), we switch to
    # a filled step curve instead: at that point the distribution is
    # dense enough that it's genuinely closer to continuous, which is the
    # whole point of the demo.
    thin_bar_width = total_range_cm * 0.015
    point_spacing = height_values[1] - height_values[0] if n_loci > 1 else total_range_cm

    if n_loci > 1 and thin_bar_width >= point_spacing:
        ax.fill_between(height_values, pmf_values, step="mid", color="#4C72B0", alpha=0.6)
        ax.plot(height_values, pmf_values, color="#4C72B0", linewidth=1, drawstyle="steps-mid")
    else:
        ax.bar(
            height_values,
            pmf_values,
            width=thin_bar_width,
            color="#4C72B0",
            edgecolor="white",
        )

    ax.axvline(mean_height, color="#C44E52", linestyle="--", linewidth=1.5, label=f"mean = {mean_height:.2f} cm")

    ax.set_xlabel("height (cm)")
    ax.set_ylabel("P(height)")
    ax.set_title(f"Phenotype distribution: n_loci = {n_loci}")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    ax
    return


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy import stats

    plt.rcParams["figure.dpi"] = 120
    return mo, np, plt, stats


if __name__ == "__main__":
    app.run()
