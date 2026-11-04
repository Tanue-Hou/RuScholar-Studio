import { FILTERS, categoryOf, issueTitle, type NoteFilter } from '../lib/labels';
import type { DiagnosticResult } from '../types';

interface Props {
  items: DiagnosticResult[];
  warnings: DiagnosticResult[];
  noteNumbers: Map<number, number>;
  filter: NoteFilter;
  onFilter: (f: NoteFilter) => void;
  onSelect: (index: number) => void;
  running: boolean;
}

export function NoteList(p: Props) {
  const counts: Record<NoteFilter, number> = { all: 0, ai: 0, style: 0, citation: 0, passed: 0 };
  for (const d of p.items) {
    const c = categoryOf(d);
    counts[c]++;
    if (c !== 'passed') counts.all++;
  }
  counts.citation += p.warnings.length;
  counts.all += p.warnings.length;

  // "全部批注" lists annotations only; passed sentences have their own filter.
  const visible = p.items.filter(d => {
    const c = categoryOf(d);
    return p.filter === 'all' ? c !== 'passed' : c === p.filter;
  });
  const showWarnings = (p.filter === 'all' || p.filter === 'citation') && p.warnings.length > 0;

  return (
    <section className="aside-section" aria-labelledby="notes-title">
      <h2 className="eyebrow" id="notes-title">批注</h2>
      <div className="filters" role="group" aria-label="筛选批注">
        {FILTERS.map(f => (
          <button key={f.value} type="button" className="filter" aria-pressed={p.filter === f.value} onClick={() => p.onFilter(f.value)}>
            {f.label} <span className="num">{counts[f.value]}</span>
          </button>
        ))}
      </div>

      {showWarnings && (
        <ul className="notes" aria-label="全文引用完整性">
          {p.warnings.map((w, i) => (
            <li key={`w${i}`} className="note">
              <div className="note-btn" style={{ cursor: 'default' }}>
                <span className="note-no" aria-hidden>§</span>
                <span>
                  <span className="note-title">{w.explanation}</span>
                  {w.suggestion && w.suggestion !== '-' && <span className="note-excerpt" style={{ fontFamily: 'var(--font-sans)' }}>{w.suggestion}</span>}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}

      {visible.length > 0 ? (
        <ul className="notes">
          {visible.map(d => {
            const no = p.noteNumbers.get(d.index);
            const passed = d.status !== 'flagged';
            return (
              <li key={d.index} className="note">
                <button type="button" className="note-btn" onClick={() => p.onSelect(d.index)}>
                  <span className={`note-no ${passed ? 'muted' : ''}`}>{passed ? '✓' : no}</span>
                  <span style={{ minWidth: 0 }}>
                    <span className="note-title">{passed ? '无需修改' : issueTitle(d.issue_type)}</span>
                    <span className="note-excerpt">{d.text}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      ) : !showWarnings && (
        <p className="meta empty">
          {p.running ? '批注会随分析逐条出现。'
            : p.filter === 'all' ? '没有需要修改的地方。'
            : '此类别下没有条目。'}
        </p>
      )}
    </section>
  );
}
