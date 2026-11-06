"""Run the app's QAOA circuit on a real IBM quantum computer and save the counts for the notebook.

    python scripts/run_hardware.py                  # real hardware (needs a saved IBM Quantum account)
    python scripts/run_hardware.py --backend ibm_xxx --shots 2000
    python scripts/run_hardware.py --dry-run        # SIMULATED stand-in, to test this script. Never counts as hardware.

One-time account setup (token from your IBM Quantum Platform dashboard):
    python -c "from qiskit_ibm_runtime import QiskitRuntimeService as S; S.save_account(token='YOUR_TOKEN', overwrite=True)"
Check the hackathon instructions for the channel/instance you are allowed to use.

It takes the SAME circuit the web app uses (same problem, same trained angles from solver/angles.json), transpiles it for
the chosen backend, runs it once, and also runs the identical circuit on an ideal simulator and on a noisy simulator built
from a snapshot of an IBM device (FakeTorino). Output: results/hardware_run.json (or hardware_run_dryrun.json).
The notebook picks the file up and compares hardware vs. simulator.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

from qiskit.circuit.library import QAOAAnsatz  # noqa: E402
from qiskit.transpiler import generate_preset_pass_manager  # noqa: E402
from qiskit_aer import AerSimulator  # noqa: E402
from qiskit_aer.primitives import SamplerV2 as AerSampler  # noqa: E402
from qiskit_ibm_runtime.fake_provider import FakeTorino  # noqa: E402
from qiskit_optimization.translators import to_ising  # noqa: E402

from solver import scenario as S  # noqa: E402
from solver import service as V  # noqa: E402
from undertow.data_synthetic import adjacency_pairs  # noqa: E402
from undertow.qubo import build_lean_program  # noqa: E402


def two_qubit_gates(circ) -> int:
    ops = circ.count_ops()
    return int(sum(ops.get(g, 0) for g in ("cz", "ecr", "cx")))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", help="IBM backend name (default: least busy that fits)")
    ap.add_argument("--budget", type=int, help="budget in crew-days (default: the app's default)")
    ap.add_argument("--shots", type=int, default=2000)
    ap.add_argument("--dry-run", action="store_true", help="simulated stand-in; does not contact IBM")
    args = ap.parse_args()

    df = S.load_df()
    rng = S.budget_range(df)
    budget = args.budget or rng["default_units"]
    saved = V._load_angles().get(str(budget))
    if not saved:
        sys.exit(f"No saved angles for budget {budget}. Run: python scripts/warm_check.py")

    ids = S.candidate_ids(df)
    cand = df[df["segment_id"].isin(ids)]
    cids = set(ids)
    pairs = [(a, b) for a, b in adjacency_pairs(df) if a in cids and b in cids]
    lean = build_lean_program(cand, pairs, saved["price"])
    names = [v.name for v in lean.variables]
    cost_op, _ = to_ising(lean)
    measured = QAOAAnsatz(cost_op, reps=V.REPS).measure_all(inplace=False)
    theta = saved["theta"]
    print(f"Problem: budget {budget} crew-days, {len(names)} qubits, {len(theta)} trained angles, {args.shots} shots")

    # --- the identical circuit on an ideal simulator and a noisy simulator (snapshot of a real IBM device) ---
    ideal_pm = generate_preset_pass_manager(optimization_level=1, backend=AerSimulator())
    ideal = AerSampler(seed=7).run([ideal_pm.run(measured).assign_parameters(theta)], shots=args.shots).result()[0].data.meas.get_counts()
    fake = FakeTorino()
    fake_isa = generate_preset_pass_manager(optimization_level=3, backend=fake, seed_transpiler=7).run(measured).assign_parameters(theta)
    noisy = AerSampler.from_backend(fake, seed=7).run([fake_isa], shots=args.shots).result()[0].data.meas.get_counts()

    # --- the device ---
    if args.dry_run:
        backend_name, job_id = "DRY RUN (FakeTorino noise simulation, NOT hardware)", "dry-run"
        isa = fake_isa
        t0 = time.time()
        hw = AerSampler.from_backend(fake, seed=11).run([isa], shots=args.shots).result()[0].data.meas.get_counts()
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as RuntimeSampler
        service = QiskitRuntimeService()
        backend = service.backend(args.backend) if args.backend else service.least_busy(
            operational=True, simulator=False, min_num_qubits=len(names))
        backend_name = backend.name
        isa = generate_preset_pass_manager(optimization_level=3, backend=backend, seed_transpiler=7).run(measured).assign_parameters(theta)
        print(f"Submitting to {backend_name} ({two_qubit_gates(isa)} two-qubit gates, depth {isa.depth()}) ...")
        job = RuntimeSampler(mode=backend).run([isa], shots=args.shots)
        job_id = job.job_id()
        print("Job id:", job_id, "(waiting; hardware jobs queue)")
        t0 = time.time()
        hw = job.result()[0].data.meas.get_counts()

    out = {
        "dry_run": bool(args.dry_run), "backend": backend_name, "job_id": job_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "budget_units": budget, "shots": args.shots, "num_qubits": len(names), "variable_names": names,
        "transpiled": {"depth": int(isa.depth()), "two_qubit_gates": two_qubit_gates(isa)},
        "run_seconds": round(time.time() - t0, 1),
        "counts": {"hardware": hw, "noisy_simulator": noisy, "ideal_simulator": ideal},
    }
    dest = ROOT / "results" / ("hardware_run_dryrun.json" if args.dry_run else "hardware_run.json")
    dest.write_text(json.dumps(out), encoding="utf-8")
    print(f"Saved {dest}")


if __name__ == "__main__":
    main()
