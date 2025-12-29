"""
Disclaimer Cleaner - Refactored for Pipeline Pattern
Takes full text, removes disclaimers, returns cleaned text.
"""
import re
from typing import Dict, List


class DisclaimerCleaner:
    """Pipeline cleaner for legal disclaimers and caution paragraphs."""
    
    # Disclaimer keywords for density-based detection
    DISCLAIMER_KEYWORDS = [
        'confidential', 'legally protected', 'intended solely', 'disclosure',
        'dissemination', 'distribution', 'recipient', 'notify the sender',
        'delete it permanently', 'viruses', 'malicious codes', 'liability',
        'damages', 'error', 'transaction', 'contract', 'privilege',
        'prohibited', 'reliance', 'omissions', 'disclaims', 'attached files',
        'mutations', 'defamatory', 'infringement', 'copyright', 
        'electronic transmission', 'not necessarily secure', 'mutations in their transfer'
    ]
    
    # High-confidence disclaimer markers
    DISCLAIMER_MARKERS = [
        r'This e-mail message may contain confidential',
        r'This email.*?confidential.*?legally protected',
        r'(?i)本电子邮件及其附件含有.*?保密信息',  # Chinese
    ]
    
    # Disclaimer ending markers
    DISCLAIMER_ENDINGS = [
        r'confirmation of any transaction or contract',
        r'attachments are not intended as an offer',
        r'strictly prohibited'
    ]
    
    # Direct pattern matches
    BOILERPLATE_PATTERNS = [
        r'(?i)intended solely for the addressee',
        r'(?i)intended solely for the use of the individual',
        r'(?i)confidentiality notice',
        r'(?i)delete this email',
        r'(?i)views or opinions presented',
        r'(?i)accepts no liability',
        r'(?i)do not reply to this email',
        r'(?i)system generated',
        r'(?i)this email and any files transmitted',
        r'(?i)disclosing, copying, distributing or taking any action',
        r'(?i)contrary to organizational policy',
        r'(?i)employee responsible will be personally liable',
        r'(?i)on behalf of the .* group',
    ]
    
    DENSITY_THRESHOLD = 3  # Min keywords to classify as disclaimer
    
    def __init__(self, logger=None):
        self.logger = logger
        self._compiled_patterns = [re.compile(p) for p in self.BOILERPLATE_PATTERNS]
        self.stats = {
            "disclaimers_removed": 0,
            "disclaimer_blocks_removed": 0,
            "paragraphs_removed": 0,
            "keyword_matches": []
        }
    
    def clean(self, text: str) -> str:
        """
        Pipeline entry point: Remove disclaimers from text.
        
        Args:
            text: Full input text (already cleaned by cc_footer_cleaner)
            
        Returns:
            Text with disclaimers removed
        """
        if not text:
            return ""
        
        # Step 1: Remove disclaimer blocks (before segmentation)
        text = self._remove_disclaimer_blocks(text)
        
        # Step 2: Remove disclaimer paragraphs (after segmentation)
        text = self._remove_disclaimer_paragraphs(text)
        
        return text
    
    def _remove_disclaimer_blocks(self, text: str) -> str:
        """Remove large disclaimer blocks before segmentation."""
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            found_disclaimer = False
            
            for marker in self.DISCLAIMER_MARKERS:
                match = re.search(marker, text, re.IGNORECASE | re.DOTALL)
                if match:
                    found_disclaimer = True
                    start_pos = match.start()
                    
                    # Find the end
                    end_pos = len(text)
                    for end_marker in self.DISCLAIMER_ENDINGS:
                        end_match = re.search(end_marker, text[start_pos:], re.IGNORECASE)
                        if end_match:
                            end_pos = start_pos + end_match.end()
                            # Find sentence end
                            remainder = text[end_pos:end_pos+200]
                            sentence_end = re.search(r'[.\n]', remainder)
                            if sentence_end:
                                end_pos += sentence_end.end()
                            break
                    
                    # Remove block
                    if end_pos > start_pos:
                        if self.logger:
                            self.logger.debug(f"[Disclaimer Block] Removed {end_pos - start_pos} chars")
                        self.stats["disclaimer_blocks_removed"] += 1
                        text = text[:start_pos] + text[end_pos:]
                        break
            
            if not found_disclaimer:
                break
            
            iteration += 1
        
        return text
    
    def _remove_disclaimer_paragraphs(self, text: str) -> str:
        """Remove disclaimer paragraphs using density analysis."""
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        cleaned_paragraphs = []
        
        for para in paragraphs:
            if self._is_disclaimer(para):
                self.stats["disclaimers_removed"] += 1
                self.stats["paragraphs_removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Disclaimer] Removed: {para[:50]}...")
                continue
            
            cleaned_paragraphs.append(para)
        
        return '\n\n'.join(cleaned_paragraphs)
    
    def _is_disclaimer(self, text: str) -> bool:
        """Detect disclaimer using keyword density or pattern matching."""
        text_lower = text.lower()
        
        # Method 1: Keyword density
        matched_keywords = {kw for kw in self.DISCLAIMER_KEYWORDS if kw in text_lower}
        
        if len(matched_keywords) >= self.DENSITY_THRESHOLD:
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
    
    def get_stats(self) -> Dict:
        """Return cleaning statistics."""
        return self.stats.copy()
    
    def get_keyword_report(self) -> List[dict]:
        """Get detailed report of keyword matches."""
        return self.stats["keyword_matches"].copy()
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            "disclaimers_removed": 0,
            "disclaimer_blocks_removed": 0,
            "paragraphs_removed": 0,
            "keyword_matches": []
        }
