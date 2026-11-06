"""Snap each segment onto the real geometry of the street it is supposed to be on (OpenStreetMap via Overpass).

For every segment we take the named street from OSM (e.g. "W 40th St" -> "West 40th Street"), snap both approximate
endpoints to vertices of that street, and follow the street between them. Intersections are matched across streets
(OSM streets share a node where they cross) so neighboring segments meet cleanly.

Writes data/segments_geometry.json ({segment_id: [[lon, lat], ...]}) and data/snap_report.csv.
Only geometry changes; every attribute in data/segments.csv stays as the researcher provided it.
Only a bounding box is sent to the public Overpass API.

    python scripts/snap_to_roads.py
"""

from __future__ import annotations

import itertools
import json
import math
import re
from pathlib import Path

import networkx as nx
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
OVERPASS = "https://overpass-api.de/api/interpreter"
CACHE = ROOT / "data" / "raw" / "osm_ways.json"
PAD = 0.004               # degrees around the data
MAX_ENDPOINT_M = 260      # an endpoint farther than this from its street is not trusted
MAX_DETOUR = 2.0          # along-street length vs straight line
MIN_RATIO = 0.75          # shorter than this means an endpoint snapped to the wrong spot (a stub)


def hav(a, b) -> float:
    (lo1, la1), (lo2, la2) = a, b
    p = math.pi / 180
    h = math.sin((la2 - la1) * p / 2) ** 2 + math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2
    return 12742000 * math.asin(math.sqrt(h))


ABBR = {"w": "west", "e": "east", "n": "north", "s": "south", "st": "street", "rd": "road", "ave": "avenue", "dr": "drive", "blvd": "boulevard"}


def norm(name: str) -> str:
    return " ".join(ABBR.get(t, t) for t in re.sub(r"[^a-z0-9 ]", " ", str(name).lower()).split())


def fetch_ways(df: pd.DataFrame) -> list[dict]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))["elements"]
    lats = df[["lat1", "lat2"]].values.ravel(); lons = df[["lon1", "lon2"]].values.ravel()
    bbox = f"{lats.min() - PAD},{lons.min() - PAD},{lats.max() + PAD},{lons.max() + PAD}"
    q = f'[out:json][timeout:90];way["highway"]["name"]({bbox});out geom;'
    r = requests.post(OVERPASS, data={"data": q}, headers={"User-Agent": "undertow-hackathon-snap/0.2"}, timeout=120)
    r.raise_for_status()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(r.text, encoding="utf-8")
    return r.json()["elements"]


def street_graphs(ways: list[dict]) -> dict[str, nx.Graph]:
    graphs: dict[str, nx.Graph] = {}
    for w in ways:
        g = graphs.setdefault(norm(w["tags"]["name"]), nx.Graph())
        pts = [(p["lon"], p["lat"]) for p in w["geometry"]]
        for nid, pt in zip(w["nodes"], pts):
            g.add_node(nid, pt=pt)
        for (n1, p1), (n2, p2) in zip(zip(w["nodes"], pts), zip(w["nodes"][1:], pts[1:])):
            g.add_edge(n1, n2, length=hav(p1, p2))
    return graphs


def find_graph(graphs: dict[str, nx.Graph], street: str) -> tuple[str, nx.Graph] | None:
    key = norm(street)
    if key in graphs:
        return key, graphs[key]
    bare = re.sub(r"^(west|east|north|south) ", "", key)
    for k in graphs:
        if k == bare or re.sub(r"^(west|east|north|south) ", "", k) == bare:
            return k, graphs[k]
    return None


def near(g: nx.Graph, pt, k: int = 12) -> list[tuple[float, int]]:
    ds = sorted((hav(pt, d["pt"]), n) for n, d in g.nodes(data=True))
    return ds[:k]


def main() -> None:
    df = pd.read_csv(ROOT / "data" / "segments.csv")
    graphs = street_graphs(fetch_ways(df))

    segs = {r.segment_id: r for r in df.itertuples()}
    approx: dict[str, tuple[float, float]] = {}
    incident: dict[str, list[str]] = {}
    for r in df.itertuples():
        approx[r.u], approx[r.v] = (r.lon1, r.lat1), (r.lon2, r.lat2)
        incident.setdefault(r.u, []).append(r.segment_id)
        incident.setdefault(r.v, []).append(r.segment_id)

    graph_of = {}
    for sid, r in segs.items():
        found = find_graph(graphs, r.street_name)
        graph_of[sid] = found

    # choose, for every intersection, one vertex per incident street so crossing streets meet at the same OSM node
    vertex: dict[tuple[str, str], int] = {}      # (node, street key) -> OSM node id
    for node, sids in incident.items():
        keys = sorted({graph_of[s][0] for s in sids if graph_of[s]})
        if not keys:
            continue
        cands = {k: near(graphs[k], approx[node]) for k in keys}
        best, best_cost = None, 1e18
        for combo in itertools.product(*[cands[k] for k in keys]):
            pts = [graphs[k].nodes[n]["pt"] for k, (_, n) in zip(keys, combo)]
            cost = sum(d for d, _ in combo) + 4 * sum(hav(a, b) for a, b in itertools.combinations(pts, 2))
            if cost < best_cost:
                best, best_cost = (keys, combo), cost
        for k, (_, n) in zip(*best):
            vertex[(node, k)] = n

    geom, rows = {}, []
    for sid, r in segs.items():
        a0, b0 = (r.lon1, r.lat1), (r.lon2, r.lat2)
        straight = hav(a0, b0)
        path, used, ratio, why = [list(a0), list(b0)], "straight", None, ""
        if graph_of[sid] is None:
            why = "street not found in OSM"
        else:
            key, g = graph_of[sid]
            na, nb = vertex[(r.u, key)], vertex[(r.v, key)]
            da, db = hav(a0, g.nodes[na]["pt"]), hav(b0, g.nodes[nb]["pt"])
            try:
                nodes = nx.shortest_path(g, na, nb, weight="length")
                pts = [g.nodes[n]["pt"] for n in nodes]
                length = sum(hav(p, q) for p, q in zip(pts, pts[1:]))
                ratio = length / max(straight, 1)
                if na != nb and max(da, db) <= MAX_ENDPOINT_M and MIN_RATIO <= ratio <= MAX_DETOUR:
                    path, used = [list(p) for p in pts], "street"
                else:
                    why = f"rejected (endpoint off by {max(da, db):.0f} m, path {ratio:.1f}x straight)"
            except nx.NetworkXNoPath:
                why = "no path along that street"
        geom[sid] = path
        rows.append({"segment_id": sid, "street_name": r.street_name, "osm_street": graph_of[sid][0] if graph_of[sid] else "",
                     "used": used, "along_street_vs_straight": None if ratio is None else round(ratio, 2), "note": why})

    # keep everything connected: an intersection used by a snapped segment keeps that exact position for its straight neighbors
    node_pos: dict[str, list[float]] = {}
    for sid, r in segs.items():
        if rows[list(segs).index(sid)]["used"] == "street":
            node_pos.setdefault(r.u, geom[sid][0])
            node_pos.setdefault(r.v, geom[sid][-1])
    for i, (sid, r) in enumerate(segs.items()):
        if rows[i]["used"] == "straight":
            geom[sid] = [node_pos.get(r.u, [r.lon1, r.lat1]), node_pos.get(r.v, [r.lon2, r.lat2])]

    (ROOT / "data" / "segments_geometry.json").write_text(json.dumps(geom), encoding="utf-8")
    rep = pd.DataFrame(rows)
    rep.to_csv(ROOT / "data" / "snap_report.csv", index=False)
    print(rep.to_string(index=False))
    print(f"\n{(rep.used == 'street').sum()} of {len(rep)} segments now follow their real street; the rest stay straight.")


if __name__ == "__main__":
    main()
