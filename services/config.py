"""RuScholar 统一配置（RS-0002）。

- 在 services 包被导入时读取项目根目录的 `.env`（不需要额外依赖）；系统中已存在的环境变量优先。
- `.env` 中的相对路径一律按项目根目录解析，与启动时所在目录无关。
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PORT = 8000
MODEL_NAMES = ("Qwen3-8B-Q5_K_M.gguf", "Qwen3-4B-Q5_K_M.gguf")  # 优先 8B，退回 4B


def load_env_file(path=None, override=False):
    """读取 KEY=VALUE 格式的 .env；返回实际写入环境的键列表。"""
    path = path or os.path.join(PROJECT_ROOT, ".env")
    loaded = []
    if not os.path.isfile(path):
        return loaded
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):].strip()
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            elif " #" in value:
                value = value.split(" #", 1)[0].rstrip()
            if not key or (key in os.environ and not override):
                continue
            os.environ[key] = value
            loaded.append(key)
    return loaded


def resolve_path(value):
    """把配置中的路径解析为绝对路径：支持 ~，相对路径按项目根目录。"""
    value = os.path.expanduser(value)
    return value if os.path.isabs(value) else os.path.normpath(os.path.join(PROJECT_ROOT, value))


def model_search_dirs():
    """模型目录：项目自己的 models/，以及 PHD-Scholar 总项目的 data/models/。"""
    return [
        os.path.join(PROJECT_ROOT, "models"),
        os.path.normpath(os.path.join(PROJECT_ROOT, "..", "..", "data", "models")),
    ]


def resolve_model_path():
    env_path = os.getenv("RUSCHOLAR_MODEL_PATH")
    if env_path:
        return resolve_path(env_path)
    for name in MODEL_NAMES:
        for d in model_search_dirs():
            candidate = os.path.join(d, name)
            if os.path.exists(candidate):
                return candidate
    # 都不存在时，返回下载器的默认保存位置
    return os.path.join(PROJECT_ROOT, "models", MODEL_NAMES[0])


def rules_path():
    return resolve_path(os.getenv("RUSCHOLAR_RULES_PATH", "naturalization_layer/rules/polishing_rules_v5.json"))


def server_host():
    return os.getenv("RUSCHOLAR_HOST", "0.0.0.0")


def server_port():
    return int(os.getenv("RUSCHOLAR_PORT", str(DEFAULT_PORT)))
