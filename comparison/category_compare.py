def _normalize_category_ids(values) -> list[str]:
    ids = []
    if not values:
        return ids
    if isinstance(values, (list, tuple, set)):
        iterable = values
    else:
        iterable = [values]

    for value in iterable:
        if value is None:
            continue
        if isinstance(value, dict):
            cid = value.get("category_id") or value.get("id")
        else:
            cid = value
        if cid is None:
            continue
        ids.append(str(cid))
    return ids


def _extract_magento_category_links(magento_entry: dict | None) -> list[dict]:
    if not magento_entry:
        return []

    links = []
    raw_links = magento_entry.get("category_links") or []
    for link in raw_links:
        if not isinstance(link, dict):
            continue
        category_id = link.get("category_id")
        if category_id is None:
            continue
        links.append(
            {
                "category_id": str(category_id),
                "position": link.get("position"),
            }
        )

    if links:
        return links

    raw_ids = []
    for attr in magento_entry.get("custom_attributes", []) or []:
        if attr.get("attribute_code") == "category_ids":
            raw_ids = attr.get("value", []) or []
            break

    return [
        {"category_id": str(cid), "position": None}
        for cid in _normalize_category_ids(raw_ids)
    ]


def compare_category_links(pim_entry: dict | None, magento_entry: dict | None, magento_cat_tree: list | None = None) -> dict:
    """Compare PIM category IDs with Magento category links and category-tree metadata."""
    pim_category_ids = _normalize_category_ids((pim_entry or {}).get("categoryIds"))
    magento_links = _extract_magento_category_links(magento_entry)
    magento_category_ids = [link["category_id"] for link in magento_links if link.get("category_id")]

    if magento_cat_tree:
        from loaders.magento_loader import build_magento_category_map

        cat_map = build_magento_category_map(magento_cat_tree)
        resolved_links = []
        for link in magento_links:
            cid = link.get("category_id")
            if not cid:
                continue

            # Try to resolve using both int and string keys; the loader
            # stores both forms when possible.
            category_info = None
            try:
                if str(cid).isdigit():
                    category_info = cat_map.get(int(cid)) or cat_map.get(str(cid))
                else:
                    category_info = cat_map.get(str(cid)) or cat_map.get(cid)
            except Exception:
                category_info = cat_map.get(str(cid)) or cat_map.get(cid)

            resolved = {
                "category_id": cid,
                "position": link.get("position"),
                "category_name": category_info.get("name") if category_info else None,
                "category_position": category_info.get("position") if category_info else None,
                "position_match": None,
            }

            if category_info is not None:
                # Determine if positions match when both are present
                if link.get("position") is not None and category_info.get("position") is not None:
                    resolved["position_match"] = link.get("position") == category_info.get("position")
                else:
                    resolved["position_match"] = None

            resolved_links.append(resolved)
    else:
        resolved_links = [
            {
                "category_id": link.get("category_id"),
                "position": link.get("position"),
                "category_name": None,
                "category_position": None,
                "position_match": None,
            }
            for link in magento_links
        ]

    pim_set = set(pim_category_ids)
    magento_set = set(magento_category_ids)
    missing_in_magento = sorted(pim_set - magento_set)
    extra_in_magento = sorted(magento_set - pim_set)

    position_mismatches = []
    unknown_categories = []
    for link in resolved_links:
        if link.get("category_id") and link.get("category_name") is None:
            unknown_categories.append(link["category_id"])
        elif link.get("category_id") and link.get("position") is not None and link.get("category_position") is not None and not link.get("position_match"):
            position_mismatches.append(
                {
                    "category_id": link["category_id"],
                    "expected_position": link.get("category_position"),
                    "actual_position": link.get("position"),
                }
            )

    return {
        "matches": not missing_in_magento and not extra_in_magento and not position_mismatches and not unknown_categories,
        "pim_category_ids": pim_category_ids,
        "magento_category_ids": magento_category_ids,
        "magento_links": resolved_links,
        "missing_in_magento": missing_in_magento,
        "extra_in_magento": extra_in_magento,
        "position_mismatches": position_mismatches,
        "unknown_categories": unknown_categories,
    }
