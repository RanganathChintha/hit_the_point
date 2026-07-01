def normalize_slot(name: str) -> str:
    """Normalize a slot/set name to a consistent key."""
    if not name:
        return ""
    return name.strip().lower().replace(" ", "_").replace("-", "_")

def _extract_pim_list(data, depth: int = 0) -> list:
    """
    Recursively search any JSON structure for a list of dicts
    that contain a 'sku' key — that is the product list.
    """
    if depth > 6:
        return []

    if isinstance(data, list):
        if data and isinstance(data[0], dict) and "sku" in data[0]:
            return data
        for item in data:
            result = _extract_pim_list(item, depth + 1)
            if result:
                return result

    if isinstance(data, dict):
        for key in ["items", "products", "product", "results", "data", "records"]:
            val = data.get(key)
            if val is None:
                continue
            if isinstance(val, list) and val and isinstance(val[0], dict) and "sku" in val[0]:
                return val
            result = _extract_pim_list(val, depth + 1)
            if result:
                return result
        for val in data.values():
            if isinstance(val, (list, dict)):
                result = _extract_pim_list(val, depth + 1)
                if result:
                    return result

    return []

def parse_pim_products(data) -> dict:
    """
    Parse raw PIM JSON into a flat SKU-keyed dict.
    Handles PRODUCT, BUNDLE, and PRODUCT_VARIANT types.
    """
    result = {}
    items  = _extract_pim_list(data)

    for prod in items:
        if not isinstance(prod, dict):
            continue
        sku   = prod.get("sku")
        ptype = prod.get("productType", "PRODUCT")
        if not sku:
            continue

        entry = {
            "sku":             sku,
            "name":            prod.get("name", ""),
            "product_type":    ptype,
            "child_skus":      [],
            "parent_skus":     prod.get("parentProductSku", []) or [],
            "bundle_sets":     {},
            "categoryIds":     prod.get("categoryIds", []),
            "customer_labels": [
                {
                    "code":        cl.get("code", ""),
                    "description": cl.get("description", ""),
                }
                for cl in (prod.get("customerLabels") or [])
            ],
        }

        if ptype == "PRODUCT":
            entry["child_skus"] = [
                c["sku"]
                for c in prod.get("childProducts", [])
                if c.get("sku")
            ]

        elif ptype == "BUNDLE":
            for bs in prod.get("bundleSets", []):
                raw_name  = bs.get("bundleSetName", "")
                norm_name = normalize_slot(raw_name)
                skus = [
                    cp["sku"]
                    for cp in bs.get("childProducts", [])
                    if cp.get("sku")
                ]
                if norm_name in entry["bundle_sets"]:
                    entry["bundle_sets"][norm_name]["skus"].extend(skus)
                else:
                    entry["bundle_sets"][norm_name] = {
                        "name":       norm_name,
                        "set_type":   bs.get("bundleSetType", ""),
                        "is_default": bs.get("isDefault", False),
                        "mandatory":  bs.get("isMandatory", False),
                        "skus":       skus,
                    }

        result[sku] = entry

    return result

def build_pim_category_map(pim_cat_data: dict) -> dict:
    """
    Flatten the PIM category hierarchy into:
        { categoryId -> { name, parent } }
    """
    cat_map = {}
    try:
        categories = (
            pim_cat_data
            .get("data", {})
            .get("category", {})
            .get("getCategoryHierarchyByMarket", [{}])[0]
            .get("categories", [])
        )
    except (IndexError, AttributeError):
        categories = []

    for cat in categories:
        cat_map[cat["categoryId"]] = {
            "name":   cat.get("categoryName", "Unknown"),
            "parent": cat.get("parentCategoryId"),
        }
    return cat_map
