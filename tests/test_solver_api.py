import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from solver.app import app  # noqa: E402

client = TestClient(app)


def test_scenario_has_real_streets_and_layers():
    s = client.get("/scenario").json()
    assert s["segments"]["features"] and s["hospital"]["name"] and len(s["tide"]) == 12
    names = {f["properties"]["street"] for f in s["segments"]["features"]}
    assert not any(n.startswith("S0") for n in names)
    assert len(s["budgets"]) == 4 and s["optimizer"]["num_qubits"] == 8


def test_solve_returns_feasible_plan_matching_classical():
    s = client.get("/scenario").json()
    for b in s["budgets"][:2]:
        r = client.post("/solve", json={"budget_units": b["units"]}).json()
        assert 0 < r["plans"]["undertow"]["metrics"]["crew_days"] <= b["units"]
        assert r["classical_match"] is True
        assert len(r["counts"]) == 2 ** r["num_qubits"] and sum(r["counts"]) == r["shots"]


def test_solve_rejects_absurd_budget():
    assert client.post("/solve", json={"budget_units": 10_000}).status_code == 422
