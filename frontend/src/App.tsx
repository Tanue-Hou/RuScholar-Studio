import React, { useState, useRef, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  AlertCircle, 
  Sun, 
  Moon, 
  Sparkles, 
  Cpu, 
  CheckCircle2, 
  Play, 
  Square, 
  Copy, 
  Check, 
  BookOpen, 
  RotateCcw,
  Compass,
  Layers,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  Zap,
  Activity,
  AlertTriangle
} from 'lucide-react';
import './index.css';

interface DiagnosticResult {
  index: number;
  text: string;
  ppl: number | null;
  issue_type: string | null;
  severity: string | null;
  explanation: string | null;
  suggestion: string | null;
  think: string | null;
  status: 'ok' | 'skipped_heuristic' | 'early_exit' | 'passed' | 'flagged';
  metrics?: {
    nv_ratio: number;
    passive_count: number;
    genitive_chains_count: number;
    cliches_count: number;
  } | null;
  predictability_risk?: number;
  uniformity_risk?: number;
  translationese_risk?: number;
  redundancy_risk?: number;
  citation_audit?: {
    key: string;
    title: string;
    author: string;
    year: string;
    status: 'SUPPORTED' | 'CONTRADICTED' | 'NOT_ENOUGH_INFO' | 'AUDIT_FAILED';
    explanation_zh: string;
    evidence_snippet: string;
    think: string | null;
    source: 'local' | 'online';
  }[];
}

interface SentenceItem {
  text: string;
  status: string;
  ppl?: number | null;
  metrics?: {
    nv_ratio: number;
    passive_count: number;
    genitive_chains_count: number;
    cliches_count: number;
  } | null;
}

const DISCIPLINE_MAP: Record<string, { en: string; zh: string; color: string; icon: any }> = {
  SCI_TECH: { en: "Sci-Tech (Physical Sciences & Engineering)", zh: "理工科 (自然科学与工程技术)", color: "var(--accent-cyan)", icon: Cpu },
  AUTOMATION_CONTROL: { en: "Automation & Control Engineering", zh: "自动化与控制工程", color: "var(--accent-amber)", icon: Compass },
  AGRI_MED: { en: "Agricultural & Medical Sciences", zh: "农田与医药生命科学", color: "var(--accent-emerald)", icon: ShieldCheck },
  HUM_POL_ECON: { en: "Humanities & Social Sciences", zh: "人文社科 (政治经济与社会科学)", color: "var(--accent-indigo)", icon: BookOpen },
  ARTS_SPORTS: { en: "Arts, Sports & Culture", zh: "艺术体育与文化研究", color: "var(--accent-pink)", icon: Sparkles },
  UNIVERSAL: { en: "Universal Academic Domain", zh: "通用学术与跨学科领域", color: "var(--text-secondary)", icon: Layers }
};

const ISSUE_TITLE_MAP: Record<string, { title: string; color: string; bg: string }> = {
  ai_generated_suspicion: { title: "AI 生成特征预警 (AI Writing Pattern)", color: "var(--accent-rose)", bg: "var(--accent-rose-bg)" },
  machine_translation_cliche: { title: "机器翻译与学术套话 (Translationese & Cliché)", color: "var(--accent-amber)", bg: "var(--accent-amber-bg)" },
  citation_gap: { title: "文献引用支撑不足 (Citation Gap Alert)", color: "var(--accent-amber)", bg: "var(--accent-amber-bg)" },
  citation_contradiction: { title: "文献论点冲突 (Citation Contradiction)", color: "var(--accent-rose)", bg: "var(--accent-rose-bg)" },
  semantic_plagiarism_risk: { title: "学术改写重合风险 (High Similarity Risk)", color: "var(--accent-amber)", bg: "var(--accent-amber-bg)" },
  style_heavy: { title: "句式臃肿与冗余 (Syntactic Overload)", color: "var(--accent-violet)", bg: "var(--accent-violet-bg)" },
  json_parse_error: { title: "格式解析异常 (Formatting Parse Alert)", color: "var(--text-secondary)", bg: "rgba(255,255,255,0.05)" },
  api_request_error: { title: "云端服务连接异常 (API Connection Alert)", color: "var(--text-secondary)", bg: "rgba(255,255,255,0.05)" },
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [sentences, setSentences] = useState<SentenceItem[]>([]);
  const [integrityWarnings, setIntegrityWarnings] = useState<DiagnosticResult[]>([]);
  const [allDiagnostics, setAllDiagnostics] = useState<Record<number, DiagnosticResult>>({});
  const [selectedSentenceIndex, setSelectedSentenceIndex] = useState<number | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  
  const sentenceRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const rightColumnRef = useRef<HTMLDivElement | null>(null);
  const [engineType, setEngineType] = useState('local');
  const [apiKey, setApiKey] = useState('');
  const [baseUrl, setBaseUrl] = useState('https://api.deepseek.com/v1');
  const [localModelStatus, setLocalModelStatus] = useState<'checking'|'exists'|'missing'|'downloading'>('checking');
  const [downloadProgress, setDownloadProgress] = useState(0);
  const [stats, setStats] = useState({ flaggedCount: 0, totalPPL: 0, pplCount: 0 });
  
  const [discipline, setDiscipline] = useState<string>('UNIVERSAL');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [activeTab, setActiveTab] = useState<'all' | 'passed' | 'ai' | 'flagged' | 'integrity'>('all');

  const [bibtexFile, setBibtexFile] = useState<File | null>(null);
  const [referenceFiles, setReferenceFiles] = useState<File[]>([]);
  const [referencesUploadStatus, setReferencesUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  
  const [runningRisks, setRunningRisks] = useState<{
    predictability: number;
    uniformity: number;
    translationese: number;
    redundancy: number;
  }>({
    predictability: 0,
    uniformity: 0,
    translationese: 0,
    redundancy: 0
  });

  useEffect(() => {
    if (theme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
  }, [theme]);

  useEffect(() => {
    fetch('/api/check_model')
      .then(r => r.json())
      .then(d => setLocalModelStatus(d.exists ? 'exists' : 'missing'))
      .catch(() => setLocalModelStatus('missing'));
  }, []);

  const copyToClipboard = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1800);
  };

  const downloadLocalModel = () => {
    setLocalModelStatus('downloading');
    setDownloadProgress(0);
    const source = new EventSource('/api/download_model');
    source.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.status === 'downloading') {
        setDownloadProgress(data.progress);
      } else if (data.status === 'complete') {
        source.close();
        setLocalModelStatus('exists');
      } else if (data.status === 'error') {
        source.close();
        setLocalModelStatus('missing');
        alert('Download failed: ' + data.message);
      }
    };
    source.onerror = () => {
      source.close();
      setLocalModelStatus('missing');
      alert('Connection error during download.');
    };
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const uploadedFile = e.target.files[0];
      setFile(uploadedFile);
      
      const formData = new FormData();
      formData.append("file", uploadedFile);
      
      try {
        const response = await fetch("/api/upload", {
          method: "POST",
          body: formData,
        });
        const data = await response.json();
        setDocumentText(data.text);
      } catch (err) {
        console.error("Failed to upload document", err);
      }
    }
  };

  const stopAnalysis = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsAnalyzing(false);
    setSentences(prev => prev.map(s => s.status === 'analyzing' ? { ...s, status: 'skipped' } : s));
  };

  const startAnalysis = async () => {
    if (!documentText) return;

    if ((engineType === 'local' || engineType.startsWith('hybrid')) && localModelStatus === 'missing') {
      alert("本地大模型尚未就绪。请先在顶栏点击 '下载本地模型'，或者切换至云端 Cloud 引擎。");
      return;
    }
    
    setIsAnalyzing(true);
    setIntegrityWarnings([]);
    setAllDiagnostics({});
    setSelectedSentenceIndex(null);
    setSentences([]);
    setStats({ flaggedCount: 0, totalPPL: 0, pplCount: 0 });
    setRunningRisks({ predictability: 0, uniformity: 0, translationese: 0, redundancy: 0 });
    
    let detectedDiscipline = 'UNIVERSAL';
    try {
      const detectRes = await fetch("/api/detect_discipline", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: documentText.substring(0, 1000),
          engine_type: engineType,
          api_key: apiKey,
          base_url: baseUrl
        })
      });
      const detectData = await detectRes.json();
      detectedDiscipline = detectData.discipline || 'UNIVERSAL';
      setDiscipline(detectedDiscipline);
    } catch (err) {
      console.error("Failed to detect discipline", err);
      setDiscipline('UNIVERSAL');
    }

    let sessionId: string;
    try {
      const sessionRes = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: documentText,
          engine_type: engineType,
          api_key: apiKey,
          base_url: baseUrl,
          discipline: detectedDiscipline
        })
      });
      const sessionData = await sessionRes.json();
      sessionId = sessionData.session_id;
    } catch (err) {
      console.error("Failed to register analysis session", err);
      alert("初始化质检会话失败，请检查网络或后端状态。");
      setIsAnalyzing(false);
      return;
    }

    if (bibtexFile || referenceFiles.length > 0) {
      setReferencesUploadStatus('uploading');
      const refFormData = new FormData();
      refFormData.append("session_id", sessionId);
      if (bibtexFile) {
        try {
          const bibText = await bibtexFile.text();
          refFormData.append("bibtex", bibText);
        } catch (err) {
          console.error("Failed to read BibTeX file", err);
        }
      }
      referenceFiles.forEach(file => {
        refFormData.append("files", file);
      });
      
      try {
        const uploadRes = await fetch("/api/upload_references", {
          method: "POST",
          body: refFormData
        });
        if (!uploadRes.ok) {
          throw new Error("Failed to upload references");
        }
        setReferencesUploadStatus('success');
      } catch (err) {
        console.error("Failed to upload references", err);
        setReferencesUploadStatus('error');
      }
    } else {
      setReferencesUploadStatus('idle');
    }

    const eventSource = new EventSource(`/api/diagnose?session_id=${sessionId}`);
    eventSourceRef.current = eventSource;
    
    eventSource.addEventListener("init", (e) => {
      const data = JSON.parse(e.data);
      setProgress({ current: 0, total: data.total_sentences });
      setSentences(Array(data.total_sentences).fill({ text: '', status: 'analyzing' }));
    });
    
    eventSource.addEventListener("result", (e) => {
      const data: DiagnosticResult = JSON.parse(e.data);
      
      setSentences(prev => {
        const next = [...prev];
        if (data.index >= 0) {
          next[data.index] = { 
            text: data.text, 
            status: data.status,
            ppl: data.ppl,
            metrics: data.metrics
          };
        }
        return next;
      });
      
      setStats(prev => {
        let newFlagged = prev.flaggedCount;
        let newTotalPPL = prev.totalPPL;
        let newPplCount = prev.pplCount;
        
        if (data.index >= 0 && data.status === 'flagged') newFlagged++;
        if (data.ppl !== null && !isNaN(data.ppl)) {
          newTotalPPL += data.ppl;
          newPplCount++;
        }
        
        return { flaggedCount: newFlagged, totalPPL: newTotalPPL, pplCount: newPplCount };
      });
      
      if (data.index < 0) {
        setIntegrityWarnings(prev => [...prev, data]);
      }
      
      if (data.index >= 0) {
        setAllDiagnostics(prev => ({ ...prev, [data.index]: data }));
      }
      
      setRunningRisks({
        predictability: Math.round(data.predictability_risk || 0),
        uniformity: Math.round(data.uniformity_risk || 0),
        translationese: Math.round(data.translationese_risk || 0),
        redundancy: Math.round(data.redundancy_risk || 0)
      });
      
      if (data.index >= 0) {
        setProgress(prev => ({ ...prev, current: prev.current + 1 }));
      }
    });
    
    eventSource.addEventListener("done", (e) => {
      setIsAnalyzing(false);
      try {
        const doneData = JSON.parse(e.data);
        setRunningRisks({
          predictability: Math.round(doneData.predictability_risk || 0),
          uniformity: Math.round(doneData.uniformity_risk || 0),
          translationese: Math.round(doneData.translationese_risk || 0),
          redundancy: Math.round(doneData.redundancy_risk || 0)
        });
      } catch (err) {
        console.error("Failed to parse done risks", err);
      }
      eventSource.close();
      eventSourceRef.current = null;
    });

    eventSource.addEventListener("error", (e) => {
      const errEvent = e as MessageEvent;
      try {
        const data = JSON.parse(errEvent.data);
        alert("质检流程异常: " + (data.error || data.message || "Unknown error"));
      } catch {
        // Handled silently
      }
      setIsAnalyzing(false);
      eventSource.close();
      eventSourceRef.current = null;
    });
    
    eventSource.onerror = () => {
      setIsAnalyzing(false);
      eventSource.close();
      eventSourceRef.current = null;
    };
  };

  const scrollToSentence = (index: number) => {
    setTimeout(() => {
      if (index >= 0 && sentenceRefs.current[index]) {
        sentenceRefs.current[index]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  const renderIntegrityReport = () => (
    <div className="glass-card slide-in" style={{ 
      marginTop: '16px', 
      border: '1px solid rgba(244, 63, 94, 0.3)',
      background: 'linear-gradient(180deg, rgba(244, 63, 94, 0.06) 0%, transparent 100%)'
    }}>
      <div className="card-header" style={{ color: 'var(--accent-rose)', marginBottom: '8px' }}>
        <AlertTriangle size={16} />
        <span>参考文献规范与完整性报告 (Citation Integrity)</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
        {integrityWarnings.map((w, idx) => (
          <div key={idx} style={{ 
            background: 'var(--bg-card-inner)', 
            borderRadius: '10px', 
            padding: '12px 14px', 
            fontSize: '13px',
            border: '1px solid var(--border-subtle)'
          }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              {w.text}
            </div>
            <div style={{ color: 'var(--accent-amber)', marginBottom: '6px', fontSize: '12px' }}>
              {w.explanation}
            </div>
            {w.suggestion && w.suggestion !== '-' && (
              <div style={{ color: 'var(--accent-emerald)', fontSize: '12px', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={13} />
                <span>建议: {w.suggestion}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderCitationAudit = (diag: DiagnosticResult) => {
    if (!diag.citation_audit || diag.citation_audit.length === 0) return null;
    
    return (
      <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <ShieldCheck size={14} color="var(--accent-cyan)" />
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)' }}>
            引用支撑性核验 (Citation Evidence Audit)
          </span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {diag.citation_audit.map((audit, aIdx) => {
            const isSupported = audit.status === 'SUPPORTED';
            const isContradicted = audit.status === 'CONTRADICTED';
            const badgeColor = isSupported ? 'var(--accent-emerald)' 
                             : isContradicted ? 'var(--accent-rose)' 
                             : 'var(--accent-amber)';
            const badgeBg = isSupported ? 'var(--accent-emerald-bg)' 
                           : isContradicted ? 'var(--accent-rose-bg)' 
                           : 'var(--accent-amber-bg)';
            const statusText = isSupported ? '完全支持 (Supported)' 
                             : isContradicted ? '论点矛盾 (Contradicted)' 
                             : audit.status === 'AUDIT_FAILED' ? '审计未竟' 
                             : '证据支撑偏弱';
            const sourceText = audit.source === 'local' ? '本地文献全文' : 'OpenAlex 实时摘要';
            const sourceColor = audit.source === 'local' ? 'var(--accent-cyan)' : 'var(--accent-indigo)';
            const sourceBg = audit.source === 'local' ? 'var(--accent-cyan-bg)' : 'var(--accent-indigo-bg)';
            
            return (
              <div 
                key={aIdx} 
                style={{ 
                  padding: '10px 12px', 
                  borderRadius: '8px', 
                  backgroundColor: 'var(--bg-card-inner)', 
                  border: '1px solid var(--border-subtle)', 
                  fontSize: '12px' 
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                    [{audit.key}] {audit.title.substring(0, 42)}{audit.title.length > 42 ? '...' : ''}
                  </span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '999px', fontWeight: 600, color: sourceColor, backgroundColor: sourceBg, border: `1px solid ${sourceBg}` }}>
                      {sourceText}
                    </span>
                    <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '999px', fontWeight: 600, color: badgeColor, backgroundColor: badgeBg, border: `1px solid ${badgeBg}` }}>
                      {statusText}
                    </span>
                  </div>
                </div>
                
                <p style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: '1.45', marginBottom: '6px' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>核验结论:</strong> {audit.explanation_zh}
                </p>
                
                {audit.evidence_snippet && (
                  <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                    <summary style={{ fontSize: '11px', color: 'var(--text-tertiary)', outline: 'none', userSelect: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <ChevronRight size={12} />
                      <span>查看引文证据原文 (Evidence Snippet)</span>
                    </summary>
                    <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '6px', fontStyle: 'italic', padding: '8px 10px', background: 'rgba(0,0,0,0.25)', borderRadius: '6px', border: '1px solid var(--border-subtle)', whiteSpace: 'pre-wrap', lineHeight: '1.4' }}>
                      "{audit.evidence_snippet}"
                    </p>
                  </details>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const DisciplineIcon = DISCIPLINE_MAP[discipline]?.icon || Layers;

  return (
    <div className="app-container">
      {/* Top Floating Glass Header */}
      <header className="header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ 
            width: '36px', 
            height: '36px', 
            borderRadius: '10px', 
            background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2) 0%, rgba(99, 102, 241, 0.25) 100%)',
            border: '1px solid var(--accent-cyan-glow)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px var(--accent-cyan-glow)'
          }}>
            <Sparkles size={20} color="var(--accent-cyan)" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '17px', fontWeight: '700', letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                RuScholar Studio
              </h1>
              <span style={{ 
                backgroundColor: 'rgba(0, 229, 255, 0.1)', 
                color: 'var(--accent-cyan)', 
                padding: '2px 8px', 
                borderRadius: '999px', 
                fontSize: '10px', 
                fontWeight: 700,
                border: '1px solid rgba(0, 229, 255, 0.25)',
                letterSpacing: '0.04em'
              }}>
                VAK / GOST 质检标准
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', letterSpacing: '-0.01em' }}>
              俄联邦学位论文自然化润色与多维真伪性核验工作台
            </div>
          </div>
        </div>

        <div style={{ flex: 1 }} />

        {/* Engine Controls & Cloud Key Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select 
            value={engineType} 
            onChange={e => setEngineType(e.target.value)}
            className="tech-select font-mono"
            style={{ fontSize: '12px' }}
          >
            <option value="local">Local: Qwen3-8B-GGUF (本地)</option>
            <option value="hybrid-pro">Hybrid: Local PPL + DeepSeek Pro</option>
            <option value="hybrid-flash">Hybrid: Local PPL + deepseek-flash</option>
            <option value="cloud-pro">Cloud: Pure DeepSeek Pro (纯云端)</option>
            <option value="deepseek-flash">Cloud: deepseek-flash (高速云端)</option>
          </select>
          
          {engineType !== 'local' && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                placeholder="Base URL" 
                value={baseUrl} 
                onChange={e => setBaseUrl(e.target.value)}
                className="tech-input font-mono"
                style={{ width: '170px', fontSize: '12px' }}
              />
              <input 
                type="password" 
                placeholder="API Key" 
                value={apiKey} 
                onChange={e => setApiKey(e.target.value)}
                className="tech-input font-mono"
                style={{ width: '140px', fontSize: '12px' }}
              />
            </div>
          )}

          {(engineType === 'local' || engineType.startsWith('hybrid')) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {localModelStatus === 'exists' && (
                <div style={{ 
                  color: 'var(--accent-emerald)', 
                  fontSize: '12px', 
                  fontWeight: 600,
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px',
                  backgroundColor: 'var(--accent-emerald-bg)',
                  padding: '5px 12px',
                  borderRadius: '999px',
                  border: '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  <span style={{ display: 'inline-block', width: '6px', height: '6px', backgroundColor: 'var(--accent-emerald)', borderRadius: '50%', boxShadow: '0 0 8px var(--accent-emerald)' }}></span>
                  <span>Qwen3 引擎在线</span>
                </div>
              )}
              {localModelStatus === 'missing' && (
                <button 
                  onClick={downloadLocalModel}
                  className="btn-primary"
                  style={{ padding: '6px 14px', fontSize: '12px' }}
                >
                  <Cpu size={14} />
                  下载本地模型
                </button>
              )}
              {localModelStatus === 'downloading' && (
                <div style={{ color: 'var(--accent-cyan)', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>下载模型中:</span>
                  <span className="font-mono" style={{ fontWeight: 'bold' }}>{Math.round(downloadProgress)}%</span>
                </div>
              )}
            </div>
          )}
          
          <button 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="btn-ghost"
            style={{ padding: '8px', borderRadius: '50%' }}
            title={theme === 'dark' ? "切换为明亮模式" : "切换为暗夜模式"}
          >
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>

          <a 
            href="https://github.com/Tanue-Hou/phd-thesis-butler" 
            target="_blank" 
            rel="noreferrer"
            className="btn-ghost font-mono"
            style={{ textDecoration: 'none', fontSize: '12px' }}
          >
            <ExternalLink size={14} />
            GitHub
          </a>
          
          {file && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {isAnalyzing ? (
                <>
                  <button className="btn-primary" disabled style={{ opacity: 0.85 }}>
                    <Activity size={14} className="pulse-fast" />
                    <span>质检中 {progress.current}/{progress.total}</span>
                  </button>
                  <button 
                    onClick={stopAnalysis}
                    className="btn-danger"
                  >
                    <Square size={13} />
                    停止
                  </button>
                </>
              ) : (
                <button className="btn-primary" onClick={startAnalysis}>
                  <Play size={14} />
                  启动多维质检
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Main Studio Viewport */}
      <main className="main-content">
        {/* Left Column: Manuscript Reading Station */}
        <div className="column-left">
          {!file ? (
            <div className="upload-zone-wrapper">
              <div className="upload-zone" onClick={() => document.getElementById('file-upload')?.click()}>
                <div className="upload-icon-halo">
                  <Upload size={32} color="var(--accent-cyan)" />
                </div>
                <h2 style={{ fontSize: '20px', fontWeight: '700', letterSpacing: '-0.02em', marginBottom: '8px' }}>
                  导入俄语学术手稿
                </h2>
                <p className="text-secondary" style={{ fontSize: '14px', maxWidth: '440px', textAlign: 'center', lineHeight: '1.5' }}>
                  拖拽或点击上传俄文学位论文或期刊草稿 (支持 <strong>.docx</strong>, <strong>.pdf</strong>, <strong>.txt</strong> 格式)
                </p>
                
                <input 
                  id="file-upload" 
                  type="file" 
                  accept=".docx,.pdf,.txt" 
                  style={{ display: 'none' }} 
                  onChange={handleFileUpload}
                />
              </div>

              {/* Private Literature Corpus Configuration */}
              <div 
                style={{
                  marginTop: '24px',
                  padding: '22px 26px',
                  borderRadius: '16px',
                  backgroundColor: 'var(--bg-surface-1)',
                  border: '1px solid var(--border-subtle)',
                  backdropFilter: 'blur(24px)',
                  width: '100%',
                  boxSizing: 'border-box',
                  boxShadow: 'var(--shadow-card)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'var(--accent-blue-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <BookOpen size={16} color="var(--accent-blue)" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '14px', fontWeight: '700', color: 'var(--text-primary)' }}>
                        本地文献全文核验库 (Corpus Reference Hub)
                      </h3>
                      <p style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginTop: '2px' }}>
                        选填：若未提供本地全文 PDF，系统将自动利用 OpenAlex 检索摘要进行证据真实性核实。
                      </p>
                    </div>
                  </div>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '16px' }}>
                  {/* BibTeX Entry Card */}
                  <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', borderRadius: '10px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>BibTeX 参考文献索引</div>
                      <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-tertiary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {bibtexFile ? bibtexFile.name : '尚未选择 (.bib)'}
                      </div>
                    </div>
                    <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                      <button 
                        type="button"
                        onClick={() => document.getElementById('bibtex-upload')?.click()}
                        className="btn-ghost font-mono"
                        style={{ fontSize: '11px', padding: '4px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}
                      >
                        {bibtexFile ? '替换文件' : '选择 .bib'}
                      </button>
                    </div>
                    <input 
                      id="bibtex-upload" 
                      type="file" 
                      accept=".bib" 
                      style={{ display: 'none' }} 
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          setBibtexFile(e.target.files[0]);
                        }
                      }}
                    />
                  </div>

                  {/* PDF Full-text Corpus Card */}
                  <div style={{ padding: '12px 14px', backgroundColor: 'var(--bg-card-inner)', border: '1px solid var(--border-subtle)', borderRadius: '10px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <div>
                      <div style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '4px' }}>参考论文 PDF 全文集</div>
                      <div className="font-mono" style={{ fontSize: '11px', color: 'var(--text-tertiary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {referenceFiles.length > 0 ? `已装载 ${referenceFiles.length} 篇参考论文` : '尚未选择 (.pdf 集合)'}
                      </div>
                    </div>
                    <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'flex-end' }}>
                      <button 
                        type="button"
                        onClick={() => document.getElementById('pdfs-upload')?.click()}
                        className="btn-ghost font-mono"
                        style={{ fontSize: '11px', padding: '4px 12px', borderRadius: '6px', border: '1px solid var(--border-subtle)', color: 'var(--accent-cyan)' }}
                      >
                        {referenceFiles.length > 0 ? '重新选择' : '批量导入 PDF'}
                      </button>
                    </div>
                    <input 
                      id="pdfs-upload" 
                      type="file" 
                      multiple 
                      accept=".pdf" 
                      style={{ display: 'none' }} 
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          setReferenceFiles(Array.from(e.target.files));
                        }
                      }}
                    />
                  </div>
                </div>

                {referencesUploadStatus !== 'idle' && (
                  <div style={{ marginTop: '14px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {referencesUploadStatus === 'uploading' && <span style={{ color: 'var(--accent-cyan)' }}>⏳ 正在建立语义检索索引与文献库注册...</span>}
                    {referencesUploadStatus === 'success' && <span style={{ color: 'var(--accent-emerald)' }}>✅ 文献库注册与 BM25 索引构建完毕</span>}
                    {referencesUploadStatus === 'error' && <span style={{ color: 'var(--accent-rose)' }}>❌ 文献库注册失败，将自动降级至在线检索模式</span>}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="document-viewer">
              {/* Document Status Header Bar */}
              <div 
                style={{
                  marginBottom: '24px',
                  padding: '14px 20px',
                  borderRadius: '12px',
                  backgroundColor: 'var(--bg-surface-1)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  boxShadow: 'var(--shadow-card)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <FileText size={18} color="var(--accent-cyan)" />
                  <div>
                    <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                      {file.name}
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', marginLeft: '12px' }}>
                      文献核验: {referencesUploadStatus === 'success' ? (
                        <strong style={{ color: 'var(--accent-emerald)' }}>本地全文证据库 ({referenceFiles.length} 篇)</strong>
                      ) : (
                        <strong style={{ color: 'var(--accent-blue)' }}>在线补位模式 (OpenAlex 实时核验)</strong>
                      )}
                    </span>
                  </div>
                </div>
                
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    onClick={() => {
                      setFile(null);
                      setDocumentText('');
                      setSentences([]);
                      setAllDiagnostics({});
                      setSelectedSentenceIndex(null);
                    }}
                    className="btn-ghost"
                    style={{ fontSize: '12px', padding: '5px 12px' }}
                  >
                    <RotateCcw size={13} />
                    重新导入手稿
                  </button>
                </div>
              </div>

              {/* Manuscript Reading Canvas */}
              <div className="document-canvas">
                {sentences.length === 0 ? (
                  <div style={{ whiteSpace: 'pre-wrap', color: 'var(--text-secondary)' }}>{documentText}</div>
                ) : (
                  sentences.map((s, idx) => (
                    <span 
                      key={idx} 
                      ref={el => { sentenceRefs.current[idx] = el; }}
                      className={`sentence ${s.status} ${selectedSentenceIndex === idx ? 'selected-highlight' : ''}`}
                      title={s.status}
                      onClick={() => {
                        setSelectedSentenceIndex(idx);
                        rightColumnRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                    >
                      {s.text}
                      {s.ppl !== undefined && s.ppl !== null && (
                        <sub 
                          className="ppl-tag font-mono" 
                          style={{ 
                            color: s.ppl < 15 ? 'var(--accent-rose)' : s.ppl < 25 ? 'var(--accent-amber)' : 'var(--text-tertiary)',
                          }}
                        >
                          PPL {s.ppl}
                        </sub>
                      )}
                      {' '}
                    </span>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: High-Tech Telemetry & Stream */}
        <div className="column-right" ref={rightColumnRef}>
          <div className="stream-container">
            {/* Academic Discipline Capsule */}
            {file && (
              <div className="glass-card" style={{ 
                marginBottom: '4px', 
                border: `1px solid ${DISCIPLINE_MAP[discipline]?.color || 'var(--border-subtle)'}`,
                background: 'linear-gradient(180deg, var(--bg-surface-1) 0%, var(--bg-card-inner) 100%)'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <DisciplineIcon size={16} color={DISCIPLINE_MAP[discipline]?.color || 'var(--accent-cyan)'} />
                    <span style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 700 }}>
                      学科领域智能归类 (Academic Domain)
                    </span>
                  </div>
                  <span style={{ 
                    fontSize: '11px', 
                    padding: '2px 8px', 
                    borderRadius: '999px', 
                    backgroundColor: 'rgba(255,255,255,0.06)', 
                    color: DISCIPLINE_MAP[discipline]?.color || 'var(--text-primary)',
                    fontWeight: 600,
                    fontFamily: 'var(--font-mono)'
                  }}>
                    {discipline}
                  </span>
                </div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  {DISCIPLINE_MAP[discipline]?.zh || '通用学术与跨学科领域'}
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {DISCIPLINE_MAP[discipline]?.en || 'Universal Academic Domain'}
                </div>
              </div>
            )}

            {/* Global Telemetry & Risk Matrix */}
            {progress.total > 0 && (
              <div className="glass-card" style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '16px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                      总体风格风险率 (Style Risk)
                    </div>
                    <div className="font-mono" style={{ fontSize: '24px', fontWeight: 800, marginTop: '2px', color: stats.flaggedCount > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                      {Math.round((stats.flaggedCount / progress.total) * 100)}%
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '11px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                      平均困惑度 (Avg PPL)
                    </div>
                    <div className="font-mono" style={{ fontSize: '24px', fontWeight: 800, marginTop: '2px', color: 'var(--accent-cyan)' }}>
                      {stats.pplCount > 0 ? (stats.totalPPL / stats.pplCount).toFixed(1) : '-'}
                    </div>
                  </div>
                </div>

                {/* 4 Multi-Channel Risk Gauges */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', borderTop: '1px solid var(--border-subtle)', paddingTop: '14px' }}>
                  {/* 1. Predictability */}
                  <div>
                    <div className="telemetry-row">
                      <span style={{ color: 'var(--text-secondary)' }}>可预测性特征 (Predictability Risk)</span>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-cyan)' }}>{runningRisks.predictability}%</span>
                    </div>
                    <div className="telemetry-track">
                      <div className="telemetry-fill" style={{ width: `${runningRisks.predictability}%`, background: 'linear-gradient(90deg, #00B4D8 0%, #00E5FF 100%)' }} />
                    </div>
                  </div>

                  {/* 2. Uniformity */}
                  <div>
                    <div className="telemetry-row">
                      <span style={{ color: 'var(--text-secondary)' }}>句式均匀度 (Uniformity Risk)</span>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-violet)' }}>{runningRisks.uniformity}%</span>
                    </div>
                    <div className="telemetry-track">
                      <div className="telemetry-fill" style={{ width: `${runningRisks.uniformity}%`, background: 'linear-gradient(90deg, #8B5CF6 0%, #C084FC 100%)' }} />
                    </div>
                  </div>

                  {/* 3. Translationese */}
                  <div>
                    <div className="telemetry-row">
                      <span style={{ color: 'var(--text-secondary)' }}>机器翻译腔 (Translationese Risk)</span>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-amber)' }}>{runningRisks.translationese}%</span>
                    </div>
                    <div className="telemetry-track">
                      <div className="telemetry-fill" style={{ width: `${runningRisks.translationese}%`, background: 'linear-gradient(90deg, #F59E0B 0%, #FBBF24 100%)' }} />
                    </div>
                  </div>

                  {/* 4. Redundancy */}
                  <div>
                    <div className="telemetry-row">
                      <span style={{ color: 'var(--text-secondary)' }}>语义冗余度 (Redundancy Risk)</span>
                      <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-rose)' }}>{runningRisks.redundancy}%</span>
                    </div>
                    <div className="telemetry-track">
                      <div className="telemetry-fill" style={{ width: `${runningRisks.redundancy}%`, background: 'linear-gradient(90deg, #E11D48 0%, #FB7185 100%)' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!file && (
              <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', marginTop: '80px', padding: '0 20px' }}>
                <Zap size={36} color="var(--text-tertiary)" style={{ opacity: 0.3, margin: '0 auto 16px auto' }} />
                <h4 style={{ fontSize: '15px', color: 'var(--text-secondary)', marginBottom: '6px' }}>质检控制台就绪</h4>
                <p style={{ fontSize: '12px', lineHeight: '1.6' }}>在左侧导入手稿后，此处将流式展示每一句话的 PPL 困惑度、词法结构指标与大模型推导链条。</p>
              </div>
            )}
            
            {/* Selected Sentence Inspector */}
            {file && (
              <div className="glass-card" style={{ 
                marginBottom: '16px', 
                border: '1px solid var(--accent-cyan)', 
                background: 'linear-gradient(180deg, rgba(0, 229, 255, 0.05) 0%, var(--bg-surface-1) 100%)',
                boxShadow: '0 0 20px var(--accent-cyan-glow)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Activity size={16} color="var(--accent-cyan)" />
                    <span style={{ fontWeight: 700, color: 'var(--accent-cyan)', fontSize: '13px', letterSpacing: '0.02em' }}>
                      风格透视控制台 (Sentence Inspector)
                    </span>
                  </div>
                  {selectedSentenceIndex !== null && (
                    <button 
                      onClick={() => setSelectedSentenceIndex(null)}
                      className="btn-ghost"
                      style={{ fontSize: '11px', padding: '2px 8px' }}
                    >
                      取消选定
                    </button>
                  )}
                </div>

                {selectedSentenceIndex === null ? (
                  <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', textAlign: 'center', padding: '16px 0', lineHeight: '1.6' }}>
                    💡 提示：点击左侧手稿中的任意句子，在此透视其深层词法统计、大模型反思推断以及润色重构建议。
                  </p>
                ) : (
                  <div>
                    {allDiagnostics[selectedSentenceIndex] ? (
                      <div>
                        <div style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.6', background: 'var(--bg-card-inner)', padding: '12px 14px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                          "{allDiagnostics[selectedSentenceIndex].text}"
                        </div>
                        
                        <div style={{ background: 'var(--bg-card-inner)', borderRadius: '10px', padding: '14px', fontSize: '12px', border: '1px solid var(--border-subtle)' }}>
                          <div className="metric-row">
                            <span className="text-secondary font-mono">PPL (Perplexity 困惑度)</span>
                            <span className="metric-value font-mono" style={{ 
                              color: allDiagnostics[selectedSentenceIndex].ppl && allDiagnostics[selectedSentenceIndex].ppl! < 15 ? 'var(--accent-rose)' : allDiagnostics[selectedSentenceIndex].ppl && allDiagnostics[selectedSentenceIndex].ppl! < 25 ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                              fontWeight: 700,
                              fontSize: '13px'
                            }}>
                              {allDiagnostics[selectedSentenceIndex].ppl !== null ? allDiagnostics[selectedSentenceIndex].ppl : '云端纯推理'}
                            </span>
                          </div>
                          
                          <div className="metric-row" style={{ marginTop: '8px' }}>
                            <span className="text-secondary">裁定状态 (Status)</span>
                            <span style={{ 
                              color: allDiagnostics[selectedSentenceIndex].status === 'flagged' ? 'var(--accent-rose)' : allDiagnostics[selectedSentenceIndex].status === 'early_exit' ? 'var(--accent-cyan)' : 'var(--accent-emerald)',
                              fontWeight: 700
                            }}>
                              {allDiagnostics[selectedSentenceIndex].status === 'flagged' ? '● 存在风格异状 (Flagged)' : allDiagnostics[selectedSentenceIndex].status === 'early_exit' ? '✓ 安全通过 (Early Exit)' : '✓ 专家标准通过 (Passed)'}
                            </span>
                          </div>

                          {allDiagnostics[selectedSentenceIndex].metrics && (
                            <div style={{ marginTop: '12px', padding: '10px 12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                                <div>名/动比率: <strong className="font-mono" style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.nv_ratio}</strong></div>
                                <div>被动语态频次: <strong className="font-mono" style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.passive_count}</strong></div>
                                <div>第二格长链数: <strong className="font-mono" style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.genitive_chains_count}</strong></div>
                                <div>学术套话命中: <strong className="font-mono" style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.cliches_count}</strong></div>
                              </div>
                            </div>
                          )}

                          {allDiagnostics[selectedSentenceIndex].think && (
                            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                              <details style={{ cursor: 'pointer' }}>
                                <summary style={{ color: 'var(--text-secondary)', fontSize: '11px', outline: 'none', userSelect: 'none', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <ChevronRight size={13} />
                                  <span>模型诊断思维链 (Reasoning Trace)</span>
                                </summary>
                                <div className="terminal-block">
                                  {allDiagnostics[selectedSentenceIndex].think}
                                </div>
                              </details>
                            </div>
                          )}

                          {allDiagnostics[selectedSentenceIndex].explanation && (
                            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', marginBottom: '4px' }}>
                                异状成因剖析
                              </div>
                              <p style={{ color: allDiagnostics[selectedSentenceIndex].issue_type === 'json_parse_error' ? 'var(--accent-rose)' : 'var(--accent-amber)', lineHeight: '1.5' }}>
                                {allDiagnostics[selectedSentenceIndex].explanation}
                              </p>
                            </div>
                          )}

                          {allDiagnostics[selectedSentenceIndex].suggestion && allDiagnostics[selectedSentenceIndex].suggestion !== 'N/A' && allDiagnostics[selectedSentenceIndex].suggestion !== '-' && (
                            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)' }}>
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                  <Sparkles size={13} />
                                  <span>学界标准改写建议 (Revision Suggestion)</span>
                                </div>
                                <button 
                                  onClick={() => copyToClipboard(allDiagnostics[selectedSentenceIndex].suggestion || '', `sugg-${selectedSentenceIndex}`)}
                                  className="btn-ghost"
                                  style={{ padding: '2px 8px', fontSize: '11px', borderRadius: '4px' }}
                                >
                                  {copiedKey === `sugg-${selectedSentenceIndex}` ? (
                                    <>
                                      <Check size={12} color="var(--accent-emerald)" />
                                      <span style={{ color: 'var(--accent-emerald)' }}>已复制</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy size={12} />
                                      <span>复制</span>
                                    </>
                                  )}
                                </button>
                              </div>
                              <div style={{ 
                                color: 'var(--accent-emerald)', 
                                fontWeight: 500, 
                                lineHeight: '1.5',
                                padding: '8px 10px',
                                background: 'var(--accent-emerald-bg)',
                                borderRadius: '6px',
                                border: '1px solid rgba(16, 185, 129, 0.2)'
                              }}>
                                {allDiagnostics[selectedSentenceIndex].suggestion}
                              </div>
                            </div>
                          )}
                          
                          {renderCitationAudit(allDiagnostics[selectedSentenceIndex])}
                        </div>
                      </div>
                    ) : (
                      <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', textAlign: 'center', padding: '10px 0' }}>
                        句段选中，正在等待诊断流反馈...
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Filter Tabs & Diagnostic Stream */}
            {(() => {
              const sortedDiagnostics = Object.values(allDiagnostics).sort((a, b) => a.index - b.index);
              const passedCount = sortedDiagnostics.filter(d => d.status !== 'flagged').length;
              const aiCount = sortedDiagnostics.filter(d => d.status === 'flagged' && d.issue_type === 'ai_generated_suspicion').length;
              const styleCount = sortedDiagnostics.filter(d => d.status === 'flagged' && d.issue_type !== 'ai_generated_suspicion' && d.issue_type !== 'citation_gap' && d.issue_type !== 'citation_contradiction').length;
              const sentenceIntegrityCount = sortedDiagnostics.filter(d => d.status === 'flagged' && (d.issue_type === 'citation_gap' || d.issue_type === 'citation_contradiction')).length;
              const integrityCount = integrityWarnings.length + sentenceIntegrityCount;

              return (
                <>
                  {file && progress.total > 0 && (
                    <div className="tabs-row">
                      <div className="tabs-container">
                        <button 
                          className={`tab-btn ${activeTab === 'all' ? 'active' : ''}`}
                          onClick={() => setActiveTab('all')}
                        >
                          全部 ({sortedDiagnostics.length + integrityWarnings.length})
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === 'passed' ? 'active' : ''}`}
                          onClick={() => setActiveTab('passed')}
                        >
                          无风险 ({passedCount})
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
                          onClick={() => setActiveTab('ai')}
                        >
                          AI特征 ({aiCount})
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === 'flagged' ? 'active' : ''}`}
                          onClick={() => setActiveTab('flagged')}
                        >
                          学术套话 ({styleCount})
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === 'integrity' ? 'active' : ''}`}
                          onClick={() => setActiveTab('integrity')}
                        >
                          引文冲突 ({integrityCount})
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Render Diagnostic Items */}
                  {sortedDiagnostics
                    .filter(diag => {
                      if (activeTab === 'all') return true;
                      if (activeTab === 'passed') return diag.status !== 'flagged';
                      if (activeTab === 'ai') return diag.status === 'flagged' && diag.issue_type === 'ai_generated_suspicion';
                      if (activeTab === 'flagged') return diag.status === 'flagged' && diag.issue_type !== 'ai_generated_suspicion' && diag.issue_type !== 'citation_gap' && diag.issue_type !== 'citation_contradiction';
                      if (activeTab === 'integrity') return diag.status === 'flagged' && (diag.issue_type === 'citation_gap' || diag.issue_type === 'citation_contradiction');
                      return true;
                    })
                    .map((diag) => {
                      const isFlagged = diag.status === 'flagged';
                      const issueInfo = ISSUE_TITLE_MAP[diag.issue_type || ''] || { 
                        title: "学术风格提示 (Style Notice)", 
                        color: "var(--accent-amber)",
                        bg: "var(--accent-amber-bg)"
                      };
                      const cardAccent = !isFlagged ? 'var(--accent-emerald)' : issueInfo.color;

                      return (
                        <div 
                          key={diag.index}
                          className="diag-card slide-in" 
                          onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                          style={{ 
                            '--card-accent': cardAccent,
                            '--card-accent-glow': isFlagged ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)'
                          } as React.CSSProperties}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <div className="card-header" style={{ color: isFlagged ? issueInfo.color : 'var(--accent-emerald)', margin: 0 }}>
                              {isFlagged ? (
                                <>
                                  <AlertCircle size={15} color={issueInfo.color} />
                                  <span>{issueInfo.title}</span>
                                </>
                              ) : (
                                <>
                                  <CheckCircle2 size={15} color="var(--accent-emerald)" />
                                  <span>学界规范通过 (Clean Scholastic Style)</span>
                                </>
                              )}
                            </div>

                            <span className="font-mono" style={{ 
                              fontSize: '11px', 
                              fontWeight: 700, 
                              color: diag.ppl && diag.ppl < 15 ? 'var(--accent-rose)' : diag.ppl && diag.ppl < 25 ? 'var(--accent-amber)' : 'var(--accent-emerald)',
                              backgroundColor: 'rgba(0,0,0,0.3)',
                              padding: '2px 6px',
                              borderRadius: '4px'
                            }}>
                              {diag.ppl !== null ? `PPL ${diag.ppl}` : 'PPL -'}
                            </span>
                          </div>
                          
                          <p style={{ fontSize: '13px', color: 'var(--text-primary)', marginBottom: '10px', lineHeight: '1.5' }}>
                            "{diag.text.substring(0, 85)}{diag.text.length > 85 ? '...' : ''}"
                          </p>
                          
                          <div style={{ background: 'var(--bg-card-inner)', borderRadius: '8px', padding: '10px 12px', fontSize: '12px', border: '1px solid var(--border-subtle)' }}>
                            {diag.explanation && (
                              <div style={{ marginBottom: '6px' }}>
                                <p style={{ color: isFlagged ? 'var(--text-secondary)' : 'var(--accent-emerald)', lineHeight: '1.4' }}>
                                  {diag.explanation}
                                </p>
                              </div>
                            )}

                            {diag.suggestion && diag.suggestion !== 'N/A' && diag.suggestion !== '-' && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-emerald)', fontWeight: 600, fontSize: '11px', marginBottom: '2px' }}>
                                  <Sparkles size={12} />
                                  <span>建议改写:</span>
                                </div>
                                <p style={{ color: 'var(--accent-emerald)', fontWeight: 500, fontSize: '12px' }}>
                                  {diag.suggestion}
                                </p>
                              </div>
                            )}

                            {diag.think && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
                                <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                  <summary style={{ color: 'var(--text-tertiary)', outline: 'none', userSelect: 'none', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <ChevronRight size={12} />
                                    <span>展开模型思考推断 (Think Chain)</span>
                                  </summary>
                                  <div className="terminal-block">
                                    {diag.think}
                                  </div>
                                </details>
                              </div>
                            )}

                            {renderCitationAudit(diag)}
                          </div>
                        </div>
                      );
                    })}

                  {(activeTab === 'all' || activeTab === 'integrity') && integrityWarnings.length > 0 && renderIntegrityReport()}
                </>
              );
            })()}
            
            {isAnalyzing && (
              <div className="glass-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px', padding: '24px' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', border: '2px solid var(--border-subtle)', borderTopColor: 'var(--accent-cyan)', animation: 'spin 0.8s linear infinite' }} />
                <span style={{ fontSize: '13px', color: 'var(--accent-cyan)', fontWeight: 500 }}>深度神经网络质检计算中...</span>
                <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
              </div>
            )}
            
            {/* Future Extension Modules */}
            {progress.total > 0 && progress.current === progress.total && !isAnalyzing && (
              <div className="glass-card" style={{ marginTop: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '12px' }}>
                  <Zap size={14} color="var(--accent-cyan)" />
                  <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
                    论文深度工程扩展 (Thesis Extension Suite)
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                  <button className="btn-ghost" style={{ justifyContent: 'flex-start', padding: '10px 12px', background: 'var(--bg-card-inner)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    ✨ 全文自然化润色
                  </button>
                  <button className="btn-ghost" style={{ justifyContent: 'flex-start', padding: '10px 12px', background: 'var(--bg-card-inner)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    📚 GOST 参考文献修补
                  </button>
                  <button className="btn-ghost" style={{ justifyContent: 'flex-start', padding: '10px 12px', background: 'var(--bg-card-inner)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    📏 鲍曼/GOST 排版核查
                  </button>
                  <button className="btn-ghost" style={{ justifyContent: 'flex-start', padding: '10px 12px', background: 'var(--bg-card-inner)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                    🏗️ 章节逻辑骨架审阅
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
