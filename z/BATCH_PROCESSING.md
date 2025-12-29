# Batch Processing - Usage Guide

## Overview

The pipeline now processes **all PDFs in the input folder** and provides:
- Individual JSON outputs for each PDF
- Consolidated JSON with all results
- Complete LLM metrics (tokens, cost, timing)

## Usage

### Process All PDFs in a Folder
```bash
python main.py --input ./input_folder/
```

### Process Single PDF
```bash
python main.py --input sample.pdf
```

## Output Structure

```
outputs/
└── {timestamp}/
    ├── extracted/
    │   ├── file1_text.txt
    │   ├── file1_tables.csv
    │   ├── file2_text.txt
    │   └── file2_tables.csv
    ├── output_1_file1.json          # Individual result for file1
    ├── output_2_file2.json          # Individual result for file2
    ├── consolidated_output.json     # ⭐ ALL RESULTS + METRICS
    ├── llm_metrics.json             # ⭐ LLM METRICS ONLY
    └── processing.log
```

## Consolidated Output Format

```json
{
  "summary": {
    "total_files": 5,
    "successful": 5,
    "failed": 0,
    "model": "openai/gpt-4o",
    "processing_time_seconds": 145.23
  },
  "llm_metrics": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4567,
    "total_tokens": 19801,
    "total_cost_usd": 0.1234,
    "average_tokens_per_file": 3960.2,
    "average_cost_per_file": 0.0247
  },
  "per_file_metrics": [
    {
      "file": "vendor_email_1.pdf",
      "status": "success",
      "pages": 3,
      "tables_extracted": 2,
      "input_tokens": 3045,
      "output_tokens": 912,
      "total_tokens": 3957,
      "cost": 0.0245,
      "processing_time_seconds": 28.5,
      "output_file": "output_1_vendor_email_1.json"
    }
  ],
  "results": [
    {
      "source_file": "vendor_email_1.pdf",
      "extracted_fields": {
        "scheme_name": "Q4 Marketing Support",
        "scheme_description": "Quarterly sellout support program",
        ...
      },
      "metadata": {
        "pages": 3,
        "tables": 2,
        "processing_time": 28.5
      }
    }
  ]
}
```

## LLM Metrics Summary

Console output at the end:
```
============================================================
PROCESSING SUMMARY
============================================================
  Files Processed:  5/5
  Failed:           0
  Total Time:       145.23s

LLM METRICS:
  Model:            openai/gpt-4o
  Total Tokens:     19,801
  Input Tokens:     15,234
  Output Tokens:    4,567
  Total Cost:       $0.1234
  Avg Cost/File:    $0.0247
```

## Key Features

✅ **Batch Processing** - All PDFs in folder processed automatically  
✅ **Individual Outputs** - Each PDF gets its own output JSON  
✅ **Consolidated Results** - Single JSON with all extractions  
✅ **Complete Metrics** - Tokens, cost, timing per file and total  
✅ **Error Handling** - Failed files logged, processing continues  

## Example Workflow

```bash
# 1. Place all vendor PDFs in input_folder/
mkdir input_folder
cp vendor_email_*.pdf input_folder/

# 2. Run pipeline
python main.py --input input_folder/

# 3. Check results
cat outputs/071220252200/consolidated_output.json
cat outputs/071220252200/llm_metrics.json
```

Perfect for processing hundreds of vendor emails efficiently!
