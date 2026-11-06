import { useEffect, useState } from "react";

export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function fmtPct(v: number): string {
  return v % 1 === 0 ? String(v) : v.toFixed(1);
}

export function days(n: number): string {
  return `${n} ${n === 1 ? "crew-day" : "crew-days"}`;
}

export function useCountUp(target: number, durationMs = 800): number {
  const [val, setVal] = useState(target);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setVal(target);
      return;
    }
    const start = val;
    const diff = target - start;
    if (diff === 0) return;

    const t0 = performance.now();
    let frameId: number;

    const step = (now: number) => {
      const elapsed = now - t0;
      const progress = Math.min(1, elapsed / durationMs);
      const eased = 1 - Math.pow(1 - progress, 3);
      setVal(Math.round((start + diff * eased) * 10) / 10);
      if (progress < 1) {
        frameId = requestAnimationFrame(step);
      } else {
        setVal(target);
      }
    };

    frameId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frameId);
  }, [target]);

  return val;
}
