import marimo

__generated_with = "0.23.2"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(
        r"""
        # 🚗 Let's Make a Deal 🐐

        Three doors. One car. Two goats.

        **Pick a door.** The host — who knows what's behind them — opens a
        *different* door to show you a goat, then offers you the choice:
        **stay** or **switch**.

        Does switching help? Make a guess, play a few rounds, then check the
        scoreboard. The explanation is at the bottom — no peeking first.
        """
    )
    return


@app.cell
def _(mo, np, rng):
    def blank_tally():
        # history is a list of (switched, won) pairs, one per completed
        # round, so the convergence plot can replay the running win rate.
        return {"history": []}

    def new_round(tally):
        # The car is drawn HERE, once, and then frozen in state. Drawing it
        # in a reactive cell instead would silently re-roll it every time
        # anything upstream re-rendered, which would change the answer
        # mid-round and quietly corrupt the statistics students are
        # collecting.
        return {
            "phase": "pick",
            "car": int(rng.integers(0, 3)),
            "pick": None,
            "revealed": None,
            "final": None,
            "switched": None,
            "won": None,
            "tally": tally,
        }

    def host_reveal(car, pick):
        # The host KNOWS where the car is. He opens a door that is
        #   (a) not the contestant's pick, and
        #   (b) not the car.
        # When the contestant has already picked the car (probability 1/3),
        # both remaining doors hide goats and the host chooses between them
        # uniformly at random. When the contestant picked a goat
        # (probability 2/3), exactly one door satisfies both conditions and
        # the host's hand is forced -- that forced move is what leaks
        # information about where the car is, and it is the entire reason
        # switching wins two thirds of the time.
        candidates = [d for d in (0, 1, 2) if d != pick and d != car]
        return int(rng.choice(candidates))

    def other_door(pick, revealed):
        return next(d for d in (0, 1, 2) if d != pick and d != revealed)

    def record(tally, switched, won):
        return {"history": tally["history"] + [(switched, won)]}

    def simulate_many(tally, n_rounds):
        # Each simulated round contributes a result for BOTH strategies. For
        # a single round they are perfectly anti-correlated -- staying wins
        # exactly when switching loses -- so recording both gives clean 1/3
        # and 2/3 curves from the same rounds and makes that complementarity
        # visible. Without this, a student who only ever switches generates
        # no stay data at all and the comparison is unreadable.
        cars = rng.integers(0, 3, size=n_rounds)
        picks = rng.integers(0, 3, size=n_rounds)
        stay_wins = cars == picks

        new_history = []
        for _stay_won in stay_wins:
            new_history.append((False, bool(_stay_won)))
            new_history.append((True, not bool(_stay_won)))

        return {"history": tally["history"] + new_history}

    def win_rates(history):
        # Running win rate for each strategy, indexed by how many rounds of
        # that strategy have been played so far.
        stay_rates = []
        switch_rates = []
        stay_wins = stay_n = switch_wins = switch_n = 0

        for _switched, _won in history:
            if _switched:
                switch_n += 1
                switch_wins += _won
                switch_rates.append(switch_wins / switch_n)
            else:
                stay_n += 1
                stay_wins += _won
                stay_rates.append(stay_wins / stay_n)

        return np.array(stay_rates), np.array(switch_rates)

    get_game, set_game = mo.state(new_round(blank_tally()))
    return (
        blank_tally,
        get_game,
        host_reveal,
        new_round,
        other_door,
        record,
        set_game,
        simulate_many,
        win_rates,
    )


@app.cell
def _(
    blank_tally,
    host_reveal,
    new_round,
    other_door,
    record,
    set_game,
    simulate_many,
):
    # Every handler guards on the current phase, so a stale or double click
    # is a no-op rather than a corrupted round. Updates are functional
    # (set_game receives a function of the current state) so a click always
    # acts on the freshest state, never on one captured at definition time,
    # and the dict is rebuilt rather than mutated in place.
    def on_pick(door):
        def _update(game):
            if game["phase"] != "pick":
                return game
            return {
                **game,
                "phase": "revealed",
                "pick": door,
                "revealed": host_reveal(game["car"], door),
            }

        set_game(_update)

    def _resolve(switched):
        def _update(game):
            if game["phase"] != "revealed":
                return game
            final = (
                other_door(game["pick"], game["revealed"])
                if switched
                else game["pick"]
            )
            won = final == game["car"]
            return {
                **game,
                "phase": "done",
                "final": final,
                "switched": switched,
                "won": won,
                "tally": record(game["tally"], switched, won),
            }

        set_game(_update)

    def on_stay():
        _resolve(False)

    def on_switch():
        _resolve(True)

    def on_play_again():
        set_game(lambda game: new_round(game["tally"]))

    def on_simulate():
        set_game(
            lambda game: {
                **game,
                "tally": simulate_many(game["tally"], 100),
            }
        )

    def on_reset_tally():
        set_game(lambda game: {**game, "tally": blank_tally()})
    return (
        on_pick,
        on_play_again,
        on_reset_tally,
        on_simulate,
        on_stay,
        on_switch,
    )


@app.cell
def _(mo, on_pick, on_play_again, on_reset_tally, on_simulate, on_stay, on_switch):
    # This cell must NOT read the game state. Re-running a cell that creates
    # a UI element re-renders and resets that element, so if the buttons
    # depended on the state they would be torn down and rebuilt on every
    # click -- dropping clicks mid-round. Handlers write state; the render
    # cells below read it; nothing does both.
    # Note: the loop variable is deliberately NOT underscore-prefixed.
    # marimo rewrites _-prefixed names into cell-local variables, which are
    # not resolvable from inside a closure, so an underscore name captured by
    # these lambdas raises NameError at click time. The default-argument bind
    # is the usual guard against late-binding in a loop.
    door_buttons = [
        mo.ui.button(
            label=f"Door {door + 1}",
            full_width=True,
            on_change=lambda v, door=door: on_pick(door),
        )
        for door in range(3)
    ]

    stay_button = mo.ui.button(
        label="Stay with my door",
        kind="neutral",
        on_change=lambda v: on_stay(),
    )
    switch_button = mo.ui.button(
        label="Switch to the other door",
        kind="success",
        on_change=lambda v: on_switch(),
    )
    play_again_button = mo.ui.button(
        label="Play again",
        kind="success",
        on_change=lambda v: on_play_again(),
    )
    simulate_button = mo.ui.button(
        label="Simulate 100 rounds",
        on_change=lambda v: on_simulate(),
    )
    reset_tally_button = mo.ui.button(
        label="Reset tally",
        kind="danger",
        on_change=lambda v: on_reset_tally(),
    )
    return (
        door_buttons,
        play_again_button,
        reset_tally_button,
        simulate_button,
        stay_button,
        switch_button,
    )


@app.cell
def _(get_game, mo):
    _game = get_game()
    _phase = _game["phase"]

    # The style block is re-emitted with the doors on every render rather
    # than injected once from its own cell: that makes it idempotent and
    # avoids depending on cell output ordering, which is not something to
    # rely on in a WASM export. Selectors are scoped under .mh- so they
    # cannot collide with marimo's own styles.
    _style = """
    <style>
    .mh-stage {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        gap: 2rem;
        padding: 2.5rem 1rem 1.5rem 1rem;
        perspective: 1400px;
        background: radial-gradient(ellipse at 50% 0%,
                    #3a3357 0%, #241f38 55%, #17142270 100%);
        border-radius: 14px;
        position: relative;
        overflow: hidden;
    }
    .mh-stage::before {
        content: "";
        position: absolute;
        top: -40%;
        left: 50%;
        width: 60%;
        height: 120%;
        transform: translateX(-50%);
        background: radial-gradient(ellipse at 50% 0%,
                    rgba(255, 226, 150, 0.22) 0%, transparent 65%);
        pointer-events: none;
    }
    .mh-slot { position: relative; z-index: 1; }
    .mh-door {
        width: 150px;
        height: 230px;
        border-radius: 10px 10px 5px 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 4.6rem;
        font-family: "Segoe UI Emoji", "Apple Color Emoji",
                     "Noto Color Emoji", sans-serif;
        background: linear-gradient(160deg, #a86f3f 0%, #6f4723 55%, #53341a 100%);
        border: 3px solid #3d2612;
        box-shadow: inset 0 0 0 6px rgba(255, 255, 255, 0.07),
                    0 12px 26px rgba(0, 0, 0, 0.45);
        transition: transform 0.55s cubic-bezier(0.34, 1.2, 0.5, 1),
                    box-shadow 0.3s ease, border-color 0.3s ease;
        transform-origin: left center;
        position: relative;
    }
    .mh-door::after {
        content: "";
        position: absolute;
        right: 14px;
        top: 50%;
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background: #f0d27a;
        box-shadow: 0 0 6px rgba(240, 210, 122, 0.8);
    }
    .mh-door--open::after { display: none; }
    .mh-num {
        position: absolute;
        top: 12px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 1.05rem;
        font-weight: 800;
        font-family: system-ui, sans-serif;
        color: #f5e2b0;
        letter-spacing: 0.08em;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
    }
    .mh-door--picked {
        border-color: #ffd76e;
        box-shadow: inset 0 0 0 6px rgba(255, 255, 255, 0.07),
                    0 0 0 5px rgba(255, 215, 110, 0.55),
                    0 0 34px rgba(255, 215, 110, 0.5),
                    0 12px 26px rgba(0, 0, 0, 0.45);
        animation: mh-pulse 1.4s ease-in-out infinite;
    }
    @keyframes mh-pulse {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-7px); }
    }
    .mh-door--open {
        background: linear-gradient(160deg, #fdfbf5 0%, #e6dfd0 100%);
        border-color: #c9bda6;
        transform: rotateY(-58deg);
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.35);
    }
    .mh-door--win {
        border-color: #ffd76e;
        box-shadow: 0 0 0 6px rgba(255, 215, 110, 0.6),
                    0 0 48px rgba(255, 215, 110, 0.75);
        animation: mh-bounce 0.75s cubic-bezier(0.3, 1.4, 0.5, 1);
    }
    @keyframes mh-bounce {
        0%   { transform: rotateY(-58deg) scale(1); }
        45%  { transform: rotateY(-58deg) scale(1.14); }
        100% { transform: rotateY(-58deg) scale(1); }
    }
    .mh-door--lose {
        border-color: #C44E52;
        box-shadow: 0 0 0 5px rgba(196, 78, 82, 0.5),
                    0 0 26px rgba(196, 78, 82, 0.45);
    }
    .mh-labels {
        display: flex;
        justify-content: center;
        gap: 2rem;
        padding-top: 0.6rem;
    }
    .mh-label {
        width: 150px;
        text-align: center;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #8a8199;
        min-height: 1.3em;
    }
    .mh-label--pick { color: #c9a227; }
    .mh-banner {
        text-align: center;
        font-size: 1.6rem;
        font-weight: 800;
        font-family: system-ui, sans-serif;
        letter-spacing: 0.01em;
        padding: 0.7rem 0 0.2rem 0;
        min-height: 1.2em;
    }
    .mh-banner--win  { color: #1f8a4c; }
    .mh-banner--lose { color: #C44E52; }
    .mh-banner--ask  { color: #4C72B0; }
    </style>
    """

    _doors_html = []
    _labels_html = []

    for _door in range(3):
        _classes = ["mh-door"]
        _label_classes = ["mh-label"]
        _label = ""

        # A door stands open once the host has revealed it, or once the round
        # is over and everything is shown.
        _is_open = _door == _game["revealed"] or _phase == "done"

        if _is_open:
            _classes.append("mh-door--open")
            _face = "&#128663;" if _door == _game["car"] else "&#128016;"
        else:
            _face = "&#128682;"

        if _door == _game["pick"]:
            _label = "your pick"
            _label_classes.append("mh-label--pick")
            if _phase != "done":
                _classes.append("mh-door--picked")

        if _phase == "done":
            if _door == _game["final"]:
                _classes.append("mh-door--win" if _game["won"] else "mh-door--lose")
                _label = "switched here" if _game["switched"] else "stayed here"
            elif _door == _game["revealed"]:
                _label = "host opened"
        elif _door == _game["revealed"]:
            _label = "host opened"

        # The door number sits on the closed face only -- once a door swings
        # open the prize behind it is the thing to look at.
        _num = "" if _is_open else f'<div class="mh-num">{_door + 1}</div>'
        _doors_html.append(
            f'<div class="mh-slot"><div class="{" ".join(_classes)}">'
            f"{_num}{_face}</div></div>"
        )
        _labels_html.append(
            f'<div class="{" ".join(_label_classes)}">{_label}</div>'
        )

    if _phase == "pick":
        _banner = '<div class="mh-banner mh-banner--ask">Pick a door!</div>'
    elif _phase == "revealed":
        _banner = (
            '<div class="mh-banner mh-banner--ask">'
            "A goat! Now — stay, or switch?</div>"
        )
    elif _game["won"]:
        _banner = '<div class="mh-banner mh-banner--win">🎉 You won the car! 🎉</div>'
    else:
        _banner = '<div class="mh-banner mh-banner--lose">🐐 Goat. Bad luck!</div>'

    mo.Html(
        _style
        + f'<div class="mh-stage">{"".join(_doors_html)}</div>'
        + f'<div class="mh-labels">{"".join(_labels_html)}</div>'
        + _banner
    )
    return


@app.cell
def _(
    door_buttons,
    get_game,
    mo,
    play_again_button,
    stay_button,
    switch_button,
):
    # Only the buttons that make sense right now are shown, so the game needs
    # no instructions about which control to press; the stage banner above
    # already says what is being asked.
    _phase = get_game()["phase"]

    if _phase == "pick":
        _controls = mo.hstack(door_buttons, widths="equal", gap=2)
    elif _phase == "revealed":
        _controls = mo.hstack(
            [stay_button, switch_button], justify="center", gap=2
        )
    else:
        _controls = mo.hstack([play_again_button], justify="center")

    _controls
    return


@app.cell
def _(get_game, mo, reset_tally_button, simulate_button):
    _history = get_game()["tally"]["history"]
    _n_stay = sum(1 for _switched, _ in _history if not _switched)
    _n_switch = sum(1 for _switched, _ in _history if _switched)
    _stay_wins = sum(_won for _switched, _won in _history if not _switched)
    _switch_wins = sum(_won for _switched, _won in _history if _switched)

    _stay_pct = f"{_stay_wins / _n_stay:.0%}" if _n_stay else "–"
    _switch_pct = f"{_switch_wins / _n_switch:.0%}" if _n_switch else "–"

    # A scoreboard rather than a table: the two big percentages are the whole
    # point, and pulling them out at size is what makes the 1/3 vs 2/3 split
    # land at a glance from the back of a lecture theatre.
    _scoreboard = f"""
    <style>
    .mh-score {{
        display: flex;
        gap: 1rem;
        justify-content: center;
        padding: 0.5rem 0 0.75rem 0;
    }}
    .mh-card {{
        flex: 1 1 0;
        max-width: 240px;
        border-radius: 12px;
        padding: 1rem 0.75rem;
        text-align: center;
        font-family: system-ui, sans-serif;
        border: 2px solid;
        background: #fbfaf8;
    }}
    .mh-card--stay   {{ border-color: #C44E52; }}
    .mh-card--switch {{ border-color: #4C72B0; }}
    .mh-card-title {{
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #7a7382;
    }}
    .mh-card-pct {{
        font-size: 2.9rem;
        font-weight: 800;
        line-height: 1.15;
    }}
    .mh-card--stay .mh-card-pct   {{ color: #C44E52; }}
    .mh-card--switch .mh-card-pct {{ color: #4C72B0; }}
    .mh-card-sub {{ font-size: 0.82rem; color: #7a7382; }}
    </style>
    <div class="mh-score">
      <div class="mh-card mh-card--stay">
        <div class="mh-card-title">Stayed</div>
        <div class="mh-card-pct">{_stay_pct}</div>
        <div class="mh-card-sub">{_stay_wins} of {_n_stay} won</div>
      </div>
      <div class="mh-card mh-card--switch">
        <div class="mh-card-title">Switched</div>
        <div class="mh-card-pct">{_switch_pct}</div>
        <div class="mh-card-sub">{_switch_wins} of {_n_switch} won</div>
      </div>
    </div>
    """

    mo.vstack(
        [
            mo.Html(_scoreboard),
            mo.hstack(
                [simulate_button, reset_tally_button], justify="center", gap=1
            ),
        ],
        gap=0.5,
    )
    return


@app.cell
def _(get_game, mo, np, plt, win_rates):
    _history = get_game()["tally"]["history"]

    if not _history:
        mo.output.replace(
            mo.md(
                "*Play a round or hit simulate — the win rates get plotted here.*"
            )
        )
    else:
        _stay_rates, _switch_rates = win_rates(_history)

        _fig, _ax = plt.subplots(figsize=(9, 5))

        _ax.axhline(2 / 3, color="#4C72B0", linestyle=":", linewidth=1.2)
        _ax.axhline(1 / 3, color="#C44E52", linestyle=":", linewidth=1.2)

        if len(_switch_rates):
            _ax.plot(
                np.arange(1, len(_switch_rates) + 1),
                _switch_rates,
                color="#4C72B0",
                linewidth=1.8,
                label=f"switch (now {_switch_rates[-1]:.1%})",
            )
        if len(_stay_rates):
            _ax.plot(
                np.arange(1, len(_stay_rates) + 1),
                _stay_rates,
                color="#C44E52",
                linewidth=1.8,
                label=f"stay (now {_stay_rates[-1]:.1%})",
            )

        # Annotate the two theoretical values on the right-hand edge so the
        # dotted reference lines are self-explaining.
        _x_max = max(len(_stay_rates), len(_switch_rates))
        _ax.text(_x_max, 2 / 3, "  2/3", color="#4C72B0", va="center", fontsize=9)
        _ax.text(_x_max, 1 / 3, "  1/3", color="#C44E52", va="center", fontsize=9)

        _ax.set_xlim(1, max(_x_max, 2))
        _ax.set_ylim(0, 1)
        _ax.set_xlabel("rounds played with that strategy")
        _ax.set_ylabel("win rate so far")
        _ax.set_title("Does switching help?")
        _ax.legend(loc="center right")
        _ax.spines["top"].set_visible(False)
        _ax.spines["right"].set_visible(False)

        _fig.tight_layout()
        mo.output.replace(_ax)
    return


@app.cell
def _(mo):
    mo.accordion(
        {
            "🔎 **Why does switching win?** (play first!)": mo.md(
                r"""
                **Switching wins 2/3 of the time. Staying wins 1/3.** It is
                not 50–50.

                Your first pick had a $1/3$ chance of being right, and the
                host's reveal tells you nothing new about *your* door — he was
                always going to open a goat door. So staying wins exactly when
                your first guess was right:

                $$P(	ext{win} \mid 	ext{stay}) = 	frac{1}{3}
                \qquad
                P(	ext{win} \mid 	ext{switch}) = 	frac{2}{3}$$

                Switching wins whenever your first pick was *wrong* — and it
                usually was. Say you pick door 1:

                | Car is behind | Host opens | Stay | Switch |
                |---|---|---|---|
                | Door 1 | door 2 or 3 (free) | **win** | lose |
                | Door 2 | door 3 (forced) | lose | **win** |
                | Door 3 | door 2 (forced) | lose | **win** |

                Notice the word *forced*. Two times out of three the host has
                no choice, so the door he leaves closed is the car door. His
                knowledge leaks information — and all of it flows to the door
                you didn't pick.

                A host opening doors **at random** would sometimes reveal the
                car, and in the surviving rounds staying and switching would
                each win half the time. Same goat, same open door, completely
                different conclusion — because what you can infer depends on
                the *process* that generated the observation, not just on what
                you see. That is the part worth carrying into the rest of the
                course.
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

    # Deliberately unseeded: a fixed seed would hand every student in the lab
    # the identical sequence of doors.
    rng = np.random.default_rng()
    return mo, np, plt, rng


if __name__ == "__main__":
    app.run()
