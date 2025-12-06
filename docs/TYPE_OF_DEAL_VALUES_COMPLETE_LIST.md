# Complete List of Type of Deal Values in Codebase

This document lists **all** `type_of_deal` property values found throughout the codebase, including variations, inconsistencies, and usage patterns.

## Quick Reference

| Value          | Status        | Backend Detection | Frontend Match | Visual Indicator |
| -------------- | ------------- | ----------------- | -------------- | ---------------- |
| `Upsell`       | ✅ Primary    | ✅ (variations)   | ✅ (exact)     | Purple badge     |
| `Cross-sell`   | ✅ Primary    | ⚠️ Not detected   | ✅ (exact)     | Green badge      |
| `Renewal`      | ✅ Primary    | ✅ (variations)   | ⚠️ Unknown     | N/A              |
| `New Business` | 📝 Documented | ❌ Not checked    | ❌ Not checked | N/A              |
| `null`         | ✅ Accepted   | N/A               | N/A            | N/A              |

## Complete List of Distinct Values

1. **Upsell** - Upsell deal (primary/canonical)
2. **Cross-sell** - Cross-sell deal (primary/canonical)
3. **Renewal** - Renewal deal (primary/canonical, variations accepted)
4. **New Business** - New business deal (documented example)
5. **null** or empty string - No deal type assigned

## Value Categories

### 🔄 Upsell/Cross-sell Deals

Additional sales to existing clients.

-   **Upsell** - Upsell deal (primary/canonical)
-   **Cross-sell** - Cross-sell deal (primary/canonical)

**Backend Detection:** The `is_upsell()` function accepts case-insensitive variations:

-   `upsell`, `up-sell`, `up sell` (for upsell)
-   ⚠️ **Issue:** `cross-sell` variations are NOT detected by backend function

**Frontend Display:**

-   Purple badge (`bg-purple-100 text-purple-800`) for `Upsell`
-   Green badge (`bg-green-100 text-green-800`) for `Cross-sell` and other non-upsell types

**Note:** Both `Upsell` and `Cross-sell` are grouped together in analytics as "Upsells/Cross-sell".

### 🔁 Renewal Deals

Contract renewals.

-   **Renewal** - Renewal deal (primary/canonical)

**Backend Detection:** The `is_renewal()` function accepts case-insensitive variations:

-   `renew`, `renewal`, `re-new`

### 🆕 New Business Deals

New customer acquisitions.

-   **New Business** - New business deal (documented in database structure example)

**Note:** This value appears in documentation but is not explicitly checked in code logic.

### 🔘 Unassigned/Unknown

-   **null** or empty string - No deal type assigned

## Value Variations Mapping

| Canonical Category | Values Found in Code                   | Backend Detection              | Frontend Match |
| ------------------ | -------------------------------------- | ------------------------------ | -------------- |
| **Upsell**         | `Upsell` (exact match in frontend)     | `upsell`, `up-sell`, `up sell` | ✅ Exact       |
| **Cross-sell**     | `Cross-sell` (exact match in frontend) | ⚠️ Not detected                | ✅ Exact       |
| **Renewal**        | `Renewal` (variations accepted)        | `renew`, `renewal`, `re-new`   | ⚠️ Unknown     |
| **New Business**   | `New Business` (documented)            | ❌ Not checked                 | ❌ Not checked |
| **Unassigned**     | `null`, empty string                   | N/A                            | N/A            |

**Recommendation:** Normalize all variations to their canonical forms during data import for consistency.

## Implementation Details

### Backend (`backend/server.py`)

#### Upsell Detection Function (lines 817-823):

```817:823:backend/server.py
def is_upsell(deal_type):
    """Check if a deal type is an upsell/cross-sell (case-insensitive, handles variations)"""
    if pd.isna(deal_type):
        return False
    deal_type_str = str(deal_type).lower().strip()
    # Match: "upsell", "up-sell", "up sell", "cross-sell", "crosssell"
    return 'upsell' in deal_type_str or 'up-sell' in deal_type_str or 'up sell' in deal_type_str
```

**Key Points:**

-   Case-insensitive matching
-   Accepts variations: `upsell`, `up-sell`, `up sell`
-   ⚠️ **Does NOT check for `cross-sell`** despite comment mentioning it
-   Returns `False` for `null`/empty values

#### Renewal Detection Function (lines 825-831):

```825:831:backend/server.py
def is_renewal(deal_type):
    """Check if a deal type is a renewal (case-insensitive)"""
    if pd.isna(deal_type):
        return False
    deal_type_str = str(deal_type).lower().strip()
    # Match: "renew", "renewal", "re-new"
    return 'renew' in deal_type_str
```

**Key Points:**

-   Case-insensitive matching
-   Accepts any string containing "renew" (matches: `renew`, `renewal`, `re-new`)
-   Returns `False` for `null`/empty values

#### Data Import (lines 462, 2740, 4542, 4669):

```python
type_of_deal=str(row.get('type_of_deal', '')) if not pd.isna(row.get('type_of_deal')) else None
```

Deal type values are imported as strings, with `None` for missing values.

#### Analytics Usage:

**Upsell/Cross-sell Filtering:**

-   Used extensively in analytics calculations (lines 2985, 3094, 3101, 3337, 3448, 3455, 3644, 3701, 3706, 3809, 3832, 4252)
-   Filters deals where `is_upsell()` returns `True`
-   Grouped as "Upsells/Cross-sell" in reports

**Renewal Filtering:**

-   Used in upsell/renewal analytics (lines 3809, 3833, 3866)
-   Filters deals where `is_renewal()` returns `True`
-   Separated from upsells in partner performance reports

### Frontend

#### UpsellRenewTab Component (`frontend/src/features/upsell/components/UpsellRenewTab.jsx`):

**Filtering Logic (line 55):**

```javascript
if ((deal.type_of_deal === 'Upsell' || deal.type_of_deal === 'Cross-sell') && deal.partner) {
```

**Visual Display (lines 270-272, 324-326):**

```javascript
intro.type_of_deal === 'Upsell'
    ? 'bg-purple-100 text-purple-800'
    : 'bg-green-100 text-green-800';
```

**Key Points:**

-   Uses exact string matching (`===`)
-   Case-sensitive: `'Upsell'` ≠ `'upsell'`
-   Purple badge for `Upsell`, green for `Cross-sell` and other types

#### Main App (`frontend/src/App.js`):

**Filtering Logic (lines 6492-6493):**

```javascript
(deal.type_of_deal === 'Upsell' || deal.type_of_deal === 'Cross-sell') &&
    deal.partner;
```

**Display (lines 6804-6810, 6898-6904):**

-   Shows `type_of_deal` value directly in tables
-   Uses same color coding as UpsellRenewTab

#### DealsClosedTab Component (`frontend/src/features/deals/components/DealsClosedTab.jsx`):

**Display (line 115):**

```javascript
<Badge variant='outline'>{deal.type_of_deal}</Badge>
```

Shows deal type as a badge without color coding.

### Database Structure (`docs/database_structure.md`)

**Field Definition (line 262):**

```markdown
"type_of_deal": String | null, // Deal type
```

**Example Value (line 321):**

```markdown
"type_of_deal": "New Business",
```

## Critical Issues

### 1. Case Sensitivity Mismatch

**Backend:** Case-insensitive matching (uses `.lower()`)

-   `is_upsell()`: Accepts `upsell`, `Upsell`, `UPSELL`, `up-sell`, etc.
-   `is_renewal()`: Accepts `renew`, `Renewal`, `RENEWAL`, `re-new`, etc.

**Frontend:** Case-sensitive exact matching (`===`)

-   Only matches: `'Upsell'` and `'Cross-sell'` (exact case)
-   `'upsell'` or `'UPSELL'` will NOT match in frontend checks

**Impact:**

-   Backend may classify a deal as upsell/renewal
-   Frontend may not display it correctly if casing doesn't match exactly

### 2. Missing Cross-sell Detection

**Issue:** The `is_upsell()` function does NOT explicitly check for `cross-sell` variations, but:

-   Frontend uses `'Cross-sell'` as a valid value
-   Analytics groups upsells and cross-sells together
-   The function comment mentions "cross-sell" but doesn't implement it

**Recommended Fix:** Update `is_upsell()` to include cross-sell detection:

```python
return ('upsell' in deal_type_str or 'up-sell' in deal_type_str or 'up sell' in deal_type_str or
        'cross-sell' in deal_type_str or 'crosssell' in deal_type_str)
```

### 3. No Data Validation

Deal type values are accepted as-is from CSV/Google Sheets without normalization, leading to:

-   Inconsistent casing
-   Multiple variations of the same value
-   Frontend display issues

## Recommendations

1. **Create Centralized Constants:** Define deal type values in a constants file
2. **Implement Normalization:** Normalize variations on import:
    - `upsell`, `up-sell`, `up sell` → `Upsell`
    - `cross-sell`, `crosssell` → `Cross-sell`
    - `renew`, `renewal`, `re-new` → `Renewal`
3. **Fix Cross-sell Detection:** Update `is_upsell()` to include cross-sell checks
4. **Standardize Matching:** Use consistent case-insensitive matching in both backend and frontend
5. **Add Validation:** Reject unknown deal types or normalize them automatically
6. **Update Documentation:** Clarify which values are actually used vs. documented

## Best Practices

**For Data Entry:**

-   Use primary values (`Upsell`, `Cross-sell`, `Renewal`) with exact casing
-   Avoid variations like `up-sell`, `renew`, etc.

**For Data Import:**

-   Normalize all variations to canonical forms during import
-   Match frontend expectations: `Upsell` (capital U), `Cross-sell` (capital C, hyphen)

**For Code:**

-   Update `is_upsell()` to include cross-sell detection
-   Consider using case-insensitive matching in frontend or normalizing data before display
