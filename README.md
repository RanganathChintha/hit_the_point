# hit_the_point — PIM ↔ Storefront Reconciliation

Compares product data between the **PIM** export (source of truth) and a
**Storefront** (Magento) export — type compatibility, bundle slots/sets,
configurable children — plus a market (brand/customer-label) counter and a
category hierarchy viewer.

> **Terminology:** the system compared against PIM is called the **Storefront**.
> The word **market** refers to the PIM `customerLabel` codes (e.g. `AC`,
> `AX`, `DL`, `GA`) — a product can belong to several markets, and the
> comparison can be filtered by market.

The original CLI (`main.py`) still works. This repo also ships a **FastAPI
backend** and a **React (Vite) frontend** over the same logic.

```
loaders/      parse the raw PIM + Storefront JSON into SKU-keyed maps
comparison/   type / bundle / configurable comparison + orchestrator
hierarchy/    PIM + Storefront category → bundle → variant trees
analysis/     market (customerLabel) counter
reporting/    console printer + static HTML report
server.py     FastAPI app exposing all of the above as a REST API
frontend/     React + Vite single-page app that consumes the API
```

> **Data files** keep their original names (`data/france_products.json`,
> `data/france_categories.json`, `data/pim_prod.json`, `data/pim_cat.json`) —
> only the code/UI uses the generic "Storefront" term. The paths are set in
> `config.py` (`STOREFRONT_PRODUCTS_FILE`, `STOREFRONT_CAT_FILE`), so when you
> move to a single multi-market storefront file, just point those at it.

## Prerequisites

- Python 3.11 (a virtualenv already exists at `.venv/`)
- Node.js 18+ and npm

## 1. Backend (FastAPI)

```bash
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m uvicorn server:app --reload --port 8000
```

Loads + parses all source files **once at startup**, caches the full batch
comparison in memory. Interactive API docs at <http://127.0.0.1:8000/docs>.

### Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/health` | `{ ready: bool }` — true once data is loaded |
| GET | `/api/summary` | Dashboard totals + distinct issue categories |
| GET | `/api/reports` | Paginated table rows. Query: `search`, `category`, **`market`**, `sort`, `direction`, `page`, `page_size` |
| GET | `/api/reports/{sku}` | Full comparison detail for one SKU |
| GET | `/api/hierarchy/{sku}` | PIM + Storefront hierarchy tree lines |
| GET | `/api/markets` | All markets, or `?q=` to search code/description |
| GET | `/api/markets/{code}` | Product breakdown for one brand code |

**Market filter:** each report row carries a `markets` array (the SKU's PIM
customerLabel codes). Pass `?market=DL` to `/api/reports` to restrict the table
to one market; `market=all` (default) shows everything. It composes with
`search` and `category`.

## 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

In dev, Vite proxies `/api/*` to the backend on port 8000, so **run the backend
first**, then open <http://localhost:5173>.

Pages:
- **Dashboard** — summary cards (click to drill into the filtered table)
- **Comparison** — searchable table with a **market dropdown** + status filter,
  sortable / paginated; a Markets column shows each SKU's market codes; click a
  row for full detail + hierarchy
- **Markets** — products per brand code; "View in comparison →" jumps to the
  comparison pre-filtered by that market

### Production build

```bash
cd frontend
npm run build      # outputs to frontend/dist/
```

Set `VITE_API_BASE` at build time to serve the SPA from a different origin than
the API.

## 3. Original CLI (still available)

```bash
.venv/Scripts/python.exe main.py
```

Interactive menu: hierarchy viewer, single/batch compare, market counter, and
static HTML report export (`batch_report.html`).
