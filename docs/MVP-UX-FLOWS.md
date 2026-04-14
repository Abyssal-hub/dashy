# MVP UX Flow Scenarios

Complete user journey documentation for manual and automated testing.

---

## Flow 1: First-Time User Onboarding

**Goal:** New user registers, logs in, and creates their first dashboard

### Steps:

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 1.1 | Navigate to `http://localhost:8000` | Login page loads with email/password fields | Visual check |
| 1.2 | Click "Register" link | Alert: "Registration coming soon. Use API to create account for now." | Dialog appears |
| 1.3 | Create user via API: `curl -X POST http://localhost:8000/auth/register -H "Content-Type: application/json" -d '{"email": "test@example.com", "password": "testpass123"}'` | Returns 201 with user_id | HTTP 201 |
| 1.4 | Enter email: `test@example.com` | Email accepted in field | Field populated |
| 1.5 | Enter password: `testpass123` | Password masked (dots) | Field populated |
| 1.6 | Click "Sign In" | Redirects to `/dashboard` | URL changes |
| 1.7 | Observe dashboard | Empty state shown: "No modules yet" with "Add Your First Module" button | Visual check |

**Database State After:**
- User exists in `users` table
- No modules in `modules` table
- No dashboard layout in `dashboard_layouts` table

---

## Flow 2: Add First Portfolio Module

**Goal:** User adds a portfolio module to their dashboard

### Steps:

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 2.1 | Click "Add Your First Module" button | "Add Module" modal opens | Modal visible |
| 2.2 | Click "Module Type" dropdown | Dropdown shows: Portfolio, Calendar, Log | 3 options visible |
| 2.3 | Select "Portfolio" | Portfolio selected | Dropdown shows "Portfolio" |
| 2.4 | Enter Name: "My Investments" | Text appears in field | Field populated |
| 2.5 | Click "Add" button | Modal closes, module appears in grid | Module card visible |
| 2.6 | Observe module card | Shows: Portfolio icon, "My Investments" title, "portfolio" subtitle, "$0.00 Total Value" | Visual check |

**API Calls Made:**
```
POST /api/modules
Request: {"module_type": "portfolio", "name": "My Investments", "config": {}, "size": "medium"}
Response: 201 Created with module object
```

**Database State After:**
- Module exists in `modules` table
- `module_type` = "portfolio"
- `user_id` matches logged-in user

---

## Flow 3: Session Persistence

**Goal:** User returns and finds their dashboard intact

### Steps:

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 3.1 | Complete Flow 2 (have portfolio module) | Module visible on dashboard | Visual check |
| 3.2 | Copy URL: `http://localhost:8000/dashboard` | URL in clipboard | - |
| 3.3 | Open new browser tab | Blank tab | - |
| 3.4 | Paste URL and navigate | Dashboard loads | Page loads |
| 3.5 | Observe | "My Investments" module appears without re-login | Token still valid |
| 3.6 | Refresh page (F5) | Module still visible | Persisted |
| 3.7 | Open browser dev tools → Application → Local Storage | `token` and `refresh_token` present | Tokens exist |

**Token Behavior:**
- Access token: 15 minute expiry
- Refresh token: 7 day expiry
- If access token expires, frontend should auto-refresh (if implemented)

---

## Flow 4: Delete Module

**Goal:** User removes a module from their dashboard

### Steps:

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 4.1 | Have at least one module on dashboard | Module visible | Visual check |
| 4.2 | Click trash icon on module card | Browser confirmation dialog: "Delete this module?" | Dialog appears |
| 4.3 | Click "Cancel" | Dialog closes, module remains | No change |
| 4.4 | Click trash icon again | Confirmation dialog appears | Dialog appears |
| 4.5 | Click "OK" | Module disappears, empty state shows | Empty state visible |

**API Calls Made:**
```
DELETE /api/modules/{module_id}
Response: 204 No Content
```

**Database State After:**
- Module soft-deleted or removed from `modules` table
- Associated assets/transactions cascade deleted

---

## Flow 5: Add Multiple Module Types

**Goal:** User creates a diverse dashboard

### Steps:

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 5.1 | Add Portfolio module named "Stocks" | Portfolio card appears | Visual check |
| 5.2 | Add Calendar module named "Schedule" | Calendar card appears below/next to Portfolio | Grid layout |
| 5.3 | Add Log module named "Notes" | Log card appears | 3 modules visible |
| 5.4 | Observe grid layout | 3 modules in responsive grid | Visual check |
| 5.5 | Resize browser window (if testing responsive) | Grid adjusts columns | Responsive behavior |

**Expected Grid Behavior (MVP Static):**
- 12-column grid
- Medium modules: 6 columns wide (2 per row on desktop)
- Stacked vertically on mobile

---

## Flow 6: Logout and Re-login

**Goal:** User can logout and log back in

### Steps:

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 6.1 | Be logged in on dashboard | Dashboard visible | Visual check |
| 6.2 | Click logout icon (top right) | Redirected to login page `/` | URL changes |
| 6.3 | Check Local Storage | `token` and `refresh_token` removed | Empty |
| 6.4 | Try navigate to `/dashboard` manually | Redirected to login or 401 error | Auth check |
| 6.5 | Enter credentials and login | Redirected to dashboard with modules | Data persisted |

---

## Flow 7: Error Handling

**Goal:** System handles errors gracefully

### Scenario 7a: Invalid Login

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7a.1 | Enter wrong email | Enter: `wrong@example.com` | Field populated |
| 7a.2 | Enter any password | Enter: `wrongpass` | Field populated |
| 7a.3 | Click "Sign In" | Error message: "Invalid credentials" | Red text below form |
| 7a.4 | Observe | Still on login page, password cleared | URL unchanged |

### Scenario 7b: Backend Unavailable

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7b.1 | Stop backend: `./stop.sh` | Services stopped | Terminal check |
| 7b.2 | Try login | Error: "Network error. Is the backend running?" | Error message |
| 7b.3 | Restart: `./start.sh` | Services start | Terminal check |
| 7b.4 | Try login again | Success | Login works |

### Scenario 7c: Duplicate Module Name (if enforced)

| Step | Action | Expected Result | Verification |
|------|--------|-----------------|--------------|
| 7c.1 | Have module named "Test" | Module exists | Visual check |
| 7c.2 | Try add another "Test" | Depends on backend validation | 409 error or allowed |

---

## API Contract Verification

For each flow, verify these response schemas:

### GET /api/modules
```json
[
  {
    "id": "uuid-string",
    "module_type": "portfolio",
    "name": "My Investments",
    "config": {},
    "size": "medium",
    "is_active": true,
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

### POST /api/modules (201 Created)
```json
{
  "id": "uuid-string",
  "module_type": "portfolio",
  "name": "My Investments",
  "config": {},
  "size": "medium",
  "position_x": 0,
  "position_y": 0,
  "refresh_interval": 300,
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z"
}
```

### Error Response (401, 404, 422)
```json
{
  "detail": "Error message here"
}
```

---

## Test Data Setup

**Quick setup script for manual testing:**

```bash
# Create test user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "demo123"}'

# Login to get token (save this)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "demo123"}'

# Create sample modules (use token from above)
curl -X POST http://localhost:8000/api/modules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"module_type": "portfolio", "name": "My Stocks", "config": {}, "size": "medium"}'

curl -X POST http://localhost:8000/api/modules \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"module_type": "calendar", "name": "My Schedule", "config": {}, "size": "medium"}'
```

---

## Known MVP Limitations

| Feature | Status | Note |
|---------|--------|------|
| Registration UI | ❌ Not implemented | Use API curl command |
| Module drag-drop | ❌ Not implemented | Grid is static |
| Real portfolio data | ❌ Placeholder only | Shows "$0.00" static |
| Calendar events | ❌ Placeholder only | Shows "No events today" |
| Log entries | ❌ Placeholder only | Shows "Never" |
| Auto token refresh | ⚠️ May not work | Reload page if 401 |
| Responsive mobile | ⚠️ Basic only | Desktop-optimized |

---

## Success Criteria for MVP

✅ All 7 flows execute without JavaScript errors
✅ All API calls return expected status codes
✅ Data persists across sessions
✅ Authentication protects routes
✅ Errors show user-friendly messages

**If all above pass:** MVP frontend-backend integration is working.
