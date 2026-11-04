import { useCallback, useMemo, useReducer, useRef } from 'react';
import {
  createSession, detectDiscipline, openDiagnosisStream, uploadReferences,
} from '../api/client';
import type { DiagnosticResult, EngineSettings, InitEvent, RiskScores } from '../types';

export type Phase = 'idle' | 'preparing' | 'running' | 'done' | 'stopped' | 'error';
export type ReferencesState = 'none' | 'uploading' | 'indexed' | 'failed';

export interface Risks {
  predictability: number;
  uniformity: number;
  translationese: number;
  redundancy: number;
}

interface State {
  phase: Phase;
  error: string | null;
  discipline: string;
  nlpBackend: 'spacy' | 'fallback';
  references: ReferencesState;
  /** One slot per sentence; null until its result arrives. */
  results: (DiagnosticResult | null)[];
  /** Document-level citation-integrity warnings (index < 0). */
  warnings: DiagnosticResult[];
  risks: Risks;
}

const ZERO_RISKS: Risks = { predictability: 0, uniformity: 0, translationese: 0, redundancy: 0 };

const initialState: State = {
  phase: 'idle',
  error: null,
  discipline: 'UNIVERSAL',
  nlpBackend: 'spacy',
  references: 'none',
  results: [],
  warnings: [],
  risks: ZERO_RISKS,
};

type Action =
  | { type: 'reset' }
  | { type: 'preparing' }
  | { type: 'discipline'; discipline: string }
  | { type: 'references'; state: ReferencesState }
  | { type: 'init'; data: InitEvent }
  | { type: 'result'; data: DiagnosticResult }
  | { type: 'done'; risks: Partial<RiskScores> }
  | { type: 'stopped' }
  | { type: 'error'; message: string };

function toRisks(r: Partial<RiskScores>, fallback: Risks): Risks {
  const pick = (v: number | undefined, f: number) => (typeof v === 'number' ? Math.round(v) : f);
  return {
    predictability: pick(r.predictability_risk, fallback.predictability),
    uniformity: pick(r.uniformity_risk, fallback.uniformity),
    translationese: pick(r.translationese_risk, fallback.translationese),
    redundancy: pick(r.redundancy_risk, fallback.redundancy),
  };
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'reset':
      return initialState;
    case 'preparing':
      return { ...initialState, phase: 'preparing' };
    case 'discipline':
      return { ...state, discipline: action.discipline };
    case 'references':
      return { ...state, references: action.state };
    case 'init':
      return {
        ...state,
        phase: 'running',
        nlpBackend: action.data.nlp_backend === 'fallback' ? 'fallback' : 'spacy',
        results: Array(action.data.total_sentences).fill(null),
      };
    case 'result': {
      const d = action.data;
      // Integrity warnings are emitted before sentences with risks fixed at 0;
      // they must not reset the running document risks.
      if (d.index < 0) return { ...state, warnings: [...state.warnings, d] };
      const results = state.results.slice();
      results[d.index] = d;
      return { ...state, results, risks: toRisks(d, state.risks) };
    }
    case 'done':
      return { ...state, phase: 'done', risks: toRisks(action.risks, state.risks) };
    case 'stopped':
      return { ...state, phase: 'stopped' };
    case 'error':
      return { ...state, phase: 'error', error: action.message };
  }
}

export interface StartOptions {
  text: string;
  engine: EngineSettings;
  bibtex: File | null;
  referenceDocs: File[];
}

export function useDiagnosis() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const closeRef = useRef<(() => void) | null>(null);

  const stop = useCallback(() => {
    closeRef.current?.();
    closeRef.current = null;
    dispatch({ type: 'stopped' });
  }, []);

  const reset = useCallback(() => {
    closeRef.current?.();
    closeRef.current = null;
    dispatch({ type: 'reset' });
  }, []);

  const start = useCallback(async ({ text, engine, bibtex, referenceDocs }: StartOptions) => {
    closeRef.current?.();
    dispatch({ type: 'preparing' });

    let discipline = 'UNIVERSAL';
    try {
      discipline = await detectDiscipline(text, engine);
    } catch {
      // keep UNIVERSAL; the backend also falls back to keywords
    }
    dispatch({ type: 'discipline', discipline });

    let sessionId: string;
    try {
      sessionId = await createSession(text, discipline, engine);
    } catch (err) {
      dispatch({ type: 'error', message: `无法创建质检会话：${err instanceof Error ? err.message : err}。请确认后端服务正在运行。` });
      return;
    }

    if (bibtex || referenceDocs.length > 0) {
      dispatch({ type: 'references', state: 'uploading' });
      try {
        await uploadReferences(sessionId, bibtex, referenceDocs);
        dispatch({ type: 'references', state: 'indexed' });
      } catch {
        // Diagnosis still runs; citations fall back to OpenAlex abstracts.
        dispatch({ type: 'references', state: 'failed' });
      }
    }

    closeRef.current = openDiagnosisStream(sessionId, {
      onInit: data => dispatch({ type: 'init', data }),
      onResult: data => dispatch({ type: 'result', data }),
      onDone: risks => {
        closeRef.current = null;
        dispatch({ type: 'done', risks });
      },
      onError: message => {
        closeRef.current = null;
        dispatch({ type: 'error', message: message ?? '与后端的连接中断，质检未完成。可以重新开始质检。' });
      },
    });
  }, []);

  const summary = useMemo(() => {
    const done = state.results.filter((r): r is DiagnosticResult => r !== null);
    const ppls = done.map(r => r.ppl).filter((p): p is number => typeof p === 'number' && !Number.isNaN(p));
    const flagged = done.filter(r => r.status === 'flagged').length;
    return {
      total: state.results.length,
      completed: done.length,
      flagged,
      styleRisk: state.results.length ? Math.round((flagged / state.results.length) * 100) : 0,
      avgPpl: ppls.length ? ppls.reduce((a, b) => a + b, 0) / ppls.length : null,
    };
  }, [state.results]);

  return { ...state, summary, start, stop, reset };
}
