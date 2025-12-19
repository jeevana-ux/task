"""
DSPy Field Extraction Module
Clean, minimal implementation leveraging DSPy Chain-of-Thought for all 20 fields.
"""
import re
from datetime import datetime
from typing import Dict, Tuple
import dspy

from .signatures import SchemeExtractionSignature
from ..logger import FieldLevelLogger
from ..config import Config


class RetailerHubFieldExtractor:
    """
    Minimal DSPy-based field extractor.
    Trusts LLM outputs from Chain-of-Thought reasoning.
    """
    
    def __init__(self, logger: FieldLevelLogger):
        """Initialize with logger and DSPy ChainOfThought module."""
        self.logger = logger
        self.demos_loaded = []  # Store for logging
        
        # Try to load optimized program
        optimized_path = Config.PROJECT_ROOT / "src" / "dspy_modules" / "optimized_extractor.json"
        
        # Initialize the ChainOfThought module
        self.cot_extractor = dspy.ChainOfThought(SchemeExtractionSignature)
        
        if optimized_path.exists():
            self.logger.info("Loading optimized DSPy module (Few-Shot)...")
            
            try:
                # Standard DSPy pattern: Load saved state directly
                self.cot_extractor.load(str(optimized_path))
                
                # Extract demos for logging purposes
                demos = []
                if hasattr(self.cot_extractor, 'demos') and self.cot_extractor.demos:
                    demos = self.cot_extractor.demos
                elif hasattr(self.cot_extractor, 'predict') and hasattr(self.cot_extractor.predict, 'demos'):
                    demos = self.cot_extractor.predict.demos or []
                
                self.demos_loaded = demos
                
                if demos:
                    total_chars = sum(len(str(getattr(d, 'email_text', ''))) for d in demos)
                    self.logger.info(f"Loaded {len(demos)} few-shot examples (total input chars: {total_chars})")
                else:
                    self.logger.warning("Optimized file loaded but no demos found - using Zero-Shot")
                    
            except Exception as e:
                self.logger.warning(f"Failed to load optimized module: {e}")
                self.logger.info("Falling back to Zero-Shot mode...")
                self.cot_extractor = dspy.ChainOfThought(SchemeExtractionSignature)
        else:
            self.logger.info("Using default DSPy module (Zero-Shot)...")
    
    # Valid field mapping for reasoning extraction
    FIELD_REASONING_MAP = {
        
        "scheme_type": "scheme_type_reasoning",
        "scheme_subtype": "scheme_subtype_reasoning",
        "scheme_name": "scheme_name_reasoning",
        "scheme_description": "scheme_description_reasoning",
        "scheme_period": "scheme_period_reasoning",
        "duration": "duration_reasoning",
        "discount_type": "discount_type_reasoning",
        "max_cap": "max_cap_reasoning",
        "vendor_name": "vendor_name_reasoning",
        "price_drop_date": "price_drop_date_reasoning",
        "start_date": "start_date_reasoning",
        "end_date": "end_date_reasoning",
        "fsn_file_config_file": "fsn_file_config_file_reasoning",
        "min_actual_discount_or_agreed_claim": "min_discount_reasoning",
        "remove_gst_from_final_claim": "remove_gst_reasoning",
        "over_and_above": "over_and_above_reasoning",
        "scheme_document": "scheme_document_reasoning",
        "discount_slab_type": "discount_slab_type_reasoning",
        "best_bet": "best_bet_reasoning",
        "brand_support_absolute": "brand_support_absolute_reasoning",
        "gst_rate": "gst_rate_reasoning"
    }

    def extract_fields(
        self,
        email_text: str,
        table_data: str = "",
        xlsx_data: str = ""
    ) -> Dict:
        """
        Extract all fields using DSPy Chain-of-Thought.
        Returns tuple: (final_output_json, full_reasoning_json, token_stats)
        """
        self.logger.section("LLM Field Extraction with DSPy Chain-of-Thought")
        
        # Log input context
        self.logger.log_input_context(
            email_text=email_text,
            table_data=table_data or "No table data",
            xlsx_data=xlsx_data or "No XLSX data"
        )
        
        # Log active Few-Shot Status
        is_few_shot = False
        num_demos = 0
        
        if hasattr(self.cot_extractor, 'demos') and self.cot_extractor.demos:
             is_few_shot = True
             num_demos = len(self.cot_extractor.demos)
        elif hasattr(self.cot_extractor, 'predict') and hasattr(self.cot_extractor.predict, 'demos') and self.cot_extractor.predict.demos:
             is_few_shot = True
             num_demos = len(self.cot_extractor.predict.demos)

        if is_few_shot:
             self.logger.info(f"✨ Using {num_demos} Few-Shot Examples in Prompt", console_only=True)
             
             demos_to_log = []
             if hasattr(self.cot_extractor, 'demos'): 
                 demos_to_log = self.cot_extractor.demos
             elif hasattr(self.cot_extractor, 'predict') and hasattr(self.cot_extractor.predict, 'demos'): 
                 demos_to_log = self.cot_extractor.predict.demos
                 
             self.logger.log_few_shot_context(demos_to_log)
        else:
             self.logger.info("ℹ Using Zero-Shot (No examples loaded)", console_only=True)
             self.logger.debug(f"COT Extractor vars: {vars(self.cot_extractor).keys()}")
        
        try:
            # Call DSPy Chain-of-Thought
            result = self.cot_extractor(
                email_text=email_text,
                table_data=table_data or "No table data available",
                xlsx_data=xlsx_data or "No XLSX data provided"
            )
            
            # Capture actual token usage
            token_stats = self._get_actual_token_usage()
            
            # Extract fields AND reasoning
            fields, reasoning_data = self._extract_all_fields_with_reasoning(result)
            
            # Log extractions
            self._log_extractions(result, fields)
            
            # Build final output
            output = self._build_output(fields)
            self.logger.log_final_output(output)
            
            return output, reasoning_data, token_stats
            
        except Exception as e:
            self.logger.error(f"DSPy extraction failed: {str(e)}")
            raise
    
    def _get_actual_token_usage(self) -> Dict:
        """
        Get actual token usage from DSPy's LM history.
        This captures the real prompt size including few-shot examples.
        
        Note: In few-shot prompting, assistant messages from demos are INPUT (context),
        only the LAST assistant message is the actual OUTPUT.
        """
        try:
            lm = dspy.settings.lm
            if not hasattr(lm, 'history') or not lm.history:
                return {"input_tokens": 0, "output_tokens": 0, "total_chars": 0}
            
            last_call = lm.history[-1]
            messages = last_call.get('messages', [])
            
            if not messages:
                return {"input_tokens": 0, "output_tokens": 0, "total_chars": 0}
            
            # Find the LAST assistant message (this is the actual output)
            # All other messages (including previous assistant msgs from demos) are input
            total_input_chars = 0
            actual_output_chars = 0
            
            # Find index of last assistant message
            last_assistant_idx = -1
            for i, msg in enumerate(messages):
                if msg.get('role') == 'assistant':
                    last_assistant_idx = i
            
            for i, msg in enumerate(messages):
                content = msg.get('content', '')
                if i == last_assistant_idx:
                    # This is the actual LLM output
                    actual_output_chars = len(content)
                else:
                    # Everything else (including demo assistant msgs) is input
                    total_input_chars += len(content)
            
            # Estimate tokens (roughly 4 chars per token)
            input_tokens = total_input_chars // 4
            output_tokens = actual_output_chars // 4
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_chars": total_input_chars + actual_output_chars,
                "input_chars": total_input_chars,
                "output_chars": actual_output_chars
            }
        except Exception as e:
            self.logger.debug(f"Could not get actual token usage: {e}")
            return {"input_tokens": 0, "output_tokens": 0, "total_chars": 0}

    def _extract_all_fields_with_reasoning(self, result) -> Tuple[Dict, Dict]:
        """
        Extract values and reasoning from DSPy result.
        Returns: (fields_dict, reasoning_dict)
        """
        fields = {
            # Core classification
            "scheme_type": getattr(result, "scheme_type", "SELL_SIDE").strip(),
            "scheme_subtype": getattr(result, "scheme_subtype", "PUC").strip(),
            
            # Descriptive fields
            "scheme_name": getattr(result, "scheme_name", "Unnamed Scheme"),
            "scheme_description": getattr(result, "scheme_description", "Not specified"),
            "vendor_name": getattr(result, "vendor_name", "Unknown Vendor"),
            
            # Scheme structure
            "scheme_period": getattr(result, "scheme_period", Config.DEFAULT_SCHEME_PERIOD),
            "duration": getattr(result, "duration", "Not Specified"),
            "discount_type": getattr(result, "discount_type", "Not Specified"),
            "max_cap": getattr(result, "max_cap", "No Cap"),
            
            # Dates (normalized)
            "price_drop_date": self._normalize_date(getattr(result, "price_drop_date", "N/A")),
            "start_date": self._normalize_date(getattr(result, "start_date", "Not Specified")),
            "end_date": self._normalize_date(getattr(result, "end_date", "Not Specified")),
            
            # Config flags
            "fsn_file_config_file": getattr(result, "fsn_file_config_file", Config.DEFAULT_FSN_FILE),
            "min_actual_discount_or_agreed_claim": getattr(result, "min_actual_discount_or_agreed_claim", Config.DEFAULT_MIN_DISCOUNT_CLAIM),
            "remove_gst_from_final_claim": getattr(result, "remove_gst_from_final_claim", Config.DEFAULT_REMOVE_GST),
            "over_and_above": getattr(result, "over_and_above", Config.DEFAULT_OVER_ABOVE),
            "scheme_document": getattr(result, "scheme_document", "No"),
            
            # Conditional
            "discount_slab_type": getattr(result, "discount_slab_type", "Not Applicable"),
            "best_bet": getattr(result, "best_bet", "Not Applicable"),
            "brand_support_absolute": getattr(result, "brand_support_absolute", "Not Applicable"),
            "gst_rate": getattr(result, "gst_rate", "Not Applicable")
        }
        
        # Extract Reasoning Map
        reasoning_data = {}
        for field, reasoning_field in self.FIELD_REASONING_MAP.items():
            value = fields.get(field, "N/A")
            reasoning = getattr(result, reasoning_field, "No reasoning provided")
            confidence = self._assess_confidence(value, reasoning)
            
            reasoning_data[field] = {
                "value": value,
                "reasoning": reasoning,
                "confidence": confidence
            }
            
        # Add high-level reasoning
        reasoning_data["global_reasoning"] = getattr(result, "reasoning", "No global reasoning")
            
        return fields, reasoning_data
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Normalize date to DD/MM/YYYY format.
        Handles various input formats from LLM.
        """
        if not date_str or date_str.lower() in ["not specified", "n/a", "none", "not found"]:
            return "N/A"
        
        date_str = date_str.strip()
        
        # Already in correct format?
        if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
            return date_str
        
        # Try common date formats
        formats = [
            "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y",
            "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue
        
        # Regex fallback
        match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
        if match:
            d, m, y = match.groups()
            return f"{int(d):02d}/{int(m):02d}/{y}"
        
        return date_str  # Return as-is if can't parse
    
    def _log_extractions(self, result, fields: Dict):
        """Log all field extractions with reasoning."""
        
        # Field mapping (field_name -> reasoning_field_name)
        field_reasoning_map = {
            "scheme_type": "scheme_type_reasoning",
            "scheme_subtype": "scheme_subtype_reasoning",
            "scheme_name": "scheme_name_reasoning",
            "scheme_description": "scheme_description_reasoning",
            "scheme_period": "scheme_period_reasoning",
            "duration": "duration_reasoning",
            "discount_type": "discount_type_reasoning",
            "max_cap": "max_cap_reasoning",
            "vendor_name": "vendor_name_reasoning",
            "price_drop_date": "price_drop_date_reasoning",
            "start_date": "start_date_reasoning",
            "end_date": "end_date_reasoning",
            "fsn_file_config_file": "fsn_file_config_file_reasoning",
            "min_actual_discount_or_agreed_claim": "min_discount_reasoning",
            "remove_gst_from_final_claim": "remove_gst_reasoning",
            "over_and_above": "over_and_above_reasoning",
            "scheme_document": "scheme_document_reasoning",
            "discount_slab_type": "discount_slab_reasoning",
            "best_bet": "best_bet_reasoning",
            "brand_support_absolute": "brand_support_reasoning",
            "gst_rate": "gst_rate_reasoning"
        }
        
        for field_name, reasoning_attr in field_reasoning_map.items():
            if field_name in fields:
                reasoning = getattr(result, reasoning_attr, "No reasoning provided")
                confidence = self._assess_confidence(fields[field_name], reasoning)
                
                self.logger.log_field_extraction(
                    field_name=field_name,
                    input_snippet="See full context in log",
                    reasoning=reasoning,
                    output_value=fields[field_name],
                    confidence=confidence
                )
    
    def _assess_confidence(self, value: str, reasoning: str) -> str:
        """Simple confidence heuristic based on value and reasoning."""
        value_lower = str(value).lower()
        
        # Low confidence indicators
        if any(term in value_lower for term in ["not specified", "not found", "n/a", "unknown"]):
            return "Low"
        
        # Medium if reasoning is brief
        if len(str(reasoning)) < 50:
            return "Medium"
        
        return "High"
    
    def _build_output(self, fields: Dict) -> Dict:
        """
        Build final 20-field output JSON.
        Applies conditional logic based on scheme type.
        """
        scheme_type = fields["scheme_type"]
        scheme_subtype = fields["scheme_subtype"]
        
        # Apply conditional field rules
        if scheme_type == "BUY_SIDE" and scheme_subtype == "PERIODIC_CLAIM":
            # Keep discount_slab_type and best_bet as extracted
            pass
        else:
            fields["discount_slab_type"] = "Not Applicable"
            fields["best_bet"] = "Not Applicable"
        
        if scheme_type == "OFC":
            # Keep brand_support_absolute and gst_rate as extracted
            pass
        else:
            fields["brand_support_absolute"] = "Not Applicable"
            fields["gst_rate"] = "Not Applicable"
        
        if scheme_subtype != "PDC":
            fields["price_drop_date"] = "N/A"
        
        # Return clean output (exclude internal reasoning from final JSON)
        output = {k: v for k, v in fields.items() if k != "classification_reasoning"}
        return output
