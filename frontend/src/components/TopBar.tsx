import { Moon, Square, Sun } from 'lucide-react';
import { ENGINE_OPTIONS, usesLocalModel } from '../lib/labels';
import type { EngineType, ModelStatus } from '../types';
import type { Theme } from '../hooks/useTheme';

interface Props {
  engineType: EngineType;
  modelStatus: ModelStatus;
  theme: Theme;
  onToggleTheme: () => void;
  onOpenSettings: (trigger: HTMLElement) => void;
  canStart: boolean;
  running: boolean;
  progressLabel: string;
  onStart: () => void;
  onStop: () => void;
}

export function TopBar(p: Props) {
  const engine = ENGINE_OPTIONS.find(o => o.value === p.engineType);
  const needsModel = usesLocalModel(p.engineType);
  const dotClass = !needsModel ? 'ok' : p.modelStatus === 'exists' ? 'ok' : p.modelStatus === 'checking' ? '' : 'warn';
  const engineStatus = !needsModel
    ? '云端'
    : p.modelStatus === 'exists' ? '本地模型就绪'
    : p.modelStatus === 'downloading' ? '模型下载中'
    : p.modelStatus === 'checking' ? '检查中' : '未安装本地模型';

  return (
    <header className="topbar">
      <div className="wordmark">
        <span className="wordmark-name">RuScholar Studio</span>
        <span className="meta wordmark-sub">俄语学位论文质检工作台 · ВАК / ГОСТ</span>
      </div>
      <div className="topbar-spacer" />
      <div className="topbar-actions">
        <button
          type="button"
          className="engine-chip"
          onClick={e => p.onOpenSettings(e.currentTarget)}
          aria-label={`推理引擎：${engine?.label}，${engineStatus}。打开引擎设置`}
          title="引擎设置"
        >
          <span className={`dot ${dotClass}`} aria-hidden />
          <span>{engine?.label}</span>
          <span className="engine-chip-label meta">· {engineStatus}</span>
        </button>
        <button
          type="button"
          className="icon-btn"
          onClick={p.onToggleTheme}
          aria-label={p.theme === 'dark' ? '切换到浅色' : '切换到深色'}
          title={p.theme === 'dark' ? '切换到浅色' : '切换到深色'}
        >
          {p.theme === 'dark' ? <Sun size={18} strokeWidth={1.75} /> : <Moon size={18} strokeWidth={1.75} />}
        </button>
        {p.running ? (
          <button type="button" className="btn btn-secondary" onClick={p.onStop}>
            <Square size={12} strokeWidth={2} aria-hidden />
            停止质检 <span className="meta num">{p.progressLabel}</span>
          </button>
        ) : (
          <button type="button" className="btn btn-primary" onClick={p.onStart} disabled={!p.canStart}
            title={p.canStart ? undefined : '请先导入手稿'}>
            开始质检
          </button>
        )}
      </div>
    </header>
  );
}
