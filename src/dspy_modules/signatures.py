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
    # Field 3: Additional Conditions
    # ============================================================================
    additional_conditions = dspy.OutputField(
        desc="""Extract special conditions, restrictions, or requirements.
LOOK FOR: Caps/limits, exclusions, proof requirements, payment terms, eligibility rules.
EXAMPLES: 'Max 2 units per order', 'Proof of display required', 'Applicable on listed FSNs only'.
OUTPUT: Comma-separated list OR 'None specified' if none found."""
    )
    additional_conditions_reasoning = dspy.OutputField(
        desc="REASONING: What special terms or restrictions did you identify?"
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
FORMAT: 'DD/MM/YYYY' or 'N/A' if not PDC scheme."""
    )
    price_drop_date_reasoning = dspy.OutputField(
        desc="REASONING: Is this a PDC scheme? What price drop date was mentioned?"
    )
    
    # ============================================================================
    # Field 10 & 11: Start & End Dates
    # ============================================================================
    start_date = dspy.OutputField(
        desc="""Extract scheme START date. Format: 'DD/MM/YYYY' or 'Not Specified'.
PRIORITY: Scheme start > Invoice start > Email date."""
    )
    start_date_reasoning = dspy.OutputField(
        desc="REASONING: How did you identify the start date?"
    )
    
    end_date = dspy.OutputField(
        desc="""Extract scheme END date. Format: 'DD/MM/YYYY' or 'Not Specified'.
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

**BUY_SIDE** (Claim ID prefix: BS-PC or PDC-PDC)
→ WHAT IT MEANS: Support on PURCHASE/INWARD side. Brand helps Flipkart with purchase costs.
→ BUSINESS CONTEXT: Schemes tied to what Flipkart BUYS from the brand.
→ INDICATORS:
  - Sellin incentives (not sellout)
  - JBP/Joint Business Plan, TOT/Terms of Trade
  - Quarterly/Annual business plans (Q1, Q2, FY support)
  - NRV-linked, inwards support, inventory funding
  - Price Protection/Price Drop on cost side

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

**ONE_OFF** (Claim ID prefix: OFC-OFC)
→ WHAT IT MEANS: One-time, ad-hoc support not tied to regular schemes.
→ BUSINESS CONTEXT: Special approval for specific situation, not part of JBP/regular plan.
→ INDICATORS:
  - 'One off', 'one-off', 'one time'
  - Ad-hoc approval, special sanction
  - Specific amount approved for exception

OUTPUT: Exactly 'BUY_SIDE', 'SELL_SIDE', or 'ONE_OFF'.
THINK: Is this about helping purchase (BUY) or helping sell (SELL) or a special exception (ONE_OFF)?"""
    )
    
    scheme_subtype = dspy.OutputField(
        desc="""CLASSIFY THE SUBTYPE based on scheme_type.
        
**IF BUY_SIDE, choose one:**
- 'PERIODIC_CLAIM' (BS-PC)
- 'PDC' (PDC-PDC)

**IF SELL_SIDE, choose one of these EXACT CODES:**
  
1. **'CP'** (Coupon/VPC): Customer discount via coupon/voucher/code.
   → KEYWORDS: Coupon, VPC, Voucher, Promo Code.
   → REASONING: "Mechanism is coupon usage."

2. **'PUC'** (PUC/FDC): Pricing support/Price matching.
   → KEYWORDS: PUC, FDC, Sellout Support, Price Match, Competitive Pricing.
   → REASONING: "General pricing support to match competition."

3. **'PRX'** (Prexo/Exchange): Product Exchange/Buyback.
   → KEYWORDS: Exchange, Prexo, Upgrade, Buyback, BUP.
   → REASONING: "Linked to exchanging old devices."
   
4. **'SC'** (Super Coin): Super Coin Rewards.
   → KEYWORDS: Super Coin, SuperCoin, Reward Points.
   → REASONING: "Funded via Super Coins."

5. **'BOC'** (Bank Offer): Bank or Card specific offer.
   → KEYWORDS: Bank Offer, Card Offer, EMI Offer, HDFC, ICICI.
   → REASONING: "Tied to specific bank cards."

6. **'LS'** (Lifestyle): Lifestyle category specific.
   → KEYWORDS: Lifestyle, Fashion.

**IF ONE_OFF:**
- 'N/A'

OUTPUT: The code ONLY (e.g., 'CP', 'PUC', 'PRX')."""
    )
    
    scheme_classification_reasoning = dspy.OutputField(
        desc="""PROVIDE DETAILED REASONING for your classification.
        
1. **Analyze Scheme Type**: Why is it BUY_SIDE or SELL_SIDE?
2. **Analyze Mechanism (CRITICAL)**:
   - Does it mention "Coupons" or "VPC"? -> Must be 'CP'.
   - Does it mention "Exchange" or "BUP"? -> Must be 'PRX'.
   - Does it mention "Bank" or "Card"? -> Must be 'BOC'.
   - Is it just "Price Support" or "FDC"? -> Must be 'PUC'.
3. **Final Decision**: State the code based on the mechanism."""
    )
