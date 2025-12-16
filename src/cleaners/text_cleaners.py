"""
Text Content Cleaner
Removes email disclaimers, legal notices, and noise while preserving scheme content.
"""
import re
from typing import Dict


class ContentCleaner:
    """Clean email/PDF text by removing disclaimers and noise."""
    
    # Legal/disclaimer trigger phrases (if ANY found, check the block)
    LEGAL_TRIGGERS = [
        "confidential",
        "intended solely",
        "intended recipient",
        "delete this email",
        "notify the sender",
        "notify the system manager",
        "views or opinions presented",
        "accepts no liability",
        "employees of the flipkart group",
        "defamatory statements",
        "infringe or authorise any infringement",
        "disclosing, copying, distributing"
    ]
    
    # Regex patterns for noise (line-level removal)
    # These match lines that should be TOTALLY removed
    # Regex patterns for noise (line-level removal)
    # These match lines that should be TOTALLY removed
    NOISE_PATTERNS = [
        r"^\s*\[image:.*?\]\s*$",           # Gmail image placeholders
        r"^\s*\[cid:.*?\]\s*$",             # Gmail cid references
        r"^\s*<image\d+\..*?>\s*$",         # Image tags
        r"^\s*https?://\S+\s*$",            # Line containing ONLY a URL
        r"^\s*www\.\S+\s*$",                # Line containing ONLY a www link
        r"^\s*\d+\s*/\s*\d+\s*$",           # Page numbers
        r"^\s*[-_=]{5,}\s*$",               # Separator lines
        r"^\s*\d+,p\d+_t\d+.*$",            # OCR/Extraction artifact noise (relaxed) e.g. 2,p2_t1,,,
        r"^\[Caution\]:.*External email.*$", # External email header
    ]
    
    # Inline noise cleaning patterns (remove substring from line)
    INLINE_PATTERNS = [
        r"https?://\S+",                    # Remove HTTP links within text
        r"www\.\S+",                        # Remove www links within text
        r"^\s*\d+,p\d+_t\d+,\s*[,]*",       # Remove OCR prefixes like "2,p2_t1," or "1,p1_t2,,"
    ]

    def __init__(self):
        # Compile Regex Patterns
        self._noise_patterns = [re.compile(p, re.IGNORECASE) for p in self.NOISE_PATTERNS]
        self._inline_patterns = [re.compile(p, re.IGNORECASE) for p in self.INLINE_PATTERNS]
        
        # Compile Keyword/Flashtext-style patterns (Union of triggers)
        # We escape triggers to safely use them in regex
        escaped_triggers = [re.escape(t) for t in self.LEGAL_TRIGGERS]
        self._keyword_pattern = re.compile(r'|'.join(escaped_triggers), re.IGNORECASE)

    def clean(self, text: str) -> str:
        """
        Clean text following the requested pipeline:
        1. Layout-based removal (Handled in PDFExtractor, verified here)
        2. Flashtext-style Keyword cleaning
        3. Regex cleaning
        """
        if not text:
            return ""
        
        # Step 1: Layout & Inline Pre-processing
        # (Layout removal of Header/Footer/Table happened in PDFExtractor)
        # We do inline cleaning here to ensure keywords aren't broken by artifacts
        lines = []
        for line in text.split("\n"):
            for pattern in self._inline_patterns:
                line = pattern.sub("", line)
            lines.append(line)
        text = "\n".join(lines)

        # Step 2: Flashtext-style Keyword/Boilerplate Removal
        # logic: Identify blocks containing high density of keywords and remove them
        text = self._apply_keyword_removal(text)
        
        # Step 3: Regex Pattern Cleaning (Line-level noise)
        text = self._apply_regex_cleaning(text)
        
        # Normalization
        text = re.sub(r'\n{3,}', '\n\n', text)
        return "\n".join(line.rstrip() for line in text.split("\n")).strip()
    
    def _apply_keyword_removal(self, text: str) -> str:
        """
        🥈 Flashtext-style cleaning.
        Identifies and removes blocks containing specific boilerplate keywords.
        """
        # Split into logical blocks (paragraphs)
        chunks = re.split(r'\n\s*\n', text)
        cleaned_chunks = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
                
            # Count keyword occurrences using fast regex search
            # (Matches Flashtext's "extract_keywords" behavior)
            matches = len(self._keyword_pattern.findall(chunk))
            
            # Heuristic: If block matches multiple keywords, treat as boilerplate
            # Or if it matches specific long disclaimer patterns
            if matches >= 2 or self._is_specific_disclaimer(chunk):
                continue
                
            cleaned_chunks.append(chunk)
            
        return "\n\n".join(cleaned_chunks)

    def _apply_regex_cleaning(self, text: str) -> str:
        """
        🥉 Regex cleaning.
        Removes lines matching specific noise patterns.
        """
        lines = []
        for line in text.split("\n"):
            # Check if line matches any noise pattern
            if self._is_noise(line):
                continue
            lines.append(line)
        return "\n".join(lines)
    
    def _is_specific_disclaimer(self, text: str) -> bool:
        """Check for complex disclaimer patterns using Regex."""
        if len(text) < 50: return False
        
        disclaimer_patterns = [
            r"this\s+email\s+and\s+any\s+files",
            r"views\s+or\s+opinions\s+presented",
            r"accepts\s+no\s+liability",
            r"not\s+the\s+intended\s+recipient",
            r"employees\s+of\s+the\s+flipkart\s+group"
        ]
        
        text_lower = text.lower()
        for p in disclaimer_patterns:
             if re.search(p, text_lower):
                 return True
        return False
    
    def _is_noise(self, line: str) -> bool:
        """Check if line is noise."""
        stripped = line.strip()
        if not stripped: return False
        
        for pattern in self._noise_patterns:
            if pattern.match(stripped):
                return True
        return False
    
    def get_cleaning_stats(self, original: str, cleaned: str) -> Dict:
        """Get cleaning statistics."""
        orig_len = len(original) if original else 0
        clean_len = len(cleaned) if cleaned else 0
        diff = orig_len - clean_len
        
        return {
            "original_length": orig_len,
            "cleaned_length": clean_len,
            "reduction_chars": diff,
            "reduction_percent": round((diff / orig_len * 100), 2) if orig_len > 0 else 0,
        }
