import { useState } from 'react';
import { ISSUE_ORDER, issueMeta, issueTitle } from '../lib/issues';
import type { Calibration, DiagnosticResult } from '../types';

interface Props {
  /** One slot per sentence; null while pending. */
  results: (DiagnosticResult | null)[];
  calibration: Calibration;
  selected: number | null;
  onSelect: (index: number) => void;
}

const W = 400;
const H = 96;
const PAD_TOP = 6;

/**
 * Per-sentence perplexity, in reading order. One bar per sentence, coloured by
 * issue type (palette slot + legend label + tooltip, never colour alone); dashed lines mark
 * the discipline's calibrated PPL bounds. Hover shows the value, click selects.
 */
export function PplStrip({ results, calibration, selected, onSelect }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  // Bibliography entries are not prose and have no PPL: leave them out.
  const slots = results
    .map((r, index) => ({ r, index }))
    .filter(({ r }) => !r?.is_bibliography);
  const n = slots.length;
  if (!n) return null;

  const values = slots.map(({ r }) => (typeof r?.ppl === 'number' ? r.ppl : null));
  const hasPrefix = slots.some(({ r }) => r?.ppl_basis === 'prefix');
  const yMax = Math.max(calibration.ppl_high * 1.15, ...values.filter((v): v is number => v !== null).map(v => Math.min(v, 300)));
  const y = (v: number) => H - (Math.min(v, yMax) / yMax) * (H - PAD_TOP);
  const slot = W / n;
  const gap = n > 60 ? 0.5 : 2;
  const barW = Math.max(1, slot - gap);
  const hovered = hover !== null ? slots[hover].r : null;

  return (
    <figure className="ppl-strip">
      <div className="ppl-plot" onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img"
          aria-label={`逐句困惑度分布，共 ${n} 句；虚线为本学科下限 ${calibration.ppl_low} 与上限 ${calibration.ppl_high}`}>
          <line x1="0" x2={W} y1={H - 0.5} y2={H - 0.5} className="ppl-axis" />
          {values.map((v, i) => {
            const { r, index } = slots[i];
            const x = i * slot + gap / 2;
            const cls = [
              !r ? 'pending' : r.status === 'flagged' ? `flagged issue-${issueMeta(r.issue_type).key}` : 'passed',
              r?.ppl_basis === 'prefix' ? 'prefix' : '',
            ].join(' ');
            const top = v === null ? H - 2 : y(v);
            return (
              <g key={i}>
                <rect x={x} y={top} width={barW} height={H - top} rx={Math.min(2, barW / 2)}
                  className={`ppl-bar ${cls} ${selected === index ? 'sel' : ''} ${hover === i ? 'hover' : ''}`} />
                {/* hit target larger than the mark */}
                <rect x={i * slot} y={0} width={slot} height={H} fill="transparent"
                  onMouseEnter={() => setHover(i)} onClick={() => r && onSelect(index)}
                  style={{ cursor: r ? 'pointer' : 'default' }} />
              </g>
            );
          })}
          <line x1="0" x2={W} y1={y(calibration.ppl_low)} y2={y(calibration.ppl_low)} className="ppl-threshold" />
          <line x1="0" x2={W} y1={y(calibration.ppl_high)} y2={y(calibration.ppl_high)} className="ppl-threshold" />
        </svg>
        <span className="ppl-tick" style={{ top: `${(y(calibration.ppl_high) / H) * 100}%` }}>{calibration.ppl_high}</span>
        <span className="ppl-tick" style={{ top: `${(y(calibration.ppl_low) / H) * 100}%` }}>{calibration.ppl_low}</span>
        {hovered && hover !== null && (
          <div className="ppl-tooltip" style={{ left: `${((hover + 0.5) / n) * 100}%` }} role="status">
            <span className="mono">#{slots[hover].index + 1}</span>
            <strong className="num">{typeof hovered.ppl === 'number' ? `PPL ${hovered.ppl}` : 'PPL —'}{hovered.ppl_basis === 'prefix' ? '（前 6 词估计）' : ''}</strong>
            <span>
              {hovered.status === 'flagged' && <i className={`swatch issue-${issueMeta(hovered.issue_type).key}`} aria-hidden />}
              {hovered.status === 'flagged' ? issueTitle(hovered.issue_type) : '通过'}
            </span>
          </div>
        )}
      </div>
      <figcaption className="ppl-legend">
        {ISSUE_ORDER.filter(t => results.some(r => r?.status === 'flagged' && r.issue_type === t)).map(t => (
          <span key={t}><i className={`swatch issue-${issueMeta(t).key}`} />{issueMeta(t).title}</span>
        ))}
        <span><i className="swatch passed" />通过</span>
        {hasPrefix && <span><i className="swatch passed prefix" />浅色：前 6 词估计</span>}
        <span><i className="swatch dash" />本学科区间 {calibration.ppl_low}–{calibration.ppl_high}</span>
        <span className="ppl-legend-note">按句序 · 点击柱查看</span>
      </figcaption>
    </figure>
  );
}
