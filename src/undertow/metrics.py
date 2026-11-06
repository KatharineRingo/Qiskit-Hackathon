"""Numbers for the before/after slide. Every plan gets scored by the same functions."""

from __future__ import annotations

import pandas as pd

from .qubo import plan_value

REPAIRED_RISK = 0.05  # assumed residual failure chance after a proper full-depth repair


def corridor_open_probability(df: pd.DataFrame, chosen: set[str], column: str) -> float:
    """Chance every segment of a corridor survives the next king tide (independent failures, v0 assumption)."""
    seg = df[df[column]]
    p = 1.0
    for row in seg.itertuples():
        p *= 1 - (REPAIRED_RISK if row.segment_id in chosen else row.risk)
    return round(p, 3)


def score_plan(df: pd.DataFrame, pairs, chosen: set[str]) -> dict:
    sel = df[df["segment_id"].isin(chosen)]
    unrepaired = df[~df["segment_id"].isin(chosen)]
    return {
        "segments_repaired": len(chosen),
        "cost_used": int(sel["repair_cost"].sum()),
        "objective": plan_value(df, pairs, chosen),
        "hidden_risk_removed": round(float(sel["risk"].sum()), 2),
        "expected_failures_left": round(float(unrepaired["risk"].sum()), 2),
        "evac_route_open_%": round(100 * corridor_open_probability(df, chosen, "evac_route"), 1),
        "hospital_access_open_%": round(100 * corridor_open_probability(df, chosen, "hospital_access"), 1),
    }
