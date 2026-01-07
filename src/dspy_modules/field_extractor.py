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
        "gst_rate": "gst_rate_reasoning",
        # FSN Config fields (extracted in same LLM call)
        "config_brand_support": "config_brand_support_reasoning",
        "config_vendor_split_ratio": "config_vendor_split_reasoning",
        "config_unit_slab_lower": "config_slab_reasoning",
        "config_unit_slab_upper": "config_slab_reasoning",
        "config_max_support_value": "config_max_support_reasoning",
        "config_margin": "config_margin_reasoning"
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
            # --- TOKEN OPTIMIZATION: Truncate large inputs ---
            # Most table/xlsx data is redundant after the first few rows for RULE extraction.
            def truncate(text, max_lines=50):
                if not text: return text
                lines = text.splitlines()
                if len(lines) > max_lines:
                    return "\n".join(lines[:max_lines]) + "\n... [TRUNCATED FOR TOKEN EFFICIENCY]"
                return text

            # Truncate Table and XLSX data to 50 lines each
            optimized_table = truncate(table_data or "No table data available")
            optimized_xlsx = truncate(xlsx_data or "No XLSX data provided")
            
            self.logger.info(f"Inputs Optimized: Email ({len(email_text)} ch) | Table ({len(optimized_table)} ch) | XLSX ({len(optimized_xlsx)} ch)", console_only=True)

            # Call DSPy Chain-of-Thought
            result = self.cot_extractor(
                email_text=email_text,
                table_data=optimized_table,
                xlsx_data=optimized_xlsx
            )
            
            # Capture actual token usage
            token_stats = self._get_actual_token_usage()
            
            # Check if response was truncated (common issue with Few-Shot)
            if hasattr(result, 'scheme_type') and result.scheme_type is None:
                self.logger.warning("⚠️  LLM response appears truncated. Consider increasing --max-tokens (current: {})".format(Config.MAX_TOKENS))
                self.logger.warning("   Recommendation: --max-tokens 8000 or higher for Few-Shot mode with config fields")
            
            # Extract ALL fields AND reasoning (includes config_* fields)
            all_fields, reasoning_data = self._extract_all_fields_with_reasoning(result)
            
            # STIRCT DETERMINISTIC OVERRIDES (Apply based on raw text keywords)
            # 1. Price Drop Overrides
            pdc_keywords = ["price drop", "permanent price drop", "nlc reduction", "cost reduction", "price protection"]
            if any(kw in email_text.lower() for kw in pdc_keywords):
                all_fields["scheme_type"] = "PDC"
                all_fields["scheme_subtype"] = "PDC"
                self.logger.info("⚡ Strict Override: 'Price Drop' keywords detected. Forcing PDC-PDC.", console_only=True)
                # Inject reasoning
                if "scheme_type" in reasoning_data:
                    reasoning_data["scheme_type"]["value"] = "PDC"
                    reasoning_data["scheme_type"]["reasoning"] = "Strict Rule: 'Price Drop' keywords found in email text."
                if "scheme_subtype" in reasoning_data:
                    reasoning_data["scheme_subtype"]["value"] = "PDC"
                    reasoning_data["scheme_subtype"]["reasoning"] = "Strict Rule: 'Price Drop' keywords found in email text."

            # 2. Exchange Overrides (Only if not already PDC)
            if all_fields["scheme_type"] != "PDC":
                exchange_keywords = ["exchange", "prexo", "upgrade", "buyback", "bup", "prexo bumpup"]
                if any(kw in email_text.lower() for kw in exchange_keywords):
                    all_fields["scheme_type"] = "SELL_SIDE"
                    all_fields["scheme_subtype"] = "PRX"
                    self.logger.info("⚡ Strict Override: 'Exchange' keywords detected. Forcing SELL_SIDE-PRX.", console_only=True)
                    # Inject reasoning
                    if "scheme_type" in reasoning_data:
                        reasoning_data["scheme_type"]["value"] = "SELL_SIDE"
                        reasoning_data["scheme_type"]["reasoning"] = "Strict Rule: 'Exchange' keywords found in email text."
                    if "scheme_subtype" in reasoning_data:
                        reasoning_data["scheme_subtype"]["value"] = "PRX"
                        reasoning_data["scheme_subtype"]["reasoning"] = "Strict Rule: 'Exchange' keywords found in email text."

            # 3. LIFESTYLE (LS) STRICT OVERRIDES (Higher priority than general intent)
            ls_keywords = ["sor", "sor pricing", "sor discounts", "monsoon sale", "monsoon", "fashion", "lifestyle", "clothing", "apparel"]
            ls_vendors = [
                "aditya birla", "mgi distribution", "brand concepts", "timex", "titan", 
                "metro brands", "sumitsu", "sea turtle", 
                "beewakoof", "highlander", "leemboodi"
            ]
            
            email_lower = email_text.lower()
            vendor_lower = all_fields.get("vendor_name", "").lower()
            
            is_ls_vendor = any(v in vendor_lower for v in ls_vendors)
            has_ls_keyword = any(kw in email_lower for kw in ls_keywords)
            
            if (is_ls_vendor or has_ls_keyword) and all_fields["scheme_type"] not in ["PDC", "OFC"]:
                all_fields["scheme_type"] = "SELL_SIDE"
                all_fields["scheme_subtype"] = "LS"
                self.logger.info(f"⚡ Strict Override: Lifestyle Detection (Vendor: {is_ls_vendor}, Keywords: {has_ls_keyword}). Forcing SELL_SIDE-LS.", console_only=True)
                # Inject reasoning
                if "scheme_type" in reasoning_data:
                    reasoning_data["scheme_type"]["value"] = "SELL_SIDE"
                    reasoning_data["scheme_type"]["reasoning"] = f"Strict Rule: Lifestyle trigger (Keyword or Vendor match: {vendor_lower})."
                if "scheme_subtype" in reasoning_data:
                    reasoning_data["scheme_subtype"]["value"] = "LS"
                    reasoning_data["scheme_subtype"]["reasoning"] = f"Strict Rule: Lifestyle trigger (Keyword or Vendor match: {vendor_lower})."

            # Log extractions
            self._log_extractions(result, all_fields)
            
            # Build filtered output for Auto-Punch JSON (excludes config_* fields)
            output = self._build_output(all_fields)
            self.logger.log_final_output(output)
            
            # Return: output (filtered), reasoning, tokens, AND full fields (for config generation)
            return output, reasoning_data, token_stats, all_fields
            
        except Exception as e:
            self.logger.error(f"DSPy extraction failed: {str(e)}")
            raise
    
    def _get_actual_token_usage(self) -> Dict:
        """
        Get actual token usage from DSPy's LM history.
        This captures the real prompt size including few-shot examples.
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
            total_input_chars = 0
            actual_output_chars = 0
            
            last_assistant_idx = -1
            for i, msg in enumerate(messages):
                if msg.get('role') == 'assistant':
                    last_assistant_idx = i
            
            for i, msg in enumerate(messages):
                content = msg.get('content', '')
                if i == last_assistant_idx:
                    actual_output_chars = len(content)
                else:
                    total_input_chars += len(content)
            
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
        def safe_get(attr_name, default=""):
            value = getattr(result, attr_name, default)
            if value is None:
                return default
            return str(value).strip() if hasattr(value, 'strip') else str(value)
        
        fields = {
            "scheme_type": safe_get("scheme_type", "SELL_SIDE"),
            "scheme_subtype": safe_get("scheme_subtype", "PUC"),
            "scheme_name": safe_get("scheme_name", "Unnamed Scheme"),
            "scheme_description": safe_get("scheme_description", "Not specified"),
            "vendor_name": safe_get("vendor_name", "Unknown Vendor"),
            "scheme_period": safe_get("scheme_period", Config.DEFAULT_SCHEME_PERIOD),
            "duration": safe_get("duration", "Not Specified"),
            "discount_type": safe_get("discount_type", "Not Specified"),
            "max_cap": safe_get("max_cap", "No Cap"),
            "price_drop_date": self._normalize_date(safe_get("price_drop_date", "N/A")),
            "start_date": self._normalize_date(safe_get("start_date", "Not Specified")),
            "end_date": self._normalize_date(safe_get("end_date", "Not Specified")),
            "fsn_file_config_file": safe_get("fsn_file_config_file", Config.DEFAULT_FSN_FILE),
            "min_actual_discount_or_agreed_claim": safe_get("min_actual_discount_or_agreed_claim", Config.DEFAULT_MIN_DISCOUNT_CLAIM),
            "remove_gst_from_final_claim": safe_get("remove_gst_from_final_claim", Config.DEFAULT_REMOVE_GST),
            "over_and_above": safe_get("over_and_above", Config.DEFAULT_OVER_ABOVE),
            "scheme_document": safe_get("scheme_document", "No"),
            "discount_slab_type": safe_get("discount_slab_type", "Not Applicable"),
            "best_bet": safe_get("best_bet", "Not Applicable"),
            "brand_support_absolute": safe_get("brand_support_absolute", "Not Applicable"),
            "gst_rate": safe_get("gst_rate", "Not Applicable"),
            "config_brand_support": safe_get("config_brand_support", "Not specified in email"),
            "config_vendor_split_ratio": safe_get("config_vendor_split_ratio", "Not specified"),
            "config_unit_slab_lower": safe_get("config_unit_slab_lower", "0"),
            "config_unit_slab_upper": safe_get("config_unit_slab_upper", "999999"),
            "config_max_support_value": safe_get("config_max_support_value", "No Cap"),
            "config_margin": safe_get("config_margin", "Not specified")
        }
        
        if fields["scheme_subtype"] == "PDC":
            fields["scheme_type"] = "PDC"
            
        st_val = fields.get("scheme_type", "").upper()
        sst_val = fields.get("scheme_subtype", "").upper()
        
        if st_val == "BUY_SIDE" and sst_val == "PERIODIC_CLAIM":
            fields["discount_slab_type"] = "notApplicable"
            fields["best_bet"] = "FALSE"
            setattr(result, "discount_slab_type_reasoning", "Fixed constant 'notApplicable' enforced for BUY_SIDE PERIODIC_CLAIM per business rules.")
            setattr(result, "best_bet_reasoning", "Fixed constant 'FALSE' enforced for BUY_SIDE PERIODIC_CLAIM per business rules.")
            self.logger.debug("Applied strict overrides and updated reasoning for BUY_SIDE PERIODIC_CLAIM")
            
        if fields.get("scheme_subtype") == "BOC":
            fields["scheme_subtype"] = "PUC"
            self.logger.warning("⚡ Deprecated Subtype: 'BOC' detected. Automatically converted to 'PUC'.")
            setattr(result, "scheme_subtype_reasoning", f"(AUTO-CONVERTED FROM BOC) {getattr(result, 'scheme_subtype_reasoning', '')}")

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
            
        reasoning_data["global_reasoning"] = getattr(result, "reasoning", "No global reasoning")
        return fields, reasoning_data
    
    def _normalize_date(self, date_str: str) -> str:
        if not date_str or date_str.lower() in ["not specified", "n/a", "none", "not found"]:
            return "N/A"
        date_str = date_str.strip()
        if re.match(r"^\d{2}/\d{2}/\d{4}$", date_str):
            return date_str
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue
        match = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", date_str)
        if match:
            d, m, y = match.groups()
            return f"{int(d):02d}/{int(m):02d}/{y}"
        return date_str
    
    def _log_extractions(self, result, fields: Dict):
        for field_name, reasoning_attr in self.FIELD_REASONING_MAP.items():
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
        if value is None: value = ""
        if reasoning is None: reasoning = ""
        value_lower = str(value).lower()
        if any(term in value_lower for term in ["not specified", "not found", "n/a", "unknown"]):
            return "Low"
        reasoning_str = str(reasoning) if reasoning else ""
        if len(reasoning_str) < 50:
            return "Medium"
        return "High"
    
    def _build_output(self, fields: Dict) -> Dict:
        scheme_type = fields.get("scheme_type", "SELL_SIDE")
        scheme_subtype = fields.get("scheme_subtype", "PUC")
        base_fields = ["scheme_type", "scheme_subtype", "scheme_name", "scheme_description", "scheme_period", "duration", "discount_type", "vendor_name", "start_date", "end_date"]
        final_output = {k: fields.get(k) for k in base_fields}
        def add_field(key): final_output[key] = fields.get(key)
        if scheme_type not in ["OFC"]: add_field("fsn_file_config_file")
        if scheme_type == "OFC": add_field("max_cap")
        if scheme_type == "PDC" or (scheme_type == "BUY_SIDE" and scheme_subtype == "PDC"): add_field("price_drop_date")
        if scheme_type == "SELL_SIDE" and scheme_subtype in ["LS", "PUC"]: add_field("min_actual_discount_or_agreed_claim")
        if scheme_type == "PDC" or (scheme_type == "BUY_SIDE" and scheme_subtype in ["PERIODIC_CLAIM", "PDC"]) or (scheme_type == "SELL_SIDE" and scheme_subtype in ["CP", "PRX", "PUC", "SC"]) or (scheme_type == "OFC"): add_field("remove_gst_from_final_claim")
        if scheme_type == "PDC" or (scheme_type == "BUY_SIDE" and scheme_subtype in ["PERIODIC_CLAIM", "PDC"]) or (scheme_type == "SELL_SIDE" and scheme_subtype in ["CP", "LS", "PRX", "PUC", "SC"]): add_field("over_and_above")
        if scheme_type == "BUY_SIDE" and scheme_subtype == "PERIODIC_CLAIM": add_field("discount_slab_type")
        if scheme_type == "BUY_SIDE" and scheme_subtype == "PERIODIC_CLAIM": add_field("best_bet")
        if scheme_type == "OFC": add_field("brand_support_absolute")
        if scheme_type == "OFC": add_field("gst_rate")
        return final_output
