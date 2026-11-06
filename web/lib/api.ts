import type { Fallback, Results, Scenario, SolveResult } from "./types";

// Without NEXT_PUBLIC_SOLVER_URL (e.g. a Vercel deploy with no solver yet) the app runs from public/fallback.json.
const BASE = (process.env.NEXT_PUBLIC_SOLVER_URL || "").replace(/\/$/, "");
const TIMEOUT_MS = 8000;

let fallbackPromise: Promise<Fallback> | null = null;
export function getFallback(): Promise<Fallback> {
  fallbackPromise ??= fetch("/fallback.json").then((r) => r.json());
  return fallbackPromise;
}

async function timed<T>(path: string, init?: RequestInit): Promise<T> {
  if (!BASE) throw new Error("no solver url");
  const ctl = new AbortController();
  const t = setTimeout(() => ctl.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(BASE + path, { ...init, signal: ctl.signal });
    if (!r.ok) throw new Error(String(r.status));
    return (await r.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

/** Live from the solver API; silently falls back to the precomputed file. `offline` is true when the fallback was used. */
export async function loadScenario(): Promise<{ scenario: Scenario; results: Results; offline: boolean }> {
  try {
    const [scenario, results] = await Promise.all([timed<Scenario>("/scenario"), timed<Results>("/results")]);
    return { scenario, results, offline: false };
  } catch {
    const f = await getFallback();
    return { scenario: f.scenario, results: f.results, offline: true };
  }
}

export async function solve(budgetUnits: number): Promise<{ result: SolveResult; offline: boolean }> {
  try {
    const result = await timed<SolveResult>("/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ budget_units: budgetUnits }),
    });
    return { result, offline: false };
  } catch {
    const f = await getFallback();
    const result = f.solves[String(budgetUnits)];
    if (!result) throw new Error("no fallback for this budget");
    return { result, offline: true };
  }
}
