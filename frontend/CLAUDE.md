# CLAUDE.md — Frontend Directory

## Role
You are a **UI Engineer** working on the frontend of the Personal Monitoring Dashboard.

## Technology Stack
- Vanilla JavaScript (ES6+)
- HTML5 semantic elements
- CSS3 with CSS variables
- No frameworks (React/Vue/Angular not used)

## Conventions
- Use semantic HTML: `<header>`, `<main>`, `<section>`, `<article>`
- Accessibility: `aria-label`, `role`, keyboard navigation
- Event handling: `addEventListener()` only — no inline `onclick`
- CSS naming: BEM methodology (block--element-modifier)
- DOM manipulation: Use `createElement()` + `appendChild()` — avoid innerHTML with user data

## Module System Rules
- Each module type has a dedicated renderer function
- Renderers MUST fetch data from `/api/modules/{id}/data`
- Extract `response.data` before accessing nested fields
- Show loading state while fetching
- Show empty state when no data
- Show error state on API failure (friendly message, not raw JSON)

## API Integration
```javascript
// CORRECT — extract response.data
const response = await fetch(`/api/modules/${moduleId}/data`).then(r => r.json());
const data = response.data;  // <-- Must extract .data first
renderPortfolio(data);

// WRONG — don't access response.data.property directly
const value = response.data.portfolio_value;  // NO
const value = response.data.data.portfolio_value;  // NO — double .data
```

## Testing
- E2E tests required for all frontend changes
- QA drafts tests before Developer implements
- Visual regression: Compare screenshots against baselines
- Test empty states, error states, not just happy path

## Performance
- Debounce input handlers (300ms)
- Lazy-load module renderers
- Cache API responses in sessionStorage
