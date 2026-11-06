import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from undertow.data_synthetic import SEGMENT_COLUMNS, adjacency_pairs, make_grid_network  # noqa: E402
from undertow.qubo import build_program, plan_value  # noqa: E402
from undertow.risk import add_scores  # noqa: E402
from undertow.solve import solve_current_policy, solve_exact, solve_qaoa  # noqa: E402


def _setup(k=6, budget=5):
    _, df = make_grid_network()
    df = add_scores(df)
    pairs_all = adjacency_pairs(df)
    cand = df.sort_values("value", ascending=False).head(k)
    ids = set(cand.segment_id)
    pairs = [(a, b) for a, b in pairs_all if a in ids and b in ids]
    return df, cand, pairs, build_program(cand, pairs, budget)


def test_schema():
    _, df = make_grid_network()
    assert list(df.columns) == SEGMENT_COLUMNS


def test_risk_in_range():
    df, *_ = _setup()
    assert df["risk"].between(0, 1).all()


def test_plans_respect_budget():
    df, cand, pairs, qp = _setup()
    for plan in (solve_exact(qp), solve_current_policy(df, 5)):
        assert df[df.segment_id.isin(plan.chosen)]["repair_cost"].sum() <= 5


def test_qaoa_feasible_and_close_to_optimal():
    df, cand, pairs, qp = _setup()
    exact = solve_exact(qp)
    q = solve_qaoa(qp, reps=2, maxiter=100)
    assert cand[cand.segment_id.isin(q.chosen)]["repair_cost"].sum() <= 5
    assert plan_value(cand, pairs, q.chosen) >= 0.85 * plan_value(cand, pairs, exact.chosen)
