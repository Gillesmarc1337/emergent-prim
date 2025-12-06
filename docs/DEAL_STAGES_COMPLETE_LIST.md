# Complete List of Deal Stages in Codebase

This document lists **all** deal stage values found throughout the codebase, including variations and inconsistencies.

## Complete List of Distinct Stages (19 Unique Values)

All unique stage values found in the codebase, listed alphabetically:

1. **A Closed**
2. **B Legals**
3. **C Proposal sent**
4. **Closed Lost**
5. **Closed Won**
6. **D POA Booked**
7. **E Intro attended**
8. **F Inbox**
9. **G Stalled**
10. **H Lost - can be revived**
11. **H not relevant**
12. **I Lost**
13. **Legal**
14. **Lost**
15. **Not Relevant**
16. **POA Booked**
17. **Proposal sent**
18. **Signed**
19. **Won**

## Categorized List of Stages

### 🟢 Active Pipeline Stages (In Progress)

These stages represent deals actively moving through the sales pipeline:

-   **F Inbox** - Initial intro stage, deal just discovered
-   **E Intro attended** - Intro meeting has been attended
-   **D POA Booked** / **POA Booked** - Proof of Agreement booked
-   **C Proposal sent** / **Proposal sent** - Proposal has been sent to client
-   **B Legals** / **Legal** - Deal is in legal stage (hot deals, closest to closing)

**Probability Mappings:**

-   `B Legals`: 85% (high probability)
-   `C Proposal sent`: 50% (medium probability)
-   `D POA Booked`: 50% (medium probability)
-   `E Intro attended`: 25% (lower probability)

### ✅ Closed/Won Stages (Success)

These stages represent successfully closed deals:

-   **A Closed** - Deal closed (primary/canonical)
-   **Closed Won** - Deal closed and won (alternative)
-   **Won** - Deal won (alternative)
-   **Signed** - Deal signed (alternative)

**Note:** All four variations are treated as "closed won" in various parts of the codebase.

### ❌ Lost Stages (Failed)

These stages represent lost or failed deals:

-   **Lost** - Deal lost (primary/canonical)
-   **I Lost** - Deal lost (alternative)
-   **Closed Lost** - Deal closed and lost
-   **H Lost - can be revived** - Lost deal that can potentially be revived

### ⏸️ Stalled/Inactive Stages

These stages represent deals that are not actively progressing:

-   **G Stalled** - Deal is stalled (not progressing)
-   **H not relevant** - Not relevant (alternative to "Not Relevant")
-   **Not Relevant** - Deal is not relevant (primary/canonical)

## Primary Stages (Documented)

These are the stages documented in `docs/database_structure.md`:

1. **F Inbox** - Intro stage
2. **D POA Booked** - Proof of Agreement booked
3. **C Proposal sent** - Proposal sent
4. **B Legals** - Legal stage (hot deals)
5. **A Closed** - Deal closed
6. **Lost** - Deal lost
7. **Not Relevant** - Not relevant

**Note:** `E Intro attended` is used extensively in code but is **missing from the documentation**.

## Stage Variations Mapping

The following table maps all stage variations to their canonical (primary) stage names:

| Canonical Stage      | Variations Found in Code                                     |
| -------------------- | ------------------------------------------------------------ |
| **A Closed**         | `A Closed`, `Closed Won`, `Won`, `Signed`                    |
| **B Legals**         | `B Legals`, `Legal`                                          |
| **C Proposal sent**  | `C Proposal sent`, `Proposal sent`                           |
| **D POA Booked**     | `D POA Booked`, `POA Booked`                                 |
| **E Intro attended** | `E Intro attended` (no variations)                           |
| **F Inbox**          | `F Inbox` (no variations)                                    |
| **Lost**             | `Lost`, `I Lost`, `Closed Lost`, `H Lost - can be revived`   |
| **Not Relevant**     | `Not Relevant`, `H not relevant`, `Not relevant` (lowercase) |
| **G Stalled**        | `G Stalled` (no variations)                                  |

**Recommendation:** Normalize all variations to their canonical forms during data import.

## Stage Usage by Component

### Backend (`backend/server.py`)

#### Probability Mappings (lines 1519-1524):

-   `B Legals`: 85%
-   `C Proposal sent`: 50%
-   `D POA Booked`: 50%
-   `E Intro attended`: 25%

#### Attended Stages (line 1011-1012):

-   `E Intro attended`
-   `D POA Booked`
-   `C Proposal sent`
-   `B Legals`
-   `Closed Won`
-   `Won`
-   `Signed`
-   `Closed Lost`
-   `Lost`
-   `I Lost`

#### POA Generated Stages (line 1016-1018):

-   `D POA Booked`
-   `POA Booked`
-   `B Legals`
-   `Legal`
-   `C Proposal sent`
-   `Proposal sent`
-   `Closed Won`
-   `Won`
-   `Signed`
-   `Closed Lost`
-   `Lost`
-   `I Lost`

#### Deals Closed Stages (line 1022):

-   `A Closed`

#### POA Attended Stages (line 1165-1167):

-   `B Legals`
-   `Legal`
-   `C Proposal sent`
-   `Proposal sent`
-   `D POA Booked`
-   `POA Booked`
-   `Closed Won`
-   `Won`
-   `Signed`
-   `Closed Lost`
-   `Lost`
-   `I Lost`

#### POA Closed Stages (line 1171):

-   `A Closed`

#### Legacy POA Stages (line 1175-1176):

-   `A Closed`
-   `Closed Won`
-   `Won`
-   `Signed`
-   `Closed Lost`
-   `Lost`
-   `I Lost`
-   `B Legals`
-   `D POA Booked`
-   `Legal`
-   `POA Booked`

#### Active Pipeline Exclusions (various lines):

-   Excludes: `A Closed`, `I Lost`, `H not relevant`
-   Excludes: `Closed Won`, `Closed Lost`, `I Lost`

#### Old Pipeline Stages (line 2882, 3222, 3563):

-   `G Stalled`
-   `H Lost - can be revived`

#### YTD Closed Stages (line 2891, 3231, 3572):

-   `Closed Won`
-   `Won`
-   `Signed`

#### Hot Deals (line 1565):

-   `B Legals`

#### Hot Leads (line 1583):

-   `C Proposal sent`
-   `D POA Booked`

#### POA Stages for July-Dec (line 2972, 3852, 3886):

-   `D POA Booked`
-   `C Proposal sent`
-   `B Legals`
-   `A Closed`

### Frontend

#### Deal Pipeline Board (`frontend/src/features/meetings/components/DealPipelineBoard.jsx`):

-   `F Inbox` (line 20)
-   `E Intro attended` (line 34)

#### Advanced Stages Pipeline Board (`frontend/src/features/meetings/components/AdvancedStagesPipelineBoard.jsx`):

-   `D POA Booked` (line 16)
-   `C Proposal sent` (line 31)

#### Projections Board (`frontend/src/App.js`):

-   `B Legals` → 'next14' column (lines 1866, 2083, 2393, 2481)
-   `C Proposal sent` → 'next30' column (lines 1867, 2084, 2394, 2482)
-   `D POA Booked` → 'next60' column (lines 1868, 2085, 2395, 2483)

#### Meeting Details Table (`frontend/src/features/meetings/components/MeetingDetailsTable.jsx`):

-   Checks for: `Won`, `Closed Won`, `Lost`, `POA`, `Legal` (line 170-172)

#### Closing Projections Card (`frontend/src/features/projections/components/ClosingProjectionsCard.jsx`):

-   `B Legals` (line 18)
-   `C Proposal sent` (line 19)

## Stage Variations and Inconsistencies

### Same Concept, Different Names:

1. **Closed/Won:**

    - `A Closed` (primary)
    - `Closed Won`
    - `Won`
    - `Signed`

2. **Lost:**

    - `Lost` (primary)
    - `I Lost`
    - `Closed Lost`
    - `H Lost - can be revived`

3. **Not Relevant:**

    - `Not Relevant` (primary)
    - `H not relevant`
    - `Not relevant` (lowercase in some UI)

4. **POA Booked:**

    - `D POA Booked` (primary)
    - `POA Booked`

5. **Proposal Sent:**

    - `C Proposal sent` (primary)
    - `Proposal sent`

6. **Legals:**
    - `B Legals` (primary)
    - `Legal`

## Issues Identified

1. **No Validation on Import**: Stages are accepted as-is from CSV/Google Sheets without normalization
2. **Hardcoded Checks**: Many components use hardcoded stage string comparisons
3. **Inconsistent Naming**: Multiple variations exist for the same stage concept
4. **Case Sensitivity**: Some checks use `.includes()` which is case-sensitive
5. **Missing Stages**: `E Intro attended` is used in code but not in documentation

## Recommendations

1. Create a centralized stage constants file
2. Implement stage normalization on import
3. Map all variations to canonical stage names
4. Update documentation to include all stages actually used
5. Add validation to reject unknown stages or normalize them automatically
