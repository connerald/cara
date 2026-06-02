export type RiskLevel = "high" | "medium" | "low" | string;

export interface MetricResponse {
  key: string;
  name: string;
  value: number;
  unit: string | null;
  source_text: string | null;
  line_number: number | null;
}

export interface FindingResponse {
  area: string;
  level: RiskLevel;
  title: string;
  description: string;
  evidence: string[];
  metrics: Record<string, number | string>;
}

export interface ReportSnapshotResponse {
  company_name: string | null;
  report_period: string | null;
  report_type: string | null;
  source_path: string | null;
  raw_text_chars: number;
}

export interface ReportAnalysisResponse {
  snapshot: ReportSnapshotResponse;
  metrics: MetricResponse[];
  findings: FindingResponse[];
  score: number;
  summary_counts: Record<string, number>;
  markdown: string;
  ai_summary: string | null;
}
