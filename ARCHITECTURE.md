# Architecture Document: Personal Monitoring Dashboard

**Version:** 1.1  
**Date:** 2026-04-20  
**Status:** Phase 1 MVP Complete — Phase 2 Roadmap Defined  

---

## 1. Overview

A personal, extensible monitoring dashboard for tracking portfolios, global financial events, and custom metrics. Built as a modular system with a responsive frontend, async Python backend, and time-series database.

### 1.1 Target User
Single user, local machine deployment, with potential future migration to VPS.

### 1.2 Core Principles
- **Modularity:** Every monitor is a self-contained module (portfolio, calendar, crypto, logs).
- **Graceful Degradation:** External API failures do not break the dashboard.
- **Type Safety:** Strict typing across frontend and backend.
- **Simplicity First:** No over-engineering for single-user, low-volume workloads.

### 1.3 Architecture Phases
This document covers both the **current Phase 1 MVP implementation** and the **Phase 2 target architecture**. Key differences are explicitly marked.

| Phase | Scope | Frontend | Backend | Data Layer |
|-------|-------|----------|---------|------------|
| **Phase 1 (Current)** | MVP — single user, local deployment | Vanilla HTML/JS + Tailwind CDN | FastAPI + PostgreSQL + Redis | File-based logs, TimescaleDB metrics |
| **Phase 2 (Target)** | Production-ready, multi-user capable | Next.js 14 + TypeScript + TanStack Query | Same backend, enhanced | File-based logs (superior), full TimescaleDB analytics |

**Rationale for Phase 1 simplifications:**
- Vanilla HTML/JS: Faster iteration for MVP validation (FE-MVP-001, 2026-04-15)
- File-based logging: Simpler debugging, lower overhead, human-readable, no schema migration pain (DEV-012, 2026-04-19)
- Plain CSS grid: Good enough for static layouts; react-grid-layout for Phase 2 interactivity

---

## 2. Technology Stack

### 2.1 Frontend

#### Phase 1 (Current) — Vanilla HTML/JS
| Component | Technology | Purpose |
|-----------|------------|---------|
| Markup | HTML5 | Static pages: `index.html` (login), `dashboard.html` (dashboard) |
| Language | JavaScript (ES2022) | Vanilla JS with `fetch()` for API calls |
| Styling | Tailwind CSS (CDN) | Utility-first responsive styling |
| Grid | CSS Grid (`grid-template-columns: repeat(12, 1fr)`) | Static 12-column layout |
| State | `localStorage` + in-memory vars | JWT tokens, module cache |
| Icons | Font Awesome 6 (CDN) | UI icons |

#### Phase 2 (Target) — Next.js 14
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | Next.js 14 (App Router) | React framework with SSR/SSG |
| Language | TypeScript 5.x | Type safety |
| Styling | Tailwind CSS | Utility-first responsive styling |
| Grid | react-grid-layout | Draggable, resizable masonry grid |
| Server State | TanStack Query (React Query) | Caching, background refetching, deduplication |
| Client State | Zustand | Lightweight UI state management |
| Charts | Recharts / Tremor | Data visualization |

### 2.2 Backend
| Component | Technology | Purpose |
|-----------|------------|---------|
| Framework | FastAPI | Async API framework |
| Language | Python 3.11+ | Async I/O, data processing |
| Database Driver | asyncpg | High-performance async PostgreSQL driver |
| ORM/Query Builder | SQLAlchemy 2.0 (async) or raw SQL via asyncpg | Schema definitions + complex queries |
| Queue/Cache | Redis 7 | Message broker + query cache |
| Migrations | Alembic | Database schema versioning |

### 2.3 Data Layer
| Component | Technology | Purpose |
|-----------|------------|---------|
| Primary DB | PostgreSQL 15+ | Relational data, module configs, auth |
| Time-Series | TimescaleDB 2.11+ | Metric hypertables, compression, aggregation |
| Backup | `pg_dump` + cron | Daily backups to external drive/NAS |

### 2.4 External Services
| Service | Provider | Purpose |
|---------|----------|---------|
| Equity Prices | Yahoo Finance (`yfinance`) | Free, unofficial API |
| Crypto Prices | CoinGecko API | Free tier, no key required for basic |
| Economic Calendar | Forex Factory (scraped) | HTML parsing by custom scraper |
| Email Alerts | Resend | Transactional email API |

### 2.5 Infrastructure
| Component | Technology |
|-----------|------------|
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx (future VPS only) |
| Process Management | Uvicorn (FastAPI), cron (backups) |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BROWSER                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Masonry Grid   │  │  Full Module    │  │  Log Module     │             │
│  │  (Dashboard)    │  │  View           │  │                 │             │
│  └────────┬────────┘  └────────┬────────┘  └─────────────────┘             │
└───────────┼────────────────────┼────────────────────────────────────────────┘
            │                    │
            │ HTTP / REST        │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Auth    │ │ Dashboard│ │ Modules  │ │  Ingest  │ │  Alerts  │          │
│  │  Router  │ │  Router  │ │  Router  │ │  Router  │ │  Router  │          │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘          │
│       │            │            │            │            │                 │
│       └────────────┴────────────┴────────────┘            │                 │
│                           │                               │                 │
│                           ▼                               ▼                 │
│                     ┌──────────────┐              ┌──────────────┐          │
│                     │  PostgreSQL  │              │    Redis     │          │
│                     │  +Timescale  │              │  (Queue/Cache)│          │
│                     └──────────────┘              └──────────────┘          │
│                                                                   ▲         │
│                                                                   │         │
│                            ┌──────────────┐                       │         │
│                            │Redis Consumer│───────────────────────┘         │
│                            │(Background)  │                                 │
│                            └──────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
            ▲
            │ Redis Queue (LPUSH / BLPOP)
            │
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SCRAPER WORKER                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ Yahoo Finance   │  │   CoinGecko     │  │ Forex Factory   │             │
│  │   Scraper       │  │    Scraper      │  │    Scraper      │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Frontend Architecture

### 4.1 Application Structure

#### Phase 1 — Static Pages
- `index.html` → Login page (JWT authentication)
- `dashboard.html` → Main dashboard with grid layout
- `css/` → Custom styles (if any beyond Tailwind)
- `js/` → Module renderers and dashboard logic

**State Management:**
- **Server State:** Direct `fetch()` calls with `localStorage` JWT token
- **Client State:** In-memory variables, DOM state

#### Phase 2 — Next.js 14 App Router
- `/` → Masonry grid dashboard
- `/module/[id]` → Full module detail view
- `/login` → Authentication page

**State Management:**
- **TanStack Query:** All server state (module data, layouts, user profile)
- **Zustand:** UI state (sidebar open/close, active modal, selected time ranges)

### 4.2 Dashboard Layout

#### Phase 1 — Static CSS Grid
- **Grid:** CSS Grid with `grid-template-columns: repeat(12, 1fr)`
- **Responsive breakpoints:**
  - Desktop (>1280px): 12 columns
  - Tablet (768-1280px): 8 columns
  - Mobile (<768px): 4 columns
- **Row height:** Fixed at implicit content height (no explicit row height)
- **Modules:** Static positioning, no drag/resize
- **Layout persistence:** `PUT /dashboard/layout` stores grid config, but frontend currently hardcodes columns=12, rowHeight=100

#### Phase 2 — Masonry Grid (react-grid-layout)
- **Grid:** 4 columns desktop, 3 tablet, 2 small tablet, 1 mobile
- **Base row height:** 150px
- **Cards:** Draggable and resizable
- **Layout persistence:** `PUT /dashboard/layout` saves exact positions
- **Optimistic UI:** Drag/resize updates immediately, debounced save to backend

**Note:** Phase 1 layout is module-centric (Section 6.1 Decision B07). Grid config is hardcoded in frontend. Phase 2 introduces separate layout tables for multi-layout support.

### 4.3 Module Card Interactions
| Action | Behavior |
|--------|----------|
| Left-click | Navigate to `/module/[id]` (full view) |
| Right-click | Context menu → Configure / Remove from dashboard / Refresh |
| Drag | Reposition card (optimistic UI, debounced save) |
| Resize | Scale card dimensions; refetches data with new `size` parameter |

### 4.4 Data Freshness Indicators
- Timestamp color on every card:
  - **Green/White:** < 15 minutes old
  - **Yellow:** 15 minutes — 1 hour old
  - **Red:** > 1 hour old
- Tooltip shows exact "Last updated X min ago"

### 4.5 Theme
- **Dark mode default**
- System preference detection with manual override toggle

### 4.6 Module Render Registry Pattern

**Status:** Phase 1 — Implemented in `dashboard.html`. Phase 2 — Will migrate to React components.

**Principle:** Module content is rendered via type-specific renderer functions registered in a central lookup table. Renderers are responsible for fetching data, rendering DOM, and managing their own lifecycle (refresh intervals, error states, cleanup).

**Why this pattern:**
- Browsers do **not** execute `<script>` tags inserted via `innerHTML` (CSP/XSS prevention)
- Inline scripts in dynamically generated HTML silently fail — this is the root cause of the log module "Loading..." bug
- Renderers use standard DOM APIs (`document.createElement`, `textContent`, `fetch`, etc.)

**Phase 1 Implementation (Vanilla JS):**
```javascript
const MODULE_RENDERERS = {
    portfolio: renderPortfolioModule,
    calendar: renderCalendarModule,
    log: renderLogModule,
    crypto: renderCryptoModule,
};

function renderModules() {
    modules.forEach(module => {
        const container = createModuleContainer(module);
        const renderer = MODULE_RENDERERS[module.module_type];
        if (renderer) {
            renderer(module, container);
        } else {
            container.innerHTML = `<p>Unknown module type: ${module.module_type}</p>`;
        }
    });
}
```

**Renderer Contract:**
| Responsibility | Requirement |
|----------------|-------------|
| Input | `module` object (id, name, module_type, config, size) + DOM `container` element |
| Data fetching | Call `GET /api/modules/{module.id}/data?size=${module.size}` |
| Rendering | Populate `container` with module-specific content using DOM APIs only |
| Error handling | Show error state inside the card, never `alert()` or throw uncaught |
| Refresh | Manage own `setInterval` for live data; cancel on module removal |
| Cleanup | Remove intervals/event listeners when module is deleted or dashboard unmounts |

**Phase 2 Migration (React):**
Each renderer becomes a React component:
```typescript
// Phase 2: React component registry
const ModuleComponents: Record<string, React.FC<ModuleProps>> = {
    portfolio: PortfolioModule,
    calendar: CalendarModule,
    log: LogModule,
};
```

**Backend Contract:**
- `GET /api/modules/{id}/data` returns `{ type: "portfolio", data: {...}, meta: {...} }`
- `type` field must match frontend renderer registry key
- `size` parameter: `compact` | `standard` | `expanded` (derived from grid dimensions)

---

## 5. Backend Architecture

### 5.1 API Design
**Base URL:** `http://localhost:8000`  
**Authentication:** Bearer JWT in `Authorization` header (access token). Refresh token in `httpOnly` cookie.

#### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate, set refresh cookie |
| POST | `/auth/refresh` | Rotate access token |
| POST | `/auth/logout` | Revoke refresh token, clear cookie |

#### Dashboard Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/layout` | Get user's masonry layout |
| PUT | `/dashboard/layout` | Save layout positions |
| POST | `/dashboard/modules/{id}` | Add module to dashboard |
| DELETE | `/dashboard/modules/{id}` | Remove module from dashboard |

#### Module Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/modules` | List all configured modules |
| POST | `/modules` | Create new module |
| GET | `/modules/{id}` | Get module configuration |
| PUT | `/modules/{id}` | Update module configuration |
| DELETE | `/modules/{id}` | Delete module |
| GET | `/modules/{id}/data` | Fetch module data (`?size=compact\|standard\|expanded`) |

#### Data Ingestion Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ingest/metrics` | Batch metric ingestion |
| POST | `/ingest/events` | Batch event ingestion (calendar) |

#### Alert Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/alerts` | List active alerts |
| POST | `/alerts/{id}/acknowledge` | Acknowledge alert |
| GET | `/alerts/history` | Alert history |

#### Log Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/logs` | Structured system logs |
| GET | `/health` | System health status (DB, Redis, scraper) |

### 5.2 Module Handler Registry

**Status:** Phase 1 — Backend handlers implemented. Frontend uses static rendering (Section 4.6). Phase 2 — Full integration with `/modules/{id}/data`.

Each module type maps to a dedicated handler class:

```python
HANDLERS = {
    "portfolio": PortfolioHandler,
    "calendar": CalendarHandler,
    "crypto": CryptoHandler,
    "log": LogHandler,
}
```

#### Phase 1 — Current Implementation
- Handlers are registered and functional for portfolio and calendar modules
- `PortfolioHandler.get_data()` supports compact/standard/expanded sizes
- `CalendarHandler.get_data()` supports date range filtering
- `LogHandler.get_data()` is implemented but frontend does not call `/modules/{id}/data`
- **Frontend bypass:** Log module content is rendered directly via `MODULE_RENDERERS.log()` calling `GET /api/logs` (not `/modules/{id}/data`)

#### Phase 2 — Target Implementation
The `GET /modules/{id}/data` endpoint:
1. Looks up module type
2. Resolves current grid dimensions to `size` bucket (compact/standard/expanded)
3. Delegates to handler
4. Returns generic envelope with module-specific payload

```json
{
  "type": "portfolio",
  "data": { "positions": [...], "total_value": 12345.67 },
  "meta": { "last_updated": "2026-04-20T14:30:00Z", "size": "standard" }
}
```

**Frontend-Backend Contract:**
- `type` field must match `MODULE_RENDERERS` registry key (Section 4.6)
- `size` is derived from module config or grid dimensions
- Handler decides what data to include based on `size` (less detail for compact)

### 5.3 Authentication & Security
- **Password Hashing:** Argon2id
- **Access Token:** 15-minute expiry, HS256
- **Refresh Token:** 7-day expiry, httpOnly, Secure, SameSite=Strict cookie
- **Rate Limiting:** SlowAPI applied to `/auth/*` (5 requests/minute per IP)
- **CORS:** Restricted to frontend origin only
- **Input Validation:** Pydantic models on all endpoints
- **SQL Injection Prevention:** Parameterized queries exclusively

### 5.4 Background Tasks
- **Redis Consumer:** Async task running inside FastAPI lifespan. Drains `metrics_queue` and writes to TimescaleDB.
- **Alert Evaluator:** Event-driven (per ingest batch) + scheduled sweep (every 5 minutes via APScheduler).
- **Health Checker:** Periodic DB/Redis connectivity checks logged to Log Module.

### 5.5 HTTP Status Code Standards

| Status | Meaning | When to Use |
|--------|---------|-------------|
| **200** | OK | Successful GET, PUT, PATCH operations |
| **201** | Created | Successful POST that creates a resource |
| **204** | No Content | Successful DELETE or operations with no response body |
| **400** | Bad Request | Malformed request (JSON parse error, missing required fields) |
| **401** | Unauthorized | Missing or invalid authentication token |
| **403** | Forbidden | Authenticated but not authorized (not used in MVP) |
| **404** | Not Found | Resource does not exist |
| **422** | Unprocessable Entity | Validation error (semantically correct but invalid values) |

**MVP Specific Patterns:**
- Auth failures return **403** (implementation choice via `get_current_user`)
- Invalid module types return **422** (validation error)
- Missing auth token returns **403** (not 401, per current implementation)

---

## 6. Data Architecture

### 6.1 Database Schema Summary

#### Authentication Tables
- `users` — Single user account (email, password_hash)
- `refresh_tokens` — Rotatable refresh tokens with expiry and revocation

#### Module System Tables
- `module_types` — Registry of supported module types
- `modules` — User-configured module instances with inline layout positions:
  - `position_x`, `position_y` — Grid coordinates
  - `width`, `height` — Grid dimensions (optional)
  - `size` — Preset size category (small/medium/large)
  - `config` — Module-specific settings (JSONB)
  - `refresh_interval` — Data refresh rate in seconds

**Note:** Per **Decision B07**, layout is module-centric for MVP. Grid configuration (`columns=12`, `rowHeight=100`) is hardcoded in frontend. Future multi-layout support may introduce separate layout tables.

#### Legacy/Reserved (MVP)
- `dashboard_layouts` — Reserved for future multi-layout support. Not used in MVP.

#### Calendar Module Tables
- `calendar_events` — Personal CRUD events + scraped financial events
  - `source`: `manual` | `scraped` | `imported`
  - `external_id`: Deduplication key for scraped events
  - `scraped_keywords`: JSONB array of matched keywords

#### Portfolio Module Tables
- `asset_types` — Reference table (cash, equity, bond, real_estate, insurance)
- `portfolio_positions` — Current holdings per module
  - `quantity`, `avg_cost_basis`, `current_price`, `current_value`
  - `currency`: ISO 4217 code
  - `tags`: JSONB array
- `portfolio_snapshots` — Daily total value snapshots for historical tracking
- `fx_rates` — User-entered exchange rates (currency pair, rate, effective_date)

#### Time-Series Tables (TimescaleDB Hypertable)
- `metrics` — All time-series data
  - `time` (partition key), `metric_name`, `value`, `tags` (JSONB), `source`
  - Chunk interval: 7 days
  - Compression: Enabled after 7 days

#### Alert Tables
- `alert_rules` — Threshold conditions per user/module
- `alert_history` — Immutable record of triggered alerts + notification status

#### Scraper Configuration Tables
- `scraper_configs` — Scraper metadata, keywords, last_run tracking

### 6.2 Data Retention Policy
| Data Type | Retention |
|-----------|-----------|
| Raw metrics (per-minute) | Compress after 7 days, delete after 90 days |
| Scraped calendar events | Delete after 30 days |
| Manual calendar events | Keep indefinitely |
| Portfolio snapshots | **Keep forever** |
| Alert history | Delete after 1 year |
| System logs (Log Module) | Delete after 7 days |

### 6.3 Timezone Strategy
- **Storage:** All timestamps stored in UTC (TIMESTAMPTZ)
- **Display:** Frontend converts to local device timezone using `Intl.DateTimeFormat`
- **User input:** Calendar events submitted with timezone offset, normalized to UTC by backend

### 6.4 Backup Strategy
- **Frequency:** Daily at 03:00 via cron
- **Target:** External USB drive or NAS mount
- **Format:** `pg_dump` → GZIP
- **Rotation:** 14 backups retained
- **Encryption:** Optional GPG symmetric encryption (user-provided passphrase)

---

## 7. Module Specifications

### 7.1 Portfolio Module
**Type ID:** `portfolio`

**Features:**
- Multi-asset class support: Equity, Real Estate, Cash, Bond, Insurance
- Position-level tracking (no transaction history)
- Base currency: **SGD**
- Display currency: User-selectable (converted via manually entered FX rates)
- P&L calculation against cost basis
- Daily snapshot recording for trend charts

**Configuration (`settings` JSONB):**
```json
{
  "display_currency": "SGD",
  "show_cost_basis": true,
  "alert_thresholds": {
    "daily_change_pct": 5.0
  }
}
```

**Data Sources:**
- Yahoo Finance (`yfinance`) for equity prices
- CoinGecko for crypto prices
- Manual input for real estate, insurance, cash, and FX rates

**Refresh Modes:**
- Auto: Every 5 minutes
- Manual: User-triggered refresh

### 7.2 Calendar Module
**Type ID:** `calendar`

**Features:**
- Full CRUD for personal events
- Scraped financial event overlay (Fed, ECB, earnings, etc.)
- Keyword filtering for scraped events
- Day/week/month views (full page), upcoming list (compact)
- iCal RRULE support for recurring events

**Configuration (`settings` JSONB):**
```json
{
  "scraped_keywords": ["Fed", "ECB", "NFP", "CPI", "earnings"],
  "default_view": "month",
  "show_weekends": true
}
```

**Data Sources:**
- Manual user input
- Forex Factory scraper (hourly)

**Refresh Modes:**
- Auto: Every 1 hour
- Manual: User-triggered refresh

### 7.3 Crypto Module
**Type ID:** `crypto`

**Features:**
- Track cryptocurrency holdings and prices
- Wallet value calculation
- Price change indicators

**Data Sources:**
- CoinGecko API

**Refresh Modes:**
- Auto: Every 1 minute
- Manual: User-triggered refresh

### 7.4 Log Module
**Type ID:** `log`

**Data Source: File-Based Structured Logging (Definitive Choice)**
- **Storage:** Structured JSON log files (`app.log`, `interactions.log`) in project-local `logs/` directory
- **Rotation:** Daily rotation with automatic cleanup
- **Retention:** 7-day automatic cleanup via `cleanup_old_logs()`
- **API:** `GET /api/logs?source=system&severity=INFO&limit=50`
- **Schema per line:**
```json
{"id": "uuid", "timestamp": "2026-04-20T14:30:00+08:00", "severity": "ERROR", "message": "...", "source": "backend|frontend", "metadata": {}}
```

**Why file logging over database:**
- **Human-readable:** Can `tail -f logs/app.log` during debugging
- **Zero schema migration:** Add fields without ALTER TABLE
- **No DB overhead:** No connection pooling, no query planning, no index maintenance
- **Portability:** Copy files, grep, awk, jq — standard Unix tools work
- **Resilience:** DB down? Logs still write to disk
- **Single-user optimized:** No contention, no locking, no transaction overhead

**Features:**
- Displays structured system logs from backend
- Severity filtering (INFO, WARN, ERROR) with color coding
- Real-time streaming via polling (every 10 seconds)
- Severity buttons: ALL | INFO | WARN | ERROR

**Renderer Behavior:**
- Polls `GET /api/logs?source=system&limit=50` every 10 seconds
- Displays timestamp, severity (color-coded), message in scrollable container
- Auto-scrolls to newest entry; "Pause" button stops auto-scroll
- Uses DOM APIs only (no `innerHTML` with `<script>` tags per Section 4.6)

**Data Envelope:**
```json
{
    "logs": [
        {
            "id": "uuid",
            "timestamp": "2026-04-20T14:30:00Z",
            "severity": "ERROR",
            "message": "Database connection failed",
            "source": "backend",
            "metadata": {}
        }
    ],
    "total": 42,
    "limit": 50,
    "offset": 0
}
```

---

## 8. Data Ingestion & Scraper Architecture

### 8.1 Pipeline Flow
```
Scraper Worker ──LPUSH──▶ Redis Queue (metrics_queue) ──BLPOP──▶ FastAPI Consumer ──INSERT──▶ TimescaleDB
```

### 8.2 Batching Strategy
- Consumer accumulates messages in memory
- Flush conditions:
  - Batch reaches 100 messages
  - 5-second timeout elapses
- Bulk insert via `COPY` or parameterized batch insert for maximum throughput

### 8.3 Scraper Workers
| Scraper | Source | Frequency | Data Type |
|---------|--------|-----------|-----------|
| Yahoo Finance | `yfinance` | 5 min | Equity prices |
| CoinGecko | REST API | 1 min | Crypto prices |
| Forex Factory | HTML parsing | 1 hour | Economic events |

### 8.4 Circuit Breaker Pattern
**State Machine:** `CLOSED` → `OPEN` (after 3 failures in 5 min) → `HALF-OPEN` (after 10 min) → `CLOSED`

**Behavior:**
- **Fail-open:** Serve last known data from database/cache during outages
- **Retry:** Exponential backoff (1 min → 2 min → 4 min → capped at 10 min)
- **Frontend indicator:** Timestamp color changes based on data age

### 8.5 Graceful Shutdown
- **FastAPI (Uvicorn):** Completes active requests on `SIGTERM` (30s timeout)
- **Redis Consumer:** Finishes current batch, stops accepting new messages
- **Scraper Worker:** Completes current scrape cycle, flushes pending queue items
- **Docker Compose:** `stop_grace_period: 30s` for all services

---

## 9. Alerting Architecture

### 9.1 Alert Rule Model
- Threshold-based evaluation (`gt`, `lt`, `gte`, `lte`, `eq`)
- Attached to specific module or global metric
- Enabled/disabled toggle
- Optional email override list (defaults to user email)

### 9.2 Evaluation Strategy
| Trigger | Mechanism | Frequency |
|---------|-----------|-----------|
| **Primary** | Event-driven | On every successful ingest batch |
| **Secondary** | Scheduled sweep | Every 5 minutes (catches stale states) |

### 9.3 Notification Pipeline
1. Rule triggered → Write to `alert_history`
2. Send email via Resend API
3. Update `alert_history.email_sent = true`
4. **Deduplication:** 15-minute cooldown per rule (no repeat alerts for same condition)

### 9.4 Acknowledgment
- User can acknowledge active alerts via dashboard
- Acknowledged alerts remain in history but stop appearing in "active" list

---

## 10. Deployment Architecture

### 10.1 Local Deployment (Phase 1)
**Docker Compose Topology:**

```yaml
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file: .env

  redis:
    image: redis:7-alpine

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - postgres
      - redis

  scraper:
    build: ./backend
    command: python -m scraper_worker.main
    env_file: .env
    depends_on:
      - redis
      - postgres

volumes:
  postgres_data:
```

### 10.2 Environment Variables (`.env`)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres/dbname

# Redis
REDIS_URL=redis://redis:6379/0

# Auth
JWT_SECRET=your-256-bit-secret
ARGON2_SECRET=your-pepper-secret

# Email
RESEND_API_KEY=re_xxxxxxxx
ALERT_FROM_EMAIL=alerts@yourdomain.com

# App
FRONTEND_URL=http://localhost:3000
ENVIRONMENT=local
```

### 10.3 Future VPS Path
1. Add `nginx` reverse proxy service
2. Enable HTTPS via Let's Encrypt (Certbot)
3. Migrate backup target from NAS to S3-compatible object storage
4. Add Redis Sentinel or switch to managed Redis

---

## 11. Operational Concerns

### 11.1 Secrets Management
- `.env` file mounted into containers
- `.env` listed in `.gitignore` (never committed)
- `.env.example` provided with dummy values for documentation
- For VPS: migrate to Docker Secrets or a vault (HashiCorp Vault, AWS Secrets Manager)

### 11.2 Logging Strategy

#### 11.2.1 Backend Logging
- **Backend:** Structured JSON logs to stdout
- **Log Module:** Critical logs also written to `system_logs` table (7-day retention)
- **Docker:** stdout/stderr captured by Docker daemon (`docker logs`)

#### 11.2.2 Frontend Interaction Logging (DEV-015)
**Requirement:** Log every start and end of user interaction on the UI for debugging.

**Interaction Types Tracked:**
| Type | Description | Example |
|------|-------------|---------|
| `click` | User clicks on UI elements | Button click, link click |
| `hover` | Mouse hover over elements | Tooltip trigger, preview |
| `scroll` | Page/element scroll events | Infinite scroll, anchor |
| `input` | Form input interactions | Text entry, selection |
| `navigation` | Route/page changes | Page load, router push |
| `api_call` | API request/response | Data fetch, mutation |

**Log Schema:**
```typescript
interface InteractionLog {
  interactionId: string;      // UUID for correlation
  userId: string;             // Authenticated user
  sessionId: string;          // Browser session
  type: InteractionType;      // One of above types
  target: {
    element: string;          // DOM element identifier
    component: string;        // React component name
    route: string;            // Current page route
  };
  metadata?: Record<string, any>; // Additional context
  startedAt: ISO8601;         // Interaction start
  endedAt?: ISO8601;          // Interaction end
  duration?: number;          // Duration in milliseconds
  success: boolean;           // Success/failure status
  error?: string;             // Error message if failed
}
```

**Implementation:**
- **Frontend (Phase 1):** Vanilla JS event listeners in `dashboard.html`
- **Frontend (Phase 2):** React hook `useInteraction()` + HOC `withInteractionTracking()`
- **API:** `POST /api/logs/interaction` — 202 Accepted
- **Storage:** File-based (`interactions.log`) — same JSON line format as system logs
- **Query:** `GET /api/logs?source=frontend&limit=50` reads from `interactions.log`
- **Log Level Logic:**
  - `ERROR` - Failed interactions (success=false)
  - `WARN` - Slow interactions (>5000ms duration)
  - `INFO` - Normal interactions (<5000ms)

**Use Cases:**
1. **Bug reproduction:** See exact user steps leading to errors
2. **Performance monitoring:** Identify slow interactions
3. **Usage analytics:** Track feature usage patterns
4. **Error context:** Link failed API calls to triggering UI actions

### 11.3 Health Monitoring
- `GET /health` returns status of:
  - PostgreSQL connectivity
  - Redis connectivity
  - Scraper last-run timestamps (stale if > 2× expected interval)
- Health status displayed in Log Module

---

## 12. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Yahoo Finance API changes/breaks | Medium | High | Circuit breaker + manual price entry fallback |
| Forex Factory HTML redesign | Medium | Medium | Circuit breaker + rapid scraper update path |
| Local disk failure | Low | High | Daily `pg_dump` to external drive/NAS |
| Redis single point of failure | Low | Medium | Acceptable for local; upgrade for VPS |
| Manual FX rate outdated | Medium | Low | UI warning when rate is > 7 days old |
| Data volume exceeds expectations | Low | Low | Compression + 90-day raw metric retention |

---

## 13. Open Questions / Points for Consideration

The following decisions follow **industry golden standard** but are flagged for your override if desired:

1. **API Versioning:** Should routes be prefixed with `/api/v1/`? (Golden standard: yes, for future compatibility.)
2. **Testing Strategy:** Should the project include a defined test pyramid (unit + integration + E2E with Playwright)? (Golden standard: yes, with 70% unit / 20% integration / 10% E2E split.)
3. **CI/CD:** Should we define a GitHub Actions workflow for linting and testing? (Golden standard: yes for any code repository.)
4. **Code Quality Tools:** Black, Ruff, mypy, pre-commit hooks. (Golden standard: yes.)
5. **Frontend Error Boundaries:** React error boundaries around each module card to prevent one crash from destroying the entire dashboard. (Golden standard: yes.)

If no objection, these will be applied during implementation.

---

## 14. Decision Register

| ID | Decision | Status |
|----|----------|--------|
| F01 | Next.js + TypeScript + Tailwind | Approved |
| F02 | react-grid-layout (draggable/resizable) | Approved |
| F03 | TanStack Query + Zustand | Approved |
| F04 | Dark mode default | Approved |
| B01 | FastAPI + asyncpg + Redis | Approved |
| B02 | Single-user JWT (Argon2) | Approved |
| B03 | Resend for email | Approved |
| B04 | Rate limiting on auth endpoints | Approved |
| D01 | PostgreSQL + TimescaleDB | Approved |
| D02 | 90-day raw metric retention | Approved |
| D03 | Daily backup to external drive/NAS | Approved |
| D04 | UTC storage / local display timezone | Approved |
| P01 | Redis queue for scraper pipeline | Approved |
| P02 | Batching (100 msg or 5s timeout) | Approved |
| P03 | Circuit breaker (fail-open + stale indicator) | Approved |
| P04 | Graceful shutdown on SIGTERM | Approved |
| S01 | Yahoo Finance / CoinGecko / Forex Factory | Approved |
| U01 | Masonry grid + sidebar navigation | Approved |
| U02 | Per-module refresh policy | Approved |
| U03 | Right-click config / left-click navigate | Approved |
| M01 | Portfolio: position-level, SGD base, manual FX | Approved |
| M02 | Calendar: CRUD + scraped event overlay | Approved |
| M03 | Log Module for system observability | Approved |
| A01 | Hybrid alert evaluation (event + scheduled) | Approved |
| A02 | 15-minute alert cooldown | Approved |
| I01 | Docker Compose local deployment | Approved |
| B05 | Opaque refresh tokens (security) | **DECIDED 2024-04-16** — See DEF-011-001 |
| B06 | API response includes layout fields | **DECIDED 2024-04-16** — See DEF-011-003 |
| B07 | Module-centric layout (MVP) | **DECIDED 2026-04-16** — Positions inline in modules table, no dashboard_layouts endpoint for MVP. See QA-011. |
| F06 | Vanilla HTML/JS for Phase 1 MVP | **DECIDED 2026-04-15** — Next.js deferred to Phase 2 for faster MVP validation. See FE-MVP-001. |
| F07 | Module Render Registry pattern | **DECIDED 2026-04-20** — Type-specific renderers instead of inline `<script>` tags. See Section 4.6. |
| B10 | File-based logging (definitive) | **DECIDED 2026-04-19** — Superior for single-user: human-readable, zero schema migration, no DB overhead, Unix tool compatible. See DEV-012 and Section 7.4. |
| B11 | Separate interactions.log file | **DECIDED 2026-04-20** — Frontend interaction logs stored separately for easier debugging. See DEV-015. |

---

## 15. Phase 2 Migration Roadmap

**Trigger:** When Phase 1 MVP is validated and ready for production hardening.

### 15.1 Frontend Migration: Vanilla HTML → Next.js 14

**Effort Estimate:** 2-3 weeks

| Step | Task | Rationale |
|------|------|-----------|
| 1 | Initialize Next.js 14 project with App Router | Framework foundation |
| 2 | Migrate `MODULE_RENDERERS` to React components | Each renderer → `components/modules/{type}.tsx` |
| 3 | Implement `react-grid-layout` with layout persistence | Drag/resize interactivity (Section 4.2 Phase 2) |
| 4 | Add TanStack Query for server state | Caching, background refetch, deduplication |
| 5 | Add Zustand for client state | Sidebar, modals, filters |
| 6 | Implement React Error Boundaries per module | Prevent one crash from destroying dashboard |
| 7 | Add `useInteraction()` hook and HOC | Replace vanilla JS event tracking |
| 8 | Recharts/Tremor data visualization | Replace static text with charts |
| 9 | Port Tailwind dark theme | Preserve Phase 1 styling |

**Backward Compatibility:**
- `GET /api/modules/{id}/data` endpoint already exists (backend)
- Module response envelope (`{type, data, meta}`) remains unchanged
- JWT auth system remains unchanged

### 15.2 Backend Enhancements (No Logging Migration)

File-based logging is the definitive choice for this architecture (Section 7.4). No migration to database logging is planned.

**Phase 2 backend work:**
- Enhanced log querying (regex search, time range filtering, aggregation)
- Log shipping to external systems (optional)
- Log compression for long-term archival

### 15.3 Full Handler Integration

**Effort Estimate:** 2-3 days

| Step | Task | Rationale |
|------|------|-----------|
| 1 | Wire frontend `MODULE_RENDERERS` to `GET /modules/{id}/data` | Use intended backend contract |
| 2 | Implement `size` resolution from grid dimensions | Compact/standard/expanded per viewport |
| 3 | Update `LogHandler.get_data()` to return envelope format | Consistency with other handlers |
| 4 | Add size-aware rendering in each React component | Less detail for compact cards |

### 15.4 Decision Register Updates

New decisions needed for Phase 2:

| ID | Decision | Options |
|----|----------|---------|
| F05 | SSR vs SSG for dashboard | SSR (live data) vs SSG + client hydration |
| F08 | Chart library choice | Recharts (flexible) vs Tremor (opinionated) |
| B13 | Module data caching | TanStack Query cache duration per module type |

---

**Document Owner:** Architecture Engineer  
**Next Step:** Implementation Planning or Approval to Build
