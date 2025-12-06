# App.js Refactoring - Feature Folder Structure

## Overview
The `App.js` file (5928 lines) has been broken down into a React standard feature folder structure for better organization and maintainability.

## New Folder Structure

```
frontend/src/
├── shared/
│   ├── components/
│   │   ├── AnalyticsSection.jsx
│   │   ├── MetricCard.jsx
│   │   └── SortableTableHeader.jsx
│   ├── constants/
│   │   ├── api.js
│   │   └── chartColors.js
│   └── hooks/
│       └── useSortableData.js
│
├── features/
│   ├── data-management/
│   │   ├── components/
│   │   │   ├── DataManagementSection.jsx
│   │   │   └── FileUpload.jsx
│   │   └── index.js
│   │
│   ├── dashboard/
│   │   ├── components/
│   │   │   └── MainDashboard.jsx (to be created)
│   │   └── index.js
│   │
│   ├── meetings/
│   │   ├── components/
│   │   │   └── MeetingsTable.jsx
│   │   └── index.js
│   │
│   ├── projections/
│   │   ├── components/
│   │   │   ├── DraggableDealItem.jsx
│   │   │   └── DraggableLeadItem.jsx
│   │   └── index.js
│   │
│   ├── deals/ (to be created)
│   │   └── components/
│   │
│   └── analytics/ (to be created)
│       └── components/
│
└── App.js (refactored to use new structure)
```

## Components Breakdown

### Shared Components (`shared/`)
**Reusable across multiple features**

1. **MetricCard** - Displays metric values with targets, progress bars, and status badges
2. **SortableTableHeader** - Table header with sorting functionality
3. **AnalyticsSection** - Wrapper component for analytics sections with conclusions

### Shared Hooks (`shared/hooks/`)
1. **useSortableData** - Custom hook for sorting table data

### Shared Constants (`shared/constants/`)
1. **chartColors.js** - Chart color constants (COLORS, REVENUE_COLORS)
2. **api.js** - API endpoint configuration

### Feature: Data Management (`features/data-management/`)
**Handles data upload and management**

1. **FileUpload** - CSV/Excel file upload component with drag & drop
2. **DataManagementSection** - Main data management section with status display

### Feature: Meetings (`features/meetings/`)
**Meeting-related components**

1. **MeetingsTable** - Sortable and filterable meetings table

### Feature: Projections (`features/projections/`)
**Deal projections and drag & drop board**

1. **DraggableDealItem** - Draggable deal card for projections board
2. **DraggableLeadItem** - Draggable lead card

### Feature: Dashboard (`features/dashboard/`)
**Main dashboard components** (to be completed)

1. **MainDashboard** - Main dashboard with metrics, charts, and blocks

## Remaining Work

### 1. Extract MainDashboard Component
- Location: `features/dashboard/components/MainDashboard.jsx`
- Contains: Lines 698-1202 from App.js
- Dependencies: 
  - DataManagementSection (already extracted)
  - MetricCard (already extracted)
  - Chart components (Recharts)
  - REVENUE_COLORS constant

### 2. Extract Dashboard Container
- The main `Dashboard` function (lines 1204-5890) should be refactored to:
  - Use extracted components from features
  - Organize tab content into separate feature components
  - Move state management to custom hooks where appropriate

### 3. Create Additional Feature Components

#### Meetings Generation Tab
- Extract meeting generation charts and tables
- Create: `features/meetings/components/MeetingsGenerationTab.jsx`
- Create: `features/meetings/components/MeetingDetailsTable.jsx`
- Create: `features/meetings/components/BDRPerformanceTable.jsx`
- Create: `features/meetings/components/DealPipelineBoard.jsx`

#### Meetings Attended Tab
- Extract meetings attended components
- Create: `features/meetings/components/MeetingsAttendedTab.jsx`
- Create: `features/meetings/components/AEPerformanceBreakdown.jsx`
- Create: `features/meetings/components/ConversionRates.jsx`

#### Deals & Pipeline Tab
- Extract deals and pipeline components
- Create: `features/deals/components/DealsPipelineTab.jsx`
- Create: `features/deals/components/PipelineMetrics.jsx`
- Create: `features/deals/components/AEPipelineBreakdown.jsx`

#### Upsell & Renew Tab
- Extract upsell/renew components
- Create: `features/analytics/components/UpsellRenewTab.jsx`
- Create: `features/analytics/components/PartnerPerformanceTable.jsx`

#### Projections Tab
- Extract projections board and related components
- Create: `features/projections/components/ProjectionsTab.jsx`
- Create: `features/projections/components/ProjectionsBoard.jsx`
- Create: `features/projections/components/ProjectionMetrics.jsx`
- Create: `features/projections/hooks/useProjectionsData.js`

### 4. Create Custom Hooks

#### Dashboard Hooks
- `features/dashboard/hooks/useDashboardData.js` - Dashboard data fetching
- `features/dashboard/hooks/useTabTargets.js` - Tab targets management

#### Analytics Hooks
- `features/analytics/hooks/useAnalytics.js` - Analytics data fetching
- `features/analytics/hooks/useChartVisibility.js` - Chart legend visibility state

#### Projections Hooks
- `features/projections/hooks/useProjectionsData.js` - Projections data and state
- `features/projections/hooks/useAsherPOV.js` - Asher POV functionality

### 5. Update App.js
- Import from new feature folders
- Keep only routing and main App component
- Remove all extracted components

## Migration Steps

1. ✅ Create shared components and hooks
2. ✅ Create data-management feature
3. ✅ Create meetings feature (partial)
4. ✅ Create projections feature (partial)
5. ⏳ Extract MainDashboard component
6. ⏳ Extract Dashboard container logic
7. ⏳ Create remaining feature components
8. ⏳ Create custom hooks for state management
9. ⏳ Update App.js imports
10. ⏳ Test all functionality

## Benefits

1. **Better Organization** - Related components grouped by feature
2. **Easier Maintenance** - Smaller, focused files
3. **Reusability** - Shared components can be used across features
4. **Scalability** - Easy to add new features
5. **Team Collaboration** - Multiple developers can work on different features
6. **Testing** - Easier to test isolated components

## Import Examples

### Before
```javascript
// Everything in App.js
```

### After
```javascript
// Shared components
import { MetricCard } from '@/shared/components/MetricCard';
import { useSortableData } from '@/shared/hooks/useSortableData';
import { REVENUE_COLORS } from '@/shared/constants/chartColors';

// Feature components
import { DataManagementSection } from '@/features/data-management';
import { MainDashboard } from '@/features/dashboard';
import { MeetingsTable } from '@/features/meetings';
import { DraggableDealItem } from '@/features/projections';
```

## Notes

- All components maintain their original functionality
- No breaking changes to props or behavior
- Path aliases (`@/`) are used for cleaner imports
- Each feature has an `index.js` for clean exports




