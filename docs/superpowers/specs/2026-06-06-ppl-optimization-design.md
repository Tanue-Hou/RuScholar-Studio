# Design Spec: PPL Performance Optimization & Web UI Upgrades

**Date**: 2026-06-06  
**Status**: Approved (Brainstormed with User)  

## 1. Objective
Implement Phase P3 of the Russian Academic Naturalness Diagnostics Engine. Specifically:
- Optimize PPL computations using a configurable screening strategy with three user-selectable scanning modes: Heuristic, Early-Exit, and Hybrid.
- Refactor the Streamlit Web Application to use an interactive Apple-style dual-column layout with instant filter updates utilizing state caching.

---

## 2. Configurable Scanning Modes

Users can choose from three diagnostic performance modes in the Web UI:

### Mode 1: Heuristic Filter Only (仅启发式过滤)
- Skip PPL and LLM evaluation if a sentence is protected (formula/citation) or very short (< 6 words).
- User chooses a heuristic depth:
  - **Deep Scan (全量深检)**: Scan all remaining sentences.
  - **Smart Probe (均衡模式)**: Only scan if sentence has word count $\ge 12$ OR matches an AI cliché.
  - **Fast Check (极速模式)**: Only scan if sentence has word count $\ge 18$ OR matches an AI cliché.

### Mode 2: Early-Exit Probe Only (仅早期退出探针)
- Skip heuristic filtering (all non-protected, non-short sentences are entered).
- Run a 2-stage PPL evaluation:
  - **Stage 1**: Compute prefix PPL on the first 6 tokens (plus BOS, total 7 tokens).
  - If prefix $PPL \ge 30.0$ (highly natural, low predictability), mark as `Early Exit (Natural)` and skip the rest of the sentence.
  - **Stage 2**: Otherwise, compute full sentence PPL.

### Mode 3: Hybrid Probe (混合模式 - 默认且推荐)
- Apply **Heuristic Filter** first based on the chosen depth (Deep Scan, Smart Probe, or Fast Check).
- If a sentence passes the heuristic filter, run the **Early-Exit Probe** (Stage 1 prefix PPL check).
- Only run the full PPL and LLM Judge if both gates are passed.

---

## 3. Implementation Details

### 3.1 PPL Engine Upgrades
Update `PPLEngine.evaluate_sentence_ppl` to support early exiting:
```python
def evaluate_sentence_ppl(self, sentence: str, early_exit_tokens: int = 0, early_exit_threshold: float = 0.0) -> tuple[float, bool]:
    # Returns (ppl, was_early_exited)
```

### 3.2 Web UI Dual-Column Layout
- **Left Column (width 5)**: 
  - Scan controls (Upload draft, choose Scanning Mode, choose Heuristic Depth, Run Deep Analysis).
  - Diagnostic metric summaries.
  - Filtering controls (Filter by severity, filter by issue type, keyword search).
  - List of filterable diagnostic cards with clickable "Locate in Draft ↑" anchors linking to the right column.
- **Right Column (width 7)**:
  - Scrollable `div` styled as a sticky card containing the highlighted manuscript.
  - Highlighted sentences are color-coded by severity and contain clickable link anchors pointing to the left column cards.
- **State Caching**:
  - Store computed analysis results in `st.session_state["analysis_results"]`.
  - When filters are changed, re-render immediately using Python-level filters on the cached state without repeating any PPL or LLM Judge computations.

---

## 4. Verification Plan
- **Unit Tests**:
  - Add test cases in `tests/test_rules_engine.py` for helper functions.
  - Add test cases in `tests/test_llm_judge.py` or a new test file validating `PPLEngine`'s early exit logic.
- **Manual Verification**:
  - Run the Streamlit web app, upload a Russian draft, choose different modes and filters, and verify instant responsiveness.
