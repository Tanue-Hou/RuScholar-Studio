import json
import asyncio
from typing import AsyncGenerator

import os

from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.translationese_risk import run_translationese_checks
from naturalization_layer.source_similarity import check_source_similarity
from naturalization_layer.style_risk import calculate_style_risks, calculate_redundancy_risk
from naturalization_layer.translationese_risk import calculate_translationese_risk
from naturalization_layer.citation_integrity import check_citation_integrity

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_SKILL_RULES_PATH = os.path.join(PROJECT_ROOT, "naturalization_layer/rules/polishing_rules_v5.json")
SKILL_RULES_PATH = os.getenv("THESIS_BUTLER_RULES_PATH", PROJECT_SKILL_RULES_PATH)
CALIBRATION_CONFIG_PATH = os.path.join(PROJECT_ROOT, "naturalization_layer/calibration/calibration_config.json")

global_clusters = {}
calibration_db = {}

if os.path.exists(SKILL_RULES_PATH):
    try:
        with open(SKILL_RULES_PATH, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
            global_clusters = rules_data.get("clusters", {})
    except Exception as e:
        print(f"Failed to load skill rules: {e}")

if os.path.exists(CALIBRATION_CONFIG_PATH):
    try:
        with open(CALIBRATION_CONFIG_PATH, 'r', encoding='utf-8') as f:
            calibration_db = json.load(f)
    except Exception as e:
        print(f"Failed to load calibration config: {e}")

def get_discipline_rules(discipline: str) -> dict:
    rules = global_clusters.get(discipline, global_clusters.get("UNIVERSAL", None))
    if not rules and global_clusters:
        rules = next(iter(global_clusters.values()), None)
        
    if not rules:
        rules = {
            "do_rules": [
                "Использовать безличные и неопределенно-личные конструкции",
                "Соблюдать строгую логическую последовательность (введение -> методы -> результаты)"
            ],
            "dont_rules": [
                "Использовать местоимения первого лица (я, мы)",
                "Использовать эмоционально-окрашенную лексику и метафоры",
                "Злоупотреблять пассивным залогом и длинными цепочками существительных"
            ]
        }
    return rules

from services.shared_state import session_references, model_lock
from services.citation_audit_service import perform_nli_citation_audit

async def run_sentence_diagnose_stream(
    text: str, 
    session_id: str, 
    engine_type: str, 
    api_key: str, 
    base_url: str, 
    discipline: str, 
    engine_inst, 
    judge_inst, 
    citation_judge
) -> AsyncGenerator[dict, None]:
    """
    Run style and citation diagnostics on the entire text, yielding results in real-time.
    Shared by Web UI SSE connection.
    """
    # 1. Run Rules Engine on the whole text
    rules_res = analyze_text_rules(text)
    sentences = rules_res["sentences"]
    
    # 2. Run Citation Integrity check on the whole text
    integrity_report = check_citation_integrity(text)
    global_warnings = integrity_report.get("warnings", [])
    
    active_rules = get_discipline_rules(discipline)
    calib = calibration_db.get(discipline, calibration_db.get("UNIVERSAL", {}))
    
    ppl_low = calib.get("ppl_low", 15.0)
    ppl_high = calib.get("ppl_high", 80.0)
    nv_ratio_max = calib.get("nv_ratio_max", 4.5)
    
    # Yield init event matching frontend expectations
    yield {
        "event": "init",
        "data": json.dumps({"total_sentences": len(sentences), "discipline": discipline})
    }

    # Yield citation integrity warnings first as global diagnostics (with index = -1, -2...)
    for w_idx, warning in enumerate(global_warnings):
        yield {
            "event": "result",
            "data": json.dumps({
                "index": -1 - w_idx,
                "text": f"Citation Integrity Alert ({warning['evidence']})",
                "ppl": None,
                "issue_type": warning["issue_type"],
                "severity": warning["severity"],
                "explanation": warning["explanation_zh"],
                "suggestion": warning["rewrite_suggestion"],
                "think": f"【文献完整性校验警告】对文内引文标号与篇末参考文献列表进行交叉对照发现合规风险：{warning['explanation_zh']}。这会降低论文文献引用的规范度与学术严谨度，建议在最终稿中予以修正。",
                "status": "flagged",
                "metrics": None,
                "predictability_risk": 0.0,
                "uniformity_risk": 0.0,
                "translationese_risk": 0.0,
                "redundancy_risk": 0.0
            })
        }
        
    ppl_vals = []
    flagged_count = 0
    nv_ratios = []
    passive_counts = []
    genitive_chain_counts = []
    cliche_counts = []
    word_counts = []
    connectors_counts = []

    batch_size = 3
    if engine_type == "local":
        async def process_sentence_local(idx: int, text_str: str) -> dict:
            diag_rules = rules_res["sentence_diagnostics"][idx]
            
            if diag_rules.get("is_bibliography", False):
                return {
                    "index": idx,
                    "text": text_str,
                    "ppl": None,
                    "issue_type": None,
                    "severity": None,
                    "explanation": "参考文献免检：该句位于篇末参考文献著录区域，已跳过风格与AI检测防止格式误报。",
                    "suggestion": "无需修改。",
                    "think": "【参考文献免检】该句位于参考文献著录区域，跳过诊断以避免格式误触AI率及风格警报。",
                    "status": "passed",
                    "metrics": {
                        "nv_ratio": 0.0,
                        "passive_count": 0,
                        "genitive_chains_count": 0,
                        "cliches_count": 0,
                        "connectors_count": 0
                    }
                }
                
            has_citation = "[" in text_str
            sim_warning = check_source_similarity(text_str, has_citation)
            
            res_dict = {
                "index": idx,
                "text": text_str,
                "ppl": None,
                "issue_type": None,
                "severity": None,
                "explanation": None,
                "suggestion": None,
                "think": None,
                "status": "ok",
                "metrics": {
                    "nv_ratio": diag_rules.get("nv_ratio", 0.0),
                    "passive_count": diag_rules.get("passive_count", 0),
                    "genitive_chains_count": len(diag_rules.get("genitive_chains", [])),
                    "cliches_count": len(diag_rules.get("cliches_found", [])),
                    "connectors_count": len(diag_rules.get("connectors_found", []))
                }
            }
            
            trans_warnings = run_translationese_checks(text_str, diag_rules)
            if sim_warning and sim_warning["issue_type"] == "semantic_plagiarism_risk":
                trans_warnings.append(sim_warning)
                
            if trans_warnings:
                diag_rules["trans_warnings"] = [w["explanation_zh"] for w in trans_warnings]
            
            has_track_a_triggers = (
                len(diag_rules.get("cliches_found", [])) > 0 or
                len(diag_rules.get("genitive_chains", [])) > 0 or
                diag_rules.get("nv_ratio", 0.0) > nv_ratio_max or
                diag_rules.get("passive_count", 0) > 0 or
                len(trans_warnings) > 0
            )
            
            if engine_inst:
                ee_tokens = 6 if not has_track_a_triggers else 0
                ee_lower = ppl_low if not has_track_a_triggers else 0.0
                ee_upper = ppl_high if not has_track_a_triggers else float('inf')
                
                async with model_lock:
                    ppl, was_early_exited = await asyncio.to_thread(
                        engine_inst.evaluate_sentence_ppl, text_str, ee_tokens, ee_lower, ee_upper
                    )
                    
                res_dict["ppl"] = round(ppl, 2) if ppl else None
                is_suspicious = ppl < ppl_low or ppl > ppl_high or has_track_a_triggers
            else:
                was_early_exited = False
                is_suspicious = has_track_a_triggers
                
            if was_early_exited:
                res_dict["status"] = "early_exit"
                res_dict["think"] = (
                    f"【早期退出 (Early Exit)】评估前几个 Token 对应 Perplexity (PPL) 为 {res_dict.get('ppl')}，"
                    f"处于学术正常分布带 ({ppl_low} ~ {ppl_high}) 且无翻译腔或套话特征。已安全退回，跳过高算力专家诊断。"
                )
            elif sim_warning and sim_warning["issue_type"] == "citation_gap":
                res_dict["status"] = "flagged"
                res_dict["issue_type"] = "citation_gap"
                res_dict["severity"] = "high"
                res_dict["explanation"] = sim_warning["explanation_zh"]
                res_dict["suggestion"] = sim_warning["rewrite_suggestion"]
                res_dict["think"] = (
                    f"【学术改写与引用合规风险】该句与本地文献记录《{sim_warning['evidence']}》"
                    f"的表达重合度高，且在此处缺少参考文献引标，触发『引用缺口 (Citation Gap)』警告，请补充对应标注。"
                )
            elif is_suspicious:
                ctx_before = sentences[max(0, idx-2):idx]
                ctx_after = sentences[idx+1:min(len(sentences), idx+3)]
                
                async with model_lock:
                    diag = await asyncio.to_thread(
                        judge_inst.diagnose_sentence, 
                        text_str, 
                        stats=diag_rules, 
                        ppl=res_dict.get("ppl"), 
                        context_before=ctx_before, 
                        context_after=ctx_after,
                        skill_rules=active_rules,
                        engine_type=engine_type,
                        api_key=api_key,
                        base_url=base_url
                    )
                res_dict["think"] = diag.get("think", "")
                
                issues = diag.get("issues", [])
                
                # Low PPL Veto: override passed status if PPL is lower than ppl_low
                ppl_val = res_dict.get("ppl")
                if not issues and ppl_val is not None and ppl_val < ppl_low:
                    issues = [{
                        "issue_type": "ai_generated_suspicion",
                        "severity": "high",
                        "evidence": text_str,
                        "explanation_zh": f"物理困惑度极低 (PPL = {ppl_val:.2f} < {ppl_low:.1f})，触发一票否决 AI 风险拦截机制。该句的词汇分布过于平滑、可预测性极高，符合典型的机器生成特征。",
                        "explanation_ru": f"Крайне низкая физическая перплексивность (PPL = {ppl_val:.2f} < {ppl_low:.1f}), сработал механизм безусловной блокировки риска ИИ. Распределение слов слишком гладкое и предсказуемое, что характерно для генеративного текста.",
                        "rewrite_suggestion": "建议微调句式结构，打破过度平滑的词汇搭配，增强句子的学术个性与复杂度。"
                    }]
                    if not res_dict.get("think"):
                        res_dict["think"] = f"【一票否决拦截】检测到物理困惑度极低（PPL = {ppl_val:.2f}），已触发硬性判定拦截。"

                if issues:
                    issue = issues[0]
                    res_dict["issue_type"] = issue.get('issue_type', '')
                    res_dict["severity"] = issue.get('severity', '')
                    res_dict["explanation"] = issue.get('explanation_zh', '')
                    res_dict["suggestion"] = issue.get('rewrite_suggestion', '')
                    if res_dict["issue_type"] in ("api_request_error", "json_parse_error"):
                        res_dict["status"] = "passed"
                    else:
                        res_dict["status"] = "flagged"
                    if not res_dict["think"]:
                        res_dict["think"] = f"【专家模型判定】深度扫描检测到可疑特征：{res_dict['explanation']}"
                else:
                    res_dict["status"] = "passed"
                    if not res_dict["think"]:
                        res_dict["think"] = (
                            f"【深度扫描通过】句子经专家大模型多维度推理评估，尽管 Perplexity 偏离或有轻微规则触碰，"
                            f"但其整体语义连贯、学术表述符合规范，无显著的机器翻译或 AI 生成痕迹。"
                        )
            else:
                res_dict["status"] = "passed"
                res_dict["think"] = (
                    f"【规则通过】句子未触发生感官低 PPL 警报，亦无学术套话、拖沓修饰长链。"
                    f"名词动词比率（{res_dict['metrics']['nv_ratio']}）处于健康带，语态逻辑清晰，通过风格初筛。"
                )
                
            if session_id in session_references and citation_judge:
                audits = await perform_nli_citation_audit(
                    text_str, session_id, engine_type, api_key, base_url, citation_judge
                )
                if audits:
                    res_dict["citation_audit"] = audits
                    unsupported = [a for a in audits if a["status"] in ("CONTRADICTED", "NOT_ENOUGH_INFO")]
                    if unsupported:
                        first_un = unsupported[0]
                        res_dict["status"] = "flagged"
                        res_dict["issue_type"] = "citation_gap" if first_un["status"] == "NOT_ENOUGH_INFO" else "citation_contradiction"
                        res_dict["severity"] = "high"
                        res_dict["explanation"] = f"引用核验警告：文献《{first_un['title']}》对文中论点支撑不足或存在逻辑冲突。大模型核验结论：{first_un['explanation_zh']}"
                        res_dict["suggestion"] = "请重新检查该引言与文献的逻辑对应关系，补充原文强支撑片段，或更换更切合的参考文献。"
                        res_dict["think"] = f"【引用文献逻辑校验异常】引用的文献《{first_un['title']}》分析发现风险：{first_un['explanation_zh']}"
                        
            return res_dict

        for batch_start in range(0, len(sentences), batch_size):
            batch_sentences = sentences[batch_start:batch_start + batch_size]
            tasks = [process_sentence_local(batch_start + j, s) for j, s in enumerate(batch_sentences)]
            batch_results = await asyncio.gather(*tasks)
            
            for result in batch_results:
                ppl_vals.append(result["ppl"])
                nv_ratios.append(result["metrics"]["nv_ratio"])
                passive_counts.append(result["metrics"]["passive_count"])
                genitive_chain_counts.append(result["metrics"]["genitive_chains_count"])
                cliche_counts.append(result["metrics"]["cliches_count"])
                word_counts.append(len(result["text"].split()))
                connectors_counts.append(result["metrics"]["connectors_count"])
                
                if result["status"] == "flagged":
                    flagged_count += 1
                    
                running_pred, running_unif = calculate_style_risks(
                    ppl_vals, flagged_count, result["index"] + 1, calib, word_counts=word_counts
                )
                running_trans = calculate_translationese_risk(nv_ratios, passive_counts, genitive_chain_counts)
                running_red = calculate_redundancy_risk(
                    cliche_counts, genitive_chain_counts, passive_counts, nv_ratios, connectors_counts
                )
                
                result["predictability_risk"] = running_pred
                result["uniformity_risk"] = running_unif
                result["translationese_risk"] = running_trans
                result["redundancy_risk"] = running_red
                
                yield {"event": "result", "data": json.dumps(result)}
            
            await asyncio.sleep(0.01)
    else:
        # Branch B: Cloud / Hybrid Cloud API mode
        async def process_sentence_cloud(idx: int, text_str: str) -> dict:
            diag_rules = rules_res["sentence_diagnostics"][idx]
            
            if diag_rules.get("is_bibliography", False):
                return {
                    "index": idx,
                    "text": text_str,
                    "ppl": None,
                    "issue_type": None,
                    "severity": None,
                    "explanation": "参考文献免检：该句位于篇末参考文献著录区域，已跳过风格与AI检测防止格式误报。",
                    "suggestion": "无需修改。",
                    "think": "【参考文献免检】该句位于参考文献著录区域，跳过诊断以避免格式误触AI率及风格警报。",
                    "status": "passed",
                    "metrics": {
                        "nv_ratio": 0.0,
                        "passive_count": 0,
                        "genitive_chains_count": 0,
                        "cliches_count": 0,
                        "connectors_count": 0
                    }
                }
                
            has_citation = "[" in text_str
            sim_warning = check_source_similarity(text_str, has_citation)
            
            res_dict = {
                "index": idx,
                "text": text_str,
                "ppl": None,
                "issue_type": None,
                "severity": None,
                "explanation": None,
                "suggestion": None,
                "think": None,
                "status": "ok",
                "metrics": {
                    "nv_ratio": diag_rules.get("nv_ratio", 0.0),
                    "passive_count": diag_rules.get("passive_count", 0),
                    "genitive_chains_count": len(diag_rules.get("genitive_chains", [])),
                    "cliches_count": len(diag_rules.get("cliches_found", [])),
                    "connectors_count": len(diag_rules.get("connectors_found", []))
                }
            }
            
            trans_warnings = run_translationese_checks(text_str, diag_rules)
            if sim_warning and sim_warning["issue_type"] == "semantic_plagiarism_risk":
                trans_warnings.append(sim_warning)
                
            if trans_warnings:
                diag_rules["trans_warnings"] = [w["explanation_zh"] for w in trans_warnings]
                
            if sim_warning and sim_warning["issue_type"] == "citation_gap":
                res_dict["status"] = "flagged"
                res_dict["issue_type"] = "citation_gap"
                res_dict["severity"] = "high"
                res_dict["explanation"] = sim_warning["explanation_zh"]
                res_dict["suggestion"] = sim_warning["rewrite_suggestion"]
                res_dict["think"] = (
                    f"【学术改写与引用合规风险】该句与本地文献记录《{sim_warning['evidence']}》"
                    f"的表达重合度高，且在此处缺少参考文献引标，触发『引用缺口 (Citation Gap)』警告，请补充对应标注。"
                )
            else:
                ctx_before = sentences[max(0, idx-2):idx]
                ctx_after = sentences[idx+1:min(len(sentences), idx+3)]
                
                compute_local_ppl = engine_type.startswith("hybrid")
                ppl_val = None
                if compute_local_ppl and engine_inst:
                    async with model_lock:
                        ppl_val, _ = await asyncio.to_thread(
                            engine_inst.evaluate_sentence_ppl, text_str, 0, 0.0, float('inf')
                        )
                        ppl_val = round(ppl_val, 2) if ppl_val else None

                actual_cloud_model = "deepseek-v4-flash" if "flash" in engine_type else "deepseek-v4-pro"

                diag = await asyncio.to_thread(
                    judge_inst.diagnose_sentence, 
                    text_str, 
                    stats=diag_rules, 
                    ppl=ppl_val,
                    context_before=ctx_before, 
                    context_after=ctx_after,
                    skill_rules=active_rules,
                    engine_type=actual_cloud_model,
                    api_key=api_key,
                    base_url=base_url
                )
                res_dict["think"] = diag.get("think", "")
                res_dict["ppl"] = ppl_val
                    
                issues = diag.get("issues", [])
                
                # Low PPL Veto: override passed status if PPL is lower than ppl_low
                ppl_val = res_dict.get("ppl")
                if not issues and ppl_val is not None and ppl_val < ppl_low:
                    issues = [{
                        "issue_type": "ai_generated_suspicion",
                        "severity": "high",
                        "evidence": text_str,
                        "explanation_zh": f"物理困惑度极低 (PPL = {ppl_val:.2f} < {ppl_low:.1f})，触发一票否决 AI 风险拦截机制。该句的词汇分布过于平滑、可预测性极高，符合典型的机器生成特征。",
                        "explanation_ru": f"Крайне низкая физическая перплексивность (PPL = {ppl_val:.2f} < {ppl_low:.1f}), сработал механизм безусловной блокировки риска ИИ. Распределение слов слишком гладкое и предсказуемое, что характерно для генеративного текста.",
                        "rewrite_suggestion": "建议微调句式结构，打破过度平滑的词汇搭配，增强句子的学术个性与复杂度。"
                    }]
                    if not res_dict.get("think"):
                        res_dict["think"] = f"【一票否决拦截】检测到物理困惑度极低（PPL = {ppl_val:.2f}），已触发硬性判定拦截。"

                if issues:
                    issue = issues[0]
                    res_dict["issue_type"] = issue.get('issue_type', '')
                    res_dict["severity"] = issue.get('severity', '')
                    res_dict["explanation"] = issue.get('explanation_zh', '')
                    res_dict["suggestion"] = issue.get('rewrite_suggestion', '')
                    if res_dict["issue_type"] in ("api_request_error", "json_parse_error"):
                        res_dict["status"] = "passed"
                    else:
                        res_dict["status"] = "flagged"
                    if not res_dict["think"]:
                        res_dict["think"] = f"【专家模型判定】深度扫描检测到可疑特征：{res_dict['explanation']}"
                else:
                    res_dict["status"] = "passed"
                    if not res_dict["think"]:
                        res_dict["think"] = (
                            f"【深度扫描通过】句子经专家大模型多维度推理评估，尽管 Perplexity 偏离或有轻微规则触碰，"
                            f"但其整体语义连贯、学术表述符合规范，无显著的机器翻译或 AI 生成痕迹。"
                        )
                        
            if session_id in session_references and citation_judge:
                audits = await perform_nli_citation_audit(
                    text_str, session_id, engine_type, api_key, base_url, citation_judge
                )
                if audits:
                    res_dict["citation_audit"] = audits
                    unsupported = [a for a in audits if a["status"] in ("CONTRADICTED", "NOT_ENOUGH_INFO")]
                    if unsupported:
                        first_un = unsupported[0]
                        res_dict["status"] = "flagged"
                        res_dict["issue_type"] = "citation_gap" if first_un["status"] == "NOT_ENOUGH_INFO" else "citation_contradiction"
                        res_dict["severity"] = "high"
                        res_dict["explanation"] = f"引用核验警告：文献《{first_un['title']}》对文中论点支撑不足或存在逻辑冲突。大模型核验结论：{first_un['explanation_zh']}"
                        res_dict["suggestion"] = "请重新检查该引言与文献的逻辑对应关系，补充原文强支撑片段，或更换更切合的参考文献。"
                        res_dict["think"] = f"【引用文献逻辑校验异常】引用的文献《{first_un['title']}》分析发现风险：{first_un['explanation_zh']}"
                        
            return res_dict

        for batch_start in range(0, len(sentences), batch_size):
            batch_sentences = sentences[batch_start:batch_start + batch_size]
            tasks = [process_sentence_cloud(batch_start + j, s) for j, s in enumerate(batch_sentences)]
            batch_results = await asyncio.gather(*tasks)
            
            for result in batch_results:
                ppl_vals.append(result["ppl"])
                nv_ratios.append(result["metrics"]["nv_ratio"])
                passive_counts.append(result["metrics"]["passive_count"])
                genitive_chain_counts.append(result["metrics"]["genitive_chains_count"])
                cliche_counts.append(result["metrics"]["cliches_count"])
                word_counts.append(len(result["text"].split()))
                connectors_counts.append(result["metrics"]["connectors_count"])
                
                if result["status"] == "flagged":
                    flagged_count += 1
                    
                running_pred, running_unif = calculate_style_risks(
                    ppl_vals, flagged_count, result["index"] + 1, calib, word_counts=word_counts
                )
                running_trans = calculate_translationese_risk(nv_ratios, passive_counts, genitive_chain_counts)
                running_red = calculate_redundancy_risk(
                    cliche_counts, genitive_chain_counts, passive_counts, nv_ratios, connectors_counts
                )
                
                result["predictability_risk"] = running_pred
                result["uniformity_risk"] = running_unif
                result["translationese_risk"] = running_trans
                result["redundancy_risk"] = running_red
                
                yield {"event": "result", "data": json.dumps(result)}
            
            await asyncio.sleep(0.01)
            
    # Final document-level risks
    pred_risk, unif_risk = calculate_style_risks(
        ppl_vals, flagged_count, len(sentences), calib, word_counts=word_counts
    )
    trans_risk = calculate_translationese_risk(nv_ratios, passive_counts, genitive_chain_counts)
    redundancy_risk = calculate_redundancy_risk(
        cliche_counts, genitive_chain_counts, passive_counts, nv_ratios, connectors_counts
    )
    
    yield {
        "event": "done",
        "data": json.dumps({
            "predictability_risk": pred_risk,
            "uniformity_risk": unif_risk,
            "translationese_risk": trans_risk,
            "redundancy_risk": redundancy_risk
        })
    }

async def run_sentence_diagnose_batch(
    text: str, 
    session_id: str, 
    engine_type: str, 
    api_key: str, 
    base_url: str, 
    discipline: str, 
    engine_inst, 
    judge_inst, 
    citation_judge
) -> list[dict]:
    """
    Synchronous batch diagnostics, collecting all stream items and returning them as a list.
    Used by MCP tool.
    """
    results = []
    async for event in run_sentence_diagnose_stream(
        text, session_id, engine_type, api_key, base_url, discipline, engine_inst, judge_inst, citation_judge
    ):
        if event["event"] == "result":
            results.append(json.loads(event["data"]))
    return results
