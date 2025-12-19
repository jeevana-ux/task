"""
Text Content Cleaner
Removes email disclaimers, legal notices, and noise while PRESERVING important business content.

Strategy:
1. PROTECT important business phrases (whitelisted patterns)
2. Remove ONLY clearly identifiable boilerplate (multi-signal validation)
3. Remove Chinese text blocks (disclaimers in Chinese)
4. Remove duplicate forwarded message content
5. Remove email signatures and noise
"""
import re
from typing import Dict, List, Set

class ContentCleaner:
    """Clean email/PDF text by removing disclaimers and noise while preserving business content."""
    
    # =====================================================
    # WHITELIST: IMPORTANT BUSINESS PHRASES TO ALWAYS KEEP
    # =====================================================
    # If a paragraph contains ANY of these, it is PROTECTED and will NOT be removed
    IMPORTANT_PHRASES = [
        # Greetings and openings
        r"hi\s+dear\s+partner",
        r"dear\s+partner",
        r"dear\s+team",
        r"hi\s+team",
        r"hello\s+team",
        
        # Price and discount related
        r"price\s+drop",
        r"price\s+change",
        r"updated\s+price",
        r"discount",
        r"offer\s+price",
        r"mrp",
        r"selling\s+price",
        r"margin",
        
        # Action items
        r"kindly\s+check",
        r"kindly\s+help",
        r"please\s+find\s+attached",
        r"pfa\b",  # Please Find Attached
        r"please\s+confirm",
        r"please\s+approve",
        r"please\s+process",
        r"kindly\s+release",
        r"kindly\s+process",
        r"do\s+not\s+cancel",
        
        # Business dates and timing
        r"from\s+\d{1,2}:\d{2}",  # From 00:00
        r"\d{1,2}(?:st|nd|rd|th)\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)",
        r"effective\s+date",
        r"valid\s+from",
        r"valid\s+till",
        r"start\s+date",
        r"end\s+date",
        
        # Order and inventory related
        r"open\s+po\b",
        r"purchase\s+order",
        r"inventory",
        r"current\s+stock",
        r"fsn\b",
        
        # Claim related
        r"submit\s+the\s+support\s+file",
        r"claim",
        r"credit\s+note",
        r"cn\b",
        r"support\s+file",
        r"inventory\s+pdf",
        r"inventory\s+screenshots",
        
        # Product/Model information
        r"below\s+models",
        r"model\s+name",
        r"product\s+name",
        r"sku\b",
        r"variant",
        
        # Regards/signature line of actual sender
        r"^regards\s*$",
        r"^thanks\s*&?\s*regards\s*$",
        r"^best\s+regards\s*$",
        
        # Credit Period related
        r"cp\s*:\s*\d+\s*days",
        r"credit\s+period",
    ]
    
    # =====================================================
    # DISCLAIMER DETECTION: MUST HAVE MULTIPLE SIGNALS
    # =====================================================
    # A paragraph is ONLY removed if it matches 2+ of these LEGAL triggers
    LEGAL_TRIGGERS = [
        "confidential",
        "intended solely",
        "intended recipient",
        "delete this email",
        "delete it permanently",
        "notify the sender",
        "notify the system manager",
        "views or opinions presented",
        "accepts no liability",
        "disclaims any liability",
        "employees of the flipkart group",
        "defamatory statements",
        "infringe or authorise any infringement",
        "disclosing, copying, distributing",
        "distribution or copying thereof is strictly prohibited",
        "e-mails are not necessarily secure",
        "may contain viruses or malicious codes",
        "not intended as an offer or acceptance",
        "unless expressly stated",
        "no responsibility is assumed",
        "本电子邮件",  # Chinese email disclaimer start
        "禁止任何人",   # Chinese prohibition phrase
        "如果您错收了本邮件",  # Chinese wrong recipient phrase
    ]
    
    # Full-block disclaimer patterns (longer, specific patterns)
    DISCLAIMER_PATTERNS = [
        r"this\s+e-?mail\s+message\s+may\s+contain\s+confidential",
        r"this\s+email\s+and\s+any\s+files\s+transmitted",
        r"views\s+or\s+opinions\s+presented",
        r"accepts\s+no\s+liability",
        r"not\s+the\s+intended\s+recipient",
        r"employees\s+of\s+the\s+flipkart\s+group",
        r"e-?mails\s+are\s+not\s+necessarily\s+secure",
        r"unless\s+expressly\s+stated.*not\s+intended\s+as\s+an\s+offer",
        r"if\s+you\s+have\s+received\s+this\s+e-?mail\s+in\s+error",
        r"禁止任何人在未经授权",  # Chinese unauthorized use
    ]
    
    # =====================================================
    # NOISE PATTERNS: Line-level removal
    # =====================================================
    NOISE_PATTERNS = [
        r"^\s*\[image:.*?\]\s*$",           # Gmail image placeholders
        r"^\s*\[cid:.*?\]\s*$",             # Gmail cid references
        r"^\s*<image\d+\..*?>\s*$",         # Image tags
        r"^\s*https?://\S+\s*$",            # Line containing ONLY a URL
        r"^\s*www\.\S+\s*$",                # Line containing ONLY a www link
        r"^\s*\d+\s*/\s*\d+\s*$",           # Page numbers
        r"^\s*[-_=]{5,}\s*$",               # Separator lines
        r"^\s*\d+,p\d+_t\d+.*$",            # OCR/Extraction artifact noise
        r"^\[Caution\]:.*External email.*$", # External email header
        r"^\s*\[Quoted\s+text\s+hidden\]\s*$",  # Quoted text hidden markers
    ]
    
    # Inline noise patterns (remove substring, not whole line)
    INLINE_PATTERNS = [
        r"https?://\S+",                    # Remove HTTP links within text
        r"www\.\S+",                        # Remove www links within text
        r"^\s*\d+,p\d+_t\d+,\s*[,]*",       # Remove OCR prefixes
    ]
    
    # Chinese text detection (lines that are predominantly Chinese)
    CHINESE_PATTERN = re.compile(r'[\u4e00-\u9fff]')

    def __init__(self):
        # Compile patterns
        self._noise_patterns = [re.compile(p, re.IGNORECASE) for p in self.NOISE_PATTERNS]
        self._inline_patterns = [re.compile(p, re.IGNORECASE) for p in self.INLINE_PATTERNS]
        self._important_patterns = [re.compile(p, re.IGNORECASE) for p in self.IMPORTANT_PHRASES]
        self._disclaimer_patterns = [re.compile(p, re.IGNORECASE) for p in self.DISCLAIMER_PATTERNS]
        
        # Legal trigger pattern (union of all triggers)
        escaped_triggers = [re.escape(t) for t in self.LEGAL_TRIGGERS]
        self._legal_pattern = re.compile(r'|'.join(escaped_triggers), re.IGNORECASE)
    
    def clean(self, text: str) -> str:
        """
        Clean text with safety-first approach:
        1. Inline cleaning (URLs, artifacts)
        2. Remove Chinese text blocks
        3. Remove verified disclaimer blocks (with whitelist protection)
        4. Remove duplicate forwarded content
        5. Line-level noise removal
        """
        if not text:
            return ""
        
        # Step 1: Inline cleaning (URLs, artifacts)
        lines = []
        for line in text.split("\n"):
            for pattern in self._inline_patterns:
                line = pattern.sub("", line)
            lines.append(line)
        text = "\n".join(lines)
        
        # Step 2: Remove Chinese text blocks (disclaimers in Chinese)
        text = self._remove_chinese_blocks(text)
        
        # Step 3: Remove verified disclaimer blocks (with whitelist protection!)
        text = self._remove_disclaimer_blocks(text)
        
        # Step 4: Remove duplicate forwarded content
        text = self._deduplicate_forwarded_content(text)
        
        # Step 5: Line-level noise removal
        text = self._apply_regex_cleaning(text)
        
        # Normalization
        text = re.sub(r'\n{3,}', '\n\n', text)
        return "\n".join(line.rstrip() for line in text.split("\n")).strip()
    
    def _is_important_content(self, text: str) -> bool:
        """
        Check if text contains important business content that MUST be preserved.
        This is the WHITELIST - if True, the block is PROTECTED.
        """
        for pattern in self._important_patterns:
            if pattern.search(text):
                return True
        return False
    
    def _is_chinese_block(self, text: str) -> bool:
        """Check if text is predominantly Chinese (likely disclaimer)."""
        if not text.strip():
            return False
        
        # Count Chinese characters
        chinese_chars = len(self.CHINESE_PATTERN.findall(text))
        total_chars = len(text.replace(" ", "").replace("\n", ""))
        
        if total_chars == 0:
            return False
        
        # If more than 30% Chinese characters, treat as Chinese block
        return (chinese_chars / total_chars) > 0.3
    
    def _remove_chinese_blocks(self, text: str) -> str:
        """Remove blocks that are predominantly Chinese text (usually disclaimers)."""
        chunks = re.split(r'\n\s*\n', text)
        cleaned_chunks = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
            
            # Keep if it's important business content (even if mixed with Chinese)
            if self._is_important_content(chunk):
                cleaned_chunks.append(chunk)
                continue
            
            # Remove if predominantly Chinese
            if self._is_chinese_block(chunk):
                continue
            
            cleaned_chunks.append(chunk)
        
        return "\n\n".join(cleaned_chunks)
    
    def _is_disclaimer_block(self, text: str) -> bool:
        """
        Check if text is a disclaimer block using multi-signal validation.
        Requires EITHER:
        - 2+ legal trigger keywords, OR
        - Match to a specific long disclaimer pattern
        
        BUT: Returns False if the block contains important business content!
        """
        if len(text) < 50:
            return False
        
        # SAFETY CHECK: If it contains important business content, NEVER remove
        if self._is_important_content(text):
            return False
        
        # Count legal trigger matches
        matches = len(self._legal_pattern.findall(text))
        
        # Multi-signal: Need 2+ triggers to be considered disclaimer
        if matches >= 2:
            return True
        
        # Check specific long disclaimer patterns
        text_lower = text.lower()
        for pattern in self._disclaimer_patterns:
            if pattern.search(text_lower):
                return True
        
        return False
    
    def _remove_disclaimer_blocks(self, text: str) -> str:
        """Remove disclaimer blocks while protecting important content."""
        chunks = re.split(r'\n\s*\n', text)
        cleaned_chunks = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
            
            # Skip if it's a verified disclaimer
            if self._is_disclaimer_block(chunk):
                continue
            
            cleaned_chunks.append(chunk)
        
        return "\n\n".join(cleaned_chunks)
    
    def _deduplicate_forwarded_content(self, text: str) -> str:
        """
        Remove duplicate content from forwarded email chains.
        Keeps the first occurrence of content, removes subsequent duplicates.
        """
        # Detect forwarded message markers
        forwarded_pattern = re.compile(
            r'-{5,}\s*Forwarded\s+message\s*-{5,}|'
            r'From:.*?Sent:.*?To:.*?Subject:',
            re.IGNORECASE | re.DOTALL
        )
        
        chunks = re.split(r'\n\s*\n', text)
        seen_content: Set[str] = set()
        cleaned_chunks = []
        
        for chunk in chunks:
            if not chunk.strip():
                continue
            
            # Normalize for comparison (lowercase, remove extra spaces)
            normalized = " ".join(chunk.lower().split())
            
            # Skip very short chunks for deduplication
            if len(normalized) < 50:
                cleaned_chunks.append(chunk)
                continue
            
            # Check if we've seen this content before
            if normalized in seen_content:
                continue
            
            # Track content
            seen_content.add(normalized)
            cleaned_chunks.append(chunk)
        
        return "\n\n".join(cleaned_chunks)
    
    def _apply_regex_cleaning(self, text: str) -> str:
        """Remove lines matching specific noise patterns."""
        lines = []
        for line in text.split("\n"):
            if self._is_noise(line):
                continue
            lines.append(line)
        return "\n".join(lines)
    
    def _is_noise(self, line: str) -> bool:
        """Check if line is noise."""
        stripped = line.strip()
        if not stripped:
            return False  # Keep empty lines for structure
        
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
