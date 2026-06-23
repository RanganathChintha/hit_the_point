from loaders.france_loader import build_france_category_map

def _resolve_france_category_path(cat_id: int, cat_map: dict) -> list:
    """Walk up the France parent chain -> root-to-leaf path."""
    path    = []
    current = cat_id
    visited = set()
    while current and current not in visited:
        visited.add(current)
        entry = cat_map.get(current)
        if not entry:
            path.insert(0, f"[Unknown: {current}]")
            break
        path.insert(0, entry["name"])
        current = entry.get("parent_id")
    return path

def _find_france_parent_bundle(sku: str, france_products: dict):
    """Find the France bundle product that contains the given SKU."""
    for product in france_products.values():
        if product.get("type_id") != "bundle":
            continue
        for slot in product.get("bundle_slots", {}).values():
            if sku in slot.get("skus", []):
                return product
    return None

def get_france_hierarchy(sku: str, france_products: dict, france_cat_tree: list) -> list:
    """
    Return tree lines showing the France category -> bundle -> simple hierarchy
    for a given SKU.
    """
    product = france_products.get(sku)
    if not product:
        return [f"  ⚠️  SKU '{sku}' not found in France products."]

    cat_map       = build_france_category_map(france_cat_tree)
    parent_bundle = _find_france_parent_bundle(sku, france_products)
    lines         = []

    source         = parent_bundle if parent_bundle else product
    category_links = source.get("category_links", [])

    if not category_links:
        raw_ids = next(
            (
                a.get("value", [])
                for a in product.get("custom_attributes", [])
                if a.get("attribute_code") == "category_ids"
            ),
            [],
        )
        category_links = [{"category_id": str(cid)} for cid in raw_ids]

    if not category_links:
        category_links = [{"category_id": None}]

    for link in category_links:
        raw_id = link.get("category_id")
        path   = ["[No Category]"] if raw_id is None else _resolve_france_category_path(int(raw_id), cat_map)

        for i, node in enumerate(path):
            lines.append(f"{'    ' * i}└── {node}")

        depth = len(path)

        if parent_bundle:
            lines.append(f"{'    ' * depth}└── [bundle] {parent_bundle['sku']} — \"{parent_bundle['name']}\"")
            lines.append(f"{'    ' * (depth + 1)}└── [simple] {sku} — \"{product['name']}\"")
        else:
            lines.append(f"{'    ' * depth}└── [{product.get('type_id', 'simple')}] {sku} — \"{product['name']}\"")

        lines.append("")

    return lines
