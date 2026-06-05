# Design Spec: Russian Academic Naturalness Diagnostics Engine

**Date**: 2026-06-05 (Updated 2026-06-06)
**Context**: `phd-thesis-butler` (Russian Academic Writing Assistant)
**Status**: Formal Draft (Pending Review)

## 1. Ethical Boundary & Product Philosophy
本模块正式命名为 **Russian Academic Naturalness Diagnostics Engine (俄语学术自然度与翻译腔诊断引擎)**。
- **定位**：本模块用于多维度诊断文本中的写作风险，包括：疑似人工智能生成（AI-generated suspicion）、机器翻译腔（Translationese）、模板化表达（Generic Cliché）、语义冗余（Redundancy）、术语不一致（Terminology Inconsistency）等。
- **判断依据优先**：系统不给出武断的“查重率”百分比，而是将“AI生成”、“机翻腔”等作为具体的诊断选项（Issue Types），并强制要求模型给出明确的判断依据（Evidence）和原因解释（Explanation）。

## 2. Four-Track Architecture (四轨架构)
系统采用分离的底层统计与高层语义判别机制：

- **Track A: Rule-based diagnostics (规则与结构统计)**
  - 核心指标：`sentence_length_mean`, `sentence_length_std`, `connector_density`, `cliche_density`。
- **Track B: Qwen3 Predictability Probe (可预测性代理指标)**
  - 后端：`Qwen3-4B-GGUF` + `llama-cpp-python` (启用 `logits_all=True`)。
  - 核心指标：`token_nll_std`, `sentence_ppl_mean`, `sentence_ppl_std`, `low_surprise_token_ratio`, `predictability_plateau_length`。
  - 功能：提取预测难度特征，将异常平滑的区域抛给 Track D。
- **Track C: Redundancy & Specificity Analysis (冗余与具体性分析)**
  - 功能：检查语义重复（车轱辘话）、以及判断对象/方法/指标等是否明确。
- **Track D: Qwen3 Explanatory Review and Naturalization (解释性学术编辑)**
  - 后端：Qwen3 作为强大的学术编辑者阅读上下文。
  - 功能：在多维诊断选项中（含 AI 生成嫌疑、机翻腔等）进行归类，并提取原文证据。

## 3. LLM JSON Schema
LLM Judge 将输出详尽的 `issues` 列表，严格遵循以下结构，将“AI生成”作为可选的 `issue_type` 之一：

```json
{
  "segment_id": "p003_s002",
  "issues": [
    {
      "issue_type": "ai_generated_suspicion", // 可选: ai_generated_suspicion, machine_translation_cliche, semantic_redundancy, lack_of_specificity, etc.
      "severity": "high",
      "evidence": "В данном исследовании мы изучили... Важно отметить, что...",
      "explanation_zh": "这段话使用了高度模板化的引导语，缺乏针对该学科的具体指代，且行文结构完全符合典型大模型的万能开头模版，疑似为人工智能生成。",
      "explanation_ru": "Текст имеет шаблонную структуру, характерную для генерации ИИ, без специфической привязки к предмету...",
      "recommended_action": "rewrite",
      "rewrite_suggestion": "Проведенный анализ...",
      "author_check_required": true
    }
  ],
  "overall_comment": "整体逻辑连贯，但在引言部分存在较多疑似 AI 生成的模板化结构。",
  "safe_to_rewrite": true
}
```

## 4. Scoring System (评分系统)
构建 **Style Risk Index** (0-100)，涵盖以下诊断选项风险：
- AI-generated Suspicion Risk (疑似 AI 生成风险)
- Translationese Risk (机器翻译腔风险)
- Generic Cliché Risk (套话模板风险)
- Uniformity / Predictability Risk (结构过度均匀风险)
- Redundancy Risk (语义冗余风险)

## 5. Streamlit UI Design (双栏交互界面)
- **左栏 (Analysis Panel)**：展示分维度指标面板与 Issue Cards（诊断卡片，卡片右上角标注唯一 `issue_id`，卡片内明确标示**判断依据 Evidence**和**问题类型**）。
- **右栏 (Manuscript Viewer)**：完整展示用户文档。对应存在风险的文本通过 HTML 标签 `<mark class="risk-high" data-issue="I-001">` 进行视觉高亮。
- **P0 阶段限制**：仅支持静态高亮和点击左栏卡片时的页面锚点跳转定位。

## 6. Calibration Framework (校准集框架)
- **目录规划**：`calibration/`。
- **P0 策略**：仅创建空目录结构、`calibration_schema.json` 以及 `calibration_baseline.example.json`。使用 heuristic 阈值。
- **P1 策略**：填充真实语料样本。

## 7. RTX 3070 Runtime Strategy
- **分块策略**：按句子或短段落为 Chunk 使用滑动窗口，禁止整章无脑抛给大模型。
- **硬保护规则 (Hard Protection)**：禁止修改并豁免诊断涉及到的公式、变量、单位、数值、引用编号 `[23]`、图表编号、方法缩写。

## 8. Output Files (持久化输出)
- `style_diagnostic.json`
- `style_diagnostic_report.md`
- `highlighted_manuscript.html`
- `revision_suggestions.md`
- `author_check_items.md`
- `calibration_status.json`

## 9. Implementation Plan (执行优先次序)

### P0 (Foundation & Heuristics)
- [ ] P0-1: 冻结命名与伦理边界规范代码。
- [ ] P0-2: 实现 Pydantic 版本的 JSON Schema。
- [ ] P0-3: 实现 Track A 规则诊断（无模型版）。
- [ ] P0-4: 实现 Track D LLM Judge。
- [ ] P0-5: 实现 Streamlit 双栏 UI 静态高亮与锚点对应。
- [ ] P0-6: 接入 Track B PPL Proxy。
- [ ] P0-7: 接入 Track C 语义重复检测。
- [ ] P0-8: 建立 `calibration/` 框架目录。
- [ ] P0-9: 生成全链路离线测试报告。
