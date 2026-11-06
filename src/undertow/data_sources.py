"""Real-data loaders. Goal: produce a DataFrame with the same columns as data_synthetic.SEGMENT_COLUMNS,
save it to data/segments.csv, then run:  python run_demo.py --data data/segments.csv

These were written without network access, so treat each one as a 90%-there starting point.
If one fights you for more than an hour, keep the synthetic column and move on.

Sources
- Road network: OpenStreetMap via OSMnx.
- Tides: NOAA CO-OPS API, Virginia Key station 8723214 (Biscayne Bay).
    Docs: https://api.tidesandcurrents.noaa.gov/api/prod/
- Elevation: USGS Elevation Point Query Service (EPQS).
- Pothole history: Miami-Dade 311 Service Requests. Download a year's CSV from the
    Miami-Dade Open Data Hub (opendata.miamidade.gov / gis-mdc.opendata.arcgis.com, search "311 Service Requests")
    and filter to pothole issue types.
- Groundwater: USGS groundwater levels (waterdata.usgs.gov) for monitoring wells near the area,
    or a constant per-neighborhood estimate if time is short.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import requests

DATA = Path(__file__).resolve().parents[2] / "data"

VIRGINIA_KEY = "8723214"
NOAA_API = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
EPQS_API = "https://epqs.nationalmap.gov/v1/json"

# Pick ONE neighborhood. Miami Beach (west side, along the bay) is the classic sunny-day flooding area.
DEFAULT_PLACE = "Miami Beach, Florida, USA"


# --------------------------------------------------------------------------- roads
def load_road_segments(place: str = DEFAULT_PLACE, max_segments: int = 60) -> pd.DataFrame:
    """Drivable road segments as rows with endpoints and coordinates.

    pip install osmnx. To keep the area small, swap graph_from_place for
    ox.graph_from_point((lat, lon), dist=800, network_type="drive").
    """
    import osmnx as ox

    g = ox.graph_from_place(place, network_type="drive")
    g = ox.convert.to_undirected(g)
    nodes, edges = ox.graph_to_gdfs(g)
    edges = edges.reset_index()

    rows = []
    for i, e in enumerate(edges.head(max_segments).itertuples()):
        a, b = nodes.loc[e.u], nodes.loc[e.v]
        rows.append({
            "segment_id": f"S{i:03d}", "u": str(e.u), "v": str(e.v),
            "lat1": a.y, "lon1": a.x, "lat2": b.y, "lon2": b.x,
            "road_name": e.name if isinstance(e.name, str) else "",
            "highway": e.highway if isinstance(e.highway, str) else str(e.highway),
            "length_m": float(e.length),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- tides
def load_tides(begin: str = "20250101", end: str = "20251231", station: str = VIRGINIA_KEY) -> pd.DataFrame:
    """Daily max water level (ft above MHHW) from NOAA. The API caps hourly requests at 1 year."""
    params = {
        "product": "hourly_height", "station": station, "begin_date": begin, "end_date": end,
        "datum": "MHHW", "units": "english", "time_zone": "lst_ldt", "format": "json",
        "application": "undertow_hackathon",
    }
    r = requests.get(NOAA_API, params=params, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json()["data"])
    df["t"] = pd.to_datetime(df["t"])
    df["v"] = pd.to_numeric(df["v"], errors="coerce")
    return df.set_index("t")["v"].resample("D").max().rename("max_ft_above_mhhw").to_frame()


def tide_exposure(elevation_ft: pd.Series, daily_max: pd.Series, mhhw_ft_navd88: float = 0.0) -> pd.Series:
    """Share of days the tide reached within 1 ft of the road surface.

    Elevation from EPQS is NAVD88; tides above are relative to MHHW. Look up the MHHW-to-NAVD88
    offset on the station's Datums page and pass it as mhhw_ft_navd88, otherwise this is only relative.
    """
    water = daily_max.values + mhhw_ft_navd88
    return elevation_ft.apply(lambda z: float(np.mean(water >= z - 1.0))).round(3)


# --------------------------------------------------------------------------- elevation
def elevation_ft(lat: float, lon: float) -> float:
    r = requests.get(EPQS_API, params={"x": lon, "y": lat, "units": "Feet", "wkid": 4326}, timeout=30)
    r.raise_for_status()
    return float(r.json()["value"])


def add_elevation(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mids = zip((out.lat1 + out.lat2) / 2, (out.lon1 + out.lon2) / 2)
    out["elevation_ft"] = [round(elevation_ft(la, lo), 2) for la, lo in mids]  # cache this to CSV, it's slow
    return out


# --------------------------------------------------------------------------- 311
def load_311_potholes(csv_path: str | Path) -> pd.DataFrame:
    """Read a downloaded Miami-Dade 311 CSV and keep pothole requests.

    Column names vary by year. Print df.columns once and fix the three names below.
    """
    df = pd.read_csv(csv_path, low_memory=False)
    type_col = next(c for c in df.columns if "type" in c.lower() and "issue" in c.lower()) \
        if any("issue" in c.lower() for c in df.columns) else "Issue Type"
    pothole = df[df[type_col].astype(str).str.contains("pothole", case=False, na=False)]
    lat_col = next(c for c in df.columns if c.lower() in ("latitude", "lat", "y"))
    lon_col = next(c for c in df.columns if c.lower() in ("longitude", "lon", "long", "x"))
    return pothole.rename(columns={lat_col: "lat", lon_col: "lon"})[["lat", "lon"]].dropna()


def count_reports_near(segments: pd.DataFrame, reports: pd.DataFrame, radius_m: float = 60) -> pd.Series:
    """Number of 311 pothole reports within radius_m of each segment midpoint (fast approximation)."""
    mlat = ((segments.lat1 + segments.lat2) / 2).values[:, None]
    mlon = ((segments.lon1 + segments.lon2) / 2).values[:, None]
    dy = (reports.lat.values[None, :] - mlat) * 111_000
    dx = (reports.lon.values[None, :] - mlon) * 111_000 * np.cos(np.radians(25.8))
    return pd.Series((np.hypot(dx, dy) <= radius_m).sum(axis=1), index=segments.index)


# --------------------------------------------------------------------------- assemble
def build_segments(place: str = DEFAULT_PLACE, csv_311: str | Path | None = None,
                   evac_road_names: tuple[str, ...] = ("Alton Rd", "5th St"),
                   hospital_road_names: tuple[str, ...] = ("Alton Rd",)) -> pd.DataFrame:
    """Glue everything into the SEGMENT_COLUMNS schema and save data/segments.csv.

    evac/hospital road names are placeholders: replace them with the real evacuation
    routes from Miami-Dade's evacuation maps and the actual roads into the nearest hospital.
    """
    seg = add_elevation(load_road_segments(place))
    tides = load_tides()
    seg["tide_exposure"] = tide_exposure(seg["elevation_ft"], tides["max_ft_above_mhhw"])
    seg["groundwater_ft_below"] = (seg["elevation_ft"] * 0.6 + 0.5).round(2)  # TODO: replace with USGS wells
    seg["reports_311"] = count_reports_near(seg, load_311_potholes(csv_311)) if csv_311 else 0
    seg["evac_route"] = seg["road_name"].isin(evac_road_names)
    seg["hospital_access"] = seg["road_name"].isin(hospital_road_names)
    # Cost: full-depth repair scales with length. 1 unit ~ 100 m, capped at 3.
    seg["repair_cost"] = np.clip(np.ceil(seg["length_m"] / 100), 1, 3).astype(int)

    DATA.mkdir(exist_ok=True)
    seg.to_csv(DATA / "segments.csv", index=False)
    return seg


if __name__ == "__main__":
    import sys
    print(build_segments(csv_311=sys.argv[1] if len(sys.argv) > 1 else None).head())
