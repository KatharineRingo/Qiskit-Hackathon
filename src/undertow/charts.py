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


def _p(v: float) -> str:
    """Percent text: one decimal below 10% so 0.3% does not read as 0%."""
    return f"{v:.1f}" if 0 < v < 10 else f"{v:.0f}"


def evac_route_chart(evac_open_pct: dict[str, float], slide: bool = False, route: str = "evacuation route"):
    """evac_open_pct: {plan label: % chance the evacuation route stays open}. Plans named like today's
    approach are gray; the rest blue. Title states the gap between the best plan and today's approach."""
    items = list(evac_open_pct.items())
    today = [v for k, v in items if k.startswith(C.BASELINE_PREFIX) or k == C.PLAN_TODAY]
    others = [v for k, v in items if not (k.startswith(C.BASELINE_PREFIX) or k == C.PLAN_TODAY)]
    best = max(others) if others else None
    if best is not None and today:
        title = f"Same budget: the recommended plan keeps the {route} open {_p(best)}% of the time, vs. {_p(today[0])}% today"
    else:
        title = f"Chance the {route} stays open after a king tide"
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
            ax.annotate(f"{_p(v)}%", (v, b.get_y() + b.get_height() / 2), xytext=(6, 0),
                        textcoords="offset points", va="center", fontweight="bold")
        ax.set_xlim(0, 105)
        ax.set_xlabel(f"Chance the {route} stays open after a king tide (%)")
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


def network_figure(df, geometry: dict, chosen: set[str] | None = None, hospital: dict | None = None,
                   context: list | None = None, title: str = "", today: set[str] | None = None, label_chosen: bool = True):
    """Dark map-style picture of the road network: risk as orange glow, chosen repairs as white with a blue halo.
    df needs segment_id, risk, street_name; geometry maps segment_id -> [[lon, lat], ...]; context is a list of street lines."""
    import numpy as np
    chosen, today = chosen or set(), today or set()
    with plt.rc_context({"figure.facecolor": "#05060a", "axes.facecolor": "#05060a", "text.color": "#f0efeb", "font.size": 11}):
        fig, ax = plt.subplots(figsize=(11, 5.2), constrained_layout=True)
        labeled: set[str] = set()
        for w in context or []:
            a = np.array(w); ax.plot(a[:, 0], a[:, 1], color="#252a38", lw=0.7, zorder=1, solid_capstyle="round")
        for r in df.itertuples():
            g = np.array(geometry.get(r.segment_id) or [[r.lon1, r.lat1], [r.lon2, r.lat2]])
            c = (1.0, 0.42, 0.12)
            for w, a in ((16, 0.05), (9, 0.09)):
                ax.plot(g[:, 0], g[:, 1], color=c, lw=w * (0.4 + r.risk), alpha=a * (0.4 + r.risk), zorder=2, solid_capstyle="round")
            if r.segment_id in today:
                ax.plot(g[:, 0], g[:, 1], color="#a78bfa", lw=9, alpha=0.8, zorder=3, solid_capstyle="round")
            ax.plot(g[:, 0], g[:, 1], color=c, lw=1.5 + 3.5 * r.risk, alpha=0.35 + 0.65 * r.risk, zorder=4, solid_capstyle="round")
            if r.segment_id in chosen:
                ax.plot(g[:, 0], g[:, 1], color="#4b93ff", lw=17, alpha=0.30, zorder=5, solid_capstyle="round")
                ax.plot(g[:, 0], g[:, 1], color="white", lw=4.5, zorder=6, solid_capstyle="round")
                if label_chosen and str(r.street_name) not in labeled:
                    labeled.add(str(r.street_name))
                    mid = g[len(g) // 2]
                    ax.annotate(str(r.street_name), mid, xytext=(0, 12), textcoords="offset points", ha="center", fontsize=9,
                                color="#f0efeb", zorder=8, bbox=dict(boxstyle="round,pad=0.25", fc="#05060a", ec="#4b93ff", lw=0.6, alpha=0.85))
        if hospital:
            x, y = hospital["coord"]
            ax.scatter([x], [y], s=900, color="#4b93ff", alpha=0.25, zorder=7)
            ax.scatter([x], [y], s=380, color="white", ec="#4b93ff", lw=2.5, zorder=9)
            ax.annotate("H", (x, y), ha="center", va="center", fontsize=13, fontweight="bold", color="#4b93ff", zorder=10)
            ax.annotate(hospital["name"], (x, y), xytext=(0, 20), textcoords="offset points", ha="center", fontsize=9.5, zorder=10,
                        bbox=dict(boxstyle="round,pad=0.3", fc="#05060a", ec="#4b93ff", lw=0.8))
        pts = np.array([p for r in df.itertuples() for p in (geometry.get(r.segment_id) or [[r.lon1, r.lat1]])])
        if hospital:
            pts = np.vstack([pts, hospital["coord"]])
        padx, pady = 0.0032, 0.0012
        ax.set_xlim(pts[:, 0].min() - padx, pts[:, 0].max() + padx); ax.set_ylim(pts[:, 1].min() - pady, pts[:, 1].max() + pady)
        ax.set_aspect(1 / np.cos(np.radians(pts[:, 1].mean()))); ax.axis("off")
        if title:
            ax.set_title(title, loc="left", fontsize=14, fontweight="bold", color="#f0efeb")
        ax.text(0.995, 0.01, "Street lines © OpenStreetMap contributors", transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color="#6b7080")
    return fig
