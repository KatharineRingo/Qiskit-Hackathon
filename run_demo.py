"""End-to-end demo: data -> hidden-damage risk -> shortlist -> QUBO -> QAOA vs classical vs current policy -> map.

    python run_demo.py                      # synthetic data, local simulator
    python run_demo.py --candidates 8 --budget 6
    python run_demo.py --data data/segments.csv   # real data, same columns as data_synthetic.SEGMENT_COLUMNS
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / "src"))

from undertow.data_synthetic import adjacency_pairs, make_grid_network  # noqa: E402
from undertow.metrics import score_plan  # noqa: E402
from undertow.qubo import build_program  # noqa: E402
from undertow.risk import add_scores  # noqa: E402
from undertow.solve import num_qubits, solve_current_policy, solve_exact, solve_qaoa  # noqa: E402
from undertow.viz import build_map  # noqa: E402

OUT = Path(__file__).parent / "results"


def shortlist(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Hybrid step: the classical model narrows the city to the k most valuable candidates,
    the quantum optimizer decides which combination of those to fund.
    Raise k as hardware and patience allow (qubits = k + a few slack qubits for the budget)."""
    return df.sort_values("value", ascending=False).head(k)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="CSV of real segments (optional)")
    ap.add_argument("--candidates", type=int, default=10, help="segments sent to the optimizer")
    ap.add_argument("--budget", type=int, default=8, help="repair budget in cost units")
    ap.add_argument("--reps", type=int, default=2, help="QAOA layers")
    ap.add_argument("--skip-qaoa", action="store_true", help="classical only, for fast iteration")
    ap.add_argument("--hardware", nargs="?", const="", default=None,
                    help="also run QAOA on IBM hardware (optional backend name); see src/undertow/hardware.py")
    args = ap.parse_args()

    if args.data:
        df = pd.read_csv(args.data)
    else:
        _, df = make_grid_network()
    df = add_scores(df)
    pairs_all = adjacency_pairs(df)

    cand = shortlist(df, args.candidates)
    cand_ids = set(cand["segment_id"])
    pairs = [(a, b) for a, b in pairs_all if a in cand_ids and b in cand_ids]
    qp = build_program(cand, pairs, args.budget)

    print(f"{len(df)} segments, {len(cand)} candidates, budget {args.budget}, "
          f"{num_qubits(qp)} qubits after QUBO conversion\n")

    # The current policy picks from the whole city, like the real thing.
    results = [solve_current_policy(df, args.budget), solve_exact(qp)]
    if not args.skip_qaoa:
        results.append(solve_qaoa(qp, reps=args.reps, label="QAOA simulator"))
    if args.hardware is not None:
        from undertow.hardware import get_ibm_sampler
        sampler, backend = get_ibm_sampler(args.hardware or None)
        results.append(solve_qaoa(qp, reps=1, maxiter=30, sampler=sampler, backend=backend,
                                  label=f"QAOA on {backend.name}"))

    rows = []
    for r in results:
        s = score_plan(df, pairs_all, r.chosen)
        rows.append({"plan": r.name, **s, "seconds": round(r.seconds, 2), "note": r.note,
                     "repairs": " ".join(sorted(r.chosen))})
    table = pd.DataFrame(rows).set_index("plan")
    with pd.option_context("display.width", 200, "display.max_columns", 20):
        print(table.drop(columns=["repairs"]).to_string())
        print()
        for name, row in table.iterrows():
            print(f"{name}: {row['repairs']}")

    OUT.mkdir(exist_ok=True)
    df.to_csv(OUT / "demo_segments_scored.csv", index=False)
    table.to_csv(OUT / "demo_plan_comparison.csv")
    (OUT / "demo_qubo.lp").write_text(qp.export_as_lp_string())
    build_map(df, {r.name: r.chosen for r in reversed(results)},
              scores={r["plan"]: {k: v for k, v in r.items() if k != "plan"} for r in rows},
              demo_data=not args.data).save(str(OUT / "demo_map.html"))
    (OUT / "demo_summary.json").write_text(json.dumps(rows, indent=2, default=str))
    print(f"\nWrote {OUT}/demo_map.html, demo_plan_comparison.csv, demo_segments_scored.csv, demo_qubo.lp")


if __name__ == "__main__":
    main()
