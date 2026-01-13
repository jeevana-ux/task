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
    def generate_config(fields: Dict[str, Any], enrichment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate the configuration JSON structure based on scheme type and subtype.
        Uses LLM-extracted config_* fields AND enriched mapping data.
        """
        scheme_type = fields.get("scheme_type", "")
        scheme_subtype = fields.get("scheme_subtype", "")
        
        # Merge enrichment data into fields for convenience in generators
        if enrichment_data:
            fields = {**fields, **enrichment_data}
            
        # Handle multiple FSNs if present
        resolve_fsns = fields.get("resolved_fsns")
        if not resolve_fsns:
            resolve_fsns = ["Populate from FSN File"]
        
        # Generator result
        config_result = {}
        
        # Handle PDC as standalone
        if scheme_type == "PDC":
            config_result = ConfigGenerator._gen_PDC(fields)
        
        # BS-PC (Buy_side - Periodic_claim)
        elif hasattr(ConfigGenerator, f"_gen_{scheme_type}_{scheme_subtype}"):
            generator = getattr(ConfigGenerator, f"_gen_{scheme_type}_{scheme_subtype}")
            config_result = generator(fields)
            
        # Fallback/Generic handler
        elif scheme_type == "BUY_SIDE":
            if scheme_subtype == "PERIODIC_CLAIM":
                config_result = ConfigGenerator._gen_BUY_SIDE_PERIODIC_CLAIM(fields)
            elif scheme_subtype == "PDC":
                config_result = ConfigGenerator._gen_BUY_SIDE_PDC(fields)
                
        elif scheme_type == "SELL_SIDE":
            if scheme_subtype == "CP":
                config_result = ConfigGenerator._gen_SELL_SIDE_CP(fields)
            elif scheme_subtype == "PUC":
                config_result = ConfigGenerator._gen_SELL_SIDE_PUC(fields)
            elif scheme_subtype == "PRX":
                config_result = ConfigGenerator._gen_SELL_SIDE_PRX(fields)
            elif scheme_subtype == "SC": # Super Coin
                 config_result = ConfigGenerator._gen_SELL_SIDE_SC(fields)
            elif scheme_subtype == "LS": # Lifestyle
                 config_result = ConfigGenerator._gen_SELL_SIDE_LS(fields)

        elif scheme_type == "OFC":
             return {"info": "No FSN Config required for OFC"}

        else:
            return {"error": f"Unknown scheme configuration for {scheme_type} - {scheme_subtype}"}

        # Multi-product handling: if resolved_fsns has multiple, we duplicate the fields block per product
        if "fields" in config_result and isinstance(config_result["fields"], dict):
            base_fields = config_result["fields"]
            product_list = []
            for fsn in resolve_fsns:
                p_fields = base_fields.copy()
                p_fields["ProductId"] = fsn
                product_list.append(p_fields)
            
            # If only one FSN, keep it simple, otherwise make it a list
            if len(product_list) > 1:
                config_result["products"] = product_list
                del config_result["fields"]
            else:
                config_result["fields"]["ProductId"] = resolve_fsns[0]
                
        return config_result

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
            "extraction_source": "LLM + Local Mapping",
            "site_id": fields.get("site_id", "National"),
            "fields": {
                "ProductId": "Populate from FSN File",
                "unitSlabLower": ConfigGenerator._get_config_field(fields, "config_unit_slab_lower", "0"),
                "unitSlabUpper": ConfigGenerator._get_config_field(fields, "config_unit_slab_upper", "999999"),
                "brandSupport": ConfigGenerator._get_config_field(fields, "config_brand_support"),
                "vendorSplitRatio": ConfigGenerator._get_config_field(fields, "config_vendor_split_ratio"),
                "margin": fields.get("margin", ConfigGenerator._get_config_field(fields, "config_margin")),
                "dmrpType": fields.get("dmrpType", "Manual - From DMRP File"),
                "dmrpValue": fields.get("dmrpValue", "Manual - From DMRP File"),
                "maxSupportValue": ConfigGenerator._get_config_field(fields, "config_max_support_value", 
                                  fields.get("min_actual_discount_or_agreed_claim", "N/A"))
            }
        }
