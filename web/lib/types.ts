export type Coord = [number, number];

export interface SegProps {
  id: string;
  street: string;
  block: string;
  risk: number;
  risk_word: string;
  reason: string;
  complaints: number;
  evac: boolean;
  hospital: boolean;
  crew_days: number;
}
export interface SegFeature {
  type: "Feature";
  geometry: { type: "LineString"; coordinates: Coord[] };
  properties: SegProps;
}
export interface PolyFeature {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: Coord[][] };
  properties: { level: number; elevation_ft: number; segment: string };
}

export interface Scenario {
  demo: boolean;
  data_note: string;
  center: Coord;
  bounds: [Coord, Coord];
  bearing: number;
  segments: { features: SegFeature[] };
  route: { features: SegFeature[] };
  hospital: { name: string; coord: Coord };
  water: { features: PolyFeature[] };
  tide: { month: string; level: number; king_tide: boolean }[];
  budgets: { key: string; label: string; units: number }[];
  budget_range: { min_units: number; max_units: number; default_units: number; dollars_per_crew_day: number };
  optimizer: { candidates: string[]; num_qubits: number };
  crew_day_label: string;
}

export interface PlanMetrics {
  evac_open_pct: number;
  hospital_open_pct: number;
  failures_avoided: number;
  expected_failures: number;
  crew_days: number;
}
export interface SolveResult {
  budget_units: number;
  plans: { undertow: { segments: string[]; metrics: PlanMetrics }; today: { segments: string[]; metrics: PlanMetrics } };
  headline: { key: string; label: string; undertow: number; today: number };
  candidates: string[];
  counts: number[];
  best_state: number;
  top_samples: { bits: string; count: number; feasible: boolean }[];
  num_qubits: number;
  shots: number;
  classical_match: boolean;
  solve_ms: number;
}
export interface Results {
  random: number;
  ideal: number;
  noisy: number;
}
export interface Fallback {
  scenario: Scenario;
  results: Results;
  solves: Record<string, SolveResult>;
}
