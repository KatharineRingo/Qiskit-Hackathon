"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { loadScenario } from "@/lib/api";
import type { Scenario } from "@/lib/types";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function Page() {
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [threeD, setThreeD] = useState(true);
  useEffect(() => { loadScenario().then((r) => setScenario(r.scenario)); }, []);
  if (!scenario) return <div className="fixed inset-0 grid place-items-center muted">Loading…</div>;
  return (
    <main>
      <MapView scenario={scenario} threeD={threeD} tideLevel={1} waterOn={false} undertowIds={[]} todayIds={[]} compare={false}
        selectedId={null} focus={null} compassNonce={0} onSelect={() => {}} onBearing={() => {}} />
      <div className="fixed left-10 top-9 z-10">
        <div className="text-[15px] font-normal tracking-[0.42em]">UNDERTOW</div>
        <div className="muted mt-1 text-[13px]">Miami Beach · hidden road damage</div>
      </div>
      <div className="glass fixed bottom-8 right-8 z-10 flex gap-1 p-1 !rounded-full">
        {["2D", "3D"].map((m) => (
          <button key={m} onClick={() => setThreeD(m === "3D")} aria-pressed={threeD === (m === "3D")}
            className={`rounded-full px-4 py-2 text-sm ${threeD === (m === "3D") ? "bg-paper text-ink" : "muted"}`}>{m}</button>
        ))}
      </div>
    </main>
  );
}
