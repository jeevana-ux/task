# Complete Cleaners Module Execution Flow

## Overview: Three Files

```
src/cleaners/
├── deterministic_cleaner.py    (Main Orchestrator - 340 lines)
├── cc_footer_cleaner.py        (Cc/Header/Footer Specialist - 159 lines)
└── disclaimer_cleaner.py       (Disclaimer Specialist - 179 lines)
```

---

## Execution Entry Point

```python
from src.cleaners.deterministic_cleaner import DeterministicContentCleaner

cleaner = DeterministicContentCleaner(logger=my_logger)
cleaned_text = cleaner.clean(raw_text)
```

---

# PART 1: Initialization Phase

## File: deterministic_cleaner.py

### **Function 1: `__init__(self, logger=None)`**

**When Called:** When creating cleaner instance  
**Input:** logger (optional)  
**Output:** Initialized cleaner object

```python
def __init__(self, logger=None):
    self.logger = logger
    
    # CALL: Create CcFooterCleaner instance
    self.cc_footer_cleaner = CcFooterCleaner(logger=logger)  # ← Goes to cc_footer_cleaner.py
    
    # CALL: Create DisclaimerCleaner instance
    self.disclaimer_cleaner = DisclaimerCleaner(logger=logger)  # ← Goes to disclaimer_cleaner.py
    
    # Compile 60+ protection patterns
    self._compiled_protected = [re.compile(p) for p in self.PROTECTED_KEYWORDS]
    
    # Initialize statistics
    self.audit_summary = {
        "removed": 0,
        "retained": 0,
        "audit_log": [],
        "protected_count": 0,
        "table_count": 0
    }
```

**Flow:**
```
User creates cleaner
    ↓
deterministic_cleaner.__init__()
    ├→ cc_footer_cleaner.__init__()      (File: cc_footer_cleaner.py)
    └→ disclaimer_cleaner.__init__()     (File: disclaimer_cleaner.py)
```

---

## File: cc_footer_cleaner.py

### **Function 2: `CcFooterCleaner.__init__(self, logger=None)`**

**When Called:** From deterministic_cleaner.__init__()  
**Input:** logger  
**Output:** CcFooterCleaner instance

```python
def __init__(self, logger=None):
    self.logger = logger
    
    # Compile header patterns (From, To, Subject, etc.)
    self._compiled_headers = [re.compile(p) for p in self.HEADER_PATTERNS]
    
    # Compile footer patterns (Gmail links, pagination, etc.)
    self._compiled_footers = [re.compile(p) for p in self.FOOTER_PATTERNS]
    
    # Initialize statistics
    self.stats = {
        "cc_blocks_removed": 0,
        "headers_removed": 0,
        "footers_removed": 0,
        "paragraphs_removed": 0
    }
```

---

## File: disclaimer_cleaner.py

### **Function 3: `DisclaimerCleaner.__init__(self, logger=None)`**

**When Called:** From deterministic_cleaner.__init__()  
**Input:** logger  
**Output:** DisclaimerCleaner instance

```python
def __init__(self, logger=None):
    self.logger = logger
    
    # Compile boilerplate patterns
    self._compiled_patterns = [re.compile(p) for p in self.BOILERPLATE_PATTERNS]
    
    # Initialize statistics
    self.stats = {
        "disclaimers_removed": 0,
        "disclaimer_blocks_removed": 0,
        "paragraphs_removed": 0,
        "keyword_matches": []
    }
```

---

# PART 2: Cleaning Execution Phase

## File: deterministic_cleaner.py

### **Function 4: `clean(self, text: str) -> str`**

**When Called:** User calls `cleaner.clean(raw_text)`  
**Input:** Raw text (string)  
**Output:** Cleaned text (string)

**This is the MAIN function that orchestrates everything!**

```python
def clean(self, text: str) -> str:
    """
    Main cleaning pipeline.
    1. Normalize → 2. Preprocess → 3. Segment → 4. Protect → 5. Clean → 6. Combine
    """
    if not text:
        return ""
    
    # STEP 1: Normalize
    text = self._normalize_text(text)  # ← CALL Function 5
    
    # STEP 2: Preprocess (before segmentation)
    text = self._preprocess_cc_removal(text)  # ← CALL Function 6
    text = self._preprocess_disclaimer_removal(text)  # ← CALL Function 7
    
    # STEP 3: Segment
    paragraphs = self._segment_paragraphs(text)  # ← CALL Function 8
    if not paragraphs:
        return ""
    
    # STEP 4: Classify paragraphs
    protected_paragraphs = []
    cleanable_paragraphs = []
    
    for para in paragraphs:
        if self._is_table(para):  # ← CALL Function 9
            protected_paragraphs.append(para)
            self.audit_summary["table_count"] += 1
            self.audit_summary["retained"] += 1
            if self.logger:
                self.logger.debug(f"[Table] Protected: {para[:50]}...")
        elif self._is_protected(para):  # ← CALL Function 10
            protected_paragraphs.append(para)
            self.audit_summary["protected_count"] += 1
            self.audit_summary["retained"] += 1
            if self.logger:
                self.logger.debug(f"[Protected] Kept: {para[:50]}...")
        else:
            cleanable_paragraphs.append(para)
    
    # STEP 5: Clean non-protected paragraphs
    cleanable_text = '\n\n'.join(cleanable_paragraphs)
    cleanable_text = self._clean_with_cc_footer(cleanable_text)  # ← CALL Function 11
    cleanable_text = self._clean_with_disclaimer(cleanable_text)  # ← CALL Function 12
    
    # STEP 6: Combine
    final_paragraphs = protected_paragraphs
    if cleanable_text.strip():
        final_paragraphs.extend(cleanable_text.split('\n\n'))
    
    self._aggregate_stats()  # ← CALL Function 13
    return '\n\n'.join(final_paragraphs)
```

---

### **Function 5: `_normalize_text(self, text: str) -> str`**

**When Called:** From clean() - Step 1  
**Input:** Raw text  
**Output:** Normalized text (Unicode cleaned)

```python
def _normalize_text(self, text: str) -> str:
    """Normalize Unicode and remove OCR artifacts."""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    text = re.sub(r'\u00AD', '', text)
    text = re.sub(r'[\u2028\u2029]', '\n', text)
    text = text.replace('\u00A0', ' ')
    text = text.replace('\u2011', '-')
    return text
```

**Example:**
```
Input:  "Invoice₹123\u200B"  (has zero-width space)
Output: "Invoice₹123"        (cleaned)
```

---

### **Function 6: `_preprocess_cc_removal(self, text: str) -> str`**

**When Called:** From clean() - Step 2a  
**Input:** Normalized text (from Function 5)  
**Output:** Text with Cc lines removed

```python
def _preprocess_cc_removal(self, text: str) -> str:
    """Remove Cc: lines before segmentation."""
    lines = text.split('\n')
    cleaned_lines = []
    skip_cc_block = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Detect Cc: line
        if re.match(r'(?i)^Cc\s*:', line_stripped):
            skip_cc_block = True
            self.audit_summary["removed"] += 1
            if self.logger:
                self.logger.debug(f"[Cc] Removed: {line_stripped[:50]}...")
            continue
        
        # Check continuation lines
        if skip_cc_block:
            has_email = bool(re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', 
                                      line_stripped, re.IGNORECASE))
            ends_with_separator = line_stripped.endswith((',', ';'))
            
            if has_email or ends_with_separator:
                if self.logger:
                    self.logger.debug(f"[Cc Cont] Removed: {line_stripped[:50]}...")
                continue
            else:
                skip_cc_block = False
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
```

**Example:**
```
Input:  "From: x@y.com\nCc: a@b.com, c@d.com\nSubject: Test"
Output: "From: x@y.com\nSubject: Test"
```

---

### **Function 7: `_preprocess_disclaimer_removal(self, text: str) -> str`**

**When Called:** From clean() - Step 2b  
**Input:** Text from Function 6 (Cc removed)  
**Output:** Text with disclaimer blocks removed

```python
def _preprocess_disclaimer_removal(self, text: str) -> str:
    """Remove disclaimer blocks before segmentation."""
    disclaimer_markers = [
        r'This e-mail message may contain confidential',
        r'This email.*?confidential.*?legally protected',
        r'(?i)本电子邮件及其附件含有.*?保密信息',
    ]
    
    end_markers = [
        r'confirmation of any transaction or contract',
        r'attachments are not intended as an offer',
        r'strictly prohibited'
    ]
    
    iteration = 0
    while iteration < 10:
        found = False
        
        for marker in disclaimer_markers:
            match = re.search(marker, text, re.IGNORECASE | re.DOTALL)
            if match:
                found = True
                start_pos = match.start()
                end_pos = len(text)
                
                # Find end marker
                for end_marker in end_markers:
                    end_match = re.search(end_marker, text[start_pos:], re.IGNORECASE)
                    if end_match:
                        end_pos = start_pos + end_match.end()
                        sentence_end = re.search(r'[.\n]', text[end_pos:end_pos+200])
                        if sentence_end:
                            end_pos += sentence_end.end()
                        break
                
                # Remove block
                if end_pos > start_pos:
                    if self.logger:
                        self.logger.debug(f"[Disclaimer] Removed {end_pos - start_pos} chars")
                    self.audit_summary["removed"] += 1
                    text = text[:start_pos] + text[end_pos:]
                    break
        
        if not found:
            break
        iteration += 1
    
    return text
```

**Example:**
```
Input:  "Business text.\n\nThis e-mail message may contain confidential...(650 chars)...contract.\n\nMore text."
Output: "Business text.\n\nMore text."
```

---

### **Function 8: `_segment_paragraphs(self, text: str) -> list`**

**When Called:** From clean() - Step 3  
**Input:** Text from Function 7 (Cc & disclaimers removed)  
**Output:** List of paragraph strings

```python
def _segment_paragraphs(self, text: str) -> list:
    """Segment text into paragraphs."""
    return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
```

**Example:**
```
Input:  "Para 1 text.\n\nPara 2 text.\n\nPara 3 text."
Output: ["Para 1 text.", "Para 2 text.", "Para 3 text."]
```

---

### **Function 9: `_is_table(self, text: str) -> bool`**

**When Called:** From clean() - Step 4 (classification loop)  
**Input:** Single paragraph string  
**Output:** True if table, False otherwise

```python
def _is_table(self, text: str) -> bool:
    """Detect if paragraph is a table."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return False
    
    # Pipe-based tables
    pipe_lines = sum(1 for line in lines if line.count('|') >= 2)
    if pipe_lines >= 2:
        return True
    
    # Aligned whitespace tables
    alignment_lines = sum(1 for line in lines if re.search(r'\w{2,}\s{3,}\w{2,}', line) or '\t' in line)
    return len(lines) > 1 and (alignment_lines / len(lines)) >= 0.5
```

**Example:**
```
Input:  "| Product | Price |\n|---------|-------|\n| Item 1  | $10   |"
Output: True (has pipe characters)

Input:  "Regular paragraph text"
Output: False
```

---

### **Function 10: `_is_protected(self, text: str) -> bool`**

**When Called:** From clean() - Step 4 (classification loop)  
**Input:** Single paragraph string  
**Output:** True if has protected keywords, False otherwise

```python
def _is_protected(self, text: str) -> bool:
    """Check for business-critical keywords."""
    # Remove emails to avoid false positives
    text_no_emails = re.sub(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', '', 
                            text, flags=re.IGNORECASE)
    
    # Check if any of 60+ patterns match
    return any(p.search(text_no_emails) for p in self._compiled_protected)
```

**Example:**
```
Input:  "Claim ID: CLM-123"
Output: True (has 'claim' keyword)

Input:  "Quantity: 100 units"
Output: True (has 'quantity' and 'units' keywords)

Input:  "Generic text here"
Output: False
```

---

### **Function 11: `_clean_with_cc_footer(self, text: str) -> str`**

**When Called:** From clean() - Step 5a  
**Input:** Cleanable paragraphs joined (string)  
**Output:** Text with headers/footers removed

```python
def _clean_with_cc_footer(self, text: str) -> str:
    """Apply Cc/Footer cleaner to cleanable paragraphs."""
    if not text.strip():
        return text
    
    # Re-segment cleanable text
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    cleaned = []
    
    for para in paragraphs:
        # CALL: cc_footer_cleaner._is_header() ← Goes to cc_footer_cleaner.py
        if self.cc_footer_cleaner._is_header(para):  # ← CALL Function 14
            self.audit_summary["removed"] += 1
            if self.logger:
                self.logger.debug(f"[Header] Removed: {para[:50]}...")
        # CALL: cc_footer_cleaner._is_footer() ← Goes to cc_footer_cleaner.py
        elif self.cc_footer_cleaner._is_footer(para):  # ← CALL Function 15
            self.audit_summary["removed"] += 1
            if self.logger:
                self.logger.debug(f"[Footer] Removed: {para[:50]}...")
        else:
            cleaned.append(para)
            self.audit_summary["retained"] += 1
    
    return '\n\n'.join(cleaned)
```

**Flow:**
```
_clean_with_cc_footer()
    ├→ cc_footer_cleaner._is_header()  (Function 14)
    └→ cc_footer_cleaner._is_footer()  (Function 15)
```

---

## File: cc_footer_cleaner.py

### **Function 14: `_is_header(self, text: str) -> bool`**

**When Called:** From deterministic_cleaner._clean_with_cc_footer()  
**Input:** Paragraph string  
**Output:** True if header, False otherwise

```python
def _is_header(self, text: str) -> bool:
    """Detect email header blocks."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return False
    
    # High confidence: Thread start markers
    if any(p.search(text) for p in self._compiled_headers 
           if "wrote" in p.pattern or "Forwarded" in p.pattern):
        return True
    
    # Check for standard email metadata
    has_metadata = any(re.search(r'(?i)^\s*(From|To|Cc|Sent|Subject|Date)\s*:', line) 
                      for line in lines)
    header_lines = sum(1 for line in lines 
                      if any(p.search(line) for p in self._compiled_headers))
    
    if len(lines) == 1:
        return header_lines == 1
    return (header_lines / len(lines)) >= 0.5 or (has_metadata and len(lines) < 5)
```

**Example:**
```
Input:  "From: x@y.com\nTo: a@b.com\nSubject: Test"
Output: True (has From/To/Subject)

Input:  "Business paragraph text"
Output: False
```

---

### **Function 15: `_is_footer(self, text: str) -> bool`**

**When Called:** From deterministic_cleaner._clean_with_cc_footer()  
**Input:** Paragraph string  
**Output:** True if footer, False otherwise

```python
def _is_footer(self, text: str) -> bool:
    """Detect footer links and pagination."""
    return any(p.search(text) for p in self._compiled_footers)
```

**Example:**
```
Input:  "https://mail.google.com/mail/u/0/?ik=abc123"
Output: True (Gmail link)

Input:  "[Quoted text hidden]"
Output: True (quoted text marker)

Input:  "1/3"
Output: True (pagination)

Input:  "Business text"
Output: False
```

---

## File: deterministic_cleaner.py

### **Function 12: `_clean_with_disclaimer(self, text: str) -> str`**

**When Called:** From clean() - Step 5b  
**Input:** Text from Function 11 (headers/footers removed)  
**Output:** Text with disclaimers removed

```python
def _clean_with_disclaimer(self, text: str) -> str:
    """Apply Disclaimer cleaner to cleanable paragraphs."""
    if not text.strip():
        return text
    
    # Re-segment
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    cleaned = []
    
    for para in paragraphs:
        # CALL: disclaimer_cleaner._is_disclaimer() ← Goes to disclaimer_cleaner.py
        if self.disclaimer_cleaner._is_disclaimer(para):  # ← CALL Function 16
            self.audit_summary["removed"] += 1
            if self.logger:
                self.logger.debug(f"[Disclaimer] Removed: {para[:50]}...")
        else:
            cleaned.append(para)
    
    return '\n\n'.join(cleaned)
```

**Flow:**
```
_clean_with_disclaimer()
    └→ disclaimer_cleaner._is_disclaimer()  (Function 16)
```

---

## File: disclaimer_cleaner.py

### **Function 16: `_is_disclaimer(self, text: str) -> bool`**

**When Called:** From deterministic_cleaner._clean_with_disclaimer()  
**Input:** Paragraph string  
**Output:** True if disclaimer, False otherwise

```python
def _is_disclaimer(self, text: str) -> bool:
    """Detect disclaimer using keyword density or pattern matching."""
    text_lower = text.lower()
    
    # Method 1: Keyword density (3+ keywords)
    matched_keywords = {kw for kw in self.DISCLAIMER_KEYWORDS if kw in text_lower}
    
    if len(matched_keywords) >= self.DENSITY_THRESHOLD:  # 3
        self.stats["keyword_matches"].append({
            "text_preview": text[:100],
            "keywords_found": list(matched_keywords),
            "count": len(matched_keywords)
        })
        return True
    
    # Method 2: Pattern matching
    if any(p.search(text) for p in self._compiled_patterns):
        return True
    
    return False
```

**Example:**
```
Input:  "This content is confidential, legally protected, and disclosure is prohibited."
Output: True (has 3+ keywords: confidential, legally protected, disclosure, prohibited)

Input:  "Business content here"
Output: False
```

---

## File: deterministic_cleaner.py

### **Function 13: `_aggregate_stats(self)`**

**When Called:** From clean() - Step 6  
**Input:** None  
**Output:** None (updates self.audit_summary)

```python
def _aggregate_stats(self):
    """Aggregate statistics from cleaners."""
    # CALL: Get stats from cc_footer_cleaner
    cc_stats = self.cc_footer_cleaner.get_stats()  # ← CALL Function 17
    
    # CALL: Get stats from disclaimer_cleaner
    disclaimer_stats = self.disclaimer_cleaner.get_stats()  # ← CALL Function 18
    
    # Aggregate
    self.audit_summary["removed"] += (
        cc_stats["paragraphs_removed"] + 
        disclaimer_stats["paragraphs_removed"]
    )
```

**Flow:**
```
_aggregate_stats()
    ├→ cc_footer_cleaner.get_stats()      (Function 17)
    └→ disclaimer_cleaner.get_stats()     (Function 18)
```

---

## File: cc_footer_cleaner.py

### **Function 17: `get_stats(self) -> Dict`**

**When Called:** From deterministic_cleaner._aggregate_stats()  
**Input:** None  
**Output:** Dictionary with statistics

```python
def get_stats(self) -> Dict:
    """Return cleaning statistics."""
    return self.stats.copy()
```

**Example Output:**
```python
{
    "cc_blocks_removed": 2,
    "headers_removed": 1,
    "footers_removed": 1,
    "paragraphs_removed": 2
}
```

---

## File: disclaimer_cleaner.py

### **Function 18: `get_stats(self) -> Dict`**

**When Called:** From deterministic_cleaner._aggregate_stats()  
**Input:** None  
**Output:** Dictionary with statistics

```python
def get_stats(self) -> Dict:
    """Return cleaning statistics."""
    return self.stats.copy()
```

**Example Output:**
```python
{
    "disclaimers_removed": 1,
    "disclaimer_blocks_removed": 1,
    "paragraphs_removed": 1,
    "keyword_matches": [...]
}
```

---

# PART 3: Post-Cleaning (User Calls)

## File: deterministic_cleaner.py

### **Function 19: `get_audit_summary(self) -> Dict`**

**When Called:** User calls after cleaning  
**Input:** None  
**Output:** Comprehensive statistics

```python
def get_audit_summary(self) -> Dict:
    """Get comprehensive audit summary."""
    # CALL: Get stats from both cleaners
    cc_stats = self.cc_footer_cleaner.get_stats()  # ← Function 17
    disclaimer_stats = self.disclaimer_cleaner.get_stats()  # ← Function 18
    
    return {
        "removed": self.audit_summary["removed"],
        "retained": self.audit_summary["retained"],
        "protected": self.audit_summary["protected_count"],
        "tables_protected": self.audit_summary["table_count"],
        "audit_log": self.audit_summary["audit_log"],
        "cc_blocks_removed": cc_stats["cc_blocks_removed"],
        "headers_removed": cc_stats["headers_removed"],
        "footers_removed": cc_stats["footers_removed"],
        "disclaimers_removed": disclaimer_stats["disclaimers_removed"],
        "disclaimer_blocks_removed": disclaimer_stats["disclaimer_blocks_removed"],
    }
```

---

# Complete Function Call Tree

```
User: cleaner = DeterministicContentCleaner(logger)
    ├→ [1] deterministic_cleaner.__init__()
    │   ├→ [2] cc_footer_cleaner.__init__()
    │   └→ [3] disclaimer_cleaner.__init__()
    
User: cleaned = cleaner.clean(raw_text)
    └→ [4] deterministic_cleaner.clean()
        ├→ [5] _normalize_text()
        ├→ [6] _preprocess_cc_removal()
        ├→ [7] _preprocess_disclaimer_removal()
        ├→ [8] _segment_paragraphs()
        ├→ For each paragraph:
        │   ├→ [9] _is_table()
        │   └→ [10] _is_protected()
        ├→ [11] _clean_with_cc_footer()
        │   ├→ [14] cc_footer_cleaner._is_header()
        │   └→ [15] cc_footer_cleaner._is_footer()
        ├→ [12] _clean_with_disclaimer()
        │   └→ [16] disclaimer_cleaner._is_disclaimer()
        └→ [13] _aggregate_stats()
            ├→ [17] cc_footer_cleaner.get_stats()
            └→ [18] disclaimer_cleaner.get_stats()

User: stats = cleaner.get_audit_summary()
    └→ [19] deterministic_cleaner.get_audit_summary()
        ├→ [17] cc_footer_cleaner.get_stats()
        └→ [18] disclaimer_cleaner.get_stats()
```

---

# Data Flow Summary

```
RAW TEXT (input)
    ↓ [Function 5]
Normalized Text (Unicode cleaned)
    ↓ [Function 6]
Text without Cc blocks
    ↓ [Function 7]
Text without Cc & Disclaimers
    ↓ [Function 8]
List of Paragraphs
    ↓ [Functions 9, 10]
Classified: Protected vs Cleanable
    ↓ [Function 11 → 14, 15]
Cleanable without Headers/Footers
    ↓ [Function 12 → 16]
Cleanable without Disclaimers
    ↓ [Function 13]
Statistics Aggregated
    ↓
CLEANED TEXT (output)
```

---

# Summary: 19 Functions Across 3 Files

| # | Function | File | Called By | Purpose |
|---|----------|------|-----------|---------|
| 1 | `__init__` | deterministic_cleaner.py | User | Initialize orchestrator |
| 2 | `__init__` | cc_footer_cleaner.py | Function 1 | Initialize Cc cleaner |
| 3 | `__init__` | disclaimer_cleaner.py | Function 1 | Initialize disclaimer cleaner |
| 4 | `clean` | deterministic_cleaner.py | User | Main pipeline |
| 5 | `_normalize_text` | deterministic_cleaner.py | Function 4 | Clean Unicode |
| 6 | `_preprocess_cc_removal` | deterministic_cleaner.py | Function 4 | Remove Cc lines |
| 7 | `_preprocess_disclaimer_removal` | deterministic_cleaner.py | Function 4 | Remove disclaimer blocks |
| 8 | `_segment_paragraphs` | deterministic_cleaner.py | Function 4 | Split into paragraphs |
| 9 | `_is_table` | deterministic_cleaner.py | Function 4 | Detect tables |
| 10 | `_is_protected` | deterministic_cleaner.py | Function 4 | Detect protected data |
| 11 | `_clean_with_cc_footer` | deterministic_cleaner.py | Function 4 | Apply Cc cleaner |
| 12 | `_clean_with_disclaimer` | deterministic_cleaner.py | Function 4 | Apply disclaimer cleaner |
| 13 | `_aggregate_stats` | deterministic_cleaner.py | Function 4 | Combine statistics |
| 14 | `_is_header` | cc_footer_cleaner.py | Function 11 | Detect headers |
| 15 | `_is_footer` | cc_footer_cleaner.py | Function 11 | Detect footers |
| 16 | `_is_disclaimer` | disclaimer_cleaner.py | Function 12 | Detect disclaimers |
| 17 | `get_stats` | cc_footer_cleaner.py | Functions 13, 19 | Return Cc stats |
| 18 | `get_stats` | disclaimer_cleaner.py | Functions 13, 19 | Return disclaimer stats |
| 19 | `get_audit_summary` | deterministic_cleaner.py | User | Return combined stats |

**Total Execution Flow:** 19 function calls for a single `clean()` operation.
