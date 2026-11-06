import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from solver import scenario as S, service

t = time.time(); service.warm_angles(); print("warm", round(time.time() - t, 1), "s")
for b in S.budgets(S.load_df()):
    r = service.solve(b["units"])
    print(b["label"], b["units"], r["classical_match"], r["plans"]["undertow"]["segments"], r["headline"], r["solve_ms"], "ms")
service.solve.cache_clear()
print("cached-angle solve:", service.solve(14)["solve_ms"], "ms")
