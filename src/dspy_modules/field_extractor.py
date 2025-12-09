"""
DSPy Field Extraction Module
Chain-of-Thought based extraction for all 21 Retailer Hub fields.
"""
import dspy
import json
from typing import Dict, Optional
from .signatures import SchemeExtractionSignature
from .scheme_classifier import SchemeClassifier
from ..logger import FieldLevelLogger
from ..config import Config


class RetailerHubFieldExtractor:
    """
    Main DSPy module for extracting Retailer Hub fields using Chain-of-Thought reasoning.
    """
    
    def __init__(self, logger: FieldLevelLogger):
        """
        Initialize field extractor.
        
        Args:
            logger: Configured logger instance
        """
        self.logger = logger
        self.classifier = SchemeClassifier()
        
        # Initialize DSPy ChainOfThought module
        self.cot_extractor = dspy.ChainOfThought(SchemeExtractionSignature)
        
    def extract_fields(
        self,
        email_text: str,
        table_data: str = "",
        xlsx_data: str = ""
    ) -> Dict:
        """
        Extract all 21 fields from input data.
        
        Args:
            email_text: Cleaned email text
            table_data: Consolidated table data (if available)
            xlsx_data: XLSX spreadsheet content (if provided)
        
        Returns:
            Dictionary with extracted fields
        """
        self.logger.info("Starting DSPy field extraction with Chain-of-Thought...")
        
        # Combine all input for scheme classification
        combined_text = f"{email_text}\n\n{table_data}\n\n{xlsx_data}"
        
        # Classify scheme type first (keyword-based)
        scheme_type, scheme_subtype, classification_reasoning = self.classifier.classify(
            combined_text
        )
        
        self.logger.log_field_extraction(
            field_name="Scheme Type & Subtype",
            input_snippet=combined_text[:500],
            reasoning=classification_reasoning,
            output_value=f"{scheme_type} → {scheme_subtype}",
            confidence="High"
        )
        
        # Call DSPy ChainOfThought for field extraction
        try:
            result = self.cot_extractor(
                email_text=email_text,
                table_data=table_data or "No table data available",
                xlsx_data=xlsx_data or "No XLSX data provided"
            )
            
            # Log each field with its reasoning
            self._log_field_reasoning(result)
            
            # Build output JSON
            output = self._build_output_json(result, scheme_type, scheme_subtype)
            
            return output
        
        except Exception as e:
            self.logger.error(f"DSPy extraction failed: {str(e)}")
            raise
    
    def _log_field_reasoning(self, result):
        """
        Log reasoning for each extracted field.
        
        Args:
            result: DSPy ChainOfThought result
        """
        # Extract fields and their reasoning
        field_mappings = [
            ("scheme_name", "scheme_name_reasoning"),
            ("scheme_description", "scheme_description_reasoning"),
            ("scheme_period", "scheme_period_reasoning"),
            ("duration", "duration_reasoning"),
            ("discount_type", "discount_type_reasoning"),
            ("max_cap", "max_cap_reasoning"),
            ("vendor_name", "vendor_name_reasoning"),
            ("price_drop_date", "price_drop_date_reasoning"),
            ("start_date", "start_date_reasoning"),
            ("end_date", "end_date_reasoning"),
            ("fsn_file_config_file", "fsn_file_config_file_reasoning"),
            ("min_actual_discount_or_agreed_claim", "min_discount_reasoning"),
            ("remove_gst_from_final_claim", "remove_gst_reasoning"),
            ("over_and_above", "over_and_above_reasoning"),
            ("discount_slab_type", "discount_slab_reasoning"),
            ("best_bet", "best_bet_reasoning"),
            ("brand_support_absolute", "brand_support_reasoning"),
            ("gst_rate", "gst_rate_reasoning"),
        ]
        
        for field, reasoning_field in field_mappings:
            field_value = getattr(result, field, "Not extracted")
            reasoning = getattr(result, reasoning_field, "No reasoning provided")
            
            # Determine confidence (simple heuristic)
            confidence = self._assess_confidence(field_value, reasoning)
            
            self.logger.log_field_extraction(
                field_name=field,
                input_snippet="See full email text in processing log",
                reasoning=reasoning,
                output_value=field_value,
                confidence=confidence
            )
    
    def _assess_confidence(self, value: str, reasoning: str) -> str:
        """
        Simple confidence assessment based on value and reasoning.
        
        Args:
            value: Extracted value
            reasoning: Reasoning text
        
        Returns:
            Confidence level: High, Medium, or Low
        """
        value_lower = str(value).lower()
        
        # Low confidence indicators
        if any(indicator in value_lower for indicator in [
            "not specified", "not mentioned", "not found", "n/a", "unknown"
        ]):
            return "Low"
        
        # Medium confidence if reasoning is short
        if len(reasoning) < 50:
            return "Medium"
        
        # High confidence otherwise
        return "High"
    
    def _build_output_json(
        self,
        result,
        scheme_type: str,
        scheme_subtype: str
    ) -> Dict:
        """
        Build final output JSON with exactly 21 fields.
        
        Args:
            result: DSPy extraction result
            scheme_type: Classified scheme type
            scheme_subtype: Classified scheme subtype
        
        Returns:
            Dictionary with 21 fields
        """
        # Apply conditional logic based on scheme type
        discount_slab = getattr(result, "discount_slab_type", "Not Applicable")
        best_bet = getattr(result, "best_bet", "Not Applicable")
        brand_support = getattr(result, "brand_support_absolute", "Not Applicable")
        gst_rate = getattr(result, "gst_rate", "Not Applicable")
        price_drop_date = getattr(result, "price_drop_date", "N/A")
        
        # Conditional fields based on scheme type
        if scheme_type == "BUY_SIDE" and scheme_subtype == "PERIODIC_CLAIM":
            pass  # discount_slab and best_bet remain as extracted
        else:
            discount_slab = "Not Applicable"
            best_bet = "Not Applicable"
        
        if scheme_type == "ONE_OFF":
            pass  # brand_support and gst_rate remain as extracted
        else:
            brand_support = "Not Applicable"
            gst_rate = "Not Applicable"
        
        if scheme_subtype != "PDC":
            price_drop_date = "N/A"
        
        # Build final JSON
        output = {
            "scheme_type": scheme_type,
            "scheme_subtype": scheme_subtype,
            "scheme_name": getattr(result, "scheme_name", "Unnamed Scheme"),
            "scheme_description": getattr(result, "scheme_description", "Details not specified"),
            "scheme_period": getattr(result, "scheme_period", Config.DEFAULT_SCHEME_PERIOD),
            "duration": getattr(result, "duration", "Not Specified"),
            "discount_type": getattr(result, "discount_type", "Not Specified"),
            "max_cap": getattr(result, "max_cap", "No Cap"),
            "vendor_name": getattr(result, "vendor_name", "Unknown Vendor"),
            "price_drop_date": price_drop_date,
            "start_date": getattr(result, "start_date", "Not Specified"),
            "end_date": getattr(result, "end_date", "Not Specified"),
            "fsn_file_config_file": getattr(result, "fsn_file_config_file", Config.DEFAULT_FSN_FILE),
            "min_actual_discount_or_agreed_claim": getattr(
                result, "min_actual_discount_or_agreed_claim", Config.DEFAULT_MIN_DISCOUNT_CLAIM
            ),
            "remove_gst_from_final_claim": getattr(
                result, "remove_gst_from_final_claim", Config.DEFAULT_REMOVE_GST
            ),
            "over_and_above": getattr(result, "over_and_above", Config.DEFAULT_OVER_ABOVE),
            "discount_slab_type": discount_slab,
            "best_bet": best_bet,
            "brand_support_absolute": brand_support,
            "gst_rate": gst_rate
        }
        
        return output
