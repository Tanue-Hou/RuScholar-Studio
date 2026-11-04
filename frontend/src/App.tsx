import React, { useState, useRef, useEffect, useMemo } from 'react';
import {
  Upload,
  FileText,
  Sun,
  Moon,
  Square,
  Copy,
  Check,
  RotateCcw,
  ChevronRight,
  ExternalLink,
  Play,
} from 'lucide-react';
import './index.css';
import { uploadDocument } from './api/client';
import { PplStrip } from './components/PplStrip';
import { useDiagnosis } from './hooks/useDiagnosis';
import { useModelStatus } from './hooks/useModelStatus';
import { useTheme } from './hooks/useTheme';
import {
  DEFAULT_CALIBRATION, documentStats, fmt, int, issueBreakdown, lexicalTotals, pplStats, riskLevel,
} from './lib/analysis';
import type { CitationAudit, DiagnosticResult, EngineType, SentenceMetrics } from './types';

interface SentenceItem {
  text: string;
  status: string;
  ppl?: number | null;
  metrics?: SentenceMetrics | null;
}

const DISCIPLINE_MAP: Record<string, { zh: string; ru: string }> = {
  SCI_TECH: { zh: '理工科 · 自然科学与工程技术', ru: 'Естественные и технические науки' },
  AUTOMATION_CONTROL: { zh: '自动化与控制工程', ru: 'Автоматизация и управление' },
  AGRI_MED: { zh: '农学与医学生命科学', ru: 'Сельскохозяйственные и медицинские науки' },
  HUM_POL_ECON: { zh: '人文社科 · 政治、经济与社会', ru: 'Гуманитарные и социальные науки' },
  ARTS_SPORTS: { zh: '艺术、体育与文化研究', ru: 'Искусство, спорт и культура' },
  UNIVERSAL: { zh: '通用学术 · 跨学科', ru: 'Междисциплинарная область' },
};

const ISSUE_TITLES: Record<string, string> = {
  ai_generated_suspicion: 'AI 生成特征',
  machine_translation_cliche: '翻译腔与学术套话',
  citation_gap: '引用支撑不足',
  citation_contradiction: '与所引文献冲突',
  semantic_plagiarism_risk: '与文献表述高度重合',
  style_heavy: '句式臃肿',
  json_parse_error: '模型输出无法解析',
  api_request_error: '云端接口未响应',
};
const issueTitle = (t: string | null) => ISSUE_TITLES[t ?? ''] ?? '文风提示';

/** Issue families carry a tone so the eye can sort them; colour is never the only cue. */
const issueTone = (t: string | null): 'critical' | 'warning' | 'muted' =>
  t === 'ai_generated_suspicion' || t === 'citation_contradiction' ? 'critical'
    : t === 'json_parse_error' || t === 'api_request_error' ? 'muted' : 'warning';

const ENGINE_LABELS: Record<EngineType, string> = {
  local: '本地 · Qwen3-8B GGUF',
  'hybrid-pro': '混合 · 本地 PPL + DeepSeek Pro',
  'hybrid-flash': '混合 · 本地 PPL + DeepSeek Flash',
  'cloud-pro': '云端 · DeepSeek Pro',
  'cloud-flash': '云端 · DeepSeek Flash',
};

const RISK_ROWS = [
  { key: 'predictability', label: '可预测性', hint: '词汇分布过于平滑，困惑度偏低' },
  { key: 'uniformity', label: '句式均匀度', hint: '句长与句式结构过于整齐' },
  { key: 'translationese', label: '翻译腔', hint: '名词化、被动语态、第二格链' },
  { key: 'redundancy', label: '语义冗余', hint: '套话、连接词与冗长修饰' },
] as const;

const CHECKS = [
  ['困惑度 PPL', '本地 Qwen3 逐句计算；低于学科下限提示文本过于可预测，高于上限提示语法或翻译问题。'],
  ['名词 / 动词比', '俄语学术文体的名词化程度；超过学科上限视为结构臃肿。'],
  ['被动语态与第二格链', '统计 -ся / 被动形动词与连续属格结构，识别翻译腔。'],
  ['学术套话与连接词', '匹配 PhD Thesis Butler 规则库中的高频模板表达。'],
  ['引用核验', '按文内引标检索本地全文（BM25）或 OpenAlex 摘要，再以 NLI 判断支持、矛盾或证据不足。'],
  ['参考文献完整性', '交叉核对文内标号与文末书目，发现缺失与未引用条目。'],
];

function App() {
  const diagnosis = useDiagnosis();
  const model = useModelStatus();
  const { theme, toggle: toggleTheme } = useTheme();
  const [file, setFile] = useState<File | null>(null);
  const [documentText, setDocumentText] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const uploadRef = useRef<AbortController | null>(null);
  const [selectedSentenceIndex, setSelectedSentenceIndex] = useState<number | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const sentenceRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const rightColumnRef = useRef<HTMLDivElement | null>(null);
  const inspectorRef = useRef<HTMLElement | null>(null);
  const [engineType, setEngineType] = useState<EngineType>('local');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com/v1');
  const [activeTab, setActiveTab] = useState<'all' | 'passed' | 'ai' | 'flagged' | 'integrity'>('all');
  const [bibtexFile, setBibtexFile] = useState<File | null>(null);
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const { status: localModelStatus, progress: downloadProgress, download: downloadLocalModel } = model;
  const isAnalyzing = diagnosis.phase === 'preparing' || diagnosis.phase === 'running';
  const discipline = diagnosis.discipline;
  const runningRisks = diagnosis.risks;
  const integrityWarnings = diagnosis.warnings;
  const progress = { current: diagnosis.summary.completed, total: diagnosis.summary.total };
  const completed = useMemo(
    () => diagnosis.results.filter((r): r is DiagnosticResult => r !== null),
    [diagnosis.results],
  );
  const allDiagnostics: Record<number, DiagnosticResult> = Object.fromEntries(completed.map(r => [r.index, r]));
  const calib = diagnosis.calibration ?? DEFAULT_CALIBRATION;
  const ppl = pplStats(completed, calib);
  const lexical = lexicalTotals(completed, calib);
  const breakdown = issueBreakdown(completed);
  const docStats = useMemo(() => documentStats(documentText), [documentText]);
  const referencesUploadStatus = diagnosis.references;
  const sentences: SentenceItem[] = diagnosis.results.map(r => r ?? {
    text: '', status: isAnalyzing ? 'analyzing' : 'skipped',
  });

  useEffect(() => () => uploadRef.current?.abort(), []);

  const copyToClipboard = async (text: string, key: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 1800);
    } catch {
      setUploadError('无法复制，请手动选择建议文字。');
    }
  };

  const loadFile = async (uploadedFile: File) => {
    uploadRef.current?.abort();
    const controller = new AbortController();
    uploadRef.current = controller;
    diagnosis.reset();
    setUploading(true);
    setUploadError(null);
    try {
      const text = await uploadDocument(uploadedFile, controller.signal);
      if (controller.signal.aborted) return;
      if (!text.trim()) throw new Error('文件中没有可读取的文字，扫描版 PDF 请先进行文字识别。');
      setFile(uploadedFile);
      setDocumentText(text);
      setSelectedSentenceIndex(null);
      setActiveTab('all');
    } catch (err) {
      if (!controller.signal.aborted) setUploadError(`无法读取手稿：${err instanceof Error ? err.message : err}`);
    } finally {
      if (!controller.signal.aborted) setUploading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) void loadFile(selected);
    e.target.value = '';
  };

  const stopAnalysis = diagnosis.stop;
  const startAnalysis = () => {
    if (!documentText || uploading) return;
    if ((engineType === 'local' || engineType.startsWith('hybrid')) && localModelStatus !== 'exists') {
      setUploadError('本地模型尚未就绪，请先下载模型或切换至云端引擎。');
      return;
    }
    setUploadError(null);
    setSelectedSentenceIndex(null);
    setActiveTab('all');
    void diagnosis.start({ text: documentText, engine: { engineType, apiKey, baseUrl }, bibtex: bibtexFile, referenceDocs: referenceFiles });
  };

  const replaceManuscript = () => {
    uploadRef.current?.abort();
    setUploading(false);
    diagnosis.reset();
    setFile(null);
    setDocumentText('');
    setSelectedSentenceIndex(null);
    setActiveTab('all');
    setUploadError(null);
  };

  const scrollToSentence = (index: number) => {
    setTimeout(() => {
      if (index >= 0 && sentenceRefs.current[index]) {
        sentenceRefs.current[index]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  const selectSentence = (index: number, scrollManuscript = false) => {
    setSelectedSentenceIndex(index);
    if (scrollManuscript) scrollToSentence(index);
    setTimeout(() => inspectorRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 30);
  };

  const referenceMode = referencesUploadStatus === 'indexed' ? `本地全文证据库 · ${referenceFiles.length} 篇`
    : referencesUploadStatus === 'metadata' ? '书目信息 + OpenAlex 摘要'
    : referencesUploadStatus === 'uploading' ? '正在注册参考文献…'
    : referencesUploadStatus === 'none' && (bibtexFile || referenceFiles.length > 0) ? '已选文献，启动后注册'
    : referencesUploadStatus === 'failed' ? '注册失败，改用 OpenAlex 摘要'
    : 'OpenAlex 摘要（未提供本地文献）';

  const pplClass = (v: number | null | undefined) =>
    typeof v !== 'number' ? '' : v < calib.ppl_low ? 'is-low' : v > calib.ppl_high ? 'is-high' : '';

  const renderAuditList = (audits: CitationAudit[]) => (
    <ul className="audit-list">
      {audits.map((audit, aIdx) => {
        const tone = audit.status === 'SUPPORTED' ? 'good' : audit.status === 'CONTRADICTED' ? 'critical' : audit.status === 'AUDIT_FAILED' ? 'muted' : 'warning';
        const statusText = audit.status === 'SUPPORTED' ? '支持论点'
          : audit.status === 'CONTRADICTED' ? '与论点矛盾'
          : audit.status === 'AUDIT_FAILED' ? '未能核验' : '证据不足';
        return (
          <li key={aIdx} className="audit-item" onClick={e => e.stopPropagation()}>
            <div className="audit-head">
              <span className="audit-ref"><span className="mono">[{audit.key}]</span> {audit.title}</span>
              <span className={`tag tone-${tone}`}>{statusText}</span>
            </div>
            <div className="audit-meta">
              {[audit.author, audit.year].filter(Boolean).join(' · ') || '作者与年份未知'} · {audit.source === 'local' ? '依据本地全文' : '依据 OpenAlex 摘要'}
            </div>
            <p className="audit-body">{audit.explanation_zh}</p>
            {audit.evidence_snippet && (
              <details className="disclosure">
                <summary><ChevronRight size={13} className="chev" aria-hidden />文献原文片段</summary>
                <blockquote className="evidence">{audit.evidence_snippet}</blockquote>
              </details>
            )}
          </li>
        );
      })}
    </ul>
  );

  const disciplineInfo = DISCIPLINE_MAP[discipline] ?? DISCIPLINE_MAP.UNIVERSAL;
  const flaggedPct = progress.total ? Math.round((diagnosis.summary.flagged / progress.total) * 100) : 0;
  const selected = selectedSentenceIndex !== null ? allDiagnostics[selectedSentenceIndex] : undefined;

  return (
    <div className="app-container">
      <header className="header">
        <div className="brand">
          <span className="monogram" aria-hidden>Rs</span>
          <div className="brand-text">
            <div className="brand-row">
              <h1 className="brand-name">RuScholar Studio</h1>
              <span className="tag tone-outline">ВАК · ГОСТ</span>
            </div>
            <div className="brand-sub">俄语学位论文文风与引证质检工作台</div>
          </div>
        </div>

        <div className="header-spacer" />

        <div className="header-controls">
          <label className="field-inline">
            <span className="visually-hidden">推理引擎</span>
            <select value={engineType} onChange={e => setEngineType(e.target.value as EngineType)}
              disabled={isAnalyzing} className="tech-select">
              {(Object.keys(ENGINE_LABELS) as EngineType[]).map(k => <option key={k} value={k}>{ENGINE_LABELS[k]}</option>)}
            </select>
          </label>

          {engineType !== 'local' && (
            <>
              <input type="text" aria-label="接口地址" placeholder="https://api.deepseek.com/v1" value={baseUrl}
                onChange={e => setBaseUrl(e.target.value)} className="tech-input mono" style={{ width: 196 }} />
              <input type="password" aria-label="API Key" placeholder="API Key（留空用 .env）" value={apiKey}
                onChange={e => setApiKey(e.target.value)} className="tech-input mono" style={{ width: 168 }} />
            </>
          )}

          {(engineType === 'local' || engineType.startsWith('hybrid')) && (
            <>
              {localModelStatus === 'exists' && <span className="status-text"><i className="dot tone-good" />本地模型已加载</span>}
              {localModelStatus === 'checking' && <span className="status-text"><i className="dot" />检查模型…</span>}
              {localModelStatus === 'missing' && (
                <button onClick={downloadLocalModel} className="btn-secondary">下载本地模型 · 5.9 GB</button>
              )}
              {localModelStatus === 'downloading' && (
                <span className="status-text">下载模型 <span className="num">{Math.round(downloadProgress)}%</span></span>
              )}
            </>
          )}

          <span className="header-divider" aria-hidden />

          <button onClick={toggleTheme} className="icon-btn" aria-label={theme === 'dark' ? '切换为浅色' : '切换为深色'}
            title={theme === 'dark' ? '切换为浅色' : '切换为深色'}>
            {theme === 'dark' ? <Sun size={16} strokeWidth={1.75} /> : <Moon size={16} strokeWidth={1.75} />}
          </button>
          <a href="https://github.com/Tanue-Hou/RuScholar-Studio" target="_blank" rel="noreferrer"
            className="icon-btn" aria-label="GitHub 仓库" title="GitHub 仓库">
            <ExternalLink size={16} strokeWidth={1.75} />
          </a>

          {file && (isAnalyzing ? (
            <>
              <span className="status-text num">
                {diagnosis.phase === 'preparing' ? '准备中…' : `${progress.current} / ${progress.total} 句`}
              </span>
              <button onClick={stopAnalysis} className="btn-secondary"><Square size={12} aria-hidden />停止</button>
            </>
          ) : (
            <button className="btn-primary" onClick={startAnalysis} disabled={uploading}>
              <Play size={13} aria-hidden />{diagnosis.phase === 'idle' ? '开始质检' : '重新质检'}
            </button>
          ))}
        </div>
      </header>

      {(uploadError || model.error || diagnosis.error || diagnosis.phase === 'stopped' || diagnosis.nlpBackend === 'fallback' || engineType !== 'local') && (
        <div className="studio-notices" aria-live="polite">
          {(uploadError || model.error || diagnosis.error) && <p role="alert" className="notice tone-critical">{uploadError || model.error || diagnosis.error}</p>}
          {diagnosis.phase === 'stopped' && <p className="notice">质检已停止，{progress.total ? `已完成 ${progress.current} / ${progress.total} 句` : '尚无已完成的结果'}。可以重新开始完整质检。</p>}
          {diagnosis.nlpBackend === 'fallback' && <p className="notice tone-warning">后端缺少 spaCy 俄语模型，名动比、被动语态与第二格链为粗略估计。安装 ru_core_news_sm 后重启后端。</p>}
          {engineType !== 'local' && <p className="notice">{engineType.startsWith('hybrid') ? '混合模式：困惑度在本地计算，需要判定的句子会发送到所选云端接口。' : '云端模式：全部句子发送到所选接口，不计算困惑度。'}</p>}
        </div>
      )}

      <main className="main-content">
        {/* Left: manuscript */}
        <div className="column-left">
          {!file ? (
            <div className="upload-zone-wrapper">
              <div className="intro">
                <div className="eyebrow">新建质检</div>
                <h2 className="intro-title">导入一份俄语学术手稿</h2>
                <p className="intro-text">
                  逐句评估困惑度、名词化程度、被动语态与套话密度，并按文内引标回溯文献原文核验论点。每一项结论都附带数值、阈值与依据，不给出笼统的「AI 率」。
                </p>
              </div>

              <div className="upload-zone" role="button" tabIndex={0} aria-label="导入俄语学术手稿" aria-busy={uploading}
                onClick={() => { if (!uploading) document.getElementById('file-upload')?.click(); }}
                onKeyDown={e => { if ((e.key === 'Enter' || e.key === ' ') && !uploading) { e.preventDefault(); document.getElementById('file-upload')?.click(); } }}
                onDragOver={e => e.preventDefault()}
                onDrop={e => { e.preventDefault(); const dropped = e.dataTransfer.files[0]; if (dropped) void loadFile(dropped); }}
              >
                <Upload size={22} strokeWidth={1.5} className="upload-icon" aria-hidden />
                <div className="upload-title">{uploading ? '正在读取手稿…' : '选择或拖入手稿文件'}</div>
                <div className="upload-hint">.docx · .pdf · .txt · 单个文件不超过 50 MB · 本地模式下全文不离开本机</div>
                <input id="file-upload" type="file" accept=".docx,.pdf,.txt" style={{ display: 'none' }} onChange={handleFileUpload} />
              </div>

              <section className="card library">
                <div className="card-head">
                  <h3 className="card-title">参考文献库</h3>
                  <span className="card-meta">选填</span>
                </div>
                <p className="card-text">提供全文后，引用核验基于原文段落（BM25 检索）；未提供时按书目信息检索 OpenAlex 摘要。</p>
                <div className="library-grid">
                  <div className="library-cell">
                    <div className="library-label">BibTeX 书目</div>
                    <div className="library-value mono">{bibtexFile ? bibtexFile.name : '未选择 .bib'}</div>
                    <button type="button" className="btn-secondary btn-sm" onClick={() => document.getElementById('bibtex-upload')?.click()}>
                      {bibtexFile ? '更换文件' : '选择 .bib'}
                    </button>
                    <input id="bibtex-upload" type="file" accept=".bib" style={{ display: 'none' }}
                      onChange={e => { if (e.target.files?.length) setBibtexFile(e.target.files[0]); }} />
                  </div>
                  <div className="library-cell">
                    <div className="library-label">文献全文</div>
                    <div className="library-value mono">{referenceFiles.length > 0 ? `已选 ${referenceFiles.length} 篇` : '未选择 PDF'}</div>
                    <button type="button" className="btn-secondary btn-sm" onClick={() => document.getElementById('pdfs-upload')?.click()}>
                      {referenceFiles.length > 0 ? '重新选择' : '批量导入 PDF'}
                    </button>
                    <input id="pdfs-upload" type="file" multiple accept=".pdf" style={{ display: 'none' }}
                      onChange={e => { if (e.target.files?.length) setReferenceFiles(Array.from(e.target.files)); }} />
                  </div>
                </div>
                <p className="card-foot">文件名即引用键，例如 <span className="mono">[Smith2020].pdf</span> 对应文内 <span className="mono">[Smith2020]</span>。</p>
              </section>
            </div>
          ) : (
            <div className="document-viewer">
              <div className="doc-header">
                <FileText size={16} strokeWidth={1.75} className="doc-icon" aria-hidden />
                <div className="doc-title-block">
                  <div className="doc-title">{file.name}</div>
                  <dl className="doc-stats">
                    <div><dt>字符</dt><dd className="num">{int(docStats.characters)}</dd></div>
                    <div><dt>词</dt><dd className="num">{int(docStats.words)}</dd></div>
                    <div><dt>句</dt><dd className="num">{progress.total ? int(progress.total) : '—'}</dd></div>
                    <div><dt>文内引标</dt><dd className="num">{int(docStats.citations)}</dd></div>
                    <div><dt>文献核验</dt><dd>{referenceMode}</dd></div>
                  </dl>
                </div>
                <button onClick={replaceManuscript} className="btn-ghost"><RotateCcw size={13} aria-hidden />重新导入</button>
              </div>

              {progress.current > 0 && (
                <div className="doc-legend" aria-hidden>
                  <span><i className="legend-line flagged" />需修改</span>
                  <span><i className="legend-line" />通过</span>
                  <span><span className="legend-num is-low">7.4</span>困惑度标注，着色表示低于下限 {calib.ppl_low}</span>
                  <span className="doc-legend-note">点击句子查看指标与改写建议</span>
                </div>
              )}

              <div className="document-canvas" lang="ru">
                {progress.current === 0 ? (
                  <div className="manuscript-plain">{documentText}</div>
                ) : (
                  sentences.map((s, idx) => (
                    <span key={idx}>
                      <span ref={el => { sentenceRefs.current[idx] = el; }}
                        className={`sentence ${s.status} ${selectedSentenceIndex === idx ? 'selected-highlight' : ''}`}
                        onClick={() => s.text && selectSentence(idx)}>
                        {s.text}
                      </span>
                      {typeof s.ppl === 'number' && <sup className={`ppl-tag ${pplClass(s.ppl)}`} title="困惑度 PPL">{s.ppl}</sup>}
                      {' '}
                    </span>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right: findings */}
        <div className="column-right" ref={rightColumnRef}>
          <div className="stream-container">
            {!file && (
              <section className="card">
                <div className="card-head"><h3 className="card-title">检测项目</h3><span className="card-meta">6 项</span></div>
                <dl className="check-list">
                  {CHECKS.map(([name, desc]) => (
                    <div key={name}><dt>{name}</dt><dd>{desc}</dd></div>
                  ))}
                </dl>
              </section>
            )}

            {file && (
              <section className="card">
                <div className="card-head">
                  <h3 className="card-title">学科归类</h3>
                  <span className="card-meta mono">{discipline}</span>
                </div>
                <div className="discipline-name">{disciplineInfo.zh}</div>
                <div className="discipline-ru" lang="ru">{disciplineInfo.ru}</div>
                <dl className="threshold-row">
                  <div><dt>困惑度区间</dt><dd className="num">{calib.ppl_low}–{calib.ppl_high}</dd></div>
                  <div><dt>名动比上限</dt><dd className="num">{fmt(calib.nv_ratio_max)}</dd></div>
                  <div><dt>被动语态上限</dt><dd className="num">{calib.passive_max ?? '—'}</dd></div>
                </dl>
                {!diagnosis.calibration && <p className="card-foot">阈值为默认值；开始质检后显示本学科校准值。</p>}
              </section>
            )}

            {progress.total > 0 && (
              <section className="card">
                <div className="card-head">
                  <h3 className="card-title">概览</h3>
                  <span className="card-meta num">{progress.current} / {progress.total} 句{isAnalyzing ? ' · 分析中' : ''}</span>
                </div>
                {isAnalyzing && (
                  <div className="progress" role="progressbar" aria-label="质检进度" aria-valuemin={0} aria-valuemax={progress.total} aria-valuenow={progress.current}>
                    <div className="progress-fill" style={{ transform: `scaleX(${progress.total ? progress.current / progress.total : 0})` }} />
                  </div>
                )}
                <div className="kpi-grid">
                  <div className="kpi">
                    <div className="kpi-label">需修改</div>
                    <div className={`kpi-value ${flaggedPct >= 30 ? 'tone-critical' : ''}`}>{flaggedPct}<span className="kpi-unit">%</span></div>
                    <div className="kpi-sub num">{diagnosis.summary.flagged} / {progress.total} 句</div>
                  </div>
                  <div className="kpi">
                    <div className="kpi-label">平均困惑度</div>
                    <div className="kpi-value">{fmt(ppl.mean)}</div>
                    <div className="kpi-sub num">中位 {fmt(ppl.median)} · 范围 {fmt(ppl.min, 0)}–{fmt(ppl.max, 0)}</div>
                  </div>
                  <div className="kpi">
                    <div className="kpi-label">低于下限</div>
                    <div className={`kpi-value ${ppl.belowLow ? 'tone-critical' : ''}`}>{ppl.count ? ppl.belowLow : '—'}</div>
                    <div className="kpi-sub num">PPL &lt; {calib.ppl_low} · 高于上限 {ppl.count ? ppl.aboveHigh : '—'}</div>
                  </div>
                  <div className="kpi">
                    <div className="kpi-label">引文问题</div>
                    <div className={`kpi-value ${integrityWarnings.length ? 'tone-warning' : ''}`}>
                      {integrityWarnings.length + completed.filter(d => d.status === 'flagged' && (d.issue_type === 'citation_gap' || d.issue_type === 'citation_contradiction')).length}
                    </div>
                    <div className="kpi-sub num">书目缺失 {integrityWarnings.length} · 逐句 {completed.filter(d => d.citation_audit?.length).length} 处核验</div>
                  </div>
                </div>
                {ppl.count > 0 ? (
                  <PplStrip results={diagnosis.results} calibration={calib} selected={selectedSentenceIndex}
                    onSelect={i => selectSentence(i, true)} issueTitle={issueTitle} />
                ) : (
                  progress.current > 0 && <p className="card-foot">当前为云端模式，不计算困惑度分布。</p>
                )}
              </section>
            )}

            {progress.total > 0 && (
              <section className="card">
                <div className="card-head"><h3 className="card-title">文风风险</h3><span className="card-meta">全文累计</span></div>
                <ul className="risk-list">
                  {RISK_ROWS.map(r => {
                    const v = runningRisks[r.key];
                    const level = riskLevel(v);
                    return (
                      <li key={r.key} className="risk-row">
                        <div className="risk-name">{r.label}<span className="risk-hint">{r.hint}</span></div>
                        <div className={`risk-value num ${level === '高' ? 'tone-critical' : ''}`}>{v}%<span className="risk-level">{level}</span></div>
                        <div className="telemetry-track"><div className={`telemetry-fill ${level === '高' ? 'high' : level === '中' ? 'mid' : ''}`} style={{ transform: `scaleX(${v / 100})` }} /></div>
                      </li>
                    );
                  })}
                </ul>
                <div className="split">
                  <div>
                    <div className="sub-title">问题构成</div>
                    {breakdown.length ? (
                      <ul className="breakdown">
                        {breakdown.map(b => (
                          <li key={b.type}>
                            <span><i className={`dot tone-${issueTone(b.type)}`} />{issueTitle(b.type)}</span>
                            <span className="num">{b.count}</span>
                          </li>
                        ))}
                      </ul>
                    ) : <p className="card-foot">暂无需修改的句子。</p>}
                  </div>
                  <div>
                    <div className="sub-title">词法汇总</div>
                    <dl className="facts compact">
                      <div><dt>平均名动比</dt><dd className="num">{fmt(lexical.meanNv, 2)}</dd></div>
                      <div><dt>超出上限</dt><dd className="num">{lexical.overNv} 句</dd></div>
                      <div><dt>被动语态</dt><dd className="num">{lexical.passive}</dd></div>
                      <div><dt>第二格链</dt><dd className="num">{lexical.genitiveChains}</dd></div>
                      <div><dt>套话命中</dt><dd className="num">{lexical.cliches}</dd></div>
                      <div><dt>连接词</dt><dd className="num">{lexical.connectors}</dd></div>
                    </dl>
                  </div>
                </div>
              </section>
            )}

            {file && (
              <section className="card inspector" ref={inspectorRef}>
                <div className="card-head">
                  <h3 className="card-title">逐句详情</h3>
                  {selectedSentenceIndex !== null ? (
                    <span className="card-meta num">
                      第 {selectedSentenceIndex + 1} / {progress.total} 句
                      <button onClick={() => setSelectedSentenceIndex(null)} className="link-btn">取消选定</button>
                    </span>
                  ) : <span className="card-meta">未选定</span>}
                </div>

                {selectedSentenceIndex === null ? (
                  <p className="card-text muted">点击左侧手稿中的句子，或右侧分布图中的柱，查看该句的指标、诊断依据与改写建议。</p>
                ) : !selected ? (
                  <p className="card-text muted">这一句还在分析，结果出来后显示在这里。</p>
                ) : (
                  <>
                    <div className="verdict-row">
                      <span className={`tag tone-${selected.status === 'flagged' ? issueTone(selected.issue_type) : 'good'}`}>
                        {selected.status === 'flagged' ? issueTitle(selected.issue_type) : selected.status === 'early_exit' ? '通过 · 快速判定' : '通过'}
                      </span>
                      {selected.severity && <span className="verdict-sev">严重度 {selected.severity === 'high' ? '高' : selected.severity === 'medium' ? '中' : '低'}</span>}
                    </div>
                    <blockquote className="quote" lang="ru">{selected.text}</blockquote>

                    <table className="metric-table">
                      <thead><tr><th>指标</th><th>本句</th><th>本学科阈值</th></tr></thead>
                      <tbody>
                        <tr>
                          <td>困惑度 PPL</td>
                          <td className={`num ${pplClass(selected.ppl)}`}>{typeof selected.ppl === 'number' ? selected.ppl : '未计算'}</td>
                          <td className="num">{calib.ppl_low}–{calib.ppl_high}</td>
                        </tr>
                        {selected.metrics && <>
                          <tr><td>名词 / 动词比</td><td className={`num ${selected.metrics.nv_ratio > calib.nv_ratio_max ? 'is-low' : ''}`}>{selected.metrics.nv_ratio}</td><td className="num">≤ {fmt(calib.nv_ratio_max)}</td></tr>
                          <tr><td>被动语态</td><td className={`num ${calib.passive_max != null && selected.metrics.passive_count > calib.passive_max ? 'is-low' : ''}`}>{selected.metrics.passive_count}</td><td className="num">{calib.passive_max != null ? `≤ ${calib.passive_max}` : '—'}</td></tr>
                          <tr><td>第二格链</td><td className="num">{selected.metrics.genitive_chains_count}</td><td className="num">0 为佳</td></tr>
                          <tr><td>学术套话</td><td className="num">{selected.metrics.cliches_count}</td><td className="num">0 为佳</td></tr>
                          <tr><td>连接词</td><td className="num">{selected.metrics.connectors_count ?? '—'}</td><td className="num">—</td></tr>
                        </>}
                      </tbody>
                    </table>

                    {selected.explanation && (
                      <div className="block">
                        <div className="sub-title">诊断依据</div>
                        <p className="block-text">{selected.explanation}</p>
                      </div>
                    )}

                    {selected.suggestion && selected.suggestion !== 'N/A' && selected.suggestion !== '-' && selected.status === 'flagged' && (
                      <div className="block">
                        <div className="block-head">
                          <div className="sub-title">改写建议</div>
                          <button onClick={() => copyToClipboard(selected.suggestion || '', `sugg-${selectedSentenceIndex}`)} className="link-btn">
                            {copiedKey === `sugg-${selectedSentenceIndex}` ? <><Check size={12} aria-hidden />已复制</> : <><Copy size={12} aria-hidden />复制</>}
                          </button>
                        </div>
                        <p className="suggestion" lang="ru">{selected.suggestion}</p>
                      </div>
                    )}

                    {selected.citation_audit && selected.citation_audit.length > 0 && (
                      <div className="block">
                        <div className="sub-title">引用核验 · {selected.citation_audit.length} 条</div>
                        {renderAuditList(selected.citation_audit)}
                      </div>
                    )}

                    {selected.think && (
                      <details className="disclosure block">
                        <summary><ChevronRight size={13} className="chev" aria-hidden />模型推理过程</summary>
                        <div className="terminal-block">{selected.think}</div>
                      </details>
                    )}
                  </>
                )}
              </section>
            )}

            {(() => {
              const sortedDiagnostics = [...completed].sort((a, b) => a.index - b.index);
              const passedCount = sortedDiagnostics.filter(d => d.status !== 'flagged').length;
              const aiCount = sortedDiagnostics.filter(d => d.status === 'flagged' && d.issue_type === 'ai_generated_suspicion').length;
              const styleCount = sortedDiagnostics.filter(d => d.status === 'flagged' && d.issue_type !== 'ai_generated_suspicion' && d.issue_type !== 'citation_gap' && d.issue_type !== 'citation_contradiction').length;
              const sentenceIntegrityCount = sortedDiagnostics.filter(d => d.status === 'flagged' && (d.issue_type === 'citation_gap' || d.issue_type === 'citation_contradiction')).length;
              const integrityCount = integrityWarnings.length + sentenceIntegrityCount;
              const tabs = [
                ['all', '全部', sortedDiagnostics.length + integrityWarnings.length],
                ['ai', 'AI 特征', aiCount],
                ['flagged', '文风', styleCount],
                ['integrity', '引文', integrityCount],
                ['passed', '通过', passedCount],
              ] as const;

              return (
                <>
                  {file && progress.total > 0 && (
                    <div className="tabs-row">
                      <div className="tabs-container" role="group" aria-label="筛选诊断结果">
                        {tabs.map(([key, label, count]) => (
                          <button key={key} className={`tab-btn ${activeTab === key ? 'active' : ''}`} aria-pressed={activeTab === key} onClick={() => setActiveTab(key)}>
                            {label}<span className="tab-count num">{count}</span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {sortedDiagnostics
                    .filter(diag => {
                      if (activeTab === 'all') return true;
                      if (activeTab === 'passed') return diag.status !== 'flagged';
                      if (activeTab === 'ai') return diag.status === 'flagged' && diag.issue_type === 'ai_generated_suspicion';
                      if (activeTab === 'flagged') return diag.status === 'flagged' && diag.issue_type !== 'ai_generated_suspicion' && diag.issue_type !== 'citation_gap' && diag.issue_type !== 'citation_contradiction';
                      if (activeTab === 'integrity') return diag.status === 'flagged' && (diag.issue_type === 'citation_gap' || diag.issue_type === 'citation_contradiction');
                      return true;
                    })
                    .map(diag => {
                      const isFlagged = diag.status === 'flagged';
                      const tone = isFlagged ? issueTone(diag.issue_type) : 'good';
                      return (
                        <article key={diag.index} className={`diag-card tone-${tone} ${selectedSentenceIndex === diag.index ? 'is-selected' : ''}`}
                          onClick={() => selectSentence(diag.index, true)}>
                          <div className="diag-head">
                            <span className="diag-index mono">#{String(diag.index + 1).padStart(2, '0')}</span>
                            <span className="diag-title">{isFlagged ? issueTitle(diag.issue_type) : diag.status === 'early_exit' ? '通过 · 快速判定' : '通过'}</span>
                            <span className={`diag-ppl num ${pplClass(diag.ppl)}`}>{typeof diag.ppl === 'number' ? `PPL ${diag.ppl}` : 'PPL —'}</span>
                          </div>
                          <p className="diag-text" lang="ru">{diag.text.length > 140 ? `${diag.text.substring(0, 140)}…` : diag.text}</p>
                          {diag.metrics && (
                            <div className="diag-metrics num">
                              <span>名动比 {diag.metrics.nv_ratio}</span>
                              <span>被动 {diag.metrics.passive_count}</span>
                              <span>属格链 {diag.metrics.genitive_chains_count}</span>
                              <span>套话 {diag.metrics.cliches_count}</span>
                              {diag.citation_audit?.length ? <span>引用核验 {diag.citation_audit.length}</span> : null}
                            </div>
                          )}
                          {isFlagged && diag.explanation && <p className="diag-expl">{diag.explanation}</p>}
                          {isFlagged && diag.suggestion && diag.suggestion !== 'N/A' && diag.suggestion !== '-' && (
                            <p className="diag-sugg" lang="ru"><span className="diag-sugg-label">建议</span>{diag.suggestion}</p>
                          )}
                          {diag.think && (
                            <details className="disclosure" onClick={e => e.stopPropagation()}>
                              <summary><ChevronRight size={13} className="chev" aria-hidden />模型推理过程</summary>
                              <div className="terminal-block">{diag.think}</div>
                            </details>
                          )}
                        </article>
                      );
                    })}

                  {(activeTab === 'all' || activeTab === 'integrity') && integrityWarnings.length > 0 && (
                    <section className="card">
                      <div className="card-head"><h3 className="card-title">参考文献完整性</h3><span className="card-meta num">{integrityWarnings.length} 项</span></div>
                      <ul className="integrity-list">
                        {integrityWarnings.map((w, idx) => (
                          <li key={idx}>
                            <div className="integrity-title"><i className="dot tone-warning" />{w.explanation}</div>
                            {w.suggestion && w.suggestion !== '-' && <div className="integrity-sugg">{w.suggestion}</div>}
                            <div className="integrity-ref mono">{w.text.replace('Citation Integrity Alert ', '')}</div>
                          </li>
                        ))}
                      </ul>
                    </section>
                  )}
                </>
              );
            })()}

            {isAnalyzing && (
              <div className="pending-row" role="status">
                <span className="pending-bar" aria-hidden />
                {diagnosis.phase === 'preparing' ? '识别学科、建立会话…' : `正在分析第 ${Math.min(progress.current + 1, progress.total)} 句`}
              </div>
            )}

            {diagnosis.phase === 'done' && (
              <section className="card">
                <div className="card-head"><h3 className="card-title">更多审计</h3><span className="card-meta">通过 MCP 客户端使用</span></div>
                <ul className="roadmap-list">
                  <li><span>ВАК / ГОСТ 合规审计</span><span className="card-meta mono">thesis_audit_vak_gost_compliance</span></li>
                  <li><span>ВАК 学科代码匹配</span><span className="card-meta mono">thesis_map_vak_specialty</span></li>
                  <li><span>全文自然化润色</span><span className="card-meta">规划中 · 目前可逐句改写</span></li>
                  <li><span>章节逻辑骨架审阅</span><span className="card-meta">规划中</span></li>
                </ul>
              </section>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
