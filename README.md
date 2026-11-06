# RoadQure

**Quantum-Optimized Road Repair Planning for Coastal Flooding & King Tides**  
*Florida Gulf Coast University | Qiskit Fall Fest 2026*  

🌐 **Web App:** [https://qiskit-hackathon.vercel.app](https://qiskit-hackathon.vercel.app)  
📓 **Quantum QAOA Notebook:** [`notebooks/undertow_qaoa.ipynb`](notebooks/undertow_qaoa.ipynb)  
⚛️ **Quantum Architecture Guide:** [`QUANTUM.md`](QUANTUM.md)  
📊 **Project Overview & Benchmarks:** [`PROJECT.md`](PROJECT.md)  

> **How the demo runs:** QAOA runs live in Qiskit Aer through our local solver service (`solver/`). The hosted Vercel app replays the results recorded from that live run (`web/public/fallback.json`), so it works without a backend. To run the optimization live yourself, follow [Run it locally](#run-it-locally).

---

# Use-Case Canvas

## 1. The problem
In South Florida, king tides and rising groundwater can weaken roads from underneath before damage shows on the surface. Cities usually prioritize repairs by resident complaints (311 reports), which can miss hidden damage along critical routes. And fixing the worst roads one at a time isn't always the best plan: roads form networks, and repairing one block does little if the connecting blocks still flood.

## 2. Who has this problem
Municipal public works departments and regional transportation planners (e.g., City of Miami Beach, City of Fort Myers, Lee County DOT) who maintain road networks under fixed annual budgets.

## 3. How it's solved today
Repairs are ranked mostly by complaint volume. That produces disconnected patches and can leave evacuation and hospital corridors exposed during king tides and storms.

## 4. What "better" is worth
In our Mid-Beach demo (8 candidate roads, 14 crew-day budget, simulated flood conditions), the optimized plan kept the route to Mount Sinai Medical Center open about **33%** of the time, versus **0.3%** when repairing the most-complained-about roads with the same budget. These inputs are simulated, so this shows the approach, not a real-world forecast.

## 5. The quantum shape
**Optimization (QUBO).** Each repair is a yes/no decision. Repairing adjacent blocks on the same corridor is worth more together than apart, which is a pairwise ($x_i \cdot x_j$) term. We convert the QUBO to an Ising Hamiltonian and solve it with QAOA in Qiskit.

## 6. The honest problem-size gap
- **Hackathon demo:** 8 candidate roads on 8 qubits (256 possible plans), run on Qiskit Aer's ideal simulator and with an IBM `FakeTorino` noise model. A classical computer solves this size in milliseconds; we are not claiming a quantum speedup.
- **Production scale:** a city network of 500–1,000 road segments would need hundreds of qubits and much lower hardware noise.

## 7. What would have to be true
Quantum hardware would need higher two-qubit gate fidelity and longer coherence to run city-scale instances without noise washing out the result, and the solver would need to plug into municipal GIS and real flood data.

## 8. What we built during the hackathon
1. **Hidden-damage risk scoring:** ranks road segments by tide exposure, groundwater depth and elevation, with extra weight for hospital and evacuation routes.
2. **QUBO + QAOA engine:** `QAOAAnsatz`, `EstimatorV2` + COBYLA for training, `SamplerV2` (2,000–4,000 shots) for sampling, budget filtering on the samples.
   - Ideal simulator: near-optimal plans (≥90% of the optimum) **~31× more often than random guessing**.
   - `FakeTorino` noise model: **~26× better than random**.
   - The best QAOA plan **matched the exact classical optimum**.
3. **Formulation finding:** replacing slack-qubit budget encoding with a budget-penalty formulation cut the transpiled circuit from **12 to 8 qubits** and **468 to 37 two-qubit gates** (~92% fewer), and raised performance from **2.8× to 31×** over random.
4. **Interactive web app:** 3D flood-risk map, repair-budget slider, and a side-by-side of the QAOA plan, complaint-based prioritization, and the exact classical solver.
5. **Reproducible notebook:** circuit construction, training, sampling, transpilation at optimization levels 0–3, noise simulation, and error-suppression experiments (optimized compilation, dynamical decoupling).

## 9. Why anyone should care
Road maintenance today is mostly reactive. RoadQure shows how connected repairs can be planned around the routes people need in a flood, and what it takes to put that planning problem on a quantum computer.

---

## Data transparency
The demo uses real Miami Beach street names and approximate street geometry, Collins Avenue (a City of Miami Beach evacuation route), and Mount Sinai Medical Center's real location. Flood exposure, elevation, groundwater depth, complaint counts and repair costs are **estimated or simulated**. See [`data/DATA_NOTES.md`](data/DATA_NOTES.md). Results demonstrate the method, not actual repair recommendations.

## What's next
Swap in measured city data (NOAA tides, USGS elevation and groundwater, Miami-Dade 311), run the circuits on IBM quantum hardware, and scale to larger road networks.

---

---

## Run it locally

**You need:** Python 3.12, Node.js 18+, and Git. Commands below are for Windows PowerShell.

### 1. One-time setup
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd web
npm install
copy .env.example .env.local
cd ..
```

### 2. Start the app (two terminals from repo root)
**Terminal 1: Quantum solver backend**
```powershell
.venv\Scripts\Activate.ps1
uvicorn solver.app:app --port 8000
```
**Terminal 2: Web frontend**
```powershell
cd web
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## Quick Demo & Scripts
| Purpose | Command | Result |
|---|---|---|
| **CLI Demo & Map** | `python run_demo.py` | Writes `results/demo_map.html` |
| **Streamlit App** | `streamlit run app.py` | Opens `http://localhost:8501` |
| **Jupyter Notebook** | `jupyter notebook notebooks/undertow_qaoa.ipynb` | End-to-end QAOA analysis |
| **Test Suite** | `pytest -q` | Validates schema, budget, QAOA convergence |

All demo data is illustrative (see `data/DATA_NOTES.md`).
