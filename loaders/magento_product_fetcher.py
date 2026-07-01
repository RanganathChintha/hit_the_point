"""Fetch Magento products by website_id via the REST API.

Entry-point::

    python -m loaders.magento_product_fetcher

Credentials live in the ``.env`` file (see root ``.env`` template).
The final JSON is saved to ``data/<store_code>_products.json`` so
`magento_loader.py` can pick it up directly.
"""

import json as _json
import socket
import ssl
import time
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config import (
    MAGENTO_API_DELAY,
    MAGENTO_API_MAX_RETRIES,
    MAGENTO_API_PAGE_SIZE,
    MAGENTO_API_RETRY_DELAY,
    MAGENTO_BASE_URL,
    MAGENTO_PASSWORD,
    MAGENTO_USERNAME,
    MAGENTO_WEBSITE_ID,
    DATA_DIR,
)

_SSL = ssl.create_default_context()
_SSL.check_hostname = False
_SSL.verify_mode = ssl.CERT_NONE


# ---------------------------------------------------------------------------
#  Utilities
# ---------------------------------------------------------------------------


class _Response:
    """Drop-in so callers keep ``resp.json()`` / ``resp.status_code``."""  # ponytail: minimal adapter

    __slots__ = ("_resp", "status_code")

    def __init__(self, http_resp):
        self._resp = http_resp
        self.status_code = http_resp.getcode()

    def json(self):
        return _json.load(self._resp)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise HTTPError(self._resp.url, self.status_code, None, None, None)


class _ErrorResponse:
    """Mirrors _Response for 4xx/5xx so callers can check status_code before raising."""

    __slots__ = ("_exc", "status_code")

    def __init__(self, exc: HTTPError):
        self._exc = exc
        self.status_code = exc.code

    def json(self):
        if self._exc.fp is not None:
            try:
                return _json.load(self._exc.fp)
            except Exception:
                pass
        raise self._exc

    def raise_for_status(self):
        raise self._exc


def _req_json(method: str, url: str, **kwargs):
    """HTTPS request with disabled SSL verification."""
    timeout = kwargs.pop("timeout", 60)
    headers = kwargs.pop("headers", {})
    json_data = kwargs.pop("json", None)
    params = kwargs.pop("params", None)

    if params:
        from urllib.parse import urlencode
        url = f"{url}?{urlencode(params)}"

    data = None
    if json_data is not None:
        data = _json.dumps(json_data).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = Request(url, data=data, headers=headers, method=method.upper())
    try:
        return _Response(urlopen(req, context=_SSL, timeout=timeout))
    except HTTPError as exc:
        return _ErrorResponse(exc)
    except socket.timeout:
        raise TimeoutError() from None
    except URLError as exc:
        raise ConnectionError(str(exc.reason)) from exc


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
    resp.raise_for_status()
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

    resp = _req_json(
        "get",
        f"{MAGENTO_BASE_URL}/rest/V1/store/storeViews",
        headers=_auth_headers(token),
        timeout=30,
    )
    resp.raise_for_status()
    stores = resp.json()

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
#  Step 3 – Fetch paginated products
# ---------------------------------------------------------------------------


def fetch_page_with_retry(
    token_ref: list,
    store_code: str,
    website_id: int,
    page: int,
) -> dict:
    """Fetch a single page with exponential-ish retry."""

    params = {
        "searchCriteria[filter_groups][0][filters][0][field]": "website_id",
        "searchCriteria[filter_groups][0][filters][0][value]": website_id,
        "searchCriteria[filter_groups][0][filters][0][condition_type]": "eq",
        "searchCriteria[currentPage]": page,
        "searchCriteria[pageSize]": MAGENTO_API_PAGE_SIZE,
        "searchCriteria[sortOrders][0][field]": "sku",
        "searchCriteria[sortOrders][0][direction]": "ASC",
    }

    for attempt in range(1, MAGENTO_API_MAX_RETRIES + 1):
        try:
            resp = _req_json(
                "get",
                f"{MAGENTO_BASE_URL}/rest/{store_code}/V1/products",
                headers=_auth_headers(token_ref[0]),
                params=params,
                timeout=60,
            )

            if resp.status_code == 401:
                print(f"\n   🔄 Token expired! Refreshing (attempt {attempt})…")
                token_ref[0] = get_token()
                continue

            resp.raise_for_status()
            return resp.json()

        except (ConnectionError, TimeoutError) as exc:
            label = "Timeout" if isinstance(exc, TimeoutError) else "Connection error"
            print(f"\n   ⚠️  {label} — page {page} (attempt {attempt}/{MAGENTO_API_MAX_RETRIES})")
            if attempt < MAGENTO_API_MAX_RETRIES:
                print(f"   ⏳ Waiting {MAGENTO_API_RETRY_DELAY}s then retrying…")
                time.sleep(MAGENTO_API_RETRY_DELAY)
                print(f"   🔄 Refreshing token…")
                token_ref[0] = get_token()
            else:
                raise

    return {}  # Should never reach; satisfies mypy


def get_all_products(token_ref: list, store: dict) -> list[dict]:
    """Iterate every page and return the raw product list."""
    store_code, website_id = store["code"], store["website_id"]
    print(f"📦 Fetching products for website_id={website_id} via [{store_code}]")
    print(f"   Page size: {MAGENTO_API_PAGE_SIZE} | Delay: {MAGENTO_API_DELAY}s | Retries: {MAGENTO_API_MAX_RETRIES}\n")

    first = fetch_page_with_retry(token_ref, store_code, website_id, 1)
    total_count = first.get("total_count", 0)
    all_items = first.get("items", [])
    total_pages = (total_count + MAGENTO_API_PAGE_SIZE - 1) // MAGENTO_API_PAGE_SIZE

    print(f"   📊 Total products : {total_count}")
    print(f"   📄 Total pages    : {total_pages}")
    print(f"   ✅ Page 1/{total_pages}", end="", flush=True)

    for page in range(2, total_pages + 1):
        print(f" → {page}", end="", flush=True)
        page_data = fetch_page_with_retry(token_ref, store_code, website_id, page)
        all_items += page_data.get("items", [])
        time.sleep(MAGENTO_API_DELAY)

    print(f"\n\n🎉 All done! Total fetched: {len(all_items)} products\n")
    return all_items


# ---------------------------------------------------------------------------
#  Step 4 – Save raw products
# ---------------------------------------------------------------------------


def save_to_json(products: list[dict], store: dict) -> str:  # type: ignore[no-untyped-def]
    """Persist raw products (full, untouched) to ``data/<store_code>_products.json``."""
    import os

    os.makedirs(DATA_DIR, exist_ok=True)
    output_file = os.path.join(DATA_DIR, f"{store['code']}_products.json")

    payload = {
        "summary": {
            "website_id": store["website_id"],
            "store_code": store["code"],
            "store_name": store["name"],
            "total_count": len(products),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "products": products,  # 👈 full raw products, no cleaning
    }

    with open(output_file, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=4, ensure_ascii=False)

    print(f"\n💾 Saved to '{output_file}'")
    return output_file


# ---------------------------------------------------------------------------
#  Step 6 – CLI entry-point
# ---------------------------------------------------------------------------


def print_summary(products: list, store: dict) -> None:  # type: ignore[no-untyped-def]
    """Pretty-print a fetch summary."""
    type_counts: dict[str, int] = {}
    for p in products:
        t = p.get("type_id", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    enabled = sum(1 for p in products if p.get("status") == 1)
    disabled = sum(1 for p in products if p.get("status") == 2)

    print("=" * 55)
    print(f"  📊 SUMMARY — Website ID: {store['website_id']}")
    print(f"  🏪 Store Code : {store['code']}")
    print(f"  🏷️  Store Name : {store['name']}")
    print("=" * 55)
    print(f"  Total Products   : {len(products)}")
    print(f"  ✅ Enabled       : {enabled}")
    print(f"  ❌ Disabled      : {disabled}")
    print(f"\n  📦 By Product Type:")
    for ptype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"     {ptype:<20} : {count}")
    print("=" * 55)


def main() -> None:
    token = get_token()
    token_ref = [token]

    store = get_store_code_for_website(token_ref[0], MAGENTO_WEBSITE_ID)

    # Fetch raw products — no cleaning
    raw_products = get_all_products(token_ref, store)

    print_summary(raw_products, store)
    output_file = save_to_json(raw_products, store)  # save full raw data

    print(f"\n🚀 All done! Check '{output_file}'\n")


if __name__ == "__main__":
    main()
