try:
    from llama_cpp import Llama
except ImportError:
    Llama = None
import math
import os
from typing import Optional

import numpy as np


def sequence_nll(scores, tokens: list[int], n_tokens: int) -> float:
    """
    Total negative log-likelihood of tokens[1:n_tokens] given the logits rows
    scores[0:n_tokens-1] (row i predicts token i+1).

    Vectorised with numpy: one log-sum-exp per row instead of a Python loop
    over the whole vocabulary (~150k entries for Qwen3).
    """
    n_pred = n_tokens - 1
    logits = np.asarray(scores[:n_pred], dtype=np.float64)
    targets = np.asarray(tokens[1:n_tokens], dtype=np.int64)
    row_max = logits.max(axis=1)
    log_norm = row_max + np.log(np.exp(logits - row_max[:, None]).sum(axis=1))
    target_logits = logits[np.arange(n_pred), targets]
    return float(np.sum(log_norm - target_logits))


class PPLEngine:
    def __init__(self, model_path: str, n_gpu_layers: Optional[int] = None):
        if Llama is None:
            raise RuntimeError("llama-cpp-python is not installed. PPLEngine disabled.")
        if n_gpu_layers is None:
            n_gpu_layers = int(os.getenv("RUSCHOLAR_GPU_LAYERS", "-1"))

        # logits_all=True is required to evaluate existing prompt
        # n_ctx=3072 is necessary to prevent context overflow during styling diagnostics and NLI audits
        try:
            self.llm = Llama(model_path=model_path, n_gpu_layers=n_gpu_layers, n_ctx=3072, logits_all=True, verbose=False)
        except Exception:
            if n_gpu_layers == 0:
                raise
            self.llm = Llama(model_path=model_path, n_gpu_layers=0, n_ctx=3072, logits_all=True, verbose=False)

    def evaluate_sentence_ppl(
        self,
        sentence: str,
        early_exit_tokens: int = 0,
        early_exit_lower: float = 15.0,
        early_exit_upper: float = 80.0
    ) -> tuple[float, bool]:
        """
        Evaluate PPL of a sentence without generating new tokens.
        Supports early-exit based on the PPL of the first prefix tokens.
        Returns a tuple: (ppl, was_early_exited)
        """
        tokens = self.llm.tokenize(sentence.encode("utf-8"), add_bos=True)
        if len(tokens) <= 1:
            return 0.0, False

        # 1. Stage 1: Check prefix PPL if early exit is configured and sentence is long enough
        if early_exit_tokens > 0 and len(tokens) > early_exit_tokens + 1:
            k = early_exit_tokens + 1
            self.llm.reset()
            self.llm.eval(tokens[:k])

            prefix_ppl = math.exp(sequence_nll(self.llm._scores, tokens, k) / (k - 1))
            # Early exit ONLY if PPL is in the safe middle range.
            # Very low (< lower) = AI generated. Very high (> upper) = Bad translation.
            if early_exit_lower <= prefix_ppl <= early_exit_upper:
                return prefix_ppl, True

        # 2. Stage 2: Full evaluation (either early exit was disabled, sentence too short, or prefix was not natural enough)
        self.llm.reset()
        self.llm.eval(tokens)

        n = len(tokens)
        return math.exp(sequence_nll(self.llm._scores, tokens, n) / (n - 1)), False
