import type { DiagnosticResult, EngineSettings, InitEvent, RiskScores } from '../types';

async function expectJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = String(body.detail);
    } catch {
      // keep the status text
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export async function checkModel(): Promise<boolean> {
  const data = await expectJson<{ exists: boolean }>(await fetch('/api/check_model'));
  return data.exists;
}

export async function uploadDocument(file: File): Promise<string> {
  const form = new FormData();
  form.append('file', file);
  const data = await expectJson<{ text: string }>(await fetch('/api/upload', { method: 'POST', body: form }));
  return data.text;
}

export async function detectDiscipline(text: string, engine: EngineSettings): Promise<string> {
  const res = await fetch('/api/detect_discipline', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: text.substring(0, 1000),
      engine_type: engine.engineType,
      api_key: engine.apiKey,
      base_url: engine.baseUrl,
    }),
  });
  const data = await expectJson<{ discipline?: string }>(res);
  return data.discipline || 'UNIVERSAL';
}

export async function createSession(text: string, discipline: string, engine: EngineSettings): Promise<string> {
  const res = await fetch('/api/session', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      engine_type: engine.engineType,
      api_key: engine.apiKey,
      base_url: engine.baseUrl,
      discipline,
    }),
  });
  const data = await expectJson<{ session_id: string }>(res);
  return data.session_id;
}

export async function uploadReferences(sessionId: string, bibtex: File | null, documents: File[]): Promise<void> {
  const form = new FormData();
  form.append('session_id', sessionId);
  if (bibtex) form.append('bibtex', await bibtex.text());
  documents.forEach(f => form.append('files', f));
  await expectJson(await fetch('/api/upload_references', { method: 'POST', body: form }));
}

export interface DiagnosisHandlers {
  onInit: (data: InitEvent) => void;
  onResult: (data: DiagnosticResult) => void;
  onDone: (data: Partial<RiskScores>) => void;
  onError: (message: string | null) => void;
}

/** Subscribe to the SSE diagnosis stream. Returns a function that closes it. */
export function openDiagnosisStream(sessionId: string, h: DiagnosisHandlers): () => void {
  const source = new EventSource(`/api/diagnose?session_id=${encodeURIComponent(sessionId)}`);
  const close = () => source.close();

  source.addEventListener('init', e => h.onInit(JSON.parse((e as MessageEvent).data)));
  source.addEventListener('result', e => h.onResult(JSON.parse((e as MessageEvent).data)));
  source.addEventListener('done', e => {
    close();
    let data: Partial<RiskScores> = {};
    try {
      data = JSON.parse((e as MessageEvent).data);
    } catch {
      // risks stay at their last running values
    }
    h.onDone(data);
  });
  // Server-sent "error" events carry JSON; transport errors do not.
  source.addEventListener('error', e => {
    close();
    let message: string | null = null;
    try {
      const data = JSON.parse((e as MessageEvent).data);
      message = data.error || data.message || null;
    } catch {
      // connection dropped
    }
    h.onError(message);
  });
  return close;
}

/** POST /api/download_model and report progress (0–100) from its SSE body. */
export async function downloadModel(onProgress: (percent: number) => void): Promise<void> {
  const res = await fetch('/api/download_model', { method: 'POST' });
  if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() ?? '';
    for (const frame of frames) {
      const dataLine = frame.split(/\r?\n/).find(l => l.startsWith('data:'));
      if (!dataLine) continue;
      const data = JSON.parse(dataLine.slice(5).trim());
      if (data.status === 'downloading') onProgress(data.progress);
      else if (data.status === 'complete') return;
      else if (data.status === 'error') throw new Error(data.message || 'Download failed');
    }
  }
  throw new Error('Download stream ended unexpectedly.');
}
