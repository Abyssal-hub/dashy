# UX Test Scenario Brainstorm

## Already Covered ✅
- Single user full journey (signup → add modules → populate → verify → delete)
- Multiple modules of same type (data isolation)
- Live log updates with filtering/pagination

## Missing UX Scenarios

### 1. Empty State Experience
**User story:** New user adds a portfolio module but hasn't added any assets yet.
**UX concern:** Does the module show a helpful empty state ("Add your first stock"), or just a blank box?
**Test:** Create module → fetch data → verify UI shows empty-state message, not hardcoded $0.00.

### 2. Error State Handling
**User story:** Backend API is temporarily down or returns 500.
**UX concern:** Does the dashboard show a friendly error, or does the whole page crash?
**Test:** Mock API failure → verify module shows "Unable to load data" with retry button.

### 3. Auto-Refresh Without Jarring
**User story:** User has dashboard open for 30 minutes. Data refreshes every 5s.
**UX concern:** Do numbers update smoothly, or does the whole module flash/repaint?
**Test:** Open module → note DOM state → trigger refresh → verify only values change, not container.

### 4. Module Resize = Different Data Density
**User story:** User drags portfolio from "small" to "expanded".
**UX concern:** Small shows 3 assets + total. Expanded shows 10 assets + charts. Does data adapt?
**Test:** Create module → fetch at `size=small` → verify limited fields → fetch at `size=expanded` → verify full fields.

### 5. Browser Refresh Restores State
**User story:** User hits F5 after arranging dashboard.
**UX concern:** Do module positions, sizes, and data all restore exactly?
**Test:** Create modules → note positions → refresh → verify identical layout + data.

### 6. Cross-User Data Leak
**User story:** User A and User B both have "My Portfolio" modules.
**UX concern:** Can User A ever see User B's AAPL shares?
**Test:** Create 2 users with same module names → verify each only sees their own assets.

### 7. Large Dataset Performance
**User story:** Power user has 100 assets and 50 calendar events.
**UX concern:** Does dashboard stay <100ms to render? Or does it hang?
**Test:** Insert 100 assets → fetch → verify response time <200ms, pagination works.

### 8. Token Expiry Mid-Session
**User story:** User leaves dashboard open overnight. JWT expires.
**UX concern:** Does UI gracefully redirect to login, or show raw 401 errors?
**Test:** Expire token → trigger API call → verify redirect to login, not broken page.

### 9. Config Change = Immediate Update
**User story:** User changes calendar keyword filter from "Fed" to "ECB".
**UX concern:** Does calendar update instantly, or require page refresh?
**Test:** Update module config → fetch data → verify new filter applied immediately.

### 10. Accessibility / Keyboard Navigation
**User story:** User navigates dashboard using only keyboard (Tab, Enter, Escape).
**UX concern:** Can they add modules, view data, delete modules without mouse?
**Test:** Tab through all interactive elements → verify focus states → activate with Enter.
