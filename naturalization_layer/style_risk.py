import math

def calculate_style_risks(
    ppl_vals: list, 
    flagged_count: int, 
    total_sentences: int, 
    calibration: dict = None,
    word_counts: list = None
) -> tuple[float, float]:
    """
    Calculate Predictability and Uniformity Risk percentages.
    
    1. Predictability Risk: based on proportion of sentences with PPL below low threshold.
       If PPLs are not available, falls back to the proportion of flagged sentences.
    2. Uniformity Risk: based on standard deviation of PPLs. Flat rhythm (low std dev) flags high risk.
       If PPLs are not available, falls back to analyzing the standard deviation of word counts.
    """
    if calibration is None:
        calibration = {"ppl_low": 15.0, "ppl_high": 80.0}
        
    ppl_low = calibration.get("ppl_low", 15.0)
    
    ppl_evaluated = [p for p in ppl_vals if p is not None]
    
    # 1. Predictability Risk
    if ppl_evaluated:
        pred_count = sum(1 for p in ppl_evaluated if p < ppl_low)
        predictability_risk = round((pred_count / len(ppl_evaluated)) * 100, 1)
    else:
        predictability_risk = round((flagged_count / max(1, total_sentences)) * 100, 1)
        
    # 2. Uniformity Risk
    if ppl_evaluated and len(ppl_evaluated) > 1:
        mean_ppl = sum(ppl_evaluated) / len(ppl_evaluated)
        variance = sum((p - mean_ppl) ** 2 for p in ppl_evaluated) / len(ppl_evaluated)
        std_dev = math.sqrt(variance)
        # Scale: std_dev close to 0 -> high risk (100%), std_dev >= 30 -> low risk (0%)
        uniformity_risk = round(max(0.0, min(100.0, (30.0 - std_dev) * 4.0)), 1)
    elif word_counts and len(word_counts) > 1:
        # Fallback: Analyze sentence length (word count) variation.
        # AI-generated content tends to have highly uniform sentence lengths (low variance).
        mean_wc = sum(word_counts) / len(word_counts)
        variance_wc = sum((w - mean_wc) ** 2 for w in word_counts) / len(word_counts)
        std_dev_wc = math.sqrt(variance_wc)
        # Scale: std_dev_wc <= 1.0 -> 100% risk, std_dev_wc >= 11.0 -> 0% risk.
        # Flat rhythm of sentence lengths indicates high uniformity risk.
        uniformity_risk = round(max(0.0, min(100.0, (11.0 - std_dev_wc) * 10.0)), 1)
    else:
        uniformity_risk = 0.0
        
    return predictability_risk, uniformity_risk

def calculate_redundancy_risk(
    cliche_counts: list, 
    genitive_chain_counts: list, 
    passive_counts: list,
    nv_ratios: list,
    connectors_counts: list = None
) -> float:
    """
    Calculate document-level Redundancy Risk percentage.
    Redundancy represents stylistic wordiness, noun-stacking, passive bloating, and cliches.
    """
    if not cliche_counts:
        return 0.0
        
    redundant_sentences = 0
    total = len(cliche_counts)
    
    if connectors_counts is None:
        connectors_counts = [0] * total
        
    for i in range(total):
        cliche = cliche_counts[i]
        gen = genitive_chain_counts[i]
        pas = passive_counts[i]
        nv = nv_ratios[i]
        conn = connectors_counts[i]
        
        # Weighted score for redundancy in this sentence
        score = 0.0
        if cliche > 0:
            score += 0.8
        if gen > 0:
            score += 0.3 * gen
        if pas > 1:
            score += 0.3
        if nv > 3.5:
            score += 0.3
        if conn > 1:
            score += 0.2
            
        if score >= 0.5:
            redundant_sentences += 1
            
    return round((redundant_sentences / total) * 100, 1)
