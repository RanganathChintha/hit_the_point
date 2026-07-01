"""Fetch Magento category tree by website_id via the REST API.

Entry-point::

    python -m loaders.magento_category_fetcher

Credentials live in the ``.env`` file (see root ``.env`` template).
The final JSON is saved to ``data/<store_code>_categories.json`` so
`magento_loader.py` can pick it up directly.
"""

import json
import os
import time
from datetime import datetime

import urllib3

from config import (
    MAGENTO_API_MAX_RETRIES,
    MAGENTO_API_RETRY_DELAY,
    MAGENTO_BASE_URL,
    MAGENTO_PASSWORD,
    MAGENTO_USERNAME,
    MAGENTO_WEBSITE_ID,
    DATA_DIR,
)

try:
    import requests  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # type: ignore[no-untyped-call]


# ---------------------------------------------------------------------------
#  Utilities
# ---------------------------------------------------------------------------


def _req_json(method: str, url: str, **kwargs):  # type: ignore[no-untyped-def]
    """Thin wrapper around ``requests.{method}`` that disses SSL."""
    if requests is None:
        raise RuntimeError("requests is not installed – pip install requests")
    resp = getattr(requests, method)(
        url,
        verify=False,
        timeout=kwargs.pop("timeout", 60),
        **kwargs,
    )
    resp.raise_for_status()
    return resp


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
#  Step 1 – Authenticate
# ---------------------------------------------------------------------------


def get_token() -> str:
    """Authenticate with Magento and return the admin bearer token."""
    print("🔐 Authenticating…")
    resp = _req_json(
        "post",
        f"{MAGENTO_BASE_URL}/rest/V1/integration/admin/token",
        json={"username": MAGENTO_USERNAME, "password": MAGENTO_PASSWORD},
        timeout=30,
    )
    token = resp.json().strip('"')
    print("✅ Token retrieved!\n")
    return token


# ---------------------------------------------------------------------------
#  Step 2 – Resolve store code from website_id
# ---------------------------------------------------------------------------


def get_store_code_for_website(token: str, website_id: int) -> dict:
    """Return *{code, name, website_id, store_id}* for the first
    non-admin store view matching *website_id*."""
    print(f"🔍 Looking up store view for website_id={website_id}…")

    stores = _req_json(
        "get",
        f"{MAGENTO_BASE_URL}/rest/V1/store/storeViews",
        headers=_auth_headers(token),
        timeout=30,
    ).json()

    matched = [
        {
            "code": s["code"],
            "name": s["name"],
            "website_id": s.get("website_id"),
            "store_id": s.get("id"),
        }
        for s in stores
        if s.get("website_id") == website_id and s["code"] != "admin"
    ]

    if not matched:
        raise ValueError(f"❌ No store view found for website_id: {website_id}")

    # Diagnostics
    print(f"✅ Found {len(matched)} store view(s) for website_id {website_id}:\n")
    print(f"   {'Store Code':<35} {'Website ID':<12} {'Store ID'}")
    print(f"   {'-'*35} {'-'*12} {'-'*10}")
    for s in matched:
        print(f"   🏪 {s['code']:<35} {s['website_id']!s:<12} {s['store_id']}")
    print()

    selected = matched[0]
    print(f"   📌 Using store code: '{selected['code']}'\n")
    return selected


# ---------------------------------------------------------------------------
#  Step 3 – Fetch full nested category tree
# ---------------------------------------------------------------------------


def fetch_category_tree_with_retry(token_ref: list, store_code: str) -> dict:
    """Call ``GET /rest/{store_code}/V1/categories`` and return the full
    nested category tree as-is from the API."""

    url = f"{MAGENTO_BASE_URL}/rest/{store_code}/V1/categories"

    for attempt in range(1, MAGENTO_API_MAX_RETRIES + 1):
        try:
            print(f"   📡 Calling: {url}")
            resp = requests.get(  # type: ignore[union-attr]
                url,
                headers=_auth_headers(token_ref[0]),
                verify=False,
                timeout=60,
            )

            # Token expired → refresh
            if resp.status_code == 401:
                print(f"\n   🔄 Token expired! Refreshing (attempt {attempt})…")
                token_ref[0] = get_token()
                continue

            resp.raise_for_status()
            return resp.json()  # ✅ full nested tree

        except requests.exceptions.ConnectionError:  # type: ignore[union-attr]
            print(f"\n   ⚠️  Connection error (attempt {attempt}/{MAGENTO_API_MAX_RETRIES})")
            if attempt < MAGENTO_API_MAX_RETRIES:
                print(f"   ⏳ Waiting {MAGENTO_API_RETRY_DELAY}s then retrying…")
                time.sleep(MAGENTO_API_RETRY_DELAY)
                print(f"   🔄 Refreshing token…")
                token_ref[0] = get_token()
            else:
                raise

        except requests.exceptions.Timeout:  # type: ignore[union-attr]
            print(f"\n   ⚠️  Timeout (attempt {attempt}/{MAGENTO_API_MAX_RETRIES})")
            if attempt < MAGENTO_API_MAX_RETRIES:
                print(f"   ⏳ Waiting {MAGENTO_API_RETRY_DELAY}s then retrying…")
                time.sleep(MAGENTO_API_RETRY_DELAY)
            else:
                raise

    return {}  # Should never reach


# ---------------------------------------------------------------------------
#  Step 4 – Flatten tree for summary stats (not for output)
# ---------------------------------------------------------------------------


def flatten_tree(node: dict, result: list | None = None) -> list:
    """Recursively walk the nested tree and collect all category nodes
    into a flat list — used only for summary stats, not for output."""
    if result is None:
        result = []

    result.append(node)

    for child in node.get("children_data", []):
        flatten_tree(child, result)

    return result


# ---------------------------------------------------------------------------
#  Step 5 – Print summary
# ---------------------------------------------------------------------------


def print_summary(category_tree: dict, store: dict) -> None:
    """Pretty-print a fetch summary."""
    all_nodes = flatten_tree(category_tree)

    active = sum(1 for c in all_nodes if c.get("is_active") is True)
    inactive = sum(1 for c in all_nodes if c.get("is_active") is False)

    # Count by level
    level_counts: dict[int, int] = {}
    for c in all_nodes:
        lvl = c.get("level", 0)
        level_counts[lvl] = level_counts.get(lvl, 0) + 1

    # Total product count (leaf nodes only)
    total_products_linked = sum(
        c.get("product_count", 0)
        for c in all_nodes
        if not c.get("children_data")  # leaf categories only
    )

    print("=" * 55)
    print(f"  📊 SUMMARY — Website ID: {store['website_id']}")
    print(f"  🏪 Store Code : {store['code']}")
    print(f"  🏷️  Store Name : {store['name']}")
    print("=" * 55)
    print(f"  Total Category Nodes : {len(all_nodes)}")
    print(f"  ✅ Active             : {active}")
    print(f"  ❌ Inactive           : {inactive}")
    print(f"  🔗 Products (leaves)  : {total_products_linked}")
    print(f"\n  📂 By Level:")
    for level, count in sorted(level_counts.items()):
        print(f"     Level {level:<5} : {count} categories")
    print("=" * 55)


# ---------------------------------------------------------------------------
#  Step 6 – Save to JSON
# ---------------------------------------------------------------------------


def save_to_json(category_tree: dict, store: dict) -> str:
    """Persist the full nested category tree to
    ``data/<store_code>_categories.json``."""

    os.makedirs(DATA_DIR, exist_ok=True)
    output_file = os.path.join(DATA_DIR, f"{store['code']}_categories.json")

    all_nodes = flatten_tree(category_tree)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "summary": {
            "website_id": store["website_id"],
            "store_code": store["code"],
            "store_name": store["name"],
            "total_categories": len(all_nodes),
            "generated_at": generated_at,
        },
        "category_tree": category_tree,  # ✅ full nested tree as-is from API
    }

    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=4, ensure_ascii=False)

    print(f"\n💾 Saved to '{output_file}'")
    return output_file


# ---------------------------------------------------------------------------
#  CLI entry-point
# ---------------------------------------------------------------------------


def main() -> None:
    token = get_token()
    token_ref = [token]

    store = get_store_code_for_website(token_ref[0], MAGENTO_WEBSITE_ID)

    # Fetch full nested category tree
    print(f"📂 Fetching category tree via [{store['code']}]…\n")
    category_tree = fetch_category_tree_with_retry(token_ref, store["code"])
    print(f"\n✅ Category tree fetched successfully!\n")

    # Summary + Save
    print_summary(category_tree, store)
    output_file = save_to_json(category_tree, store)

    print(f"\n🚀 All done! Check '{output_file}'\n")


if __name__ == "__main__":
    main()
