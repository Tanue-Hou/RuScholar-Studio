"""RS-0004：本地与 CI 使用相同的无模型测试选择，不安装依赖。"""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "RUSCHOLAR_GPU_LAYERS": "0",
           "RUSCHOLAR_MODEL_PATH": str(Path(tempfile.gettempdir()) / "ruscholar-ci-no-model.gguf")}
    result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-m", "not local_model",
                             "-p", "no:cacheprovider", *sys.argv[1:]], cwd=root, env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
