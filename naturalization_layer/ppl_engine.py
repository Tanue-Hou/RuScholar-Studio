from llama_cpp import Llama
import math
import os
from typing import Optional

class PPLEngine:
    def __init__(self, model_path: str, n_gpu_layers: Optional[int] = None):
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
            
            # Calculate prefix NLL
            nll = 0.0
            for i in range(k - 1):
                logits = self.llm._scores[i, :]
                max_logit = max(logits)
                exp_sum = sum(math.exp(l - max_logit) for l in logits)
                log_probs = [l - max_logit - math.log(exp_sum) for l in logits]
                
                target_token = tokens[i + 1]
                nll -= log_probs[target_token]
                
            prefix_ppl = math.exp(nll / (k - 1))
            # Early exit ONLY if PPL is in the safe middle range.
            # Very low (< lower) = AI generated. Very high (> upper) = Bad translation.
            if early_exit_lower <= prefix_ppl <= early_exit_upper:
                return prefix_ppl, True
                
        # 2. Stage 2: Full evaluation (either early exit was disabled, sentence too short, or prefix was not natural enough)
        self.llm.reset()
        self.llm.eval(tokens)
        
        # Calculate full NLL
        nll = 0.0
        for i in range(len(tokens) - 1):
            logits = self.llm._scores[i, :]
            # Simple softmax log prob for the next token
            max_logit = max(logits)
            exp_sum = sum(math.exp(l - max_logit) for l in logits)
            log_probs = [l - max_logit - math.log(exp_sum) for l in logits]
            
            target_token = tokens[i + 1]
            nll -= log_probs[target_token]
            
        return math.exp(nll / (len(tokens) - 1)), False
