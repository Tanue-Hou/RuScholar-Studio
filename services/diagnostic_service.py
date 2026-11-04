"""
Sentence-level style + citation diagnostics, shared by the Web UI (SSE stream)
and the MCP tools (batch).

One pipeline handles every engine mode:
  * local        — local PPL (with early exit) gates whether the local judge runs;
  * hybrid-*     — local PPL (no early exit, if the model is present) + cloud judge;
  * cloud-*      — cloud judge only.
"""
import asyncio
import json
from typing import AsyncGenerator

from naturalization_layer.citation_integrity import check_citation_integrity
from naturalization_layer.llm_client import cloud_model_for
from naturalization_layer.rules_engine import analyze_text_rules
from naturalization_layer.source_similarity import check_source_similarity
from naturalization_layer.style_risk import calculate_redundancy_risk, calculate_style_risks
from naturalization_layer.translationese_risk import calculate_translationese_risk, run_translationese_checks
from services.citation_audit_service import perform_nli_citation_audit
from services.rules_config import get_calibration, get_discipline_rules
from services.model_registry import registry
from services.shared_state import session_references

# Re-exported for existing importers (mcp_server.server).
__all__ = ["get_discipline_rules", "run_sentence_diagnose_stream", "run_sentence_diagnose_batch"]

BATCH_SIZE = 3


def _empty_metrics() -> dict:
    return {
        "nv_ratio": 0.0,
        "passive_count": 0,
        "genitive_chains_count": 0,
        "cliches_count": 0,
        "connectors_count": 0
    }


def _bibliography_result(idx: int, text_str: str) -> dict:
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
        "metrics": _empty_metrics()
    }


def _base_result(idx: int, text_str: str, diag_rules: dict) -> dict:
    return {
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


def _integrity_warning_result(w_idx: int, warning: dict) -> dict:
    return {
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
    }


def _apply_citation_gap(res: dict, sim_warning: dict) -> None:
    res["status"] = "flagged"
    res["issue_type"] = "citation_gap"
    res["severity"] = "high"
    res["explanation"] = sim_warning["explanation_zh"]
    res["suggestion"] = sim_warning["rewrite_suggestion"]
    res["think"] = (
        f"【学术改写与引用合规风险】该句与本地文献记录《{sim_warning['evidence']}》"
        f"的表达重合度高，且在此处缺少参考文献引标，触发『引用缺口 (Citation Gap)』警告，请补充对应标注。"
    )


def _apply_early_exit(res: dict, ppl_low: float, ppl_high: float) -> None:
    res["status"] = "early_exit"
    res["think"] = (
        f"【早期退出 (Early Exit)】评估前几个 Token 对应 Perplexity (PPL) 为 {res.get('ppl')}，"
        f"处于学术正常分布带 ({ppl_low} ~ {ppl_high}) 且无翻译腔或套话特征。已安全退回，跳过高算力专家诊断。"
    )


def _apply_rules_pass(res: dict) -> None:
    res["status"] = "passed"
    res["think"] = (
        f"【规则通过】句子未触发生感官低 PPL 警报，亦无学术套话、拖沓修饰长链。"
        f"名词动词比率（{res['metrics']['nv_ratio']}）处于健康带，语态逻辑清晰，通过风格初筛。"
    )


def _apply_judgement(res: dict, diag: dict, text_str: str, ppl_low: float) -> None:
    """Fold the judge's verdict (plus the low-PPL veto) into the sentence result."""
    issues = diag.get("issues", [])

    # Low PPL Veto: override passed status if PPL is lower than ppl_low
    ppl_val = res.get("ppl")
    if not issues and ppl_val is not None and ppl_val < ppl_low:
        issues = [{
            "issue_type": "ai_generated_suspicion",
            "severity": "high",
            "evidence": text_str,
            "explanation_zh": f"物理困惑度极低 (PPL = {ppl_val:.2f} < {ppl_low:.1f})，触发一票否决 AI 风险拦截机制。该句的词汇分布过于平滑、可预测性极高，符合典型的机器生成特征。",
            "explanation_ru": f"Крайне низкая физическая перплексивность (PPL = {ppl_val:.2f} < {ppl_low:.1f}), сработал механизм безусловной блокировки риска ИИ. Распределение слов слишком гладкое и предсказуемое, что характерно для генеративного текста.",
            "rewrite_suggestion": "建议微调句式结构，打破过度平滑的词汇搭配，增强句子的学术个性与复杂度。"
        }]
        if not res.get("think"):
            res["think"] = f"【一票否决拦截】检测到物理困惑度极低（PPL = {ppl_val:.2f}），已触发硬性判定拦截。"

    if issues:
        issue = issues[0]
        res["issue_type"] = issue.get('issue_type', '')
        res["severity"] = issue.get('severity', '')
        res["explanation"] = issue.get('explanation_zh', '')
        res["suggestion"] = issue.get('rewrite_suggestion', '')
        # Infrastructure failures are not findings about the text.
        if res["issue_type"] in ("api_request_error", "json_parse_error"):
            res["status"] = "passed"
        else:
            res["status"] = "flagged"
        if not res["think"]:
            res["think"] = f"【专家模型判定】深度扫描检测到可疑特征：{res['explanation']}"
    else:
        res["status"] = "passed"
        if not res["think"]:
            res["think"] = (
                f"【深度扫描通过】句子经专家大模型多维度推理评估，尽管 Perplexity 偏离或有轻微规则触碰，"
                f"但其整体语义连贯、学术表述符合规范，无显著的机器翻译或 AI 生成痕迹。"
            )


def _apply_citation_audits(res: dict, audits: list) -> None:
    res["citation_audit"] = audits
    unsupported = [a for a in audits if a["status"] in ("CONTRADICTED", "NOT_ENOUGH_INFO")]
    if unsupported:
        first_un = unsupported[0]
        res["status"] = "flagged"
        res["issue_type"] = "citation_gap" if first_un["status"] == "NOT_ENOUGH_INFO" else "citation_contradiction"
        res["severity"] = "high"
        res["explanation"] = f"引用核验警告：文献《{first_un['title']}》对文中论点支撑不足或存在逻辑冲突。大模型核验结论：{first_un['explanation_zh']}"
        res["suggestion"] = "请重新检查该引言与文献的逻辑对应关系，补充原文强支撑片段，或更换更切合的参考文献。"
        res["think"] = f"【引用文献逻辑校验异常】引用的文献《{first_un['title']}》分析发现风险：{first_un['explanation_zh']}"


class _RunningRisks:
    """Accumulates per-sentence metrics and computes running / final document risks."""

    def __init__(self, calib: dict):
        self.calib = calib
        self.ppl_vals = []
        self.nv_ratios = []
        self.passive_counts = []
        self.genitive_chain_counts = []
        self.cliche_counts = []
        self.word_counts = []
        self.connectors_counts = []
        self.flagged_count = 0

    def add(self, result: dict) -> None:
        m = result["metrics"]
        self.ppl_vals.append(result["ppl"])
        self.nv_ratios.append(m["nv_ratio"])
        self.passive_counts.append(m["passive_count"])
        self.genitive_chain_counts.append(m["genitive_chains_count"])
        self.cliche_counts.append(m["cliches_count"])
        self.word_counts.append(len(result["text"].split()))
        self.connectors_counts.append(m["connectors_count"])
        if result["status"] == "flagged":
            self.flagged_count += 1

    def risks(self, n_sentences: int) -> dict:
        pred, unif = calculate_style_risks(
            self.ppl_vals, self.flagged_count, n_sentences, self.calib, word_counts=self.word_counts
        )
        return {
            "predictability_risk": pred,
            "uniformity_risk": unif,
            "translationese_risk": calculate_translationese_risk(
                self.nv_ratios, self.passive_counts, self.genitive_chain_counts
            ),
            "redundancy_risk": calculate_redundancy_risk(
                self.cliche_counts, self.genitive_chain_counts, self.passive_counts,
                self.nv_ratios, self.connectors_counts
            ),
        }


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
    Run style and citation diagnostics on the entire text, yielding SSE-shaped
    events: one "init", one "result" per integrity warning and per sentence,
    then "done" with document-level risks.
    """
    # 1. Run Rules Engine on the whole text
    rules_res = analyze_text_rules(text)
    sentences = rules_res["sentences"]

    # 2. Run Citation Integrity check on the whole text
    integrity_report = check_citation_integrity(text)
    global_warnings = integrity_report.get("warnings", [])

    active_rules = get_discipline_rules(discipline)
    calib = get_calibration(discipline)
    ppl_low = calib.get("ppl_low", 15.0)
    ppl_high = calib.get("ppl_high", 80.0)
    nv_ratio_max = calib.get("nv_ratio_max", 4.5)

    is_local = engine_type == "local"
    use_local_ppl = is_local or engine_type.startswith("hybrid")
    judge_model = "local" if is_local else cloud_model_for(engine_type)

    yield {
        "event": "init",
        "data": json.dumps({
            "total_sentences": len(sentences),
            "discipline": discipline,
            "nlp_backend": rules_res.get("nlp_backend", "spacy")
        })
    }

    # Citation integrity warnings first, as global diagnostics (index = -1, -2, ...)
    for w_idx, warning in enumerate(global_warnings):
        yield {"event": "result", "data": json.dumps(_integrity_warning_result(w_idx, warning))}

    async def diagnose_with_judge(idx: int, text_str: str, diag_rules: dict, res: dict) -> None:
        ctx_before = sentences[max(0, idx - 2):idx]
        ctx_after = sentences[idx + 1:min(len(sentences), idx + 3)]
        call = lambda: judge_inst.diagnose_sentence(  # noqa: E731
            text_str,
            stats=diag_rules,
            ppl=res.get("ppl"),
            context_before=ctx_before,
            context_after=ctx_after,
            skill_rules=active_rules,
            engine_type=judge_model,
            api_key=api_key,
            base_url=base_url
        )
        if is_local:
            diag = await registry.run_local(call)
        else:
            diag = await asyncio.to_thread(call)
        res["think"] = diag.get("think", "")
        _apply_judgement(res, diag, text_str, ppl_low)

    async def process_sentence(idx: int, text_str: str) -> dict:
        diag_rules = rules_res["sentence_diagnostics"][idx]
        if diag_rules.get("is_bibliography", False):
            return _bibliography_result(idx, text_str)

        sim_warning = check_source_similarity(text_str, "[" in text_str)
        res = _base_result(idx, text_str, diag_rules)

        trans_warnings = run_translationese_checks(text_str, diag_rules)
        if sim_warning and sim_warning["issue_type"] == "semantic_plagiarism_risk":
            trans_warnings.append(sim_warning)
        if trans_warnings:
            diag_rules["trans_warnings"] = [w["explanation_zh"] for w in trans_warnings]
        is_citation_gap = bool(sim_warning and sim_warning["issue_type"] == "citation_gap")

        if is_local:
            has_track_a_triggers = (
                len(diag_rules.get("cliches_found", [])) > 0 or
                len(diag_rules.get("genitive_chains", [])) > 0 or
                diag_rules.get("nv_ratio", 0.0) > nv_ratio_max or
                diag_rules.get("passive_count", 0) > 0 or
                len(trans_warnings) > 0
            )
            was_early_exited = False
            if engine_inst:
                # Early exit only for "clean" sentences: no rule triggers at all.
                ee_tokens = 6 if not has_track_a_triggers else 0
                ee_lower = ppl_low if not has_track_a_triggers else 0.0
                ee_upper = ppl_high if not has_track_a_triggers else float('inf')
                ppl, was_early_exited = await registry.run_local(
                    engine_inst.evaluate_sentence_ppl, text_str, ee_tokens, ee_lower, ee_upper
                )
                res["ppl"] = round(ppl, 2) if ppl else None
                is_suspicious = ppl < ppl_low or ppl > ppl_high or has_track_a_triggers
            else:
                is_suspicious = has_track_a_triggers

            if was_early_exited:
                _apply_early_exit(res, ppl_low, ppl_high)
            elif is_citation_gap:
                _apply_citation_gap(res, sim_warning)
            elif is_suspicious:
                await diagnose_with_judge(idx, text_str, diag_rules, res)
            else:
                _apply_rules_pass(res)
        else:
            if is_citation_gap:
                _apply_citation_gap(res, sim_warning)
            else:
                if use_local_ppl and engine_inst:
                    ppl, _ = await registry.run_local(
                        engine_inst.evaluate_sentence_ppl, text_str, 0, 0.0, float('inf')
                    )
                    res["ppl"] = round(ppl, 2) if ppl else None
                await diagnose_with_judge(idx, text_str, diag_rules, res)

        if session_id in session_references and citation_judge:
            audits = await perform_nli_citation_audit(
                text_str, session_id, engine_type, api_key, base_url, citation_judge
            )
            if audits:
                _apply_citation_audits(res, audits)

        return res

    running = _RunningRisks(calib)
    for batch_start in range(0, len(sentences), BATCH_SIZE):
        batch = sentences[batch_start:batch_start + BATCH_SIZE]
        batch_results = await asyncio.gather(
            *[process_sentence(batch_start + j, s) for j, s in enumerate(batch)]
        )
        for result in batch_results:
            running.add(result)
            result.update(running.risks(result["index"] + 1))
            yield {"event": "result", "data": json.dumps(result)}
        await asyncio.sleep(0.01)

    yield {"event": "done", "data": json.dumps(running.risks(len(sentences)))}


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
    Collect all "result" events of the stream into a list. Used by MCP tools.
    """
    results = []
    async for event in run_sentence_diagnose_stream(
        text, session_id, engine_type, api_key, base_url, discipline, engine_inst, judge_inst, citation_judge
    ):
        if event["event"] == "result":
            results.append(json.loads(event["data"]))
    return results
