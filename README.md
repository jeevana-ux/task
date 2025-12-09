# PDF Extraction & Retailer Hub Field Mapping System

An enterprise-level system for extracting vendor email data from PDFs and automatically mapping to Flipkart Retailer Hub fields using DSPy framework with Chain-of-Thought reasoning.

## Features

✅ **Multi-Format PDF Extraction**: Handles text-based and scanned PDFs using PyMuPDF, pdfplumber, and Tesseract OCR  
✅ **Table Consolidation**: Extracts all tables to a single CSV file  
✅ **Intelligent Text Cleaning**: Removes disclaimers, cautions, forwarded messages, and links using regex patterns  
✅ **DSPy Framework**: Chain-of-Thought reasoning for 21 Retailer Hub fields  
✅ **Enterprise Logging**: Field-level reasoning traces, token usage, cost tracking, model parameters  
✅ **Timestamp-based Output**: Folders named with `DDMMYYYYHHMM` convention  
✅ **XLSX Support**: Converts Excel files to text for processing  

## Architecture

```
pdf_extractor_2.0/
├── src/
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Enterprise logging system
│   ├── extractors/
│   │   ├── pdf_extractor.py      # Multi-library PDF text extraction
│   │   ├── table_extractor.py    # Table extraction to CSV
│   │   └── text_cleaner.py       # Regex-based content cleaning
│   ├── dspy_modules/
│   │   ├── signatures.py         # DSPy signature definitions
│   │   ├── field_extractor.py    # ChainOfThought field extraction
│   │   └── scheme_classifier.py  # Scheme type classification
│   └── utils/
│       ├── file_handler.py       # File I/O and folder management
│       └── token_tracker.py      # Token counting and cost calculation
├── main.py                       # CLI orchestration pipeline
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variable template
├── PROMPT_REFINED.md             # Refined LLM prompt document
└── README.md                     # This file
```

## Installation

### Prerequisites
- Python 3.9+
- Tesseract OCR installed ([Download](https://github.com/tesseract-ocr/tesseract))
- OpenRouter API Key

### Setup

1. **Clone or navigate to project directory**:
```bash
cd c:\Users\Admin\.gemini\antigravity\scratch\pdf_extractor_2.0
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Configure environment**:
```bash
# Create .env file from template
copy .env.example .env

# Edit .env and add your OpenRouter API key
# OPENROUTER_API_KEY=your_key_here
```

4. **Verify Tesseract installation**:
```bash
# Windows:
tesseract --version

# Set path in .env if not in system PATH
# TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## Usage

### Basic Usage

**Process a single PDF**:
```bash
python main.py --input sample.pdf
```

**Process a folder** (multiple PDFs and XLSX files):
```bash
python main.py --input ./vendor_emails/
```

**Specify output directory**:
```bash
python main.py --input sample.pdf --output ./results/
```

**Use a specific model**:
```bash
python main.py --input sample.pdf --model openai/gpt-4o-mini
```

### Advanced Options

```bash
python main.py --help

Options:
  --input PATH          Input PDF file or folder path (required)
  --output PATH         Output directory (default: ./outputs/)
  --model TEXT          OpenRouter model name (default: qwen/qwen-2.5-72b-instruct)
  --temperature FLOAT   LLM temperature 0.0-1.0 (default: 0.1)
  --max-tokens INT      Max output tokens (default: 4000)
  --verbose             Enable detailed logging to console
```

## Output Structure
```
outputs/
└── 071220252200/                 # Timestamp folder
    ├── extracted_output/         # Raw extracted artifacts
    │   └── vendor_email_1_071220252200/
    │       ├── vendor_email_1_raw.txt
    │       └── vendor_email_1_tables.csv
    │
    ├── cleaned_data/             # Filtered & cleaned text
    │   └── vendor_email_1_071220252200/
    │       └── vendor_email_1_cleaned.txt
    │
    ├── final_output/             # Final JSON results
    │   ├── vendor_email_1_output.json
    │   ├── consolidated_output.json
    │   └── llm_metrics.json
    │
    └── processing.log
```

### Sample Output JSON

```json
{
  "scheme_name": "Q4 Marketing Support Scheme",
  "scheme_description": "Quarterly marketing support for sellout activities",
  "scheme_period": "Duration",
  "duration": "01/10/2024 to 31/12/2024",
  "discount_type": "Percentage of NLC",
  "max_cap": "500000",
  "vendor_name": "Samsung India Electronics",
  "price_drop_date": "N/A",
  "start_date": "01/10/2024",
  "end_date": "31/12/2024",
  "fsn_file_config_file": "Yes",
  "min_actual_discount_or_agreed_claim": "TRUE",
  "remove_gst_from_final_claim": "Yes",
  "over_and_above": "FALSE",
  "discount_slab_type": "Not Applicable",
  "best_bet": "No",
  "brand_support_absolute": "Not Applicable",
  "gst_rate": "Not Applicable",
  "scheme_type": "SELL_SIDE",
  "scheme_subtype": "PUC/FDC"
}
```

## Logging

The system provides comprehensive logging at multiple levels:

### Console Output
- High-level progress indicators
- Critical errors and warnings
- Summary statistics (tokens, cost, processing time)

### Log File (`processing.log`)
```
[2024-12-06 15:55:00] [INFO] Starting PDF extraction for: sample.pdf
[2024-12-06 15:55:02] [DEBUG] Extracted 1,234 words, 3 tables
[2024-12-06 15:55:03] [INFO] Text cleaned: removed 5 disclaimers, 12 links
[2024-12-06 15:55:10] [DSPy] Field: scheme_name
                      Input: "Subject: Q4 Marketing Support..."
                      Reasoning: Subject line contains clear scheme identifier
                      Confidence: High
                      Output: "Q4 Marketing Support Scheme"
[2024-12-06 15:55:45] [TOKENS] Input: 2,345 | Output: 987 | Total: 3,332
[2024-12-06 15:55:45] [COST] Model: openai/gpt-4o | Cost: $0.0234
[2024-12-06 15:55:45] [PARAMS] temperature=0.1, top_p=1.0, max_tokens=4000
```

## Field Extraction Details

The system extracts **21 mandatory fields** as per Retailer Hub requirements:

1. Scheme Name
2. Scheme Description
3. Scheme Period
4. Duration
5. Discount Type
6. Max Cap
7. Vendor Name
8. Price Drop Date (PDC only)
9. Start Date
10. End Date
11. FSN File/Config File
12. Minimum of Actual Discount or Agreed Claim Amount
13. Remove GST from Final Claim Amount
14. Over & Above
15. Discount Slab Type (Buyside-Periodic only)
16. Best Bet (Buyside-Periodic only)
17. Brand Support Absolute (One-Off Claims)
18. GST Rate (One-Off Claims)
19. Scheme Type
20. Scheme Subtype

See [PROMPT_REFINED.md](PROMPT_REFINED.md) for detailed extraction logic.

## Scheme Classification

The system classifies schemes into hierarchical types:

**BUY_SIDE**
- PERIODIC_CLAIM (JBP, ToT, Quarterly plans)
- PDC (Price drops, cost reductions)

**SELL_SIDE**
- PUC/FDC (Sellout support, pricing support)
- COUPON (Promo codes, discount coupons)
- SUPER COIN (Loyalty rewards)
- PREXO (Exchange offers)
- BANK OFFER (Card offers, cashback)

**ONE_OFF**
- Ad-hoc approvals, special one-time support

## Text Cleaning Rules

Automatically removes:
- Email disclaimers ("This email is confidential...")
- Caution notices ("CAUTION: This email...")
- Forwarded message chains ("---------- Forwarded message...")
- HTTP/HTTPS links
- Email footers and signatures
- Confidentiality statements

## Performance

| Metric | Typical Value |
|--------|--------------|
| PDF Extraction | 2-5 seconds/page |
| LLM Processing | 10-30 seconds |
| Total (10-page PDF) | 30-60 seconds |
| Token Usage | 2,000-5,000 tokens |
| Cost (GPT-4o) | $0.02-$0.05/PDF |

## Troubleshooting

### PyMuPDF DLL Error on Windows
If you encounter `ImportError: DLL load failed` related to PyMuPDF:
- The system automatically falls back to `pdfplumber`
- This is a known issue on some Windows environments
- Performance may be slightly slower but functionality is preserved

### Tesseract OCR Not Found
```
Error: Tesseract not installed
Solution: Install Tesseract and set TESSERACT_CMD in .env
```

### OpenRouter API Error
```
Error: Unauthorized (401)
Solution: Check OPENROUTER_API_KEY in .env
```

### Table Extraction Issues
```
Issue: Tables not detected
Solution: Ensure PDF is not heavily scanned/rotated. System will attempt OCR fallback.
```

### Missing Fields in Output
```
Issue: Some fields show "Not Specified"
Solution: This is expected when data is not present in the PDF. Check logs for reasoning.
```

## Development

### Running Tests
```bash
# Future implementation
pytest tests/
```

### Code Quality
```bash
# Format code
black src/ main.py

# Lint
pylint src/ main.py
```

## Contributing

This is an enterprise internal tool. For issues or enhancements, contact the development team.

## License

Proprietary - Flipkart Internal Use Only

## Support

For technical support or questions:
- Check logs in `outputs/{timestamp}/processing.log`
- Review [PROMPT_REFINED.md](PROMPT_REFINED.md) for field extraction logic
- Contact: KAM Automation Team

---

**Version**: 2.0  
**Last Updated**: December 2024  
**Maintained by**: Flipkart Retailer Hub Automation Team
