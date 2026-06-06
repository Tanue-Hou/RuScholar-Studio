import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llama_cpp import Llama
import numpy as np

MODEL_PATH = "models/Qwen3-4B-Q5_K_M.gguf"
if not os.path.exists(MODEL_PATH):
    print("Model file not found. Skipping validation.")
    sys.exit(0)

print("Loading model...")
llm = Llama(model_path=MODEL_PATH, n_gpu_layers=-1, n_ctx=2048, logits_all=True, verbose=False)

sentence = "Это тестовое предложение."
tokens = llm.tokenize(sentence.encode("utf-8"), add_bos=True)
print(f"Tokens: {tokens} (Count: {len(tokens)})")

llm.reset()
llm.eval(tokens)

scores = llm._scores
print(f"Scores type: {type(scores)}")
if hasattr(scores, "shape"):
    print(f"Scores shape: {scores.shape}")
else:
    # In older llama-cpp versions, it might not be a numpy array or might have different shape
    print(f"Scores dir: {dir(scores)}")

# Let's inspect rows
n_tokens = len(tokens)
print("Inspecting logits at different positions:")
for i in range(min(5, n_tokens)):
    row = scores[i, :]
    print(f"Row {i} - min: {np.min(row):.4f}, max: {np.max(row):.4f}, argmax: {np.argmax(row)}")
