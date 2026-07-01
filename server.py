"""
FastAPI backend for the PIM ↔ Magento reconciliation tool.

Loads all source data once at startup, runs the batch comparison, caches the
results, and exposes them (plus hierarchy) as a REST API consumed
by the React frontend.

Run:  uvicorn server:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from config import (
    get_magento_products_file,
    get_magento_cat_file,
    MAGENTO_CUSTOMER_GROUP_FILE,
    PIM_PRODUCTS_FILE,
    PIM_CAT_FILE,
    DATA_DIR,
    MAGENTO_WEBSITE_ID,
)
from loaders.json_loader import load_json
from loaders.pim_loader import parse_pim_products
from loaders.magento_loader import (
    parse_magento_products,
    build_magento_id_to_sku,
    extract_magento_categories,
)
from loaders.magento_category_fetcher import (
    get_token,
    get_store_code_for_website,
    fetch_category_tree_with_retry,
)
from loaders.magento_product_fetcher import get_all_products
from loaders.magento_customer_loader import parse_magento_customer_groups
from comparison.customer_group_comparison import (
    compare_customer_groups,
    batch_compare_customer_groups,
)
from hierarchy.pim_hierarchy import get_pim_hierarchy
from hierarchy.magento_hierarchy import get_magento_hierarchy
from comparison.orchestrator import compare_product, batch_compare
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
    "magento_customer_groups": {},
    "customer_group_comparison": {},
    "id_to_sku": {},
    "rows": [],          # cached comparison rows (one per PIM SKU)
    "rows_by_sku": {},   # sku -> row
    "summary": {},
}


def _load_everything() -> None:
    """Load + parse all source files and pre-compute the batch comparison."""
    print("Loading source files ...")
    magento_products_file = get_magento_products_file()
    magento_cat_file = get_magento_cat_file()
    magento_raw = load_json(magento_products_file)
    magento_cat_raw = load_json(magento_cat_file)
    pim_raw = load_json(PIM_PRODUCTS_FILE)
    pim_cat_raw = load_json(PIM_CAT_FILE)
    print("Parsing ...")
    magento_map = parse_magento_products(magento_raw)
    id_to_sku = build_magento_id_to_sku(magento_raw)
    magento_cat_tree = extract_magento_categories(magento_cat_raw)
    # Merge any other category files present in the data directory so
    # the category map covers all available category JSON dumps.
    try:
        from pathlib import Path
        data_dir = Path(DATA_DIR)
        for p in sorted(data_dir.glob("*_categories.json")):
            if str(p) == magento_cat_file:
                continue
            other_raw = load_json(str(p))
            other_tree = extract_magento_categories(other_raw)
            if other_tree:
                magento_cat_tree.extend(other_tree)
    except Exception:
        pass
    pim_map = parse_pim_products(pim_raw)
    magento_customer_groups = parse_magento_customer_groups(MAGENTO_CUSTOMER_GROUP_FILE)

    STATE["pim_map"] = pim_map
    STATE["pim_cat_data"] = pim_cat_raw
    STATE["magento_map"] = magento_map
    STATE["magento_cat_tree"] = magento_cat_tree
    STATE["magento_customer_groups"] = magento_customer_groups
    STATE["id_to_sku"] = id_to_sku
    STATE["magento_products_file"] = magento_products_file
    STATE["magento_cat_file"] = magento_cat_file

    print(
        f"Ready - {len(pim_map):,} PIM SKUs | "
        f"{len(magento_map):,} Magento SKUs | "
        f"{len(id_to_sku):,} ID->SKU mappings"
    )

    print("Running batch comparison ...")
    reports = batch_compare(pim_map, magento_map, id_to_sku, magento_cat_tree)
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
            "found_in_magento": True,
            "type_comparison": None,
            "bundle_comparison": None,
            "configurable_comparison": None,
            "category_comparison": None,
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

    # Compute customer group comparison data
    print("Computing customer group comparison data...")
    cg_data = batch_compare_customer_groups(pim_map, magento_customer_groups, magento_map)
    STATE["customer_group_comparison"] = {}
    for data in cg_data:
        STATE["customer_group_comparison"][data["sku"]] = data

    # Calculate customer group comparison summary statistics.
    # With the bidirectional definition, fully_matched == True only when
    # pim_only AND magento_only are both empty. Anything else is a problem.
    skus_with_pim_data = [sku for sku in pim_map.keys() if pim_map[sku].get("customer_labels")]
    total_skus_with_cg = len(skus_with_pim_data)
    matched_skus = sum(1 for data in cg_data if data["fully_matched"])
    not_matched_skus = sum(1 for data in cg_data if not data["fully_matched"])

    total_cg_mappings = sum(data["total_pim_groups"] for data in cg_data)
    matched_mappings = sum(data["match_count"] for data in cg_data)

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
        "issue_categories": all_cats,
        # Customer group comparison specific stats
        "customer_group_comparison": {
            "total_skus_with_groups": total_skus_with_cg,
            "matched_skus": matched_skus,
            "not_matched_skus": not_matched_skus,
            "total_pim_groups": total_cg_mappings,
            "matched_groups": matched_mappings,
            "match_rate": (matched_mappings / total_cg_mappings * 100) if total_cg_mappings > 0 else 0
        }
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


def _save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def _fetch_magento_data() -> tuple[str, str]:
    token = get_token()
    store = get_store_code_for_website(token, MAGENTO_WEBSITE_ID)
    products = get_all_products([token], store)
    categories = fetch_category_tree_with_retry([token], store["code"])

    products_file = Path(DATA_DIR) / f"{store['code']}_products.json"
    categories_file = Path(DATA_DIR) / f"{store['code']}_categories.json"
    _save_json(products_file, products)
    _save_json(categories_file, categories)

    return str(products_file), str(categories_file)


# ──────────────────────────────────────────────────────────────────────────
#  Endpoints
# ──────────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"ready": STATE["ready"]}


@app.get("/api/summary")
def summary():
    _require_ready()
    summary_data = STATE["summary"].copy()
    summary_data["magento_products_file"] = STATE.get("magento_products_file")
    summary_data["magento_cat_file"] = STATE.get("magento_cat_file")
    return summary_data


@app.post("/api/magento-reload")
def magento_reload(fetch: bool = Query(False, description="Fetch fresh Magento data from the Magento API when true; otherwise reload existing files.")):
    if fetch:
        products_file, categories_file = _fetch_magento_data()
        message = f"Fetched Magento data to {products_file} and {categories_file}."
        # Clear cached file selection if config uses dynamic resolution.
    else:
        message = "Reloaded existing Magento Magento data files."

    _load_everything()
    return {
        "status": "ok",
        "message": message,
        "magento_products_file": STATE.get("magento_products_file"),
        "magento_cat_file": STATE.get("magento_cat_file"),
    }


@app.get("/api/reports")
def reports(
    search: str = Query("", description="Match against SKU or name"),
    category: str = Query("all", description="'all', 'ok', an issue category, or a product type (simple/bundle/configurable)"),
    sort: str = Query("sku"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """Server-side filtered / sorted / paginated comparison rows (table view)."""
    _require_ready()
    rows = STATE["rows"]
    q = search.strip().lower()

    # Product-type categories that select by type rather than issue
    PRODUCT_TYPE_CATEGORIES = {"simple", "bundle", "configurable"}

    def matches(r: dict) -> bool:
        if q and q not in r["sku"].lower() and q not in (r.get("name") or "").lower():
            return False
        if category == "all":
            return True
        if category == "ok":
            return not r["has_issues"]
        if category in PRODUCT_TYPE_CATEGORIES:
            # Match based on the resolved product type
            pim_t = r.get("pim_type", "")
            mag_t = r.get("magento_type", "")
            # PIM types: PRODUCT, BUNDLE, PRODUCT_VARIANT, NOT IN PIM
            # Magento types: simple, bundle, configurable
            if category == "bundle":
                return pim_t == "BUNDLE" or mag_t == "bundle"
            if category == "configurable":
                return pim_t == "PRODUCT" and mag_t == "configurable"
            if category == "simple":
                return pim_t in ("PRODUCT_VARIANT", "NOT IN PIM") or (pim_t == "PRODUCT" and mag_t == "simple")
            return False
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
            sku, STATE["pim_map"], STATE["magento_map"], STATE["id_to_sku"], STATE.get("magento_cat_tree")
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


# ──────────────────────────────────────────────────────────────────────────
#  Customer Group Comparison Endpoints
# ──────────────────────────────────────────────────────────────────────────


@app.get("/api/customer-group-comparison/summary")
def customer_group_summary():
    """Get summary statistics for customer group comparison."""
    _require_ready()
    return STATE["summary"].get("customer_group_comparison", {})


@app.get("/api/customer-group-comparison")
def customer_group_reports(
    search: str = Query("", description="Match against SKU or name"),
    match_status: str = Query("all", description="'all', 'matched', or 'not_matched'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    """Get customer group comparison data with filtering.

    match_status values:
      - 'all':         every SKU
      - 'matched':     pim_only and magento_only are both empty
      - 'not_matched': any difference on either side (a problem)
    """
    _require_ready()
    cg_data = STATE["customer_group_comparison"]

    def matches_match_status(data: dict) -> bool:
        if match_status == "all":
            return True
        if match_status == "matched":
            return data["fully_matched"]
        if match_status == "not_matched":
            return not data["fully_matched"]
        return True

    filtered = [
        data for sku, data in cg_data.items()
        if (not search or search.lower() in sku.lower() or
            any(search.lower() in pg["code"].lower() for pg in data.get("pim_groups", [])))
        and matches_match_status(data)
    ]

    total = len(filtered)
    start = (page - 1) * page_size
    page_data = filtered[start:start + page_size]

    # Format for frontend consumption
    items = []
    for data in page_data:
        items.append({
            "sku": data["sku"],
            "pim_groups": data.get("pim_groups", []),
            "magento_groups": data.get("magento_groups", []),
            "shared": data.get("shared", []),
            "pim_only": data.get("pim_only", []),
            "magento_only": data.get("magento_only", []),
            "match_count": data["match_count"],
            "total_pim_groups": data["total_pim_groups"],
            "fully_matched": data["fully_matched"],
            "match_percentage": (data["match_count"] / data["total_pim_groups"] * 100) if data["total_pim_groups"] > 0 else 0
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "items": items,
    }


@app.get("/api/customer-group-comparison/{sku}")
def customer_group_detail(sku: str):
    """Get detailed customer group comparison for a specific SKU."""
    _require_ready()
    data = STATE["customer_group_comparison"].get(sku)
    if data is None:
        # PIM is the source of truth; only PIM SKUs are included in comparison
        if sku not in STATE["pim_map"]:
            raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found in PIM.")
        # Return empty data structure
        data = {
            "sku": sku,
            "pim_groups": [],
            "magento_groups": [],
            "shared": [],
            "pim_only": [],
            "magento_only": [],
            "match_count": 0,
            "total_pim_groups": 0,
            "fully_matched": True,
        }
    return data
