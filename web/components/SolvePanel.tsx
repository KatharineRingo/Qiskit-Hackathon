"use client";

import { Switch } from "./ControlPanel";
import DotGrid from "./DotGrid";
import { fmtPct, useCountUp, usd } from "@/lib/hooks";
import type { Scenario, SolveResult } from "@/lib/types";

export type Phase = "idle" | "solving" | "done";

interface Props {
  phase: Phase;
  step: number;            // 0..2 while solving
  reveal: number;          // 0..1 dot grid reveal
  result: SolveResult | null;
  scenario: Scenario;
  compare: boolean;
  onCompare: (v: boolean) => void;
  offline: boolean;
}

function Dot({ done, active }: { done: boolean; active: boolean }) {
  return <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full transition-all duration-500 ${done ? "bg-water" : active ? "bg-paper shadow-[0_0_10px_2px_rgba(240,239,235,.6)]" : "bg-white/20"}`} />;
}

export default function SolvePanel({ phase, step, reveal, result, scenario, compare, onCompare, offline }: Props) {
  const target = result?.headline.undertow ?? 0;
  const shown = useCountUp(phase === "done" ? target : 0);
  if (phase === "idle") return null;
  const q = result?.num_qubits ?? scenario.optimizer.num_qubits;
  const steps = ["Building the puzzle", `Quantum search · ${q} qubits`, "Checking with a classical computer"];

  if (phase === "solving" || !result) {
    return (
      <section className="glass fade-up p-7" aria-live="polite" aria-label="Searching">
        <ol className="space-y-3 text-[15px]">
          {steps.map((s, i) => (
            <li key={s} className={`flex items-start gap-3 transition-opacity duration-500 ${i > step ? "opacity-40" : ""}`}>
              <Dot done={i < step} active={i === step} /><span>{s}</span>
            </li>
          ))}
        </ol>
        {result && (
          <div className="mt-5">
            <DotGrid counts={result.counts} bestState={result.best_state} reveal={reveal} />
            <p className="muted mt-2 text-xs">Each dot is one possible plan. Brighter means the quantum search found it more often.</p>
          </div>
        )}
      </section>
    );
  }

  const rows = result.plans.undertow.segments
    .map((id) => scenario.segments.features.find((f) => f.properties.id === id)!.properties)
    .sort((a, b) => a.street.localeCompare(b.street) || a.block.localeCompare(b.block));
  return (
    <section className="glass fade-up p-7" aria-live="polite" aria-label="Result">
      <div className="step-no uppercase">{result.headline.label}</div>
      <div className="mt-1 flex items-start gap-3">
        <div className="text-[84px] font-light leading-none tabular-nums tracking-tight">{fmtPct(shown)}<span className="text-[36px]">%</span></div>
        <p className="muted mt-3 text-[13px] leading-snug">vs. {fmtPct(result.headline.today)}% fixing the most-complained roads</p>
      </div>
      <ul className="mt-5 divide-y divide-white/10 text-[15px]">
        {rows.map((r) => (
          <li key={r.id} className="flex justify-between gap-3 py-2">
            <span>{r.street}{r.block !== "full length" && <span className="muted"> · {r.block}</span>}</span>
            <span className="muted shrink-0">{usd(r.crew_days * scenario.budget_range.dollars_per_crew_day)}</span>
          </li>
        ))}
      </ul>
      <label className="mt-4 flex items-center justify-between gap-4 text-[15px]">
        <span>Compare with today&apos;s approach</span><Switch on={compare} onChange={onCompare} label="Compare with today's approach" />
      </label>
      <p className="muted mt-4 text-[13px]">
        {result.classical_match ? "✓ Chosen by quantum search · confirmed by a classical computer" : "Chosen by quantum search · a classical computer found a slightly better plan"}
      </p>
      {offline && <p className="muted mt-2 text-[11px] opacity-70">offline mode</p>}
    </section>
  );
}
