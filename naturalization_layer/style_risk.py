import math

def calculate_style_risks(ppl_vals: list, flagged_count: int, total_sentences: int, calibration: dict = None) -> tuple[float, float]:
    """
    Calculate Predictability and Uniformity Risk percentages.
    
    1. Predictability Risk: based on proportion of sentences with PPL below low threshold.
    2. Uniformity Risk: based on standard deviation of PPLs. Flat rhythm (low std dev) flags high risk.
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
    if len(ppl_evaluated) > 1:
        mean_ppl = sum(ppl_evaluated) / len(ppl_evaluated)
        variance = sum((p - mean_ppl) ** 2 for p in ppl_evaluated) / len(ppl_evaluated)
        std_dev = math.sqrt(variance)
        # Scale: std_dev close to 0 -> high risk (100%), std_dev >= 30 -> low risk (0%)
        uniformity_risk = round(max(0.0, min(100.0, (30.0 - std_dev) * 4.0)), 1)
    else:
        uniformity_risk = 0.0
        
    return predictability_risk, uniformity_risk
