"""Folium map: segments colored by hidden risk, chosen repairs drawn thick, one layer per plan."""

from __future__ import annotations

import folium
import pandas as pd


def _risk_color(r: float) -> str:
    if r >= 0.7:
        return "#c0392b"
    if r >= 0.4:
        return "#e67e22"
    return "#27ae60"


def build_map(df: pd.DataFrame, plans: dict[str, set[str]]) -> folium.Map:
    center = [df[["lat1", "lat2"]].values.mean(), df[["lon1", "lon2"]].values.mean()]
    m = folium.Map(location=center, zoom_start=15, tiles="cartodbpositron")

    base = folium.FeatureGroup(name="Hidden-damage risk", show=True)
    for row in df.itertuples():
        tags = [t for t, on in (("evac route", row.evac_route), ("hospital access", row.hospital_access)) if on]
        tip = (f"<b>{row.segment_id}</b><br>risk {row.risk:.2f} | 311 reports {row.reports_311}"
               f"<br>elev {row.elevation_ft} ft | tide {row.tide_exposure:.2f} | cost {row.repair_cost}"
               + (f"<br>{', '.join(tags)}" if tags else ""))
        folium.PolyLine([(row.lat1, row.lon1), (row.lat2, row.lon2)], color=_risk_color(row.risk),
                        weight=6, opacity=0.85, tooltip=tip).add_to(base)
    base.add_to(m)

    palette = ["#2c3e50", "#8e44ad", "#2980b9", "#16a085"]
    for i, (name, chosen) in enumerate(plans.items()):
        layer = folium.FeatureGroup(name=f"Repairs: {name}", show=(i == 0))
        for row in df[df["segment_id"].isin(chosen)].itertuples():
            folium.PolyLine([(row.lat1, row.lon1), (row.lat2, row.lon2)], color=palette[i % len(palette)],
                            weight=14, opacity=0.45, tooltip=f"{name}: repair {row.segment_id}").add_to(layer)
        layer.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m
