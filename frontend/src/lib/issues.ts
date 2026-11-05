// One source of truth for issue types: label, colour slot and underline style.
//
// Colours come from the validated categorical palette (dataviz reference),
// assigned in fixed order: blue, orange, aqua, yellow, magenta, then violet.
// Green (slot 6) is skipped on purpose because it would read as "passed".
// Six hues cannot all be told apart pairwise (the palette guarantees only 3),
// so every colour is paired with a text label and, in the manuscript, a
// distinct underline style. Colour is never the only cue.

export type IssueKey = 'trans' | 'ai' | 'gap' | 'style' | 'plag' | 'contra' | 'other';
export type LineStyle = 'solid' | 'bold' | 'dotted' | 'double' | 'dashed';

export interface IssueMeta {
  key: IssueKey;
  title: string;
  line: LineStyle;
  lineLabel: string;
}

export const ISSUES: Record<string, IssueMeta> = {
  machine_translation_cliche: { key: 'trans', title: '翻译腔与学术套话', line: 'solid', lineLabel: '实线' },
  ai_generated_suspicion: { key: 'ai', title: 'AI 生成特征', line: 'bold', lineLabel: '粗实线' },
  citation_gap: { key: 'gap', title: '引用支撑不足', line: 'dashed', lineLabel: '虚线' },
  style_heavy: { key: 'style', title: '句式臃肿', line: 'dotted', lineLabel: '点线' },
  semantic_plagiarism_risk: { key: 'plag', title: '与文献表述高度重合', line: 'double', lineLabel: '双线' },
  citation_contradiction: { key: 'contra', title: '与所引文献冲突', line: 'dashed', lineLabel: '虚线' },
};

const OTHER: IssueMeta = { key: 'other', title: '文风提示', line: 'solid', lineLabel: '实线' };
const INFRA: Record<string, string> = {
  json_parse_error: '模型输出无法解析',
  api_request_error: '云端接口未响应',
};

/** Fixed display order (the palette order). */
export const ISSUE_ORDER = Object.keys(ISSUES);

export function issueMeta(type: string | null | undefined): IssueMeta {
  if (type && ISSUES[type]) return ISSUES[type];
  if (type && INFRA[type]) return { ...OTHER, title: INFRA[type] };
  // An issue type the UI does not know yet: show the model's own label rather
  // than a generic one, so nothing is silently renamed.
  if (type && type !== 'unknown') return { ...OTHER, title: `其他：${type}` };
  return OTHER;
}

export const issueTitle = (type: string | null | undefined) => issueMeta(type).title;
