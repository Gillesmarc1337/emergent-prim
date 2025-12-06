# Migration Guide - Using the New Structure

This guide shows how to update `App.js` and `Dashboard` to use the new professional structure.

## 🔄 Import Changes

### Before (Old App.js)
```javascript
// Everything defined in App.js
function useSortableData(items, config) { ... }
function MetricCard({ title, value, ... }) { ... }
function MainDashboard({ analytics, ... }) { ... }
```

### After (New Structure)
```javascript
// Shared components
import { MetricCard, SortableTableHeader, AnalyticsSection } from '@/shared/components';
import { useSortableData } from '@/shared/hooks';
import { REVENUE_COLORS, COLORS, API } from '@/shared/constants';
import { formatDate, formatValue, getAgingBadge } from '@/shared/utils';

// Services
import { analyticsService, projectionsService, dataService, viewsService } from '@/services/api';

// Features
import { MainDashboard, useDashboardData, useTabTargets } from '@/features/dashboard';
import { DataManagementSection, FileUpload } from '@/features/data-management';
import { MeetingsTable } from '@/features/meetings';
import { DraggableDealItem, DraggableLeadItem } from '@/features/projections';
import { useAnalytics, useUpsellRenew } from '@/features/analytics';
```

## 📝 Example: Refactored Dashboard Component

### Before
```javascript
function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const loadAnalytics = async () => {
    setLoading(true);
    const viewParam = currentView?.id ? `&view_id=${currentView.id}` : '';
    const response = await axios.get(`${API}/analytics/monthly?month_offset=${monthOffset}${viewParam}`);
    setAnalytics(response.data);
    setLoading(false);
  };
  
  // ... 4000+ more lines
}
```

### After
```javascript
import { useAnalytics } from '@/features/analytics';
import { useTabTargets } from '@/features/dashboard';
import { MainDashboard } from '@/features/dashboard';

function Dashboard() {
  const { viewConfig, currentView } = useAuth();
  
  // Use custom hooks
  const { analytics, loading, error, refresh } = useAnalytics({
    viewMode,
    monthOffset,
    dateRange,
    currentView,
    useCustomDate
  });
  
  const tabTargets = useTabTargets(currentView);
  
  // Calculate period months
  const actualPeriodMonths = useMemo(() => {
    if (useCustomDate && dateRange?.from && dateRange?.to) {
      return calculatePeriodMonths(dateRange.from, dateRange.to);
    }
    return viewMode === 'yearly' ? 6 : 1;
  }, [useCustomDate, dateRange, viewMode]);
  
  // Clean component code
  return (
    <Tabs>
      <TabsContent value="dashboard">
        <MainDashboard 
          analytics={analytics} 
          currentView={currentView}
          tabTargets={tabTargets}
          actualPeriodMonths={actualPeriodMonths}
        />
      </TabsContent>
      {/* Other tabs */}
    </Tabs>
  );
}
```

## 🔧 Step-by-Step Migration

### Step 1: Update Imports in App.js
Replace all inline component definitions with imports:

```javascript
// Remove these:
function useSortableData(...) { ... }
function MetricCard(...) { ... }
function MainDashboard(...) { ... }

// Add these:
import { useSortableData } from '@/shared/hooks';
import { MetricCard } from '@/shared/components';
import { MainDashboard } from '@/features/dashboard';
```

### Step 2: Replace API Calls with Services
```javascript
// Before
const response = await axios.get(`${API}/analytics/dashboard${viewParam}`);

// After
import { analyticsService } from '@/services/api';
const data = await analyticsService.getDashboard(viewId);
```

### Step 3: Use Custom Hooks
```javascript
// Before
const [dashboardData, setDashboardData] = useState(null);
const [loading, setLoading] = useState(true);
useEffect(() => {
  // Complex fetching logic
}, [dependencies]);

// After
import { useDashboardData } from '@/features/dashboard';
const { dashboardData, loading, error, refresh } = useDashboardData(currentView);
```

### Step 4: Use Utility Functions
```javascript
// Before
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

// After
import { formatDate } from '@/shared/utils';
const formatted = formatDate(dateStr);
```

## ✅ Checklist for Complete Migration

- [ ] Update all imports in App.js
- [ ] Replace inline API calls with service layer
- [ ] Replace state management with custom hooks
- [ ] Use utility functions instead of inline helpers
- [ ] Remove duplicate component definitions
- [ ] Test all functionality
- [ ] Verify no linter errors
- [ ] Update any remaining inline functions

## 🎯 Benefits After Migration

1. **Smaller Files**: App.js reduced from 5928 to ~500 lines
2. **Better Organization**: Clear feature boundaries
3. **Easier Testing**: Isolated components and hooks
4. **Team Collaboration**: Multiple developers can work simultaneously
5. **Maintainability**: Changes isolated to specific features
6. **Scalability**: Easy to add new features

## 📚 Reference

- See `src/README.md` for complete structure
- See `docs/REFACTORING_COMPLETE.md` for what was accomplished
- See `docs/refactoring-structure.md` for detailed breakdown




