"""
Process-wide owner of the local GGUF model and the judges built on it.

Replaces three hand-rolled lazy-loading blocks (backend/main.py diagnose and
detect_discipline endpoints, mcp_server/server.py get_engines).
"""
import asyncio
import logging
import os
import threading
from typing import Optional

from naturalization_layer.llm_judge import StyleJudge
from naturalization_layer.nli_judge import NLICitationJudge
from naturalization_layer.ppl_engine import PPLEngine
from services import shared_state

logger = logging.getLogger(__name__)


class ModelRegistry:
    def __init__(self, model_path: Optional[str] = None):
        self._model_path = model_path
        self._load_lock = threading.Lock()
        self._inference_lock = threading.RLock()
        self._engine = None
        self._load_error: Optional[str] = None
        self._style_judge = None
        self._citation_judge = None
        # Legacy async lock retained for import compatibility. New native calls
        # use run_local()/call_local() so cancellation cannot release a running worker.
        self.model_lock = shared_state.model_lock

    @property
    def model_path(self) -> str:
        return self._model_path or shared_state.MODEL_PATH

    def model_exists(self) -> bool:
        return os.path.exists(self.model_path)

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def get_engine(self) -> Optional[PPLEngine]:
        """Loaded PPLEngine, or None when the model file is missing or failed to load."""
        if self._engine is not None:
            return self._engine
        if not self.model_exists():
            return None
        if self._load_error is not None:
            # Don't retry a multi-GB load on every request; call reset() to retry.
            return None
        with self._load_lock:
            if self._engine is None and self._load_error is None:
                try:
                    self._engine = PPLEngine(self.model_path)
                    logger.info("Local model loaded from %s", self.model_path)
                except Exception as e:
                    self._load_error = str(e)
                    logger.warning("Local model unavailable (%s). Running in heuristics-only mode.", e)
        return self._engine

    def get_style_judge(self, engine_type: str) -> StyleJudge:
        """StyleJudge bound to the local LLM for engine_type == "local", else a cloud-only judge."""
        engine = self.get_engine() if engine_type == "local" else None
        if engine is not None:
            if self._style_judge is None:
                self._style_judge = StyleJudge(engine.llm)
            return self._style_judge
        return StyleJudge(None)

    def get_citation_judge(self) -> NLICitationJudge:
        engine = self.get_engine()
        if engine is None:
            return NLICitationJudge(None)
        if self._citation_judge is None:
            self._citation_judge = NLICitationJudge(engine.llm)
        return self._citation_judge

    def get_judges(self, engine_type: str):
        """(engine_or_None, style_judge, citation_judge) for one analysis run."""
        if engine_type.startswith("cloud"):
            return None, StyleJudge(None), NLICitationJudge(None)
        return self.get_engine(), self.get_style_judge(engine_type), self.get_citation_judge()

    def call_local(self, operation, *args, **kwargs):
        """Serialize a whole native operation in its worker thread.

        Cancelling an asyncio request cannot stop a llama.cpp worker. The lock
        stays held until that worker returns, including after a client disconnect.
        """
        with self._inference_lock:
            return operation(*args, **kwargs)

    async def run_local(self, operation, *args, **kwargs):
        return await asyncio.to_thread(self.call_local, operation, *args, **kwargs)

    def reset(self) -> None:
        """Drop the loaded model (e.g. after a download) so the next call reloads it."""
        with self._load_lock, self._inference_lock:
            self._engine = None
            self._load_error = None
            self._style_judge = None
            self._citation_judge = None


registry = ModelRegistry()
