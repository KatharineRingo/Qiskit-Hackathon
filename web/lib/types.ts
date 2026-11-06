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
  geometry: {
    type: "LineString";
    coordinates: [number, number][];
  };
  properties: SegProps;
}

export interface Scenario {
  demo: boolean;
  data_note: string;
  center: [number, number];
  bounds: [[number, number], [number, number]];
  bearing: number;
  segments: {
    type: "FeatureCollection";
    features: SegFeature[];
  };
  route: {
    type: "FeatureCollection";
    features: SegFeature[];
  };
  hospital: {
    name: string;
    coord: [number, number];
  };
  water: {
    type: "FeatureCollection";
    features: any[];
  };
  tide: {
    month: string;
    level: number;
    king_tide: boolean;
  }[];
  budgets: {
    key: string;
    label: string;
    units: number;
  }[];
  optimizer: {
    candidates: string[];
    num_qubits: number;
  };
  crew_day_label: string;
}

export interface Results {
  random: number;
  ideal: number;
  noisy: number;
}

export interface PlanMetrics {
  evac_open_pct: number;
  hospital_open_pct: number;
  failures_avoided: number;
  expected_failures: number;
  crew_days: number;
}

export interface Plan {
  segments: string[];
  metrics: PlanMetrics;
}

export interface Headline {
  key: string;
  label: string;
  undertow: number;
  today: number;
}

export interface TopSample {
  bits: string;
  count: number;
  feasible: boolean;
}

export interface SolveResult {
  budget_units: number;
  plans: {
    undertow: Plan;
    today: Plan;
  };
  headline: Headline;
  candidates: string[];
  counts: number[];
  best_state: number;
  top_samples: TopSample[];
  num_qubits: number;
  shots: number;
  classical_match: boolean;
  solve_ms: number;
  price: number;
}
