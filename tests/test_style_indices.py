import pytest
import math

def calculate_risks(ppl_vals, nv_ratios, passive_counts, genitive_chain_counts, cliche_counts, flagged_count, total_sentences):
    ppl_evaluated = [p for p in ppl_vals if p is not None]
    
    # 1. Predictability Risk
    if ppl_evaluated:
        pred_count = sum(1 for p in ppl_evaluated if p < 15.0)
        predictability_risk = round((pred_count / len(ppl_evaluated)) * 100, 1)
    else:
        predictability_risk = round((flagged_count / max(1, total_sentences)) * 100, 1)
        
    # 2. Uniformity Risk
    if len(ppl_evaluated) > 1:
        mean_ppl = sum(ppl_evaluated) / len(ppl_evaluated)
        variance = sum((p - mean_ppl) ** 2 for p in ppl_evaluated) / len(ppl_evaluated)
        std_dev = math.sqrt(variance)
        uniformity_risk = round(max(0.0, min(100.0, (30.0 - std_dev) * 4.0)), 1)
    else:
        uniformity_risk = 0.0
        
    # 3. Translationese Risk
    trans_scores = []
    for nv, pas, gen in zip(nv_ratios, passive_counts, genitive_chain_counts):
        nv_score = min(2.0, max(0.0, nv - 1.5)) / 2.0
        pas_score = min(1.0, pas * 0.5)
        gen_score = min(1.0, gen * 0.5)
        trans_scores.append((nv_score + pas_score + gen_score) / 3.0)
    
    translationese_risk = round((sum(trans_scores) / max(1, len(trans_scores))) * 100, 1)
    
    # 4. Redundancy Risk
    if cliche_counts:
        cliche_sent_count = sum(1 for c in cliche_counts if c > 0)
        redundancy_risk = round((cliche_sent_count / len(cliche_counts)) * 100, 1)
    else:
        redundancy_risk = 0.0
        
    return {
        "predictability_risk": predictability_risk,
        "uniformity_risk": uniformity_risk,
        "translationese_risk": translationese_risk,
        "redundancy_risk": redundancy_risk
    }

def test_style_risk_calculations():
    # Test case 1: High predictability (all PPL < 15) and low variance (uniform)
    res = calculate_risks(
        ppl_vals=[12.0, 11.5, 12.5],
        nv_ratios=[1.0, 1.2, 1.1],
        passive_counts=[0, 0, 0],
        genitive_chain_counts=[0, 0, 0],
        cliche_counts=[0, 0, 0],
        flagged_count=0,
        total_sentences=3
    )
    assert res["predictability_risk"] == 100.0
    # low std dev (around 0.4) means very high uniformity risk
    assert res["uniformity_risk"] > 90.0
    assert res["translationese_risk"] == 0.0
    assert res["redundancy_risk"] == 0.0

    # Test case 2: Normal PPL, high translationese and redundancy
    res2 = calculate_risks(
        ppl_vals=[45.0, 50.0, 48.0],
        nv_ratios=[3.5, 4.0, 3.8],
        passive_counts=[2, 1, 3],
        genitive_chain_counts=[1, 2, 2],
        cliche_counts=[1, 0, 1],
        flagged_count=1,
        total_sentences=3
    )
    assert res2["predictability_risk"] == 0.0
    assert res2["redundancy_risk"] == 66.7 # 2 out of 3 sentences have cliches
    assert res2["translationese_risk"] > 50.0
