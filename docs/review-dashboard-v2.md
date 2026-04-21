## Review: dashboard.html
**Status:** NEEDS_WORK
**Mode:** Adversarial

### [AUTO-FIXED] — Issues found (would need code changes)
1. **[INLINE-ONCLICK]** Multiple inline `onclick` handlers violate frontend conventions:
   - Line ~370: `<button onclick="logout()">` in sidebar user profile
   - Line ~466: `<button onclick="openAddModuleModal()">` in header Add Module button
   - Line ~478: `<button onclick="openAddModuleModal()">` in empty state
   - Line ~560: `<button onclick="closeAddModuleModal()">` in modal Cancel
   - Line ~561: `<button onclick="submitAddModule()">` in modal Add button
   → Frontend CLAUDE.md explicitly states: "Event handling: `addEventListener()` only — no inline `onclick`"

2. **[XSS-MODULE-NAME]** `module.name` is rendered into innerHTML without escaping in `renderModules()`:
   ```javascript
   card.innerHTML = `...<h3 class="font-semibold text-white">${module.name}</h3>...`;
   ```
   If a malicious user creates a module named `<img src=x onerror=alert(1)>`, it executes.
   → `escapeHtml()` exists in the file but is NOT used for module metadata.

3. **[XSS-MODULE-TYPE]** `module.module_type` rendered without escaping:
   ```javascript
   `<span>${module.module_type}</span>`
   ```
   Same XSS vector as above.

4. **[INNERHTML-WITH-USER-DATA]** `innerHTML` used as the primary DOM construction method for module cards, violating CLAUDE.md: "DOM manipulation: Use `createElement()` + `appendChild()` — avoid innerHTML with user data"
   - The whole `renderModules()` function builds cards via `innerHTML`
   - Module renderers (`renderPortfolioModule`, `renderCalendarModule`, `renderLogModule`) all use `innerHTML`
   - While `escapeHtml()` is used for some fields (log messages, event titles), it is NOT used for:
     - `module.name`
     - `module.module_type`
     - Portfolio asset counts
     - Calendar event categories
     - Log sources

5. **[REDUNDANT-GRID-STYLES]** `getGridClass()` returns Tailwind `col-span-N` classes AND `getWidth()` returns numeric values applied via `style.cssText = 'grid-column: span N'` — both define the same grid span, creating conflicting/inconsistent layout behavior depending on CSS specificity.

6. **[NO-ARIA-ROLES]** Zero accessibility markup despite CLAUDE.md requiring "Accessibility: `aria-label`, `role`, keyboard navigation":
   - No `role="navigation"` on sidebar `<nav>`
   - No `aria-label` on any buttons (delete, add module, close modal)
   - No `role="dialog"`, `aria-modal="true"` on modal
   - No `aria-describedby` on form inputs
   - No `aria-expanded` on modal trigger

7. **[NO-KEYBOARD-MODAL-TRAP]** Modal can be opened but focus is not trapped inside. Pressing Tab cycles to elements behind the modal. Escape key only closes modal because of a global keydown listener — but if a form field has focus, this may interfere with other Escape behaviors.

8. **[NO-DEBOUNCE]** Input handlers and API calls are not debounced, violating CLAUDE.md Performance rule: "Debounce input handlers (300ms)". The module deletion via `confirm()` could be clicked rapidly.

9. **[NO-SESSIONSTORAGE-CACHE]** API responses are not cached in sessionStorage, violating CLAUDE.md Performance rule. Every page load re-fetches all module data.

10. **[NO-LAZY-LOAD]** All module renderers fire simultaneously on load. For 20 modules, that's 20 concurrent API requests with no batching or lazy loading.

11. **[NO-ERROR-BOUNDARY]** If a single module renderer throws (e.g., `renderPortfolioModule` crashes on malformed API data), there is no try/catch in `renderModules()` — the exception propagates and may break the entire dashboard grid.

12. **[RACE-CONDITION-401]** In `api()`, when response.status === 401, `logout()` is called (which does `window.location.href = '/'`) but the function then returns `undefined`. The caller (`loadModules`) checks `if (!response)` and calls `showEmptyState()`. This creates a race: the page may try to render an empty state while simultaneously navigating away.

13. **[MODAL-NO-CLICK-OUTSIDE]** Modal cannot be closed by clicking the backdrop overlay. Users must click Cancel or Escape. This is poor UX.

14. **[NO-LOADING-STATE-DELETE]** `deleteModule()` has no loading/disabled state. A double-click or rapid clicks could fire multiple DELETE requests.

15. **[API-RESPONSE-ASSUMPTION]** `api()` assumes all responses are JSON but never checks `Content-Type`. A 500 error from a proxy/load balancer returning HTML would cause `response.json()` to throw, resulting in an unhandled rejection.

### [ASK] — Requires human decision
1. **[TAILWIND-CDN]** The dashboard uses `cdn.tailwindcss.com` in production. This is a development CDN, not meant for production (no purging, slower, external dependency). Should the project:
   - a) Keep Tailwind CDN for simplicity (accept performance cost)
   - b) Switch to a build step with PostCSS/Tailwind CLI (adds complexity)
   - c) Inline critical styles and load the rest lazily

2. **[FONT-AWESOME-CDN]** External Font Awesome and Google Fonts CDNs are hard dependencies. If these fail (network, CDN block, privacy mode), the UI breaks (no icons, fallback font). Should icons be inlined as SVG or self-hosted?

3. **[ALERT-FOR-ERRORS]** `showError()` uses `alert()` which blocks the UI thread and is poor UX. Should this be replaced with an in-app toast/notification system?

4. **[GRID-COLUMN-CONFLICT]** The `style.cssText = \`grid-column: span ${getWidth(module)};\`` overrides the Tailwind `col-span-*` class. Which layout system should be canonical — inline styles or Tailwind classes?

### [INFO] — Observations
1. **[MODULE-RENDERERS-REGISTRY]** The `MODULE_RENDERERS` registry pattern (DEF-020, DEF-021) is well-implemented and extensible. Each renderer correctly extracts `responseData.data` before accessing nested fields.

2. **[ESCAPEHTML-EXISTS]** An `escapeHtml()` helper exists and IS used correctly for event titles, log messages, and log sources. The pattern is good but coverage is incomplete.

3. **[AUTH-GUARD]** Token check on load (`if (!token) window.location.href = '/'`) is present and functional.

4. **[TIME-WIDGET]** The timezone display (NYC/LON/TYO) is a nice touch and works correctly with `Intl.DateTimeFormat` via `toLocaleTimeString`.

5. **[SYSTEM-MOCK-DATA]** System Status widget shows hardcoded mock data (42% CPU, 68% Memory, 23% Disk) — this is expected for a static widget but should be documented if not connected to a real monitoring API.

6. **[CONFIRM-FOR-DELETE]** Using `confirm()` for delete operations provides a basic safety guard, but it is a blocking browser dialog that prevents interaction with the rest of the page.

### Summary
- Critical: 2 (XSS via module.name, XSS via module.module_type)
- Major: 5 (inline onclick, innerHTML with user data, no aria/roles, redundant grid styles, no error boundaries)
- Minor: 8 (no debounce, no cache, no lazy load, modal UX, 401 race, no loading on delete, API assumption, no keyboard trap)
- Recommendation: **FIX_THEN_SHIP** — The XSS issues (Critical) and convention violations (inline onclick, innerHTML instead of createElement) must be addressed before shipping. The major accessibility gaps also need fixing.
