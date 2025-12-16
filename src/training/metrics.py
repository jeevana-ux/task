"""
DSPy Evaluation Metrics for Retailer Hub
"""
import dspy

def validate_extraction(example, pred, trace=None):
    """
    Weighted metric to evaluate extraction quality.
    
    Weights:
    - 3.0: Classification (Scheme Type/Subtype) - CRITICAL
    - 1.0: Structured Data (Dates, Amounts, Vendor) - IMPORTANT
    - 0.5: Creative Content (Name, Description) - LENIENT (as requested)
    """
    score = 0.0
    total_weight = 0.0
    
    # Helper to safe get string normalized
    def get_str(obj, key):
        return str(getattr(obj, key, '')).strip().lower()

    # --- 1. Classification (High Weight) ---
    # These effectively determine the logic path
    if get_str(pred, 'scheme_type') == get_str(example, 'scheme_type'):
        score += 3.0
    total_weight += 3.0
    
    if get_str(pred, 'scheme_subtype') == get_str(example, 'scheme_subtype'):
        score += 3.0
    total_weight += 3.0
    
    # --- 2. Structured Fields (Medium Weight) ---
    # We check these strictly but less weight than classification
    structured_fields = [
        'vendor_name', 'duration', 'discount_type', 
        'max_cap', 'start_date', 'end_date',
        'over_and_above', 'remove_gst_from_final_claim'
    ]
    
    for k in structured_fields:
        if get_str(pred, k) == get_str(example, k):
            score += 1.0
        total_weight += 1.0

    # --- 3. Creative Fields (Low Weight) ---
    # As requested, these should not be heavily penalized for exact matches.
    # We essentially check if they exist and are non-empty.
    creative_fields = ['scheme_name', 'scheme_description']
    
    for k in creative_fields:
        pred_val = get_str(pred, k)
        # Pass if the model generated something substantial (>3 chars)
        # This allows the few-shot optimizer to learn FORMAT without being
        # rejected for slightly different wording.
        if len(pred_val) > 3: 
            score += 0.5 
        total_weight += 0.5
        
    return score / total_weight if total_weight > 0 else 0
