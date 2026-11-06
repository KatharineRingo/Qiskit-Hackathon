"use client";

import type { Scenario } from "@/lib/types";

interface Props {
  scenario: Scenario;
  waterOn: boolean;
  onWater: (v: boolean) => void;
  budgetIdx: number;
  onBudget: (i: number) => void;
  solving: boolean;
  onSolve: () => void;
}

export function Switch({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button role="switch" aria-checked={on} aria-label={label} onClick={() => onChange(!on)}
      className={`relative h-6 w-11 shrink-0 rounded-full transition-colors duration-500 ${on ? "bg-water" : "bg-white/15"}`}>
      <span className={`absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-paper transition-transform duration-500 ${on ? "translate-x-5" : ""}`} />
    </button>
  );
}

export default function ControlPanel({ scenario, waterOn, onWater, budgetIdx, onBudget, solving, onSolve }: Props) {
  const b = scenario.budgets[budgetIdx];
  return (
    <section className="glass p-7" aria-label="Controls">
      <div className="flex items-baseline gap-3"><span className="step-no">01</span><h2 className="text-[17px] font-medium">Hidden damage</h2></div>
      <p className="muted mt-3 text-[15px] leading-snug">Orange streets look fine on top but soak from below at high tide.</p>
      <label className="mt-4 flex items-center justify-between gap-4 text-[15px]">
        <span>See the water underneath</span><Switch on={waterOn} onChange={onWater} label="See the water underneath" />
      </label>

      <hr className="my-6 border-white/10" />
      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-3"><span className="step-no">02</span><h2 className="text-[17px] font-medium">Repair budget</h2></div>
        <span className="muted text-sm">{b.units} {scenario.crew_day_label}</span>
      </div>
      <div className="mt-4 grid grid-cols-4 rounded-2xl bg-white/[0.07] p-1" role="group" aria-label="Repair budget">
        {scenario.budgets.map((x, i) => (
          <button key={x.key} onClick={() => onBudget(i)} aria-pressed={i === budgetIdx}
            className={`rounded-xl py-2 text-sm transition-colors duration-500 ${i === budgetIdx ? "bg-paper font-medium text-ink" : "muted hover:text-paper"}`}>{x.label}</button>
        ))}
      </div>

      <hr className="my-6 border-white/10" />
      <div className="flex items-baseline gap-3"><span className="step-no">03</span><h2 className="text-[17px] font-medium">Best repairs</h2></div>
      <button className="btn mt-4 w-full" onClick={onSolve} disabled={solving}>{solving ? "Searching…" : "Find the best repairs"}</button>
    </section>
  );
}
