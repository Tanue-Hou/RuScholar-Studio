import { DISCIPLINES, RISKS } from '../lib/labels';
import type { Phase, Risks } from '../hooks/useDiagnosis';

interface Props {
  phase: Phase;
  discipline: string;
  total: number;
  completed: number;
  flagged: number;
  styleRisk: number;
  avgPpl: number | null;
  risks: Risks;
}

const HIGH = 60;

export function Summary(p: Props) {
  const d = DISCIPLINES[p.discipline] ?? DISCIPLINES.UNIVERSAL;
  const running = p.phase === 'running' || p.phase === 'preparing';
  const pct = p.total ? Math.round((p.completed / p.total) * 100) : 0;

  return (
    <section className="aside-section" aria-labelledby="summary-title">
      <h2 className="eyebrow" id="summary-title">学科</h2>
      <p className="discipline">{d.zh}</p>
      <p className="meta">{d.ru}</p>

      {p.phase === 'preparing' && <p className="secondary" style={{ marginTop: 'var(--s4)' }}>正在识别学科并准备会话…</p>}

      {p.total > 0 && (
        <>
          <div className="figures">
            <div>
              <div className="eyebrow">需修改的句子</div>
              <div className={`figure-value ${p.styleRisk >= HIGH ? 'alert' : ''}`}>{p.styleRisk}%</div>
              <div className="meta num">{p.flagged} / {p.total} 句</div>
            </div>
            <div>
              <div className="eyebrow">平均困惑度</div>
              <div className="figure-value">{p.avgPpl === null ? '—' : p.avgPpl.toFixed(1)}</div>
              <div className="meta">{p.avgPpl === null ? '云端模式不计算' : '越低越像机器生成'}</div>
            </div>
          </div>

          {running && (
            <div className="progress" role="progressbar" aria-label="质检进度" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
              <div className="progress-fill" style={{ transform: `scaleX(${pct / 100})` }} />
            </div>
          )}

          <ul className="risk-list" aria-label="文风风险维度">
            {RISKS.map(r => {
              const v = p.risks[r.key];
              return (
                <li key={r.key} className="risk-row" title={r.hint}>
                  <span className="risk-label">{r.label}</span>
                  <span className="num">{v}%</span>
                  <span className="risk-track" aria-hidden>
                    <span className={`risk-fill ${v >= HIGH ? 'high' : ''}`} style={{ transform: `scaleX(${v / 100})`, display: 'block' }} />
                  </span>
                </li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
