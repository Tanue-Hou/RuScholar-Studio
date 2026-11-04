// Shapes of the backend's /api responses and SSE events (see services/diagnostic_service.py).

export type EngineType = 'local' | 'hybrid-pro' | 'hybrid-flash' | 'cloud-pro' | 'cloud-flash';

export type SentenceStatus = 'ok' | 'early_exit' | 'passed' | 'flagged';

export interface SentenceMetrics {
  nv_ratio: number;
  passive_count: number;
  genitive_chains_count: number;
  cliches_count: number;
  connectors_count?: number;
}

export type AuditStatus = 'SUPPORTED' | 'CONTRADICTED' | 'NOT_ENOUGH_INFO' | 'AUDIT_FAILED';

export interface CitationAudit {
  key: string;
  title: string;
  author: string;
  year: string;
  status: AuditStatus;
  explanation_zh: string;
  evidence_snippet: string;
  think?: string | null;
  source: 'local' | 'online';
}

export interface RiskScores {
  predictability_risk: number;
  uniformity_risk: number;
  translationese_risk: number;
  redundancy_risk: number;
}

/** One "result" event. index < 0 marks a document-level citation-integrity warning. */
export interface DiagnosticResult extends Partial<RiskScores> {
  index: number;
  text: string;
  ppl: number | null;
  issue_type: string | null;
  severity: string | null;
  explanation: string | null;
  suggestion: string | null;
  think: string | null;
  status: SentenceStatus;
  metrics?: SentenceMetrics | null;
  citation_audit?: CitationAudit[];
}

export interface InitEvent {
  total_sentences: number;
  discipline: string;
  nlp_backend?: 'spacy' | 'fallback';
}

export type ModelStatus = 'checking' | 'exists' | 'missing' | 'downloading';

export interface EngineSettings {
  engineType: EngineType;
  apiKey: string;
  baseUrl: string;
}
