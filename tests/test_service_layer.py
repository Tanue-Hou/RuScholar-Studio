"""Tests for the consolidated service layer (phase 2 of the architecture review)."""
import asyncio
import io
import json
from unittest.mock import MagicMock, patch

import pytest

from naturalization_layer.discipline import detect_discipline_by_keywords
from naturalization_layer.llm_client import (
    call_openai_compatible, clean_json_text, cloud_model_for, is_cloud_model, resolve_cloud_model,
)
from services.session_store import ExpiringDict
from services.settings import load_dotenv


# ---------- settings ----------

def test_load_dotenv_keeps_existing_env(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text('# comment\nRS_TEST_A=from_file\nexport RS_TEST_B="quoted"\nRS_TEST_C=\n', encoding="utf-8")
    monkeypatch.setenv("RS_TEST_A", "from_env")
    monkeypatch.delenv("RS_TEST_B", raising=False)
    load_dotenv(str(env))
    import os
    assert os.environ["RS_TEST_A"] == "from_env"
    assert os.environ["RS_TEST_B"] == "quoted"


# ---------- session store ----------

def test_expiring_dict_drops_idle_entries():
    now = [0.0]
    d = ExpiringDict(ttl_seconds=10, clock=lambda: now[0])
    d["old"] = 1
    now[0] = 5
    d["fresh"] = 2
    now[0] = 12
    _ = d["fresh"]          # reading refreshes the entry
    d["new"] = 3            # writes purge entries idle > ttl
    assert "old" not in d
    assert set(d) == {"fresh", "new"}


def test_expiring_dict_is_a_mapping():
    d = ExpiringDict(ttl_seconds=0)
    d.setdefault("a", {}).update(x=1)
    assert d.get("a") == {"x": 1} and d.get("missing") is None
    assert d.pop("a") == {"x": 1} and len(d) == 0


# ---------- llm client ----------

def test_engine_mappings():
    assert resolve_cloud_model("hybrid-pro") == "deepseek-v4-pro"
    assert resolve_cloud_model("cloud-flash") == "deepseek-flash"
    assert resolve_cloud_model("local") == "local"
    assert not is_cloud_model("local")
    assert cloud_model_for("hybrid-flash") == "deepseek-flash"
    assert cloud_model_for("cloud-pro") == "deepseek-v4-pro"


@pytest.mark.parametrize("raw, think, body", [
    ('<think>推理</think>\n{"a": 1}', "推理", '{"a": 1}'),
    ('推理</think>Вот JSON: {"a": 1} спасибо', "推理", '{"a": 1}'),
    ('<think>未闭合', "未闭合", "{}"),
    ('```json\n{"a": 1}\n```', "", '{"a": 1}'),
])
def test_clean_json_text(raw, think, body):
    assert clean_json_text(raw) == (think, body)


def test_cloud_call_falls_back_to_env_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://example.test/v1")
    captured = {}

    def fake_urlopen(req, timeout):
        captured["auth"] = req.headers["Authorization"]
        captured["url"] = req.full_url
        body = {"choices": [{"message": {"content": "{}", "reasoning_content": "r"}}]}
        return io.BytesIO(json.dumps(body).encode())

    with patch("urllib.request.urlopen", fake_urlopen):
        out = call_openai_compatible("deepseek-flash", "", "", "sys", "user")
    assert captured == {"auth": "Bearer env-key", "url": "https://example.test/v1/chat/completions"}
    assert out == "<think>r</think>\n{}"


def test_keyword_discipline_detection():
    assert detect_discipline_by_keywords("Синтез регулятора для робота") == "AUTOMATION_CONTROL"
    assert detect_discipline_by_keywords("Спортивная подготовка") == "ARTS_SPORTS"
    assert detect_discipline_by_keywords("Абстрактный текст") == "UNIVERSAL"


# ---------- model registry ----------

def test_registry_without_model_file(tmp_path):
    from services.model_registry import ModelRegistry
    reg = ModelRegistry(model_path=str(tmp_path / "missing.gguf"))
    engine, style, cit = reg.get_judges("local")
    assert engine is None and style.llm is None and cit.llm is None


def test_registry_caches_load_failure_until_reset(tmp_path):
    from services import model_registry
    model = tmp_path / "m.gguf"
    model.write_bytes(b"x")
    reg = model_registry.ModelRegistry(model_path=str(model))
    with patch.object(model_registry, "PPLEngine", side_effect=RuntimeError("boom")) as ctor:
        assert reg.get_engine() is None
        assert reg.get_engine() is None
        assert ctor.call_count == 1 and reg.load_error == "boom"
    fake = MagicMock()
    with patch.object(model_registry, "PPLEngine", return_value=fake):
        reg.reset()
        assert reg.get_engine() is fake
        assert reg.get_style_judge("local").llm is fake.llm
        assert reg.get_style_judge("cloud-pro").llm is None
        assert reg.get_citation_judge() is reg.get_citation_judge()


def test_mcp_get_engines_reports_load_failure(tmp_path):
    from mcp_server import server
    with patch.object(server.registry, "get_engine", return_value=None), \
         patch.object(server.registry, "model_exists", return_value=True), \
         patch.object(type(server.registry), "load_error", "bad file"):
        with pytest.raises(ValueError, match="failed to load: bad file"):
            server.get_engines("local")


# ---------- references ----------

def test_reference_ingestion_and_reset():
    from services import reference_service as rs
    sid = "test-ingest"
    rs.ingest_bibtex(sid, "@article{smith2020, title={Grip}, author={Smith}, year={2020}}")
    key = rs.ingest_reference_document(sid, "[Smith2020].txt", "Коэффициент сцепления зависит от температуры.".encode())
    assert key == "smith2020"
    assert rs.list_reference_keys(sid) == {"bibtex_keys": ["smith2020"], "pdf_keys": ["smith2020"]}
    assert rs.ingest_reference_text(sid, "empty.txt", "   ") is None
    assert rs.reset_reference_session(sid) is True
    assert rs.list_reference_keys(sid) == {"bibtex_keys": [], "pdf_keys": []}
    assert rs.reset_reference_session("never-created") is False


def test_resolve_reference_order_and_failure_cache():
    from services import citation_audit_service as cas
    from services.reference_service import ensure_reference_session, ingest_reference_text
    sid = "test-resolve"
    session = ensure_reference_session(sid)
    ingest_reference_text(sid, "local1.txt", "Температура влияет на сцепление шин.")
    session["bib_mapping"] = {"2": "Petrov P. Temperature effects. 2020.", "3": "Ivanov. Roads."}

    calls = []

    def fake_openalex(q):
        calls.append(q)
        return {"title": "Roads", "abstract": "About roads"} if "Ivanov" in q else None

    async def run():
        with patch.object(cas, "fetch_openalex_abstract", fake_openalex):
            local = await cas.resolve_reference(session, "local1", "температура")
            miss1 = await cas.resolve_reference(session, "2", "x")
            miss2 = await cas.resolve_reference(session, "2", "x")
            online = await cas.resolve_reference(session, "3", "x")
            nothing = await cas.resolve_reference(session, "99", "x")
        return local, miss1, miss2, online, nothing

    local, miss1, miss2, online, nothing = asyncio.run(run())
    assert local["source"] == "local" and local["snippets"]
    assert miss1["source"] == miss2["source"] == "unknown"
    assert calls.count("Petrov P. Temperature effects. 2020.") == 1  # failure cached
    assert online == {"title": "Roads", "author": "", "year": "", "snippets": ["About roads"], "source": "online"}
    assert nothing["snippets"] == [] and len(calls) == 2


# ---------- unified diagnostic pipeline ----------

class _Engine:
    llm = None

    def __init__(self, ppl):
        self.ppl = ppl
        self.calls = []

    def evaluate_sentence_ppl(self, s, ee_tokens, lo, hi):
        self.calls.append((ee_tokens, lo, hi))
        return self.ppl, bool(ee_tokens and lo <= self.ppl <= hi)


def _run(engine_type, engine, judge):
    from services.diagnostic_service import run_sentence_diagnose_batch
    return asyncio.run(run_sentence_diagnose_batch(
        "Студенты читают книгу.", "pipeline-test", engine_type, "", "", "UNIVERSAL", engine, judge, None
    ))


def test_local_mode_early_exit_skips_judge():
    judge = MagicMock()
    engine = _Engine(ppl=40.0)
    [res] = _run("local", engine, judge)
    assert res["status"] == "early_exit"
    judge.diagnose_sentence.assert_not_called()
    assert engine.calls[0][0] == 6


def test_hybrid_mode_uses_local_ppl_and_cloud_judge():
    judge = MagicMock()
    judge.diagnose_sentence.return_value = {"issues": [], "think": ""}
    engine = _Engine(ppl=40.123)
    [res] = _run("hybrid-flash", engine, judge)
    kwargs = judge.diagnose_sentence.call_args.kwargs
    assert kwargs["engine_type"] == "deepseek-flash" and kwargs["ppl"] == 40.12
    assert engine.calls == [(0, 0.0, float("inf"))]
    assert res["status"] == "passed" and res["ppl"] == 40.12


def test_cloud_mode_never_touches_local_model():
    judge = MagicMock()
    judge.diagnose_sentence.return_value = {
        "issues": [{"issue_type": "style_heavy", "severity": "medium", "explanation_zh": "e", "rewrite_suggestion": "r"}],
        "think": "t",
    }
    engine = _Engine(ppl=40.0)
    [res] = _run("cloud-pro", engine, judge)
    assert engine.calls == []
    assert judge.diagnose_sentence.call_args.kwargs["engine_type"] == "deepseek-v4-pro"
    assert res["status"] == "flagged" and res["ppl"] is None


def test_init_event_carries_discipline_calibration():
    from services.diagnostic_service import run_sentence_diagnose_stream
    from services.rules_config import get_calibration

    async def first_event():
        gen = run_sentence_diagnose_stream("Студенты читают книгу.", "calib-test", "cloud-pro", "", "",
                                           "AUTOMATION_CONTROL", None, MagicMock(), None)
        ev = await gen.__anext__()
        await gen.aclose()
        return ev

    ev = asyncio.run(first_event())
    data = json.loads(ev["data"])
    calib = get_calibration("AUTOMATION_CONTROL")
    assert ev["event"] == "init"
    assert data["calibration"]["ppl_low"] == calib.get("ppl_low", 15.0)
    assert data["calibration"]["nv_ratio_max"] == calib.get("nv_ratio_max", 4.5)


# ---------- RS-0020: data the UI relies on ----------

_BODY_AND_BIB = (
    "Важно отметить, что предложенная модель является новой и эффективной. "
    "Обеспечение координации распределения сил управления подсистем шасси осуществляется посредством реализации алгоритма. "
    "Студенты читают книгу каждый вечер в библиотеке университета. "
    "Результаты были получены и были проанализированы авторами. \n"
    "Список литературы\n1. Иванов И.И. Сцепление шин. М.: Наука, 2019.\n2. Petrov P. Dynamics. 2020.\n"
)


def _cloud_events(judge_side_effect):
    from naturalization_layer.llm_judge import StyleJudge
    from services.diagnostic_service import run_sentence_diagnose_stream

    async def run():
        out = []
        with patch("naturalization_layer.llm_judge.call_openai_compatible", side_effect=judge_side_effect), \
             patch("services.citation_audit_service.fetch_openalex_abstract", return_value=None):
            async for ev in run_sentence_diagnose_stream(_BODY_AND_BIB, "rs0020", "cloud-pro", "", "", "SCI_TECH",
                                                         None, StyleJudge(None), None):
                out.append((ev["event"], json.loads(ev["data"])))
        return out
    return asyncio.run(run())


def test_bibliography_is_marked_and_excluded_from_risks():
    multi = json.dumps({"issues": [
        {"issue_type": "machine_translation_cliche", "severity": "high", "explanation_zh": "a", "rewrite_suggestion": "x"},
    ]})
    events = _cloud_events(lambda *a, **k: multi)
    results = [d for e, d in events if e == "result" and d["index"] >= 0]
    body = [r for r in results if not r["is_bibliography"]]
    bib = [r for r in results if r["is_bibliography"]]
    assert len(body) == 4 and len(bib) >= 2
    done = [d for e, d in events if e == "done"][0]
    # All 4 body sentences are flagged; in cloud mode predictability falls back
    # to the flagged share, which must be over body sentences only (was 40%).
    assert done["predictability_risk"] == 100.0


def test_all_judge_issues_are_kept():
    multi = json.dumps({"issues": [
        {"issue_type": "machine_translation_cliche", "severity": "high", "explanation_zh": "a", "rewrite_suggestion": "x"},
        {"issue_type": "ai_generated_suspicion", "severity": "high", "explanation_zh": "b", "rewrite_suggestion": "y"},
    ]})
    events = _cloud_events(lambda *a, **k: multi)
    first = [d for e, d in events if e == "result" and d["index"] == 0][0]
    assert first["issue_type"] == "machine_translation_cliche"  # primary unchanged
    assert [i["issue_type"] for i in first["issues"]] == ["machine_translation_cliche", "ai_generated_suspicion"]


def test_judge_failure_is_marked_not_assessed():
    events = _cloud_events(RuntimeError("401 Unauthorized"))
    body = [d for e, d in events if e == "result" and d["index"] >= 0 and not d["is_bibliography"]]
    assert body and all(r["judge_error"] and r["status"] == "passed" and r["issues"] == [] for r in body)
    # Nothing was judged, so the flagged-share fallback has nothing to report.
    done = [d for e, d in events if e == "done"][0]
    assert done["predictability_risk"] == 0.0


def test_local_early_exit_ppl_is_marked_prefix():
    from services.diagnostic_service import run_sentence_diagnose_batch

    class Engine:
        llm = None
        def evaluate_sentence_ppl(self, s, ee_tokens, lo, hi):
            return 40.0, bool(ee_tokens)

    res = asyncio.run(run_sentence_diagnose_batch(
        "Студенты читают книгу.", "rs0020-ee", "local", "", "", "UNIVERSAL", Engine(), MagicMock(), None))
    assert res[0]["status"] == "early_exit" and res[0]["ppl_basis"] == "prefix"
