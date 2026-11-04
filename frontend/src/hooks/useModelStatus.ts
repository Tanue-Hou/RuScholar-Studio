import { useCallback, useEffect, useState } from 'react';
import { checkModel, downloadModel } from '../api/client';
import type { ModelStatus } from '../types';

export function useModelStatus() {
  const [status, setStatus] = useState<ModelStatus>('checking');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkModel()
      .then(exists => setStatus(exists ? 'exists' : 'missing'))
      .catch(() => setStatus('missing'));
  }, []);

  const download = useCallback(async () => {
    setStatus('downloading');
    setProgress(0);
    setError(null);
    try {
      await downloadModel(setProgress);
      setStatus('exists');
    } catch (err) {
      setStatus('missing');
      setError(err instanceof Error ? err.message : String(err));
    }
  }, []);

  return { status, progress, error, download };
}
