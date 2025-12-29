# ✅ LLM Prompt Enhanced - Business Rules Added

## Three Critical Rules Implemented

### **RULE 1: Price Drop → PDC/PDC**

**Trigger:** If email mentions:
- "Price Drop"
- "NLC reduction"
- "cost reduction"
- "price protection"

**Action:**
```
scheme_type = 'BUY_SIDE'
scheme_subtype = 'PDC'
```

**Example:**
```
Email: "Price Drop effective from 24th June for realme P3 X 5G"
Output: scheme_type='BUY_SIDE', sub_type='PDC'
```

---

### **RULE 2: Lifestyle Vendors → SELL-SIDE/LS**

**Trigger:** If vendor is ANY of these 9 brands:
1. ADITYA BIRLA LIFESTYLE BRANDS LIMITED
2. ADITYA BIRLA FASHION AND RETAIL LIMITED
3. MGI DISTRIBUTION PVT LTD
4. BRAND CONCEPTS LIMITED
5. Timex Group India Limited
6. Titan Company Ltd
7. METRO BRANDS LIMITED
8. SUMITSU APPAREL PVT. LTD.
9. Sea Turtle Private Limited

**Action:**
```
scheme_type = 'SELL_SIDE'
scheme_subtype = 'LS' (LIFESTYLE)
```

**Example:**
```
Email from: Titan Company Ltd
Output: scheme_type='SELL_SIDE', sub_type='LS'
(Regardless of other keywords in email)
```

---

### **RULE 3: PUC vs CP Distinction**

**CP (Coupon):** ONLY for actual COUPON mechanisms
```
Keywords: Coupon, VPC, Voucher, Promo Code, Coupon Code
Mechanism: Customer uses a coupon/voucher code at checkout
Example: "VPC codes for customer discounts"
```

**PUC (General Pricing):** CP/Pricing/Sellout Support/rest all
```
INCLUDES:
- CP support (when NOT coupon-based)
- Pricing support
- Sellout support
- Competitive pricing
- FDC support

Keywords: PUC, FDC, Sellout Support, Price Match, CP (when NOT coupon), Pricing support
Mechanism: General support for selling price, NOT via coupon mechanism
Default: Use PUC if unclear between PUC and CP

Examples:
- "CP support for competitive pricing" → PUC (NOT CP)
- "Sellout support of 5%" → PUC
- "FDC for price matching" → PUC
```

---

## Prompt Changes Summary

### **In scheme_type field:**

**Added:**
```python
**CRITICAL RULE 1 - PRICE DROP DETECTION:**
→ If email mentions "Price Drop", "NLC reduction", "cost reduction" → scheme_type = 'BUY_SIDE'

**CRITICAL RULE 2 - LIFESTYLE VENDOR DETECTION:**
→ If vendor is ANY of 9 Lifestyle brands → scheme_type = 'SELL_SIDE'
```

### **In scheme_subtype field:**

**Added:**
```python
**CRITICAL: Apply these rules FIRST:**
1. If "Price Drop" → subtype = 'PDC'
2. If Lifestyle vendor → subtype = 'LS'

**CRITICAL RULE 3 - PUC vs CP DISTINCTION:**
CP = ONLY actual COUPON mechanisms (VPC/Voucher codes)
PUC = General pricing/sellout support (including non-coupon CP support)
```

### **In reasoning fields:**

**Added mandatory checks:**
```python
1. Did you check for "Price Drop" keywords? → If yes, MUST be PDC
2. Did you check vendor against 9 Lifestyle brands? → If match, MUST be LS
3. For SELL_SIDE: Did you distinguish CP (coupon) vs PUC (pricing)?
```

---

## Examples in Prompt

### **Example 1: Price Drop**
```
Email: "Price Drop effective from 24th June"
Reasoning: "Subtype is 'PDC' because the email explicitly states 'Price Drop effective from 24th June', which triggers the Price Drop → PDC rule."
Output: scheme_type='BUY_SIDE', sub_type='PDC'
```

### **Example 2: Lifestyle Vendor**
```
Email from: Titan Company Ltd
Reasoning: "Subtype is 'LS' because the vendor is 'Titan Company Ltd', which is in the Lifestyle vendor list, triggering the Lifestyle → LS rule."
Output: scheme_type='SELL_SIDE', sub_type='LS'
```

### **Example 3: PUC vs CP**
```
Email: "CP support for competitive pricing"
Reasoning: "Subtype is 'PUC' (NOT CP) because while the email mentions 'CP support', there are NO coupon codes or VPC mentioned - this is general pricing support, not a coupon mechanism."
Output: sub_type='PUC'

Email: "VPC codes for customer discounts"
Reasoning: "Subtype is 'CP' because the email contains 'VPC codes' and 'customer coupon vouchers', indicating actual coupon usage mechanism."
Output: sub_type='CP'
```

---

## What This Prevents

### **Before (Without Rules):**
```
Email: "Price Drop from 24th"
Wrong Output: scheme_type='SELL_SIDE', sub_type='PUC'
(LLM might misclassify based on other keywords)
```

### **After (With Rules):**
```
Email: "Price Drop from 24th"
Correct Output: scheme_type='BUY_SIDE', sub_type='PDC'
(Rule explicitly enforces PDC classification)
```

---

### **Before (Without Lifestyle Rule):**
```
Email from: Titan Company Ltd about "Sellout support"
Wrong Output: scheme_type='SELL_SIDE', sub_type='PUC'
(Misses Lifestyle classification)
```

### **After (With Lifestyle Rule):**
```
Email from: Titan Company Ltd about "Sellout support"
Correct Output: scheme_type='SELL_SIDE', sub_type='LS'
(Lifestyle vendor rule overrides other keywords)
```

---

### **Before (Without PUC/CP Distinction):**
```
Email: "CP support for pricing"
Wrong Output: sub_type='CP'
(Confuses CP support with CP coupons)
```

### **After (With PUC/CP Distinction):**
```
Email: "CP support for pricing"
Correct Output: sub_type='PUC'
(Correctly identifies as general pricing, not coupon)
```

---

## Implementation Status

✅ Rule 1: Price Drop → PDC/PDC (IMPLEMENTED)  
✅ Rule 2: Lifestyle Vendors → SELL-SIDE/LS (IMPLEMENTED)  
✅ Rule 3: PUC vs CP Distinction (IMPLEMENTED)  

**All three rules are now active in:** `src/dspy_modules/signatures.py`

The LLM will now:
1. Check Price Drop keywords FIRST → If found, enforce PDC
2. Check vendor against Lifestyle list FIRST → If match, enforce LS
3. Distinguish between CP (coupons) and PUC (general pricing) clearly

**These rules will apply to all future extractions!**
