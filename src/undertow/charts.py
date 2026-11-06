"""Plain-language charts. Each function returns a matplotlib Figure; titles state the takeaway
and are computed from the numbers passed in. slide=True gives a 16:9, large-font version."""

from __future__ import annotations

from contextlib import contextmanager

import matplotlib

matplotlib.use("Agg", force=False)
import matplotlib.pyplot as plt  # noqa: E402

from . import copy as C  # noqa: E402

INK, MUTED, GRID, BG = "#1c1c1c", "#52514e", "#ebeae6", "#fcfcfb"

# Technical run names -> everyday words (the notebook keeps the technical names in its tables).
RUN_LABELS = {
    "Random guessing": "Random guessing",
    "Ideal simulator": "Quantum optimizer\n(perfect conditions)",
    "Noisy, level 1": "Quantum optimizer\n(realistic noise, basic)",
    "Noisy, level 3": "Quantum optimizer\n(realistic noise)",
    "Noisy, level 3 + DD": "Quantum optimizer\n(realistic noise + extra cleanup)",
}


@contextmanager
def _style(slide: bool):
    base = 20 if slide else 11
    with plt.rc_context({
        "figure.facecolor": BG, "axes.facecolor": BG, "axes.edgecolor": "#d6d5d0", "axes.labelcolor": MUTED,
        "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.grid": True, "grid.color": GRID,
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": base, "axes.titlesize": base + 4, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": base,
    }):
        yield


def _fig(slide: bool, w: float = 8.5, h: float = 4.2):
    return plt.subplots(figsize=(16, 9) if slide else (w, h), constrained_layout=True)


def _title(fig, text: str, slide: bool, width: int) -> None:
    fig.suptitle(_wrap(text, width), x=0.01, ha="left", fontweight="bold", fontsize=(26 if slide else 14))


def _wrap(text: str, width: int) -> str:
    import textwrap
    return "\n".join(textwrap.wrap(text, width))


def evac_route_chart(evac_open_pct: dict[str, float], slide: bool = False):
    """evac_open_pct: {plan label: % chance the evacuation route stays open}. Plans named like today's
    approach are gray; the rest blue. Title states the gap between the best plan and today's approach."""
    items = list(evac_open_pct.items())
    today = [v for k, v in items if k.startswith(C.BASELINE_PREFIX) or k == C.PLAN_TODAY]
    others = [v for k, v in items if not (k.startswith(C.BASELINE_PREFIX) or k == C.PLAN_TODAY)]
    best = max(others) if others else None
    if best is not None and today:
        title = f"Same budget: the recommended plan keeps the evacuation route open {best:.0f}% of the time, vs. {today[0]:.0f}% today"
    else:
        title = "Chance the evacuation route stays open after a king tide"
    def nice(k: str) -> str:
        if k.startswith(C.BASELINE_PREFIX):
            return C.PLAN_TODAY
        if "exact" in k.lower():
            return C.PLAN_RECOMMENDED + " (exact solver)"
        if "noisy" in k.lower():
            return C.PLAN_RECOMMENDED + " (quantum optimizer,\nrealistic noise)"
        if "QAOA" in k:
            return C.PLAN_RECOMMENDED + " (quantum optimizer)"
        return k
    if slide and best is not None:  # one clear comparison: today's approach vs. the recommended plan
        keep_rec = next((k for k, v in items if v == best and "noisy" not in k.lower()), None)
        items = [(k, v) for k, v in items if k.startswith(C.BASELINE_PREFIX) or k == keep_rec]
    names = {k: nice(k) for k, _ in items}
    if slide and best is not None:
        names = {k: (C.PLAN_TODAY if k.startswith(C.BASELINE_PREFIX) else C.PLAN_RECOMMENDED) for k, _ in items}
    with _style(slide):
        fig, ax = _fig(slide, 9, 3.6)
        labels = [names[k] for k, _ in items][::-1]
        vals = [v for _, v in items][::-1]
        colors = [C.COLOR_TODAY if lab == C.PLAN_TODAY else C.COLOR_RECOMMENDED for lab in labels]
        bars = ax.barh(labels, vals, color=colors, height=0.55)
        for b, v in zip(bars, vals):
            ax.annotate(f"{v:.0f}%", (v, b.get_y() + b.get_height() / 2), xytext=(6, 0),
                        textcoords="offset points", va="center", fontweight="bold")
        ax.set_xlim(0, 105)
        ax.set_xlabel("Chance the evacuation route stays open after a king tide (%)")
        ax.grid(axis="y", visible=False)
        _title(fig, title, slide, 62 if slide else 60)
    return fig


def good_plans_chart(p_good_pct: dict[str, float], slide: bool = False):
    """p_good_pct: {technical run name: % of attempts that were good repair plans}. Needs 'Random guessing'.
    slide=True keeps only random / perfect / realistic-noise bars for a clean headline chart."""
    order = ["Random guessing", "Ideal simulator", "Noisy, level 3"] if slide else \
        [k for k in RUN_LABELS if k in p_good_pct]
    rnd = p_good_pct["Random guessing"]
    ideal = p_good_pct.get("Ideal simulator")
    title = (f"The quantum optimizer finds good repair plans {ideal / rnd:.0f}x more often than random guessing"
             if ideal and rnd else "How often each method finds a good repair plan")
    with _style(slide):
        fig, ax = _fig(slide, 9.5, 4.4)
        vals = [p_good_pct[k] for k in order]
        colors = [C.COLOR_RANDOM if k == "Random guessing" else C.COLOR_RECOMMENDED for k in order]
        bars = ax.bar([RUN_LABELS[k] for k in order], vals, color=colors, width=0.6)
        for b, v in zip(bars, vals):
            ax.annotate(f"{v:.1f}%", (b.get_x() + b.get_width() / 2, v), xytext=(0, 5),
                        textcoords="offset points", ha="center", fontweight="bold")
        ax.set_ylabel("Share of attempts that are good repair plans (%)")
        ax.tick_params(axis="x", labelsize=(16 if slide else 8))
        ax.grid(axis="x", visible=False)
        _title(fig, title, slide, 62 if slide else 62)
    return fig


def training_chart(histories: list[list[float]]):
    """Technical chart for the notebook: how the optimizer improves over iterations."""
    import numpy as np
    with _style(False):
        fig, ax = _fig(False, 8, 4)
        for i, h in enumerate(histories):
            ax.plot(np.minimum.accumulate(h), lw=2, label=f"Attempt {i + 1}")
        ax.set_title("The optimizer improves its repair plan with each step", loc="left")
        ax.set_xlabel("Optimizer step")
        ax.set_ylabel("Plan quality (lower = better)")
        ax.legend(frameon=False)
    return fig
