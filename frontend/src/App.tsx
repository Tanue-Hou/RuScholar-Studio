import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, AlertCircle, LayoutDashboard, Sun, Moon } from 'lucide-react';
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

const DISCIPLINE_MAP: Record<string, { en: string; zh: string; color: string }> = {
  SCI_TECH: { en: "Sci-Tech (Physical Sciences & Engineering)", zh: "理工科 (自然科学⟣工程技术)", color: "var(--apple-blue-text)" },
  AUTOMATION_CONTROL: { en: "Automation & Control Engineering", zh: "自动化与控制工程", color: "var(--apple-orange-text)" },
  AGRI_MED: { en: "Agricultural & Medical Sciences", zh: "农田与医药生命科学", color: "var(--apple-green-text)" },
  HUM_POL_ECON: { en: "Humanities & Social Sciences", zh: "人文社科 (政治经济与社会科学)", color: "var(--apple-purple-text)" },
  ARTS_SPORTS: { en: "Arts, Sports & Culture", zh: "艺术体育与文化研究", color: "var(--apple-pink-text)" },
  UNIVERSAL: { en: "Universal Academic Domain", zh: "通用学术与跨学科领域", color: "var(--text-secondary)" }
};

const ISSUE_TITLE_MAP: Record<string, { title: string; color: string }> = {
  ai_generated_suspicion: { title: "AI 生成特征预警 (AI Writing Detected)", color: "var(--apple-red-text)" },
  machine_translation_cliche: { title: "机器翻译与学术套话 (Translationese & Cliché)", color: "var(--apple-orange-text)" },
  citation_gap: { title: "引用支撑不足 (Citation Gap Alert)", color: "var(--apple-orange-text)" },
  citation_contradiction: { title: "文献论点冲突 (Citation Contradiction)", color: "var(--apple-red-text)" },
  semantic_plagiarism_risk: { title: "学术改写重合风险 (High Similarity Risk)", color: "var(--apple-orange-text)" },
  style_heavy: { title: "句式臃肿与冗余 (Style Overloaded)", color: "var(--apple-purple-text)" },
  json_parse_error: { title: "格式解析异常 (Formatting Parse Alert)", color: "var(--text-secondary)" },
  api_request_error: { title: "云端服务连接异常 (API Connection Alert)", color: "var(--text-secondary)" },
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
      
      // Upload to backend to parse
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
      alert("本地大模型尚未就绪。请先在顶栏点击 'Download Local Model' 下载并初始化大模型，或者切换到纯云端 Cloud 引擎。");
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

    // Register session via POST to protect sensitive details and api keys
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
      alert("Failed to initialize secure session.");
      setIsAnalyzing(false);
      return;
    }

    // Upload references if any are selected
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
        alert("Failed to upload references. The system will automatically fallback to online retrieval.");
      }
    } else {
      setReferencesUploadStatus('idle');
    }

    // Connect to SSE using session_id
    const eventSource = new EventSource(`/api/diagnose?session_id=${sessionId}`);
    eventSourceRef.current = eventSource;
    
    eventSource.addEventListener("init", (e) => {
      const data = JSON.parse(e.data);
      setProgress({ current: 0, total: data.total_sentences });
      // Initialize sentence array placeholder
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
      
      // Update running style risks calculated strictly on the backend
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
        alert("Analysis Error: " + (data.error || data.message || "Unknown error"));
      } catch {
        alert("Analysis Error occurred.");
      }
      setIsAnalyzing(false);
      eventSource.close();
      eventSourceRef.current = null;
    });
    
    eventSource.onerror = () => {
      console.error("SSE Error");
      setIsAnalyzing(false);
      eventSource.close();
      eventSourceRef.current = null;
    };
  };

  const renderIntegrityReport = () => (
    <div className="glass-card slide-in" style={{ 
      marginTop: '16px', 
      borderLeft: '4px solid var(--apple-red-text)'
    }}>
      <div className="card-header" style={{ color: 'var(--apple-red-text)', marginBottom: '8px' }}>
        <AlertCircle size={16} color="var(--apple-red-text)" />
        <span style={{ fontWeight: 600 }}>参考文献规范与完整性报告 (Citation Integrity Report)</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
        {integrityWarnings.map((w, idx) => (
          <div key={idx} style={{ 
            background: 'var(--card-inner-bg)', 
            borderRadius: '8px', 
            padding: '10px 12px', 
            fontSize: '13px' 
          }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
              {w.text}
            </div>
            <div style={{ color: 'var(--apple-orange-text)', marginBottom: '4px' }}>
              {w.explanation}
            </div>
            {w.suggestion && w.suggestion !== '-' && (
              <div style={{ color: 'var(--apple-green-text)', fontSize: '12px', fontWeight: 500 }}>
                💡 建议: {w.suggestion}
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
      <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid var(--glass-border)' }}>
        <p className="text-secondary" style={{ marginBottom: '6px', fontSize: '11px', fontWeight: 600 }}>
          引用与证据核验 (Citation Audit)
        </p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {diag.citation_audit.map((audit, aIdx) => {
            const badgeColor = audit.status === 'SUPPORTED' ? 'var(--apple-green-text)' 
                             : audit.status === 'CONTRADICTED' ? 'var(--apple-red-text)' 
                             : audit.status === 'AUDIT_FAILED' ? 'var(--text-tertiary)' 
                             : 'var(--apple-orange-text)';
            const badgeBg = audit.status === 'SUPPORTED' ? 'rgba(52, 199, 89, 0.1)' 
                           : audit.status === 'CONTRADICTED' ? 'rgba(255, 69, 58, 0.1)' 
                           : audit.status === 'AUDIT_FAILED' ? 'rgba(142, 142, 147, 0.1)' 
                           : 'rgba(255, 159, 10, 0.1)';
            const statusText = audit.status === 'SUPPORTED' ? '完全支持' 
                             : audit.status === 'CONTRADICTED' ? '论点矛盾' 
                             : audit.status === 'AUDIT_FAILED' ? '审计未完成' 
                             : '支持度不足/弱引用';
            const sourceText = audit.source === 'local' ? '本地全文库' : '在线文献摘要';
            const sourceBg = audit.source === 'local' ? 'rgba(0, 122, 255, 0.1)' : 'rgba(120, 86, 214, 0.1)';
            const sourceColor = audit.source === 'local' ? 'var(--apple-blue-text)' : 'var(--apple-purple-text)';
            
            return (
              <div 
                key={aIdx} 
                style={{ 
                  padding: '8px 10px', 
                  borderRadius: '6px', 
                  backgroundColor: 'rgba(255, 255, 255, 0.02)', 
                  border: '1px solid var(--glass-border)', 
                  fontSize: '12px' 
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', marginBottom: '6px', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    [{audit.key}] {audit.title.substring(0, 45)}{audit.title.length > 45 ? '...' : ''}
                  </span>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '4px', fontWeight: 600, color: sourceColor, backgroundColor: sourceBg }}>
                      {sourceText}
                    </span>
                    <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '4px', fontWeight: 600, color: badgeColor, backgroundColor: badgeBg }}>
                      {statusText}
                    </span>
                  </div>
                </div>
                
                <p style={{ color: 'var(--text-secondary)', fontSize: '12px', lineHeight: '1.4', marginBottom: '6px' }}>
                  <strong>核验分析:</strong> {audit.explanation_zh}
                </p>
                
                {audit.evidence_snippet && (
                  <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                    <summary style={{ fontSize: '10px', color: 'var(--text-tertiary)', outline: 'none', userSelect: 'none' }}>
                      ▶ 查看文献证据原文 (Evidence Snippet)
                    </summary>
                    <p style={{ fontSize: '11px', color: 'var(--text-tertiary)', marginTop: '4px', fontStyle: 'italic', padding: '6px', background: 'rgba(0,0,0,0.1)', borderRadius: '4px', whiteSpace: 'pre-wrap', lineHeight: '1.3' }}>
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

  const scrollToSentence = (index: number) => {
    setTimeout(() => {
      if (index >= 0 && sentenceRefs.current[index]) {
        sentenceRefs.current[index]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 50);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <LayoutDashboard size={24} color="var(--apple-orange)" />
          <h1 style={{ fontSize: '20px', fontWeight: '600', letterSpacing: '-0.5px' }}>PhD Thesis Butler</h1>
          <span style={{ color: 'var(--text-tertiary)', margin: '0 8px' }}>|</span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '15px' }}>Style Diagnostics</span>
          <span style={{ 
            backgroundColor: 'rgba(255, 69, 58, 0.1)', 
            color: 'var(--apple-red-text)', 
            padding: '2px 8px', 
            borderRadius: '4px', 
            fontSize: '11px', 
            fontWeight: 600,
            marginLeft: '8px'
          }}>
            仅供参考 (Reference Only)
          </span>
        </div>
        <div style={{ flex: 1 }} />
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <select 
            value={engineType} 
            onChange={e => setEngineType(e.target.value)}
            style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px' }}
          >
            <option value="local">Local: Qwen3-4B-GGUF</option>
            <option value="hybrid-pro">Hybrid: Local PPL + DeepSeek Pro</option>
            <option value="hybrid-flash">Hybrid: Local PPL + DeepSeek Flash</option>
            <option value="cloud-pro">Cloud: Pure DeepSeek Pro</option>
            <option value="cloud-flash">Cloud: Pure DeepSeek Flash</option>
          </select>
          
          {engineType !== 'local' && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <input 
                type="text" 
                placeholder="Base URL" 
                value={baseUrl} 
                onChange={e => setBaseUrl(e.target.value)}
                style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', width: '180px' }}
              />
              <input 
                type="password" 
                placeholder="API Key" 
                value={apiKey} 
                onChange={e => setApiKey(e.target.value)}
                style={{ backgroundColor: 'var(--glass-bg)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', width: '150px' }}
              />
            </div>
          )}

          {(engineType === 'local' || engineType.startsWith('hybrid')) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {localModelStatus === 'exists' && (
                <div style={{ 
                  color: '#34c759', 
                  fontSize: '13px', 
                  fontWeight: 500,
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '6px',
                  backgroundColor: 'rgba(52, 199, 89, 0.15)',
                  padding: '4px 10px',
                  borderRadius: '12px',
                  border: '1px solid rgba(52, 199, 89, 0.3)'
                }}>
                  <span>本地模型已就绪</span>
                  <span style={{ display: 'inline-block', width: '6px', height: '6px', backgroundColor: '#34c759', borderRadius: '50%' }}></span>
                </div>
              )}
              {localModelStatus === 'missing' && (
                <button 
                  onClick={downloadLocalModel}
                  style={{ backgroundColor: 'var(--apple-blue)', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', cursor: 'pointer' }}
                >
                  Download Local Model
                </button>
              )}
              {localModelStatus === 'downloading' && (
                <div style={{ color: 'var(--apple-blue)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span>正在下载模型:</span>
                  <span style={{ fontWeight: 'bold' }}>{Math.round(downloadProgress)}%</span>
                </div>
              )}
            </div>
          )}
          
          <button 
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            style={{ 
              backgroundColor: 'transparent', 
              color: 'var(--text-secondary)', 
              border: 'none', 
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '6px'
            }}
            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>

          <a 
            href="https://github.com/Tanue-Hou/phd-thesis-butler" 
            target="_blank" 
            rel="noreferrer"
            style={{ color: 'var(--text-secondary)', fontSize: '13px', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <svg height="16" viewBox="0 0 16 16" width="16" fill="currentColor"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"></path></svg>
            phd-thesis-butler
          </a>
          
          {file && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {isAnalyzing ? (
                <>
                  <button className="btn-primary" disabled style={{ opacity: 0.7 }}>
                    Analyzing... {progress.current}/{progress.total}
                  </button>
                  <button 
                    onClick={stopAnalysis}
                    style={{ 
                      backgroundColor: 'var(--apple-red)', 
                      color: 'white', 
                      border: 'none', 
                      borderRadius: '20px', 
                      padding: '8px 16px', 
                      fontWeight: 600, 
                      cursor: 'pointer',
                      fontSize: '14px',
                      boxShadow: '0 2px 8px rgba(255, 69, 58, 0.3)'
                    }}
                  >
                    Stop
                  </button>
                </>
              ) : (
                <button className="btn-primary" onClick={startAnalysis}>
                  Run Analysis
                </button>
              )}
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Left Column: Document Viewer */}
        <div className="column-left">
          {!file ? (
            <div className="upload-zone" onClick={() => document.getElementById('file-upload')?.click()}>
              <Upload size={48} color="var(--text-secondary)" style={{ marginBottom: '16px' }} />
              <h2>Upload Manuscript</h2>
              <p className="text-secondary" style={{ marginTop: '8px' }}>Drag & drop your .docx, .pdf or .txt file here</p>
              <input 
                id="file-upload" 
                type="file" 
                accept=".docx,.pdf,.txt" 
                style={{ display: 'none' }} 
                onChange={handleFileUpload}
              />
              
              <div 
                style={{
                  marginTop: '28px',
                  padding: '16px 20px',
                  borderRadius: '12px',
                  backgroundColor: 'var(--glass-bg)',
                  border: '1px solid var(--glass-border)',
                  backdropFilter: 'blur(10px)',
                  width: '100%',
                  maxWidth: '460px',
                  boxSizing: 'border-box',
                  textAlign: 'left'
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-primary)' }}>
                  <FileText size={16} color="var(--apple-blue)" />
                  本地文献核验库 (选填)
                </h3>
                <p style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '14px', lineHeight: '1.4' }}>
                  如果不提供本地 PDF，系统诊断时将自动解析正文引文与文末参考文献，并联网（OpenAlex）获取摘要进行真实性核验。
                </p>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--glass-border)', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', marginRight: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: '500', color: 'var(--text-primary)' }}>BibTeX 文献数据库</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {bibtexFile ? bibtexFile.name : '未选择 (.bib)'}
                      </span>
                    </div>
                    <button 
                      type="button"
                      onClick={() => document.getElementById('bibtex-upload')?.click()}
                      style={{ fontSize: '11px', padding: '4px 10px', border: '1px solid var(--apple-blue)', color: 'var(--apple-blue)', backgroundColor: 'transparent', borderRadius: '4px', cursor: 'pointer', fontWeight: '500', flexShrink: 0 }}
                    >
                      {bibtexFile ? '替换' : '选择'}
                    </button>
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

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', backgroundColor: 'rgba(255,255,255,0.02)', border: '1px solid var(--glass-border)', borderRadius: '6px' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', marginRight: '8px' }}>
                      <span style={{ fontSize: '12px', fontWeight: '500', color: 'var(--text-primary)' }}>参考文献 PDF 列表</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-tertiary)', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                        {referenceFiles.length > 0 ? `已选择 ${referenceFiles.length} 个文件` : '未选择 (.pdf)'}
                      </span>
                    </div>
                    <button 
                      type="button"
                      onClick={() => document.getElementById('pdfs-upload')?.click()}
                      style={{ fontSize: '11px', padding: '4px 10px', border: '1px solid var(--apple-blue)', color: 'var(--apple-blue)', backgroundColor: 'transparent', borderRadius: '4px', cursor: 'pointer', fontWeight: '500', flexShrink: 0 }}
                    >
                      {referenceFiles.length > 0 ? '重选' : '选择'}
                    </button>
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
                  <div style={{ marginTop: '10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    {referencesUploadStatus === 'uploading' && <span style={{ color: 'var(--apple-blue)' }}>⏳ 正在向会话注册文献库...</span>}
                    {referencesUploadStatus === 'success' && <span style={{ color: 'var(--apple-green-text)' }}>✅ 文献库注册绑定成功</span>}
                    {referencesUploadStatus === 'error' && <span style={{ color: 'var(--apple-red-text)' }}>❌ 文献库注册失败 (自动回退至在线模式)</span>}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="document-viewer">
              <div 
                style={{
                  marginBottom: '20px',
                  padding: '12px 16px',
                  borderRadius: '8px',
                  backgroundColor: 'var(--glass-bg)',
                  border: '1px solid var(--glass-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  fontSize: '13px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={16} color="var(--apple-blue)" />
                  <span>
                    文献核验模式: {' '}
                    {referencesUploadStatus === 'success' ? (
                      <strong style={{ color: 'var(--apple-green-text)' }}>本地文献库已绑定 ({referenceFiles.length} PDF)</strong>
                    ) : (
                      <strong style={{ color: 'var(--apple-blue-text)' }}>在线补位模式已激活 (基于 OpenAlex 摘要核验)</strong>
                    )}
                  </span>
                </div>
                <button 
                  onClick={() => {
                    setBibtexFile(null);
                    setReferenceFiles([]);
                    setReferencesUploadStatus('idle');
                  }}
                  style={{ fontSize: '11px', padding: '4px 8px', border: '1px solid var(--glass-border)', color: 'var(--text-secondary)', backgroundColor: 'transparent', borderRadius: '4px', cursor: 'pointer' }}
                >
                  重置文献库
                </button>
              </div>

              {sentences.length === 0 ? (
                <div style={{ whiteSpace: 'pre-wrap' }}>{documentText}</div>
              ) : (
                sentences.map((s, idx) => (
                  <span 
                    key={idx} 
                    ref={el => { sentenceRefs.current[idx] = el; }}
                    className={`sentence ${s.status} ${selectedSentenceIndex === idx ? 'selected-highlight' : ''}`}
                    title={s.status}
                    style={{ cursor: 'pointer' }}
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
                          color: s.ppl < 15 ? 'var(--apple-red-text)' : s.ppl < 25 ? 'var(--apple-orange-text)' : 'var(--text-secondary)',
                          marginLeft: '4px',
                          fontSize: '10px',
                          verticalAlign: 'sub',
                          opacity: 0.8,
                          userSelect: 'none'
                        }}
                      >
                        {s.ppl}
                      </sub>
                    )}
                    {' '}
                  </span>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right Column: Diagnostics Stream */}
        <div className="column-right" ref={rightColumnRef}>
          <div className="stream-container">
            {file && (
              <div className="glass-card" style={{ marginBottom: '8px', borderLeft: `4px solid ${DISCIPLINE_MAP[discipline]?.color || 'var(--text-secondary)'}`, transition: 'all 0.5s ease' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Academic Discipline / 学科领域分类
                </div>
                <div style={{ fontSize: '16px', fontWeight: 600, marginTop: '4px', color: DISCIPLINE_MAP[discipline]?.color || 'var(--text-primary)' }}>
                  {DISCIPLINE_MAP[discipline]?.en || 'Universal Academic'}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                  {DISCIPLINE_MAP[discipline]?.zh || '通用学术与跨学科领域'}
                </div>
              </div>
            )}

            {/* Global Stats & Telemetry */}
            {progress.total > 0 && (
              <div className="glass-card" style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div>
                    <div className="text-secondary" style={{ fontSize: '12px' }}>Style Risk / 风格风险率</div>
                    <div style={{ fontSize: '20px', fontWeight: 600, color: stats.flaggedCount > 0 ? 'var(--apple-red-text)' : 'var(--apple-green-text)' }}>
                      {Math.round((stats.flaggedCount / progress.total) * 100)}%
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="text-secondary" style={{ fontSize: '12px' }}>Avg Perplexity (PPL)</div>
                    <div style={{ fontSize: '20px', fontWeight: 600, color: 'var(--apple-orange-text)' }}>
                      {stats.pplCount > 0 ? (stats.totalPPL / stats.pplCount).toFixed(1) : '-'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', borderTop: '1px solid var(--glass-border)', paddingTop: '14px' }}>
                  {/* 1. Predictability Risk */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Predictability Risk (可预测性风险)</span>
                      <span style={{ fontWeight: 600, color: 'var(--apple-blue-text)' }}>{runningRisks.predictability}%</span>
                    </div>
                    <div style={{ height: '6px', background: 'var(--card-inner-bg)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${runningRisks.predictability}%`, background: 'var(--apple-blue)', borderRadius: '3px', transition: 'width 0.3s ease' }} />
                    </div>
                  </div>

                  {/* 2. Uniformity Risk */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Uniformity Risk (句式均匀性风险)</span>
                      <span style={{ fontWeight: 600, color: 'var(--apple-purple-text)' }}>{runningRisks.uniformity}%</span>
                    </div>
                    <div style={{ height: '6px', background: 'var(--card-inner-bg)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${runningRisks.uniformity}%`, background: 'var(--apple-purple)', borderRadius: '3px', transition: 'width 0.3s ease' }} />
                    </div>
                  </div>

                  {/* 3. Translationese Risk */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Translationese Risk (翻译腔风险)</span>
                      <span style={{ fontWeight: 600, color: 'var(--apple-orange-text)' }}>{runningRisks.translationese}%</span>
                    </div>
                    <div style={{ height: '6px', background: 'var(--card-inner-bg)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${runningRisks.translationese}%`, background: 'var(--apple-orange)', borderRadius: '3px', transition: 'width 0.3s ease' }} />
                    </div>
                  </div>

                  {/* 4. Redundancy Risk */}
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
                      <span style={{ color: 'var(--text-secondary)' }}>Redundancy Risk (语义冗余风险)</span>
                      <span style={{ fontWeight: 600, color: 'var(--apple-red-text)' }}>{runningRisks.redundancy}%</span>
                    </div>
                    <div style={{ height: '6px', background: 'var(--card-inner-bg)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${runningRisks.redundancy}%`, background: 'var(--apple-red)', borderRadius: '3px', transition: 'width 0.3s ease' }} />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {!file && (
              <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', marginTop: '40px' }}>
                <FileText size={48} style={{ opacity: 0.2, margin: '0 auto 16px auto' }} />
                <p>Upload a document to begin the<br/>AI diagnostics stream.</p>
              </div>
            )}
            
            {/* Selected Sentence Inspector */}
            {file && (
              <div className="glass-card" style={{ 
                marginBottom: '20px', 
                border: '1px solid var(--apple-blue)', 
                background: 'rgba(0, 122, 255, 0.04)',
                padding: '16px',
                borderRadius: '12px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <LayoutDashboard size={16} color="var(--apple-blue-text)" />
                    <span style={{ fontWeight: 600, color: 'var(--apple-blue-text)', fontSize: '14px' }}>
                      风格透视 (Sentence Inspector)
                    </span>
                  </div>
                  {selectedSentenceIndex !== null && (
                    <button 
                      onClick={() => setSelectedSentenceIndex(null)}
                      style={{ 
                        background: 'none', 
                        border: 'none', 
                        color: 'var(--text-tertiary)', 
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                    >
                      Clear
                    </button>
                  )}
                </div>

                {selectedSentenceIndex === null ? (
                  <p style={{ color: 'var(--text-tertiary)', fontSize: '13px', textAlign: 'center', padding: '10px 0' }}>
                    💡 点击左侧文档中的任意句子，在此透视模型深度 analysis 及风格修改建议。
                  </p>
                ) : (
                  <div>
                    {allDiagnostics[selectedSentenceIndex] ? (
                      <div>
                        <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.5', background: 'var(--card-inner-bg)', padding: '10px', borderRadius: '6px' }}>
                          "{allDiagnostics[selectedSentenceIndex].text}"
                        </p>
                        
                        <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                          <div className="metric-row" style={{ marginTop: 0 }}>
                            <span className="text-secondary font-mono">PPL (Perplexity)</span>
                            <span className="metric-value font-mono" style={{ 
                              color: allDiagnostics[selectedSentenceIndex].ppl && allDiagnostics[selectedSentenceIndex].ppl! < 15 ? 'var(--apple-red-text)' : allDiagnostics[selectedSentenceIndex].ppl && allDiagnostics[selectedSentenceIndex].ppl! < 25 ? 'var(--apple-orange-text)' : 'var(--text-secondary)',
                              fontWeight: 600
                            }}>
                              {allDiagnostics[selectedSentenceIndex].ppl !== null ? allDiagnostics[selectedSentenceIndex].ppl : 'N/A (API模式)'}
                            </span>
                          </div>
                          
                          <div className="metric-row">
                            <span className="text-secondary">Status</span>
                            <span style={{ 
                              color: allDiagnostics[selectedSentenceIndex].status === 'flagged' ? 'var(--apple-red-text)' : allDiagnostics[selectedSentenceIndex].status === 'early_exit' ? 'var(--apple-blue-text)' : 'var(--apple-green-text)',
                              fontWeight: 600
                            }}>
                              {allDiagnostics[selectedSentenceIndex].status === 'flagged' ? '风格警报 (Flagged)' : allDiagnostics[selectedSentenceIndex].status === 'early_exit' ? '早退通过 (Early Exit)' : '通过 (Passed)'}
                            </span>
                          </div>

                          {allDiagnostics[selectedSentenceIndex].metrics && (
                            <div style={{ marginTop: '8px', padding: '8px', background: 'var(--card-inner-bg)', borderRadius: '6px' }}>
                              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', fontSize: '11px', color: 'var(--text-secondary)' }}>
                                <div>名/动比率: <span style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.nv_ratio}</span></div>
                                <div>被动语态: <span style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.passive_count}</span></div>
                                <div>第二格长链: <span style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.genitive_chains_count}</span></div>
                                <div>套话匹配: <span style={{ color: 'var(--text-primary)' }}>{allDiagnostics[selectedSentenceIndex].metrics?.cliches_count}</span></div>
                              </div>
                            </div>
                          )}

                          {allDiagnostics[selectedSentenceIndex].think && (
                            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)' }}>
                              <details style={{ cursor: 'pointer' }}>
                                <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none' }}>
                                  ▶ View Model Reasoning (模型诊断原因)
                                </summary>
                                <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '8px', whiteSpace: 'pre-wrap', lineHeight: '1.4', fontFamily: 'var(--font-mono)' }}>
                                  {allDiagnostics[selectedSentenceIndex].think}
                                </p>
                              </details>
                            </div>
                          )}

                          {allDiagnostics[selectedSentenceIndex].explanation && (
                            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)' }}>
                              <p className="text-secondary" style={{ marginBottom: '4px' }}>Analysis</p>
                              <p style={{ color: allDiagnostics[selectedSentenceIndex].issue_type === 'json_parse_error' ? 'var(--apple-red-text)' : 'var(--apple-orange-text)' }}>
                                {allDiagnostics[selectedSentenceIndex].explanation}
                              </p>
                            </div>
                          )}

                          {allDiagnostics[selectedSentenceIndex].suggestion && allDiagnostics[selectedSentenceIndex].suggestion !== 'N/A' && allDiagnostics[selectedSentenceIndex].suggestion !== '-' && (
                            <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)' }}>
                              <p className="text-secondary" style={{ marginBottom: '4px' }}>Suggestion (修改建议)</p>
                              <p style={{ color: 'var(--apple-green-text)', fontWeight: 500 }}>{allDiagnostics[selectedSentenceIndex].suggestion}</p>
                            </div>
                          )}
                          {renderCitationAudit(allDiagnostics[selectedSentenceIndex])}
                        </div>
                      </div>
                    ) : (
                      <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', textAlign: 'center' }}>
                        Sentence clicked, waiting for diagnostic stream results...
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}

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
                      </div>
                      <div className="tabs-container">
                        <button 
                          className={`tab-btn ${activeTab === 'ai' ? 'active' : ''}`}
                          onClick={() => setActiveTab('ai')}
                        >
                          AI风险 ({aiCount})
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === 'flagged' ? 'active' : ''}`}
                          onClick={() => setActiveTab('flagged')}
                        >
                          风格警报 ({styleCount})
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === 'integrity' ? 'active' : ''}`}
                          onClick={() => setActiveTab('integrity')}
                        >
                          文献异常 ({integrityCount})
                        </button>
                      </div>
                    </div>
                  )}

                  {activeTab === 'all' && (
                    <>
                      {sortedDiagnostics.map((diag) => (
                        diag.status === 'flagged' ? (
                          <div 
                            key={diag.index}
                            className="glass-card slide-in" 
                            onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                            style={{ borderLeft: '4px solid var(--apple-red)' }}
                          >
                            {(() => {
                              const issueInfo = ISSUE_TITLE_MAP[diag.issue_type || ''] || { title: "学术风格警报 (Style Alert)", color: "var(--apple-orange-text)" };
                              return (
                                <div className="card-header" style={{ color: issueInfo.color, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                  <AlertCircle size={16} color={issueInfo.color} />
                                  <span style={{ fontWeight: 600 }}>{issueInfo.title}</span>
                                </div>
                              );
                            })()}
                            
                            <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.4' }}>
                              "{diag.text.substring(0, 80)}..."
                            </p>
                            
                            <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                              <div className="metric-row" style={{ marginTop: 0, display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span className="text-secondary font-mono">PPL (Perplexity)</span>
                                <span className="metric-value red font-mono" style={{ color: 'var(--apple-red-text)', fontWeight: 600 }}>{diag.ppl !== null ? diag.ppl : 'N/A'}</span>
                              </div>
                              <div className="metric-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span className="text-secondary">Issue</span>
                                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{diag.issue_type}</span>
                              </div>
                              
                              {diag.think && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                    <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none', fontSize: '11px' }}>
                                      ▶ View Model Reasoning
                                    </summary>
                                    <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '6px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                      {diag.think}
                                    </p>
                                  </details>
                                </div>
                              )}

                              {diag.explanation && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Analysis</p>
                                  <p style={{ color: diag.issue_type === 'json_parse_error' ? 'var(--apple-red-text)' : 'var(--apple-orange-text)', fontSize: '12px', lineHeight: '1.4' }}>{diag.explanation}</p>
                                </div>
                              )}
                              
                              {diag.suggestion && diag.suggestion !== 'N/A' && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Suggestion</p>
                                  <p style={{ color: 'var(--apple-green-text)', fontWeight: 500, fontSize: '12px' }}>{diag.suggestion}</p>
                                </div>
                              )}
                              {renderCitationAudit(diag)}
                            </div>
                          </div>
                        ) : (
                          <div 
                            key={diag.index}
                            className="glass-card slide-in passed-card" 
                            onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                            style={{ borderLeft: '4px solid var(--apple-green)' }}
                          >
                            <div className="card-header" style={{ color: 'var(--apple-green-text)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                              <div style={{ width: '16px', height: '16px', borderRadius: '50%', background: 'var(--apple-green)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '10px', fontWeight: 'bold' }}>✓</div>
                              <span style={{ fontWeight: 600 }}>无风险 (Passed / Clean Style)</span>
                            </div>
                            
                            <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.4' }}>
                              "{diag.text.substring(0, 80)}..."
                            </p>
                            
                            <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                              <div className="metric-row" style={{ marginTop: 0, display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span className="text-secondary font-mono">PPL (Perplexity)</span>
                                <span className="metric-value font-mono" style={{ color: 'var(--apple-green-text)', fontWeight: 600 }}>{diag.ppl !== null ? diag.ppl : 'N/A'}</span>
                              </div>
                              <div className="metric-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span className="text-secondary">Status</span>
                                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                                  {diag.status === 'early_exit' ? '安全通过 (Early Exit)' : '专家通过 (Passed)'}
                                </span>
                              </div>
                              
                              {diag.think && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                    <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none', fontSize: '11px' }}>
                                      ▶ View Model Reasoning
                                    </summary>
                                    <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '6px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                      {diag.think}
                                    </p>
                                  </details>
                                </div>
                              )}
                              {renderCitationAudit(diag)}
                            </div>
                          </div>
                        )
                      ))}
                      {integrityWarnings.length > 0 && renderIntegrityReport()}
                    </>
                  )}

                  {activeTab === 'passed' && (
                    <>
                      {sortedDiagnostics.filter(d => d.status !== 'flagged').map((diag) => (
                        <div 
                          key={diag.index}
                          className="glass-card slide-in passed-card" 
                          onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                          style={{ borderLeft: '4px solid var(--apple-green)' }}
                        >
                          <div className="card-header" style={{ color: 'var(--apple-green-text)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                            <div style={{ width: '16px', height: '16px', borderRadius: '50%', background: 'var(--apple-green)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: '10px', fontWeight: 'bold' }}>✓</div>
                            <span style={{ fontWeight: 600 }}>无风险 (Passed / Clean Style)</span>
                          </div>
                          
                          <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.4' }}>
                            "{diag.text.substring(0, 80)}..."
                          </p>
                          
                          <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                            <div className="metric-row" style={{ marginTop: 0, display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span className="text-secondary font-mono">PPL (Perplexity)</span>
                              <span className="metric-value font-mono" style={{ color: 'var(--apple-green-text)', fontWeight: 600 }}>{diag.ppl !== null ? diag.ppl : 'N/A'}</span>
                            </div>
                            <div className="metric-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span className="text-secondary">Status</span>
                              <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                                {diag.status === 'early_exit' ? '安全通过 (Early Exit)' : '专家通过 (Passed)'}
                              </span>
                            </div>
                            
                            {diag.think && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                  <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none', fontSize: '11px' }}>
                                    ▶ View Model Reasoning
                                  </summary>
                                  <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '6px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                    {diag.think}
                                  </p>
                                </details>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </>
                  )}

                  {activeTab === 'ai' && (
                    <>
                      {sortedDiagnostics.filter(d => d.status === 'flagged' && d.issue_type === 'ai_generated_suspicion').map((diag) => (
                        <div 
                          key={diag.index}
                          className="glass-card slide-in" 
                          onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                          style={{ borderLeft: '4px solid var(--apple-red)' }}
                        >
                          {(() => {
                            const issueInfo = ISSUE_TITLE_MAP[diag.issue_type || ''] || { title: "AI 生成特征预警", color: "var(--apple-red-text)" };
                            return (
                              <div className="card-header" style={{ color: issueInfo.color, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                <AlertCircle size={16} color={issueInfo.color} />
                                <span style={{ fontWeight: 600 }}>{issueInfo.title}</span>
                              </div>
                            );
                          })()}
                          
                          <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.4' }}>
                            "{diag.text.substring(0, 80)}..."
                          </p>
                          
                          <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                            <div className="metric-row" style={{ marginTop: 0, display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span className="text-secondary font-mono">PPL (Perplexity)</span>
                              <span className="metric-value red font-mono" style={{ color: 'var(--apple-red-text)', fontWeight: 600 }}>{diag.ppl !== null ? diag.ppl : 'N/A'}</span>
                            </div>
                            <div className="metric-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span className="text-secondary">Issue</span>
                              <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{diag.issue_type}</span>
                            </div>
                            
                            {diag.think && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                  <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none', fontSize: '11px' }}>
                                    ▶ View Model Reasoning
                                  </summary>
                                  <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '6px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                    {diag.think}
                                  </p>
                                </details>
                              </div>
                            )}

                            {diag.explanation && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Analysis</p>
                                <p style={{ color: 'var(--apple-red-text)', fontSize: '12px', lineHeight: '1.4' }}>{diag.explanation}</p>
                              </div>
                            )}
                            
                            {diag.suggestion && diag.suggestion !== 'N/A' && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Suggestion</p>
                                <p style={{ color: 'var(--apple-green-text)', fontWeight: 500, fontSize: '12px' }}>{diag.suggestion}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </>
                  )}

                  {activeTab === 'flagged' && (
                    <>
                      {sortedDiagnostics.filter(d => d.status === 'flagged' && d.issue_type !== 'ai_generated_suspicion' && d.issue_type !== 'citation_gap' && d.issue_type !== 'citation_contradiction').map((diag) => (
                        <div 
                          key={diag.index}
                          className="glass-card slide-in" 
                          onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                          style={{ borderLeft: '4px solid var(--apple-orange)' }}
                        >
                          {(() => {
                            const issueInfo = ISSUE_TITLE_MAP[diag.issue_type || ''] || { title: "学术风格警报 (Style Alert)", color: "var(--apple-orange-text)" };
                            return (
                              <div className="card-header" style={{ color: issueInfo.color, display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                                <AlertCircle size={16} color={issueInfo.color} />
                                <span style={{ fontWeight: 600 }}>{issueInfo.title}</span>
                              </div>
                            );
                          })()}
                          
                          <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.4' }}>
                            "{diag.text.substring(0, 80)}..."
                          </p>
                          
                          <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                            <div className="metric-row" style={{ marginTop: 0, display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span className="text-secondary font-mono">PPL (Perplexity)</span>
                              <span className="metric-value red font-mono" style={{ color: 'var(--apple-red-text)', fontWeight: 600 }}>{diag.ppl !== null ? diag.ppl : 'N/A'}</span>
                            </div>
                            <div className="metric-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span className="text-secondary">Issue</span>
                              <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{diag.issue_type}</span>
                            </div>
                            
                            {diag.think && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                  <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none', fontSize: '11px' }}>
                                    ▶ View Model Reasoning
                                  </summary>
                                  <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '6px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                    {diag.think}
                                  </p>
                                </details>
                              </div>
                            )}

                            {diag.explanation && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Analysis</p>
                                <p style={{ color: diag.issue_type === 'json_parse_error' ? 'var(--apple-red-text)' : 'var(--apple-orange-text)', fontSize: '12px', lineHeight: '1.4' }}>{diag.explanation}</p>
                              </div>
                            )}
                            
                            {diag.suggestion && diag.suggestion !== 'N/A' && (
                              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Suggestion</p>
                                <p style={{ color: 'var(--apple-green-text)', fontWeight: 500, fontSize: '12px' }}>{diag.suggestion}</p>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </>
                  )}

                  {activeTab === 'integrity' && (
                    <>
                      {sortedDiagnostics.filter(d => d.status === 'flagged' && (d.issue_type === 'citation_gap' || d.issue_type === 'citation_contradiction')).map((diag) => {
                        const isContradiction = diag.issue_type === 'citation_contradiction';
                        return (
                          <div 
                            key={diag.index}
                            className="glass-card slide-in" 
                            onClick={() => { scrollToSentence(diag.index); setSelectedSentenceIndex(diag.index); }}
                            style={{ borderLeft: isContradiction ? '4px solid var(--apple-red)' : '4px solid var(--apple-orange)' }}
                          >
                            <div className="card-header" style={{ color: isContradiction ? 'var(--apple-red-text)' : 'var(--apple-orange-text)', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                              <AlertCircle size={16} color={isContradiction ? 'var(--apple-red-text)' : 'var(--apple-orange-text)'} />
                              <span style={{ fontWeight: 600 }}>
                                {isContradiction ? '文献论点冲突 (Citation Contradiction)' : '引用支撑不足 (Citation Gap Alert)'}
                              </span>
                            </div>
                            
                            <p style={{ fontSize: '14px', color: 'var(--text-primary)', marginBottom: '12px', lineHeight: '1.4' }}>
                              "{diag.text.substring(0, 80)}..."
                            </p>
                            
                            <div style={{ background: 'var(--card-inner-bg)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                              <div className="metric-row" style={{ marginTop: 0, display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span className="text-secondary font-mono">PPL (Perplexity)</span>
                                <span className="metric-value red font-mono" style={{ color: 'var(--apple-red-text)', fontWeight: 600 }}>{diag.ppl !== null ? diag.ppl : 'N/A'}</span>
                              </div>
                              <div className="metric-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span className="text-secondary">Issue</span>
                                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{diag.issue_type}</span>
                              </div>
                              
                              {diag.think && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <details style={{ cursor: 'pointer' }} onClick={(e) => e.stopPropagation()}>
                                    <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none', fontSize: '11px' }}>
                                      ▶ View Model Reasoning
                                    </summary>
                                    <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '6px', whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', lineHeight: '1.4' }}>
                                      {diag.think}
                                    </p>
                                  </details>
                                </div>
                              )}

                              {diag.explanation && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Analysis</p>
                                  <p style={{ color: 'var(--apple-red-text)', fontSize: '12px', lineHeight: '1.4' }}>{diag.explanation}</p>
                                </div>
                              )}
                              
                              {diag.suggestion && diag.suggestion !== 'N/A' && (
                                <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--glass-border)' }}>
                                  <p className="text-secondary" style={{ marginBottom: '2px', fontSize: '11px' }}>Suggestion</p>
                                  <p style={{ color: 'var(--apple-green-text)', fontWeight: 500, fontSize: '12px' }}>{diag.suggestion}</p>
                                </div>
                              )}
                              
                              {renderCitationAudit(diag)}
                            </div>
                          </div>
                        );
                      })}
                      {integrityWarnings.length > 0 && renderIntegrityReport()}
                    </>
                  )}
                </>
              );
            })()}
            
            {isAnalyzing && (
              <div className="glass-card" style={{ opacity: 0.5, display: 'flex', justifyContent: 'center', padding: '24px' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', border: '2px solid var(--glass-border)', borderTopColor: 'var(--text-primary)', animation: 'spin 1s linear infinite' }} />
                <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
              </div>
            )}
            
            {/* Future Extension UI (Placed after AI Queries) */}
            {progress.total > 0 && progress.current === progress.total && !isAnalyzing && (
              <div className="glass-card" style={{ marginTop: '24px', opacity: 0.8 }}>
                <h3 style={{ fontSize: '14px', marginBottom: '12px', color: 'var(--text-secondary)' }}>Extension Capabilities</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <button className="btn-secondary" style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: '13px', background: 'var(--card-inner-bg)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', borderRadius: '6px', cursor: 'pointer' }}>✨ 润色 (Polishing)</button>
                  <button className="btn-secondary" style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: '13px', background: 'var(--card-inner-bg)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', borderRadius: '6px', cursor: 'pointer' }}>📚 参考文献修正 (Citations)</button>
                  <button className="btn-secondary" style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: '13px', background: 'var(--card-inner-bg)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', borderRadius: '6px', cursor: 'pointer' }}>📏 格式检查 (Formatting)</button>
                  <button className="btn-secondary" style={{ width: '100%', textAlign: 'left', padding: '8px 12px', fontSize: '13px', background: 'var(--card-inner-bg)', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', borderRadius: '6px', cursor: 'pointer' }}>🏗️ 结构分析 (Structure)</button>
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
