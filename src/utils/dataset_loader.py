import json
import os
import dspy
from typing import List

def load_dataset(json_file_path: str) -> List[dspy.Example]:
    """
    Loads a dataset from a JSON file where input text can be referenced from external files.
    
    Expected JSON structure:
    [
      {
        "input_file": "inputs/doc_001.txt",  # Relative to the JSON file
        "labels": { ... }
      },
      ...
    ]
    """
    base_dir = os.path.dirname(json_file_path)
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    examples = []
    for item in data:
        # 1. Resolve Input Text (Email Text)
        email_text = ""
        
        # Check for input_file key first
        input_ref = item.get("input_file") or item.get("input", "")
        
        # If the input reference looks like a file path, read its contents
        if input_ref and (input_ref.endswith('.txt') or input_ref.endswith('.md')):
            # Path is relative to the JSON file location
            file_path = os.path.join(base_dir, input_ref)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as tf:
                    email_text = tf.read().strip()
                    print(f"[OK] Loaded content from: {input_ref} ({len(email_text)} chars)")
            else:
                print(f"⚠️ Warning: Input file not found: {file_path}")
                email_text = input_ref  # Fallback to the path string if file not found
        else:
            # Direct text content (not a file reference)
            email_text = input_ref
        
        # 2. Prepare Inputs (With Token Optimization)
        def truncate_context(text, max_lines=50):
            if not text: return text
            l = str(text).splitlines()
            if len(l) > max_lines:
                return "\n".join(l[:max_lines]) + "\n... [TRUNCATED]"
            return text

        inputs = {
            "email_text": truncate_context(email_text, max_lines=100), # Emails can be slightly longer
            "table_data": truncate_context(item.get("table_data", "No table data available"), max_lines=30),
            "xlsx_data": truncate_context(item.get("xlsx_data", "No XLSX data provided"), max_lines=30)
        }
        
        # 3. Prepare Labels
        raw_labels = item.get("labels", {})
        labels = {}
        
        # Mapping for messy CSV keys to DSPy fields
        key_map = {
            "Scheme Type": "scheme_type",
            "Sub Type": "scheme_subtype", 
            "Scheme Name": "scheme_name",
            "Description": "scheme_description",
            "Scheme Period": "scheme_period",
            "Duration": "duration",
            "DISCOUNT_TYPE": "discount_type",
            "BRAND_SUPPORT_ABSOLUTE": "brand_support_absolute",
            "GST Ratet": "gst_rate",
            "GST Rate": "gst_rate",
            
            # Fuzzy match keys (startswith checks might be better, but explicit map is safer if known)
            "Max Cap (ï¿½) / GLOBAL_CAP_AMOUNT": "max_cap",
            "Max Cap": "max_cap",
            "DISCOUNT_SLAB_TYPE (Applicable for Buyside-Periodic)": "discount_slab_type",
            "DISCOUNT_SLAB_TYPE": "discount_slab_type",
            "BEST_BET ( Applicable for Buyside-Periodic)": "best_bet",
            "BEST_BET": "best_bet",
            "Minimum of actual discount OR agreed claim (whichever is lower)": "min_actual_discount_or_agreed_claim",
            "FSN File / Config File (If Any) (YES/NO/O/P FILE)": "fsn_file_config_file",
            "Over & Above (If selected this will override duplicity check)": "over_and_above",
            "Remove GST from final claim amount": "remove_gst_from_final_claim",
            "Scheme Document attached (Yes/No)": "scheme_document",
            "Start Date": "start_date",
            "End Date": "end_date",
            "Vendor": "vendor_name",
            "Vendor Name": "vendor_name",
            "Price Drop Date": "price_drop_date"
        }

        for k, v in raw_labels.items():
            # Direct map
            if k in key_map:
                labels[key_map[k]] = v
                continue
            
            # Fuzzy fallback
            k_upper = k.upper()
            if "MAX CAP" in k_upper: labels["max_cap"] = v
            elif "SLAB" in k_upper: labels["discount_slab_type"] = v
            elif "BEST BET" in k_upper: labels["best_bet"] = v
            elif "MINIMUM OF ACTUAL" in k_upper: labels["min_actual_discount_or_agreed_claim"] = v
            elif "FSN" in k_upper or "CONFIG" in k_upper: labels["fsn_file_config_file"] = v
            elif "OVER & ABOVE" in k_upper: labels["over_and_above"] = v
            elif "GST" in k_upper and "REMOVE" in k_upper: labels["remove_gst_from_final_claim"] = v
            elif "DOCUMENT" in k_upper and "ATTACHED" in k_upper: labels["scheme_document"] = v
            elif "VENDOR" in k_upper: labels["vendor_name"] = v
            elif "PRICE DROP" in k_upper: labels["price_drop_date"] = v
            elif "START" in k_upper and "DATE" in k_upper: labels["start_date"] = v
            elif "END" in k_upper and "DATE" in k_upper: labels["end_date"] = v
            else:
                # Keep original if no map found (might match by chance or be irrelevant)
                # But normalize spaces to underscores just in case
                new_k = k.lower().replace(" ", "_")
                labels[new_k] = v

        # 4. Create DSPy Example
        # distinct inputs from labels using with_inputs
        example = dspy.Example(**inputs, **labels).with_inputs("email_text", "table_data", "xlsx_data")
        examples.append(example)
        
    return examples
