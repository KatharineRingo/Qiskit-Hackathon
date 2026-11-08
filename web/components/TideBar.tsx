"use client";

import type { Scenario } from "@/lib/types";

const FULL = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

export default function TideBar({ scenario, month, onMonth, compare }: { scenario: Scenario; month: number; onMonth: (i: number) => void; compare: boolean }) {
  const t = scenario.tide, cur = t[month];
  const first = t.findIndex((x) => x.king_tide);
  const last = t.length - 1 - [...t].reverse().findIndex((x) => x.king_tide);
  const pct = (i: number) => ((i + 0.5) / t.length) * 100;
  return (
    <div className="fixed inset-x-4 bottom-9 z-10 md:inset-x-auto md:bottom-8 md:left-10 md:w-[min(560px,calc(100vw-520px))] md:min-w-[340px]">
      <div className="muted mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[12px] md:mb-5 md:gap-x-6 md:text-[13px]">
        <span className="flex items-center gap-2"><i className="h-[3px] w-5 rounded bg-dmg" />Hidden damage</span>
        <span className="flex items-center gap-2"><i className="h-[3px] w-5 rounded bg-white" />RoadQure repairs</span>
        {compare && <span className="flex items-center gap-2"><i className="h-[3px] w-5 rounded bg-today" />Today&apos;s approach</span>}
        <span className="hidden items-center gap-2 md:flex"><i className="w-5 border-t border-dashed border-paper/80" />Evacuation route</span>
        <span className="hidden items-center gap-2 md:flex"><i className="grid h-4 w-4 place-items-center rounded-full bg-paper text-[10px] font-semibold not-italic text-water">H</i>Hospital</span>
      </div>
      <div className="flex items-end justify-between">
        <div className="text-[32px] font-light md:text-[44px] leading-none tracking-tight">{FULL[month]}</div>
        <div className={`pb-1 text-right text-[12px] md:text-[14px] ${cur.king_tide ? "text-water" : "muted"}`}>{cur.king_tide ? "King tide · water in the road base" : "Normal tides"}</div>
      </div>
      <div className="relative mt-3">
        {first >= 0 && <div className="absolute top-[13px] h-[3px] rounded bg-dmg/70" style={{ left: `${pct(first)}%`, width: `${pct(last) - pct(first)}%` }} title="King tide season" />}
        <input type="range" min={0} max={t.length - 1} step={1} value={month} onChange={(e) => onMonth(Number(e.target.value))}
          aria-label="Month" aria-valuetext={`${FULL[month]}, ${cur.king_tide ? "king tide" : "normal tides"}`} />
        <div className="relative mt-1 h-4 font-mono text-[11px] text-paper/60">
          {t.map((x, i) => <span key={x.month} className={`absolute -translate-x-1/2 ${i === month ? "text-paper" : ""}`} style={{ left: `${pct(i)}%` }}>{x.month[0]}</span>)}
        </div>
      </div>
    </div>
  );
}
