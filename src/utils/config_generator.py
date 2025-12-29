"""
Configuration Generator for Retailer Hub
Generates scheme-specific configuration JSONs based on scheme type and subtype.
"""
from typing import Dict, Any, List

class ConfigGenerator:
    """
    Generates FSN/Scheme Configuration files based on scheme classification.
    """
    
    @staticmethod
    def generate_config(fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate the configuration JSON structure based on scheme type and subtype.
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
    def _gen_PDC(fields: Dict) -> Dict:
        """Generate config for PDC (Price Drop Claim) - standalone scheme type"""
        return {
            "config_type": "PDC",
            "fields": {
                "ProductId": "Derived from FSN File",
                "brandSupport": "Derived from Price Drop Amount",
                "maxQuantity": "Derived from Stock/Sales",
                "priceDropDate": fields.get("price_drop_date", "N/A")
            }
        }

    @staticmethod
    def _gen_BUY_SIDE_PERIODIC_CLAIM(fields: Dict) -> Dict:
        return {
            "config_type": "BS-PC",
            "fields": {
                "ProductId": "Derived from FSN File",
                "unitSlabUpper": "Derived from Slabs",
                "unitSlabLower": "Derived from Slabs",
                "brandSupport": "Derived from Scheme Terms",
                "maxSupportValue": fields.get("max_cap", "No Cap"),
                "bestBetQuantity": fields.get("best_bet", "N/A")
            }
        }

    @staticmethod
    def _gen_BUY_SIDE_PDC(fields: Dict) -> Dict:
        return {
            "config_type": "BS-PDC",
            "fields": {
                "ProductId": "Derived from FSN File",
                "brandSupport": "Derived from Price Drop",
                "maxQuantity": "Derived from Stock/Sales"
            }
        }

    @staticmethod
    def _gen_SELL_SIDE_CP(fields: Dict) -> Dict:
        return {
            "config_type": "SS-CP",
            "fields": {
                "ProductId": "Derived from FSN File",
                "brandSupport": "Derived from Coupon Value",
                "vendorSplitRatio": "Derived from Sharing %"
            }
        }

    @staticmethod
    def _gen_SELL_SIDE_PUC(fields: Dict) -> Dict:
        return {
            "config_type": "SS-PUC",
            "fields": {
                "ProductId": "Derived from FSN File",
                "brandSupport": "Derived from Support Amount",
                "vendorSplitRatio": "Derived from Sharing %",
                "unitSlabUpper": "Derived from Slabs",
                "unitSlabLower": "Derived from Slabs",
                "maxSupportValue": fields.get("max_cap", "No Cap"),
                "maxCapFKFunding": "Derived from Agreement",
                "margin": "Derived from Margin"
            }
        }

    @staticmethod
    def _gen_SELL_SIDE_PRX(fields: Dict) -> Dict:
        return {
            "config_type": "SS-PRX",
            "fields": {
                "ProductId": "Derived from FSN File",
                "incomingFsn": "Derived from Exchange logic",
                "vendorSplitRatio": "Derived from Sharing %",
                "exchangeSlabFrom": "Derived from Slabs",
                "exchangeSlabTo": "Derived from Slabs",
                "agreedSupport": "Derived from Support Amount"
            }
        }
        
    @staticmethod
    def _gen_SELL_SIDE_SC(fields: Dict) -> Dict:
        return {
             "config_type": "SS-SC",
             "fields": {
                 "ProductId": "Derived from FSN File"
             }
        }

    @staticmethod
    def _gen_SELL_SIDE_LS(fields: Dict) -> Dict:
        return {
            "config_type": "SS-LS",
            "description": "Lifestyle Scheme - DMRP details to be populated from DMRP file",
            "fields": {
                "ProductId": "Derived from FSN File",
                "unitSlabLower": "Derived from Slabs",
                "unitSlabUpper": "Derived from Slabs",
                "brandSupport": "Derived from Support",
                "vendorSplitRatio": "Derived from Sharing %",
                "margin": "Derived from Margin",
                "dmrpType": "Derived from DMRP File",
                "dmrpValue": "Derived from DMRP File",
                "maxSupportValue": fields.get("min_actual_discount_or_agreed_claim", "N/A")
            }
        }
