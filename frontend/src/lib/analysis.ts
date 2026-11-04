// Derived, display-only statistics. Everything here is computed from data the
// backend already sends; nothing is estimated or invented on the client.
import type { Calibration, DiagnosticResult } from '../types';

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
  mean: number | null;
  median: number | null;
  min: number | null;
  max: number | null;
  belowLow: number;
  aboveHigh: number;
}

export function pplStats(results: DiagnosticResult[], calib: Calibration): PplStats {
  const values = results.map(r => r.ppl).filter((p): p is number => typeof p === 'number' && Number.isFinite(p));
  if (!values.length) return { count: 0, mean: null, median: null, min: null, max: null, belowLow: 0, aboveHigh: 0 };
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return {
    count: values.length,
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
  const withMetrics = results.filter(r => r.metrics);
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

/** Flagged sentences per issue type, most frequent first. */
export function issueBreakdown(results: DiagnosticResult[]): { type: string; count: number }[] {
  const counts = new Map<string, number>();
  for (const r of results) {
    if (r.status !== 'flagged') continue;
    const key = r.issue_type || 'unknown';
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  return [...counts.entries()].map(([type, count]) => ({ type, count })).sort((a, b) => b.count - a.count);
}

export type Level = '低' | '中' | '高';
export const riskLevel = (v: number): Level => (v >= 60 ? '高' : v >= 35 ? '中' : '低');

export const fmt = (n: number | null | undefined, digits = 1) =>
  typeof n === 'number' && Number.isFinite(n) ? n.toFixed(digits) : '—';

export const int = (n: number) => n.toLocaleString('zh-CN');
