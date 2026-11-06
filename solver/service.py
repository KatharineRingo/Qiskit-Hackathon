"""Live solve: lean formulation -> QAOA on Qiskit Aer (train with EstimatorV2, sample with SamplerV2),
plus the exact classical plan and today's approach, scored the same way."""

from __future__ import annotations

import json
import time
import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from . import scenario as S

warnings.filterwarnings("ignore")

from qiskit.circuit.library import QAOAAnsatz  # noqa: E402
from qiskit.transpiler import generate_preset_pass_manager  # noqa: E402
from qiskit_aer import AerSimulator  # noqa: E402
from qiskit_aer.primitives import EstimatorV2, SamplerV2  # noqa: E402
from qiskit_optimization.translators import to_ising  # noqa: E402

from undertow.data_synthetic import adjacency_pairs  # noqa: E402
from undertow.metrics import REPAIRED_RISK, score_plan  # noqa: E402
from undertow.qubo import build_lean_program, build_program, plan_value, tune_price  # noqa: E402
from undertow.solve import solve_current_policy, solve_exact  # noqa: E402

SEED, REPS, SHOTS = 7, 2, 2000
ANGLES = Path(__file__).with_name("angles.json")   # saved QAOA angles per budget: warm start so a solve takes ~1-3 s


def _load_angles() -> dict:
    return json.loads(ANGLES.read_text()) if ANGLES.exists() else {}


def _metrics(df, pairs_all, chosen: set[str]) -> dict:
    s = score_plan(df, pairs_all, chosen)
    sel = df[df["segment_id"].isin(chosen)]
    return {"evac_open_pct": s["evac_route_open_%"], "hospital_open_pct": s["hospital_access_open_%"],
            "failures_avoided": round(float((sel["risk"] - REPAIRED_RISK).clip(lower=0).sum()), 2),
            "expected_failures": s["expected_failures_left"], "crew_days": int(s["cost_used"])}


def _train(op, circ, estimator, starts: int = 2, maxiter: int = 120) -> list[float]:
    best = None
    for start in range(starts):
        x0 = np.random.default_rng(start).uniform(0, np.pi, circ.num_parameters)
        res = minimize(lambda th: float(estimator.run([(circ, op, th)]).result()[0].data.evs), x0,
                       method="COBYLA", options={"maxiter": maxiter})
        if best is None or res.fun < best.fun:
            best = res
    return [float(v) for v in best.x]


@lru_cache(maxsize=64)
def solve(budget: int) -> dict:
    t0 = time.perf_counter()
    df = S.load_df()
    pairs_all = adjacency_pairs(df)
    ids = S.candidate_ids(df)
    cand = df[df["segment_id"].isin(ids)]
    cids = set(ids)
    pairs = [(a, b) for a, b in pairs_all if a in cids and b in cids]
    cost = cand.set_index("segment_id")["repair_cost"].to_dict()

    saved = _load_angles().get(str(budget)) or {}
    price = saved.get("price")
    if price is None:  # brute-force bisection: slow, so it is saved with the angles
        price = tune_price(cand, pairs, budget)
    lean = build_lean_program(cand, pairs, price)
    names = [v.name for v in lean.variables]
    cost_op, _ = to_ising(lean)
    n = cost_op.num_qubits

    backend = AerSimulator(seed_simulator=SEED)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    ansatz = QAOAAnsatz(cost_op, reps=REPS)
    circ = pm.run(ansatz)
    if saved.get("theta") and len(saved["theta"]) == circ.num_parameters:
        theta = saved["theta"]
    else:
        theta = _train(cost_op, circ, EstimatorV2(options={"run_options": {"seed": SEED}}))

    meas = pm.run(ansatz.measure_all(inplace=False)).assign_parameters(theta)
    counts = SamplerV2(seed=SEED).run([meas], shots=SHOTS).result()[0].data.meas.get_counts()

    def decode(bs: str) -> set[str]:   # Qiskit bitstrings are little-endian
        return {nm for nm, b in zip(names, bs[::-1]) if b == "1"}

    def fits(ch: set[str]) -> bool:
        return bool(ch) and sum(cost[x] for x in ch) <= budget

    feasible = [decode(bs) for bs in counts if fits(decode(bs))]
    chosen = max(feasible, key=lambda ch: plan_value(cand, pairs, ch)) if feasible else set()

    exact = solve_exact(build_program(cand, pairs, budget)).chosen
    today = solve_current_policy(df, budget).chosen
    match = bool(chosen) and abs(plan_value(cand, pairs, chosen) - plan_value(cand, pairs, exact)) < 1e-6

    state = [0] * (2 ** n)
    for bs, c in counts.items():
        state[int(bs, 2)] = c
    best_state = int("".join("1" if nm in chosen else "0" for nm in reversed(names)), 2)
    top = sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    um, tm = _metrics(df, pairs_all, chosen), _metrics(df, pairs_all, today)
    key = max(("evac_open_pct", "hospital_open_pct"), key=lambda k: um[k] - tm[k])
    label = {"evac_open_pct": "Evacuation route open", "hospital_open_pct": "Route to the hospital open"}[key]
    return {
        "budget_units": budget,
        "plans": {"undertow": {"segments": sorted(chosen), "metrics": um}, "today": {"segments": sorted(today), "metrics": tm}},
        "headline": {"key": key, "label": label, "undertow": um[key], "today": tm[key]},
        "candidates": names, "counts": state, "best_state": best_state,
        "top_samples": [{"bits": bs, "count": c, "feasible": fits(decode(bs))} for bs, c in top],
        "num_qubits": n, "shots": SHOTS, "classical_match": bool(match),
        "solve_ms": int((time.perf_counter() - t0) * 1000), "theta": [round(float(v), 6) for v in theta], "price": float(price),
    }


def warm_angles() -> None:
    """Train once per preset budget and save the angles (run via scripts/make_fallback.py)."""
    out = _load_angles()
    for b in S.budgets(S.load_df()):
        solve.cache_clear()
        r = solve(b["units"])
        out[str(b["units"])] = {"theta": r["theta"], "price": r["price"]}
        ANGLES.write_text(json.dumps(out))
    solve.cache_clear()
