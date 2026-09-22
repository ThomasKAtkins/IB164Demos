import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(
        r"""
        # The Binomial Distribution

        A binomial random variable $X \sim \text{Binomial}(n, p)$ counts the
        number of successes in $n$ independent trials, each with success
        probability $p$.

        $$P(X = x) = \binom{n}{x} p^x (1-p)^{n-x}, \qquad x = 0, 1, \dots, n$$

        Enter values below for $n$ (number of trials) and $p$
        (probability of success on each trial), and see how the shape of
        the distribution changes.
        """
    )
    return


@app.cell
def _(mo):
    n_box = mo.ui.number(start=1, stop=1000, value=10, step=1, label="n (number of trials)")
    p_box = mo.ui.number(start=0.0, stop=1.0, value=0.5, step=0.0001, label="p (probability of success)")
    mo.hstack([n_box, p_box], justify="start", gap=3)
    return n_box, p_box


@app.cell
def _(mo, n_box, p_box):
    mo.md(f"**Current parameters:** n = {n_box.value}, p = {p_box.value:.4f}")
    return


@app.cell
def _(mo, n_box, np, p_box, stats):
    mo.stop(
        n_box.value is None or p_box.value is None,
        mo.md("*Enter values for both n and p to see the distribution.*"),
    )

    n = n_box.value
    p = p_box.value

    x_values = np.arange(0, n + 1)
    pmf_values = stats.binom.pmf(x_values, n, p)

    mean = n * p
    variance = n * p * (1 - p)
    std = np.sqrt(variance)
    return mean, n, p, pmf_values, std, variance, x_values


@app.cell
def _(mean, mo, std, variance):
    mo.md(
        f"""
        **Summary statistics:**
        Mean $= np = {mean:.3f}$ &nbsp;|&nbsp;
        Variance $= np(1-p) = {variance:.3f}$ &nbsp;|&nbsp;
        Std. Dev. $= {std:.3f}$
        """
    )
    return


@app.cell
def _(mean, n, p, plt, x_values, pmf_values):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x_values, pmf_values, color="#4C72B0", edgecolor="white", width=0.85)
    ax.axvline(mean, color="#C44E52", linestyle="--", linewidth=1.5, label=f"mean = {mean:.2f}")
    ax.set_xlabel("x (number of successes)")
    ax.set_ylabel("P(X = x)")
    ax.set_title(f"Binomial Distribution: n = {n}, p = {p:.4f}")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    ax
    return ax, fig


@app.cell
def _(mo, n, pmf_values, x_values):
    def _format_prob(p_val):
        # Use fixed-point for anything that would round to a visible value,
        # and fall back to scientific notation for very small tail probabilities.
        return f"{p_val:.4f}" if p_val >= 0.00005 else f"{p_val:.2e}"

    if n <= 20:
        header = "| x | P(X = x) |\n|---:|---:|\n"
        rows = "\n".join(
            f"| {x_val} | {_format_prob(p_val)} |"
            for x_val, p_val in zip(x_values, pmf_values)
        )
        table_output = mo.md(f"### Probability table\n\n{header}{rows}")
    else:
        table_output = mo.md(
            f"*n = {n} exceeds 20, so the probability table is hidden. "
            "Lower n to 20 or below to see the table.*"
        )
    table_output
    return (table_output,)


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
