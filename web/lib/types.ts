// Mirrors the JSON shapes written by scripts/export_dashboard_data.py.
// Keep in sync with that script's _write_json payloads.

export type Period = "Q1" | "Q2" | "Q3";
export const PERIODS: Period[] = ["Q1", "Q2", "Q3"];

export type ConceptCategory =
  | "accounting_fact"
  | "abstract_header"
  | "dimensional"
  | "dei";

export interface GraphNode {
  id: string;
  label: string;
  category: ConceptCategory;
  isCustom: boolean;
  pagerank: number;
  degree: number;
  industry: string | null;
  sizeClass: string | null;
  complexity: number | null;
  x: number;
  y: number;
  driftNext: number | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
  layer: "structural" | "co_reporting";
}

export interface GraphData {
  period: Period;
  nodeCount: number;
  edgeCount: number;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface OverviewMetric {
  id: string;
  label: string;
  sublabel: string;
  q1q2: number | null;
  q2q3: number | null;
  q3?: number;
  decelerating: boolean | null;
}

export interface OverviewData {
  headline: string;
  counterIntuitive: string;
  metrics: OverviewMetric[];
  datasetStats: { period: Period; concepts: number; edges: number; entities: number }[];
  rawVsAlignedDrift: { raw: number; aligned: number };
}

export interface SegmentationGroup {
  group: string;
  mean: number;
  n: number;
}

export interface RegressionTerm {
  term: string;
  coef: number;
  stdErr: number;
  pValue: number;
  significant: boolean;
}

export interface SegmentationData {
  sampleSize: number;
  regressionFormula: string;
  byIndustry: SegmentationGroup[];
  bySize: SegmentationGroup[];
  byComplexity: SegmentationGroup[];
  centralityVsDrift: { conceptId: string; pagerank: number; drift: number }[];
  regression: RegressionTerm[];
  customVsStandard: {
    drift: { isCustom: boolean; mean: number; n: number }[];
    weightedDegree: { isCustom: boolean; mean: number; n: number }[];
  };
}

export type FindingStatus = "answered" | "partial" | "open";

export interface FindingQuestion {
  number: string;
  status: FindingStatus;
  text: string;
}

export interface FindingSection {
  letter: string;
  title: string;
  questions: FindingQuestion[];
}

export interface FindingsData {
  sections: FindingSection[];
  totalQuestions: number;
  answeredQuestions: number;
}
