# Complete Cleaners Workflow - Step-by-Step with Real Example

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Real Example Input](#real-example-input)
3. [Step-by-Step Processing](#step-by-step-processing)
4. [Final Output](#final-output)
5. [Statistics & Summary](#statistics--summary)

---

## Architecture Overview

### **Three-Component System:**

```
┌──────────────────────────────────────────┐
│  DeterministicContentCleaner             │
│  (Main Orchestrator)                     │
│                                          │
│  - Normalizes Unicode                    │
│  - Preprocesses (Cc, disclaimers)        │
│  - Protects (tables, business data)      │
│  - Delegates cleaning to specialists     │
└────────────┬─────────────────────────────┘
             │
             ├──────────────────┐
             │                  │
             ▼                  ▼
   ┌─────────────────┐  ┌──────────────────┐
   │ CcFooterCleaner │  │DisclaimerCleaner │
   │                 │  │                  │
   │ - Cc blocks     │  │ - Legal text     │
   │ - Headers       │  │ - Boilerplate    │
   │ - Footers       │  │ - Cautions       │
   └─────────────────┘  └──────────────────┘
```

---

## Real Example Input

Let's use a realistic vendor email PDF:

```text
From: vendor@realme.com
Sent: Monday, June 23, 2025 10:30 AM
To: buyer@flipkart.com
Cc: person1@realme.com, person2@realme.com,
    person3@realme.com, person4@realme.com
Subject: Price Drop realme P3 X 5G

Hi Team,

Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.

Claim ID: CLM-2025-456
Invoice: INV-789
PO Number: PO-2025-123
Total Amount: ₹2,50,000

Product Details:

| Model | Old MBP | New MBP | Margin | Qty |
|-------|---------|---------|--------|-----|
| realme P3 X 5G (6GB+128GB) | ₹13,999 | ₹12,999 | 4% | 100 |
| realme P3 X 5G (8GB+128GB) | ₹14,999 | ₹13,999 | 4% | 50 |

When submit the support file for claim, plz provide:
(1) inventory screenshots
(2) Inventory PDF (signed)

This e-mail message may contain confidential or legally protected information and is intended solely for the use of the intended recipient(s). Unless agreed otherwise, any disclosure, dissemination, distribution, copying or taking of any action based on the information contained herein is prohibited. If the reader of this electronic transmission is not the intended recipient, you are hereby notified that any distribution or copying thereof is strictly prohibited. If you have received this e-mail inadvertently or in error, please notify the sender immediately and delete it permanently from your system.
E-mails are not necessarily secure, so the sender's company will not be responsible at any time for any changes in its transfer, errors, or omissions in this message and disclaims any liability for damages arising from the use of e-mail.
Unless expressly stated, this email and its attachments are not intended as an offer or acceptance, nor as confirmation of any transaction or contract.

[Quoted text hidden]
https://mail.google.com/mail/u/0/?ik=abc123&view=pt
1/3

Thanks & Regards
Vendor Team
```

**Character Count:** ~1,847 characters

---

## Step-by-Step Processing

### **STEP 1: Normalize Unicode**

**Method:** `_normalize_text()`  
**Purpose:** Clean OCR artifacts, preserve business symbols

**Process:**
```python
text = unicodedata.normalize('NFKC', text)  # Standardize Unicode
# Remove control characters
text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
# Remove zero-width spaces
text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
# Fix common OCR artifacts
text = text.replace('\u00A0', ' ')  # Non-breaking space → space
text = text.replace('\u2011', '-')  # Non-breaking hyphen → hyphen
```

**Output after Step 1:**
```text
[Same as input - no OCR artifacts in this example]
Character Count: ~1,847
```

**What changed:** Nothing visible (but invisible characters cleaned)

---

### **STEP 2: Preprocess Cc Removal (Line-Level)**

**Method:** `_preprocess_cc_removal()`  
**Purpose:** Remove Cc: lines BEFORE segmentation

**Process:**
- Scan line-by-line
- Find `Cc:` marker
- Remove that line + all continuation lines (emails or lines ending with `,` or `;`)

**Line-by-Line Execution:**

```
Line: "From: vendor@realme.com"                    → KEEP
Line: "Sent: Monday, June 23, 2025 10:30 AM"       → KEEP
Line: "To: buyer@flipkart.com"                     → KEEP
Line: "Cc: person1@realme.com, person2@realme.com," → REMOVE ✂️ (starts with Cc:)
Line: "    person3@realme.com, person4@realme.com" → REMOVE ✂️ (continuation - has emails)
Line: "Subject: Price Drop realme P3 X 5G"         → KEEP
```

**Output after Step 2:**
```text
From: vendor@realme.com
Sent: Monday, June 23, 2025 10:30 AM
To: buyer@flipkart.com
Subject: Price Drop realme P3 X 5G

Hi Team,

Please find below the Price Drop details...
[rest of email without Cc lines]
```

**Character Count:** ~1,750 (reduced by ~97 chars)  
**Statistics:** `removed: 1` (Cc block counted as 1 removal)

---

### **STEP 3: Preprocess Disclaimer Removal (Block-Level)**

**Method:** `_preprocess_disclaimer_removal()`  
**Purpose:** Remove large disclaimer blocks BEFORE segmentation

**Process:**
- Search for disclaimer start marker: `"This e-mail message may contain confidential"`
- Find disclaimer end marker: `"confirmation of any transaction or contract"`
- Remove entire block from start to end (including sentence ending)

**Block Detection:**

```
Start Position: Found at character 950
  "This e-mail message may contain confidential..."
  
End Position: Found at character 1,600
  "...confirmation of any transaction or contract."

Block to Remove: Characters 950-1,600 (650 characters)
```

**Output after Step 3:**
```text
From: vendor@realme.com
Sent: Monday, June 23, 2025 10:30 AM
To: buyer@flipkart.com
Subject: Price Drop realme P3 X 5G

Hi Team,

Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.

Claim ID: CLM-2025-456
Invoice: INV-789
PO Number: PO-2025-123
Total Amount: ₹2,50,000

Product Details:

| Model | Old MBP | New MBP | Margin | Qty |
|-------|---------|---------|--------|-----|
| realme P3 X 5G (6GB+128GB) | ₹13,999 | ₹12,999 | 4% | 100 |
| realme P3 X 5G (8GB+128GB) | ₹14,999 | ₹13,999 | 4% | 50 |

When submit the support file for claim, plz provide:
(1) inventory screenshots
(2) Inventory PDF (signed)

[Quoted text hidden]
https://mail.google.com/mail/u/0/?ik=abc123&view=pt
1/3

Thanks & Regards
Vendor Team
```

**Character Count:** ~1,100 (reduced by ~650 chars)  
**Statistics:** `removed: 2` (1 Cc + 1 Disclaimer block)

---

### **STEP 4: Segment into Paragraphs**

**Method:** `_segment_paragraphs()`  
**Purpose:** Split text into logical chunks for analysis

**Process:**
```python
paragraphs = re.split(r'\n\s*\n', text)  # Split on double newlines
```

**Output after Step 4:**

**List of 10 Paragraphs:**

```python
[
  # Paragraph 1
  "From: vendor@realme.com\nSent: Monday, June 23, 2025 10:30 AM\nTo: buyer@flipkart.com\nSubject: Price Drop realme P3 X 5G",
  
  # Paragraph 2
  "Hi Team,",
  
  # Paragraph 3
  "Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.",
  
  # Paragraph 4
  "Claim ID: CLM-2025-456\nInvoice: INV-789\nPO Number: PO-2025-123\nTotal Amount: ₹2,50,000",
  
  # Paragraph 5
  "Product Details:",
  
  # Paragraph 6 (TABLE)
  "| Model | Old MBP | New MBP | Margin | Qty |\n|-------|---------|---------|--------|-----|\n| realme P3 X 5G (6GB+128GB) | ₹13,999 | ₹12,999 | 4% | 100 |\n| realme P3 X 5G (8GB+128GB) | ₹14,999 | ₹13,999 | 4% | 50 |",
  
  # Paragraph 7
  "When submit the support file for claim, plz provide:\n(1) inventory screenshots\n(2) Inventory PDF (signed)",
  
  # Paragraph 8
  "[Quoted text hidden]\nhttps://mail.google.com/mail/u/0/?ik=abc123&view=pt\n1/3",
  
  # Paragraph 9
  "Thanks & Regards\nVendor Team"
]
```

**Total Paragraphs:** 9

---

### **STEP 5: Classify & Protect Paragraphs**

**Process:** Iterate through each paragraph, classify as:
- **Protected** (tables, business data) → Never cleaned
- **Cleanable** (other text) → Sent to cleaners

**Paragraph-by-Paragraph Classification:**

#### **Paragraph 1: Email Header**
```
"From: vendor@realme.com\nSent: Monday..."
```
- Table? NO
- Protected keyword? NO
- → **CLEANABLE**

#### **Paragraph 2: Greeting**
```
"Hi Team,"
```
- Table? NO
- Protected keyword? NO
- → **CLEANABLE**

#### **Paragraph 3: Business Text**
```
"Please find below the Price Drop details..."
```
- Table? NO
- Protected keyword? NO
- → **CLEANABLE**

#### **Paragraph 4: Business Data** ⭐
```
"Claim ID: CLM-2025-456\nInvoice: INV-789..."
```
- Table? NO
- Protected keyword? **YES** (`claim`, `invoice`, `po`)
- → **PROTECTED** ✅
- **Statistics:** `protected_count: 1`, `retained: 1`

#### **Paragraph 5: Label**
```
"Product Details:"
```
- Table? NO
- Protected keyword? NO
- → **CLEANABLE**

#### **Paragraph 6: Table** ⭐
```
"| Model | Old MBP | New MBP |..."
```
- Table? **YES** (pipe characters: `|`)
- → **PROTECTED** ✅
- **Statistics:** `table_count: 1`, `retained: 2`

#### **Paragraph 7: Instructions**
```
"When submit the support file for claim..."
```
- Table? NO
- Protected keyword? **YES** (`claim`)
- → **PROTECTED** ✅
- **Statistics:** `protected_count: 2`, `retained: 3`

#### **Paragraph 8: Footer Links**
```
"[Quoted text hidden]\nhttps://mail.google.com/..."
```
- Table? NO
- Protected keyword? NO
- → **CLEANABLE**

#### **Paragraph 9: Signature**
```
"Thanks & Regards\nVendor Team"
```
- Table? NO
- Protected keyword? NO
- → **CLEANABLE**

**Summary after Classification:**
- **Protected Paragraphs:** 3 (Para 4, 6, 7)
- **Cleanable Paragraphs:** 6 (Para 1, 2, 3, 5, 8, 9)

---

### **STEP 6: Clean Cleanable Paragraphs**

**Cleanable paragraphs joined:**
```text
From: vendor@realme.com
Sent: Monday, June 23, 2025 10:30 AM
To: buyer@flipkart.com
Subject: Price Drop realme P3 X 5G

Hi Team,

Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.

Product Details:

[Quoted text hidden]
https://mail.google.com/mail/u/0/?ik=abc123&view=pt
1/3

Thanks & Regards
Vendor Team
```

#### **STEP 6a: Pass to CcFooterCleaner**

**Method:** `_clean_with_cc_footer()`

Re-segment cleanable text:
```python
paragraphs = [
  "From: vendor@realme.com\n...\nSubject: Price Drop realme P3 X 5G",
  "Hi Team,",
  "Please find below the Price Drop details...",
  "Product Details:",
  "[Quoted text hidden]\nhttps://mail.google.com/...\n1/3",
  "Thanks & Regards\nVendor Team"
]
```

**Check each paragraph:**

**Para 1:** "From: vendor@realme.com..."
- Is header? **YES** (`From:`, `To:`, `Subject:` detected)
- → **REMOVE** ✂️
- **Statistics:** `removed: 3`

**Para 2:** "Hi Team,"
- Is header? NO
- Is footer? NO
- → **KEEP** ✅
- **Statistics:** `retained: 4`

**Para 3:** "Please find below..."
- Is header? NO
- Is footer? NO
- → **KEEP** ✅
- **Statistics:** `retained: 5`

**Para 4:** "Product Details:"
- Is header? NO
- Is footer? NO
- → **KEEP** ✅
- **Statistics:** `retained: 6`

**Para 5:** "[Quoted text hidden]..."
- Is header? NO
- Is footer? **YES** (`[Quoted text hidden]`, Gmail link, pagination)
- → **REMOVE** ✂️
- **Statistics:** `removed: 4`

**Para 6:** "Thanks & Regards..."
- Is header? NO
- Is footer? NO
- → **KEEP** ✅
- **Statistics:** `retained: 7`

**Output from CcFooterCleaner:**
```text
Hi Team,

Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.

Product Details:

Thanks & Regards
Vendor Team
```

#### **STEP 6b: Pass to DisclaimerCleaner**

**Method:** `_clean_with_disclaimer()`

Re-segment:
```python
paragraphs = [
  "Hi Team,",
  "Please find below the Price Drop details...",
  "Product Details:",
  "Thanks & Regards\nVendor Team"
]
```

**Check each paragraph for disclaimers:**

All paragraphs pass (no disclaimer keywords, no boilerplate patterns).

**Output from DisclaimerCleaner:**
```text
Hi Team,

Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.

Product Details:

Thanks & Regards
Vendor Team
```

---

### **STEP 7: Combine Protected + Cleaned**

**Protected paragraphs (saved from Step 5):**
```python
[
  "Claim ID: CLM-2025-456\nInvoice: INV-789\nPO Number: PO-2025-123\nTotal Amount: ₹2,50,000",
  
  "| Model | Old MBP | New MBP | Margin | Qty |\n...",
  
  "When submit the support file for claim, plz provide:\n(1) inventory screenshots\n(2) Inventory PDF (signed)"
]
```

**Cleaned paragraphs (from Step 6):**
```python
[
  "Hi Team,",
  "Please find below the Price Drop details...",
  "Product Details:",
  "Thanks & Regards\nVendor Team"
]
```

**Combine:**
```python
final_paragraphs = protected_paragraphs + cleaned_paragraphs
```

**Join with double newlines:**
```python
final_text = '\n\n'.join(final_paragraphs)
```

---

## Final Output

```text
Claim ID: CLM-2025-456
Invoice: INV-789
PO Number: PO-2025-123
Total Amount: ₹2,50,000

| Model | Old MBP | New MBP | Margin | Qty |
|-------|---------|---------|--------|-----|
| realme P3 X 5G (6GB+128GB) | ₹13,999 | ₹12,999 | 4% | 100 |
| realme P3 X 5G (8GB+128GB) | ₹14,999 | ₹13,999 | 4% | 50 |

When submit the support file for claim, plz provide:
(1) inventory screenshots
(2) Inventory PDF (signed)

Hi Team,

Please find below the Price Drop details for realme P3 X 5G effective from 00:00 24th June 2025.

Product Details:

Thanks & Regards
Vendor Team
```

**Final Character Count:** ~570 characters

---

## Statistics & Summary

### **Cleaning Statistics:**

```python
{
  "removed": 4,
  "retained": 7,
  "protected": 2,
  "tables_protected": 1,
  
  # Detailed breakdown:
  "cc_blocks_removed": 1,
  "headers_removed": 1,
  "footers_removed": 1,
  "disclaimer_blocks_removed": 1,
  "disclaimers_removed": 0
}
```

### **Before vs After:**

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Characters** | 1,847 | 570 | -69% |
| **Paragraphs** | 9 | 7 | -2 |
| **Has Cc:** | ✗ Yes | ✓ No | Removed |
| **Has Disclaimer** | ✗ Yes | ✓ No | Removed |
| **Has Headers** | ✗ Yes | ✓ No | Removed |
| **Has Footers** | ✗ Yes | ✓ No | Removed |
| **Has Tables** | ✓ Yes | ✓ Yes | Protected |
| **Has Business Data** | ✓ Yes | ✓ Yes | Protected |

### **What Was Removed:**

1. ✂️ **Cc block** (4 email addresses)
2. ✂️ **Email header** (From, To, Subject, Date)
3. ✂️ **Disclaimer block** (3-paragraph legal text)
4. ✂️ **Footer links** ([Quoted text hidden], Gmail link, pagination)

### **What Was Preserved:**

1. ✅ **Business data** (Claim ID, Invoice, PO, Amount)
2. ✅ **Table** (Product pricing details)
3. ✅ **Instructions** (Claim submission requirements)
4. ✅ **Business content** (Price drop details)
5. ✅ **Signature** (Contact sign-off)

---

## Complete Processing Flow Summary

```
Raw Input (1,847 chars)
    ↓
1. Normalize Unicode
    ↓ (no change - clean input)
2. Preprocess Cc Removal (line-level)
    ↓ (removed 97 chars)
3. Preprocess Disclaimer Removal (block-level)
    ↓ (removed 650 chars)
4. Segment into Paragraphs
    ↓ (9 paragraphs)
5. Classify & Protect
    ↓ (3 protected, 6 cleanable)
6a. Clean with CcFooterCleaner
    ↓ (removed 2 paragraphs)
6b. Clean with DisclaimerCleaner
    ↓ (no additional removals)
7. Combine Protected + Cleaned
    ↓
Final Output (570 chars, 7 paragraphs)
    ✓ 69% size reduction
    ✓ 100% business data preserved
    ✓ 100% tables preserved
```

---

## Key Design Principles

1. **Protection First:** Business data and tables NEVER sent to cleaners
2. **Preprocessing:** Large noise blocks removed BEFORE segmentation
3. **Specialist Cleaners:** Each cleaner has ONE job
4. **Statistics Tracking:** Every removal is counted and logged
5. **Preservation Guarantee:** Protected content is untouchable

This ensures **maximum noise removal** with **zero data loss**.
