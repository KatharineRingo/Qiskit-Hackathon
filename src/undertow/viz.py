"""Folium map for residents and city staff: hidden damage risk, recommended repairs, today's approach.

Reusable pieces for other front ends: build_map(), headline_text(), segment_explanation().
All wording lives in undertow.copy.
"""

from __future__ import annotations

import html

import folium
import pandas as pd
from branca.element import Element

from . import copy as C


def pick_plans(plans: dict[str, set[str]]) -> tuple[str | None, str | None]:
    """(recommended_name, today_name). Today's approach = the plan named like the current policy;
    recommended = the first other plan in the dict (run_demo puts the best optimizer first)."""
    today = next((n for n in plans if n.startswith(C.BASELINE_PREFIX)), None)
    rec = next((n for n in plans if n != today), None)
    return rec, today


def headline_text(scores: dict[str, dict] | None, plans: dict[str, set[str]]) -> str:
    """One-line headline computed from score_plan() output, keyed by plan name."""
    rec, today = pick_plans(plans)
    key = "evac_route_open_%"
    get = lambda n: (scores or {}).get(n, {}).get(key) if n else None  # noqa: E731
    return C.headline(get(rec), get(today))


def segment_explanation(row) -> str:
    """One plain sentence on why a segment is (or isn't) at risk, built from its data."""
    if hasattr(row, "_asdict"):
        row = row._asdict()
    reasons = []
    if row["elevation_ft"] <= C.LOW_ELEVATION_FT:
        reasons.append(C.WHY_LOW)
    if row["tide_exposure"] >= C.HIGH_TIDE_EXPOSURE:
        reasons.append(C.WHY_TIDE)
    if row["groundwater_ft_below"] <= C.SHALLOW_WATER_FT:
        reasons.append(C.WHY_WATER)
    if not reasons:
        return (C.WHY_COMPLAINTS if row["reports_311"] >= C.MANY_COMPLAINTS else C.WHY_FALLBACK) + "."
    text = "; ".join(reasons)
    text = text[0].upper() + text[1:]
    if row["reports_311"] <= C.FEW_COMPLAINTS and row["risk"] >= C.RISK_LEVELS[1][0]:
        text += f"; {C.WHY_HIDDEN}"
    return text + "."


def _route_tag(row) -> str:
    tags = [t for t, on in ((C.ROUTE_EVAC, row.evac_route), (C.ROUTE_HOSPITAL, row.hospital_access)) if on]
    return " and ".join(tags) if tags else C.ROUTE_NONE


def _name(row) -> str:
    street = getattr(row, "street_name", None)
    if isinstance(street, str) and street.strip():
        return street.strip()
    return f"Segment {row.segment_id}"


def _popup(row, rec_set, today_set, has_today) -> str:
    level = C.risk_level(row.risk)
    lines = [
        f"<b>{html.escape(_name(row))}</b>",
        f"<span style='color:{C.risk_color(row.risk)};font-weight:600'>{level} {C.RISK_NAME.lower()}</span>",
        html.escape(segment_explanation(row)),
        html.escape(_route_tag(row)),
        f"{C.PLAN_RECOMMENDED}: " + (C.REPAIRED_YES if row.segment_id in rec_set else C.REPAIRED_NO),
    ]
    if has_today:
        lines.append(f"{C.PLAN_TODAY}: " + (C.REPAIRED_YES if row.segment_id in today_set else C.REPAIRED_NO))
    return "<div style='font:14px/1.4 system-ui,sans-serif;min-width:200px'>" + "<br>".join(lines) + "</div>"


_CSS = """
<style>
.ut-panel{position:absolute;z-index:9999;background:rgba(255,255,255,.96);border-radius:10px;
 box-shadow:0 1px 6px rgba(0,0,0,.3);font:14px/1.4 system-ui,sans-serif;color:#1c1c1c;padding:10px 14px}
.ut-title{top:10px;left:56px;max-width:min(520px,calc(100vw - 80px));font-size:16px;font-weight:600}
.ut-legend{bottom:24px;left:10px;max-width:260px;font-size:13px}
.ut-row{display:flex;align-items:center;gap:8px;margin:3px 0}
.ut-demo{display:block;margin-top:6px;padding:3px 8px;background:#fff3cd;border-radius:6px;font-size:12px;font-weight:400}
.ut-legend summary{cursor:pointer;font-weight:600;font-size:13px}
.ut-sw{display:inline-block;width:26px;height:0;border-top-width:5px;border-top-style:solid}
.ut-halo{display:inline-block;width:26px;height:12px;border-radius:6px;opacity:.5}
@media (max-width:600px){
 .ut-title{left:10px;top:52px;font-size:14px;max-width:calc(100vw - 20px)}
 .ut-legend{font-size:12px;max-width:170px;padding:6px 8px;bottom:50px}
}
</style>
"""


def _legend_html(has_today: bool) -> str:
    rows = "".join(
        f"<div class='ut-row'><span class='ut-sw' style='border-top-color:{color}'></span>{label}"
        f" {C.RISK_NAME.lower()}</div>" for _, label, color in reversed(C.RISK_LEVELS))
    rows += (f"<div class='ut-row'><span class='ut-halo' style='background:{C.COLOR_RECOMMENDED}'></span>"
             f"{C.LAYER_RECOMMENDED}</div>")
    if has_today:
        rows += (f"<div class='ut-row'><span class='ut-halo' style='background:{C.COLOR_TODAY}'></span>"
                 f"{C.LAYER_TODAY}</div>")
    rows += (f"<div class='ut-row'><span class='ut-sw' style='border-top-style:dashed;"
             f"border-top-color:{C.COLOR_ROUTE_EVAC}'></span>{C.ROUTE_EVAC}</div>"
             f"<div class='ut-row'><span class='ut-sw' style='border-top-style:dotted;"
             f"border-top-color:{C.COLOR_ROUTE_HOSPITAL}'></span>{C.ROUTE_HOSPITAL}</div>")
    return (f"<details id='ut-key' class='ut-panel ut-legend' open><summary>Map key</summary>{rows}</details>"
            "<script>if(window.innerWidth<600){document.getElementById('ut-key').removeAttribute('open')}</script>")


def build_map(df: pd.DataFrame, plans: dict[str, set[str]], scores: dict[str, dict] | None = None,
              demo_data: bool = False) -> folium.Map:
    """plans: {plan name: set of repaired segment_ids}. scores: {plan name: score_plan() dict} for the headline.
    Optional df column `street_name` is used in popups when present."""
    center = [df[["lat1", "lat2"]].values.mean(), df[["lon1", "lon2"]].values.mean()]
    # OpenStreetMap tiles need no API key (CartoDB tiles now stamp "API KEY REQUIRED" on the map).
    m = folium.Map(location=center, zoom_start=15, tiles="OpenStreetMap", zoom_control="bottomright")
    m.fit_bounds([[df[["lat1", "lat2"]].values.min(), df[["lon1", "lon2"]].values.min()],
                  [df[["lat1", "lat2"]].values.max(), df[["lon1", "lon2"]].values.max()]], padding=(60, 60))

    rec_name, today_name = pick_plans(plans)
    rec_set = set(plans.get(rec_name, ())) if rec_name else set()
    today_set = set(plans.get(today_name, ())) if today_name else set()
    has_today = today_name is not None

    def line(row):
        return [(row.lat1, row.lon1), (row.lat2, row.lon2)]

    # Repair halos go underneath the risk lines so colors stay readable.
    if rec_name:
        g = folium.FeatureGroup(name=C.LAYER_RECOMMENDED, show=True)
        for row in df[df["segment_id"].isin(rec_set)].itertuples():
            folium.PolyLine(line(row), color=C.COLOR_RECOMMENDED, weight=18, opacity=0.4).add_to(g)
        g.add_to(m)
    if has_today:
        g = folium.FeatureGroup(name=C.LAYER_TODAY, show=False)
        for row in df[df["segment_id"].isin(today_set)].itertuples():
            folium.PolyLine(line(row), color=C.COLOR_TODAY, weight=18, opacity=0.4).add_to(g)
        g.add_to(m)

    base = folium.FeatureGroup(name=C.LAYER_RISK, show=True)
    for row in df.itertuples():
        folium.PolyLine(line(row), color=C.risk_color(row.risk), weight=6, opacity=0.9,
                        tooltip=f"{_name(row)}: {C.risk_level(row.risk)} {C.RISK_NAME.lower()}",
                        popup=folium.Popup(_popup(row, rec_set, today_set, has_today), max_width=280)).add_to(base)
    base.add_to(m)

    routes = folium.FeatureGroup(name=C.LAYER_ROUTES, show=True)
    for row in df.itertuples():
        if row.evac_route:
            folium.PolyLine(line(row), color=C.COLOR_ROUTE_EVAC, weight=2.5, dash_array="8 8", opacity=1,
                            interactive=False).add_to(routes)
        if row.hospital_access:
            folium.PolyLine(line(row), color=C.COLOR_ROUTE_HOSPITAL, weight=3, dash_array="2 7", opacity=1,
                            interactive=False).add_to(routes)
    routes.add_to(m)

    folium.LayerControl(collapsed=True, position="topright").add_to(m)

    head = html.escape(headline_text(scores, plans))
    demo = f"<span class='ut-demo'>{html.escape(C.DEMO_DATA_NOTE)}</span>" if demo_data else ""
    panels = _CSS + f"<div class='ut-panel ut-title'>{head}{demo}</div>" + _legend_html(has_today)
    m.get_root().html.add_child(Element(panels))
    return m
