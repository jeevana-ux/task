"""
Configuration Generator for Retailer Hub
Generates scheme-specific configuration JSONs using LLM-extracted fields.
"""
from typing import Dict, Any, List

class ConfigGenerator:
    """
    Generates FSN/Scheme Configuration files based on scheme classification.
    Now uses LLM-extracted config_ fields for actual values instead of placeholders.
    """
    
    @staticmethod
    def generate_config(fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the configuration JSON structure based on scheme type and subtype.
        Uses LLM-extracted config_* fields for actual values.
        """
        scheme_type = fields.get("scheme_type", "")
        scheme_subtype = fields.get("scheme_subtype", "")
        
        # Handle PDC as standalone
        if scheme_type == "PDC":
            return ConfigGenerator._gen_PDC(fields)
        
        # Normalize keys for lookup
        key = f"{scheme_type}_{scheme_subtype}"
        
        # BS-PC (Buy_side - Periodic_claim)
        if hasattr(ConfigGenerator, f"_gen_{scheme_type}_{scheme_subtype}"):
            generator = getattr(ConfigGenerator, f"_gen_{scheme_type}_{scheme_subtype}")
            return generator(fields)
            
        # Fallback/Generic handler
        if scheme_type == "BUY_SIDE":
            if scheme_subtype == "PERIODIC_CLAIM":
                return ConfigGenerator._gen_BUY_SIDE_PERIODIC_CLAIM(fields)
            if scheme_subtype == "PDC":
                return ConfigGenerator._gen_BUY_SIDE_PDC(fields)
                
        if scheme_type == "SELL_SIDE":
            if scheme_subtype == "CP":
                return ConfigGenerator._gen_SELL_SIDE_CP(fields)
            if scheme_subtype == "PUC":
                return ConfigGenerator._gen_SELL_SIDE_PUC(fields)
            if scheme_subtype == "PRX":
                return ConfigGenerator._gen_SELL_SIDE_PRX(fields)
            if scheme_subtype == "SC": # Super Coin
                 return ConfigGenerator._gen_SELL_SIDE_SC(fields)
            if scheme_subtype == "LS": # Lifestyle
                 return ConfigGenerator._gen_SELL_SIDE_LS(fields)

        if scheme_type == "OFC":
             return {"info": "No FSN Config required for OFC"}

        return {"error": f"Unknown scheme configuration for {scheme_type} - {scheme_subtype}"}

    @staticmethod
    def _get_config_field(fields: Dict, config_key: str, fallback: str = "Not specified") -> str:
        """Helper to get LLM-extracted config field with fallback."""
        value = fields.get(config_key, fallback)
        return value if value else fallback

    @staticmethod
    def _gen_PDC(fields: Dict) -> Dict:
        """Generate config for PDC (Price Drop Claim) - standalone scheme type"""
        return {
            "config_type": "PDC",
            "extraction_source": "LLM",
            "fields": {
                "ProductId": "Populate from FSN File",
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "maxQuantity": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "priceDropDate": fields.get("price_drop_date", "N/A"),
                "maxSupportValue": ConfigGenerator._get_config_field(fields, "config_max_support_value", "No Cap")
            }
        }

    @staticmethod
    def _gen_BUY_SIDE_PERIODIC_CLAIM(fields: Dict) -> Dict:
        return {
            "config_type": "BS-PC",
            "extraction_source": "LLM",
            "fields": {
                "ProductId": "Populate from FSN File",
                "unitSlabLower": ConfigGenerator._get_config_field(fields, "config_unit_slab_lower", "0"),
                "unitSlabUpper": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "maxSupportValue": ConfigGenerator._get_config_field(fields, "config_max_support_value", "No Cap"),
                "bestBetQuantity": fields.get("best_bet", "N/A")
            }
        }

    @staticmethod
    def _gen_BUY_SIDE_PDC(fields: Dict) -> Dict:
        return {
            "config_type": "BS-PDC",
            "extraction_source": "LLM",
            "fields": {
                "ProductId": "Populate from FSN File",
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "maxQuantity": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "maxSupportValue": ConfigGenerator._get_config_field(fields, "config_max_support_value", "No Cap")
            }
        }

    @staticmethod
    def _gen_SELL_SIDE_CP(fields: Dict) -> Dict:
        return {
            "config_type": "SS-CP",
            "extraction_source": "LLM",
            "fields": {
                "ProductId": "Populate from FSN File",
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "vendorSplitRatio": ConfigGenerator._get_config_field(fields, "config_vendor_split_ratio")
            }
        }

    @staticmethod
    def _gen_SELL_SIDE_PUC(fields: Dict) -> Dict:
        return {
            "config_type": "SS-PUC",
            "extraction_source": "LLM",
            "fields": {
                "ProductId": "Populate from FSN File",
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "vendorSplitRatio": ConfigGenerator._get_config_field(fields, "config_vendor_split_ratio"),
                "unitSlabLower": ConfigGenerator._get_config_field(fields, "config_unit_slab_lower", "0"),
                "unitSlabUpper": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "maxSupportValue": ConfigGenerator._get_config_field(fields, "config_max_support_value", "No Cap"),
                "margin": ConfigGenerator._get_config_field(fields, "config_margin")
            }
        }

    @staticmethod
    def _gen_SELL_SIDE_PRX(fields: Dict) -> Dict:
        return {
            "config_type": "SS-PRX",
            "extraction_source": "LLM",
            "fields": {
                "ProductId": "Populate from FSN File",
                "incomingFsn": "Populate from Exchange FSN File",
                "vendorSplitRatio": ConfigGenerator._get_config_field(fields, "config_vendor_split_ratio"),
                "exchangeSlabFrom": ConfigGenerator._get_config_field(fields, "config_unit_slab_lower", "0"),
                "exchangeSlabTo": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "agreedSupport": ConfigGenerator._get_config_field(fields, "config_brand_support")
            }
        }
        
    @staticmethod
    def _gen_SELL_SIDE_SC(fields: Dict) -> Dict:
        return {
             "config_type": "SS-SC",
             "extraction_source": "LLM",
             "fields": {
                 "ProductId": "Populate from FSN File",
                 "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support")
             }
        }

    @staticmethod
    def _gen_SELL_SIDE_LS(fields: Dict) -> Dict:
        return {
            "config_type": "SS-LS",
            "extraction_source": "LLM",
            "description": "Lifestyle Scheme - DMRP details may need manual population from DMRP file",
            "fields": {
                "ProductId": "Populate from FSN File",
                "unitSlabLower": ConfigGenerator._get_config_field(fields, "config_unit_slab_lower", "0"),
                "unitSlabUpper": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "vendorSplitRatio": ConfigGenerator._get_config_field(fields, "config_vendor_split_ratio"),
                "margin": ConfigGenerator._get_config_field(fields, "config_margin"),
                "dmrpType": "Manual - From DMRP File",
                "dmrpValue": "Manual - From DMRP File",
                "maxSupportValue": ConfigGenerator._get_config_field(fields, "config_max_support_value", 
                                  fields.get("min_actual_discount_or_agreed_claim", "N/A"))
            }
        }
