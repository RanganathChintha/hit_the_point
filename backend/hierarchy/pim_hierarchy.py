from loaders.pim_loader import build_pim_category_map

def _resolve_pim_category_path(category_ids: list, cat_map: dict) -> list:
    """Walk up the PIM parent chain for each categoryId -> root-to-leaf paths."""
    paths = []
    for cat_id in category_ids:
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
            current = entry["parent"]
        if path:
            paths.append(path)
    return paths

def get_pim_hierarchy(sku: str, pim_products: dict, pim_cat_data: dict) -> list:
    """
    Return tree lines showing the PIM category -> bundle -> variant hierarchy
    for a given SKU.
    """
    product = pim_products.get(sku)
    if not product:
        return [f"  ⚠️  SKU '{sku}' not found in PIM products."]

    cat_map = build_pim_category_map(pim_cat_data)
    lines   = []

    parent_skus = product.get("parent_skus", [])

    if parent_skus:
        parent_sku  = parent_skus[0]
        parent      = pim_products.get(parent_sku, {})
        parent_name = parent.get("name", "Unknown")
        parent_type = parent.get("product_type", "Unknown")

        parent_cat_ids = [c["categoryId"] for c in parent.get("categoryIds", [])]
        parent_paths   = _resolve_pim_category_path(parent_cat_ids, cat_map)

        if not parent_paths:
            parent_paths = [["[No Category]"]]

        for path in parent_paths:
            for i, node in enumerate(path):
                lines.append(f"{'    ' * i}└── {node}")
            depth = len(path)
            lines.append(f"{'    ' * depth}└── [{parent_type}] {parent_sku} — \"{parent_name}\"")
            lines.append(f"{'    ' * (depth + 1)}└── [{product['product_type']}] {sku} — \"{product['name']}\"")
            lines.append("")

    else:
        cat_ids = [c["categoryId"] for c in product.get("categoryIds", [])]
        paths   = _resolve_pim_category_path(cat_ids, cat_map)

        if not paths:
            paths = [["[No Category]"]]

        for path in paths:
            for i, node in enumerate(path):
                lines.append(f"{'    ' * i}└── {node}")
            depth = len(path)
            lines.append(f"{'    ' * depth}└── [{product['product_type']}] {sku} — \"{product['name']}\"")
            lines.append("")

    return lines
