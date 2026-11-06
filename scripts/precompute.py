"""Run the optimization ahead of time and write web/data.json for the front end.

    python scripts/precompute.py                 # uses data/segments.csv if present, else synthetic
    python scripts/precompute.py --data other.csv --candidates 10

Four preset budgets (Small / Medium / Large / Max) are set as shares of the total repair cost, so they
scale with whatever data is loaded. The Undertow plan comes from the LEAN QAOA formulation
(one qubit per segment, tuned price per cost unit) on the Aer simulator; if QAOA never samples a plan
that fits the budget, the exact classical plan is used and the budget entry says so.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

from qiskit.transpiler import generate_preset_pass_manager  # noqa: E402
from qiskit_aer import AerSimulator  # noqa: E402
from qiskit_aer.primitives import SamplerV2 as AerSampler  # noqa: E402
from qiskit_algorithms import QAOA  # noqa: E402
from qiskit_algorithms.optimizers import COBYLA  # noqa: E402
from qiskit_algorithms.utils import algorithm_globals  # noqa: E402
from qiskit_optimization.algorithms import MinimumEigenOptimizer  # noqa: E402

from undertow import copy as C  # noqa: E402
from undertow.data_synthetic import adjacency_pairs, make_grid_network  # noqa: E402
from undertow.metrics import REPAIRED_RISK, score_plan  # noqa: E402
from undertow.qubo import build_lean_program, build_program, plan_value, tune_price  # noqa: E402
from undertow.risk import add_scores  # noqa: E402
from undertow.solve import solve_current_policy, solve_exact  # noqa: E402
from undertow.viz import data_note, segment_explanation  # noqa: E402

BUDGET_PRESETS = [("small", "Small", 0.10), ("medium", "Medium", 0.20), ("large", "Large", 0.30), ("max", "Max", 0.45)]
OUT = ROOT / "web" / "data.json"


def qaoa_lean_plan(cand: pd.DataFrame, pairs, budget: int, reps: int, seed: int = 42) -> tuple[set[str], str]:
    """Best feasible plan among the QAOA samples of the lean formulation."""
    price = tune_price(cand, pairs, budget)
    lean = build_lean_program(cand, pairs, price)
    algorithm_globals.random_seed = seed
    backend = AerSimulator(seed_simulator=seed)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    qaoa = QAOA(sampler=AerSampler(seed=seed), optimizer=COBYLA(maxiter=150), reps=reps, transpiler=pm)
    res = MinimumEigenOptimizer(qaoa).solve(lean)
    cost = cand.set_index("segment_id")["repair_cost"].to_dict()
    names = [v.name for v in lean.variables]
    best, best_v = None, -1.0
    for s in res.samples:
        chosen = {n for n, x in zip(names, s.x) if round(x) == 1}
        if chosen and sum(cost[c] for c in chosen) <= budget:
            v = plan_value(cand, pairs, chosen)
            if v > best_v:
                best, best_v = chosen, v
    if best is None:
        exact = solve_exact(build_program(cand, pairs, budget))
        return exact.chosen, "fallback_exact"
    return best, "qaoa"


def street_names(df: pd.DataFrame) -> dict[str, str]:
    """Readable names: the street from the data, with 'block n' when a street has several segments."""
    street = df["street_name"] if "street_name" in df else pd.Series(["Unnamed road"] * len(df), index=df.index)
    street = street.fillna("Unnamed road").replace("", "Unnamed road")
    names, seen = {}, {}
    totals = street.value_counts().to_dict()
    for sid, st in zip(df["segment_id"], street):
        seen[st] = seen.get(st, 0) + 1
        names[sid] = f"{st}, block {seen[st]}" if totals[st] > 1 else st
    return names


def metrics(df, pairs_all, chosen: set[str], budget: int) -> dict:
    s = score_plan(df, pairs_all, chosen)
    sel = df[df["segment_id"].isin(chosen)]
    return {
        "evac_open_pct": s["evac_route_open_%"],
        "hospital_open_pct": s["hospital_access_open_%"],
        "failures_avoided": round(float((sel["risk"] - REPAIRED_RISK).clip(lower=0).sum()), 2),
        "budget_used": int(s["cost_used"]),
        "budget": int(budget),
        "roads_repaired": int(s["segments_repaired"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="segments CSV (default: data/segments.csv, else synthetic)")
    ap.add_argument("--candidates", type=int, default=10, help="roads sent to the optimizer (= qubits in the lean form)")
    ap.add_argument("--reps", type=int, default=2)
    args = ap.parse_args()

    csv = Path(args.data) if args.data else ROOT / "data" / "segments.csv"
    synthetic = not csv.exists()
    df = make_grid_network()[1] if synthetic else pd.read_csv(csv)
    df = add_scores(df).reset_index(drop=True)
    pairs_all = adjacency_pairs(df)
    cand = df.sort_values("value", ascending=False).head(args.candidates)
    ids = set(cand["segment_id"])
    pairs = [(a, b) for a, b in pairs_all if a in ids and b in ids]

    index = {sid: i for i, sid in enumerate(df["segment_id"])}  # internal numbers; ids never shown
    names = street_names(df)
    segments = []
    for r in df.itertuples():
        segments.append({
            "name": names[r.segment_id],
            "path": [[r.lon1, r.lat1], [r.lon2, r.lat2]],
            "risk": float(r.risk),
            "risk_word": C.risk_level(r.risk),
            "reason": segment_explanation(r),
            "evac": bool(r.evac_route),
            "hospital": bool(r.hospital_access),
        })

    total_cost = int(df["repair_cost"].sum())
    budgets = []
    for key, label, share in BUDGET_PRESETS:
        budget = max(int(df["repair_cost"].min()), round(total_cost * share))
        print(f"{label}: budget {budget} ...", flush=True)
        today = solve_current_policy(df, budget).chosen
        plan, how = qaoa_lean_plan(cand, pairs, budget, args.reps)
        budgets.append({
            "key": key, "label": label, "budget": budget, "optimizer": how,
            "plans": {
                "undertow": {"repairs": sorted(index[s] for s in plan), "metrics": metrics(df, pairs_all, plan, budget)},
                "today": {"repairs": sorted(index[s] for s in today), "metrics": metrics(df, pairs_all, today, budget)},
            },
        })

    note = data_note(df, synthetic)
    data = {
        "synthetic": synthetic,
        "data_note": note,
        "budget_unit": C.BUDGET_UNIT,
        "route_labels": C.ROUTE_METRICS,
        "center": [float(df[["lon1", "lon2"]].values.mean()), float(df[["lat1", "lat2"]].values.mean())],
        "bounds": [[float(df[["lon1", "lon2"]].values.min()), float(df[["lat1", "lat2"]].values.min())],
                   [float(df[["lon1", "lon2"]].values.max()), float(df[["lat1", "lat2"]].values.max())]],
        "segments": segments,
        "budgets": budgets,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"Wrote {OUT} ({len(segments)} roads, {len(budgets)} budgets)")


if __name__ == "__main__":
    main()
