# Complete List of Relevance Values in Codebase

This document lists **all** relevance property values found throughout the codebase, including variations and their usage.

## Complete List of Distinct Values (5 Unique Values)

All unique relevance values found in the codebase:

1. **Relevant** - Meeting is relevant (primary/canonical)
2. **Question mark** - Meeting relevance is questionable (primary/canonical)
3. **Maybe** - Meeting relevance is questionable (alternative to "Question mark")
4. **Not relevant** - Meeting is not relevant (primary/canonical)
5. **all** - Filter value to show all relevance types (UI filter only)

**Note:** `null` or empty string is also accepted and represents meetings without a relevance value assigned.

## Categorized List of Values

### ✅ Relevant Meetings (Positive)

- **Relevant** - Meeting is confirmed as relevant to the business

**Visual Indicator:** Green badge (`bg-green-500`)

### ❓ Questionable Meetings (Uncertain)

- **Question mark** - Meeting relevance is uncertain (primary/canonical)
- **Maybe** - Meeting relevance is uncertain (alternative)

**Visual Indicator:** Yellow badge (`bg-yellow-500`)

**Note:** Both `Question mark` and `Maybe` are treated as equivalent in the codebase and both display with a yellow indicator.

### ❌ Not Relevant Meetings (Negative)

- **Not relevant** - Meeting is confirmed as not relevant

**Visual Indicator:** Red badge (`bg-red-500`)

### 🔘 Unassigned/Unknown

- **null** or empty string - No relevance value assigned

**Visual Indicator:** Gray badge (`bg-gray-500`)

### 🔍 Filter Value

- **all** - Special filter value used in dropdowns to show all relevance types (not stored in database)

## Value Variations Mapping

The following table maps all relevance variations to their canonical (primary) categories:

| Canonical Category | Values Found in Code                    | Visual Indicator |
| ------------------ | --------------------------------------- | ---------------- |
| **Relevant**       | `Relevant`                               | Green            |
| **Questionable**   | `Question mark`, `Maybe`                | Yellow           |
| **Not Relevant**   | `Not relevant`                           | Red              |
| **Unassigned**     | `null`, empty string                     | Gray             |
| **Filter**         | `all` (UI only, not stored)              | N/A              |

**Recommendation:** Normalize `Maybe` to `Question mark` during data import for consistency.

## Usage by Component

### Backend (`backend/server.py`)

#### Relevance Analysis (lines 876-879):

```python
relevant = period_data[period_data['relevance'] == 'Relevant']
question_mark = period_data[period_data['relevance'].isin(['Question mark', 'Maybe'])]
not_relevant = period_data['relevance'] == 'Not relevant']
```

**Key Points:**
- `Relevant` is checked with exact match (`==`)
- `Question mark` and `Maybe` are both accepted using `.isin()`
- `Not relevant` is checked with exact match (`==`)

#### Relevance Rate Calculation (line 884):

```python
'relevance': lambda x: (x == 'Relevant').sum()
```

Only `Relevant` meetings are counted in relevance rate calculations.

#### Data Import (lines 456, 2734, 4536, 4663):

```python
relevance=str(row.get('relevance', '')) if not pd.isna(row.get('relevance')) else None
```

Relevance values are imported as strings, with `None` for missing values.

### Frontend

#### Meeting Details Table (`frontend/src/features/meetings/components/MeetingDetailsTable.jsx`):

**Filter Dropdown (lines 82-89):**
- Default value: `'all'`
- Options: `'all'`, `'Relevant'`, `'Question mark'`, `'Maybe'`, `'Not relevant'`

**Visual Display (lines 160-164):**
```javascript
meeting.relevance === 'Relevant' ? 'bg-green-500' :
meeting.relevance === 'Question mark' || meeting.relevance === 'Maybe' ? 'bg-yellow-500' :
meeting.relevance === 'Not relevant' ? 'bg-red-500' :
'bg-gray-500'
```

**Filtering Logic (line 28):**
```javascript
if (filters.relevance !== 'all' && meeting.relevance !== filters.relevance) return false;
```

#### Main App (`frontend/src/App.js`):

**Relevance Data for Charts (lines 2716-2729):**
```javascript
const relevanceData = [
    { name: 'Relevant', value: analytics.meeting_generation.relevance_analysis.relevant, color: '#00C49F' },
    { name: 'Questionable', value: analytics.meeting_generation.relevance_analysis.question_mark, color: '#FFBB28' },
    { name: 'Not Relevant', value: analytics.meeting_generation.relevance_analysis.not_relevant, color: '#FF8042' }
];
```

**Visual Display (lines 3782-3793):**
- Same color coding logic as MeetingDetailsTable
- Green for `Relevant`
- Yellow for `Question mark` or `Maybe`
- Red for `Not relevant`
- Gray for unassigned

**Filter Default (line 2596):**
```javascript
relevance: 'all',
```

#### Relevance Analysis Component (`frontend/src/features/meetings/components/RelevanceAnalysis.jsx`):

**Data Mapping (lines 9-12):**
```javascript
const relevanceData = [
    { name: 'Relevant', value: relevanceAnalysis.relevant, color: '#00C49F' },
    { name: 'Questionable', value: relevanceAnalysis.question_mark, color: '#FFBB28' },
    { name: 'Not Relevant', value: relevanceAnalysis.not_relevant, color: '#FF8042' }
];
```

**Relevance Rate Display (line 20):**
```javascript
Relevance Rate: {relevanceAnalysis.relevance_rate.toFixed(1)}%
```

### Database Structure (`docs/database_structure.md`)

**Field Definition (line 256):**
```markdown
"relevance": String | null,         // Relevance indicator
```

**Example Value (line 315):**
```markdown
"relevance": "High",
```

**Note:** The example shows `"High"` which is not found in the actual codebase. This appears to be outdated documentation.

## Value Variations and Inconsistencies

### Same Concept, Different Names:

1. **Questionable:**
   - `Question mark` (primary/canonical)
   - `Maybe` (alternative)

### Case Sensitivity

All relevance checks in the codebase use exact string matching (`===` or `==`), which means:
- `'Relevant'` ≠ `'relevant'` (case-sensitive)
- `'Not relevant'` ≠ `'Not Relevant'` (case-sensitive)

**Current Implementation:** The codebase uses exact case matching, so data must match exactly.

## Issues Identified

1. **Case Sensitivity:** All checks use exact string matching, which could cause issues if data has inconsistent casing
2. **Alternative Value:** `Maybe` is accepted but `Question mark` is the canonical form
3. **No Validation:** Relevance values are accepted as-is from CSV/Google Sheets without normalization
4. **Outdated Documentation:** Database structure example shows `"High"` which doesn't exist in code
5. **Missing Normalization:** No centralized normalization of `Maybe` → `Question mark`

## Recommendations

1. **Create Centralized Constants:** Define relevance values in a constants file
2. **Implement Normalization:** Normalize `Maybe` to `Question mark` on import
3. **Add Validation:** Reject unknown relevance values or normalize them automatically
4. **Case Normalization:** Normalize casing on import (e.g., `'relevant'` → `'Relevant'`)
5. **Update Documentation:** Fix database structure example to show actual values
6. **Type Safety:** Consider using enums or constants instead of string literals

## Expected Values Summary

For data import and API usage, the following values are expected:

| Value           | Status      | Description                          |
| --------------- | ----------- | ------------------------------------ |
| `Relevant`      | ✅ Primary  | Meeting is relevant                  |
| `Question mark` | ✅ Primary  | Meeting relevance is questionable    |
| `Maybe`         | ⚠️ Accepted | Alternative to "Question mark"       |
| `Not relevant`  | ✅ Primary  | Meeting is not relevant              |
| `null`          | ✅ Accepted | No relevance assigned                |
| `all`           | 🔍 Filter   | UI filter only (not stored in DB)    |

**Best Practice:** Use the primary values (`Relevant`, `Question mark`, `Not relevant`) for new data entry.


