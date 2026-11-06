"""Scenario for the web app: real Miami Beach streets, hidden risk, evacuation route, hospital, low-lying water.

Uses data/segments.csv when present. Otherwise the synthetic network is mapped onto real streets
(approximate coordinates). Everything here is demo data and says so.
"""

from __future__ import annotations

import math
import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from undertow import copy as C  # noqa: E402
from undertow.data_synthetic import adjacency_pairs, make_grid_network  # noqa: E402
from undertow.risk import add_scores  # noqa: E402
from undertow.viz import segment_explanation  # noqa: E402

CANDIDATES = 8                      # roads sent to the optimizer = qubits (2^8 = 256 possible plans)
BUDGET_SHARES = [("small", "Small", 0.10), ("medium", "Medium", 0.20), ("large", "Large", 0.30), ("max", "Max", 0.45)]
DOLLARS_PER_CREW_DAY = 10_000        # illustrative assumption, not a real cost estimate
HOSPITAL = {"name": "Mount Sinai Medical Center", "coord": [-80.1372, 25.8127]}  # approximate, 4300 Alton Rd

# Used only when data/segments.csv is missing: (street, (lat1, lon1), (lat2, lon2)) with approximate coordinates.
RISK_STREETS = [
    ("West Ave (10th-14th St)", (25.7790, -80.1420), (25.7860, -80.1420)),
    ("Dade Blvd (along Collins Canal)", (25.7955, -80.1380), (25.7955, -80.1310)),
    ("Alton Rd (6th-10th St)", (25.7740, -80.1395), (25.7800, -80.1395)),
    ("Purdy Ave (Sunset Harbour)", (25.7885, -80.1445), (25.7945, -80.1445)),
    ("Bay Rd (20th-23rd St)", (25.7930, -80.1470), (25.7990, -80.1470)),
]
COMPLAINT_STREETS = [
    ("Collins Ave", (25.7770, -80.1295), (25.7840, -80.1290)),
    ("Washington Ave", (25.7770, -80.1330), (25.7840, -80.1325)),
    ("Ocean Dr", (25.7770, -80.1280), (25.7840, -80.1275)),
    ("Pine Tree Dr", (25.7990, -80.1340), (25.8050, -80.1335)),
]


def _remap_synthetic(df: pd.DataFrame) -> pd.DataFrame:
    """Put synthetic segments on real streets: riskiest ones on the hidden-risk streets,
    most-complained ones on the high-complaint streets."""
    df = df.copy()
    df["street_name"] = None
    risky = df.sort_values("risk", ascending=False).head(len(RISK_STREETS))
    rest = df.drop(risky.index).sort_values("reports_311", ascending=False).head(len(COMPLAINT_STREETS))
    for (name, p1, p2), idx in list(zip(RISK_STREETS, risky.index)) + list(zip(COMPLAINT_STREETS, rest.index)):
        df.loc[idx, ["lat1", "lon1", "lat2", "lon2", "street_name"]] = [*p1, *p2, name]
    df = df[df["street_name"].notna()].copy()
    df[["lat1", "lon1", "lat2", "lon2"]] = df[["lat1", "lon1", "lat2", "lon2"]].astype(float)
    df.loc[df["street_name"].isin([s[0] for s in RISK_STREETS]), "reports_311"] = 1
    df.loc[df["street_name"].isin([s[0] for s in COMPLAINT_STREETS]), "reports_311"] = 8
    return df.reset_index(drop=True)


@lru_cache(maxsize=1)
def load_df() -> pd.DataFrame:
    csv = ROOT / "data" / "segments.csv"
    if csv.exists():
        df = pd.read_csv(csv)
    else:
        df = _remap_synthetic(add_scores(make_grid_network()[1]))
    return add_scores(df).reset_index(drop=True)


def data_source_note(df: pd.DataFrame) -> str:
    return C.ESTIMATED_DATA_NOTE if "data_source" in df else C.DEMO_DATA_NOTE


def block_names(df: pd.DataFrame) -> dict[str, tuple[str, str]]:
    street = df["street_name"].fillna("Unnamed road")
    totals = street.value_counts().to_dict()
    seen, out = {}, {}
    for sid, st in zip(df["segment_id"], street):
        seen[st] = seen.get(st, 0) + 1
        out[sid] = (st, f"block {seen[st]}" if totals[st] > 1 else "full length")
    return out


def _quad(p1, p2, half_width_deg: float):
    (lon1, lat1), (lon2, lat2) = p1, p2
    k = math.cos(math.radians((lat1 + lat2) / 2))
    dx, dy = (lon2 - lon1) * k, lat2 - lat1
    n = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / n * half_width_deg, dx / n * half_width_deg
    pts = [(lon1 + nx / k, lat1 + ny), (lon2 + nx / k, lat2 + ny), (lon2 - nx / k, lat2 - ny), (lon1 - nx / k, lat1 - ny)]
    return [[[float(x), float(y)] for x, y in pts + [pts[0]]]]


def candidate_ids(df: pd.DataFrame) -> list[str]:
    return list(df.sort_values("value", ascending=False).head(CANDIDATES)["segment_id"])


def budgets(df: pd.DataFrame) -> list[dict]:
    total = int(df["repair_cost"].sum())
    return [{"key": k, "label": lbl, "units": max(int(df["repair_cost"].min()), round(total * s))} for k, lbl, s in BUDGET_SHARES]


def budget_range(df: pd.DataFrame) -> dict:
    """Slider range in crew-days (whole numbers), plus the illustrative dollar rate."""
    ids = candidate_ids(df)
    lo = int(df[df["segment_id"].isin(ids)]["repair_cost"].min())
    presets = budgets(df)
    return {"min_units": lo, "max_units": presets[-1]["units"], "default_units": presets[1]["units"],
            "dollars_per_crew_day": DOLLARS_PER_CREW_DAY}


def tide_curve() -> list[dict]:
    """Illustrative monthly tide level (0-1), peaking in the autumn king tide season."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    out = []
    for i, m in enumerate(months):
        level = (1 + math.cos(2 * math.pi * (i - 9) / 12)) / 2
        out.append({"month": m, "level": round(level, 3), "king_tide": level >= 0.85})
    return out


def scenario() -> dict:
    df = load_df()
    names = block_names(df)
    feats = []
    for r in df.itertuples():
        st, blk = names[r.segment_id]
        feats.append({"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[r.lon1, r.lat1], [r.lon2, r.lat2]]},
                      "properties": {"id": r.segment_id, "street": st, "block": blk, "risk": float(r.risk),
                                     "risk_word": C.risk_level(r.risk), "reason": segment_explanation(r),
                                     "complaints": int(r.reports_311), "evac": bool(r.evac_route),
                                     "hospital": bool(r.hospital_access), "crew_days": int(r.repair_cost)}})
    route = [f for f in feats if f["properties"]["evac"] or f["properties"]["hospital"]]
    low = df[df["elevation_ft"] <= df["elevation_ft"].quantile(0.4)]
    water = []
    for r in low.itertuples():
        for lvl, hw in enumerate((0.00095, 0.00065, 0.00035), start=1):
            water.append({"type": "Feature", "geometry": {"type": "Polygon", "coordinates": _quad((r.lon1, r.lat1), (r.lon2, r.lat2), hw)},
                          "properties": {"level": lvl, "elevation_ft": float(r.elevation_ft), "segment": r.segment_id}})
    lons = df[["lon1", "lon2"]].values.ravel(); lats = df[["lat1", "lat2"]].values.ravel()
    xy = np.column_stack([(lons - lons.mean()) * math.cos(math.radians(lats.mean())), lats - lats.mean()])
    _, _, vt = np.linalg.svd(xy, full_matrices=False)
    theta = math.degrees(math.atan2(vt[0][0], vt[0][1])) % 180            # compass heading of the long axis, 0-180
    return {
        "demo": True,
        "data_note": data_source_note(df) + f" Dollar amounts are illustrative (${DOLLARS_PER_CREW_DAY:,} per crew-day).",
        "center": [float(lons.mean()), float(lats.mean())],
        "bounds": [[float(min(lons.min(), HOSPITAL["coord"][0])), float(min(lats.min(), HOSPITAL["coord"][1]))],
                   [float(max(lons.max(), HOSPITAL["coord"][0])), float(max(lats.max(), HOSPITAL["coord"][1]))]],
        "bearing": round(theta - 90, 1),
        "segments": {"type": "FeatureCollection", "features": feats},
        "route": {"type": "FeatureCollection", "features": route},
        "hospital": HOSPITAL,
        "water": {"type": "FeatureCollection", "features": water},
        "tide": tide_curve(),
        "budgets": budgets(df),
        "budget_range": budget_range(df),
        "optimizer": {"candidates": candidate_ids(df), "num_qubits": CANDIDATES},
        "crew_day_label": C.BUDGET_UNIT,
    }
