"use client";

/** One dot per possible plan (2^n), lit by how often the quantum search sampled it. `reveal` (0-1) fades dots in. */
export default function DotGrid({ counts, bestState, reveal }: { counts: number[]; bestState: number; reveal: number }) {
  const side = Math.ceil(Math.sqrt(counts.length));
  const max = Math.max(1, ...counts);
  const step = 11;
  return (
    <svg viewBox={`0 0 ${side * step} ${side * step}`} className="w-full" role="img"
      aria-label={`${counts.length} possible repair plans, brightness shows how often the quantum search found each one`}>
      {counts.map((c, i) => {
        const x = (i % side) * step + step / 2, y = Math.floor(i / side) * step + step / 2;
        const order = ((i * 2654435761) % 4294967296) / 4294967296;   // fixed pseudo-random reveal order
        const on = order <= reveal;
        const b = Math.sqrt(c / max);
        const best = i === bestState;
        return (
          <g key={i} style={{ opacity: on ? 1 : 0, transition: "opacity .5s" }}>
            <circle cx={x} cy={y} r={best ? 4.6 : 1.1 + b * 2.6} fill={best ? "#ffffff" : "#4b93ff"} fillOpacity={best ? 1 : 0.12 + b * 0.88} />
            {best && <circle cx={x} cy={y} r={7.5} fill="none" stroke="#4b93ff" strokeOpacity={0.8} />}
          </g>
        );
      })}
    </svg>
  );
}
