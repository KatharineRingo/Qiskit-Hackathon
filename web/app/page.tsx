"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ControlPanel from "@/components/ControlPanel";
import HowItWorks from "@/components/HowItWorks";
import SolvePanel, { type Phase } from "@/components/SolvePanel";
import StreetCard from "@/components/StreetCard";
import TideBar from "@/components/TideBar";
import { loadScenario, solve } from "@/lib/api";
import { prefersReducedMotion } from "@/lib/hooks";
import type { Results, Scenario, SegProps, SolveResult } from "@/lib/types";
import type { Focus } from "@/components/MapView";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });
const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, prefersReducedMotion() ? 0 : ms));

export default function Page() {
  const [data, setData] = useState<{ scenario: Scenario; results: Results } | null>(null);
  const [offline, setOffline] = useState(false);
  const [threeD, setThreeD] = useState(true);
  const [bearing, setBearing] = useState(0);
  const [compassNonce, setCompassNonce] = useState(0);
  const [waterOn, setWaterOn] = useState(false);
  const [month, setMonth] = useState(0);
  const [budgetUnits, setBudgetUnits] = useState<number | null>(null);
  const [phase, setPhase] = useState<Phase>("idle");
  const [step, setStep] = useState(0);
  const [reveal, setReveal] = useState(0);
  const [result, setResult] = useState<SolveResult | null>(null);
  const [compare, setCompare] = useState(false);
  const [focus, setFocus] = useState<Focus | null>(null);
  const [selected, setSelected] = useState<SegProps | null>(null);
  const [how, setHow] = useState(false);
  const [sheet, setSheet] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = useRef(0);

  useEffect(() => {
    loadScenario().then((r) => {
      setData({ scenario: r.scenario, results: r.results });
      setOffline(r.offline);
      const peak = r.scenario.tide.reduce((b, t, i, a) => (t.level > a[b].level ? i : b), 0);
      setMonth(peak);
      setBudgetUnits(r.scenario.budget_range.default_units);
    });
  }, []);

  const resetSolve = useCallback(() => {
    run.current++;
    setPhase("idle"); setResult(null); setCompare(false); setFocus(null); setError(null);
  }, []);

  const onSolve = useCallback(async () => {
    if (!data || budgetUnits == null) return;
    const id = ++run.current;
    setPhase("solving"); setStep(0); setReveal(0); setResult(null); setCompare(false); setFocus(null); setError(null); setSelected(null);
    const units = budgetUnits;
    const [res] = await Promise.all([solve(units).catch(() => null), sleep(800)]);
    if (id !== run.current) return;
    if (!res) { setPhase("idle"); setError("The search could not run. Please try again."); return; }
    setStep(1); setResult(res.result); setOffline(res.offline);
    const t0 = performance.now(), dur = prefersReducedMotion() ? 1 : 1700;
    await new Promise<void>((done) => {
      const tick = (now: number) => {
        if (id !== run.current) return done();
        const t = Math.min(1, (now - t0) / dur);
        setReveal(t);
        t < 1 ? requestAnimationFrame(tick) : done();
      };
      requestAnimationFrame(tick);
    });
    if (id !== run.current) return;
    await sleep(500);
    if (id !== run.current) return;
    setStep(2);
    await sleep(1000);
    if (id !== run.current) return;
    setPhase("done");
    setFocus({ ids: res.result.plans.undertow.segments, nonce: Date.now() });
  }, [data, budgetUnits]);

  const done = phase === "done" && result;
  const undertowIds = useMemo(() => (done ? result.plans.undertow.segments : []), [done, result]);
  const todayIds = useMemo(() => (done ? result.plans.today.segments : []), [done, result]);

  if (!data || budgetUnits == null) return <div className="fixed inset-0 grid place-items-center text-sm muted">Loading…</div>;
  const { scenario, results } = data;

  return (
    <main>
      <MapView scenario={scenario} threeD={threeD} tideLevel={scenario.tide[month]?.level ?? 1} kingTide={!!scenario.tide[month]?.king_tide} waterOn={waterOn}
        undertowIds={undertowIds} todayIds={todayIds} compare={compare && !!done} selectedId={selected?.id ?? null}
        focus={focus} compassNonce={compassNonce} onSelect={setSelected} onBearing={setBearing} />

      <header className="pointer-events-none fixed left-4 top-4 z-10 md:left-10 md:top-9">
        <h1 className="text-[15px] font-normal tracking-[0.42em]">ROADQURE</h1>
        <div className="muted mt-1 text-[13px]">Miami Beach · hidden road damage</div>
      </header>
      <nav className="fixed right-4 top-4 z-20 flex items-center gap-4 text-[14px] md:right-10 md:top-9 md:gap-6">
        <span className="muted hidden sm:inline" title={scenario.data_note}>Demo data</span>
        <button onClick={() => setHow((v) => !v)} className="text-water hover:text-paper" aria-expanded={how}>How it works</button>
      </nav>

      <StreetCard seg={selected} onClose={() => setSelected(null)} />

      <div className={`scroll-hidden fixed inset-x-3 bottom-[224px] z-10 max-h-[calc(100dvh-350px)] ${sheet ? "flex" : "hidden md:flex"} flex-col gap-3 overflow-y-auto md:inset-x-auto md:bottom-24 md:right-8 md:top-[88px] md:max-h-none md:w-[400px] md:gap-4`}>
        <ControlPanel scenario={scenario} waterOn={waterOn} onWater={setWaterOn} budgetUnits={budgetUnits}
          onBudget={(u) => { setBudgetUnits(u); resetSolve(); }} solving={phase === "solving"} onSolve={onSolve} />
        <SolvePanel phase={phase} step={step} reveal={reveal} result={result} scenario={scenario} compare={compare} onCompare={setCompare} offline={offline} />
        {error && <p className="glass p-5 text-sm">{error}</p>}
      </div>

      <button onClick={() => setSheet((v) => !v)} aria-expanded={sheet}
        className="glass fixed bottom-[176px] left-4 z-10 !rounded-full px-5 py-2.5 text-sm md:hidden">{sheet ? "Hide controls ▾" : "Controls ▴"}</button>

      <TideBar scenario={scenario} month={month} onMonth={setMonth} compare={compare && !!done} />

      <div className="fixed right-4 top-[60px] z-10 flex items-center gap-2 md:bottom-8 md:right-8 md:top-auto md:gap-3">
        <div className="glass flex gap-1 !rounded-full p-1" role="group" aria-label="Map view">
          {["2D", "3D"].map((m) => (
            <button key={m} onClick={() => setThreeD(m === "3D")} aria-pressed={threeD === (m === "3D")}
              className={`rounded-full px-4 py-2.5 text-sm md:py-2 transition-colors duration-500 ${threeD === (m === "3D") ? "bg-paper text-ink" : "muted"}`}>{m}</button>
          ))}
        </div>
        <button onClick={() => setCompassNonce((n) => n + 1)} aria-label="Reset map rotation" className="glass grid h-11 w-11 place-items-center !rounded-full">
          <svg width="18" height="18" viewBox="0 0 24 24" style={{ transform: `rotate(${-bearing}deg)`, transition: "transform .3s" }} aria-hidden>
            <path d="M12 2l5 19-5-4-5 4z" fill="#f0efeb" />
          </svg>
        </button>
      </div>

      <HowItWorks open={how} onClose={() => setHow(false)} scenario={scenario} results={results} />
    </main>
  );
}
