"""Benchmark PPL arithmetic on synthetic logits; does not load a GGUF model."""
import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

import numpy as np

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from naturalization_layer.ppl_engine import sequence_nll


def reference_nll(scores, tokens):
    nll = 0.0
    for i, token in enumerate(tokens[1:]):
        logits = scores[i]
        peak = max(logits)
        z = sum(math.exp(value - peak) for value in logits)
        nll += peak + math.log(z) - logits[token]
    return float(nll)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tokens", type=int, default=16)
    parser.add_argument("--vocab", type=int, default=150000)
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()
    if min(args.tokens - 1, args.vocab, args.repeats) < 1:
        parser.error("tokens >= 2, vocab >= 1, repeats >= 1 are required")
    rng = np.random.default_rng(0)
    scores = rng.normal(size=(args.tokens, args.vocab))
    tokens = rng.integers(args.vocab, size=args.tokens).tolist()
    timings = {}
    outputs = {}
    for name, function in [("reference", lambda: reference_nll(scores, tokens)),
                           ("vectorized", lambda: sequence_nll(scores, tokens, len(tokens)))]:
        elapsed = []
        for _ in range(args.repeats):
            start = time.perf_counter()
            outputs[name] = function()
            elapsed.append(time.perf_counter() - start)
        timings[name] = statistics.median(elapsed)
    tracemalloc.start()
    sequence_nll(scores, tokens, len(tokens))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    error = abs(outputs["reference"] - outputs["vectorized"])
    assert error < 1e-4, error
    print(json.dumps({"synthetic_only": True, **vars(args), "median_seconds": timings,
                      "speedup": timings["reference"] / timings["vectorized"],
                      "absolute_nll_error": error, "vectorized_peak_scratch_bytes": peak}, indent=2))


if __name__ == "__main__":
    main()
