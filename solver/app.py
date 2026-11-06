"""FastAPI solver. Run from the repo root:  uvicorn solver.app:app --reload"""

from __future__ import annotations

import csv
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import scenario as S
from . import service

app = FastAPI(title="Undertow solver")
origins = [o for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o]
app.add_middleware(
    CORSMiddleware, allow_origins=origins,
    allow_origin_regex=os.environ.get("ALLOWED_ORIGIN_REGEX", r"https://.*\.vercel\.app"),
    allow_methods=["*"], allow_headers=["*"],
)


class SolveIn(BaseModel):
    budget_units: int = Field(gt=0, le=10_000)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/scenario")
def scenario():
    return S.scenario()


@app.post("/solve")
def solve(body: SolveIn):
    rng = S.budget_range(S.load_df())
    if not rng["min_units"] <= body.budget_units <= rng["max_units"]:
        raise HTTPException(422, f"budget_units must be between {rng['min_units']} and {rng['max_units']}")
    return {k: v for k, v in service.solve(body.budget_units).items() if k != "theta"}


@app.get("/results")
def results():
    """Sampling results from the notebook, for the 'How it works' bars."""
    path = S.ROOT / "results" / "sampling_results.csv"
    with path.open(encoding="utf-8") as f:
        rows = {r["run"]: float(r["P(good plan, >=90% of optimum)"]) * 100 for r in csv.DictReader(f)}
    return {"random": rows["Random guessing"], "ideal": rows["Ideal simulator"], "noisy": rows["Noisy, level 3"]}
