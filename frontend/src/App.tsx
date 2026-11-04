import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { uploadDocument } from './api/client';
import { ImportView } from './components/ImportView';
import { Inspector } from './components/Inspector';
import { ManuscriptPage } from './components/ManuscriptPage';
import { NoteList } from './components/NoteList';
import { SettingsSheet } from './components/SettingsSheet';
import { Summary } from './components/Summary';
import { TopBar } from './components/TopBar';
import { useDiagnosis } from './hooks/useDiagnosis';
import { useModelStatus } from './hooks/useModelStatus';
import { useTheme } from './hooks/useTheme';
import { usesLocalModel, type NoteFilter } from './lib/labels';
import type { DiagnosticResult, EngineSettings } from './types';

export default function App() {
  const { theme, toggle: toggleTheme } = useTheme();
  const model = useModelStatus();
  const diagnosis = useDiagnosis();

  const [engine, setEngine] = useState<EngineSettings>({
    engineType: 'local',
    apiKey: '',
    baseUrl: 'https://api.deepseek.com/v1',
  });
  const [settingsOpen, setSettingsOpen] = useState(false);
  const settingsTrigger = useRef<HTMLElement | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [documentText, setDocumentText] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [bibtex, setBibtex] = useState<File | null>(null);
  const [referenceDocs, setReferenceDocs] = useState<File[]>([]);

  const [selected, setSelected] = useState<number | null>(null);
  const [filter, setFilter] = useState<NoteFilter>('all');
  const [showPpl, setShowPpl] = useState(false);

  // Opening or closing a note swaps the panel content: start it at the top.
  const asideRef = useRef<HTMLElement>(null);
  useEffect(() => {
    asideRef.current?.scrollTo({ top: 0 });
  }, [selected]);

  const openSettings = useCallback((trigger?: HTMLElement) => {
    settingsTrigger.current = trigger ?? (document.activeElement as HTMLElement | null);
    setSettingsOpen(true);
  }, []);
  const closeSettings = useCallback(() => {
    setSettingsOpen(false);
    settingsTrigger.current?.focus();
  }, []);

  const loadFile = async (f: File) => {
    setUploading(true);
    setUploadError(null);
    try {
      const text = await uploadDocument(f);
      if (!text.trim()) throw new Error('文件中没有可读取的文字（扫描版 PDF 需要先做文字识别）');
      setFile(f);
      setDocumentText(text);
      diagnosis.reset();
      setSelected(null);
    } catch (err) {
      setUploadError(`无法读取「${f.name}」：${err instanceof Error ? err.message : err}`);
    } finally {
      setUploading(false);
    }
  };

  const replaceManuscript = () => {
    diagnosis.reset();
    setFile(null);
    setDocumentText('');
    setSelected(null);
    setFilter('all');
  };

  const start = () => {
    if (!documentText) return;
    if (usesLocalModel(engine.engineType) && model.status !== 'exists') {
      openSettings();
      return;
    }
    setSelected(null);
    setFilter('all');
    diagnosis.start({ text: documentText, engine, bibtex, referenceDocs });
  };

  const items = useMemo(
    () => diagnosis.results.filter((r): r is DiagnosticResult => r !== null),
    [diagnosis.results],
  );
  // Footnote-style numbering of flagged sentences in reading order.
  const noteNumbers = useMemo(() => {
    const m = new Map<number, number>();
    let n = 0;
    for (const r of items) if (r.status === 'flagged') m.set(r.index, ++n);
    return m;
  }, [items]);

  const running = diagnosis.phase === 'running' || diagnosis.phase === 'preparing';
  const { summary } = diagnosis;

  return (
    <div className="app">
      <TopBar
        engineType={engine.engineType}
        modelStatus={model.status}
        theme={theme}
        onToggleTheme={toggleTheme}
        onOpenSettings={openSettings}
        canStart={!!file && !uploading}
        running={running}
        progressLabel={summary.total ? `${summary.completed}/${summary.total}` : ''}
        onStart={start}
        onStop={diagnosis.stop}
      />

      <div className="workspace">
        <main className="desk">
          {!file ? (
            <ImportView
              onFile={loadFile}
              uploading={uploading}
              uploadError={uploadError}
              bibtex={bibtex}
              onBibtex={setBibtex}
              referenceDocs={referenceDocs}
              onReferenceDocs={setReferenceDocs}
            />
          ) : (
            <ManuscriptPage
              fileName={file.name}
              documentText={documentText}
              phase={diagnosis.phase}
              results={diagnosis.results}
              completed={summary.completed}
              noteNumbers={noteNumbers}
              selected={selected}
              onSelect={setSelected}
              showPpl={showPpl}
              onTogglePpl={() => setShowPpl(v => !v)}
              references={diagnosis.references}
              hasReferenceFiles={!!bibtex || referenceDocs.length > 0}
              onReplace={replaceManuscript}
            />
          )}
        </main>

        <aside className="aside" aria-label="质检结果" ref={asideRef}>
          {diagnosis.phase === 'idle' ? (
            <section className="aside-section">
              <h2 className="eyebrow">如何使用</h2>
              <ol className="secondary" style={{ marginTop: 'var(--s3)', paddingLeft: '1.2em', display: 'grid', gap: 'var(--s2)' }}>
                <li>导入手稿，可选附上参考文献。</li>
                <li>在右上角确认推理引擎：本地完全离线，云端更快。</li>
                <li>点击「开始质检」。需要修改的句子会带上编号批注，点开即可看到原因与改写建议。</li>
              </ol>
            </section>
          ) : (
            <>
              <Summary
                phase={diagnosis.phase}
                discipline={diagnosis.discipline}
                total={summary.total}
                completed={summary.completed}
                flagged={summary.flagged}
                styleRisk={summary.styleRisk}
                avgPpl={summary.avgPpl}
                risks={diagnosis.risks}
              />

              {(diagnosis.error || diagnosis.nlpBackend === 'fallback' || diagnosis.phase === 'stopped') && (
                <section className="aside-section" style={{ display: 'grid', gap: 'var(--s3)' }}>
                  {diagnosis.error && <p className="notice" role="alert">{diagnosis.error}</p>}
                  {diagnosis.phase === 'stopped' && <p className="notice" role="status">质检已停止，已完成的批注仍然有效。可以重新开始完整质检。</p>}
                  {diagnosis.nlpBackend === 'fallback' && (
                    <p className="notice" role="status">
                      后端缺少 spaCy 俄语模型，名词/动词比、被动语态、第二格链等指标只是粗略估计。
                      安装后重新质检：<code>python -m spacy download ru_core_news_sm</code>
                    </p>
                  )}
                </section>
              )}

              {selected !== null ? (
                <Inspector
                  result={diagnosis.results[selected] ?? null}
                  noteNumber={noteNumbers.get(selected)}
                  onBack={() => setSelected(null)}
                />
              ) : (
                <NoteList
                  items={items}
                  warnings={diagnosis.warnings}
                  noteNumbers={noteNumbers}
                  filter={filter}
                  onFilter={setFilter}
                  onSelect={setSelected}
                  running={running}
                />
              )}
            </>
          )}
        </aside>
      </div>

      <SettingsSheet
        open={settingsOpen}
        onClose={closeSettings}
        engine={engine}
        onChange={setEngine}
        modelStatus={model.status}
        downloadProgress={model.progress}
        downloadError={model.error}
        onDownload={model.download}
      />
    </div>
  );
}
