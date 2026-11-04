from backend.main import app


def _methods(path):
    return {m for r in app.routes if getattr(r, "path", None) == path for m in r.methods}


def test_download_model_is_post_only():
    # A GET would let any web page start a multi-GB download via <img>/<script>.
    assert _methods("/api/download_model") == {"POST"}


def test_cors_is_not_wildcard():
    cors = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"][0]
    assert "*" not in cors.kwargs["allow_origins"]


def test_upload_size_limit(monkeypatch):
    from fastapi.testclient import TestClient
    import backend.main as m
    from services.settings import Settings
    monkeypatch.setattr(m, "settings", Settings(max_upload_bytes=10))
    c = TestClient(m.app)
    assert c.post("/api/upload", files={"file": ("a.txt", b"x" * 10)}).status_code == 200
    assert c.post("/api/upload", files={"file": ("a.txt", b"x" * 11)}).status_code == 413
    r = c.post("/api/upload_references", data={"session_id": "s"}, files=[("files", ("b.txt", b"x" * 11))])
    assert r.status_code == 413


def test_placeholder_routes_removed():
    from backend.main import app
    paths = {getattr(r, "path", None) for r in app.routes}
    assert not paths & {"/api/polish", "/api/references", "/api/format", "/api/structure"}


def test_local_nli_without_model_does_not_call_llm():
    from naturalization_layer.nli_judge import NLICitationJudge
    res = NLICitationJudge(None).verify_citation("claim", ["snippet"], "local")
    assert res["status"] == "AUDIT_FAILED" and "本地模型" in res["explanation_zh"]
