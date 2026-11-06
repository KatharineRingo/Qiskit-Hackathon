# How quantum is used in RoadQure (and what it does not do)

## 1. The 30-second version

- **The problem.** A city can afford to repair only some of its flood-damaged roads. Which combination protects the most? Roads form a network, so the answer depends on which repairs sit next to each other: fixing one block of a route is worth little if the next block still floods.
- **The math.** That choice (repair this road or not, with a budget and bonuses for connected repairs) is a **QUBO**: a yes/no variable per road with at most pairwise terms. A QUBO maps directly onto an **Ising model**, a set of interacting spins, whose lowest-energy state is the best plan.
- **The quantum step.** We use **QAOA** (Quantum Approximate Optimization Algorithm) in Qiskit. It prepares a quantum state that is tuned so measuring it returns good plans more often than bad ones.
- **The result.** On our demo data the quantum search lands on a near-best plan many times more often than random guessing, and its best plan matches the exact classical optimum. That plan keeps far more of the route to the hospital open than fixing the most-complained-about roads. The exact numbers are in `results/summary.md`.
- **The honest part.** This is a small, simulated problem. A laptop solves it exactly in milliseconds. We do **not** claim a quantum speedup.

## 2. Where quantum lives in the code

```
data/segments.csv
      │
      ▼
src/undertow/risk.py      risk and importance of each road -> "value" of repairing it
      │
      ▼
src/undertow/qubo.py      build_lean_program(): one binary variable (qubit) per road
      │                    maximize  Σ value·x  +  Σ synergy·x_i·x_j   (budget enforced by a price per crew-day)
      ▼
to_ising()                QUBO -> Ising Hamiltonian H_C made of Z and ZZ terms
      │
      ▼
QAOAAnsatz(H_C, reps=2)   the parameterized circuit: Hadamards, then alternating cost and mixer layers
      │
      ▼
EstimatorV2 + COBYLA      classical optimizer tunes the angles by minimizing the expected energy <H_C>
      │
      ▼
SamplerV2                 run the tuned circuit, measure many times ("shots") -> bitstrings like 10110010
      │
      ▼
post-select + compare     drop plans over budget; "1" = repair this road. Compare with the exact classical answer
```

- **Qubit meaning.** Qubit `i` in state |1> means "repair road `i`", and |0> means "skip it".
- **Cost layer.** Phase rotations (`RZ` on single qubits, `RZZ` between qubits of connected roads) that encode the values and the connected-repair bonuses.
- **Mixer layer.** `RX` rotations that let probability move between plans.
- **Training.** The angles are tuned with `EstimatorV2` (expectation values) and COBYLA. The final circuit is sampled with `SamplerV2`.
- **Where to read it.** `notebooks/RoadQure_qaoa.ipynb` walks through every step with results. The web app's live search is `solver/service.py`.

### What superposition does and does not mean
The circuit starts in an equal superposition over all `2^n` plans, but that does **not** mean it "checks every plan at once and picks the best." Each measurement returns **one** bitstring.
QAOA works only if the tuned interference makes good plans measurably more likely, and we show exactly that by sampling 2,000 to 4,000 times and counting.

## 3. Why quantum might help, and why it does not yet

- **Why it is a natural fit.** The number of possible plans doubles with every road (`2^n`), and the connected-repair bonuses couple the choices, which makes the problem hard in general. QAOA is designed for exactly this QUBO/Ising shape.
- **Why it does not help at our size.** With 8 roads there are 256 plans. Exact classical solving is instant.
- **Real cities.** Regular classical solvers (integer programming, local search, annealing) already handle hundreds of roads well. There is **no proof that QAOA beats them**, and today's quantum hardware cannot run problems that large anyway: circuits get deep, and noise grows with depth.
- **What we do show.** The full pipeline works end to end (real-world problem, QUBO, QAOA in Qiskit, comparison with an exact solver and today's practice), including the effect of compilation, noise and error suppression. It is ready to be run on larger instances and better hardware as they arrive.

## 4. Running on real IBM quantum hardware

The simulator results come from Qiskit Aer, including a noise model taken from a snapshot of a real IBM device (FakeTorino). That is a simulation, **not** a hardware run.
To run the same circuit the web app uses on a real device:

1. **Get an IBM Quantum account and API key** from the IBM Quantum Platform (check the hackathon instructions for the channel and instance you may use).
2. **Save your account once** (this stores the key on your machine; never commit it):
   ```powershell
   .venv\Scripts\Activate.ps1
   python -c "from qiskit_ibm_runtime import QiskitRuntimeService as S; S.save_account(token='PASTE_YOUR_KEY', overwrite=True)"
   ```
3. **Run it** (a hardware job can queue for a while; run it early):
   ```powershell
   python scripts/run_hardware.py
   ```
   It picks the least-busy compatible device, transpiles the circuit for it, runs 2,000 shots, and also runs the identical circuit on an ideal and a noisy simulator.
   Everything is saved to `results/hardware_run.json`.
4. **See it in the notebook.** Re-run the "Real quantum hardware" cell in `notebooks/RoadQure_qaoa.ipynb`. It compares hardware, noisy simulator and ideal simulator side by side.

To check the script without using hardware time, run `python scripts/run_hardware.py --dry-run`. That uses a simulated stand-in and writes `results/hardware_run_dryrun.json`, which is never treated as a hardware result.
