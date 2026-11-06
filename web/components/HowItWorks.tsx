"use client";

import type { Results, Scenario } from "@/lib/types";

const NOTEBOOK = "https://github.com/KatharineRingo/Qiskit-Hackathon/blob/main/notebooks/undertow_qaoa.ipynb";

const STEPS: [string, string][] = [
  ["Find the hidden damage.", "King tides soak the ground under a road, so it fails from below before potholes show. We score every street from tide exposure, groundwater and elevation."],
  ["Count what a failure costs.", "A soaked road on an evacuation or hospital route matters more than one on a quiet street."],
  ["Search for the best repairs.", "With a limited budget, the best set of repairs is a puzzle with many possible answers. A quantum search explores them together and favors the good ones."],
  ["Check the answer.", "A classical computer solves the same puzzle, and we compare both with fixing the most-complained roads."],
];

export default function HowItWorks({ open, onClose, scenario, results }: { open: boolean; onClose: () => void; scenario: Scenario; results: Results }) {
  const bars = [
    { label: "Random guessing", v: results.random, c: "bg-white/30" },
    { label: "Quantum search, ideal", v: results.ideal, c: "bg-water" },
    { label: "Quantum search, real-chip noise", v: results.noisy, c: "bg-water/70" },
  ];
  const max = Math.max(...bars.map((b) => b.v));
  const q = scenario.optimizer.num_qubits;
  return (
    <aside role="dialog" aria-label="How it works" aria-hidden={!open}
      className={`glass fixed bottom-8 right-8 top-20 z-30 w-[440px] max-w-[calc(100vw-32px)] overflow-y-auto p-8 transition-all duration-700 ${open ? "translate-x-0 opacity-100" : "pointer-events-none translate-x-8 opacity-0"}`}>
      <div className="flex items-center justify-between">
        <h2 className="text-[22px] font-light">How it works</h2>
        <button onClick={onClose} aria-label="Close" className="muted text-2xl leading-none hover:text-paper">×</button>
      </div>
      <ol className="mt-5 space-y-4 text-[15px]">
        {STEPS.map(([t, d], i) => (
          <li key={t} className="flex gap-4"><span className="step-no pt-1">0{i + 1}</span><div><div className="font-medium">{t}</div><p className="muted mt-1 leading-snug">{d}</p></div></li>
        ))}
      </ol>
      <h3 className="mt-8 text-[15px] font-medium">How often each method finds a good plan</h3>
      <p className="muted mt-1 text-[13px]">Share of attempts that land on a near-best plan.</p>
      <div className="mt-3 space-y-3">
        {bars.map((b) => (
          <div key={b.label}>
            <div className="flex justify-between text-[13px]"><span>{b.label}</span><span className="muted tabular-nums">{b.v.toFixed(1)}%</span></div>
            <div className="mt-1 h-2 rounded bg-white/10"><div className={`h-2 rounded ${b.c}`} style={{ width: `${(b.v / max) * 100}%` }} /></div>
          </div>
        ))}
      </div>
      <h3 className="mt-8 text-[15px] font-medium">Honest limits</h3>
      <ul className="muted mt-2 list-disc space-y-1.5 pl-5 text-[14px] leading-snug">
        <li>Today this searches {q} qubits, a very small problem.</li>
        <li>A classical computer keeps up at this size, and we show that it agrees.</li>
        <li>Real quantum chips are still noisy, which is why the real-chip bar is lower.</li>
        <li>There is no guaranteed speedup. The goal is to show the method works and is ready to scale.</li>
        <li>{scenario.data_note}</li>
      </ul>
      <a href={NOTEBOOK} target="_blank" rel="noopener noreferrer" className="mt-6 inline-block text-[14px] text-water underline underline-offset-4">See the full analysis in the notebook</a>
    </aside>
  );
}
