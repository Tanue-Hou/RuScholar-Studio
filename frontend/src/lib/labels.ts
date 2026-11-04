import type { AuditStatus, DiagnosticResult, EngineType } from '../types';

export const ENGINE_OPTIONS: { value: EngineType; label: string; hint: string }[] = [
  { value: 'local', label: '本地', hint: 'Qwen3 GGUF，完全离线' },
  { value: 'hybrid-pro', label: '混合 · Pro', hint: '本地困惑度 + DeepSeek Pro 判定' },
  { value: 'hybrid-flash', label: '混合 · Flash', hint: '本地困惑度 + DeepSeek Flash 判定' },
  { value: 'cloud-pro', label: '云端 · Pro', hint: '纯 DeepSeek Pro' },
  { value: 'cloud-flash', label: '云端 · Flash', hint: '纯 DeepSeek Flash，最快' },
];

export const usesLocalModel = (e: EngineType) => e === 'local' || e.startsWith('hybrid');

export const DISCIPLINES: Record<string, { zh: string; ru: string }> = {
  SCI_TECH: { zh: '理工科', ru: 'Естественные и технические науки' },
  AUTOMATION_CONTROL: { zh: '自动化与控制', ru: 'Автоматизация и управление' },
  AGRI_MED: { zh: '农学与医学', ru: 'Сельскохозяйственные и медицинские науки' },
  HUM_POL_ECON: { zh: '人文社科', ru: 'Гуманитарные и социальные науки' },
  ARTS_SPORTS: { zh: '艺术、体育与文化', ru: 'Искусство, спорт и культура' },
  UNIVERSAL: { zh: '通用学术', ru: 'Междисциплинарная область' },
};

export const ISSUE_TITLES: Record<string, string> = {
  ai_generated_suspicion: 'AI 生成特征',
  machine_translation_cliche: '翻译腔与学术套话',
  style_heavy: '句式臃肿',
  semantic_plagiarism_risk: '与文献表述高度重合',
  citation_gap: '引用支撑不足',
  citation_contradiction: '与所引文献矛盾',
  json_parse_error: '模型输出无法解析',
  api_request_error: '云端服务未响应',
};

export const issueTitle = (type: string | null) => ISSUE_TITLES[type ?? ''] ?? '文风提示';

export type NoteFilter = 'all' | 'ai' | 'style' | 'citation' | 'passed';

const CITATION_ISSUES = new Set(['citation_gap', 'citation_contradiction']);

export function categoryOf(d: DiagnosticResult): Exclude<NoteFilter, 'all'> {
  if (d.status !== 'flagged') return 'passed';
  if (d.issue_type === 'ai_generated_suspicion') return 'ai';
  if (CITATION_ISSUES.has(d.issue_type ?? '')) return 'citation';
  return 'style';
}

export const FILTERS: { value: NoteFilter; label: string }[] = [
  { value: 'all', label: '全部批注' },
  { value: 'ai', label: 'AI 特征' },
  { value: 'style', label: '文风' },
  { value: 'citation', label: '引文' },
  { value: 'passed', label: '已通过' },
];

export const AUDIT_LABELS: Record<AuditStatus, string> = {
  SUPPORTED: '文献支持该论点',
  CONTRADICTED: '与文献矛盾',
  NOT_ENOUGH_INFO: '证据不足',
  AUDIT_FAILED: '未能核验',
};

export const RISKS: { key: 'predictability' | 'uniformity' | 'translationese' | 'redundancy'; label: string; hint: string }[] = [
  { key: 'predictability', label: '可预测性', hint: '词汇分布是否过于平滑（困惑度偏低）' },
  { key: 'uniformity', label: '句式均匀度', hint: '句长与结构是否过于整齐划一' },
  { key: 'translationese', label: '翻译腔', hint: '名词化、被动语态与第二格链' },
  { key: 'redundancy', label: '语义冗余', hint: '套话、连接词与冗长修饰' },
];

export const STATUS_LABELS: Record<string, string> = {
  flagged: '需修改',
  passed: '通过',
  early_exit: '通过（快速判定）',
  ok: '通过',
};
