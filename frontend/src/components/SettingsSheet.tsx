import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { ENGINE_OPTIONS, usesLocalModel } from '../lib/labels';
import type { EngineSettings, ModelStatus } from '../types';

interface Props {
  open: boolean;
  onClose: () => void;
  engine: EngineSettings;
  onChange: (next: EngineSettings) => void;
  modelStatus: ModelStatus;
  downloadProgress: number;
  downloadError: string | null;
  onDownload: () => void;
}

const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function SettingsSheet(p: Props) {
  const sheetRef = useRef<HTMLDivElement>(null);
  const { onClose, open } = p;

  // Focus first control on open; trap Tab inside; Escape closes.
  useEffect(() => {
    if (!open) return;
    const sheet = sheetRef.current;
    sheet?.querySelector<HTMLElement>('input:checked, ' + FOCUSABLE)?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { e.preventDefault(); onClose(); return; }
      if (e.key !== 'Tab' || !sheet) return;
      const items = Array.from(sheet.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(el => !el.hasAttribute('disabled'));
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  const { engine } = p;
  const cloud = engine.engineType !== 'local';
  const local = usesLocalModel(engine.engineType);

  return (
    <>
      <div className="scrim" onClick={onClose} aria-hidden />
      <div className="sheet" role="dialog" aria-modal="true" aria-labelledby="settings-title" ref={sheetRef}>
        <div className="sheet-head">
          <h2 className="sheet-title" id="settings-title">推理引擎</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="关闭引擎设置" title="关闭 (Esc)">
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>
        <div className="sheet-body">
          <fieldset className="field" style={{ border: 'none' }}>
            <legend className="field-label" style={{ marginBottom: 'var(--s2)' }}>运行方式</legend>
            <div className="engine-options">
              {ENGINE_OPTIONS.map(o => (
                <label key={o.value} className="engine-option">
                  <input
                    type="radio"
                    name="engine"
                    value={o.value}
                    checked={engine.engineType === o.value}
                    onChange={() => p.onChange({ ...engine, engineType: o.value })}
                  />
                  <span>
                    <span className="engine-option-label">{o.label}</span>
                    <span className="meta" style={{ display: 'block' }}>{o.hint}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          {local && (
            <div className="field">
              <span className="field-label">本地模型</span>
              {p.modelStatus === 'exists' && <p className="secondary"><span className="dot ok" style={{ display: 'inline-block', marginRight: 8 }} />{engine.engineType === 'local' ? 'Qwen3 GGUF 已就绪，正文在本机推理。' : 'Qwen3 GGUF 已就绪，本地计算困惑度，句子发送到所选云端接口判定。'}</p>}
              {p.modelStatus === 'checking' && <p className="secondary">正在检查…</p>}
              {p.modelStatus === 'downloading' && (
                <div>
                  <p className="secondary">正在下载模型 <span className="num">{Math.round(p.downloadProgress)}%</span></p>
                  <div className="progress" role="progressbar" aria-valuenow={Math.round(p.downloadProgress)} aria-valuemin={0} aria-valuemax={100} aria-label="模型下载进度">
                    <div className="progress-fill" style={{ transform: `scaleX(${p.downloadProgress / 100})` }} />
                  </div>
                </div>
              )}
              {p.modelStatus === 'missing' && (
                <>
                  <p className="secondary">尚未安装本地模型（约 5.9 GB）。下载后可使用本地推理；也可以选择纯云端方式。</p>
                  <div><button type="button" className="btn btn-secondary" onClick={p.onDownload}>下载本地模型</button></div>
                </>
              )}
              {p.downloadError && <p className="notice" role="alert">下载没有完成：{p.downloadError}。请检查网络后重试。</p>}
            </div>
          )}

          {cloud && (
            <>
              <label className="field">
                <span className="field-label">API Key</span>
                <input
                  className="input mono"
                  type="password"
                  autoComplete="off"
                  value={engine.apiKey}
                  onChange={e => p.onChange({ ...engine, apiKey: e.target.value })}
                />
                <span className="meta">留空时使用后端 .env 中的 DEEPSEEK_API_KEY。仅保存在本页内存中。</span>
              </label>
              <label className="field">
                <span className="field-label">接口地址</span>
                <input
                  className="input mono"
                  type="url"
                  value={engine.baseUrl}
                  onChange={e => p.onChange({ ...engine, baseUrl: e.target.value })}
                />
                <span className="meta">兼容 OpenAI 格式的地址，例如 https://api.deepseek.com/v1</span>
              </label>
            </>
          )}
        </div>
      </div>
    </>
  );
}
