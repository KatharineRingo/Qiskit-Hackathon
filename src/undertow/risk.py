"""Hidden-damage risk: how likely a segment's base is failing even if the surface looks fine.

v0 is a transparent weighted score so the team can explain every number to judges.
Upgrade path: once you have real 311 history, train a classifier (e.g. gradient boosting)
on "segment got a repeat pothole within N weeks" and replace hidden_damage_risk().
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Weights are a starting guess. Tune them, and say in the pitch that they're tunable.
W_TIDE = 0.45          # king-tide water on/under the road
W_GROUNDWATER = 0.35   # saturated base from a high water table
W_ELEVATION = 0.20     # low ground drains slowly

# How much a road matters if it fails.
CRIT_BASE = 1.0
CRIT_EVAC = 1.5
CRIT_HOSPITAL = 1.0


def _scale(x: pd.Series) -> pd.Series:
    lo, hi = x.min(), x.max()
    return (x - lo) / (hi - lo) if hi > lo else x * 0


def hidden_damage_risk(df: pd.DataFrame) -> pd.Series:
    """0-1 probability-like score that the subgrade is compromised."""
    tide = df["tide_exposure"]
    wet_base = 1 - _scale(df["groundwater_ft_below"])   # shallow water table -> 1
    low = 1 - _scale(df["elevation_ft"])                 # low ground -> 1
    raw = W_TIDE * tide + W_GROUNDWATER * wet_base + W_ELEVATION * low
    # Squash so the score behaves like a failure probability and isn't stuck near 0.5.
    return pd.Series(1 / (1 + np.exp(-6 * (raw - 0.45))), index=df.index).round(3)


def criticality(df: pd.DataFrame) -> pd.Series:
    """How much the city loses when this segment fails."""
    return (
        CRIT_BASE
        + CRIT_EVAC * df["evac_route"].astype(float)
        + CRIT_HOSPITAL * df["hospital_access"].astype(float)
    )


def add_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["risk"] = hidden_damage_risk(out)
    out["criticality"] = criticality(out)
    out["value"] = (out["risk"] * out["criticality"]).round(3)  # expected harm avoided by repairing
    return out
