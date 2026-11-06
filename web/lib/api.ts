import type { Results, Scenario, SolveResult } from "./types";

const SOLVER_URL = process.env.NEXT_PUBLIC_SOLVER_URL || "http://localhost:8000";

export async function loadScenario(): Promise<{ scenario: Scenario; results: Results; offline: boolean }> {
  try {
    const res = await fetch(`${SOLVER_URL}/scenario`, { signal: AbortSignal.timeout(3000) });
    if (res.ok) {
      const data = await res.json();
      return { scenario: data.scenario, results: data.results, offline: false };
    }
  } catch {
    // fall through to fallback
  }

  const fb = await fetch("/fallback.json");
  const data = await fb.json();
  return { scenario: data.scenario, results: data.results, offline: true };
}

export async function solve(budgetUnits: number): Promise<{ result: SolveResult; offline: boolean }> {
  try {
    const res = await fetch(`${SOLVER_URL}/solve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ budget: budgetUnits }),
      signal: AbortSignal.timeout(8000),
    });
    if (res.ok) {
      const result = await res.json();
      return { result, offline: false };
    }
  } catch {
    // fall through to fallback
  }

  const fb = await fetch("/fallback.json");
  const data = await fb.json();
  const solves = data.solves || {};
  const result = solves[String(budgetUnits)] || Object.values(solves)[0];
  return { result, offline: true };
}
