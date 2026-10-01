import sys
import os
import time

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from naturalization_layer.ppl_engine import PPLEngine
from naturalization_layer.llm_judge import StyleJudge
from naturalization_layer.nli_judge import NLICitationJudge
from services.shared_state import MODEL_PATH

def main():
    print(f"=== [RuScholar Studio] Verifying 8B Model Upgrade ===")
    print(f"Resolved MODEL_PATH: {MODEL_PATH}")
    assert os.path.exists(MODEL_PATH), f"Model file not found at {MODEL_PATH}"
    
    file_size = os.path.getsize(MODEL_PATH)
    print(f"Model file size: {file_size} bytes ({file_size / (1024**3):.2f} GB)")
    
    # 1. Initialize PPLEngine
    print("\n[Step 1/4] Loading PPLEngine with Apple Silicon Metal acceleration...")
    t0 = time.time()
    engine = PPLEngine(MODEL_PATH)
    print(f"PPLEngine loaded in {time.time() - t0:.2f}s. Vocab size: {engine.llm.n_vocab()}")
    
    # 2. Test PPL evaluation on Russian academic text
    print("\n[Step 2/4] Testing Perplexity (PPL) calculation...")
    test_sentence = "В данной работе исследуются современные алгоритмы адаптивного управления динамическими системами."
    ppl, early_exit = engine.evaluate_sentence_ppl(test_sentence)
    print(f"Test sentence: '{test_sentence}'")
    print(f"Computed PPL: {ppl:.2f} (Early exit: {early_exit})")
    assert ppl > 0, "PPL calculation failed or returned non-positive value"
    
    # 3. Test Discipline Detection & Style Review
    print("\n[Step 3/4] Testing StyleJudge with local 8B model...")
    judge = StyleJudge(engine.llm)
    discipline = judge.detect_discipline("Математическая модель устойчивости робототехнических комплексов.", engine_type="local")
    print(f"Detected Discipline: {discipline}")
    assert discipline in ("AUTOMATION_CONTROL", "SCI_TECH", "UNIVERSAL"), f"Unexpected discipline: {discipline}"
    
    # 4. Test Citation NLI
    print("\n[Step 4/4] Testing NLICitationJudge with local 8B model...")
    nli = NLICitationJudge(engine.llm)
    audit = nli.verify_citation(
        sentence="Применение адаптивного ПИД-регулятора снижает время переходного процесса на 25%.",
        snippets=["Эксперименты показали, что адаптивный ПИД-регулятор сокращает время переходного процесса на 25-28%."],
        engine_type="local"
    )
    print(f"Citation Audit Result: {audit.get('status')} - {audit.get('explanation_zh')}")
    assert audit.get("status") in ("SUPPORTED", "CONTRADICTED", "NOT_ENOUGH_INFO"), "NLI audit failed"
    
    print("\n✅ All 8B model integration tests passed successfully!")

if __name__ == "__main__":
    main()
