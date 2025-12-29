# Modular Text Cleaning System

## Overview
The cleaning system is now split into specialized, independent modules for better debugging and maintenance:

```
src/cleaners/
├── deterministic_cleaner.py    # Main orchestrator
├── cc_footer_cleaner.py        # Cc blocks, headers, footers
└── disclaimer_cleaner.py       # Legal disclaimers & cautions
```

## Architecture

### 1. **cc_footer_cleaner.py** - Cc & Footer Removal
**Purpose:** Remove email metadata and footer noise

**What it cleans:**
- ✅ Cc: email lists (entire paragraph from "Cc:" to last email)
- ✅ Email headers (From, To, Subject, timestamps)
- ✅ Forwarded message markers
- ✅ Gmail/Outlook footer links
- ✅ Pagination marks (1/4, 2/3, etc.)

**Key Methods:**
- `clean_paragraph(text)` → Returns `(should_keep, reason)`
- `_is_cc_block(text)` → Detects Cc: blocks
- `_is_header(text)` → Detects email headers
- `_is_footer(text)` → Detects footer links
- `get_stats()` → Returns removal counts

**Debugging:** Each removal is logged with category and reason.

---

### 2. **disclaimer_cleaner.py** - Disclaimer & Caution Removal
**Purpose:** Remove legal boilerplate using keyword density

**What it cleans:**
- ✅ Confidentiality notices
- ✅ Legal disclaimers
- ✅ Liability waivers
- ✅ "Views expressed" clauses

**Detection Method:**
- **Keyword Density:** If 3+ unique legal keywords found → Remove
- **Pattern Match:** Direct regex for common phrases

**Key Methods:**
- `clean_paragraph(text)` → Returns `(should_keep, reason)`
- `_is_disclaimer(text)` → Density + pattern check
- `get_keyword_report()` → Detailed report of matched keywords (for debugging)

**Debugging:** Returns list of matched keywords for each removed paragraph.

---

### 3. **deterministic_cleaner.py** - Main Orchestrator
**Purpose:** Coordinate all cleaners and protect business data

**Pipeline:**
1. **Normalize** text (Unicode, OCR cleanup)
2. **Segment** into paragraphs
3. For each paragraph:
   - Check if **table** → KEEP
   - Check if has **protected keywords** (claim, invoice, etc.) → KEEP
   - Run **Cc/Footer cleaner**
   - Run **Disclaimer cleaner**
   - Keep if passed all checks
4. Return cleaned text

**Protected Assets:**
- ✅ Tables (Markdown pipes or aligned columns)
- ✅ Business keywords: claim, invoice, bill, FSN, SKU, PO, CN, DN

**Key Methods:**
- `clean(text)` → Main entry point
- `_process_paragraph(text)` → Routes paragraph through cleaners
- `get_audit_summary()` → Comprehensive stats from all cleaners
- `get_detailed_report()` → Full debugging report with keyword matches

---

## Usage Example

```python
from src.cleaners.deterministic_cleaner import DeterministicContentCleaner

cleaner = DeterministicContentCleaner(logger=my_logger)

# Clean text
cleaned = cleaner.clean(raw_text)

# Get stats
stats = cleaner.get_audit_summary()
print(f"Removed: {stats['removed']}")
print(f"Cc blocks: {stats['cc_blocks_removed']}")
print(f"Disclaimers: {stats['disclaimers_removed']}")

# Get detailed debugging report
report = cleaner.get_detailed_report()
print(report['disclaimer_keyword_matches'])
```

---

## Debugging Guide

### To debug Cc/Footer cleaning:
```python
from src.cleaners.cc_footer_cleaner import CcFooterCleaner

cleaner = CcFooterCleaner(logger=logger)
should_keep, reason = cleaner.clean_paragraph(paragraph)
print(f"Keep: {should_keep}, Reason: {reason}")
print(cleaner.get_stats())
```

### To debug Disclaimer cleaning:
```python
from src.cleaners.disclaimer_cleaner import DisclaimerCleaner

cleaner = DisclaimerCleaner(logger=logger)
should_keep, reason = cleaner.clean_paragraph(paragraph)

# See which keywords triggered removal
report = cleaner.get_keyword_report()
for match in report:
    print(f"Removed: {match['text_preview']}")
    print(f"Keywords: {match['keywords_found']}")
```

---

## Statistics Breakdown

The `get_audit_summary()` method returns:

```python
{
    "removed": 10,                    # Total paragraphs removed
    "retained": 25,                   # Total paragraphs kept
    "protected": 5,                   # Business data protected
    "tables_protected": 2,            # Tables protected
    "cc_blocks_removed": 1,           # Cc: blocks removed
    "headers_removed": 3,             # Email headers removed
    "footers_removed": 2,             # Footer links removed
    "disclaimers_removed": 4,         # Disclaimers removed
    "audit_log": [...]                # List of removed paragraphs
}
```

---

## Testing

Run the comprehensive test suite:
```bash
python test_modular_cleaning.py
```

Tests cover:
- ✅ Cc block removal
- ✅ Disclaimer detection
- ✅ Table preservation
- ✅ Full integration with all cleaners

---

## Benefits of Modular Design

1. **Easy Debugging:** Test each cleaner independently
2. **Clear Separation:** Each file has one responsibility
3. **Maintainability:** Update rules without touching other modules
4. **Granular Stats:** Know exactly what was removed and why
5. **Logging:** Each cleaner logs its own removals
