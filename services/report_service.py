import json

def generate_markdown_report(diagnostics: list[dict], citations: list[dict] = None) -> str:
    """
    Generate a beautiful, structured Markdown academic audit report from sentence diagnostics
    and citation audit results.
    """
    # 1. Separate global citation warnings, normal sentence results, and final session stats if any
    global_warnings = [d for d in diagnostics if d.get("index", 0) < 0]
    sentence_results = [d for d in diagnostics if d.get("index", 0) >= 0]
    
    # Extract overall risks from the last element if available or calculate approximations
    overall_risks = {
        "predictability_risk": 0.0,
        "uniformity_risk": 0.0,
        "translationese_risk": 0.0,
        "redundancy_risk": 0.0
    }
    if sentence_results:
        # Diagnostic results usually contain running risk metrics, grab the last one
        last_s = sentence_results[-1]
        for key in overall_risks:
            if key in last_s:
                overall_risks[key] = last_s[key]

    # Organize sentence results into flagged vs passed/ok
    flagged_sentences = [s for s in sentence_results if s.get("status") == "flagged"]
    passed_sentences = [s for s in sentence_results if s.get("status") in ("passed", "early_exit", "ok")]
    
    # 2. Build Markdown sections
    md = []
    md.append("# 学术论文写作质量与文献证据链审计报告")
    md.append("\n本报告由 **PhD Thesis Butler** 自动生成，系统基于本地规则启发式、物理 PPL 探针以及 NLI 证据链验证对您的手稿进行了多轨深度审计。\n")
    
    # Section: Document-Level Risk Indices
    md.append("## 1. 文档级风格与合规风险指数")
    md.append("| 风险维度 | 风险值 | 状态 | 评估释义 |")
    md.append("| :--- | :---: | :---: | :--- |")
    
    def get_risk_status(val: float) -> str:
        if val >= 70.0:
            return "🔴 高风险"
        elif val >= 40.0:
            return "🟡 中风险"
        return "🟢 低风险"
        
    md.append(f"| **学术预测度风险 (Predictability Risk)** | {overall_risks['predictability_risk']:.1f}% | {get_risk_status(overall_risks['predictability_risk'])} | 表征文本学术表意特征的异常流畅度（低 PPL 集中度），用于初步筛查潜在 di AI 代写与公式化套话风险。 |")
    md.append(f"| **行文均匀度风险 (Uniformity Risk)** | {overall_risks['uniformity_risk']:.1f}% | {get_risk_status(overall_risks['uniformity_risk'])} | 指示文本句子长度或句式结构的多样性缺乏度，极高值反映机器生成典型的千篇一律特征。 |")
    md.append(f"| **机器翻译腔风险 (Translationese Risk)** | {overall_risks['translationese_risk']:.1f}% | {get_risk_status(overall_risks['translationese_risk'])} | 检测俄文学术写作中常见的英语直译、被动语态泛滥及第二格名词链叠加倾向。 |")
    md.append(f"| **冗余修饰风险 (Redundancy Risk)** | {overall_risks['redundancy_risk']:.1f}% | {get_risk_status(overall_risks['redundancy_risk'])} | 统计文本中高频学术虚词、无实意连接词及套话填充词比例，表征句式是否精炼简洁。 |")

    
    # Section: Global Citation Integrity
    if global_warnings:
        md.append("\n## 2. 引用完整性交叉比对警告")
        md.append("在手稿的引文标号与文末参考文献著录（References）的交叉校验中，发现以下合规问题：\n")
        for idx, w in enumerate(global_warnings):
            md.append(f"### ⚠️ 完整性警告 {idx + 1}")
            md.append(f"- **问题类型**: `{w.get('issue_type')}` (严重度: `{w.get('severity')}`)")
            md.append(f"- **具体问题**: {w.get('explanation')}")
            md.append(f"- **修改建议**: {w.get('suggestion')}")
            if w.get("think"):
                md.append(f"- **审计思路**:\n  > {w.get('think')}")
            md.append("")

    # Section: Flagged Style & Syntax Sentences
    md.append("\n## 3. 需优化句段及风格诊断明细")
    if not flagged_sentences:
        md.append("🎉 **极佳！未在正文中检测到显著的风格警报、机器翻译腔或套话风险。**\n")
    else:
        md.append(f"本次诊断在正文中检测到共 **{len(flagged_sentences)}** 处存在学术表达缺陷、AI套话或翻译腔倾向的句子：\n")
        for idx, s in enumerate(flagged_sentences):
            md.append(f"### 🔍 问题句段 {idx + 1} (句索引: {s.get('index')})")
            md.append(f"**原句:**")
            md.append(f"> {s.get('text')}")
            md.append("")
            md.append(f"- **问题分类**: `{s.get('issue_type')}` (严重度: `{s.get('severity')}`)")
            if s.get("ppl") is not None:
                md.append(f"- **句子 Perplexity (PPL)**: `{s.get('ppl')}`")
            md.append(f"- **诊断释义**: {s.get('explanation')}")
            md.append(f"- **润色建议**: {s.get('suggestion')}")
            
            # Print metrics
            m = s.get("metrics", {})
            if m:
                metrics_str = ", ".join([f"{k}: {v}" for k, v in m.items() if v != 0])
                if metrics_str:
                    md.append(f"- **句法特征量**: `{metrics_str}`")
                    
            if s.get("think"):
                md.append(f"- **专家判定推理**:\n  > {s.get('think')}")
            
            # Citation audit in context of sentence
            sentence_audits = s.get("citation_audit", [])
            if sentence_audits:
                md.append("- **本句关联文献证据链核验 (NLI Citation Audit)**:")
                for sa in sentence_audits:
                    status_emoji = {
                        "SUPPORTED": "🟢 SUPPORTED (支撑)",
                        "CONTRADICTED": "🔴 CONTRADICTED (冲突)",
                        "NOT_ENOUGH_INFO": "🟡 NOT_ENOUGH_INFO (证据不足)",
                        "AUDIT_FAILED": "⚪ AUDIT_FAILED (审计未完成)"
                    }.get(sa.get("status"), sa.get("status"))
                    
                    md.append(f"  - **引文 Key**: `[{sa.get('key')}]` — 《{sa.get('title')}》")
                    md.append(f"  - **校验结论**: **{status_emoji}**")
                    md.append(f"  - **逻辑说明**: {sa.get('explanation_zh')}")
                    md.append(f"  - **证据原文片段 (Snippets)**:\n    > {sa.get('evidence_snippet')}")
            md.append("")

    # Section: Comprehensive Citation Evidence Check
    # Collect all citation audits across all sentences
    all_citation_audits = []
    for s in sentence_results:
        sentence_audits = s.get("citation_audit", [])
        for sa in sentence_audits:
            # Avoid duplicating same check
            all_citation_audits.append((s.get("text"), sa))
            
    if all_citation_audits:
        md.append("\n## 4. 参考文献断言证据链审计明细 (NLI Citation Audits)")
        md.append("以下是正文中包含的所有引用标记对应文献片段的逻辑支持度审计记录：\n")
        
        md.append("| 文中主张断言 (Claim) | 引用序号/Key | 关联文献标题 | NLI 核验状态 | 判定解释 |")
        md.append("| :--- | :---: | :--- | :---: | :--- |")
        
        for claim, sa in all_citation_audits:
            status_badge = {
                "SUPPORTED": "🟢 支持",
                "CONTRADICTED": "🔴 冲突",
                "NOT_ENOUGH_INFO": "🟡 证据不足",
                "AUDIT_FAILED": "⚪ 异常"
            }.get(sa.get("status"), sa.get("status"))
            
            # Truncate claim for table formatting
            claim_trunc = claim[:30] + "..." if len(claim) > 30 else claim
            title_trunc = sa.get("title", "")[:35] + "..." if len(sa.get("title", "")) > 35 else sa.get("title", "")
            
            md.append(f"| {claim_trunc} | `[{sa.get('key')}]` | 《{title_trunc}》 | {status_badge} | {sa.get('explanation_zh')} |")
            
        md.append("\n### NLI 证据链片段索引")
        for idx, (claim, sa) in enumerate(all_citation_audits):
            md.append(f"#### [{idx + 1}] 引文 `[{sa.get('key')}]` — 《{sa.get('title')}》")
            md.append(f"- **文中主张 (Claim)**: \"{claim}\"")
            md.append(f"- **文献来源**: `{sa.get('source')} database`")
            md.append(f"- **提取证据片段 (Snippet)**:")
            md.append(f"  > {sa.get('evidence_snippet')}")
            if sa.get("think"):
                md.append(f"- **判定思考轨迹 (Trace)**:\n  > {sa.get('think')}")
            md.append("")

    # Section: Audit Methodology & Configuration
    md.append("\n## 5. 审计说明与判定标准")
    md.append("- **学术预测度风险**: 指句子在统计学（基于 Qwen 本地语言模型计算）上表现出不合常理的极低困惑度（Perplexity < 10），说明其高度契合大模型生成的预测模式。")
    md.append("- **机器翻译腔检验**: 结合俄语依存语法树，计算第二格链状修饰（Genitive chains）、主宾被动语态比例以及特定英语翻译映射套话。")
    md.append("- **文献 NLI 校验**: 利用学术自然语言推理（Natural Language Inference）模型/专家提示词对 Claim 和文献 Snippet 进行蕴含、矛盾、无关三分类映射判断。")
    md.append("\n---\n*PhD Thesis Butler © 2026. 保持严谨与学术纯粹性。*")
    
    return "\n".join(md)

def export_report_data(diagnostics: list[dict], citations: list[dict] = None, format_type: str = "markdown") -> str:
    """
    Main export controller for exporting diagnostics and citation audit reports.
    """
    if format_type == "json":
        return json.dumps({
            "diagnostics": diagnostics,
            "citations": citations or [],
            "overall_summary": {
                "total_diagnosed_sentences": len([d for d in diagnostics if d.get("index", 0) >= 0]),
                "flagged_count": len([d for d in diagnostics if d.get("status") == "flagged"])
            }
        }, ensure_ascii=False, indent=2)
    else:
        return generate_markdown_report(diagnostics, citations)
