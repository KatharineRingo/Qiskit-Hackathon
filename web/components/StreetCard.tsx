"use client";

import type { SegProps } from "@/lib/types";

export default function StreetCard({ seg, onClose }: { seg: SegProps | null; onClose: () => void }) {
  if (!seg) return null;
  return (
    <aside className="glass fade-up fixed inset-x-3 top-[108px] z-10 p-5 md:inset-x-auto md:left-10 md:top-28 md:w-[320px] md:p-6" aria-live="polite">
      <button onClick={onClose} aria-label="Close" className="muted absolute right-5 top-4 text-xl leading-none hover:text-paper">×</button>
      <h3 className="pr-6 text-[17px] font-medium">{seg.street}</h3>
      {seg.block !== "full length" && <div className="muted text-[13px]">{seg.block}</div>}
      <div className="mt-3 text-[15px] text-dmg">{seg.risk_word} hidden damage</div>
      <p className="muted mt-2 text-[14px] leading-snug">{seg.reason}</p>
      <div className="muted mt-3 text-[13px]">{seg.complaints} {seg.complaints === 1 ? "complaint" : "complaints"} in the last year</div>
    </aside>
  );
}
