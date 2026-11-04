"""
Central runtime configuration.

Every environment variable the app reads is declared here, so there is one
place to look. `.env` in the project root is loaded on import (real environment
variables always win), so the values in `.env.example` actually take effect.
"""
import os
from dataclasses import dataclass, field

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv(path: str) -> None:
    """Minimal KEY=VALUE loader (no new dependency). Existing env vars are kept."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key.startswith("export "):
                key = key[len("export "):].strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            os.environ.setdefault(key, value)


if not os.getenv("RUSCHOLAR_SKIP_DOTENV"):
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def _abs(path: str) -> str:
    path = os.path.expanduser(path)
    return path if os.path.isabs(path) else os.path.join(PROJECT_ROOT, path)


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value not in (None, "") else default


@dataclass(frozen=True)
class Settings:
    # Rules and calibration resources
    rules_path: str = field(default_factory=lambda: _abs(_env(
        "RUSCHOLAR_RULES_PATH", "naturalization_layer/rules/polishing_rules_v5.json")))
    calibration_path: str = field(default_factory=lambda: _abs(_env(
        "RUSCHOLAR_CALIBRATION_PATH", "naturalization_layer/calibration/calibration_config.json")))

    # Optional cloud judge (OpenAI-compatible). Used when a request carries no key.
    deepseek_api_key: str = field(default_factory=lambda: _env("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = field(default_factory=lambda: _env("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
    cloud_timeout_seconds: float = field(default_factory=lambda: float(_env("RUSCHOLAR_CLOUD_TIMEOUT", "30")))

    # Web server
    host: str = field(default_factory=lambda: _env("RUSCHOLAR_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(_env("RUSCHOLAR_PORT", "8000")))
    cors_origins: tuple = field(default_factory=lambda: tuple(
        o.strip() for o in _env("RUSCHOLAR_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
        if o.strip()))

    # In-memory sessions (pending analyses and uploaded references) expire after this.
    session_ttl_seconds: int = field(default_factory=lambda: int(_env("RUSCHOLAR_SESSION_TTL", "7200")))

    def resolve_api_key(self, request_key: str) -> str:
        return (request_key or "").strip() or self.deepseek_api_key

    def resolve_base_url(self, request_url: str) -> str:
        return (request_url or "").strip() or self.deepseek_base_url


settings = Settings()
