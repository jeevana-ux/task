"""
Scheme Classification Module
Uses keyword matching to classify scheme type and subtype.
"""
from typing import Tuple, List
from ..config import Config


class SchemeClassifier:
    """Classifies schemes based on keyword analysis."""
    
    def __init__(self):
        """Initialize classifier with keyword mappings from config."""
        self.keywords = Config.SCHEME_KEYWORDS
    
    def _find_keywords(self, text: str, keyword_list: List[str]) -> List[str]:
        """
        Find matching keywords in text.
        
        Args:
            text: Input text (lowercased)
            keyword_list: List of keywords to search for
        
        Returns:
            List of found keywords
        """
        text_lower = text.lower()
        found = []
        
        for keyword in keyword_list:
            if keyword in text_lower:
                found.append(keyword)
        
        return found
    
    def classify(self, text: str) -> Tuple[str, str, str]:
        """
        Classify scheme type and subtype.
        
        Args:
            text: Combined email text and table data
        
        Returns:
            Tuple of (scheme_type, scheme_subtype, reasoning)
        """
        text_lower = text.lower()
        reasoning_parts = []
        
        # Check ONE_OFF first (highest priority)
        one_off_keywords = self._find_keywords(text, self.keywords["ONE_OFF"])
        if one_off_keywords:
            reasoning = f"Found ONE_OFF keywords: {', '.join(one_off_keywords)}"
            return "ONE_OFF", "N/A", reasoning
        
        # Check BUY_SIDE subtypes
        buy_side_periodic = self._find_keywords(
            text, 
            self.keywords["BUY_SIDE"]["PERIODIC_CLAIM"]
        )
        buy_side_pdc = self._find_keywords(
            text,
            self.keywords["BUY_SIDE"]["PDC"]
        )
        
        # Check SELL_SIDE subtypes
        puc_fdc = self._find_keywords(text, self.keywords["SELL_SIDE"]["PUC/FDC"])
        coupon = self._find_keywords(text, self.keywords["SELL_SIDE"]["COUPON"])
        super_coin = self._find_keywords(text, self.keywords["SELL_SIDE"]["SUPER COIN"])
        prexo = self._find_keywords(text, self.keywords["SELL_SIDE"]["PREXO"])
        bank_offer = self._find_keywords(text, self.keywords["SELL_SIDE"]["BANK OFFER"])
        
        # Decision logic: PDC takes precedence if keywords found
        if buy_side_pdc:
            reasoning = f"Found BUY_SIDE → PDC keywords: {', '.join(buy_side_pdc)}"
            return "BUY_SIDE", "PDC", reasoning
        
        if buy_side_periodic:
            reasoning = f"Found BUY_SIDE → PERIODIC_CLAIM keywords: {', '.join(buy_side_periodic)}"
            return "BUY_SIDE", "PERIODIC_CLAIM", reasoning
        
        # SELL_SIDE classification
        if bank_offer:
            reasoning = f"Found SELL_SIDE → BANK OFFER keywords: {', '.join(bank_offer)}"
            return "SELL_SIDE", "BANK OFFER", reasoning
        
        if coupon:
            reasoning = f"Found SELL_SIDE → COUPON keywords: {', '.join(coupon)}"
            return "SELL_SIDE", "COUPON", reasoning
        
        if super_coin:
            reasoning = f"Found SELL_SIDE → SUPER COIN keywords: {', '.join(super_coin)}"
            return "SELL_SIDE", "SUPER COIN", reasoning
        
        if prexo:
            reasoning = f"Found SELL_SIDE → PREXO keywords: {', '.join(prexo)}"
            return "SELL_SIDE", "PREXO", reasoning
        
        if puc_fdc:
            reasoning = f"Found SELL_SIDE → PUC/FDC keywords: {', '.join(puc_fdc)}"
            return "SELL_SIDE", "PUC/FDC", reasoning
        
        # Default fallback
        reasoning = "No specific keywords found. Defaulting to SELL_SIDE → PUC/FDC"
        return Config.DEFAULT_SCHEME_TYPE, Config.DEFAULT_SCHEME_SUBTYPE, reasoning
