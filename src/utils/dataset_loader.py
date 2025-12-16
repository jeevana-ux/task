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
                    print(f"✓ Loaded content from: {input_ref} ({len(email_text)} chars)")
            else:
                print(f"⚠️ Warning: Input file not found: {file_path}")
                email_text = input_ref  # Fallback to the path string if file not found
        else:
            # Direct text content (not a file reference)
            email_text = input_ref
        
        # 2. Prepare Inputs
        # We ensure all inputs defined in the Signature are present
        inputs = {
            "email_text": email_text,
            "table_data": item.get("table_data", "No table data available"),
            "xlsx_data": item.get("xlsx_data", "No XLSX data provided")
        }
        
        # 3. Prepare Labels
        labels = item.get("labels", {})
        
        # 4. Create DSPy Example
        # distinct inputs from labels using with_inputs
        example = dspy.Example(**inputs, **labels).with_inputs("email_text", "table_data", "xlsx_data")
        examples.append(example)
        
    return examples
