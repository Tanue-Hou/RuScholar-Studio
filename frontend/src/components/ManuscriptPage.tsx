import { useEffect, useRef, useState } from 'react';
import type { DiagnosticResult } from '../types';
import type { Phase, ReferencesState } from '../hooks/useDiagnosis';

interface Props {
  fileName: string;
  documentText: string;
  phase: Phase;
  results: (DiagnosticResult | null)[];
  completed: number;
  noteNumbers: Map<number, number>;
  selected: number | null;
  onSelect: (index: number) => void;
  showPpl: boolean;
  onTogglePpl: () => void;
  references: ReferencesState;
  hasReferenceFiles: boolean;
  onReplace: () => void;
}

const REFERENCE_MODE: Record<ReferencesState, string> = {
  none: '引用核验：OpenAlex 摘要',
  uploading: '正在为参考文献建立索引…',
  indexed: '引用核验：本地文献全文',
  metadata: '引用核验：书目信息与 OpenAlex 摘要',
  failed: '文献索引失败，改用 OpenAlex 摘要',
};

export function ManuscriptPage(p: Props) {
  const refs = useRef(new Map<number, HTMLSpanElement>());
  const [confirming, setConfirming] = useState(false);

  useEffect(() => {
    if (p.selected !== null) {
      refs.current.get(p.selected)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [p.selected]);

  const analysed = p.results.length > 0;
  const running = p.phase === 'running' || p.phase === 'preparing';
  const referenceMode = p.references === 'none' && p.hasReferenceFiles ? '参考文献将在质检开始时建立索引' : REFERENCE_MODE[p.references];

  return (
    <article className="page" aria-label="手稿">
      <header className="page-head">
        <div style={{ minWidth: 0 }}>
          <h1 className="page-title">{p.fileName}</h1>
          <p className="meta" style={{ marginTop: 'var(--s1)' }}>{referenceMode}</p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--s1)', flex: 'none' }}>
          {analysed && (
            <button type="button" className="btn btn-quiet btn-sm" aria-pressed={p.showPpl} onClick={p.onTogglePpl}>
              {p.showPpl ? '隐藏困惑度' : '显示困惑度'}
            </button>
          )}
          <button type="button" className="btn btn-quiet btn-sm" disabled={running}
            onClick={() => (p.completed > 0 ? setConfirming(true) : p.onReplace())}>
            更换手稿
          </button>
        </div>
      </header>

      {confirming && (
        <div className="confirm" role="alert">
          <span className="confirm-text">更换手稿会清除「{p.fileName}」的 {p.completed} 条质检结果，且无法恢复。</span>
          <button type="button" className="btn btn-danger btn-sm" onClick={() => { setConfirming(false); p.onReplace(); }}>
            清除结果并更换
          </button>
          <button type="button" className="btn btn-quiet btn-sm" onClick={() => setConfirming(false)} autoFocus>
            保留结果
          </button>
        </div>
      )}

      {!analysed ? (
        <div className="manuscript" style={{ color: 'var(--ink-2)' }}>{p.documentText}</div>
      ) : (
        <div className="manuscript">
          {p.results.map((r, idx) => {
            if (!r) return null;
            const no = p.noteNumbers.get(idx);
            const flagged = r.status === 'flagged';
            const cls = ['s', flagged && 'flagged', p.selected === idx && 'selected'].filter(Boolean).join(' ');
            return (
              <span key={idx}>
                <span
                  ref={el => { if (el) refs.current.set(idx, el); else refs.current.delete(idx); }}
                  className={cls}
                  role="button"
                  tabIndex={flagged ? 0 : -1}
                  aria-label={flagged ? `批注 ${no}：${r.text}` : undefined}
                  onClick={() => p.onSelect(idx)}
                  onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); p.onSelect(idx); } }}
                >
                  {r.text}
                </span>
                {no !== undefined && <span className="note-mark" aria-hidden>{no}</span>}
                {p.showPpl && typeof r.ppl === 'number' && <span className="ppl-mark num" title="困惑度 (PPL)">{r.ppl}</span>}
                {' '}
              </span>
            );
          })}
          {running && p.completed < p.results.length && (
            <span className="s pending">
              {'\n\n'}正在分析第 {p.completed + 1} / {p.results.length} 句…
            </span>
          )}
        </div>
      )}
    </article>
  );
}
