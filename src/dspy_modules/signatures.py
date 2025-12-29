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
        desc="""Extract discount slab structure (Buyside-Periodic only).
FORMAT: Describe tiers, e.g., '0-50L: 2%, 50L-1Cr: 3%'.
OUTPUT: Slab description, 'Not Applicable' for non-Periodic, 'Not Specified' if no slabs."""
    )
    discount_slab_reasoning = dspy.OutputField(
        desc="REASONING: What tiered structure did you find?"
    )
    
    # ============================================================================
    # Field 18: Best Bet (Buyside-Periodic Only)
    # ============================================================================
    best_bet = dspy.OutputField(
        desc="""Performance-based incentive (Buyside-Periodic only).
LOOK FOR: 'best bet', 'performance bonus', 'target achievement'.
OUTPUT: Description if found, 'No' if not, 'Not Applicable' for non-Periodic."""
    )
    best_bet_reasoning = dspy.OutputField(
        desc="REASONING: Did you find performance-based incentives?"
    )
    
    # ============================================================================
    # Field 19: Brand Support Absolute (One-Off Only)
    # ============================================================================
    brand_support_absolute = dspy.OutputField(
        desc="""Absolute support amount (One-Off claims only).
LOOK FOR: 'approved amount', 'sanctioned Rs.X', 'one-time support'.
OUTPUT: Number only, 'Not Applicable' for non One-Off."""
    )
    brand_support_reasoning = dspy.OutputField(
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
→ If the email mentions "Price Drop", "NLC reduction", "cost reduction", "price protection", or similar:
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
  THEN: scheme_type = 'SELL_SIDE' AND scheme_subtype = 'LS' (LIFESTYLE)
  REGARDLESS of other keywords in the email.

**PDC** (Price Drop Claim - STANDALONE)
→ WHAT IT MEANS: Price protection or price drop compensation.
→ BUSINESS CONTEXT: When supplier reduces price, they compensate for existing stock.
→ INDICATORS:
  - "Price Drop", "Price Protection", "NLC reduction"
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
        
**CRITICAL: Apply these rules FIRST:**
1. If "Price Drop" mentioned → scheme_type = 'PDC' AND subtype = 'PDC' (STANDALONE, even if other keywords present)
2. If Lifestyle vendor → subtype = 'LS' (even if other keywords present)

**IF BUY_SIDE, choose one:**
- **'PDC'** (PDC-PDC): Price Drop Claim / Price Protection
  → CRITICAL: ANY mention of "Price Drop", "NLC reduction", "cost reduction" → MUST be PDC
  → KEYWORDS: Price Drop, Price Protection, Cost Reduction, NLC Change
  
- 'PERIODIC_CLAIM' (BS-PC): Quarterly/Annual support schemes
  → KEYWORDS: JBP, TOT, Q1/Q2 support, Sellin incentive
  → ONLY if NOT a price drop scenario

**IF SELL_SIDE, choose one of these EXACT CODES:**

**CRITICAL RULE 3 - PUC vs CP DISTINCTION:**
→ **'CP'** (Coupon): ONLY for actual COUPON mechanisms
   - KEYWORDS: Coupon, VPC, Voucher, Promo Code, Coupon Code
   - REASONING: "Customer uses a coupon/voucher code at checkout"
   - NOT for general pricing support!

→ **'PUC'** (PUC/FDC): General pricing/sellout support (CP/Pricing/Sellout Support/rest all)
   - INCLUDES: CP support (NOT coupon-based), Pricing support, Sellout support, Competitive pricing
   - KEYWORDS: PUC, FDC, Sellout Support, Price Match, CP (when NOT coupon), Pricing support
   - REASONING: "General support for selling price, NOT via coupon mechanism"
   - DEFAULT: Use PUC if unclear between PUC and CP

→ **'LS'** (Lifestyle): LIFESTYLE category vendors
   - **CRITICAL: ANY of the 9 Lifestyle vendors → MUST be LS**
   - Vendors: Aditya Birla, MGI Distribution, Brand Concepts, Timex, Titan, Metro Brands, Sumitsu Apparel, Sea Turtle
   
→ 'PRX' (Prexo/Exchange): Product Exchange/Buyback
   - KEYWORDS: Exchange, Prexo, Upgrade, Buyback, BUP
   
→ 'SC' (Super Coin): Super Coin Rewards
   - KEYWORDS: Super Coin, SuperCoin, Reward Points
 
→ 'BOC' (Bank Offer): Bank or Card specific offer
   - KEYWORDS: Bank Offer, Card Offer, EMI Offer, HDFC, ICICI

**IF OFC (One-Off):**
- 'OFC'

OUTPUT: The code ONLY (e.g., 'PDC', 'PUC', 'CP', 'LS', 'PRX', 'OFC')."""
    )
    
    scheme_subtype_reasoning = dspy.OutputField(
        desc="""EXPLAIN YOUR SUBTYPE DECISION (based on the scheme_type you chose).

**MANDATORY CHECKS:**
1. Did you check for "Price Drop" keywords? → If yes, subtype MUST be PDC
2. Did you check the vendor against the 9 Lifestyle brands? → If match, subtype MUST be LS
3. For SELL_SIDE: Did you distinguish between:
   - CP (actual COUPON mechanism with coupon codes)
   - PUC (general pricing/sellout support, including non-coupon CP support)

Structure:
1. **Rule Application**: Which critical rules did you apply?
2. **Mechanism Analysis**: What is the specific support mechanism?
   - For SELL_SIDE: Is it Coupon (CP)? Or general pricing (PUC)? Or Lifestyle (LS)?
   - For BUY_SIDE: Is it price drop (PDC)? Or periodic (PERIODIC_CLAIM)?
3. **Key Evidence**: What specific words/phrases indicate this mechanism?
4. **Why this code?**: Why this subtype and not others in the same category?

Example: "Subtype is 'PDC' because the email explicitly states 'Price Drop effective from 24th June', which triggers the Price Drop → PDC rule."

Example: "Subtype is 'LS' because the vendor is 'Titan Company Ltd', which is in the Lifestyle vendor list, triggering the Lifestyle → LS rule."

Example: "Subtype is 'PUC' (NOT CP) because while the email mentions 'CP support', there are NO coupon codes or VPC mentioned - this is general pricing support, not a coupon mechanism."

Example: "Subtype is 'CP' because the email contains 'VPC codes' and 'customer coupon vouchers', indicating actual coupon usage mechanism."
"""
    )

