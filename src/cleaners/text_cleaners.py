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
        "legally protected",
        "intended recipient",
        "intended solely",
        "unauthorized",
        "delete this email",
        "notify the sender",
        "privileged",
        "disclaimer",
        "liability",
        "viruses",
        "malicious",
        "not intended as an offer",
    ]
    
    # Regex patterns for noise (line-level removal)
    NOISE_PATTERNS = [
        r"^\s*\[image:.*?\]\s*$",           # Gmail image placeholders
        r"^\s*\[cid:.*?\]\s*$",             # Gmail cid references
        r"^\s*<image\d+\..*?>\s*$",         # Image tags
        r"https?://mail\.google\.com/.*",   # Gmail links
        r"^\s*\d+\s*/\s*\d+\s*$",           # Page numbers
        r"^\s*Page\s+\d+.*$",               # Page markers
        r"^\s*[-_=]{5,}\s*$",               # Separator lines
        r"^CAUTION:.*$",                    # Caution headers
        r"^\[EXTERNAL\].*$",                # External email markers
    ]
    
    def __init__(self):
        self._noise_patterns = [re.compile(p, re.IGNORECASE) for p in self.NOISE_PATTERNS]
    
    def clean(self, text: str) -> str:
        """Clean text by removing noise and disclaimers."""
        if not text:
            return ""
        
        # Step 1: Remove legal disclaimer blocks
        text = self._remove_legal_blocks(text)
        
        # Step 2: Remove noise patterns line by line
        lines = []
        for line in text.split("\n"):
            if not self._is_noise(line):
                lines.append(line)
        text = "\n".join(lines)
        
        # Step 3: Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        
        return text.strip()
    
    def _remove_legal_blocks(self, text: str) -> str:
        """
        Remove legal disclaimer blocks using smart detection.
        Finds blocks containing legal phrases and removes them.
        """
        # Split text into chunks (by double newlines or long single sections)
        chunks = re.split(r'\n\s*\n', text)
        cleaned = []
        
        for chunk in chunks:
            if self._is_legal_disclaimer(chunk):
                continue
            cleaned.append(chunk)
        
        return "\n\n".join(cleaned)
    
    def _is_legal_disclaimer(self, text: str) -> bool:
        """Check if text block is a legal disclaimer."""
        if not text or len(text) < 50:
            return False
        
        text_lower = text.lower()
        
        # Count matching legal trigger words
        matches = sum(1 for trigger in self.LEGAL_TRIGGERS if trigger in text_lower)
        
        # If 3+ legal triggers found, it's likely a disclaimer
        if matches >= 3:
            return True
        
        # Check for specific disclaimer patterns
        disclaimer_patterns = [
            r"this\s+e?-?mail.*(?:confidential|intended|recipient)",
            r"if\s+you\s+(?:are\s+not|have\s+received).*(?:intended|error)",
            r"(?:delete|destroy).*(?:immediately|permanently)",
            r"(?:liability|responsible).*(?:damage|loss|error)",
            r"(?:attachment|files?).*(?:virus|malicious)",
            r"unless\s+expressly\s+stated.*(?:offer|contract)",
        ]
        
        for pattern in disclaimer_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
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
