# Hit the Point — PIM ↔ Magento Reconciliation Tool

Compares product data between the **PIM** export (source of truth) and a
**Magento** e-commerce store — type compatibility, bundle slots/sets,
configurable children, and customer group assignments — plus a market
(brand/customer-label) counter, market matching, and a category hierarchy viewer.

> **Terminology:** the system compared against PIM is called **Magento**.
> The word **market** refers to the PIM `customerLabel` codes (e.g. `AC`,
> `AX`, `DL`, `GA`) — a product can belong to several markets, and the
> comparison can be filtered by market.

The original CLI (`main.py`) still works. This repo also ships a **FastAPI
backend** and a **React (Vite) frontend** over the same logic.

---

## Project Structure

```
hit_the_point/
├── config.py                          # File paths, type mappings, constants
├── server.py                          # FastAPI app (REST API, in-memory state)
├── main.py                            # Original CLI entry point
├── requirements.txt                   # Python dependencies
├── start.bat                          # One-click launcher (backend + frontend)
├── .env                               # Magento API credentials (not in git)
│
├── data/                              # Source JSON data files
│   ├── france_products.json           # Magento products
│   ├── france_categories.json         # Magento categories
│   ├── pim_prod.json                  # PIM products
│   ├── pim_cat.json                   # PIM categories
│   └── magento_customer_group.json    # Magento customer groups
│
├── loaders/                           # JSON parsing modules
│   ├── json_loader.py                 # Generic JSON file loader
│   ├── pim_loader.py                  # Parses PIM product JSON
│   ├── magento_loader.py             # Parses Magento product JSON
│   ├── magento_customer_loader.py     # Parses Magento customer group JSON
│   └── magento_product_fetcher.py     # Fetches products from Magento API
│
├── comparison/                        # Core comparison logic
│   ├── orchestrator.py                # Main comparison orchestrator
│   ├── type_compare.py               # Product type compatibility check
│   ├── bundle_compare.py             # Bundle slots comparison
│   ├── configurable_compare.py        # Configurable children comparison
│   ├── customer_group_comparison.py   # Customer group bidirectional compare
│   └── market_matching.py            # Market matching logic
│
├── hierarchy/                         # Category / bundle tree builders
│   ├── pim_hierarchy.py
│   └── magento_hierarchy.py
│
├── analysis/                          # Market (brand / customer-label) counter
│   └── market_counter.py
│
├── reporting/                         # Output generation
│   ├── html_reporter.py              # Static HTML report builder
│   └── printer.py                     # Console output formatting
│
└── frontend/                          # React SPA
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx                   # React entry point
        ├── App.jsx                    # Router and layout
        ├── api.js                     # API client
        ├── hooks.js                    # useAsync, useDebounced hooks
        ├── styles.css                 # Application styles
        ├── components/
        │   ├── Common.jsx             # Loading, ErrorBox, Empty, StatusBadges
        │   └── SkuCopyButton.jsx      # Copy SKU to clipboard
        └── pages/
            ├── Dashboard.jsx
            ├── Comparison.jsx
            ├── SkuDetail.jsx
            ├── CustomerGroupComparison.jsx
            ├── CustomerGroupComparisonDetail.jsx
            ├── Markets.jsx
            ├── MarketDetail.jsx
            ├── MarketMatching.jsx
            └── MarketMatchingDetail.jsx
```

> **Data files** keep their original names (`france_products.json`,
> `france_categories.json`, etc.) — only the code/UI uses the generic "Magento"
> term. The paths are set in `config.py` (`MAGENTO_PRODUCTS_FILE`,
> `MAGENTO_CAT_FILE`), so when you move to a single multi-market Magento file,
> just point those at it.

---

## Prerequisites

- **Python 3.11** — a virtualenv already exists at `.venv/`
- **Node.js 18+** and npm
- A `.env` file with Magento API credentials (see [Configuration](#configuration) below)

---

## Quick Start

### One-Click Launcher (Windows)

```bat
start.bat
```

Starts both the backend and frontend servers automatically.

### Manual Setup

#### 1. Backend (FastAPI)

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn server:app --reload --port 8000
```

Loads + parses all source files **once at startup**, caches the full batch
comparison in memory. Interactive API docs at <http://127.0.0.1:8000/docs>.

#### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev        # → http://localhost:5173
```

In dev, Vite proxies `/api/*` to the backend on port 8000, so **run the backend
first**, then open <http://localhost:5173>.

#### 3. Production Build

```bash
cd frontend
npm run build      # outputs to frontend/dist/
```

Set `VITE_API_BASE` at build time to serve the SPA from a different origin than
the API.

#### 4. Original CLI (still available)

```bash
.venv\Scripts\python.exe main.py
```

Interactive menu with 5 modes: hierarchy viewer, single compare, batch compare,
market counter, and static HTML report export (`batch_report.html`).

---

## Configuration

### Environment Variables (`.env`)

| Variable | Description |
| -------- | ----------- |
| `MAGENTO_BASE_URL` | Magento store base URL (e.g. `https://pprod2-oe.sivantos.com`) |
| `MAGENTO_USERNAME` | Magento API username |
| `MAGENTO_PASSWORD` | Magento API password |
| `MAGENTO_WEBSITE_ID` | Magento website ID to filter by |

### Key Constants (`config.py`)

| Constant | Default | Description |
| -------- | ------- | ----------- |
| `MAGENTO_PRODUCTS_FILE` | `data/france_products.json` | Magento product JSON file |
| `MAGENTO_CAT_FILE` | `data/france_categories.json` | Magento category JSON file |
| `MAGENTO_CUSTOMER_GROUP_FILE` | `data/magento_customer_group.json` | Customer group JSON file |
| `PIM_PRODUCTS_FILE` | `data/pim_prod.json` | PIM product JSON file |
| `PIM_CAT_FILE` | `data/pim_cat.json` | PIM category JSON file |
| `MAGENTO_API_PAGE_SIZE` | `100` | Products per API request page |
| `MAGENTO_API_DELAY` | `0.5` | Seconds between API calls |
| `MAGENTO_API_MAX_RETRIES` | `5` | Max retry attempts for API calls |
| `MAGENTO_API_RETRY_DELAY` | `10` | Seconds between retries |

### Type Mapping (PIM → Magento)

| PIM Type | Allowed Magento Types |
| -------- | --------------------- |
| `PRODUCT` | `configurable`, `simple` |
| `BUNDLE` | `bundle` |
| `PRODUCT_VARIANT` | `simple` |

---

## API Endpoints

### Core Comparison

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/health` | `{ ready: bool }` — true once data is loaded |
| GET | `/api/summary` | Dashboard totals + distinct issue categories |
| GET | `/api/reports` | Paginated table rows. Query: `search`, `category`, **`market`**, `sort`, `direction`, `page`, `page_size` |
| GET | `/api/reports/{sku}` | Full comparison detail for one SKU |
| GET | `/api/hierarchy/{sku}` | PIM + Magento hierarchy tree lines |

**Market filter:** each report row carries a `markets` array (the SKU's PIM
customerLabel codes). Pass `?market=DL` to `/api/reports` to restrict the table
to one market; `market=all` (default) shows everything. It composes with
`search` and `category`.

### Customer Group Comparison

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/customer-group-comparison` | Customer group comparison listing for all SKUs |
| GET | `/api/customer-group-comparison/{sku}` | Customer group detail for one SKU |
| GET | `/api/customer-group-comparison/summary` | Summary statistics for customer group match rate |

### Markets

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/markets` | All markets, or `?q=` to search code/description |
| GET | `/api/markets/{code}` | Product breakdown for one brand code |

---

## Frontend Pages

| Page | Route | Description |
| ---- | ----- | ----------- |
| **Dashboard** | `/` | Summary cards: perfect matches, total issues, missing in Magento, missing in PIM, type mismatches, bundle issues, configurable issues, and customer group match rate. Click any card to drill into the filtered comparison table. |
| **Comparison** | `/comparison` | Searchable, sortable, paginated table of all PIM SKUs vs Magento, with a **market dropdown** + status filter. A Markets column shows each SKU's market codes. Click a row for full detail + hierarchy. |
| **SKU Detail** | `/comparison/:sku` | Full per-SKU comparison: type match, bundle slots, configurable children, and side-by-side PIM vs Magento hierarchy trees. |
| **Customer Group Comparison** | `/customer-group-comparison` | Bidirectional comparison of PIM customer labels vs Magento customer groups. Shows shared, PIM-only, and Magento-only groups per SKU. |
| **Customer Group Detail** | `/customer-group-comparison/:sku` | Per-SKU customer group breakdown with full detail. |
| **Markets** | `/markets` | Products per brand/customer-label code. "View in comparison →" jumps to the comparison page pre-filtered by that market. |
| **Market Detail** | `/markets/:code` | Product breakdown by type for a specific market. |
| **Market Matching** | `/market-matching` | Market matching overview — shows how PIM customer labels map to Magento customer groups. |
| **Market Matching Detail** | `/market-matching/:sku` | Per-SKU market matching detail view. |

---

## How the Comparison Works

The comparison is **PIM-driven** — the orchestrator iterates over PIM products
and checks each one against its Magento counterpart. Magento-only products
(missing in PIM) are handled separately.

### 1. Type Comparison

Validates that each PIM product type maps to the correct Magento type using the
mapping table in `config.py` (see above). A `PRODUCT` in PIM should appear as
either `configurable` or `simple` in Magento; a `BUNDLE` must be `bundle`; and a
`PRODUCT_VARIANT` must be `simple`.

### 2. Bundle Comparison

Compares bundle slots and their child SKUs between PIM and Magento. Detects:
- Missing or extra slots
- Child SKU mismatches within a slot

### 3. Configurable Comparison

Compares configurable product child SKUs — identifies children that are present
in one system but missing in the other.

### 4. Customer Group Comparison

Bidirectional comparison showing which customer labels (PIM) and customer groups
(Magento) are shared, PIM-only, or Magento-only for each SKU.

---

## Python Dependencies

| Package | Purpose |
| ------- | ------- |
| `fastapi` | REST API framework |
| `uvicorn` | ASGI server |
| `python-dotenv` | `.env` file loading |
| `requests` | Magento API HTTP client |

See `requirements.txt` for pinned versions.
