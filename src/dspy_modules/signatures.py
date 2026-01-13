"""
DSPy Signatures for Retailer Hub Field Extraction
Enhanced prompts with deep reasoning for accurate field extraction.
LLM should analyze business context, not just match keywords.
"""
import dspy


class SchemeExtractionSignature(dspy.Signature):
    """
    Extract Retailer Hub claim fields from vendor email/PDF content.
    
    CRITICAL INSTRUCTIONS:
    1. Do NOT rely solely on keyword matching - analyze the BUSINESS CONTEXT.
    2. Understand the INTENT behind the email - what is the brand trying to communicate?
    3. Consider the ENTIRE email content before making classification decisions.
    4. Provide detailed REASONING for each field extraction.
    5. When uncertain, analyze what makes business sense given the context.
    """
    
    # Input fields
    email_text = dspy.InputField(
        desc="Email content from brand/vendor regarding commercial schemes, offers, or support"
    )
    table_data = dspy.InputField(
        desc="Tabular data (FSN lists, SKU data, discount slabs, pricing info)"
    )
    xlsx_data = dspy.InputField(
        desc="XLSX spreadsheet content (may contain product/SKU configuration)"
    )
    
    # ============================================================================
    # Field 1: Scheme Name
    # ============================================================================
    scheme_name = dspy.OutputField(
        desc="""Extract or construct the scheme name.
ANALYZE: Look at email subject, headers, and opening lines for scheme/offer title.
PATTERNS: 'Scheme', 'Offer', 'Support', 'Plan', 'Program', 'Initiative', 'Approval'.
CONSTRUCT IF MISSING: Create from [Brand] + [Period/Event] + [Type], e.g., 'Realme Q1 Pricing Support'.
FORMAT: Short phrase, 3-7 words max.
EXAMPLES: 'Campus Diwali Sellout Offer', 'Puma FY25 JBP Scheme', 'Samsung Price Protection Claim'."""
    )
    scheme_name_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify/construct the scheme name? What text patterns indicated this?"
    )
    
    # ============================================================================
    # Field 2: Scheme Description
    # ============================================================================
    scheme_description = dspy.OutputField(
        desc="""Summarize the scheme's purpose and offer in 1-2 concise lines.
ANALYZE: What is the brand offering? What is the business intent? What support/discount type?
INCLUDE: Offer type, percentage/amount, applicable products, purpose.
EXCLUDE: Subject line verbatim, lengthy details.
FORMAT: 10-20 words, single sentence.
EXAMPLE: 'Brand offers 5% sellout support on select SKUs for Q1 visibility campaign.'"""
    )
    scheme_description_reasoning = dspy.OutputField(
        desc="REASONING: What is the core offer? How did you distill the business intent?"
    )
    
    # ============================================================================
    # Field 4: Scheme Period Type
    # ============================================================================
    scheme_period = dspy.OutputField(
        desc="""Classify as 'Duration' or 'Event'.
DURATION: Has date range (from X to Y), runs continuously. Q1/Q2/FY periods, month-based.
EVENT: Tied to specific event (Diwali, Big Billion Days, Republic Day Sale).
DEFAULT: Return 'Duration' if unclear.
OUTPUT: Exactly 'Duration' or 'Event'."""
    )
    scheme_period_reasoning = dspy.OutputField(
        desc="REASONING: Is this a time-period scheme or event-based scheme?"
    )
    
    # ============================================================================
    # Field 5: Duration (Date Range)
    # ============================================================================
    duration = dspy.OutputField(
        desc="""Extract the scheme validity period.
FORMAT: 'DD/MM/YYYY to DD/MM/YYYY' ONLY.
CONVERT: All date formats to DD/MM/YYYY (Jan 1, 2024 → 01/01/2024).
LOOK FOR: 'valid from', 'effective from', 'w.e.f', 'period', 'from...to', 'until'.
IF NOT FOUND: Return 'Not Specified'."""
    )
    duration_reasoning = dspy.OutputField(
        desc="REASONING: What dates did you find? How did you identify start vs end?"
    )
    
    # ============================================================================
    # Field 6: Discount Type
    # ============================================================================
    discount_type = dspy.OutputField(
        desc="""Identify the discount calculation basis.
OPTIONS:
- 'Percentage of NLC': Discount on Net Landing Cost (% of NLC, NLC-linked).
- 'Percentage of MRP': Discount on Maximum Retail Price (% of MRP).
- 'Absolute': Fixed rupee amount (Rs.X per unit, flat amount).
- 'Not Specified': Basis not mentioned.
ANALYZE: Look for how the discount/support is calculated, not just the value."""
    )
    discount_type_reasoning = dspy.OutputField(
        desc="REASONING: What calculation basis was indicated? How did you determine this?"
    )
    
    # ============================================================================
    # Field 7: Max Cap
    # ============================================================================
    max_cap = dspy.OutputField(
        desc="""Extract maximum support/claim cap amount.
LOOK FOR: 'cap', 'maximum', 'not exceeding', 'upto', 'ceiling', 'limit'.
OUTPUT: Number only without currency symbols (50000, not Rs.50,000).
IF NOT FOUND: Return 'No Cap'."""
    )
    max_cap_reasoning = dspy.OutputField(
        desc="REASONING: What cap-related language did you find?"
    )
    
    # ============================================================================
    # Field 8: Vendor Name (Brand Name)
    # ============================================================================
    vendor_name = dspy.OutputField(
        desc="""Extract the BRAND/COMPANY name offering the scheme.
CORRECT: 'Campus', 'Puma', 'Realme', 'Samsung', 'LG', 'Whirlpool', 'Vivo', 'iQOO'.
LOOK FOR: Brand in signature, letterhead, email domain, 'From' brand name.
CRITICAL: Return brand name, NOT personal names (Rajesh Kumar, M. Sonika).
ANALYZE: Who is PROVIDING the support? That's the vendor."""
    )
    vendor_name_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the brand vs personal sender name?"
    )

    # ============================================================================
    # NEW: Model Name (For FSN Lookup)
    # ============================================================================
    model_name = dspy.OutputField(
        desc="""Extract the primary Model Name or Series mentioned.
LOOK FOR: specific model identifiers, product titles, series names (e.g., 'Galaxy S24', 'Air Jordan 1', 'Model: X100').
FORMAT: Return the most specific model name found. If multiple, return the dominant one or main series.
IF NOT FOUND: Return 'Not Specified'."""
    )

    # ============================================================================
    # NEW: Extracted FSNs (Found in text)
    # ============================================================================
    extracted_fsns = dspy.OutputField(
        desc="""Extract any explicit FSNs (Flipkart Serial Numbers) mentioned in text or tables.
FSN PATTERN: 13-16 character alphanumeric codes (e.g., 'ACCFGH1234567890').
FORMAT: Semi-colon separated list (e.g., 'FSN1;FSN2;FSN3').
IF NOT FOUND: Return 'None'."""
    )
    
    # ============================================================================
    # Field 9: Price Drop Date (PDC Only)
    # ============================================================================
    price_drop_date = dspy.OutputField(
        desc="""Extract price drop effective date (PDC schemes only).
APPLICABLE: Only if scheme involves price reduction/protection.
LOOK FOR: 'price drop effective', 'cost change w.e.f', 'NLC revision from'.
STRICT FORMAT: 'DD/MM/YYYY' (e.g. 25/05/2024) or 'N/A'."""
    )
    price_drop_date_reasoning = dspy.OutputField(
        desc="REASONING: Is this a PDC scheme? What price drop date was mentioned?"
    )

    # ============================================================================
    # NEW: Cities/Locations (For Grocery/HL City-based offers)
    # ============================================================================
    cities_locations = dspy.OutputField(
        desc="""Extract any cities, regions, or warehouse locations mentioned as the scope of the offer.
APPLICABLE: Mostly for Grocery/HL where offers are city-specific.
LOOK FOR: 'Mumbai', 'Bangalore', 'Western Region', 'Chennai Warehouse', 'North Zone'.
FORMAT: Semi-colon separated list.
IF NOT FOUND: Return 'National'."""
    )

    # ============================================================================
    # NEW: Sub Periods (For multi-period schemes)
    # ============================================================================
    sub_periods = dspy.OutputField(
        desc="""Identify if the scheme has multiple sub-periods with different dates/ranges.
PATTERN: '1st-10th Nov: 5% off, 11th-20th: 10% off'.
FORMAT: List ranges as 'DD/MM/YYYY to DD/MM/YYYY'. Semi-colon separated.
IF NOT FOUND: Return 'Single Period'."""
    )
    
    # ============================================================================
    # Field 10 & 11: Start & End Dates
    # ============================================================================
    start_date = dspy.OutputField(
        desc="""Extract scheme START date. STRICT FORMAT: 'DD/MM/YYYY' (e.g. 01/01/2024) or 'Not Specified'.
PRIORITY: Scheme start > Invoice start > Email date."""
    )
    start_date_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the start date?"
    )
    
    end_date = dspy.OutputField(
        desc="""Extract scheme END date. STRICT FORMAT: 'DD/MM/YYYY' (e.g. 31/12/2024) or 'Not Specified'.
LOOK FOR: 'valid until', 'ending', 'expires on', 'through'."""
    )
    end_date_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the end date?"
    )
    
    # ============================================================================
    # Field 12: FSN/Config File Present
    # ============================================================================
    fsn_file_config_file = dspy.OutputField(
        desc="""Is there a list of FSNs, SKUs, or product config?
CHECK: table_data, xlsx_data for product identifiers.
LOOK FOR: FSN codes, SKU lists, model numbers, 'attached list', 'refer attachment'.
OUTPUT: 'Yes' if product list exists, 'No' otherwise."""
    )
    fsn_file_config_file_reasoning = dspy.OutputField(
        desc="REASONING: Did you find product lists or configuration data?"
    )
    
    # ============================================================================
    # Field 13: Minimum of Actual Discount or Agreed Claim
    # ============================================================================
    min_actual_discount_or_agreed_claim = dspy.OutputField(
        desc="""Is there a 'minimum of actual vs agreed' cap clause?
LOOK FOR: 'whichever is lower', 'minimum of actual', 'lower of the two'.
OUTPUT: 'TRUE' if such logic mentioned, 'FALSE' otherwise."""
    )
    min_discount_reasoning = dspy.OutputField(
        desc="REASONING: Did you find comparative minimum clause?"
    )
    
    # ============================================================================
    # Field 14: Remove GST from Final Claim
    # ============================================================================
    remove_gst_from_final_claim = dspy.OutputField(
        desc="""GST handling instruction.
- 'Yes': Amount INCLUDES GST (inclusive of tax).
- 'No': Amount EXCLUDES GST (plus GST/GST extra).
- 'Not Specified': GST treatment not mentioned."""
    )
    remove_gst_reasoning = dspy.OutputField(
        desc="REASONING: What GST-related phrases did you find?"
    )
    
    # ============================================================================
    # Field 15: Over & Above
    # ============================================================================
    over_and_above = dspy.OutputField(
        desc="""Is support ADDITIONAL to existing schemes?
LOOK FOR: 'over and above', 'O&A', 'in addition to', 'additional support'.
OUTPUT: 'TRUE' only if explicitly stated, 'FALSE' otherwise."""
    )
    over_and_above_reasoning = dspy.OutputField(
        desc="REASONING: Was O&A explicitly mentioned?"
    )
    
    # ============================================================================
    # Field 16: Scheme Document Present
    # ============================================================================
    scheme_document = dspy.OutputField(
        desc="""Is formal approval/letter attached or referenced?
LOOK FOR: 'approval letter', 'attached approval', 'sanction document'.
OUTPUT: 'Yes' or 'No'."""
    )
    scheme_document_reasoning = dspy.OutputField(
        desc="REASONING: Did you find formal document references?"
    )
    
    # ============================================================================
    # Field 17: Discount Slab Type (Buyside-Periodic Only)
    # ============================================================================
    discount_slab_type = dspy.OutputField(
        desc="""Output 'notApplicable' (fixed value for Buyside-Periodic). 
        'Not Applicable' for all other scheme types."""
    )
    discount_slab_type_reasoning = dspy.OutputField(
        desc="REASONING: For Buyside-Periodic, state that this is a fixed constant requirement."
    )
    
    # ============================================================================
    # Field 18: Best Bet (Buyside-Periodic Only)
    # ============================================================================
    best_bet = dspy.OutputField(
        desc="""Output 'FALSE' (fixed string for Buyside-Periodic). 
        'Not Applicable' for all other scheme types."""
    )
    best_bet_reasoning = dspy.OutputField(
        desc="REASONING: For Buyside-Periodic, state that this is a fixed constant requirement."
    )
    
    # ============================================================================
    # Field 19: Brand Support Absolute (One-Off Only)
    # ============================================================================
    brand_support_absolute = dspy.OutputField(
        desc="""Absolute support amount (One-Off claims only).
LOOK FOR: 'approved amount', 'sanctioned Rs.X', 'one-time support'.
OUTPUT: Number only, 'Not Applicable' for non One-Off."""
    )
    brand_support_absolute_reasoning = dspy.OutputField(
        desc="REASONING: What approval amount was stated?"
    )
    
    # ============================================================================
    # Field 20: GST Rate (One-Off Only)
    # ============================================================================
    gst_rate = dspy.OutputField(
        desc="""GST rate for One-Off claims.
OUTPUT: Percentage (e.g., '18%'), 'Not Applicable' for non One-Off, 'Not Specified' if not mentioned."""
    )
    gst_rate_reasoning = dspy.OutputField(
        desc="REASONING: What GST rate was explicitly stated?"
    )
    
    # ============================================================================
    # Field 21: Scheme Type and Subtype (CRITICAL - REASON DEEPLY)
    # ============================================================================
    scheme_type = dspy.OutputField(
        desc="""CLASSIFY THE SCHEME TYPE with deep reasoning.
        
DO NOT just match keywords. ANALYZE THE BUSINESS CONTEXT:

**CRITICAL RULE 1 - PRICE DROP DETECTION (HIGHEST PRIORITY):**
→ If the email mentions "Price drop", "Permanent Price drop", "NLC reduction", "cost reduction", "price protection", or similar:
  THEN: scheme_type = 'PDC' AND scheme_subtype = 'PDC'
  This is a STANDALONE CATEGORY. Do NOT classify as BUY_SIDE or SELL_SIDE.
  STOP processing other rules if this matches.

**CRITICAL RULE 2 - LIFESTYLE VENDOR DETECTION:**
→ If the vendor is ANY of these LIFESTYLE brands:
  - ADITYA BIRLA LIFESTYLE BRANDS LIMITED
  - ADITYA BIRLA FASHION AND RETAIL LIMITED
  - MGI DISTRIBUTION PVT LTD
  - BRAND CONCEPTS LIMITED
  - Timex Group India Limited
  - Titan Company Ltd
  - METRO BRANDS LIMITED
  - SUMITSU APPAREL PVT. LTD.
  - Sea Turtle Private Limited
  - High Star
  - Juneberry
  THEN: scheme_type = 'SELL_SIDE' AND scheme_subtype = 'LS' (LIFESTYLE)
  REGARDLESS of other keywords in the email.

**PDC** (Price Drop Claim - STANDALONE)
→ WHAT IT MEANS: Price protection or price drop compensation.
→ BUSINESS CONTEXT: When supplier reduces price, they compensate for existing stock.
→ INDICATORS:
  - "Price drop", "Permanent Price drop", "Price Protection", "NLC reduction"
  - "Cost reduction", "Price change compensation"
→ OUTPUT: scheme_type = 'PDC', scheme_subtype = 'PDC'

**BUY_SIDE** (Claim ID prefix: BS-PC)
→ WHAT IT MEANS: Support on PURCHASE/INWARD side. Brand helps Flipkart with purchase costs.
→ BUSINESS CONTEXT: Schemes tied to what Flipkart BUYS from the brand.
→ INDICATORS:
  - Sellin incentives (not sellout)
  - JBP/Joint Business Plan, TOT/Terms of Trade
  - Quarterly/Annual business plans (Q1, Q2, FY support)
  - NRV-linked, inwards support, inventory funding
→ OUTPUT: scheme_type = 'BUY_SIDE'

**SELL_SIDE** (Claim ID prefix: SS-xxx)
→ WHAT IT MEANS: Support on SELLING/OUTWARD side. Brand helps Flipkart sell to customers.
→ BUSINESS CONTEXT: Schemes tied to what Flipkart SELLS to end customers.
→ INDICATORS:
  - Sellout support (customer sales)
  - Coupons/VPC for customer discounts
  - Exchange/Prexo offers (customer trade-in)
  - Bank offers (customer payment)
  - Super Coin rewards (customer incentive)
  - Pricing/CP support on selling price
  - **LIFESTYLE vendors** ← ALWAYS LS SUBTYPE
→ OUTPUT: scheme_type = 'SELL_SIDE'

**OFC** (One-Off Claim)
→ WHAT IT MEANS: One-time, ad-hoc support not tied to regular schemes.
→ BUSINESS CONTEXT: Special approval for specific situation, not part of JBP/regular plan.
→ INDICATORS:
  - 'One off', 'one-off', 'one time'
  - Ad-hoc approval, special sanction
  - Specific amount approved for exception
→ OUTPUT: scheme_type = 'OFC'

OUTPUT: Exactly 'PDC', 'BUY_SIDE', 'SELL_SIDE', or 'OFC'.
THINK: Is this a Price Drop (PDC)? Or helping purchase (BUY_SIDE)? Or helping sell (SELL_SIDE)? Or special exception (OFC)?"""
    )
    
    scheme_type_reasoning = dspy.OutputField(
        desc="""EXPLAIN YOUR SCHEME TYPE DECISION.
        
Structure:
1. **Rule Check**: Did any CRITICAL RULES apply (Price Drop → PDC, Lifestyle Vendor → LS)?
2. **Business Direction**: Is support for Flipkart's BUYING or SELLING activity?
3. **Key Evidence**: What specific phrases/keywords led to this classification?
4. **Why not others?**: Why did you rule out the other types?

Example: "This is PDC because it mentions 'Price Drop effective from 24th', triggering the Price Drop → PDC rule."
Example: "This is SELL_SIDE because the vendor is 'Titan Company Ltd' which is a Lifestyle vendor, triggering the Lifestyle → LS rule."
"""
    )
    
    scheme_subtype = dspy.OutputField(
        desc="""CLASSIFY THE SUBTYPE based on scheme_type.
        
**CRITICAL: Priority Rules (Apply in order):**
1. **PDC Rule**: If "Price drop", "Permanent Price drop", "NLC reduction", "cost reduction", or "price protection" mentioned → subtype MUST be 'PDC'.
2. **LS Rule**: Subtype MUST be 'LS' if:
   - Keywords like "SOR", "SOR discounts", "Monsoon Sale", "Monsoon", "Fashion", "Lifestyle", or "Clothing" are present.
   - OR if no keywords, the vendor identified from the email (check "To:" address) belongs to a LIFESTYLE brand (Aditya Birla, Timex, Titan, Metro, Brand Concepts, beewakoof, Highlander, Leemboodi, High Star, Juneberry etc.).

**IF SELL_SIDE (Flipkart Selling Support), choose one of these EXACT CODES:**

- **'CP'** (Coupon): ONLY when explicit coupon codes (VPC, Promo Code, Voucher Code) are mentioned for customer checkout.
  → KEYWORDS: Coupon Code, VPC, Voucher Code, Promo Code.
  → USE THIS ONLY if you see evidence of specific codes customers use at checkout.

- **'PUC'** (Pricing/Sellout): General pricing, sellout support, price match, or "CP support" where NO coupon code is involved.
  → INCLUDES: PUC, FDC, Sellout Support, Price Match, CP/Pricing/Sellout Support/rest all.
  → **DEFAULT**: Use PUC for all general selling price support if no specific codes are mentioned.

- **'PRX'** (Exchange): Product Exchange / Buyback / Prexo / Upgrade / BUP.
  → KEYWORDS: Exchange, Prexo, Upgrade, Buyback, BUP, Prexo Bumpup.

- **'SC'** (SuperCoin): SuperCoin Reward Points support.
  → KEYWORDS: Super Coin, SuperCoin, Reward Points.

- **'LS'** (Lifestyle): Handled by LS Priority Rule above. Includes Clothing, Watches, Footwear, etc.
  → KEYWORDS: Lifestyle, Fashion, Clothing, Monsoon Sale, SOR discounts, SOR.

**IF BUY_SIDE (Flipkart Buying Support), choose one:**
- **'PDC'**: Price Drop / Price protection (Handled by Rule 1).
- **'PERIODIC_CLAIM'**: Quarterly/Annual/TOT/JBP support (Only if NOT a price drop).

**IF OFC (One-Off):**
- 'OFC'

OUTPUT: One code only (e.g., 'CP', 'PUC', 'PRX', 'SC', 'LS', 'PDC', 'PERIODIC_CLAIM', 'OFC')."""
    )
    
    scheme_subtype_reasoning = dspy.OutputField(
        desc="""EXPLAIN your subtype decision with focus on SELL_SIDE distinctions.

1. **Rule Check**: Did Rule 1 (PDC) or Rule 2 (LS) apply first? (Mention specifically if LS keywords or the 'To:' email address was the trigger).
2. **Mechanism Analysis**: If SELL_SIDE, identify the customer-facing mechanism:
   - Is it actual **Coupon Codes** (CP)? 
   - Is it general **Pricing/Sellout Support** (PUC)? 
   - Is it **Exchange/Upgrade** (PRX)?
   - Is it **SuperCoin Rewards** (SC)?
   *Note: Many emails say "CP support" but mean general pricing (PUC). Only choose 'CP' if you see customer-facing codes/vouchers.*
3. **Keyword Evidence**: List the specific phrases from the text that confirm this mechanism (e.g., "Exchange value", "SuperCoin support", "VPC code 'GET100'").
4. **Exclusion**: Why did you rule out the other Sell-Side types (e.g., Why PUC instead of CP)?
"""
    )

    # ============================================================================
    # FSN CONFIG FIELDS - Extracted in same LLM call for efficiency
    # ============================================================================
    
    config_brand_support = dspy.OutputField(
        desc="""Extract the BRAND SUPPORT value (discount/support amount per unit).
LOOK FOR: 
- Percentage values: "5% of NLC", "10% off MRP", "Discount of 15%"
- Absolute values: "Rs.100 per unit", "₹50 support", "Fixed Rs.500"
- Slab-based: Extract the primary/first slab value
FORMAT: Return the value as-is (e.g., "5% of NLC", "Rs.100", "15%")
IF NOT FOUND: Return "Not specified in email"
"""
    )
    config_brand_support_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the brand support value? What text indicated this amount?"
    )
    
    config_vendor_split_ratio = dspy.OutputField(
        desc="""Extract the VENDOR SPLIT RATIO (cost sharing between vendor and Flipkart).
LOOK FOR:
- Split mentions: "50:50 sharing", "70-30 split", "Vendor bears 100%"
- Percentage splits: "80% vendor, 20% FK", "Vendor share: 60%"
- Common patterns: "Brand funded", "Vendor fully funded" = 100:0
FORMAT: Return as "X:Y" (e.g., "80:20", "100:0", "50:50")
IF NOT FOUND: Return "Not specified"
"""
    )
    config_vendor_split_reasoning = dspy.OutputField(
        desc="REASONING: How did you determine the split ratio? What text indicated the sharing arrangement?"
    )
    
    config_unit_slab_lower = dspy.OutputField(
        desc="""Extract the LOWER BOUND of the unit/quantity slab.
LOOK FOR:
- Slab definitions: "1-100 units", "Min qty: 50", "From 0 to 500"
- Minimum thresholds: "Above 100 units", "Starting from 1"
FORMAT: Return numeric value only (e.g., "0", "1", "100")
IF NOT FOUND: Return "0" as default lower bound
"""
    )
    
    config_unit_slab_upper = dspy.OutputField(
        desc="""Extract the UPPER BOUND of the unit/quantity slab.
LOOK FOR:
- Slab definitions: "1-100 units", "Max qty: 500", "Up to 1000"
- Maximum limits: "Quantity cap: 999", "No limit" = "999999"
FORMAT: Return numeric value only (e.g., "100", "500", "999999")
IF NOT FOUND: Return "999999" (no upper limit)
"""
    )
    config_slab_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the slab bounds? What quantities were mentioned?"
    )
    
    config_max_support_value = dspy.OutputField(
        desc="""Extract the MAXIMUM SUPPORT VALUE (cap on total support amount).
LOOK FOR:
- Max cap mentions: "Max support: Rs.10L", "Cap of ₹50,000", "Global cap: 1Cr"
- Limit phrases: "Not exceeding", "Up to", "Maximum reimbursement"
FORMAT: Return the amount (e.g., "Rs.10,00,000", "₹50000", "1Cr")
IF NOT FOUND: Return "No Cap"
"""
    )
    config_max_support_reasoning = dspy.OutputField(
        desc="REASONING: How did you find the max support cap? What text indicated this limit?"
    )
    
    config_margin = dspy.OutputField(
        desc="""Extract the MARGIN percentage (if mentioned).
LOOK FOR:
- Margin mentions: "Margin: 8%", "8% margin", "Retail margin of 10%"
- Profit margins: "Dealer margin", "Trade margin"
FORMAT: Return percentage value (e.g., "8%", "10%")
IF NOT FOUND: Return "Not specified"
"""
    )
    config_margin_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the margin? What text mentioned margin percentage?"
    )
    
    # Global Logic Summary
    reasoning = dspy.OutputField(desc="High-level logic summary of the extraction process.")
