import pandas as pd
from pathlib import Path
import logging
import re

class MappingManager:
    """
    Handles deterministic lookups in local Excel/ODS files for FSNs and LS metadata.
    Ensures data privacy by keeping these files outside the LLM context.
    """
    def __init__(self, fsn_mapping_path: str, ls_mapping_path: str, logger=None):
        self.logger = logger
        self.fsn_mapping_path = Path(fsn_mapping_path)
        self.ls_mapping_path = Path(ls_mapping_path)
        self.fsn_df = None
        self.ls_df = None
        self._load_mappings()

    def _load_mappings(self):
        """Load mapping files into pandas dataframes."""
        try:
            if self.fsn_mapping_path.exists():
                # Use odf engine for .ods files
                engine = 'odf' if self.fsn_mapping_path.suffix == '.ods' else None
                self.fsn_df = pd.read_excel(self.fsn_mapping_path, engine=engine)
                if self.logger: self.logger.info(f"✅ Loaded FSN Mapping: {len(self.fsn_df)} rows")
            else:
                if self.logger: self.logger.warning(f"⚠️ FSN Mapping file not found: {self.fsn_mapping_path}")
            
            if self.ls_mapping_path.exists():
                engine = 'odf' if self.ls_mapping_path.suffix == '.ods' else None
                self.ls_df = pd.read_excel(self.ls_mapping_path, engine=engine)
                if self.logger: self.logger.info(f"✅ Loaded LS Mapping: {len(self.ls_df)} rows")
            else:
                if self.logger: self.logger.warning(f"⚠️ LS Mapping file not found: {self.ls_mapping_path}")
                
        except Exception as e:
            if self.logger: self.logger.error(f"❌ Failed to load mapping files: {e}")

    def resolve_fsns(self, model_name: str, extracted_fsns: str = "") -> list:
        """
        Multi-stage FSN resolution.
        1. Use FSNs extracted from PDF if present.
        2. Else, lookup FSNs by Model Name in Excel (Whitespace-agnostic).
        """
        # Step 1: Parse extracted FSNs
        valid_fsns = []
        if extracted_fsns and extracted_fsns.lower() != "none":
            # Split by common separators
            raw_fsns = re.split(r'[;,\n\s]+', extracted_fsns)
            valid_fsns = [f.strip() for f in raw_fsns if len(f.strip()) >= 10]
            
        if valid_fsns:
            if self.logger: self.logger.info(f"🔍 Using {len(valid_fsns)} FSNs found in PDF text.")
            return valid_fsns

        # Step 2: Fallback to Model Name Lookup
        if self.fsn_df is None or not model_name or model_name.lower() in ["not specified", "n/a", "none"]:
            return []

        if self.logger: self.logger.info(f"🔍 PDF had no FSNs. Searching mapping for Model: '{model_name}'...")
        
        try:
            # Step 2a: Whitespace-agnostic match
            def collapse(s): return re.sub(r'\s+', '', str(s)).lower()
            model_collapsed = collapse(model_name)
            
            # Match against collapsed 'Model Name' or 'Title'
            model_name_collapsed = self.fsn_df['Model Name'].astype(str).apply(collapse)
            title_collapsed = self.fsn_df['Title'].astype(str).apply(collapse) if 'Title' in self.fsn_df.columns else model_name_collapsed
            
            mask = (model_name_collapsed == model_collapsed) | (title_collapsed == model_collapsed)
            results = self.fsn_df[mask]['FSN'].unique().tolist()
            
            # Step 2b: Fallback to partial match if no exact whitespace-agnostic match
            if not results:
                model_mask = self.fsn_df['Model Name'].astype(str).str.contains(model_name, case=False, na=False)
                title_mask = self.fsn_df['Title'].astype(str).str.contains(model_name, case=False, na=False) if 'Title' in self.fsn_df.columns else model_mask
                results = self.fsn_df[model_mask | title_mask]['FSN'].unique().tolist()
            
            if results:
                if self.logger: self.logger.info(f"✨ Mapped '{model_name}' to {len(results)} FSN(s) via Excel.")
                return results
            else:
                if self.logger: self.logger.warning(f"❓ No FSN match found for model '{model_name}' in Excel.")
        except Exception as e:
            if self.logger: self.logger.error(f"Error during FSN lookup: {e}")
            
        return []

    def get_ls_enrichment(self, vendor_name: str, city_name: str = "National") -> dict:
        """
        Fetches Margin, DMRP Type, DMRP Value, and Vendor Site for SS-LS schemes.
        Looks specifically for the 'Brand' column in the LS mapping sheet.
        Handles whitespace discrepancies like 'IndoEra' vs 'Indo Era'.
        """
        if self.ls_df is None or not vendor_name or vendor_name.lower() in ["unknown vendor", "not specified", "unknown"]:
            return {}

        try:
            # LS Mapping might have 'Brand' or 'Brand '
            brand_col = next((c for c in self.ls_df.columns if str(c).strip().lower() == 'brand'), None)
            
            if not brand_col:
                if self.logger: self.logger.warning(f"⚠️ 'Brand' column not found in LS mapping. Available: {self.ls_df.columns.tolist()}")
                return {}

            # Step 1: Whitespace-agnostic match
            # Collapse both strings (remove all spaces) for comparison
            def collapse(s): return re.sub(r'\s+', '', str(s)).lower()
            
            vendor_collapsed = collapse(vendor_name)
            
            # Apply collapse to the brand column
            brand_series_collapsed = self.ls_df[brand_col].astype(str).apply(collapse)
            mask = (brand_series_collapsed == vendor_collapsed)
            
            row = self.ls_df[mask].head(1)
            
            # Step 2: Fallback to partial match if still not found
            if row.empty:
                mask = self.ls_df[brand_col].astype(str).str.contains(vendor_name, case=False, na=False)
                row = self.ls_df[mask].head(1)
                
            if row.empty:
                if self.logger: self.logger.debug(f"No LS mapping found for brand: {vendor_name} (collapsed: {vendor_collapsed})")
                return {}

            def clean_percentage_value(val):
                """Converts '30%', '0.3', or 'DMRP is 40%' to '30', '30', or '40'."""
                s = str(val).strip()
                if not s or s.lower() == 'nan' or s == '-':
                    return "Not Specified"
                
                # Check for explicit percentage signal in text (e.g., "DMRP is 40%")
                percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%', s)
                if percentage_match:
                    val_str = percentage_match.group(1)
                    # Convert to int if it's a whole number (e.g., 40.0 -> 40)
                    try:
                        f_val = float(val_str)
                        return str(int(f_val)) if f_val.is_integer() else val_str
                    except:
                        return val_str
                
                # Try to handle decimal fractions (e.g., 0.37 -> 37)
                try:
                    f = float(s)
                    if 0 < f < 1:
                        return str(int(round(f * 100)))
                    return str(int(f)) if f.is_integer() else str(f)
                except ValueError:
                    return s

            def get_val(df_row, col_name, default="Not Specified"):
                # Flexible column matching
                actual_col = next((c for c in df_row.columns if col_name.lower() in str(c).lower()), None)
                if not actual_col: return default
                val = df_row[actual_col].iloc[0]
                if pd.isna(val) or str(val).lower() == 'nan':
                    return default
                return str(val).strip()

            dmrp_details_raw = get_val(row, "DMRP Details")
            dmrp_factor_raw = get_val(row, "DMRP Factor")
            margin_raw = get_val(row, "Margin")
            
            # Logic: If raw details contains '%', type is PERCENTAGE, else ABSOLUTE
            dmrp_type = "ABSOLUTE"
            if "%" in dmrp_details_raw:
                dmrp_type = "PERCENTAGE"

            res = {
                "margin": clean_percentage_value(margin_raw),
                "dmrpType": dmrp_type,
                "dmrpValue": clean_percentage_value(dmrp_details_raw), 
                "site_id": get_val(row, "SC", default="National_Site")
            }
            if self.logger: 
                matched_brand = row[brand_col].iloc[0]
                self.logger.info(f"✅ Enriched LS fields for brand '{vendor_name}' (Matched in Excel as '{matched_brand}')")
            return res
        except Exception as e:
            if self.logger: self.logger.error(f"Error during LS enrichment: {e}")
            return {}
