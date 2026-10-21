"""RS-0002：统一配置（.env 读取、路径解析、模型查找、端口）。"""
import os

from services import config


def test_load_env_file_parses_and_respects_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text(
        "# 注释\n"
        "RS_TEST_A=hello\n"
        "export RS_TEST_B=\"quoted value\"\n"
        "RS_TEST_C=x # 行尾注释\n"
        "RS_TEST_KEEP=from_file\n"
        "not a pair\n",
        encoding="utf-8",
    )
    for k in ("RS_TEST_A", "RS_TEST_B", "RS_TEST_C"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("RS_TEST_KEEP", "from_env")
    loaded = config.load_env_file(str(env))
    assert os.environ["RS_TEST_A"] == "hello"
    assert os.environ["RS_TEST_B"] == "quoted value"
    assert os.environ["RS_TEST_C"] == "x"
    assert os.environ["RS_TEST_KEEP"] == "from_env"  # 已存在的环境变量优先
    assert "RS_TEST_KEEP" not in loaded


def test_missing_env_file_is_ignored(tmp_path):
    assert config.load_env_file(str(tmp_path / "nope.env")) == []


def test_relative_paths_resolve_against_project_root():
    assert config.resolve_path("models/x.gguf") == os.path.join(config.PROJECT_ROOT, "models", "x.gguf")
    assert config.resolve_path("/abs/x.gguf") == "/abs/x.gguf"


def test_model_env_relative_path(monkeypatch):
    monkeypatch.setenv("RUSCHOLAR_MODEL_PATH", "../../data/models/m.gguf")
    expected = os.path.normpath(os.path.join(config.PROJECT_ROOT, "..", "..", "data", "models", "m.gguf"))
    assert config.resolve_model_path() == expected


def test_model_search_prefers_8b_then_4b(tmp_path, monkeypatch):
    monkeypatch.delenv("RUSCHOLAR_MODEL_PATH", raising=False)
    project_models, shared_models = tmp_path / "models", tmp_path / "data_models"
    project_models.mkdir()
    shared_models.mkdir()
    monkeypatch.setattr(config, "model_search_dirs", lambda: [str(project_models), str(shared_models)])

    # 都没有：返回下载器默认位置（项目 models/ 下的 8B）
    assert config.resolve_model_path().endswith(os.path.join("models", "Qwen3-8B-Q5_K_M.gguf"))

    (project_models / "Qwen3-4B-Q5_K_M.gguf").write_text("4b")
    assert config.resolve_model_path() == str(project_models / "Qwen3-4B-Q5_K_M.gguf")

    (shared_models / "Qwen3-8B-Q5_K_M.gguf").write_text("8b")
    assert config.resolve_model_path() == str(shared_models / "Qwen3-8B-Q5_K_M.gguf")


def test_default_port_is_8000(monkeypatch):
    monkeypatch.delenv("RUSCHOLAR_PORT", raising=False)
    assert config.server_port() == 8000
    monkeypatch.setenv("RUSCHOLAR_PORT", "9001")
    assert config.server_port() == 9001
