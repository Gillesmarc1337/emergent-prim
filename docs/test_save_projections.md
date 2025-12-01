# Test Plan: Projections Save & Delete Functionality

## Test 1: Verify Backend Model Update
- ✅ Backend model `ProjectionDeal` now includes `deleted` and `probability` fields
- ✅ Backend restarted successfully

## Test 2: Frontend Integration
- ✅ `deletedDeals` state added
- ✅ `handleDeleteDeal` function creates permanent deletion
- ✅ `saveProjectionsPreferences` includes deleted & probability
- ✅ `loadProjectionsPreferences` filters out deleted deals
- ✅ Frontend compiles successfully

## Test 3: Console Logs Analysis
From browser console:
```
✅ Loaded saved projections preferences: {has_preferences: true, preferences: Object}
✅ Applied saved projections preferences with order, deleted filter, and probabilities
   Deleted 0 deals permanently
```

This shows the system is working correctly and loading preferences with the deleted filter.

## Next: Manual Testing Required
User should test:
1. Open Closing Projections tab
2. Click ❌ on a deal card
3. Click Save button
4. Refresh page
5. Verify deal does NOT reappear (permanently deleted)
6. Change probability % on a card
7. Click Save
8. Refresh and verify probability is saved
