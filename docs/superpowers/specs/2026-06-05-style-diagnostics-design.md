# Design Spec: Style Diagnostics & Academic Naturalization (Workflow 5)

**Date**: 2026-06-05
**Context**: `phd-thesis-butler` (Russian Academic Writing Assistant)
**Status**: Draft (Pending User Review)

## 1. 目标 (Objective)

构建一个完全本地化、支持离线运行的俄语学术写作诊断引擎（Workflow 5）。该引擎主要用于检测和修复俄语论文草稿中的**机器翻译腔（Translationese）**、**AI套话模板**以及**句法过度均匀（Uniformity）**的问题。

本方案在设计上逆向参考了主流防剽窃系统（如 Antiplagiat.ru）的 AI 检测逻辑，通过引入代理指标（Proxy Indicators）来提升文本的真实感和学术自然度，但不承诺或直接输出“AI 概率”。

## 2. 硬件与核心模型 (Hardware & Target Model)

为完美适配 **RTX 3070 (8GB VRAM, CUDA)** 与 **Apple M3 Pro (Unified Memory, Metal)**：

*   **推断后端**: `llama-cpp-python` (跨平台硬件加速兼容，显存管理极其精准)。
*   **核心模型**: **Qwen 3 (4B-Instruct)** 或 **Qwen2.5-3B-Instruct** (量化格式：GGUF `Q5_K_M` 或 `Q8_0`)。
*   **显存占用**: 模型文件占 3.2GB 左右，预留约 1GB 显存给 2000 Tokens 左右的 KV Cache，完美适配 8GB VRAM 环境且杜绝 OOM。

## 3. “双轨并进”诊断架构 (The Anti-Simulator Pipeline)

引擎执行流程分为两个并行的探测轨道：

### 3.1 概率与突发度探测流 (Logits & Burstiness Analysis)
利用 `llama-cpp-python` 的底层 API 提取 token 的生成概率，不进行文本生成，仅进行评估。

*   **滑动窗口切块**: 为了保护显存并提高速度，文本被切分为每次 300-500 词的段落组（Chunks）。
*   **平均困惑度 (Mean PPL)**: 提取每一个俄语 token 的负对数似然度（Negative Log-Likelihood），计算句子级的 PPL。
*   **突发度计算 (Burstiness Variance)**: 统计段落内不同句子 PPL 的标准差。若标准差 $CV < 0.5$（即每句话长短与复杂度过度一致），触发 `Uniformity Risk: HIGH`。
*   **局部概率陷阱**: 检查句子内部是否存在局部的“低频词汇尖峰”。AI 文本通常全句处于高概率区，若某句全域概率平滑无异常波动，则判定为“套话”。

### 3.2 高层风格特征判别器 (LLM-as-a-Judge)
针对在 3.1 中被标记为高风险（如 PPL 极度平滑或方差极小）的句子，触发 Qwen 模型的生成功能，进行零样本（Zero-shot）病理诊断。

*   **输入**: 高风险句及其前后文。
*   **输出格式 (JSON)**:
    ```json
    {
      "has_translationese": true,
      "syntax_uniformity_issue": true,
      "cliches_found": ["Важно отметить, что", "Таким образом"],
      "naturalization_suggestion": "Исследование выявило..." // 带有倒装或名词化压缩的改写建议
    }
    ```

## 4. 自然化改写策略 (Academic Naturalization Tactics)

生成的改写建议（`naturalization_suggestion`）将严格遵循以下策略，以打破 AI 特征：
1.  **次优词注入 (Rank-Shift)**: 打破首选词概率分布，使用中低频的特定学术词汇。
2.  **句法倒装 (Syntactic Inversion)**: 舍弃默认的 S-V-O 结构，使用宾语/状语前置以符合高级俄语学术行文习惯。
3.  **名词化压缩 (Nominalization)**: 将口语化或机械的从句压缩为嵌套的名词第二格短语。

## 5. 输出报告展示 (Diagnostic Output)

诊断系统绝不会输出诸如 "AI Rate: 85%" 的误导性指标，而是输出专业的诊断报告：

```text
[诊断结果]
- Predictability risk: High (文本过于模式化)
- Sentence uniformity risk: High (句长极度均匀)
- Translationese risk: Medium

[高风险句分析]
> "В данном контексте мы можем видеть, что результаты показывают..."
- 问题: 包含典型翻译腔，且缺乏专业指代。
- Qwen 改写建议: "Полученные результаты свидетельствуют о..."
```

## 6. 本地部署目录结构设计

*   `scripts/style_diagnostics.py`: CLI 启动文件。
*   `naturalization_layer/qwen_evaluator.py`: 封装 `llama-cpp-python` 的 Logits 提取和 PPL 计算模块。
*   `naturalization_layer/prompts/judge_prompt.md`: Qwen JSON 格式诊断与重写提示词。

## 7. 运行参数示例

```bash
# 在 RTX 3070 或 M3 Pro 上本地启动诊断
python scripts/style_diagnostics.py \
  --input draft.md \
  --model qwen3-4b-instruct-q5_k_m.gguf \
  --mode full-diagnostics
```
