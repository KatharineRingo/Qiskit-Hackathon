# RoadQure

## Run it

**You need:** Python 3.12, Node.js 18+, and Git. Commands below are for Windows PowerShell
(macOS/Linux: use `source .venv/bin/activate` and `cp` instead of `copy`).

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
If PowerShell blocks the activate script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### 2. Start the app (two terminals, both from the repo root)
**Terminal 1: the quantum solver.** Wait until it prints "Application startup complete".
```powershell
.venv\Scripts\Activate.ps1
uvicorn solver.app:app --port 8000
```
**Terminal 2: the web app.**
```powershell
cd web
npm run dev
```
Open **http://localhost:3000** and press **Find the best repairs**.
If the solver is not running, the app still works from saved results and shows a small "offline mode" note.

### Other ways to run it
| What | Command | Where |
|---|---|---|
| Command-line demo (writes `results/demo_*`) | `python run_demo.py` | `results/demo_map.html` |
| Streamlit app | `streamlit run app.py` | http://localhost:8501 |
| Earlier static page | `python scripts/precompute.py` then `python -m http.server -d static 8001` | http://localhost:8001 |
| Notebook | `jupyter notebook notebooks/RoadQure_qaoa.ipynb` | |
| Tests | `pytest -q` | |

Refresh the saved offline results after changing the data or solver: `python scripts/make_fallback.py`
(run `python scripts/warm_check.py` first if the data changed, to re-train the saved QAOA angles).

**Troubleshooting**
- Port already in use: pick another one, e.g. `uvicorn solver.app:app --port 8010`, and set `NEXT_PUBLIC_SOLVER_URL=http://localhost:8010` in `web/.env.local`, then restart `npm run dev`.
- The page says "offline mode" after solving: the solver is not reachable. Check terminal 1 and that `web/.env.local` exists.
- Map is blank or unstyled: the basemap loads from the internet, so check your connection.

Details, options and repo layout: see [PROJECT.md](PROJECT.md).

# Use-Case Canvas

## 1. The problem
Write one paragraph for a reader unfamiliar with your field.
Use plain language and define any necessary technical terms.

## 2. Who has this problem
Be specific. Not "banks": "mid-size asset managers rebalancing
multi-asset portfolios monthly under UCITS constraints."

## 3. How it's solved today
What tool, what algorithm, how long does it take, how good is the answer?
This is your baseline. Without it you have no story.
If you don't know, that's your first research task.

## 4. What "better" is worth
Put a number on it. Currency, hours, lives, tonnes of CO2, error rate,
any unit, but a number. "It would be nice" is not an answer.

## 5. The quantum shape
Which of the three shapes is it? (Optimization / Simulation / Learning)
Why? What's the combinatorial explosion, the quantum system, or the
hidden structure?

## 6. The honest problem-size gap
How big is a real instance? How big can we run during the hackathon?
State both numbers. Explain the gap between the demonstration and a realistic application.

## 7. What would have to be true
For this to become useful beyond the demonstration, what would need
to change in hardware, algorithms, data, operations, or regulation?

## 8. What we will build or analyze during the hackathon
A tiny, concrete, achievable thing. Not the vision. The demo.
"We map a small routing instance to a QUBO, run a simulation,
compare with a classical solver, and test on hardware if feasible."

## 9. Why anyone should care
Three sentences. This becomes your opening slide.

## Web app (Next.js + live quantum solver)

`solver/` is a FastAPI service that runs QAOA on the Qiskit Aer simulator when you press "Find the best repairs".
`web/` is the Next.js front end (MapLibre + deck.gl). If the solver is unreachable or takes over 8 seconds, the app silently
uses `web/public/fallback.json` and shows a small "offline mode" note.

To run it locally, see **Run it** at the top.

### Deploy
1. **Solver on Render.** Push the repo to GitHub. In Render choose New, then Blueprint, and select the repo.
   `render.yaml` builds `solver/Dockerfile` (build context = repo root). When it is live, open `https://<your-service>.onrender.com/health`
   and note the URL. No Docker is needed on your machine. Free instances sleep when idle, so the first request can take a minute
   (the web app uses the fallback meanwhile).
2. **Web on Vercel.** Import the same repo in Vercel and set **Root Directory** to `web`. Add the environment variable
   `NEXT_PUBLIC_SOLVER_URL` = the Render URL from step 1 (no trailing slash), for Production and Preview, then deploy.
3. **CORS.** The solver already allows `http://localhost:3000` and any `https://*.vercel.app`. For a custom domain, set
   `ALLOWED_ORIGINS` on the Render service to a comma-separated list that includes it.
4. Open the Vercel URL, press **Find the best repairs**, and check that "offline mode" does not appear under the result.

All data is demo data (see `data/DATA_NOTES.md`).
