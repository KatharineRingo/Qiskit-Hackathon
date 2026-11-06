"""Solvers: QAOA (quantum), exact classical (ground truth), and the city's current policy (baseline).

Be upfront in the pitch: at hackathon size the exact classical solver keeps up or wins.
The demo shows (1) the formulation, (2) that QAOA lands on or near the optimum,
(3) that the formulation beats "fill what people complain about" by a wide margin.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2 as AerSampler
from qiskit_algorithms import QAOA, NumPyMinimumEigensolver
from qiskit_algorithms.optimizers import COBYLA
from qiskit_algorithms.utils import algorithm_globals
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_optimization.converters import QuadraticProgramToQubo


@dataclass
class PlanResult:
    name: str
    chosen: set[str]
    seconds: float
    note: str = ""


def _chosen(result, qp: QuadraticProgram) -> set[str]:
    return {v.name for v, x in zip(qp.variables, result.x) if round(x) == 1}


def num_qubits(qp: QuadraticProgram) -> int:
    return QuadraticProgramToQubo().convert(qp).get_num_vars()


def solve_exact(qp: QuadraticProgram) -> PlanResult:
    t = time.perf_counter()
    res = MinimumEigenOptimizer(NumPyMinimumEigensolver()).solve(qp)
    return PlanResult("Classical exact", _chosen(res, qp), time.perf_counter() - t)


def solve_qaoa(qp: QuadraticProgram, reps: int = 2, maxiter: int = 150, seed: int = 42,
               sampler=None, backend=None, label: str = "QAOA") -> PlanResult:
    """QAOA on the Aer simulator by default.

    For IBM hardware, pass sampler= and backend= from hardware.get_ibm_sampler().
    The circuit is transpiled for whichever backend runs it (the plain StatevectorSampler
    skips this and is ~100x slower, which is why we use Aer).
    """
    algorithm_globals.random_seed = seed
    backend = backend or AerSimulator(seed_simulator=seed)
    sampler = sampler or AerSampler(seed=seed)
    pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
    t = time.perf_counter()
    qaoa = QAOA(sampler=sampler, optimizer=COBYLA(maxiter=maxiter), reps=reps, transpiler=pm)
    res = MinimumEigenOptimizer(qaoa).solve(qp)
    return PlanResult(f"{label} (reps={reps})", _chosen(res, qp), time.perf_counter() - t,
                      note=f"{num_qubits(qp)} qubits")


def solve_current_policy(df: pd.DataFrame, budget: int) -> PlanResult:
    """What cities do today: fix the segments with the most pothole complaints until the money runs out."""
    t = time.perf_counter()
    chosen, spent = set(), 0
    for row in df.sort_values("reports_311", ascending=False).itertuples():
        if spent + row.repair_cost <= budget:
            chosen.add(row.segment_id)
            spent += row.repair_cost
    return PlanResult("Current policy (most 311 reports)", chosen, time.perf_counter() - t)
