# Implementation Plan - Dynamic Output Schema

## Goal
Implement dynamic JSON output schema where fields are explicitly included/excluded based on the `scheme_type` and `scheme_subtype` determined by the LLM.

## User Requirements
1. The output fields must vary based on `scheme_type`.
2. **Specific Constraint:** `max_cap` (Global Cap Amount) must ONLY be present for `scheme_type == 'OFC'`.

## Proposed Field Logic

### 1. Base Fields (Always Present)
These fields define the core metadata and are common across all scheme types.
- `scheme_type`
- `scheme_subtype`
- `scheme_name`
- `scheme_description`
- `scheme_period`
- `duration`
- `start_date`
- `end_date`
- `discount_type`
- `vendor_name`
- `fsn_file_config_file`
- `min_actual_discount_or_agreed_claim`
- `remove_gst_from_final_claim`
- `over_and_above`
- `scheme_document`

### 2. Conditional Fields

| Field Name | Condition for Inclusion |
|------------|-------------------------|
| **max_cap** | `scheme_type == 'OFC'` |
| **brand_support_absolute** | `scheme_type == 'OFC'` |
| **gst_rate** | `scheme_type == 'OFC'` |
| **price_drop_date** | `scheme_subtype == 'PDC'` |
| **discount_slab_type** | `scheme_type == 'BUY_SIDE'` AND `scheme_subtype == 'PERIODIC_CLAIM'` |
| **best_bet** | `scheme_type == 'BUY_SIDE'` AND `scheme_subtype == 'PERIODIC_CLAIM'` |

## Proposed Changes

### [MODIFY] src/dspy_modules/field_extractor.py

Update `_build_output` method to:
1. define the comprehensive field set.
2. create a filtered dictionary based on the rules above.
3. specific removal of keys instead of setting them to "Not Applicable".

## Verification Plan

### Automated Tests
- Create a test script `test_dynamic_schema.py` that mocks the LLM output (or allows manual injection) and verifies the final JSON keys for three test cases:
  1. **OFC Case:** Verify `max_cap`, `brand_support`, `gst_rate` present. Verify PDC/Periodic fields missing.
  2. **PDC Case:** Verify `price_drop_date` present. Verify OFC fields (`max_cap`) missing.
  3. **Periodic Case:** Verify `discount_slab_type`, `best_bet` present. Verify others missing.
  4. **Sell Side Case:** Verify ONLY base fields present.

### Manual Verification
- Run `main.py` on the sample files and inspect the output JSONs in `final_output`.
