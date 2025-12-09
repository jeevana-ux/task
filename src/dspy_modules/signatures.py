"""
DSPy Signatures for Retailer Hub Field Extraction
Defines the input/output signatures for Chain-of-Thought reasoning.
"""
import dspy


class SchemeExtractionSignature(dspy.Signature):
    """Extract Retailer Hub fields from vendor email content using Chain-of-Thought reasoning."""
    
    # Input fields
    email_text = dspy.InputField(
        desc="Cleaned email text content from PDF extraction"
    )
    table_data = dspy.InputField(
        desc="Tabular data extracted from the email (if available)"
    )
    xlsx_data = dspy.InputField(
        desc="XLSX spreadsheet content (if provided)"
    )
    
    # Output fields with reasoning
    scheme_name = dspy.OutputField(
        desc="Scheme name extracted from email content. Look for titles, headers containing 'Scheme', 'Offer', 'Support', 'Plan', or 'Program'. Return short phrase."
    )
    scheme_name_reasoning = dspy.OutputField(
        desc="Step-by-step reasoning for extracting scheme_name"
    )
    
    scheme_description = dspy.OutputField(
        desc="1-2 line summary (10-15 words max) of the scheme's purpose from email body, excluding subject line"
    )
    scheme_description_reasoning = dspy.OutputField(
        desc="Reasoning for scheme_description"
    )
    
    scheme_period = dspy.OutputField(
        desc="'Duration' if scheme has start/end dates, 'Event' if tied to specific event. Default: 'Duration'"
    )
    scheme_period_reasoning = dspy.OutputField(
        desc="Reasoning for scheme_period"
    )
    
    duration = dspy.OutputField(
        desc="Scheme date range in format 'DD/MM/YYYY to DD/MM/YYYY'. Look for 'valid from', 'effective from', 'until', 'till', 'to', 'period'"
    )
    duration_reasoning = dspy.OutputField(
        desc="Reasoning for duration extraction"
    )
    
    discount_type = dspy.OutputField(
        desc="One of: 'Percentage of NLC', 'Percentage of MRP', 'Absolute', or 'Not Specified'"
    )
    discount_type_reasoning = dspy.OutputField(
        desc="Reasoning for discount_type classification"
    )
    
    max_cap = dspy.OutputField(
        desc="Maximum support amount (number only). Look for 'cap', 'maximum', 'not exceeding', 'upto'. Return 'No Cap' if not mentioned."
    )
    max_cap_reasoning = dspy.OutputField(
        desc="Reasoning for max_cap extraction"
    )
    
    vendor_name = dspy.OutputField(
        desc="Name of the brand or company (e.g., Campus, Puma, Realme, Adidas). Return the precise company or brand name. Do NOT return the name of a contact person (e.g., 'M. Sonika', 'Salesh Agarwal') or the email sender's personal name."
    )
    vendor_name_reasoning = dspy.OutputField(
        desc="Reasoning for vendor_name extraction"
    )
    
    price_drop_date = dspy.OutputField(
        desc="Date of price reduction (DD/MM/YYYY) for PDC schemes. Look for 'price drop effective', 'PDC from'. Return 'N/A' if not PDC or not found."
    )
    price_drop_date_reasoning = dspy.OutputField(
        desc="Reasoning for price_drop_date"
    )
    
    start_date = dspy.OutputField(
        desc="Scheme start date (DD/MM/YYYY). Prefer explicit 'scheme start date' over invoice dates."
    )
    start_date_reasoning = dspy.OutputField(
        desc="Reasoning for start_date"
    )
    
    end_date = dspy.OutputField(
        desc="Scheme end date (DD/MM/YYYY)"
    )
    end_date_reasoning = dspy.OutputField(
        desc="Reasoning for end_date"
    )
    
    fsn_file_config_file = dspy.OutputField(
        desc="'Yes' if email mentions FSN codes, SKU lists, model numbers, configuration files. 'No' otherwise."
    )
    fsn_file_config_file_reasoning = dspy.OutputField(
        desc="Reasoning for FSN file detection"
    )
    
    min_actual_discount_or_agreed_claim = dspy.OutputField(
        desc="'TRUE' if mentions 'whichever is lower', 'minimum of', 'cap at agreed amount'. 'FALSE' otherwise."
    )
    min_discount_reasoning = dspy.OutputField(
        desc="Reasoning for minimum discount clause"
    )
    
    remove_gst_from_final_claim = dspy.OutputField(
        desc="'Yes' if 'inclusive of GST', 'No' if 'exclusive of GST', 'Not Specified' if not mentioned"
    )
    remove_gst_reasoning = dspy.OutputField(
        desc="Reasoning for GST treatment"
    )
    
    over_and_above = dspy.OutputField(
        desc="'TRUE' only if explicitly mentions 'over and above', 'in addition to', 'O&A'. FALSE otherwise."
    )
    over_and_above_reasoning = dspy.OutputField(
        desc="Reasoning for over & above classification"
    )
    
    discount_slab_type = dspy.OutputField(
        desc="Textual description of discount slabs (only for Buyside-Periodic). 'Not Applicable' otherwise."
    )
    discount_slab_reasoning = dspy.OutputField(
        desc="Reasoning for discount slab extraction"
    )
    
    best_bet = dspy.OutputField(
        desc="Performance-based incentive value/description (Buyside-Periodic only). 'No' if not mentioned, 'Not Applicable' for other types."
    )
    best_bet_reasoning = dspy.OutputField(
        desc="Reasoning for best bet extraction"
    )
    
    brand_support_absolute = dspy.OutputField(
        desc="Absolute support amount for One-Off schemes. Look for 'approving amount of', 'sanctioned amount'. Number only. 'Not Applicable' for other types."
    )
    brand_support_reasoning = dspy.OutputField(
        desc="Reasoning for brand support amount"
    )
    
    gst_rate = dspy.OutputField(
        desc="GST percentage for One-Off schemes (e.g., '18%'). 'Not Applicable' for other scheme types."
    )
    gst_rate_reasoning = dspy.OutputField(
        desc="Reasoning for GST rate extraction"
    )
    
    scheme_type = dspy.OutputField(
        desc="One of: 'BUY_SIDE', 'SELL_SIDE', 'ONE_OFF'"
    )
    scheme_subtype = dspy.OutputField(
        desc="One of: 'PERIODIC_CLAIM', 'PDC', 'PUC/FDC', 'COUPON', 'SUPER COIN', 'PREXO', 'BANK OFFER', 'N/A'"
    )
    scheme_classification_reasoning = dspy.OutputField(
        desc="Detailed reasoning for scheme type and subtype classification based on keywords"
    )
    confidence_explanation = dspy.OutputField(
        desc="Explanation for the confidence level"
    )
