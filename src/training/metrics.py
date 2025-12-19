"""
DSPy Evaluation Metrics for Retailer Hub
"""
import dspy
import re
from datetime import datetime

# --- Helper Functions ---

def get_str(obj, key):
    return str(getattr(obj, key, '')).strip().lower()

def normalize_date(date_str):
    if not date_str or date_str in ["not specified", "n/a", "none"]:
        return "n/a"
    
    # Try DD/MM/YYYY
    if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
        return date_str
        
    # Try parsing common formats
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y", "%B %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%d/%m/%Y")
        except:
            continue
            
    # Regex fallback to extract DD/MM/YYYY parts
    match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
    if match:
         d, m, y = match.groups()
         return f"{int(d):02d}/{int(m):02d}/{y}"
    return date_str

# --- Metric Function ---

# --- Normalization Helpers ---

def normalize_scheme_type(val):
    """Normalize scheme type to standard model outputs: BUY_SIDE, SELL_SIDE, OFC."""
    v = str(val).strip().upper()
    
    # BUY_SIDE variations
    if v in ['BUY_SIDE', 'BS', 'BS-PC', 'PDC-PDC', 'BUY SIDE']: return 'BUY_SIDE'
    
    # SELL_SIDE variations
    if v in ['SELL_SIDE', 'SS', 'SS-CP', 'SS-PUC', 'SS-PRX', 'SS-SC', 'SS-BOC', 'SS-LS', 'SELL SIDE']: return 'SELL_SIDE'
    
    # OFC variations
    if v in ['OFC', 'ONE_OFF', 'ONE OFF', 'OFC-OFC']: return 'OFC'
    
    return v.lower() # Fallback

def normalize_scheme_subtype(val):
    """Normalize subtype to standard codes: CP, PUC, PRX, SC, BOC, LS, PDC, PERIODIC_CLAIM, OFC."""
    v = str(val).strip().upper()
    
    # BUY_SIDE Subtypes
    if v in ['PERIODIC_CLAIM', 'BS-PC', 'PERIODIC CLAIM']: return 'PERIODIC_CLAIM'
    if v in ['PDC', 'PDC-PDC']: return 'PDC'
    
    # SELL_SIDE Subtypes
    if v in ['CP', 'COUPON', 'SS-CP', 'VPC']: return 'CP'
    if v in ['PUC', 'PUC_FDC', 'SS-PUC', 'PRICE MATCH']: return 'PUC'
    if v in ['PRX', 'PREXO', 'SS-PRX', 'EXCHANGE']: return 'PRX'
    if v in ['SC', 'SUPER_COIN', 'SS-SC', 'SUPER COIN']: return 'SC'
    if v in ['BOC', 'BANK OFFERS', 'SS-BOC', 'BANK OFFER']: return 'BOC'
    if v in ['LS', 'LIFESTYLE', 'SS-LS']: return 'LS'
    
    # OFC Subtypes
    if v in ['OFC', 'ONE_OFF', 'ONE OFF', 'OFC-OFC']: return 'OFC'
    
    return v.lower() # Fallback

# --- Metric Function ---

# --- Normalization Helpers ---

def normalize_scheme_type(val):
    """Normalize scheme type to standard model outputs: BUY_SIDE, SELL_SIDE, OFC."""
    v = str(val).strip().upper()
    
    # BUY_SIDE variations
    if v in ['BUY_SIDE', 'BS', 'BS-PC', 'PDC-PDC', 'BUY SIDE', 'PDC']: return 'BUY_SIDE'
    
    # SELL_SIDE variations
    if v in ['SELL_SIDE', 'SS', 'SS-CP', 'SS-PUC', 'SS-PRX', 'SS-SC', 'SS-BOC', 'SS-LS', 'SELL SIDE']: return 'SELL_SIDE'
    
    # OFC variations
    if v in ['OFC', 'ONE_OFF', 'ONE OFF', 'OFC-OFC']: return 'OFC'
    
    return v.lower() # Fallback

def normalize_scheme_subtype(val):
    """Normalize subtype to standard codes."""
    v = str(val).strip().upper()
    
    if v in ['PERIODIC_CLAIM', 'BS-PC', 'PERIODIC CLAIM', 'PC']: return 'PERIODIC_CLAIM'
    if v in ['PDC', 'PDC-PDC']: return 'PDC'
    if v in ['CP', 'COUPON', 'SS-CP', 'VPC']: return 'CP'
    if v in ['PUC', 'PUC_FDC', 'SS-PUC', 'PRICE MATCH']: return 'PUC'
    if v in ['PRX', 'PREXO', 'SS-PRX', 'EXCHANGE']: return 'PRX'
    if v in ['SC', 'SUPER_COIN', 'SS-SC', 'SUPER COIN']: return 'SC'
    if v in ['BOC', 'BANK OFFERS', 'SS-BOC', 'BANK OFFER']: return 'BOC'
    if v in ['LS', 'LIFESTYLE', 'SS-LS']: return 'LS'
    if v in ['OFC', 'ONE_OFF', 'ONE OFF', 'OFC-OFC']: return 'OFC'
    
    return v.lower()

def normalize_na(val):
    """Normalize 'Not Applicable' variations."""
    v = str(val).strip().lower()
    if v in ['not applicable', 'n/a', 'none', 'no', 'nofield', 'nan', '']:
        return 'not applicable'
    return v

def normalize_duration(val):
    """Normalize duration string format."""
    v = str(val).strip().lower()
    # Replace different separators with ' to '
    v = v.replace(' - ', ' to ').replace('-', ' to ')
    # Normalize 'to' spacing
    v = re.sub(r'\s+to\s+', ' to ', v)
    return v

# --- Metric Function ---

def validate_extraction(example, pred, trace=None):
    score = 0.0
    total_weight = 0.0
    
    # --- 1. Classification ---
    pred_type = normalize_scheme_type(get_str(pred, 'scheme_type'))
    ref_type = normalize_scheme_type(get_str(example, 'scheme_type'))
    
    if pred_type == ref_type:
        score += 3.0
    total_weight += 3.0
    
    pred_subtype = normalize_scheme_subtype(get_str(pred, 'scheme_subtype'))
    ref_subtype = normalize_scheme_subtype(get_str(example, 'scheme_subtype'))
    
    if pred_subtype == ref_subtype:
        score += 3.0
    total_weight += 3.0
    
    # --- 2. Structured Fields ---
    structured_fields = [
        'vendor_name', 'discount_type', 
        'max_cap', 'over_and_above', 'remove_gst_from_final_claim',
        'brand_support_absolute'
    ]
    # Special handling for duration
    if normalize_duration(get_str(pred, 'duration')) == normalize_duration(get_str(example, 'duration')):
         score += 1.0
    total_weight += 1.0

    # Fields that might have N/A logic
    for k in structured_fields:
        p = normalize_na(get_str(pred, k))
        e = normalize_na(get_str(example, k))
        if p == e:
            score += 1.0
        total_weight += 1.0
        
    for k in ['start_date', 'end_date']:
        val_pred = normalize_date(get_str(pred, k))
        val_ref = normalize_date(get_str(example, k))
        if val_pred == val_ref:
            score += 1.0
        total_weight += 1.0

    # --- 3. Creative Fields ---
    for k in ['scheme_name', 'scheme_description']:
        if len(get_str(pred, k)) > 3: 
            score += 0.5 
        total_weight += 0.5
        
    return score / total_weight if total_weight > 0 else 0
