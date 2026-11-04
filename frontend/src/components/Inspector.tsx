import { useState } from 'react';
import { ArrowLeft, Check, ChevronRight, Copy } from 'lucide-react';
import { AUDIT_LABELS, STATUS_LABELS, issueTitle } from '../lib/labels';
import type { CitationAudit, DiagnosticResult } from '../types';

interface Props {
  result: DiagnosticResult | null;
  noteNumber?: number;
  onBack: () => void;
}

const hasText = (s: string | null | undefined) => !!s && s !== '-' && s !== 'N/A';

function Trace({ label, text }: { label: string; text: string }) {
  return (
    <details className="trace block">
      <summary><ChevronRight className="chev" size={14} aria-hidden />{label}</summary>
      <div className="trace-body">{text}</div>
    </details>
  );
}

function Audits({ audits }: { audits: CitationAudit[] }) {
  return (
    <div className="block">
      <h3 className="eyebrow" style={{ marginBottom: 'var(--s2)' }}>引用核验</h3>
      <ul className="audits">
        {audits.map((a, i) => {
          const tone = a.status === 'SUPPORTED' ? 'good' : a.status === 'AUDIT_FAILED' ? '' : 'bad';
          return (
            <li key={i} className="audit">
              <div className="audit-head">
                <span className="audit-title"><span className="mono">[{a.key}]</span> {a.title}</span>
                <span className={`audit-status ${tone}`}>{AUDIT_LABELS[a.status] ?? a.status}</span>
              </div>
              <p className="meta" style={{ marginTop: 2 }}>{a.source === 'local' ? '依据：本地文献全文' : '依据：OpenAlex 摘要'}</p>
              <p className="prose" style={{ marginTop: 'var(--s2)' }}>{a.explanation_zh}</p>
              {a.evidence_snippet && <Trace label="文献原文片段" text={a.evidence_snippet} />}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function Inspector({ result, noteNumber, onBack }: Props) {
  const [copied, setCopied] = useState(false);

  const copy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // clipboard blocked; the text stays selectable
    }
  };

  return (
    <section className="aside-section" aria-labelledby="inspector-title">
      <button type="button" className="btn btn-quiet btn-sm back" onClick={onBack}>
        <ArrowLeft size={14} aria-hidden /> 返回全部批注
      </button>

      {!result ? (
        <p className="secondary" style={{ marginTop: 'var(--s4)' }}>这一句还在分析中，结果出来后会显示在这里。</p>
      ) : (
        <>
          <h2 className="section-title" id="inspector-title" style={{ marginTop: 'var(--s4)' }}>
            {result.status === 'flagged'
              ? <>{noteNumber !== undefined && <span style={{ color: 'var(--accent)' }}>{noteNumber}. </span>}{issueTitle(result.issue_type)}</>
              : '无需修改'}
          </h2>
          <blockquote className="quote">{result.text}</blockquote>

          <dl className="facts">
            <dt>结论</dt><dd>{STATUS_LABELS[result.status] ?? result.status}</dd>
            <dt>困惑度</dt><dd>{typeof result.ppl === 'number' ? result.ppl : '未计算（云端模式）'}</dd>
            {result.metrics && <>
              <dt>名词 / 动词</dt><dd>{result.metrics.nv_ratio}</dd>
              <dt>被动语态</dt><dd>{result.metrics.passive_count}</dd>
              <dt>第二格链</dt><dd>{result.metrics.genitive_chains_count}</dd>
              <dt>学术套话</dt><dd>{result.metrics.cliches_count}</dd>
            </>}
          </dl>

          {hasText(result.explanation) && (
            <div className="block">
              <h3 className="eyebrow" style={{ marginBottom: 'var(--s2)' }}>原因</h3>
              <p className="prose">{result.explanation}</p>
            </div>
          )}

          {hasText(result.suggestion) && result.status === 'flagged' && (
            <div className="block">
              <div className="block-head">
                <h3 className="eyebrow">建议改写</h3>
                <button type="button" className="btn btn-quiet btn-sm" onClick={() => copy(result.suggestion!)}>
                  {copied ? <><Check size={14} aria-hidden /> 已复制</> : <><Copy size={14} aria-hidden /> 复制</>}
                </button>
              </div>
              <p className="suggestion" lang="ru">{result.suggestion}</p>
            </div>
          )}

          {result.citation_audit && result.citation_audit.length > 0 && <Audits audits={result.citation_audit} />}

          {hasText(result.think) && <Trace label="模型推理过程" text={result.think!} />}
        </>
      )}
    </section>
  );
}
