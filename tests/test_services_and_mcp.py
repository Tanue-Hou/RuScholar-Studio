import pytest
from unittest.mock import patch, MagicMock
from services.report_service import generate_markdown_report, export_report_data
from services.shared_state import session_references
from naturalization_layer.rag_retriever import BM25Retriever
import mcp_server.server

def test_report_generation():
    diagnostics = [
        {
            "index": -1,
            "text": "Citation Integrity Alert ([1])",
            "ppl": None,
            "issue_type": "missing_references_listing",
            "severity": "medium",
            "explanation": "引文标注[1]在文末参考文献列表中未找到对应条目。",
            "suggestion": "请在文末参考文献列表中添加[1]对应的文献著录。",
            "think": "【文献完整性校验警告】对文内引文标号与篇末参考文献列表进行交叉对照发现合规风险",
            "status": "flagged"
        },
        {
            "index": 0,
            "text": "Это тестовое предложение с высокой AI-вероятностью.",
            "ppl": 8.5,
            "issue_type": "ai_cliche",
            "severity": "high",
            "explanation": "Обнаружены ИИ-шаблоны.",
            "suggestion": "Переписать более естественно.",
            "think": "Тестовое рассуждение.",
            "status": "flagged",
            "metrics": {
                "nv_ratio": 5.0,
                "passive_count": 1
            },
            "predictability_risk": 80.0,
            "uniformity_risk": 50.0,
            "translationese_risk": 90.0,
            "redundancy_risk": 40.0
        }
    ]
    
    # Test Markdown Export
    report_md = export_report_data(diagnostics, format_type="markdown")
    assert "质量与文献证据链审计报告" in report_md
    assert "Это тестовое предложение" in report_md
    assert "ИИ-шаблоны" in report_md
    assert "8.5" in report_md
    assert "80.0%" in report_md # predictability risk 80.0 -> 80%

    # Test JSON Export
    report_json_str = export_report_data(diagnostics, format_type="json")
    import json
    report_json = json.loads(report_json_str)
    assert "diagnostics" in report_json
    assert report_json["overall_summary"]["flagged_count"] == 2

def test_mcp_retrieve_evidence():
    import asyncio
    from mcp_server.server import retrieve_evidence
    
    async def run():
        session_id = "test_mcp_sess"
        session_references[session_id] = {
            "bibtex": {
                "smith2020": {
                    "title": "Robotics Navigation",
                    "author": "Smith, J.",
                    "year": "2020"
                }
            },
            "corpus": {},
            "retrievers": {},
            "online_cache": {},
            "bib_mapping": {}
        }
        
        # Set up mock BM25 retriever for local search
        corpus_entries = [{"text": "Local snippet about control systems.", "metadata": {"key": "smith2020"}}]
        session_references[session_id]["retrievers"]["smith2020"] = BM25Retriever(corpus_entries)
        
        res = await retrieve_evidence(
            claim="Advanced control systems used in robotics navigation.",
            citation_key="smith2020",
            session_id=session_id
        )
        
        assert res["citation_key"] == "smith2020"
        assert res["title"] == "Robotics Navigation"
        assert res["source"] == "local"
        assert len(res["snippets"]) > 0
        assert "control systems" in res["snippets"][0]

    asyncio.run(run())

@patch("mcp_server.server.get_engines")
def test_mcp_suggest_revision(mock_get_engines):
    import asyncio
    from mcp_server.server import suggest_revision
    
    # Mock engines and LLM responses
    mock_engine = MagicMock()
    mock_judge = MagicMock()
    mock_cit_judge = MagicMock()
    mock_get_engines.return_value = (mock_engine, mock_judge, mock_cit_judge)
    
    mock_judge.diagnose_sentence.return_value = {
        "think": "Analysis shows too much passive voice.",
        "issues": [
            {
                "issue_type": "passive_voice",
                "severity": "medium",
                "explanation_zh": "句子中被动语态过多。",
                "rewrite_suggestion": "Решение предложено авторами."
            }
        ]
    }
    
    async def run():
        res = await suggest_revision(
            sentence="Решение было предложено со стороны авторов.",
            discipline="AUTOMATION_CONTROL",
            engine_type="hybrid-pro"
        )
        
        assert res["status"] == "flagged"
        assert res["issue_type"] == "passive_voice"
        assert "被动语态过多" in res["explanation"]
        assert res["rewrite_suggestion"] == "Решение предложено авторами."

    asyncio.run(run())

def test_mcp_stdio_jsonrpc():
    import sys
    import subprocess
    import json
    
    # Start the server as a subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp_server.server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # 1. Send initialize request
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "TestClient",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        
        # Read initialize response
        init_resp_line = proc.stdout.readline()
        init_resp = json.loads(init_resp_line)
        assert init_resp["id"] == 1
        assert "result" in init_resp
        
        # 2. Send notifications/initialized notification
        init_notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        proc.stdin.write(json.dumps(init_notif) + "\n")
        proc.stdin.flush()
        
        # 3. Send tools/list request
        list_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        proc.stdin.write(json.dumps(list_req) + "\n")
        proc.stdin.flush()
        
        # Read tools/list response
        list_resp_line = proc.stdout.readline()
        list_resp = json.loads(list_resp_line)
        
        assert list_resp["id"] == 2
        assert "result" in list_resp
        tools = list_resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        
        assert "thesis_analyze_manuscript" in tool_names
        assert "thesis_audit_citations" in tool_names
        assert "thesis_retrieve_evidence" in tool_names
        assert "thesis_suggest_revision" in tool_names
        assert "thesis_export_report" in tool_names
        assert "thesis_check_model_installed" in tool_names
        assert "thesis_download_model_tool" in tool_names
        assert "thesis_route_workflow" in tool_names
    finally:
        proc.terminate()
        proc.wait()

def test_mcp_check_model_installed():
    from mcp_server.server import check_model_installed
    from naturalization_layer.model_downloader import EXPECTED_SIZE
    
    # Case 1: Model does not exist
    with patch("os.path.exists", return_value=False):
        res = check_model_installed()
        assert res["installed"] is False
        assert res["size_bytes"] == 0
        assert "Please call 'download_model_tool'" in res["message"]
        
    # Case 2: Model exists but size is incorrect
    with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=12345):
        res = check_model_installed()
        assert res["installed"] is False
        assert res["size_bytes"] == 12345
        assert "incorrect size" in res["message"]
        
    # Case 3: Model exists and size is correct
    with patch("os.path.exists", return_value=True), patch("os.path.getsize", return_value=EXPECTED_SIZE):
        res = check_model_installed()
        assert res["installed"] is True
        assert res["size_bytes"] == EXPECTED_SIZE
        assert "installed and verified" in res["message"]

def test_mcp_download_model_tool():
    import asyncio
    from mcp_server.server import download_model_tool
    
    async def run_success():
        with patch("naturalization_layer.model_downloader.download_model") as mock_download:
            res = await download_model_tool()
            assert res["status"] == "success"
            assert "successfully" in res["message"]
            mock_download.assert_called_once()
            
    async def run_error():
        with patch("naturalization_layer.model_downloader.download_model", side_effect=Exception("Connection timed out")):
            res = await download_model_tool()
            assert res["status"] == "error"
            assert "Connection timed out" in res["message"]
            
    asyncio.run(run_success())
    asyncio.run(run_error())

def test_mcp_get_engines_missing_model_error_message():
    from mcp_server.server import get_engines
    
    with patch("os.path.exists", return_value=False):
        with pytest.raises(ValueError) as exc_info:
            get_engines("local")
        error_msg = str(exc_info.value)
        assert "Local model not found" in error_msg
        assert "download_model_tool" in error_msg
        assert "python -c" in error_msg

def test_ppl_veto_logic():
    import asyncio
    from services.diagnostic_service import run_sentence_diagnose_batch
    
    # Mock engine_inst to return ppl=7.5 (which is < ppl_low 15.0)
    mock_engine = MagicMock()
    mock_engine.evaluate_sentence_ppl.return_value = (7.5, False)
    
    # Mock judge_inst to return empty issues (i.e. Passed)
    mock_judge = MagicMock()
    mock_judge.diagnose_sentence.return_value = {
        "think": "LLM thinks this sentence is normal",
        "issues": []
    }
    
    async def run():
        results = await run_sentence_diagnose_batch(
            text="В данной работе рассматривается оценка коэффициента сцепления.",
            session_id="test_veto_session",
            engine_type="local",
            api_key="",
            base_url="",
            discipline="UNIVERSAL",
            engine_inst=mock_engine,
            judge_inst=mock_judge,
            citation_judge=None
        )
        # Should be flagged because PPL is 7.5 < 15.0
        assert len(results) == 1
        res = results[0]
        assert res["status"] == "flagged"
        assert res["issue_type"] == "ai_generated_suspicion"
        assert "物理困惑度极低" in res["explanation"]
        assert "7.5" in res["explanation"]
        
    asyncio.run(run())

def test_mcp_e2e_references_flow():
    import asyncio
    import tempfile
    import os
    import shutil
    from mcp_server.server import register_references, audit_citations, export_report, clear_references, list_references
    from mcp_server.server import EngineType, ReportFormat
    
    # 1. Create a temporary folder and a text file named smith2020.txt
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "smith2020.txt")
    with open(tmp_path, "wb") as f:
        f.write(b"Deep learning model for navigation has high efficiency and robustness.")
        
    try:
        session_id = "test_mcp_e2e_session"
        bibtex = """
        @article{smith2020,
            title={Deep Learning Model},
            author={Smith, J.},
            year={2020}
        }
        """
        
        # 2. Register references (BibTeX and local file)
        async def run_register():
            res = await register_references(
                session_id=session_id,
                bibtex_text=bibtex,
                pdf_paths=[tmp_path]
            )
            assert res["status"] == "success"
            assert "smith2020" in res["bibtex_keys_added"]
            assert "smith2020" in res["pdf_keys_added"]
            
            # List references
            list_res = list_references(session_id)
            assert "smith2020" in list_res["bibtex_keys"]
            assert "smith2020" in list_res["pdf_keys"]
            
        asyncio.run(run_register())
        
        # 3. Perform citation audit on a text that cites [smith2020]
        # We mock get_engines to avoid loading the real model if not needed
        with patch("mcp_server.server.get_engines") as mock_get_engines:
            mock_engine = MagicMock()
            mock_judge = MagicMock()
            mock_cit_judge = MagicMock()
            mock_get_engines.return_value = (mock_engine, mock_judge, mock_cit_judge)
            
            # Mock NLI verification to support the claim
            mock_cit_judge.verify_citation.return_value = {
                "think": "NLI support match",
                "status": "SUPPORTED",
                "explanation_zh": "证据完全支持主张",
                "evidence_snippet": "has high efficiency and robustness"
            }
            
            text_to_audit = f"Это тестовое предложение. [smith2020] говорит о высокой эффективности.\n\nСписок литературы:\n[smith2020] Smith, J. Deep Learning Model. 2020."
            
            async def run_audit():
                audit_res = await audit_citations(
                    text=text_to_audit,
                    session_id=session_id,
                    engine_type=EngineType.local
                )
                assert len(audit_res["integrity_warnings"]) == 0
                assert len(audit_res["sentence_citation_audits"]) > 0
                
                # Check NLI results
                audits = audit_res["sentence_citation_audits"][0]["audits"]
                assert audits[0]["status"] == "SUPPORTED"
                assert audits[0]["key"] == "smith2020"
                
                # 4. Export report in JSON format and Markdown format
                report_md = export_report(
                    diagnostics=[{
                        "index": 0,
                        "text": "Это тестовое предложение.",
                        "status": "flagged",
                        "issue_type": "ai_cliche",
                        "severity": "medium",
                        "explanation": "Обнаружены шаблоны.",
                        "suggestion": "Изменить.",
                        "predictability_risk": 20.0,
                        "uniformity_risk": 30.0,
                        "translationese_risk": 15.0,
                        "redundancy_risk": 10.0,
                        "citation_audit": audits
                    }],
                    citations=audits,
                    format=ReportFormat.markdown
                )
                assert "质量与文献证据链审计报告" in report_md
                assert "smith2020" in report_md
                assert "20.0%" in report_md # verify that risk values do not multiply by 100
                
            asyncio.run(run_audit())
            
            # 5. Clear references
            clear_res = clear_references(session_id)
            assert clear_res["status"] == "success"
            list_res = list_references(session_id)
            assert len(list_res["bibtex_keys"]) == 0
            assert len(list_res["pdf_keys"]) == 0
            
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)

def test_mcp_route_workflow():
    import asyncio
    from mcp_server.server import thesis_route_workflow
    
    async def run():
        # Case 1: Citation audit routing
        res = await thesis_route_workflow("Please check if references [1] and [2] in my paper are consistent and verify them using NLI")
        assert res["findings"]["workflow"] == "citation_audit"
        assert "thesis_audit_citations" in res["next_actions"]
        
        # Case 2: Literature review / Landscape routing
        res2 = await thesis_route_workflow("I want to search for similar dissertations from eLIBRARY or Zotero and construct a landscape report")
        assert res2["findings"]["workflow"] == "literature_landscape"
        assert "thesis_register_references" in res2["next_actions"]
        
        # Case 3: Structure planning routing
        res3 = await thesis_route_workflow("Help me draft an outline and plan the methodology chapters for my VAK thesis")
        assert res3["findings"]["workflow"] == "planning_and_structure"
        assert "thesis_map_vak_specialty" in res3["next_actions"]
        
        # Case 4: Polishing routing
        res4 = await thesis_route_workflow("Polish this sentence: В работе рассматривается метод управления...")
        assert res4["findings"]["workflow"] == "polishing_and_style"
        assert "thesis_analyze_manuscript" in res4["next_actions"]
        
    asyncio.run(run())

def test_mcp_map_vak_specialty():
    import asyncio
    from mcp_server.server import thesis_map_vak_specialty
    
    async def run():
        res = await thesis_map_vak_specialty(
            topic="Системный анализ и управление обработкой информации",
            abstract="В данной работе разрабатываются новые методы системного анализа алгоритмов принятия решений.",
            keywords="системный анализ, управление"
        )
        assert res["findings"]["code"] == "2.3.1"
        assert "confidence" in res["findings"]
        assert len(res["findings"]["gost_structure"]) > 0
        assert "thesis_analyze_manuscript" in res["next_actions"]
        
    asyncio.run(run())

def test_mcp_granular_citation_tools():
    import asyncio
    from mcp_server.server import (
        thesis_extract_claims,
        thesis_classify_evidence_need,
        thesis_bind_evidence,
        thesis_judge_claim_evidence_nli
    )
    
    async def run():
        # 1. Extract claims
        text = "Это тестовое предложение. В работе предложен новый метод [1]. Актуальность темы очевидна."
        res_extract = thesis_extract_claims(text)
        assert len(res_extract["findings"]) == 3
        assert res_extract["findings"][1]["claim_type"] == "cited_assertion"
        assert res_extract["findings"][1]["citation_keys"] == ["1"]
        
        # 2. Classify evidence need
        res_need1 = thesis_classify_evidence_need("В работе предложен новый метод")
        assert res_need1["findings"]["need_level"] == "medium"
        
        res_need2 = thesis_classify_evidence_need("Актуальность темы очевидна")
        assert res_need2["findings"]["need_level"] == "low"
        
        # 3. Bind evidence (using a session without references, should bind empty but succeed)
        res_bind = await thesis_bind_evidence(
            claim="В работе предложен новый метод",
            references=["1"],
            session_id="test_session_granular"
        )
        assert len(res_bind["findings"]) == 1
        assert res_bind["findings"][0]["citation_key"] == "1"
        assert res_bind["findings"][0]["source"] == "unknown"
        
        # 4. Judge NLI (mocked or empty snippets fallback)
        res_nli = await thesis_judge_claim_evidence_nli(
            claim="В работе предложен новый метод",
            snippets=[]
        )
        assert res_nli["findings"]["status"] == "NOT_ENOUGH_INFO"
        
    asyncio.run(run())

@patch("mcp_server.server.get_engines")
def test_mcp_audit_vak_gost_compliance(mock_get_engines):
    import asyncio
    from mcp_server.server import thesis_audit_vak_gost_compliance
    
    # Force get_engines to return None to prevent actual local model load in tests
    mock_get_engines.return_value = (None, None, None)
    
    async def run():
        # Introduction with some missing VAK headers
        manuscript = """
        Введение
        Актуальность темы исследования обусловлена необходимостью автоматизации.
        Научная новизна результатов заключается в разработке новых алгоритмов.
        Положения, выносимые на защиту:
        1. Метод управления...
        Список литературы
        [1] Иванов И.И. Алгоритмы оптимизации // Вестник компьютерных технологий. 2022. Т. 5, № 2. С. 10–15.
        [2] Петров П.П. Моделирование систем.
        """
        
        res = await thesis_audit_vak_gost_compliance(
            manuscript=manuscript,
            vak_code="2.3.1"
        )
        
        findings = res["findings"]
        # Relevance is present
        assert findings["vak_structure_audit"]["relevance"]["status"] == "passed"
        # Goal/tasks is missing
        assert findings["vak_structure_audit"]["goal_tasks"]["status"] == "missing"
        assert "研究目标与任务 (Цель и задачи)" in findings["missing_vak_headers"]
        
        # Bibliography GOST score audit
        assert len(findings["bibliography_gost_audit"]) == 2
        # First one is correct (score 100), second one is missing elements (score 50)
        assert findings["bibliography_gost_audit"][0]["score"] == 100
        assert findings["bibliography_gost_audit"][1]["score"] == 50
        assert findings["average_gost_score"] == 75.0
        
        # Citation integrity
        assert findings["citation_integrity"]["has_bibliography"] is True
        
        # VAK code requirements
        assert findings["vak_code_requirements"]["vak_code"] == "2.3.1"
        assert findings["vak_code_requirements"]["min_publications"] == 3
        assert "3" in findings["vak_code_requirements"]["publication_warning"]
        
    asyncio.run(run())





