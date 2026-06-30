"""
FastAPI backend for the PIM ↔ Magento reconciliation tool.

Loads all source data once at startup, runs the batch comparison, caches the
results, and exposes them (plus markets and hierarchy) as a REST API consumed
by the React frontend.

Run:  uvicorn server:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import (
    MAGENTO_PRODUCTS_FILE,
    MAGENTO_CAT_FILE,
    PIM_PRODUCTS_FILE,
    PIM_CAT_FILE,
)
from loaders.json_loader import load_json
from loaders.pim_loader import parse_pim_products
from loaders.magento_loader import (
    parse_magento_products,
    build_magento_id_to_sku,
    extract_magento_categories,
)
from hierarchy.pim_hierarchy import get_pim_hierarchy
from hierarchy.magento_hierarchy import get_magento_hierarchy
from comparison.orchestrator import compare_product, batch_compare
from analysis.market_counter import (
    build_market_index,
    list_all_markets,
    get_market_products,
    search_market_by_description,
)
from reporting.html_reporter import (
    _build_row,
    _has_issues,
    _issue_categories,
)

# ──────────────────────────────────────────────────────────────────────────
#  In-memory application state (populated at startup)
# ──────────────────────────────────────────────────────────────────────────

STATE: dict = {
    "ready": False,
    "pim_map": {},
    "pim_cat_data": {},
    "magento_map": {},
    "magento_cat_tree": [],
    "id_to_sku": {},
    "market_index": {},
    "rows": [],          # cached comparison rows (one per PIM SKU)
    "rows_by_sku": {},   # sku -> row
    "summary": {},
}


def _load_everything() -> None:
    """Load + parse all source files and pre-compute the batch comparison."""
    print("Loading source files ...")
    magento_raw = load_json(MAGENTO_PRODUCTS_FILE)
    magento_cat_raw = load_json(MAGENTO_CAT_FILE)
    pim_raw = load_json(PIM_PRODUCTS_FILE)
    pim_cat_raw = load_json(PIM_CAT_FILE)

    print("Parsing ...")
    magento_map = parse_magento_products(magento_raw)
    id_to_sku = build_magento_id_to_sku(magento_raw)
    magento_cat_tree = extract_magento_categories(magento_cat_raw)
    pim_map = parse_pim_products(pim_raw)

    STATE["pim_map"] = pim_map
    STATE["pim_cat_data"] = pim_cat_raw
    STATE["magento_map"] = magento_map
    STATE["magento_cat_tree"] = magento_cat_tree
    STATE["id_to_sku"] = id_to_sku
    STATE["market_index"] = build_market_index(pim_map)

    print(
        f"Ready - {len(pim_map):,} PIM SKUs | "
        f"{len(magento_map):,} Magento SKUs | "
        f"{len(id_to_sku):,} ID->SKU mappings"
    )

    print("Running batch comparison ...")
    reports = batch_compare(pim_map, magento_map, id_to_sku)
    rows = [_build_row(r, pim_map, magento_map) for r in reports]

    # Add rows for SKUs in Magento but not in PIM (Missing in PIM)
    pim_skus = set(pim_map)
    magento_skus = set(magento_map)
    missing_in_pim_skus = magento_skus - pim_skus
    for sku in missing_in_pim_skus:
        magento_entry = magento_map.get(sku, {})
        row = {
            "sku": sku,
            "name": magento_entry.get("name", ""),
            "pim_type": "NOT IN PIM",
            "magento_type": magento_entry.get("type_id", "?"),
            "has_issues": True,
            "issue_cats": ["Missing in PIM"],
            "markets": [],
            "found_in_magento": True,
            "type_comparison": None,
            "bundle_comparison": None,
            "configurable_comparison": None,
        }
        rows.append(row)

    STATE["rows"] = rows
    STATE["rows_by_sku"] = {r["sku"]: r for r in rows}

    total = len(reports)
    perfect = sum(1 for r in reports if not _has_issues(r))
    missing = sum(1 for r in reports if not r["found_in_magento"])
    type_mm = sum(
        1 for r in reports
        if r.get("type_comparison") and not r["type_comparison"]["types_match"]
    )
    bundle_iss = sum(
        1 for r in reports if _has_issues(r) and r.get("bundle_comparison")
    )
    config_iss = sum(
        1 for r in reports if _has_issues(r) and r.get("configurable_comparison")
    )

    # Distinct issue categories present (used to populate frontend filter)
    all_cats = sorted({c for r in rows for c in r["issue_cats"]})

    # Count products in Magento but not in PIM
    missing_in_pim = len(missing_in_pim_skus)

    STATE["summary"] = {
        "total": total,
        "perfect": perfect,
        "total_issues": total - perfect,
        "missing_in_magento": missing,
        "missing_in_pim": missing_in_pim,
        "type_mismatches": type_mm,
        "bundle_issues": bundle_iss,
        "configurable_issues": config_iss,
        "pim_sku_count": len(pim_map),
        "magento_sku_count": len(magento_map),
        "market_count": len(STATE["market_index"]),
        "issue_categories": all_cats,
    }
    STATE["ready"] = True
    print("Backend ready.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_everything()
    yield
    STATE.clear()


app = FastAPI(
    title="PIM ↔ Magento Reconciliation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_ready() -> None:
    if not STATE["ready"]:
        raise HTTPException(status_code=503, detail="Data still loading, retry shortly.")


# ──────────────────────────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"ready": STATE["ready"]}


@app.get("/api/summary")
def summary():
    _require_ready()
    return STATE["summary"]


@app.get("/api/reports")
def reports(
    search: str = Query("", description="Match against SKU or name"),
    category: str = Query("all", description="'all', 'ok', or an issue category"),
    market: str = Query("all", description="'all' or a market/brand code (e.g. AC, DL)"),
    sort: str = Query("sku"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """Server-side filtered / sorted / paginated comparison rows (table view)."""
    _require_ready()
    rows = STATE["rows"]
    q = search.strip().lower()
    market_code = market.strip().upper()

    def matches(r: dict) -> bool:
        if q and q not in r["sku"].lower() and q not in (r.get("name") or "").lower():
            return False
        if market_code != "ALL" and market_code not in r.get("markets", []):
            return False
        if category == "all":
            return True
        if category == "ok":
            return not r["has_issues"]
        if category == "Missing in Magento":
            return "Missing in Magento" in r["issue_cats"]
        if category == "Missing in PIM":
            return "Missing in PIM" in r["issue_cats"]
        return category in r["issue_cats"]

    filtered = [r for r in rows if matches(r)]

    sort_key = sort if sort in ("sku", "name", "pim_type", "magento_type", "has_issues") else "sku"
    reverse = direction == "desc"
    filtered.sort(
        key=lambda r: (r.get(sort_key) if r.get(sort_key) is not None else ""),
        reverse=reverse,
    )

    total = len(filtered)
    start = (page - 1) * page_size
    page_rows = filtered[start:start + page_size]

    # Slim payload for the table; full detail comes from /api/reports/{sku}
    items = [
        {
            "sku": r["sku"],
            "name": r["name"],
            "pim_type": r["pim_type"],
            "magento_type": r["magento_type"],
            "has_issues": r["has_issues"],
            "issue_cats": r["issue_cats"],
            "markets": r.get("markets", []),
        }
        for r in page_rows
    ]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": items,
    }


@app.get("/api/reports/{sku}")
def report_detail(sku: str):
    """Full comparison detail for a single SKU."""
    _require_ready()
    row = STATE["rows_by_sku"].get(sku)
    if row is None:
        # Compute on demand (e.g. a SKU only present in Magento, not PIM)
        report = compare_product(
            sku, STATE["pim_map"], STATE["magento_map"], STATE["id_to_sku"]
        )
        if not report["found_in_pim"] and not report["found_in_magento"]:
            raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found.")
        row = _build_row(report, STATE["pim_map"], STATE["magento_map"])
    return row


@app.get("/api/hierarchy/{sku}")
def hierarchy(sku: str):
    """PIM + Magento category → bundle → variant tree lines for a SKU."""
    _require_ready()
    pim_lines = get_pim_hierarchy(sku, STATE["pim_map"], STATE["pim_cat_data"])
    magento_lines = get_magento_hierarchy(
        sku, STATE["magento_map"], STATE["magento_cat_tree"]
    )
    return {
        "sku": sku,
        "found_in_pim": sku in STATE["pim_map"],
        "found_in_magento": sku in STATE["magento_map"],
        "pim": pim_lines,
        "magento": magento_lines,
    }


@app.get("/api/markets")
def markets(q: str = Query("", description="Optional search over code/description")):
    """List all markets, or search by code/description when q is provided."""
    _require_ready()
    if q.strip():
        results = search_market_by_description(q, STATE["market_index"])
        return {"items": sorted(results, key=lambda m: m["code"]), "count": len(results)}
    items = list_all_markets(STATE["market_index"])
    return {"items": items, "count": len(items)}


@app.get("/api/markets/{code}")
def market_detail(code: str):
    """Full breakdown for one market/brand code."""
    _require_ready()
    detail = get_market_products(code, STATE["market_index"], STATE["pim_map"])
    if detail is None:
        suggestions = search_market_by_description(code, STATE["market_index"])
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Brand code '{code.upper()}' not found.",
                "suggestions": sorted(suggestions, key=lambda m: m["code"]),
            },
        )
    return detail
