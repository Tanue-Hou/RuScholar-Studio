// Derived, display-only statistics. Everything here is computed from data the
// backend already sends; nothing is estimated or invented on the client.
import type { Calibration, DiagnosticResult } from '../types';

const INFRA_TYPES = new Set(['api_request_error', 'json_parse_error']);

/** Prose sentences only: bibliography entries are not assessed and must not dilute statistics. */
export const bodyOf = (results: DiagnosticResult[]) => results.filter(r => !r.is_bibliography);

/** The judge failed for this sentence, so it was not assessed (not a pass). */
export const isUnjudged = (r: DiagnosticResult) =>
  r.status !== 'flagged' && (!!r.judge_error || INFRA_TYPES.has(r.issue_type ?? ''));

/** Issue types found in a flagged sentence (all of them, primary first). */
export function issueTypesOf(r: DiagnosticResult): string[] {
  if (r.status !== 'flagged') return [];
  const list = r.issues?.length ? r.issues.map(i => i.issue_type) : [r.issue_type ?? 'unknown'];
  return [...new Set(list.filter(Boolean))];
}

export const DEFAULT_CALIBRATION: Calibration = { ppl_low: 15, ppl_high: 80, nv_ratio_max: 4.5, passive_max: null };

export interface DocumentStats {
  characters: number;
  words: number;
  citations: number;
}

export function documentStats(text: string): DocumentStats {
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const citations = (text.match(/\[[^\]\n]{1,40}\]/g) ?? []).length;
  return { characters: text.length, words, citations };
}

export interface PplStats {
  count: number;
  /** How many of the values are early-exit prefix estimates. */
  prefix: number;
  mean: number | null;
  median: number | null;
  min: number | null;
  max: number | null;
  belowLow: number;
  aboveHigh: number;
}

export function pplStats(results: DiagnosticResult[], calib: Calibration): PplStats {
  const withPpl = bodyOf(results).filter(r => typeof r.ppl === 'number' && Number.isFinite(r.ppl));
  const values = withPpl.map(r => r.ppl as number);
  const prefix = withPpl.filter(r => r.ppl_basis === 'prefix').length;
  if (!values.length) return { count: 0, prefix: 0, mean: null, median: null, min: null, max: null, belowLow: 0, aboveHigh: 0 };
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return {
    count: values.length,
    prefix,
    mean: values.reduce((a, b) => a + b, 0) / values.length,
    median: sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    belowLow: values.filter(v => v < calib.ppl_low).length,
    aboveHigh: values.filter(v => v > calib.ppl_high).length,
  };
}

export interface LexicalTotals {
  sentences: number;
  meanNv: number | null;
  overNv: number;
  passive: number;
  genitiveChains: number;
  cliches: number;
  connectors: number;
}

export function lexicalTotals(results: DiagnosticResult[], calib: Calibration): LexicalTotals {
  const withMetrics = bodyOf(results).filter(r => r.metrics);
  const sum = (f: (r: DiagnosticResult) => number) => withMetrics.reduce((a, r) => a + f(r), 0);
  return {
    sentences: withMetrics.length,
    meanNv: withMetrics.length ? sum(r => r.metrics!.nv_ratio) / withMetrics.length : null,
    overNv: withMetrics.filter(r => r.metrics!.nv_ratio > calib.nv_ratio_max).length,
    passive: sum(r => r.metrics!.passive_count),
    genitiveChains: sum(r => r.metrics!.genitive_chains_count),
    cliches: sum(r => r.metrics!.cliches_count),
    connectors: sum(r => r.metrics!.connectors_count ?? 0),
  };
}

/**
 * Sentences per issue type, most frequent first. A sentence with several
 * findings counts once under each of its types (it used to count only under
 * its first, which hid e.g. AI features behind translationese).
 */
export function issueBreakdown(results: DiagnosticResult[]): { type: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const r of bodyOf(results)) {
    for (const key of issueTypesOf(r)) counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()].map(([type, count]) => ({ type, count })).sort((a, b) => b.count - a.count);
}

export type Level = '低' | '中' | '高';
export const riskLevel = (v: number): Level => (v >= 60 ? '高' : v >= 35 ? '中' : '低');

export const fmt = (n: number | null | undefined, digits = 1) =>
  typeof n === 'number' && Number.isFinite(n) ? n.toFixed(digits) : '—';

export const int = (n: number) => n.toLocaleString('zh-CN');
