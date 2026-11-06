# Undertow

**Miami fills the potholes it can see. Undertow finds the roads failing underwater, then uses
quantum optimization to decide which repairs keep the city connected when the next king tide hits.**

Built for the Qiskit IBM hackathon through Florida Gulf Coast University.

## The problem
In South Florida, roads don't fail from freeze-thaw. They fail from below: king tides and a rising
water table soak the base under the pavement, and the road loses strength long before a pothole shows up.
Cities react to 311 complaints, so they keep patching surfaces over saturated bases, and the potholes come back.

## What Undertow does
1. **Hidden-damage risk (classical).** Scores each road segment on tide exposure, groundwater depth and elevation,
   not on complaints.
2. **Repair planning (quantum).** Picks which segments to repair under a fixed budget. Repairs on connected
   segments of the same evacuation or hospital corridor reinforce each other. That pairwise effect is the
   quadratic term that makes this a natural QUBO, solved with QAOA in Qiskit.
3. **Before/after.** Compares the plan against today's policy (fix whatever gets the most 311 reports).

```
segments -> risk score -> shortlist (classical) -> QUBO -> QAOA (quantum) -> repair plan -> map
```

## Quick pipeline results (run_demo.py, synthetic data, 10 candidates, 14 qubits)
| Plan | Objective | Evac route stays open | Hospital access stays open |
|---|---|---|---|
| Current policy (most 311 reports) | 3.69 | 44.7% | 83.4% |
| Classical exact | 5.85 | 79.1% | 83.4% |
| QAOA, Aer simulator | 5.85 | 79.1% | 83.4% |

These numbers come from fake data and only prove the pipeline works. Replace them with real-data results.

**Honesty note for judges:** at this size a classical exact solver is just as good and faster. Quantum matters
because the formulation (pairwise repair interactions over a whole city's road network) grows quickly,
and this is the shape of problem quantum optimization is being built for. We show QAOA reaches the optimum
on the problem sizes today's hardware can handle.

## Main results: `notebooks/undertow_qaoa.ipynb` (synthetic data, 8 segments, 8 qubits)
| Run | Good repair plans (% of shots) | vs. random guessing |
|---|---|---|
| Random guessing | 1.2% | 1x |
| QAOA, ideal simulator | 18.6% | 16x |
| QAOA, noisy simulator (FakeTorino noise, opt. level 3) | 12.7% | 11x |

- **What we learned:** encoding the budget with slack qubits (11 qubits, 578 two-qubit gates on device) gave only 2x over random.
  Switching to one qubit per segment with a tuned price per cost unit (8 qubits, 100 two-qubit gates) gave 16x.
- **Error suppression:** heavier transpilation helped slightly; dynamical decoupling did not help in simulation
  (the noise model has little of the idle dephasing DD targets). Testing on hardware is a next step.
- Charts and tables: `results/`.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_demo.py                  # ~5 seconds, writes results/demo_map.html
jupyter notebook notebooks/undertow_qaoa.ipynb   # main analysis, ~1 minute
pytest -q
```
Options: `--candidates 12 --budget 10 --reps 3`, `--skip-qaoa` (fast iteration), `--data data/segments.csv`,
`--hardware [backend_name]` (IBM hardware, see `src/undertow/hardware.py`).

## Repo layout
```
notebooks/undertow_qaoa.ipynb  main analysis: circuit, transpilation, Estimator/Sampler, ideal vs noisy
run_demo.py                 quick end-to-end pipeline + map
src/undertow/
  data_synthetic.py         fake Miami Beach-style network (defines the CSV schema)
  data_sources.py           real-data loaders: OSM roads, NOAA tides, USGS elevation, Miami-Dade 311
  risk.py                   hidden-damage risk + corridor criticality
  qubo.py                   repair plan as a QUBO: slack version + lean one-qubit-per-segment version
  solve.py                  QAOA, exact classical, current-policy baseline
  hardware.py               IBM Quantum hardware sampler
  metrics.py                scoring used for every plan (incl. corridor-open probability)
  viz.py                    Folium map with one layer per plan
tests/                      pytest checks: schema, budget, QAOA within 15% of optimal
TEAM_PLAN.md                who does what
```

## Data sources
- Roads: OpenStreetMap (OSMnx)
- Tides: NOAA CO-OPS, Virginia Key station 8723214
- Elevation: USGS Elevation Point Query Service
- Pothole reports: Miami-Dade County 311 Service Requests (Open Data Hub)
- Groundwater: USGS groundwater levels (TODO)

## Model assumptions (v0, say these out loud)
- Risk weights are hand-set and tunable; upgrade to a trained model on repeat-pothole history.
- Segment failures are treated as independent when computing corridor-open probability.
- A full-depth repair leaves a 5% residual failure chance.
