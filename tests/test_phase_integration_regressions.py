"""RS-0016: regressions at the boundaries of Claude's three refactoring phases."""
import asyncio
import threading
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from services.model_registry import ModelRegistry
from services.session_store import ExpiringDict
from services.settings import Settings


@pytest.mark.parametrize("access", ["get", "contains", "iter", "len"])
def test_expired_sessions_cannot_be_revived_by_reading(access):
    now = [0.0]
    store = ExpiringDict(10, clock=lambda: now[0])
    store["expired"] = {"text": "synthetic"}
    now[0] = 11
    if access == "get":
        assert store.get("expired") is None
    elif access == "contains":
        assert "expired" not in store
    elif access == "iter":
        assert list(store) == []
    else:
        assert len(store) == 0


def test_local_inference_stays_serialized_after_request_cancellation():
    reg = ModelRegistry()
    entered, release = threading.Event(), threading.Event()
    second_entered = threading.Event()

    def first_call():
        entered.set()
        assert release.wait(5)

    async def scenario():
        first = asyncio.create_task(reg.run_local(first_call))
        try:
            assert await asyncio.to_thread(entered.wait, 2)
            first.cancel()
            with pytest.raises(asyncio.CancelledError):
                await first
            second = asyncio.create_task(reg.run_local(second_entered.set))
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(asyncio.shield(second), 0.05)
            assert not second_entered.is_set()
            release.set()
            await asyncio.wait_for(second, 2)
            assert second_entered.is_set()
        finally:
            release.set()
            if not first.done():
                await first

    asyncio.run(scenario())


def test_cloud_discipline_uses_configured_credentials_without_local_model(monkeypatch):
    import backend.main as web
    judge = MagicMock()
    judge.detect_discipline.return_value = "SCI_TECH"
    monkeypatch.setattr(web, "settings", Settings(deepseek_api_key="synthetic-env-key"))
    monkeypatch.setattr(web, "StyleJudge", lambda _: judge)
    monkeypatch.setattr(web.registry, "get_engine", lambda: pytest.fail("cloud classification loaded GGUF"))
    response = TestClient(web.app).post("/api/detect_discipline", json={
        "text": "Температура материала.", "engine_type": "cloud-pro",
    })
    assert response.json() == {"discipline": "SCI_TECH"}
    assert judge.detect_discipline.call_args.args[1:3] == ("deepseek-v4-pro", "synthetic-env-key")


def test_local_discipline_does_not_use_retained_cloud_key(monkeypatch):
    import backend.main as web
    judge = MagicMock()
    judge.detect_discipline.return_value = "AUTOMATION_CONTROL"
    monkeypatch.setattr(web.registry, "get_engine", lambda: object())
    monkeypatch.setattr(web.registry, "get_style_judge", lambda _: judge)
    monkeypatch.setattr(web, "StyleJudge", lambda _: pytest.fail("local classification selected a cloud judge"))
    response = TestClient(web.app).post("/api/detect_discipline", json={
        "text": "Управление роботом.", "engine_type": "local", "api_key": "retained-synthetic-key",
    })
    assert response.json() == {"discipline": "AUTOMATION_CONTROL"}
    assert judge.detect_discipline.call_args.args[1] == "local"


def test_cloud_judges_do_not_load_the_local_model(monkeypatch):
    reg = ModelRegistry()
    monkeypatch.setattr(reg, "get_engine", lambda: pytest.fail("pure cloud mode loaded GGUF"))
    engine, style, citation = reg.get_judges("cloud-pro")
    assert engine is None and style.llm is None and citation.llm is None


def test_diagnosis_session_is_claimed_before_streaming(monkeypatch):
    import backend.main as web
    monkeypatch.setattr(web, "pending_analyses", ExpiringDict(60))
    monkeypatch.setattr(web.registry, "get_judges", lambda _: (None, MagicMock(), None))

    async def scenario():
        created = await web.create_session(web.SessionRequest(text="synthetic", engine_type="cloud-pro"))
        sid = created["session_id"]
        await web.diagnose_stream(sid)
        duplicate = await web.diagnose_stream(sid)
        events = [event async for event in duplicate.body_iterator]
        assert events[0]["event"] == "error"
        assert "Session expired or not found" in events[0]["data"]

    asyncio.run(scenario())


def test_mcp_cloud_classification_uses_selected_engine_and_env_credentials(monkeypatch):
    from mcp_server import core
    judge = MagicMock()
    judge.detect_discipline.return_value = "SCI_TECH"
    monkeypatch.setattr(core, "settings", Settings(deepseek_api_key="synthetic-env-key"))
    monkeypatch.setattr(core.app, "get_engines", lambda _: (None, judge, None))

    async def batch(**kwargs):
        return [kwargs["discipline"]]

    monkeypatch.setattr(core, "run_sentence_diagnose_batch", batch)
    assert asyncio.run(core.analyze_manuscript("synthetic", engine_type="cloud-pro")) == ["SCI_TECH"]
    assert judge.detect_discipline.call_args.args[1:3] == ("deepseek-v4-pro", "synthetic-env-key")


def test_vak_cloud_json_with_shared_reasoning_prefix(monkeypatch):
    import json
    from naturalization_layer.llm_judge import StyleJudge
    from naturalization_layer.vak_specialty_mapper import load_vak_nomenclature, map_vak_specialty
    code = load_vak_nomenclature()[0]["code"]
    content = '<think>synthetic reasoning</think>' + json.dumps({"code": code, "confidence": 0.95})
    monkeypatch.setattr(StyleJudge, "_call_deepseek_api", lambda *args: content)
    result = asyncio.run(map_vak_specialty("synthetic", engine_type="cloud-pro", api_key="synthetic-key"))
    assert result["code"] == code and result["confidence"] == 0.95


def test_ppl_scratch_memory_is_bounded_and_scores_are_unchanged():
    import tracemalloc
    import numpy as np
    from naturalization_layer.ppl_engine import sequence_nll
    scores = np.zeros((256, 4096), dtype=np.float32)
    scores.flags.writeable = False
    tokens = [1] * 256
    tracemalloc.start()
    try:
        result = sequence_nll(scores, tokens, len(tokens))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert result == pytest.approx(255 * np.log(4096))
    assert np.count_nonzero(scores) == 0
    assert peak < 8 * 1024 * 1024
