"""
Deterministic Content Cleaner - Lean Pipeline with Protection
Chains specialized cleaners while preserving business data and tables.
"""
import re
import unicodedata
from typing import Dict

from .cc_footer_cleaner import CcFooterCleaner
from .disclaimer_cleaner import DisclaimerCleaner


class DeterministicContentCleaner:
    """
    Pipeline orchestrator with data protection.
    
    Flow: Normalize → Preprocess → Segment → Protect → Clean → Output
    """
    
    # Business-critical keywords (always protected)
    # Expanded to cover all email types: claims, products, logistics, contacts, etc.
    PROTECTED_KEYWORDS = [
        # Core Business (14 keywords)
        r'\b(scheme|claim|invoice|bill|payment|fsn|sku|po\s*#?|order|cn|dn|debit|credit)\b',
        r'\btotal\s+amount\b',
        r'\bvendor\s+name\b',
        
        # Product & Model (5 keywords)
        r'\b(product|model|brand|item|category)\b',
        
        # Quantity & Stock (6 keywords)
        r'\b(quantity|qty|units?|stock|pieces?|items?)\b',
        
        # Pricing & Financial (6 keywords)
        r'\b(price|amount|cost|value|rate|margin)\b',
        r'\b(discount|rebate|commission|incentive)\b',
        
        # Dates & Time (5 keywords)
        r'\b(date|effective|deadline|due|valid|expiry)\b',
        
        # Logistics & Shipping (8 keywords)
        r'\b(warehouse|delivery|shipping|truck|transport|dispatch|location|address)\b',
        
        # Actions & Instructions (6 keywords)
        r'\b(submit|provide|attach|send|upload|confirm)\b',
        
        # Documents & Files (5 keywords)
        r'\b(document|file|report|screenshot|attachment)\b',
        
        # Contact Information (4 keywords)
        r'\b(contact|phone|email|mobile)\b',
        
        # Identifiers (5 keywords)
        r'\b(serial|batch|lot|tracking|id)\b',
        
        # Specifications (4 keywords)
        r'\b(specification|spec|features?|details?)\b',
        
        # Currency Symbols (matches ₹100, $50, etc.)
        r'[₹€£¥\$]\s*\d',
        
        # Quantities with Units (matches 100 units, 50 kg, etc.)
        r'\d+\s*(units?|pieces?|kgs?|grams?|litres?|tons?)',
        
        # Date Patterns (DD/MM/YYYY, DD-MM-YYYY)
        r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        
        # Time Patterns (10:30 AM, 2:45 PM)
        r'\d{1,2}:\d{2}\s*(?:AM|PM)',
        
        # Percentages (4%, 10.5%)
        r'\d+\.?\d*\s*%',
        
        # Common Business IDs (CLM-123, INV-456, PO-789)
        r'\b[A-Z]{2,4}-\d{3,}',
    ]
    
    def __init__(self, logger=None):
        self.logger = logger
        self.cc_footer_cleaner = CcFooterCleaner(logger=logger)
        self.disclaimer_cleaner = DisclaimerCleaner(logger=logger)
        self._compiled_protected = [re.compile(p) for p in self.PROTECTED_KEYWORDS]
        
        # Statistics
        self.audit_summary = {
            "removed": 0,
            "retained": 0,
            "audit_log": [],
            "protected_count": 0,
            "table_count": 0
        }
    
    def clean(self, text: str) -> str:
        """
        Main cleaning pipeline.
        
        1. Normalize → 2. Preprocess → 3. Segment → 4. Protect → 5. Clean → 6. Combine
        """
        if not text:
            return ""
        
        # Step 1: Normalize
        text = self._normalize_text(text)
        
        # Step 2: Preprocess (before segmentation)
        text = self._preprocess_cc_removal(text)
        text = self._preprocess_from_to_removal(text)
        text = self._preprocess_disclaimer_removal(text)
        
        # Step 3: Segment
        paragraphs = self._segment_paragraphs(text)
        if not paragraphs:
            return ""
        
        # Step 4: Classify paragraphs
        protected_paragraphs = []
        cleanable_paragraphs = []
        
        for para in paragraphs:
            if self._is_table(para):
                protected_paragraphs.append(para)
                self.audit_summary["table_count"] += 1
                self.audit_summary["retained"] += 1
                if self.logger:
                    self.logger.debug(f"[Table] Protected: {para[:50]}...")
            elif self._is_protected(para):
                protected_paragraphs.append(para)
                self.audit_summary["protected_count"] += 1
                self.audit_summary["retained"] += 1
                if self.logger:
                    self.logger.debug(f"[Protected] Kept: {para[:50]}...")
            else:
                cleanable_paragraphs.append(para)
        
        # Step 5: Clean non-protected paragraphs
        cleanable_text = '\n\n'.join(cleanable_paragraphs)
        cleanable_text = self._clean_with_cc_footer(cleanable_text)
        cleanable_text = self._clean_with_disclaimer(cleanable_text)
        
        # Step 6: Combine
        final_paragraphs = protected_paragraphs
        if cleanable_text.strip():
            final_paragraphs.extend(cleanable_text.split('\n\n'))
        
        self._aggregate_stats()
        return '\n\n'.join(final_paragraphs)
    
    def _normalize_text(self, text: str) -> str:
        """Normalize Unicode and remove OCR artifacts."""
        text = unicodedata.normalize('NFKC', text)
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text) #stripping control chars
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text) #Invisible char removal
        text = re.sub(r'\u00AD', '', text) #hyphenation
        text = re.sub(r'[\u2028\u2029]', '\n', text) #standardize line breaks
        text = text.replace('\u00A0', ' ') #Space normalization
        text = text.replace('\u2011', '-') #Hyphen normalization
        return text
    
    def _preprocess_cc_removal(self, text: str) -> str:
        """Remove Cc: lines before segmentation."""
        lines = text.split('\n')
        cleaned_lines = []
        skip_cc_block = False
        
        for line in lines:
            line_stripped = line.strip()
            
            if re.match(r'(?i)^Cc\s*:', line_stripped):
                skip_cc_block = True
                self.audit_summary["removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Cc] Removed: {line_stripped[:50]}...")
                continue
            
            if skip_cc_block:
                has_email = bool(re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', line_stripped, re.IGNORECASE))
                ends_with_separator = line_stripped.endswith((',', ';'))
                
                if has_email or ends_with_separator:
                    if self.logger:
                        self.logger.debug(f"[Cc Cont] Removed: {line_stripped[:50]}...")
                    continue
                else:
                    skip_cc_block = False
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _preprocess_from_to_removal(self, text: str) -> str:
        """
        Safely removes From: and To: address headers, including multi-line lists.
        Handles cases like:
        From: Name <email@domain.com>
        To: Recipient 1 <r1@domain.com>,
            Recipient 2 <r2@domain.com>
        """
        lines = text.split('\n')
        cleaned_lines = []
        skip_block = False
        
        # Pattern to match start of header
        header_pattern = re.compile(r'(?i)^(From|To)\s*:', re.IGNORECASE)
        # Pattern to identify continuation (emails or comma-separated names)
        email_pattern = re.compile(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', re.IGNORECASE)
        
        for line in lines:
            line_stripped = line.strip()
            
            # Detect start of an address header
            if header_pattern.match(line_stripped):
                skip_block = True
                self.audit_summary["removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Address] Removing header: {line_stripped[:50]}...")
                continue
            
            # Handle potential multi-line continuation
            if skip_block:
                if not line_stripped:
                    # Empty line reliably ends a header block
                    skip_block = False
                else:
                    # Check if this line is a continuation of the address list
                    has_email = bool(email_pattern.search(line_stripped))
                    is_list_continuation = line_stripped.endswith((',', ';')) or '<' in line_stripped or '>' in line_stripped
                    
                    if has_email or is_list_continuation:
                        if self.logger:
                            self.logger.debug(f"[Address Cont] Removing continuation: {line_stripped[:30]}...")
                        # Not incrementing 'removed' count for every line to avoid skewing stats, 
                        # usually the header block counts as one removal event.
                        continue
                    else:
                        # Line doesn't look like an address continuation, stop skipping
                        skip_block = False
            
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _preprocess_disclaimer_removal(self, text: str) -> str:
        """Remove disclaimer blocks before segmentation."""
        disclaimer_markers = [
            r'This e-mail message may contain confidential',
            r'This email.*?confidential.*?legally protected',
            r'This email and any files transmitted.*?confidential',
            r'This message contains confidential information',
            r'Any views or opinions presented in this email',
            r'(?i)本电子邮件及其附件含有.*?保密信息',
        ]
        
        end_markers = [
            r'confirmation of any transaction or contract',
            r'attachments are not intended as an offer',
            r'strictly prohibited',
            r'personally liable for any damages',
            r'actions taken on the basis of the information provided',
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
                    
                    for end_marker in end_markers:
                        end_match = re.search(end_marker, text[start_pos:], re.IGNORECASE)
                        if end_match:
                            end_pos = start_pos + end_match.end()
                            sentence_end = re.search(r'[.\n]', text[end_pos:end_pos+200])
                            if sentence_end:
                                end_pos += sentence_end.end()
                            break
                    
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
    
    def _segment_paragraphs(self, text: str) -> list:
        """Segment text into paragraphs."""
        return [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
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
    
    def _is_protected(self, text: str) -> bool:
        """Check for business-critical keywords."""
        text_no_emails = re.sub(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', '', text, flags=re.IGNORECASE)
        return any(p.search(text_no_emails) for p in self._compiled_protected)
    
    def _clean_with_cc_footer(self, text: str) -> str:
        """Apply Cc/Footer cleaner to cleanable paragraphs."""
        if not text.strip():
            return text
        
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        cleaned = []
        
        for para in paragraphs:
            if self.cc_footer_cleaner._is_header(para):
                self.audit_summary["removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Header] Removed: {para[:50]}...")
            elif self.cc_footer_cleaner._is_footer(para):
                self.audit_summary["removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Footer] Removed: {para[:50]}...")
            else:
                cleaned.append(para)
                self.audit_summary["retained"] += 1
        
        return '\n\n'.join(cleaned)
    
    def _clean_with_disclaimer(self, text: str) -> str:
        """Apply Disclaimer cleaner to cleanable paragraphs."""
        if not text.strip():
            return text
        
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        cleaned = []
        
        for para in paragraphs:
            if self.disclaimer_cleaner._is_disclaimer(para):
                self.audit_summary["removed"] += 1
                if self.logger:
                    self.logger.debug(f"[Disclaimer] Removed: {para[:50]}...")
            else:
                cleaned.append(para)
                
        
        return '\n\n'.join(cleaned)
    
    def _aggregate_stats(self):
        """Aggregate statistics from cleaners."""
        cc_stats = self.cc_footer_cleaner.get_stats()
        disclaimer_stats = self.disclaimer_cleaner.get_stats()
        self.audit_summary["removed"] += cc_stats["paragraphs_removed"] + disclaimer_stats["paragraphs_removed"]
    
    def get_cleaning_stats(self, original: str, cleaned: str) -> Dict:
        """Calculate cleaning statistics."""
        orig_len = len(original) if original else 0
        clean_len = len(cleaned) if cleaned else 0
        reduction = orig_len - clean_len
        
        return {
            "original_length": orig_len,
            "cleaned_length": clean_len,
            "reduction_chars": reduction,
            "reduction_percent": round((reduction / orig_len * 100), 2) if orig_len > 0 else 0,
        }
    
    def get_audit_summary(self) -> Dict:
        """Get comprehensive audit summary."""
        cc_stats = self.cc_footer_cleaner.get_stats()
        disclaimer_stats = self.disclaimer_cleaner.get_stats()
        
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
    
    def get_detailed_report(self) -> Dict:
        """Get detailed debugging report."""
        return {
            "summary": self.get_audit_summary(),
            "disclaimer_keyword_matches": self.disclaimer_cleaner.get_keyword_report()
        }
