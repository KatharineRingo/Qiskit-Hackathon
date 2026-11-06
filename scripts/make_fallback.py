"""Precompute web/public/fallback.json: /scenario, /results and /solve for every preset budget.
The web app uses it silently when the solver API is unreachable or slow.   python scripts/make_fallback.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from solver.app import app  # noqa: E402

client = TestClient(app)
scenario = client.get("/scenario").json()
rng = scenario["budget_range"]
solves = {str(u): client.post("/solve", json={"budget_units": u}).json() for u in range(rng["min_units"], rng["max_units"] + 1)}
out = {"scenario": scenario, "results": client.get("/results").json(), "solves": solves}
dest = ROOT / "web" / "public" / "fallback.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out), encoding="utf-8")
print(f"Wrote {dest} ({dest.stat().st_size // 1024} KB, {len(solves)} budgets)")
