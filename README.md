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
python scripts/precompute.py            # runs the optimizer for 4 budgets, writes web/data.json
python -m http.server -d web 8000       # then open http://localhost:8000
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
