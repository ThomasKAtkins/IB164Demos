import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # Distinguishing Close Hypotheses: The Power of Sample Size

    Suppose we are trying to tell apart two competing hypotheses about a
    coin (or any binary process):

    $$H_1: p = 0.5 \qquad \text{vs.} \qquad H_2: p = 0.5 / 0.95 \approx 0.526$$

    These two values of $p$ are close together, so with a small number
    of trials $n$ it is hard to tell which one generated our data — the
    sampling distributions of the estimator $\hat{p} = X/n$ overlap
    heavily. As $n$ grows, both distributions narrow (their standard
    deviation shrinks like $1/\sqrt{n}$), and the two hypotheses become
    easier to separate.

    Move the slider below to change $n$ and watch the two distributions
    pull apart.
    """)
    return


@app.cell
def _(mo, np):
    n_slider = mo.ui.slider(
        steps=np.round(np.logspace(np.log10(5), np.log10(50000), 41)).astype(int),
        value=5,
        label="n (number of trials, log scale)",
        show_value=True,
        full_width=True,
    )
    n_slider
    return (n_slider,)


@app.cell
def _(n_slider, np, stats):
    n = int(n_slider.value)

    p1 = 0.5
    p2 = 0.5 / 0.95

    mean1, std1 = p1, np.sqrt(p1 * (1 - p1) / n)
    mean2, std2 = p2, np.sqrt(p2 * (1 - p2) / n)

    # Restrict to a window around both distributions (using the normal
    # approximation) so plotting stays fast and well-zoomed even when n is
    # large enough that the full 0..n support would be mostly empty bars.
    pad = 6 * max(std1, std2)
    lo_x = max(0, int(np.floor((min(mean1, mean2) - pad) * n)))
    hi_x = min(n, int(np.ceil((max(mean1, mean2) + pad) * n)))

    x_values = np.arange(lo_x, hi_x + 1)
    phat_values = x_values / n

    pmf1 = stats.binom.pmf(x_values, n, p1)
    pmf2 = stats.binom.pmf(x_values, n, p2)
    return mean1, mean2, n, p1, p2, phat_values, pmf1, pmf2, std1, std2


@app.cell
def _(mean1, mean2, mo, n, std1, std2):
    separation = abs(mean2 - mean1)
    pooled_std = (std1 + std2) / 2
    separation_in_stds = separation / pooled_std if pooled_std > 0 else float("inf")

    mo.md(
        f"""
        **n = {n}**

        $\\hat{{p}}$ under $H_1$: mean $= {mean1:.4f}$, std. dev. $= {std1:.4f}$
        &nbsp;|&nbsp;
        $\\hat{{p}}$ under $H_2$: mean $= {mean2:.4f}$, std. dev. $= {std2:.4f}$

        Separation between means $\\approx {separation_in_stds:.2f}$ pooled standard deviations
        """
    )
    return


@app.cell
def _(mean1, mean2, n, p1, p2, phat_values, plt, pmf1, pmf2):
    fig, ax = plt.subplots(figsize=(9, 5))

    width = (1 / n) * 0.9

    ax.bar(
        phat_values,
        pmf1,
        width=width,
        color="#4C72B0",
        alpha=0.6,
        edgecolor="#4C72B0",
        label=f"$H_1$: p = {p1:.3f}",
    )
    ax.bar(
        phat_values,
        pmf2,
        width=width,
        color="#C44E52",
        alpha=0.6,
        edgecolor="#C44E52",
        label=f"$H_2$: p = {p2:.3f}",
    )

    ax.axvline(mean1, color="#4C72B0", linestyle="--", linewidth=1.2)
    ax.axvline(mean2, color="#C44E52", linestyle="--", linewidth=1.2)

    ax.set_xlabel(r"$\hat{p} = x / n$ (sample proportion)")
    ax.set_ylabel(r"$P(\hat{p} = x/n)$")
    ax.set_title(f"Sampling distributions of $\\hat{{p}}$ under $H_1$ and $H_2$ (n = {n})")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Zoom to where the bars actually are (matches the windowed x_values
    # computed above), with a little breathing room on each side.
    ax.set_xlim(phat_values.min() - width, phat_values.max() + width)

    fig.tight_layout()
    ax
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Chi-square test p-value vs. sample size

    Now suppose the coin's true probability actually is $H_2$
    ($p = 0.526$), and at each $n$ we run a chi-square goodness-of-fit
    test of the observed count against the null $H_1$ ($p = 0.5$). The
    resulting p-value is itself a random variable — its value depends
    on which $x$ happened to come up. Because $X \sim \text{Binomial}(n,
    p_2)$ has a known exact distribution, and the p-value is a
    deterministic function of $x$, we can compute the *exact* sampling
    distribution of the p-value at every $n$ (no simulation needed).

    The plot below shows the median p-value together with the 5th and
    95th percentiles, across a range of $n$, so you can see not just
    the typical p-value but how much it varies from one experiment to
    the next.
    """)
    return


@app.cell
def _(mo):
    show_pvalue_plot = mo.ui.checkbox(label="Show chi-square p-value vs. n plot", value=False)
    show_pvalue_plot
    return (show_pvalue_plot,)


@app.cell
def _(np, stats):
    def _chisq_pvalue_percentiles(n_trials, p_true, p_null, pcts):
        # X ~ Binomial(n_trials, p_true) has a known exact pmf. The
        # 2-category chi-square statistic (and hence its p-value) is a
        # deterministic function of x, so we can push the pmf of X through
        # that function to get the *exact* distribution of the p-value —
        # no Monte Carlo simulation required.
        x_support = np.arange(0, n_trials + 1)
        pmf = stats.binom.pmf(x_support, n_trials, p_true)

        expected_success = n_trials * p_null
        expected_failure = n_trials * (1 - p_null)
        observed_failure = n_trials - x_support
        chisq_stat = (
            (x_support - expected_success) ** 2 / expected_success
            + (observed_failure - expected_failure) ** 2 / expected_failure
        )
        pvalues = stats.chi2.sf(chisq_stat, df=1)

        order = np.argsort(pvalues)
        pvalues_sorted = pvalues[order]
        cdf_sorted = np.cumsum(pmf[order])

        idx = np.clip(np.searchsorted(cdf_sorted, pcts), 0, len(pvalues_sorted) - 1)
        return pvalues_sorted[idx]

    p1_pv = 0.5
    p2_pv = 0.5 / 0.95

    n_axis = np.unique(np.round(np.logspace(np.log10(5), np.log10(50000), 60)).astype(int))

    percentile_results = np.array(
        [_chisq_pvalue_percentiles(n_trials, p2_pv, p1_pv, [0.05, 0.5, 0.95]) for n_trials in n_axis]
    )
    p05_curve = percentile_results[:, 0]
    median_curve = percentile_results[:, 1]
    p95_curve = percentile_results[:, 2]
    return median_curve, n_axis, p05_curve, p95_curve


@app.cell
def _(median_curve, mo, n_axis, p05_curve, p95_curve, plt, show_pvalue_plot):
    if show_pvalue_plot.value:
        pv_fig, pv_ax = plt.subplots(figsize=(9, 5))

        pv_ax.plot(n_axis, median_curve, color="#4C72B0", linewidth=2, label="median p-value")
        pv_ax.fill_between(
            n_axis,
            p05_curve,
            p95_curve,
            color="#4C72B0",
            alpha=0.25,
            label="5th–95th percentile",
        )
        pv_ax.axhline(0.05, color="#C44E52", linestyle="--", linewidth=1.2, label="p = 0.05")

        pv_ax.set_xscale("log")
        pv_ax.set_xlabel("n (number of trials, log scale)")
        pv_ax.set_ylabel("chi-square test p-value")
        pv_ax.set_ylim(0, 1)
        pv_ax.set_title(
            r"P-value of $\chi^2$ test ($H_0: p=0.5$) when data truly comes from $p \approx 0.526$"
        )
        pv_ax.legend()
        pv_ax.spines["top"].set_visible(False)
        pv_ax.spines["right"].set_visible(False)

        pv_fig.tight_layout()
        pvalue_plot_output = pv_ax
    else:
        pvalue_plot_output = mo.md("")

    pvalue_plot_output
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
