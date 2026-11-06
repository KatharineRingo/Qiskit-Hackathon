"""The repair-planning problem as a quadratic binary program (becomes a QUBO for QAOA).

Decision: x_i = 1 if we repair segment i this cycle.

maximize   sum_i value_i * x_i                     (harm avoided by each repair)
         + sum_(i,j adjacent) synergy_ij * x_i x_j (repairs on connected segments reinforce each other)
subject to sum_i cost_i * x_i <= budget

The quadratic synergy term is the reason this is a natural fit for a QUBO:
fixing one block of an evacuation route is worth little if the next block still floods.
Qiskit's QuadraticProgramToQubo turns the budget constraint into a penalty with slack qubits.
"""

from __future__ import annotations

import pandas as pd
from qiskit_optimization import QuadraticProgram

SYNERGY_WEIGHT = 0.5  # how strongly connected repairs reinforce each other


def synergy(a: pd.Series, b: pd.Series) -> float:
    """Bonus for repairing two adjacent segments together.

    Bigger when both are risky and both sit on the same critical corridor.
    """
    shared_corridor = (a["evac_route"] and b["evac_route"]) or (a["hospital_access"] and b["hospital_access"])
    corridor_boost = 2.0 if shared_corridor else 0.5
    return round(SYNERGY_WEIGHT * corridor_boost * min(a["risk"], b["risk"]), 3)


def build_program(df: pd.DataFrame, pairs: list[tuple[str, str]], budget: int) -> QuadraticProgram:
    qp = QuadraticProgram("undertow_repair_plan")
    for sid in df["segment_id"]:
        qp.binary_var(name=sid)

    rows = df.set_index("segment_id")
    linear = rows["value"].to_dict()
    quadratic = {}
    for a, b in pairs:
        if a in rows.index and b in rows.index:
            s = synergy(rows.loc[a], rows.loc[b])
            if s > 0:
                quadratic[(a, b)] = s

    qp.maximize(linear=linear, quadratic=quadratic)
    qp.linear_constraint(linear=rows["repair_cost"].to_dict(), sense="<=", rhs=budget, name="budget")
    return qp


def shadow_price(df: pd.DataFrame, budget: int) -> float:
    """Price per cost unit for the lean formulation (classic knapsack Lagrangian heuristic).

    Rank segments by value per cost, fill the budget greedily, and use the value/cost ratio of the
    first segment that doesn't fit. Repairs worth less than this per unit get pushed out. O(n log n), scales fine.
    """
    spent = 0
    for row in df.assign(ratio=df["value"] / df["repair_cost"]).sort_values("ratio", ascending=False).itertuples():
        if spent + row.repair_cost > budget:
            return float(row.ratio)
        spent += row.repair_cost
    return 0.0


def tune_price(df: pd.DataFrame, pairs: list[tuple[str, str]], budget: int, iters: int = 30) -> float:
    """Smallest price per cost unit whose best lean plan fits the budget (bisection).

    Starts from the greedy shadow price; synergy bonuses usually push the real price higher.
    The inner "best lean plan" is brute force here (fine up to ~20 segments). At city scale you'd
    get it from QAOA samples or a local search instead; the bisection stays the same.
    """
    import itertools
    import numpy as np

    def best_plan_cost(price: float) -> int:
        qp = build_lean_program(df, pairs, price)
        cost = df.set_index("segment_id")["repair_cost"]
        names = [v.name for v in qp.variables]
        best = max(itertools.product([0, 1], repeat=len(names)), key=lambda b: qp.objective.evaluate(np.array(b)))
        return int(sum(cost[n] for n, b in zip(names, best) if b))

    lo, hi = shadow_price(df, budget), float((df["value"] / df["repair_cost"]).max()) + 1.0
    if best_plan_cost(lo) <= budget:
        return lo
    for _ in range(iters):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if best_plan_cost(mid) > budget else (lo, mid)
    return hi


def build_lean_program(df: pd.DataFrame, pairs: list[tuple[str, str]], price: float) -> QuadraticProgram:
    """One qubit per segment, no slack qubits: the budget becomes a price per cost unit.

    maximize sum_i (value_i - price * cost_i) x_i + sum synergy_ij x_i x_j
    Plans over budget are filtered out afterwards (post-selection).
    """
    qp = QuadraticProgram("undertow_lean")
    rows = df.set_index("segment_id")
    for sid in rows.index:
        qp.binary_var(name=sid)
    linear = {s: float(rows.loc[s, "value"] - price * rows.loc[s, "repair_cost"]) for s in rows.index}
    quadratic = {(a, b): synergy(rows.loc[a], rows.loc[b]) for a, b in pairs if a in rows.index and b in rows.index}
    qp.maximize(linear=linear, quadratic=quadratic)
    return qp


def plan_value(df: pd.DataFrame, pairs: list[tuple[str, str]], chosen: set[str]) -> float:
    """Objective value of any plan, so baseline and quantum plans are scored the same way."""
    rows = df.set_index("segment_id")
    total = float(rows.loc[list(chosen), "value"].sum()) if chosen else 0.0
    for a, b in pairs:
        if a in chosen and b in chosen:
            total += synergy(rows.loc[a], rows.loc[b])
    return round(total, 3)
