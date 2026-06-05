from llama_cpp import Llama
import math

class PPLEngine:
    def __init__(self, model_path: str):
        # n_gpu_layers=-1 delegates all layers to Metal/CUDA
        # logits_all=True is required to evaluate existing prompt
        self.llm = Llama(model_path=model_path, n_gpu_layers=-1, logits_all=True, verbose=False)
        
    def evaluate_sentence_ppl(self, sentence: str) -> float:
        """
        Evaluate PPL of a sentence without generating new tokens.
        """
        tokens = self.llm.tokenize(sentence.encode("utf-8"), add_bos=True)
        if len(tokens) <= 1:
            return 0.0
            
        self.llm.reset()
        self.llm.eval(tokens)
        
        # Calculate NLL
        nll = 0.0
        for i in range(len(tokens) - 1):
            logits = self.llm._scores[i, :]
            # Simple softmax log prob for the next token
            max_logit = max(logits)
            exp_sum = sum(math.exp(l - max_logit) for l in logits)
            log_probs = [l - max_logit - math.log(exp_sum) for l in logits]
            
            target_token = tokens[i + 1]
            nll -= log_probs[target_token]
            
        return math.exp(nll / (len(tokens) - 1))
