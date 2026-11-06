# Qiskit-Hackathon

## Run it
Windows PowerShell (macOS/Linux: use `source .venv/bin/activate`):
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_demo.py        # command-line demo, writes results/demo_*
streamlit run app.py      # interactive UI at http://localhost:8501
```
Web front end (static page, no build step):
```powershell
python scripts/precompute.py            # runs the optimizer for 4 budgets, writes static/data.json
python -m http.server -d static 8000    # then open http://localhost:8000
```
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

### Run locally
```powershell
# terminal 1: solver (from the repo root, venv active)
pip install -r solver/requirements.txt
uvicorn solver.app:app --port 8000

# terminal 2: web
cd web
copy .env.example .env.local        # NEXT_PUBLIC_SOLVER_URL=http://localhost:8000
npm install
npm run dev                         # http://localhost:3000
```
Refresh the offline data after changing the data or solver: `python scripts/make_fallback.py`
(and `python scripts/warm_check.py` to re-train the saved QAOA angles in `solver/angles.json`).

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
