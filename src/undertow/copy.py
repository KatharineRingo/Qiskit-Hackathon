"""All plain-language wording and display thresholds for the map, charts and any web app.

Anything a resident or city staff member reads should be defined here so every front end
(Folium map, matplotlib charts, Streamlit, the web app) uses the same words.
Technical terms (QAOA, qubits, QUBO) belong in code and the notebook, not here.
"""

from __future__ import annotations

# ---- risk levels -------------------------------------------------------------------------
# (lower bound inclusive, label, color). Checked from the top down.
RISK_LEVELS = [
    (0.70, "High", "#b3261e"),
    (0.40, "Medium", "#d98200"),
    (0.00, "Low", "#2e7d32"),
]
RISK_NAME = "Hidden damage risk"


def risk_level(risk: float) -> str:
    return next(label for lo, label, _ in RISK_LEVELS if risk >= lo)


def risk_color(risk: float) -> str:
    return next(color for lo, _, color in RISK_LEVELS if risk >= lo)


# ---- layer / plan names ------------------------------------------------------------------
LAYER_RISK = "Hidden damage risk"
LAYER_RECOMMENDED = "Recommended repairs"
LAYER_TODAY = "Today's approach (most complaints)"
LAYER_ROUTES = "Evacuation & hospital routes"

PLAN_RECOMMENDED = "Recommended plan"
PLAN_TODAY = "Today's approach"
BASELINE_PREFIX = "Current policy"  # solver plan names starting with this are "today's approach"

# ---- colors (one place so charts and map agree) ------------------------------------------
COLOR_RECOMMENDED = "#1b5fd1"
COLOR_TODAY = "#6b6b6b"
COLOR_ROUTE_EVAC = "#14213d"
COLOR_ROUTE_HOSPITAL = "#7b2d8e"
COLOR_RANDOM = "#b0b0b0"

# ---- headline & notes --------------------------------------------------------------------
DEMO_DATA_NOTE = "Demo data: made-up roads for illustration, not real measurements."
BUDGET_UNIT = "crew-days"


def headline(recommended_pct: float | None, today_pct: float | None) -> str:
    if recommended_pct is None:
        return "Hidden damage risk and recommended repairs"
    if today_pct is None:
        return f"Evacuation route stays open {recommended_pct:.0f}% of the time with the recommended repairs"
    if recommended_pct > today_pct:
        return (f"Same budget: evacuation route stays open {recommended_pct:.0f}% of the time "
                f"vs. {today_pct:.0f}% with today's approach")
    return (f"Same budget: evacuation route stays open {recommended_pct:.0f}% of the time "
            f"(today's approach: {today_pct:.0f}%)")


# ---- "why is this road risky" phrases ----------------------------------------------------
LOW_ELEVATION_FT = 3.0
HIGH_TIDE_EXPOSURE = 0.40
SHALLOW_WATER_FT = 2.5
FEW_COMPLAINTS = 2
MANY_COMPLAINTS = 4

WHY_LOW = "Low-lying"
WHY_TIDE = "floods during king tides"
WHY_WATER = "groundwater is close to the surface"
WHY_HIDDEN = "few complaints so far, but damage is likely building underneath"
WHY_FALLBACK = "Little exposure to tides or groundwater"
WHY_COMPLAINTS = "Many complaints, but lower hidden risk"

ROUTE_EVAC = "Evacuation route"
ROUTE_HOSPITAL = "Hospital access"
ROUTE_NONE = "Not on an evacuation or hospital route"

REPAIRED_YES = "Repaired"
REPAIRED_NO = "Not repaired"
