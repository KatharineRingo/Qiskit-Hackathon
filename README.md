# RoadQure

**Quantum-Optimized Road Repair Planning for Coastal Flooding & King Tides**  
*Florida Gulf Coast University | Qiskit Fall Fest 2026*  

🌐 **Live Interactive Web App:** [https://qiskit-hackathon.vercel.app/?v=1](https://qiskit-hackathon.vercel.app/?v=1)  
📓 **Quantum QAOA Notebook:** [`notebooks/undertow_qaoa.ipynb`](notebooks/undertow_qaoa.ipynb)  
⚛️ **Quantum Architecture Guide:** [`QUANTUM.md`](QUANTUM.md)  
📊 **Project Overview & Benchmarks:** [`PROJECT.md`](PROJECT.md)  

---

# Use-Case Canvas

## 1. The problem
In coastal South Florida, roads don't fail from snow or freeze-thaw cycles—they fail from below. Rising sea levels and recurring king tides soak the porous base underneath the asphalt, compromising structural integrity long before surface cracks appear. Today, cities reactively patch visible potholes reported by 311 citizen complaints. This repeatedly paves over waterlogged foundations while failing to protect contiguous evacuation routes and hospital corridors.

## 2. Who has this problem
Municipal public works departments and regional transportation planners (e.g., City of Miami Beach, City of Fort Myers, Lee County DOT) responsible for maintaining road networks under strict annual capital budgets.

## 3. How it's solved today
Cities prioritize repairs through greedy ranking based on 311 complaint volume. This creates isolated, disconnected patches that leave emergency transit corridors compromised during seasonal king tides and tropical storms.

## 4. What "better" is worth
For the exact same taxpayer budget, RoadQure increases the survival probability of the primary hurricane evacuation route from **44.7% to 79.1%** and avoids premature secondary paving failures across flood-prone corridors.

## 5. The quantum shape
**Optimization (Combinatorial QUBO)**. Repairing adjacent road segments along a corridor produces network synergy ($x_i \cdot x_j$): fixing one block has minimal value if the next block remains impassable. This pairwise connectivity bonus is a natural quadratic term mapped to a qubit Hamiltonian and solved using QAOA in Qiskit.

## 6. The honest problem-size gap
- **Hackathon Demo:** 8–10 candidate segments mapped onto 8–14 qubits, evaluated across ideal simulation, IBM Heron noise models (`FakeTorino`), and live hardware.
- **Production Scale:** 500–1,000 city road segments requiring 500+ logical qubits with fault-tolerant error mitigation.

## 7. What would have to be true
Commercial quantum hardware must achieve deeper coherence times and higher two-qubit gate fidelities to evaluate full municipal networks without noise degradation, supported by low-latency quantum cloud runtimes integrated into municipal GIS tools.

## 8. What we built during the hackathon
1. **Classical Flood Model:** Ingests NOAA tidal gauges, USGS elevation, and 311 history to score hidden subterranean risk.
2. **Lean QUBO & QAOA Engine:** Lagrangian price formulation achieving a **$16\times$ concentration of good repair plans** over random guessing.
3. **Interactive Web App:** Deployed on Vercel with 3D map views, tide sliders, and live quantum solution rendering.

## 9. Why anyone should care
Road maintenance is currently reactive, wasteful, and blind to climate risk. RoadQure connects real coastal hydrological data to quantum optimization, doubling evacuation route resilience without increasing municipal budgets.

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
