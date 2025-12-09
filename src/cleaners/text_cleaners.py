"""Text content cleaning filters."""

import re
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


# Disclaimer detection patterns
DISCLAIMER_KEY_PHRASES = [
    "this email and any files transmitted with it are confidential",
    "if you are not the intended recipient",
    "please notify the sender immediately",
    "delete this email",
    "unauthorized use",
    "confidentiality notice",
    "privileged communication",
    "disclaimer",
    "caution: external email",
    "think before you click",
]

# Email headers to remove
EMAIL_HEADER_PREFIXES = (
    "From:",
    "To:",
    "Cc:",
    "Bcc:",
    "Sent:",
    "Date:",
    "Subject:", # Subject is usually preserved by extractors but repeated in bodies
)

# Gmail-specific noise patterns
GMAIL_NOISE_PATTERNS = [
    r"^\s*\[image:.*?\]\s*$",
    r"^\s*\[cid:.*?\]\s*$",
    r"^\s*<image\d+\..*?>\s*$",
    r"https?://mail\.google\.com/.*",  # Google Mail print/view links
    r".*\.\.\. \d+/\d+$",             # Page numbers with ellipsis (e.g., ... 4/4)
    r"^\s*\d+\s*/\s*\d+\s*$",         # Standalone page numbers
]

SEPARATOR_LINE_RE = re.compile(r"^\s*[-_]{2,}\s*$")
PHONE_NUMBER_RE = re.compile(r"(\+?91[\-\s]?)?[6-9]\d{9}") # Simple Indian mobile regex context


class DisclaimerFilter:
    """Filter to remove email disclaimers and caution notices."""
    
    @property
    def name(self) -> str:
        return "Disclaimer Filter"
    
    def looks_like_disclaimer(self, text: str) -> bool:
        """Check if text block looks like a disclaimer."""
        text_lower = text.lower()
        
        # Check for disclaimer key phrases
        phrase_count = sum(
            1 for phrase in DISCLAIMER_KEY_PHRASES
            if phrase in text_lower
        )
        
        if phrase_count >= 2:
            return True
        
        # Check for very long single-paragraph blocks
        if len(text) > 500 and "\n\n" not in text:
            if any(phrase in text_lower for phrase in DISCLAIMER_KEY_PHRASES):
                return True
        
        return False
    
    def clean(self, text: str) -> str:
        """Remove disclaimer blocks from text."""
        lines = text.split("\n")
        cleaned_lines = []
        in_disclaimer = False
        
        for line in lines:
            if self.looks_like_disclaimer(line):
                in_disclaimer = True
                continue
            
            if in_disclaimer:
                if SEPARATOR_LINE_RE.match(line) or not line.strip():
                    in_disclaimer = False
                continue
            
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)


class EmailHeaderFilter:
    """Filter to remove email headers."""
    
    @property
    def name(self) -> str:
        return "Email Header Filter"
    
    def clean(self, text: str) -> str:
        """Remove email headers."""
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            if line.strip().startswith(EMAIL_HEADER_PREFIXES):
                continue
            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)


class GmailNoiseFilter:
    """Filter to remove Gmail-specific noise (links, artifacts)."""
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in GMAIL_NOISE_PATTERNS]
        # Regex for lines with heavy email address density (e.g. participant lists)
        self.email_list_pattern = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}).*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")
    
    @property
    def name(self) -> str:
        return "Gmail Noise Filter"
    
    def clean(self, text: str) -> str:
        """Remove Gmail noise patterns."""
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            # Check explicit noise patterns
            if any(pattern.match(line.strip()) for pattern in self.patterns):
                continue
            
            # Check for lists of email addresses
            if self.email_list_pattern.search(line):
                continue

            cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)


class SignatureFilter:
    """Filter to remove signatures and 'Regards' blocks."""
    
    @property
    def name(self) -> str:
        return "Signature Filter"
    
    def clean(self, text: str) -> str:
        """Remove signatures."""
        lines = text.split("\n")
        cleaned_lines = []
        
        skip_remaining = False
        # Reverse iterate logic is sometimes better, but let's do forward for safety
        # Actually, signatures can appear multiple times if forwarded.
        
        i = 0
        while i < len(lines):
            line = lines[i]
            line_strip = line.strip()
            line_lower = line_strip.lower()
            
            # Check for signature start
            if line_lower in ["regards", "warm regards", "best regards", "thanks & regards", "thanks and regards", "cheers", "best"]:
                # Look ahead to see if it's followed by a name or typical signature content
                # For now, we'll assume it's a signature and skip it and the next few short lines
                # But we need to be careful not to skip real content if "Regards" is just a word.
                
                # If exact match or starts with these, it's likely a signature
                is_signature = True
            
                if is_signature:
                    # check next few lines for phone numbers or names
                    # Heuristic: Skip until we hit a blank line or separator, OR just skip the next block
                    # Simplified: Skip this line. If next lines are short (< 50 chars) or phone numbers, skip them too.
                    
                    # Add current buffer
                    # But if we are in a signature block, we stop adding.
                    
                    # Let's peek ahead
                    j = i + 1
                    signature_depth = 0
                    while j < len(lines) and signature_depth < 6: # scan max 6 lines for signature info
                        next_line = lines[j].strip()
                        if not next_line:
                            j += 1
                            continue
                            
                        # If it's a phone number or short text (likely name)
                        if len(next_line) < 50 or PHONE_NUMBER_RE.search(next_line):
                             j += 1
                             signature_depth += 1
                        else:
                            break
                    
                    # If we found valid signature content, skip these lines
                    i = j
                    continue

            # Remove standalone phone numbers if they look like contact info (not in a table)
            if len(line_strip) < 30 and PHONE_NUMBER_RE.search(line_strip):
                 i += 1
                 continue

            cleaned_lines.append(line)
            i += 1
            
        return "\n".join(cleaned_lines)


class ContentCleaner:
    """Main content cleaner that applies all filters."""
    
    def __init__(self):
        """Initialize with all available filters."""
        self.filters = [
            GmailNoiseFilter(), # Run first to remove clutter
            EmailHeaderFilter(),
            DisclaimerFilter(),
            SignatureFilter(),
        ]
    
    def clean_text(self, text: str) -> str:
        """Apply all text cleaning filters."""
        cleaned = text
        
        for filter_obj in self.filters:
            cleaned = filter_obj.clean(cleaned)
        
        # Final cleanup: remove excessive blank lines
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        
        return cleaned.strip()
        
    def clean(self, text: str) -> str:
        """Alias for clean_text to match interface."""
        return self.clean_text(text)

    def get_cleaning_stats(self, original: str, cleaned: str) -> dict:
        """Get statistics about cleaning operations."""
        return {
            "original_length": len(original),
            "cleaned_length": len(cleaned),
            "reduction_chars": len(original) - len(cleaned),
            "reduction_percent": ((len(original) - len(cleaned)) / len(original) * 100) 
                                 if len(original) > 0 else 0,
            "links_removed": 0
        }
