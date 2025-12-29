"""
Cc and Footer Cleaner - Refactored for Pipeline Pattern
Takes full text, removes Cc blocks and footers, returns cleaned text.
"""
import re
from typing import Dict


class CcFooterCleaner:
    """Pipeline cleaner for Cc blocks, headers, and footer links."""
    
    # Email thread header patterns
    HEADER_PATTERNS = [
        r'(?i)^\s*(From|Sent|Date|To|Subject)\s*:.*',
        r'(?i)-+\s*Forwarded message\s*-+',
        r'(?i)On\s+.*wrote\s*:',
        r'(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b.*?(?:AM|PM|at|on)',
        r'(?i)^\s*(?:["\']?[\w\s.-]+["\']?\s*)?<[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}>',
        r'(?i)^\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s*(?:AM|PM)$'
    ]
    
    # Footer noise patterns
    FOOTER_PATTERNS = [
        r'(?i)https?://mail\.google\.com/.*',
        r'(?i)\[Quoted text hidden\]',
        r'^\d+/\d+$',  # Pagination
        r'(?i)click here to unsubscribe',
        r'(?i)manage preferences',
    ]
    
    def __init__(self, logger=None):
        self.logger = logger
        self._compiled_headers = [re.compile(p) for p in self.HEADER_PATTERNS]
        self._compiled_footers = [re.compile(p) for p in self.FOOTER_PATTERNS]
        self.stats = {
            "cc_blocks_removed": 0,
            "headers_removed": 0,
            "footers_removed": 0,
            "paragraphs_removed": 0
        }
    
    def clean(self, text: str) -> str:
        """
        Pipeline entry point: Remove Cc blocks, headers, and footers from text.
        
        Args:
            text: Full input text
            
        Returns:
            Cleaned text with Cc/headers/footers removed
        """
        if not text:
            return ""
        
        # Step 1: Remove Cc blocks (line-by-line preprocessing)
        text = self._remove_cc_blocks(text)
        
        # Step 2: Remove headers and footers (paragraph-level)
        text = self._remove_headers_footers(text)
        
        return text
    
    def _remove_cc_blocks(self, text: str) -> str:
        """Remove Cc: lines and their continuations."""
        lines = text.split('\n')
        cleaned_lines = []
        skip_cc_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect start of Cc block
            if re.match(r'(?i)^Cc\s*:', line_stripped):
                skip_cc_block = True
                self.stats["cc_blocks_removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Cc Line] Removed: {line_stripped[:50]}...")
                continue
            
            # Check if we're in a Cc block continuation
            if skip_cc_block:
                has_email = bool(re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', line_stripped, re.IGNORECASE))
                ends_with_separator = line_stripped.endswith((',', ';'))
                
                if has_email or ends_with_separator:
                    if self.logger:
                        self.logger.debug(f"[Cc Continuation] Removed: {line_stripped[:50]}...")
                    continue
                else:
                    skip_cc_block = False
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _remove_headers_footers(self, text: str) -> str:
        """Remove email headers and footer links from paragraphs."""
        # Segment into paragraphs
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        cleaned_paragraphs = []
        
        for para in paragraphs:
            # Check if header
            if self._is_header(para):
                self.stats["headers_removed"] += 1
                self.stats["paragraphs_removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Header] Removed: {para[:50]}...")
                continue
            
            # Check if footer
            if self._is_footer(para):
                self.stats["footers_removed"] += 1
                self.stats["paragraphs_removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Footer] Removed: {para[:50]}...")
                continue
            
            # Keep paragraph
            cleaned_paragraphs.append(para)
        
        return '\n\n'.join(cleaned_paragraphs)
    
    def _is_header(self, text: str) -> bool:
        """Detect email header blocks."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            return False
        
        # High confidence: Thread start markers
        if any(p.search(text) for p in self._compiled_headers if "wrote" in p.pattern or "Forwarded" in p.pattern):
            return True
        
        # Check for standard email metadata
        has_metadata = any(re.search(r'(?i)^\s*(From|To|Cc|Sent|Subject|Date)\s*:', line) for line in lines)
        header_lines = sum(1 for line in lines if any(p.search(line) for p in self._compiled_headers))
        
        if len(lines) == 1:
            return header_lines == 1
        return (header_lines / len(lines)) >= 0.5 or (has_metadata and len(lines) < 5)
    
    def _is_footer(self, text: str) -> bool:
        """Detect footer links and pagination."""
        return any(p.search(text) for p in self._compiled_footers)
    
    def get_stats(self) -> Dict:
        """Return cleaning statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            "cc_blocks_removed": 0,
            "headers_removed": 0,
            "footers_removed": 0,
            "paragraphs_removed": 0
        }
