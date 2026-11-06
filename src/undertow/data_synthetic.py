"""Synthetic Miami Beach-style road network so the whole pipeline runs before real data lands.

Everything here is FAKE but shaped like the real thing:
- low-lying segments near the bay get more tidal exposure and higher groundwater
- hidden subgrade damage tracks flood exposure, not visible potholes
- 311 pothole reports only partly reflect hidden damage (that's the point of the project)

Swap this module out for data_sources.py once real data is loaded. Keep the same columns.
"""

from __future__ import annotations

import networkx as nx
import numpy as np
import pandas as pd

# Rough bounding box around Miami Beach. Used only to place fake segments on the map.
ORIGIN_LAT, ORIGIN_LON = 25.785, -80.140
STEP_LAT, STEP_LON = 0.004, 0.004

SEGMENT_COLUMNS = [
    "segment_id", "u", "v",               # graph endpoints
    "lat1", "lon1", "lat2", "lon2",       # geometry for the map
    "elevation_ft",                       # lower = worse
    "tide_exposure",                      # 0-1, share of king-tide days with water on/under road
    "groundwater_ft_below",               # depth to water table; smaller = saturated base
    "reports_311",                        # visible pothole complaints (what the city reacts to)
    "evac_route",                         # bool, on the evacuation corridor
    "hospital_access",                    # bool, on the path to the hospital
    "repair_cost",                        # integer cost units (1 unit ~ one crew-day)
]


def make_grid_network(rows: int = 3, cols: int = 4, seed: int = 7) -> tuple[nx.Graph, pd.DataFrame]:
    """Build a small grid of road segments with fake but plausible attributes.

    rows x cols intersections -> rows*(cols-1) + cols*(rows-1) segments.
    The default 3x4 grid gives 17 segments; keep the quantum run small with max_segments in run_demo.
    """
    rng = np.random.default_rng(seed)
    g = nx.grid_2d_graph(rows, cols)

    # West side (col 0) is the bay side: lowest ground.
    def node_pos(n):
        r, c = n
        return ORIGIN_LAT + r * STEP_LAT, ORIGIN_LON + c * STEP_LON

    evac_nodes = {(1, c) for c in range(cols)}          # middle row runs west->east to the causeway
    hospital_nodes = {(r, cols - 1) for r in range(rows)}  # east column leads to the hospital

    records = []
    for i, (u, v) in enumerate(sorted(g.edges())):
        (lat1, lon1), (lat2, lon2) = node_pos(u), node_pos(v)
        mean_col = (u[1] + v[1]) / 2
        bayside = 1 - mean_col / max(cols - 1, 1)  # 1 at bay, 0 inland

        elevation = round(float(np.clip(2.0 + 3.5 * (1 - bayside) + rng.normal(0, 0.4), 0.5, 7.0)), 2)
        tide = round(float(np.clip(0.65 * bayside + rng.normal(0, 0.08), 0, 1)), 2)
        groundwater = round(float(np.clip(0.8 + 0.6 * elevation + rng.normal(0, 0.3), 0.2, 6.0)), 2)

        # Visible complaints mostly track traffic and surface wear, only weakly track flooding.
        reports = int(rng.poisson(1.5 + 3.0 * rng.random() + 1.0 * bayside))

        records.append({
            "segment_id": f"S{i:02d}",
            "u": f"{u[0]}-{u[1]}", "v": f"{v[0]}-{v[1]}",
            "lat1": lat1, "lon1": lon1, "lat2": lat2, "lon2": lon2,
            "elevation_ft": elevation,
            "tide_exposure": tide,
            "groundwater_ft_below": groundwater,
            "reports_311": reports,
            "evac_route": u in evac_nodes and v in evac_nodes,
            "hospital_access": u in hospital_nodes and v in hospital_nodes,
            "repair_cost": int(rng.integers(1, 4)),
        })

    df = pd.DataFrame.from_records(records, columns=SEGMENT_COLUMNS)
    return g, df


def adjacency_pairs(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Segments that share an intersection. These are the pairs whose repairs reinforce each other."""
    by_node: dict[str, list[str]] = {}
    for row in df.itertuples():
        by_node.setdefault(row.u, []).append(row.segment_id)
        by_node.setdefault(row.v, []).append(row.segment_id)
    pairs = set()
    for segs in by_node.values():
        for a in segs:
            for b in segs:
                if a < b:
                    pairs.add((a, b))
    return sorted(pairs)
