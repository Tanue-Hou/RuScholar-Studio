import React, { useState, useRef } from 'react';
import { Upload, FileText, AlertCircle, LayoutDashboard } from 'lucide-react';
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
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [documentText, setDocumentText] = useState<string>('');
  const [sentences, setSentences] = useState<{ text: string, status: string }[]>([]);
  const [diagnostics, setDiagnostics] = useState<DiagnosticResult[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  
  const sentenceRefs = useRef<(HTMLSpanElement | null)[]>([]);

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

  const startAnalysis = () => {
    if (!documentText) return;
    
    setIsAnalyzing(true);
    setDiagnostics([]);
    setSentences([]);
    
    // Connect to SSE
    const encodedText = encodeURIComponent(documentText);
    const eventSource = new EventSource(`/api/diagnose?text=${encodedText}`);
    
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
        next[data.index] = { text: data.text, status: data.status };
        return next;
      });
      
      if (data.status === 'flagged') {
        setDiagnostics(prev => [...prev, data]);
      }
      
      setProgress(prev => ({ ...prev, current: prev.current + 1 }));
    });
    
    eventSource.addEventListener("done", () => {
      setIsAnalyzing(false);
      eventSource.close();
    });
    
    eventSource.onerror = () => {
      console.error("SSE Error");
      setIsAnalyzing(false);
      eventSource.close();
    };
  };

  const scrollToSentence = (index: number) => {
    if (sentenceRefs.current[index]) {
      sentenceRefs.current[index]?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Temporary highlight effect could be added here
    }
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
            color: 'var(--apple-red)', 
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
            <button className="btn-primary" onClick={startAnalysis} disabled={isAnalyzing}>
              {isAnalyzing ? `Analyzing... ${progress.current}/${progress.total}` : 'Run Analysis'}
            </button>
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
              <p className="text-secondary" style={{ marginTop: '8px' }}>Drag & drop your .docx or .txt file here</p>
              <input 
                id="file-upload" 
                type="file" 
                accept=".docx,.txt" 
                style={{ display: 'none' }} 
                onChange={handleFileUpload}
              />
            </div>
          ) : (
            <div className="document-viewer">
              {sentences.length === 0 ? (
                <div style={{ whiteSpace: 'pre-wrap' }}>{documentText}</div>
              ) : (
                sentences.map((s, idx) => (
                  <span 
                    key={idx} 
                    ref={el => { sentenceRefs.current[idx] = el; }}
                    className={`sentence ${s.status}`}
                    title={s.status}
                  >
                    {s.text}{' '}
                  </span>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right Column: Diagnostics Stream */}
        <div className="column-right">
          <div className="stream-container">
            {!file && (
              <div style={{ textAlign: 'center', color: 'var(--text-tertiary)', marginTop: '40px' }}>
                <FileText size={48} style={{ opacity: 0.2, margin: '0 auto 16px auto' }} />
                <p>Upload a document to begin the<br/>AI diagnostics stream.</p>
              </div>
            )}
            
            {diagnostics.map((diag, i) => (
              <div 
                key={i} 
                className="glass-card slide-in" 
                onClick={() => scrollToSentence(diag.index)}
              >
                <div className="card-header">
                  <AlertCircle size={16} color="var(--apple-red)" />
                  <span style={{ color: 'var(--apple-red)' }}>AI Trigger Detected</span>
                </div>
                
                <p style={{ fontSize: '15px', color: 'var(--text-primary)', marginBottom: '12px' }}>
                  "{diag.text.substring(0, 80)}..."
                </p>
                
                <div style={{ background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '12px', fontSize: '13px' }}>
                  <div className="metric-row" style={{ marginTop: 0 }}>
                    <span className="text-secondary font-mono">PPL (Perplexity)</span>
                    <span className="metric-value red font-mono">{diag.ppl}</span>
                  </div>
                  <div className="metric-row">
                    <span className="text-secondary">Issue</span>
                    <span>{diag.issue_type}</span>
                  </div>
                  
                  {diag.think && (
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)' }}>
                      <details style={{ cursor: 'pointer' }}>
                        <summary className="text-secondary" style={{ marginBottom: '4px', outline: 'none', userSelect: 'none' }}>
                          ▶ View Model Reasoning
                        </summary>
                        <p style={{ color: 'var(--text-tertiary)', fontSize: '12px', marginTop: '8px', whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                          {diag.think}
                        </p>
                      </details>
                    </div>
                  )}
                  
                  {diag.explanation && (
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)' }}>
                      <p className="text-secondary" style={{ marginBottom: '4px' }}>Analysis</p>
                      <p style={{ color: diag.issue_type === 'json_parse_error' ? 'var(--apple-red)' : 'var(--apple-orange)' }}>{diag.explanation}</p>
                    </div>
                  )}
                  
                  {diag.suggestion && diag.suggestion !== 'N/A' && (
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--glass-border)' }}>
                      <p className="text-secondary" style={{ marginBottom: '4px' }}>Suggestion</p>
                      <p style={{ color: 'var(--apple-green)' }}>{diag.suggestion}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isAnalyzing && (
              <div className="glass-card" style={{ opacity: 0.5, display: 'flex', justifyContent: 'center', padding: '24px' }}>
                <div style={{ width: '20px', height: '20px', borderRadius: '50%', border: '2px solid var(--glass-border)', borderTopColor: 'var(--text-primary)', animation: 'spin 1s linear infinite' }} />
                <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
