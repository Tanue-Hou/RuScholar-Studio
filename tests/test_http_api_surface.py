"""RS-0011：HTTP/API 契约回归，不触发模型 lifespan 或模型下载。"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.mark.parametrize("path", ["/api/polish", "/api/references", "/api/format", "/api/structure"])
def test_placeholder_endpoints_are_not_advertised_or_callable(path):
    assert path not in app.openapi()["paths"]
    client = TestClient(app)  # 不启用 lifespan；仅测试路由层。
    response = client.post(path, params={"text": "public synthetic sample"})
    # 无静态构建时 404，根目录 StaticFiles 挂载后 POST 可返回 405；均不再是占位能力。
    assert response.status_code in (404, 405)


def test_existing_api_contract_is_preserved(tmp_path, monkeypatch):
    paths = app.openapi()["paths"]
    for path, method in [("/api/upload", "post"), ("/api/upload_references", "post"),
                         ("/api/detect_discipline", "post"), ("/api/session", "post"),
                         ("/api/diagnose", "get"), ("/api/check_model", "get"),
                         ("/api/download_model", "post")]:
        assert method in paths[path]
    monkeypatch.setattr("backend.main.registry._model_path", str(tmp_path / "absent.gguf"))
    response = TestClient(app).get("/api/check_model")
    assert response.status_code == 200
    assert response.json() == {"exists": False}
