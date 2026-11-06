# RoadQure

**Miami fills the potholes it can see. RoadQure finds the roads failing underwater, then uses
quantum optimization to decide which repairs keep the city connected when the next king tide hits.**

Built for the Qiskit IBM hackathon through Florida Gulf Coast University.

## The problem
In South Florida, roads don't fail from freeze-thaw. They fail from below: king tides and a rising
water table soak the base under the pavement, and the road loses strength long before a pothole shows up.
Cities react to 311 complaints, so they keep patching surfaces over saturated bases, and the potholes come back.

## What RoadQure does
1. **Hidden-damage risk (classical).** Scores each road segment on tide exposure, groundwater depth and elevation,
   not on complaints.
2. **Repair planning (quantum).** Picks which segments to repair under a fixed budget. Repairs on connected
   segments of the same evacuation or hospital corridor reinforce each other. That pairwise effect is the
   quadratic term that makes this a natural QUBO, solved with QAOA in Qiskit.
3. **Before/after.** Compares the plan against today's policy (fix whatever gets the most 311 reports).

```
segments -> risk score -> shortlist (classical) -> QUBO -> QAOA (quantum) -> repair plan -> map
```

## Results (notebooks/RoadQure_qaoa.ipynb: Mid-Beach demo data, 8 roads, 8 qubits, budget 14 crew-days, 2 QAOA layers)
Compared on the whole area. A route counts as "open" only if every block survives the next king tide.

| Plan | Objective | Evacuation route open | Route to the hospital open |
|---|---|---|---|
| Today's approach (most 311 complaints) | 3.07 | 61.5% | 0.3% |
| Classical exact (the best possible plan) | 9.45 | 61.5% | 32.7% |
| QAOA, ideal simulator | 9.45 | 61.5% | 32.7% |
| QAOA, noisy simulator (FakeTorino noise model) | 9.45 | 61.5% | 32.7% |

The evacuation route is unchanged because on this data it sits on a low-risk road, so no plan touches it.

**How often each method finds a good plan** (a valid plan within 10% of the best, out of 4,000 samples):
| Run | Good plans | vs. random guessing |
|---|---|---|
| Random guessing | 0.8% | 1x |
| QAOA, ideal simulator | 24.5% | 31x |
| QAOA, noisy simulator (FakeTorino noise, compilation level 3) | 20.4% | 26x |

- **Encoding the budget:** extra "slack" qubits (12 qubits, 468 two-qubit gates on device) gave only 2.8x over random. One qubit per road with a tuned price per crew-day (8 qubits, 37 two-qubit gates) gave 31x.
- **Error suppression:** heavier transpilation cut the two-qubit gate count (41 to 37) and helped slightly; dynamical decoupling did not help in simulation (the noise model has little of the idle dephasing it targets).
- **Real hardware:** not run yet. `python scripts/run_hardware.py` runs the same circuit on an IBM device; see `QUANTUM.md`.
- These numbers come from a fresh notebook run and are saved in `results/`. The data is illustrative (see `data/DATA_NOTES.md`), so they show that the method works, not what Miami Beach should repair.

**Honesty note:** at this size a classical exact solver is just as good and much faster. We do not claim a quantum speedup.
Real classical solvers handle hundreds of roads easily, and no one has shown QAOA beating them. What we show is the working pipeline, the formulation lessons, and the noise and error-suppression analysis.

## Quick start
```bash
python -m venv .venv
source .venv/bin/activate           # macOS/Linux
.venv\Scripts\Activate.ps1          # Windows PowerShell (no `source`, and no `&&` in PowerShell 5.1)
pip install -r requirements.txt
python run_demo.py                  # ~5 seconds, writes results/demo_map.html
streamlit run app.py                # interactive UI at http://localhost:8501
jupyter notebook notebooks/RoadQure_qaoa.ipynb   # main analysis, ~3 minutes
pytest -q
```
Options: `--candidates 12 --budget 10 --reps 3`, `--skip-qaoa` (fast iteration), `--data data/segments.csv`,
`--hardware [backend_name]` (IBM hardware, see `src/RoadQure/hardware.py`).

## Interactive UI
`streamlit run app.py` opens a browser app wrapping the same pipeline as `run_demo.py`. Use the sidebar sliders
(repair budget, candidates sent to the optimizer, QAOA layers), click **Run optimization**, and compare the current
311-report policy, the classical exact solver and QAOA on the map, in a table and in bar charts.
It uses the synthetic network; real-data upload and hardware runs are not wired into the UI yet.

## Repo layout
```
notebooks/RoadQure_qaoa.ipynb  main analysis: circuit, transpilation, Estimator/Sampler, ideal vs noisy
run_demo.py                 quick end-to-end pipeline + map
app.py                      Streamlit UI: budget/candidate/QAOA sliders, map, plan comparison
src/RoadQure/
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
