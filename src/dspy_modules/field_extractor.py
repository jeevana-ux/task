"""
DSPy Field Extraction Module
Chain-of-Thought based extraction for all 21 Retailer Hub fields.
Scheme classification is now LLM-based with reasoning, not keyword matching.
"""
import dspy
import json
from typing import Dict, Optional
from .signatures import SchemeExtractionSignature
from ..logger import FieldLevelLogger
from ..config import Config


class RetailerHubFieldExtractor:
    """
    Main DSPy module for extracting Retailer Hub fields using Chain-of-Thought reasoning.
    Scheme type/subtype classification is done by the LLM with detailed reasoning.
    """
    
    def __init__(self, logger: FieldLevelLogger):
        """
        Initialize field extractor.
        
        Args:
            logger: Configured logger instance
        """
        self.logger = logger
        
        # Initialize DSPy ChainOfThought module for all field extraction including classification
        self.cot_extractor = dspy.ChainOfThought(SchemeExtractionSignature)
        
    def extract_fields(
        self,
        email_text: str,
        table_data: str = "",
        xlsx_data: str = ""
    ) -> Dict:
        """
        Extract all 21 fields from input data using LLM with Chain-of-Thought reasoning.
        Scheme type and subtype are classified by the LLM, not keyword matching.
        
        Args:
            email_text: Cleaned email text
            table_data: Consolidated table data (if available)
            xlsx_data: XLSX spreadsheet content (if provided)
        
        Returns:
            Dictionary with extracted fields
        """
        self.logger.section("LLM Field Extraction with DSPy Chain-of-Thought")
        
        # Log input context being sent to LLM
        self.logger.log_input_context(
            email_text=email_text,
            table_data=table_data or "No table data",
            xlsx_data=xlsx_data or "No XLSX data"
        )
        
        # Call DSPy ChainOfThought for ALL field extraction including scheme type/subtype
        try:
            result = self.cot_extractor(
                email_text=email_text,
                table_data=table_data or "No table data available",
                xlsx_data=xlsx_data or "No XLSX data provided"
            )
            
            # Extract scheme type and subtype from LLM result
            scheme_type = self._normalize_scheme_type(
                getattr(result, "scheme_type", Config.DEFAULT_SCHEME_TYPE)
            )
            scheme_subtype = self._normalize_scheme_subtype(
                getattr(result, "scheme_subtype", Config.DEFAULT_SCHEME_SUBTYPE),
                scheme_type
            )
            classification_reasoning = getattr(
                result, "scheme_classification_reasoning", "LLM-based classification"
            )
            
            # Log scheme classification with LLM reasoning
            self.logger.log_field_extraction(
                field_name="scheme_type",
                input_snippet="Full email context",
                reasoning=classification_reasoning,
                output_value=scheme_type,
                confidence=self._assess_confidence(scheme_type, classification_reasoning)
            )
            self.logger.log_field_extraction(
                field_name="scheme_subtype",
                input_snippet="Full email context",
                reasoning=classification_reasoning,
                output_value=scheme_subtype,
                confidence=self._assess_confidence(scheme_subtype, classification_reasoning)
            )
            
            # Log each field with its reasoning
            self._log_field_reasoning(result)
            
            # Build output JSON using LLM-extracted scheme type/subtype
            output = self._build_output_json(result, scheme_type, scheme_subtype)
            
            # Log final output JSON
            self.logger.log_final_output(output)
            
            return output
        
        except Exception as e:
            self.logger.error(f"DSPy extraction failed: {str(e)}")
            raise
    
    def _normalize_scheme_type(self, raw_type: str) -> str:
        """
        Normalize scheme type to one of the valid values.
        
        Args:
            raw_type: Raw scheme type from LLM
        
        Returns:
            Normalized scheme type: BUY_SIDE, SELL_SIDE, or ONE_OFF
        """
        if not raw_type:
            return Config.DEFAULT_SCHEME_TYPE
        
        raw_upper = raw_type.upper().strip()
        
        # Direct match
        valid_types = ["BUY_SIDE", "SELL_SIDE", "ONE_OFF"]
        if raw_upper in valid_types:
            return raw_upper
        
        # Handle variations
        if any(term in raw_upper for term in ["BUY", "BUYSIDE", "BUY-SIDE"]):
            return "BUY_SIDE"
        if any(term in raw_upper for term in ["SELL", "SELLSIDE", "SELL-SIDE"]):
            return "SELL_SIDE"
        if any(term in raw_upper for term in ["ONE", "ONEOFF", "ONE-OFF", "ADHOC", "AD-HOC"]):
            return "ONE_OFF"
        
        # Default fallback
        self.logger.warning(f"Unknown scheme_type '{raw_type}', defaulting to {Config.DEFAULT_SCHEME_TYPE}")
        return Config.DEFAULT_SCHEME_TYPE
    
    def _normalize_scheme_subtype(self, raw_subtype: str, scheme_type: str) -> str:
        """
        Normalize scheme subtype based on the scheme type.
        Maps LLM output variations to standard subtype names.
        
        Args:
            raw_subtype: Raw scheme subtype from LLM
            scheme_type: Normalized scheme type
        
        Returns:
            Normalized scheme subtype matching Retailer Hub format
        """
        if not raw_subtype:
            return Config.DEFAULT_SCHEME_SUBTYPE
        
        raw_upper = raw_subtype.upper().strip().replace(" ", "_")
        
        # For ONE_OFF, always return N/A
        if scheme_type == "ONE_OFF":
            return "N/A"
        
        # Handle BUY_SIDE subtypes
        if scheme_type == "BUY_SIDE":
            if any(term in raw_upper for term in ["PERIODIC", "CLAIM", "JBP", "TOT", "NRV", "BS_PC", "BS-PC"]):
                return "PERIODIC_CLAIM"
            if any(term in raw_upper for term in ["PDC", "PRICE_DROP", "PRICE_PROTECTION", "PP"]):
                return "PDC"
            # Default for BUY_SIDE
            return "PERIODIC_CLAIM"
        
        # Handle SELL_SIDE subtypes
        if scheme_type == "SELL_SIDE":
            # COUPON (CP)
            if any(term in raw_upper for term in ["COUPON", "VPC", "PROMO", "VOUCHER", "SS_CP", "SS-CP", "CP"]):
                return "CP"

            # PUC_FDC (PUC)
            if any(term in raw_upper for term in ["PUC", "FDC", "SELLOUT", "SELL_OUT", "PRICING", "SS_PUC", "SS-PUC"]):
                return "PUC"
            
            # SUPER_COIN (SC)
            if any(term in raw_upper for term in ["SUPER_COIN", "SUPERCOIN", "SUPER", "SC_FUNDING", "SS_SC", "SS-SC", "SC"]):
                return "SC"
            
            # PREXO (PRX)
            if any(term in raw_upper for term in ["PREXO", "PRX", "EXCHANGE", "UPGRADE", "BUP", "BUMP", "SS_PRX", "SS-PRX"]):
                return "PRX"
            
            # BANK_OFFER (BOC)
            if any(term in raw_upper for term in ["BANK", "CARD", "EMI", "HDFC", "ICICI", "AXIS", "SS_BOC", "SS-BOC", "BOC"]):
                return "BOC"
            
            # LIFESTYLE (LS)
            if any(term in raw_upper for term in ["LIFESTYLE", "LS", "SS_LS", "SS-LS"]):
                return "LS"
            
            # Default for SELL_SIDE
            return "PUC"
        
        # Final fallback
        if scheme_type == "BUY_SIDE":
            return "PERIODIC_CLAIM"
        elif scheme_type == "SELL_SIDE":
            return "PUC"
        
        return Config.DEFAULT_SCHEME_SUBTYPE
    
    def _log_field_reasoning(self, result):
        """
        Log reasoning for each extracted field.
        
        Args:
            result: DSPy ChainOfThought result
        """
        # Extract fields and their reasoning (excluding scheme_type/subtype which is logged separately)
        field_mappings = [
            ("scheme_name", "scheme_name_reasoning"),
            ("scheme_description", "scheme_description_reasoning"),
            ("additional_conditions", "additional_conditions_reasoning"),
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
            ("scheme_document", "scheme_document_reasoning"),
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
        Uses LLM-extracted scheme_type and scheme_subtype.
        
        Args:
            result: DSPy extraction result
            scheme_type: LLM-classified scheme type (normalized)
            scheme_subtype: LLM-classified scheme subtype (normalized)
        
        Returns:
            Dictionary with 21 fields
        """
        # Apply conditional logic based on LLM-determined scheme type
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
        
        # Build final JSON with all 21 fields
        output = {
            "scheme_type": scheme_type,
            "scheme_subtype": scheme_subtype,
            "scheme_name": getattr(result, "scheme_name", "Unnamed Scheme"),
            "scheme_description": getattr(result, "scheme_description", "Details not specified"),
            "additional_conditions": getattr(result, "additional_conditions", "None specified"),
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
            "scheme_document": getattr(result, "scheme_document", "No"),
            "discount_slab_type": discount_slab,
            "best_bet": best_bet,
            "brand_support_absolute": brand_support,
            "gst_rate": gst_rate,
            "classification_reasoning": getattr(result, "scheme_classification_reasoning", "")
        }
        
        return output
