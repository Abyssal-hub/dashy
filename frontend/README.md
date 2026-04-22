# Dashy Frontend — React + TypeScript Rewrite

This is a complete frontend rewrite of the Dashy personal monitoring dashboard, built with **React 18**, **TypeScript**, and **Vite**.

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

The dev server starts at `http://localhost:5173` and proxies API requests to `http://localhost:8000`.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| Routing | react-router-dom |
| Layout | react-grid-layout (drag/resize) |
| State (Client) | Zustand |
| State (Server) | TanStack Query |
| Styling | Tailwind CSS + shadcn/ui |
| Charts | Recharts |
| Icons | Lucide React |

## Scripts

- `npm run dev` — Start development server
- `npm run build` — Production build
- `npm run preview` — Preview production build
- `npm run typecheck` — TypeScript type check (no emit)

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/
│   │   ├── ui/          # shadcn/ui base components (Button, Card, Input, etc.)
│   │   ├── layout/      # Sidebar, Header, DashboardGrid
│   │   ├── modules/     # LogViewer, module renderers
│   │   └── auth/        # LoginForm
│   ├── hooks/           # Custom React hooks (useAuth, useModules, useLogs, etc.)
│   ├── stores/          # Zustand stores (auth, dashboard, UI)
│   ├── lib/             # API client, constants, utilities
│   ├── types/           # Shared TypeScript types
│   ├── pages/           # Page-level components (LoginPage, DashboardPage)
│   ├── App.tsx          # Router setup
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles + Tailwind directives
├── index.html           # HTML entry point
├── vite.config.ts       # Vite configuration
├── tailwind.config.js   # Tailwind + custom theme tokens
├── tsconfig.json        # TypeScript config
└── package.json         # Dependencies
```

## Key Features

### Drag/Resize Dashboard
- Powered by `react-grid-layout`
- Modules can be dragged and resized in edit mode
- Layout changes are saved per-module via `POST /api/modules/{id}/layout`

### Real-Time Log Streaming
- **Stream mode**: Live SSE connection to `GET /api/logs/stream`
- **Static mode**: Polling via TanStack Query
- Severity filters, source filters, full-text search
- Export to JSON or CSV

### Authentication
- JWT-based auth with automatic token refresh
- Login page with form validation
- Protected routes via `PrivateRoute` guard

### Dark Theme
- Custom color tokens matching the original `dashboard.html` aesthetic
- Glass-morphism cards with gradient accents
- Custom scrollbars and hover effects

## Backend API Additions

Three new endpoints were added to the FastAPI backend:

1. **`GET /api/modules`** — List all modules with layout data  
   *(Already existed; enhanced response)*

2. **`POST /api/modules/{id}/layout`** — Update a single module's position/size  
   ```json
   {
     "position_x": 0,
     "position_y": 0,
     "width": 2,
     "height": 2
   }
   ```

3. **`GET /api/logs/stream`** — Server-Sent Events for real-time logs  
   Query params: `severity`, `source`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |

## Notes

- The old Next.js scaffolding in `frontend-old/` was replaced entirely by this Vite project.
- No database migrations were needed; existing `modules` table already has `position_x`, `position_y`, `width`, `height` columns.
- All TypeScript compiles cleanly with `noUnusedLocals` and `noUnusedParameters` enabled.
