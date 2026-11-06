import { useEffect, useRef, useState } from "react";

export const prefersReducedMotion = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Animates a number toward `value`. */
export function useCountUp(value: number, ms = 1100): number {
  const [shown, setShown] = useState(0);
  const from = useRef(0);
  useEffect(() => {
    if (prefersReducedMotion()) { setShown(value); from.current = value; return; }
    const start = performance.now(), a = from.current;
    let raf = 0;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms), e = 1 - Math.pow(1 - t, 3);
      const v = a + (value - a) * e;
      from.current = v; setShown(v);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, ms]);
  return shown;
}

export const fmtPct = (v: number) => (v > 0 && v < 10 ? v.toFixed(1) : v.toFixed(0));
export const days = (n: number) => `${n} ${n === 1 ? "day" : "days"}`;
export const usd = (n: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(n);
