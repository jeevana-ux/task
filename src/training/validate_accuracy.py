import sys
import os
import json
from pathlib import Path
import dspy
from dspy.evaluate import Evaluate
from dspy.teleprompt import LabeledFewShot

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.config import Config
from src.utils.dataset_loader import load_dataset
from src.dspy_modules.signatures import SchemeExtractionSignature
# Use the clean metrics we verified
from src.training.metrics import validate_extraction, get_str, normalize_date, normalize_scheme_type, normalize_scheme_subtype, normalize_na, normalize_duration

def validate_only():
    """
    Load the optimized extractor and validate accuracy against val.json.
    """
    print("=== Validation Only (Fresh Start) ===")
    
    # 1. Setup LM
    try:
        lm = dspy.LM(
            model=Config.DEFAULT_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENROUTER_BASE_URL,
            max_tokens=4000
        )
    except AttributeError:
        lm = dspy.OpenAI(
            model=Config.DEFAULT_MODEL,
            api_key=Config.OPENROUTER_API_KEY,
            api_base=Config.OPENROUTER_BASE_URL,
            max_tokens=Config.MAX_TOKENS
        )
    dspy.configure(lm=lm)
    
    # 2. Load Validation Data
    val_file = project_root / "train" / "val.json"
    if not val_file.exists():
        print(f"[ERROR] Validation file not found: {val_file}")
        return

    print(f"Loading validation data from: {val_file}")
    valset = load_dataset(str(val_file))
    print(f"Loaded {len(valset)} validation examples.")
    
    if not valset:
        print("[ERROR] Validation set is empty.")
        return

    # 3. Load Optimized Module
    optimized_path = project_root / "src" / "dspy_modules" / "optimized_extractor.json"
    if not optimized_path.exists():
         print(f"[ERROR] Optimized module not found at {optimized_path}")
         return

    print(f"Loading optimized module from: {optimized_path}")
    
    with open(optimized_path, 'r', encoding='utf-8') as f:
        saved_state = json.load(f)
    
    demos_raw = saved_state.get('predict', {}).get('demos', [])
    
    compiled_program = None
    if demos_raw:
        demos = []
        for d in demos_raw:
            ex = dspy.Example(**d).with_inputs("email_text", "table_data", "xlsx_data")
            demos.append(ex)
            
        print(f"Found {len(demos)} few-shot demos in saved file.")
        
        student = dspy.ChainOfThought(SchemeExtractionSignature)
        optimizer = LabeledFewShot(k=len(demos))
        compiled_program = optimizer.compile(student, trainset=demos)
    else:
        print("Using Zero-Shot (No demos found).")
        compiled_program = dspy.ChainOfThought(SchemeExtractionSignature)

    # 4. Evaluate
    print("\n--- Starting Evaluation (This may take a few minutes) ---")
    
    # We disable display_progress to avoid Unicode errors on Windows
    evaluator = Evaluate(
        devset=valset, 
        metric=validate_extraction, 
        num_threads=1, 
        display_progress=False, 
        display_table=True
    )
    
    # Safe execution
    score_obj = 0.0
    try:
        score_obj = evaluator(compiled_program)
        
        # dspy.Evaluate returns object or float depending on version/config
        final_score = 0.0
        if hasattr(score_obj, 'score'):
             final_score = float(score_obj.score) # usually 0-100
        elif isinstance(score_obj, (float, int)):
             final_score = float(score_obj)
        else:
             # Try treating it as float convertible
             try: final_score = float(score_obj)
             except: str(score_obj)

        print(f"\n[RESULT] Validation Score: {final_score}")
        if final_score > 1.0:
            print("         (Note: DSPy likely reports this as a percentage 0-100)")
            
    except Exception as e:
        print(f"\n[ERROR] Evaluation failed: {e}")

    # 5. Diagnostics (Detailed Breakdown)
    print("\n\n=== DIAGNOSTICS: Mismatch Analysis (First 3 Examples) ===")
    
    for i, example in enumerate(valset[:3]):
        print(f"\n--- Example #{i+1} ---")
        
        # FIX: Pass arguments as KEYWORD arguments
        pred = compiled_program(
            email_text=example.email_text, 
            table_data=example.table_data, 
            xlsx_data=example.xlsx_data
        )
        
        fields_to_check = [
            'scheme_type', 'scheme_subtype', 'vendor_name', 
            'duration', 'start_date', 'end_date', 'brand_support_absolute'
        ]
        
        has_mismatch = False
        for field in fields_to_check:
            # Normalize using the same logic as the metric
            expected = get_str(example, field)
            actual = get_str(pred, field)
            
            # Additional normalization for display check
            if field == 'scheme_type':
                expected = normalize_scheme_type(expected)
                actual = normalize_scheme_type(actual)
            elif field == 'scheme_subtype':
                 expected = normalize_scheme_subtype(expected)
                 actual = normalize_scheme_subtype(actual)
            elif field in ['start_date', 'end_date']:
                expected = normalize_date(expected)
                actual = normalize_date(actual)
            elif field == 'duration':
                expected = normalize_duration(expected)
                actual = normalize_duration(actual)
            else:
                # Default N/A check for other fields
                expected = normalize_na(expected)
                actual = normalize_na(actual)
            
            if expected != actual:
                print(f"   [MISMATCH] {field}")
                print(f"      Expected: '{expected}'")
                print(f"      Actual:   '{actual}'")
                has_mismatch = True
        
        if not has_mismatch:
             print("   [PERFECT MATCH] All key fields matched.")
             
        # Print Metric Score for this item
        item_score = validate_extraction(example, pred)
        print(f"   Item Metric Score: {item_score:.2f} / 1.0")

if __name__ == "__main__":
    validate_only()
