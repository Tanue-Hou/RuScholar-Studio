import { useRef, useState } from 'react';
import { FileUp } from 'lucide-react';

interface Props {
  onFile: (file: File) => void;
  uploading: boolean;
  uploadError: string | null;
  bibtex: File | null;
  onBibtex: (file: File | null) => void;
  referenceDocs: File[];
  onReferenceDocs: (files: File[]) => void;
}

const MANUSCRIPT_TYPES = '.docx,.pdf,.txt';

export function ImportView(p: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const bibRef = useRef<HTMLInputElement>(null);
  const docsRef = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const pick = (files: FileList | null) => {
    if (files && files.length > 0) p.onFile(files[0]);
  };

  return (
    <div className="import">
      <h1 className="import-title">导入一份俄语学术手稿</h1>
      <p className="import-lede">
        逐句检查文风、翻译腔与 AI 生成特征，并核对每一处引用是否真有文献支撑。所有问题以页边批注的形式给出，结论可追溯，不给出单一的「AI 率」。
      </p>

      <button
        type="button"
        className={`dropzone ${drag ? 'drag' : ''}`}
        onClick={() => inputRef.current?.click()}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); pick(e.dataTransfer.files); }}
        disabled={p.uploading}
        aria-describedby="dropzone-hint"
      >
        <FileUp className="dropzone-icon" size={28} strokeWidth={1.5} aria-hidden />
        <span style={{ fontWeight: 500 }}>{p.uploading ? '正在读取手稿…' : '选择或拖入手稿文件'}</span>
        <span className="meta" id="dropzone-hint">支持 .docx、.pdf、.txt，单个文件不超过 50 MB</span>
      </button>
      <input ref={inputRef} type="file" accept={MANUSCRIPT_TYPES} hidden onChange={e => pick(e.target.files)} />
      {p.uploadError && <p className="notice" role="alert" style={{ marginTop: 'var(--s3)' }}>{p.uploadError}</p>}

      <section className="section" aria-labelledby="refs-title">
        <h2 className="section-title" id="refs-title">参考文献（可选）</h2>
        <p className="secondary" style={{ marginTop: 'var(--s2)' }}>
          提供文献全文后，引用核验将基于原文段落；未提供时，系统会按书目信息检索 OpenAlex 摘要进行核验。
        </p>
        <div className="ref-grid">
          <div className="ref-card">
            <div>
              <div className="ref-card-name">BibTeX 书目</div>
              <div className="meta ref-card-file">{p.bibtex ? p.bibtex.name : '未选择 .bib 文件'}</div>
            </div>
            <div className="ref-card-actions">
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => bibRef.current?.click()}>
                {p.bibtex ? '更换 .bib' : '选择 .bib'}
              </button>
              {p.bibtex && <button type="button" className="btn btn-quiet btn-sm" onClick={() => p.onBibtex(null)}>移除</button>}
            </div>
            <input ref={bibRef} type="file" accept=".bib" hidden
              onChange={e => { if (e.target.files?.[0]) p.onBibtex(e.target.files[0]); e.target.value = ''; }} />
          </div>
          <div className="ref-card">
            <div>
              <div className="ref-card-name">文献全文</div>
              <div className="meta ref-card-file">
                {p.referenceDocs.length ? `已选 ${p.referenceDocs.length} 篇` : '未选择（PDF / DOCX / TXT）'}
              </div>
              <div className="meta">文件名即引用键，例如 [Smith2020].pdf</div>
            </div>
            <div className="ref-card-actions">
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => docsRef.current?.click()}>
                {p.referenceDocs.length ? '重新选择' : '选择文件'}
              </button>
              {p.referenceDocs.length > 0 && <button type="button" className="btn btn-quiet btn-sm" onClick={() => p.onReferenceDocs([])}>清空</button>}
            </div>
            <input ref={docsRef} type="file" accept=".pdf,.docx,.txt" multiple hidden
              onChange={e => { if (e.target.files?.length) p.onReferenceDocs(Array.from(e.target.files)); e.target.value = ''; }} />
          </div>
        </div>
      </section>
    </div>
  );
}
