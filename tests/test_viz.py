import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from undertow import copy as C  # noqa: E402
from undertow.data_synthetic import make_grid_network  # noqa: E402
from undertow.risk import add_scores  # noqa: E402
from undertow.viz import build_map, headline_text, pick_plans, segment_explanation  # noqa: E402

PLANS = {"QAOA simulator (reps=2)": {"S03", "S07"}, "Current policy (most 311 reports)": {"S12"}}
SCORES = {"QAOA simulator (reps=2)": {"evac_route_open_%": 79.1},
          "Current policy (most 311 reports)": {"evac_route_open_%": 44.7}}


def _df():
    return add_scores(make_grid_network()[1])


def test_risk_levels_use_plain_words():
    assert C.risk_level(0.9) == "High" and C.risk_level(0.5) == "Medium" and C.risk_level(0.1) == "Low"


def test_pick_plans():
    assert pick_plans(PLANS) == ("QAOA simulator (reps=2)", "Current policy (most 311 reports)")


def test_headline_is_computed_from_scores():
    h = headline_text(SCORES, PLANS)
    assert "79%" in h and "45%" in h and "today's approach" in h


def test_headline_without_scores_has_no_numbers():
    assert not any(ch.isdigit() for ch in headline_text(None, PLANS))


def test_explanation_is_one_plain_sentence_for_every_segment():
    for row in _df().itertuples():
        s = segment_explanation(row)
        assert s.endswith(".") and s.count(".") == 1
        assert not any(w in s.lower() for w in ("qaoa", "qubit", "objective"))


def test_explanation_flags_hidden_damage():
    row = _df().iloc[0].to_dict()
    row.update(elevation_ft=2.0, tide_exposure=0.6, groundwater_ft_below=2.0, reports_311=0, risk=0.9)
    s = segment_explanation(row)
    assert "king tides" in s and "underneath" in s


def test_build_map_html_has_plain_labels_and_no_jargon():
    html = build_map(_df(), PLANS, SCORES, demo_data=True).get_root().render()
    for expected in (C.LAYER_RECOMMENDED, C.LAYER_TODAY, "Demo data", "Evacuation route", "79%"):
        assert expected in html
    for jargon in ("QAOA", "qubit", "Hamiltonian"):
        assert jargon not in html


def test_build_map_no_demo_note_for_real_data_and_uses_street_name():
    df = _df()
    df["street_name"] = "Collins Ave"
    html = build_map(df, PLANS, SCORES, demo_data=False).get_root().render()
    assert "Demo data" not in html and "Collins Ave" in html
